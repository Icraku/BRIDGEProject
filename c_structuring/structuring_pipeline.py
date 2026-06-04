import time
from datetime import datetime, date, time as dt_time
from tqdm import tqdm
from ollama import Client

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from database_utils.db_utils import fetch_records, fetch_record
from database_utils.db_save import safe_save
from database_utils.queries import get_processed_ids

from c_structuring.nar_schema_mapper import map_to_schema
from c_structuring.bool_nullifier import nullify_unticked_bools, BOOL_FIELD_LABELS
from utils.text_cleaning import strip_markdown_fences
from schemas.neonatal_admission_form.nar_schema_included import NARRecord
from schemas.neonatal_admission_form.nar_full_schema import (
    NARFullRecord,
    NAR_REQUIRED_FIELDS,
    inclusion_status,
)
from schemas.internal_transfer_form.itf_schema import ITFRecord

# ------------------------
def clean_for_db(d, _bool_fields=set(BOOL_FIELD_LABELS.keys())):
    if d is None:
        return None
    if isinstance(d, dict):
        result = {}
        for k, v in d.items():
            cleaned = clean_for_db(v)
            # If a bool field came back None, store as "null" string
            # so SurrealDB doesn't coerce it to false
            if cleaned is None and k in _bool_fields:
                result[k] = "null"
            else:
                result[k] = cleaned
        return result
    elif isinstance(d, list):
        return [clean_for_db(v) for v in d]
    elif isinstance(d, dt_time):
        return d.strftime("%H:%M")
    elif isinstance(d, date):
        return d.strftime("%d-%m-%Y")
    elif isinstance(d, datetime):
        return d.strftime("%d-%m-%Y %H:%M")
    return d

# ------------------------
# FETCH MARKDOWN

def fetch_markdown_for_record(record_id: str, all_records: list) -> str | None:
    """Combine markdown for a record (page 1 and page 2)."""
    record_list = [
        r for r in all_records
        if record_id in str(r.get("id")).split(":")[-1]
    ]
    if not record_list:
        return None
    markdown_list = [
        strip_markdown_fences(r.get("extracted_text", ""))
        for r in record_list
        if "extracted_text" in r
    ]
    return "\n\n".join(markdown_list)


# ------------------------
# STRUCTURE RECORD

def structure_record(record_id: str, markdown_text: str, model_name: str, base_url: str):
    """
    Convert markdown to structured JSON using the full extraction schema.
    Returns:
      {
        "full_content":         dict of all extracted fields,
        "required_content":     dict of only the NARRecord fields,
        "supplementary_content":dict of the extra (not-included) fields,
        "inclusion_map":        {field: "included" | "not included"},
        "runtime_seconds":      float,
      }
    """

    system_prompt = (
        f"Extract information from the provided Markdown. "
        f"The response MUST be a json. "
        f"The format should be {NARFullRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")

    """system_prompt = (
        f"Extract information from the provided Markdown. "
        f"If the field has not been filled, return N/A, Example born_where: N/A "
        f"If you cannot read a field correctly, return the question mark symbol in its place, Example: Date of Admission: 12/??/2024 "
        f"The response MUST be a json. "
        f"The format should be {NARRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")"""

    start_time = time.perf_counter()

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{__text__}")]
    )

    prompt = prompt_template.invoke({"__text__": markdown_text})

    llm = ChatOllama(model=model_name, base_url=base_url)
    structured_llm = llm.with_structured_output(NARFullRecord)
    result: NARFullRecord = structured_llm.invoke(prompt)

    end_time = time.perf_counter()
    runtime_seconds = end_time - start_time

    full_dict = result.model_dump()

    # Split into required vs supplementary
    required_dict = {k: v for k, v in full_dict.items() if k in NAR_REQUIRED_FIELDS}
    supplementary_dict = {k: v for k, v in full_dict.items() if k not in NAR_REQUIRED_FIELDS}

    # Build inclusion map for every extracted field
    inclusion_map = {field: inclusion_status(field) for field in full_dict}

    return {
        "full_content": full_dict,
        "required_content": required_dict,
        "supplementary_content": supplementary_dict,
        "inclusion_map": inclusion_map,
        "runtime_seconds": runtime_seconds,
    }


# ------------------------
# MAIN

def run_structuring_pipeline(
    model_name: str,
    host_url: str,
    table_in: str = "extractions",
    table_out: str = "structured_Q",
    resume: bool = True,
    run_id = None,
    **kwargs,
):
    """
    Convert extracted markdown to structured JSON while mapped to schema.

    Saves to three tables:
      - table_out          : full extraction (all fields, NARFullRecord)
      - "structured_required"  : only the NARRecord fields
      - "mapped"               : schema-mapped output for downstream use
    """

    client = Client(host=host_url)

    all_records = fetch_records(table_in)

    image_ids = get_processed_ids(table_in)
    image_ids = list(set([i.split("_page")[0] for i in image_ids]))

    structured_ids = []

    for record_id in tqdm(image_ids):

        record_start_time = time.perf_counter()

        print(f"\n=== Structuring {record_id} ===")

        run_id = datetime.now().isoformat()
        print(f"{record_id} → {run_id}")

        # ------------------------
        # RESUME
        if resume:
            try:
                existing = fetch_record(table_out, record_id)
                if existing:
                    print("Already structured, skipping")
                    structured_ids.append(record_id)
                    continue
            except Exception:
                pass

        # ------------------------
        # FETCH MARKDOWN
        markdown_text = fetch_markdown_for_record(record_id, all_records)
        if not markdown_text:
            print("No markdown found, skipping")
            continue

        # ------------------------
        # STRUCTURE
        try:
            structure_result = structure_record(
                record_id,
                markdown_text,
                model_name,
                host_url
            )

            full_dict         = structure_result["full_content"]
            required_dict     = structure_result["required_content"]
            supplementary_dict = structure_result["supplementary_content"]
            inclusion_map     = structure_result["inclusion_map"]
            llm_runtime_seconds = structure_result["runtime_seconds"]

            # Post-process: blank bool fields changed to None instead of false
            # Applied to the required subset (matches existing nullifier logic)
            required_dict = nullify_unticked_bools(required_dict, markdown_text)

        except Exception as e:
            print(f"Structuring failed: {e}")
            continue

        # ------------------------
        # MAP TO SCHEMA
        try:
            mapped_output = map_to_schema(required_dict)
        except Exception as e:
            print(f"Mapping failed: {e}")
            continue

        # ------------------------
        # RECORD TIMER END
        record_end_time = time.perf_counter()
        total_record_runtime = (record_end_time - record_start_time)

        # ------------------------
        # CLEAN FOR DB
        clean_full = clean_for_db(full_dict)
        clean_required = clean_for_db(required_dict)
        clean_supplementary = clean_for_db(supplementary_dict)
        clean_mapped = clean_for_db(mapped_output)

        # Debug: fields that should be None
        nulled = {k: v for k, v in clean_required.items() if v is None}
        print(f"  Fields that should be None: {list(nulled.keys())}")

        # ------------------------
        # SAVE RESULTS
        try:
            # Full extraction table (all fields + inclusion map)
            safe_save(
                {
                    "structured_text": clean_full,
                    "inclusion_map": inclusion_map,
                    "run_id": run_id,
                    "llm_runtime_seconds": llm_runtime_seconds,
                    "total_record_runtime_seconds": total_record_runtime,
                },
                table_out,
                record_id,
            )

            # Required-fields-only table (backwards-compatible with evaluation)
            safe_save(
                {
                    "structured_text": clean_required,
                    "run_id": run_id,
                },
                "structured_required",
                record_id,
            )

            # Supplementary fields table
            safe_save(
                {
                    "structured_text": clean_supplementary,
                    "run_id": run_id,
                },
                "structured_supplementary",
                record_id,
            )

            # Schema-mapped output
            safe_save(
                {
                    "mapped_fields": clean_mapped,
                    "run_id": run_id,
                },
                "mapped",
                record_id,
            )

            structured_ids.append(record_id)
            print(f"Saved: {record_id}")

        except Exception as e:
            print(f"Save failed: {e}")
            continue

    return structured_ids