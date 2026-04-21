import datetime
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
def clean_for_db(d):
    if isinstance(d, dict):
        return {k: clean_for_db(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_for_db(v) for v in d]
    elif isinstance(d, datetime.time):
        return d.strftime("%H:%M")
    elif isinstance(d, datetime.date):
        return d.strftime("%d-%m-%Y")
    elif isinstance(d, datetime.datetime):
        return d.strftime("%d-%m-%Y %H:%M")
    return d

# ------------------------
# FETCH MARKDOWN

def fetch_markdown_for_record(record_id: str, all_records: list) -> str | None:
    """
    Combine markdown for a record (page 1 and page 2).
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
# STRUCTURE RECORD

def structure_record(record_id: str, markdown_text: str, model_name: str, base_url: str):
    """
    Convert markdown to structured JSON using schema.
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

    return result.model_dump()


# ------------------------
# MAIN

def run_structuring_pipeline(
    model_name: str,
    host_url: str,
    table_in: str = "extractions",
    table_out: str = "structured",
    resume: bool = True
):
    """
    Convert extracted markdown to structured JSON while mapped to schema.
    """

    client = Client(host=host_url)

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
                host_url
            )

        except Exception as e:
            print(f"Structuring failed: {e}")
            continue

        # ------------------------
        # MAP TO SCHEMA
        try:
            mapped_output = map_to_schema(structured_dict)
        except Exception as e:
            print(f"Mapping failed: {e}")
            continue

        # ------------------------
        # SAVE RESULTS

        clean_structured = clean_for_db(structured_dict)
        clean_mapped = clean_for_db(mapped_output)

        try:
            safe_save(
                {"structured_text": clean_structured},
                table_out,
                record_id
            )

            safe_save(
                {"mapped_fields": clean_mapped}, #***
                "mapped",
                record_id
            )

            structured_ids.append(record_id)
            print(f"Saved: {record_id}")

        except Exception as e:
            print(f"Save failed: {e}")
            continue

    return structured_ids