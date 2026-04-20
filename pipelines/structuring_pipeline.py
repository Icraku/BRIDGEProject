# pipelines/structuring_pipeline.py

from tqdm import tqdm
from ollama import Client

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from db.db_utils import fetch_records, fetch_record
from db.db_save import safe_save
from db.queries import get_processed_ids

from mapping.nar_mapper import map_to_schema
from utils.text_cleaning import strip_markdown_fences
from nar_schema.narP1_schema import NARRecord


# ------------------------
# FETCH MARKDOWN FOR ONE RECORD

def fetch_markdown_for_record(record_id: str, all_records: list) -> str | None:
    """
    Combine markdown entries for a record (multi-page).
    """

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
# STRUCTURE ONE RECORD

def structure_record(record_id: str, markdown_text: str, model_name: str, base_url: str):
    """
    Convert markdown → structured JSON using schema.
    """

    system_prompt = (
        f"Extract information from the provided Markdown. "
        f"The response MUST be a json. "
        f"The format should be {NARRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{__text__}")]
    )

    prompt = prompt_template.invoke({"__text__": markdown_text})

    llm = ChatOllama(
        model=model_name,
        base_url=base_url
    )

    structured_llm = llm.with_structured_output(NARRecord)

    result = structured_llm.invoke(prompt)

    return result.model_dump()   # clean dict


# ------------------------
# MAIN PIPELINE

def run_structuring_pipeline(
    model_name: str,
    base_url: str,
    table_in: str = "extractions",
    table_out: str = "structured",
    resume: bool = True
):
    """
    Convert extracted markdown → structured JSON → mapped schema.
    """

    client = Client(host=base_url)

    all_records = fetch_records(table_in)

    image_ids = get_processed_ids(table_in)
    image_ids = list(set([i.split("_page")[0] for i in image_ids]))

    structured_ids = []

    for record_id in tqdm(image_ids):
        print(f"\n=== Structuring {record_id} ===")

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
            structured_dict = structure_record(
                record_id,
                markdown_text,
                model_name,
                base_url
            )

        except Exception as e:
            print(f"Structuring failed: {e}")
            continue

        # ------------------------
        # MAP TO CLEAN SCHEMA
        try:
            mapped_output = map_to_schema(structured_dict)
        except Exception as e:
            print(f"Mapping failed: {e}")
            continue

        # ------------------------
        # SAVE RESULTS
        try:
            save_safe(
                {"structured_text": structured_dict},
                table_out,
                record_id
            )

            save_safe(
                {"mapped_fields": mapped_output},
                "mapped",
                record_id
            )

            structured_ids.append(record_id)
            print(f"Saved: {record_id}")

        except Exception as e:
            print(f"Save failed: {e}")
            continue

    return structured_ids