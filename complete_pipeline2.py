from pathlib import Path
import json
import os

from dotenv import load_dotenv
from c_structuring.structuring_pipeline import (
    structure_record,
    clean_for_db
)

from c_structuring.nar_schema_mapper import map_to_schema


# ============================================================
# LOAD ENV
# ============================================================

load_dotenv()
IP_SERVER = os.getenv("IP_SERVER")


# ============================================================
# MAIN FUNCTION (WHAT YOUR SENIOR ASKED FOR)
# ============================================================

def markdown_to_structured_json(md_path: Path) -> dict:
    """
    Converts a Markdown file into structured JSON using the
    existing structuring pipeline logic.

    Steps:
    1. Read markdown file
    2. Run LLM structuring (structure_record)
    3. Map to schema (map_to_schema)
    4. Clean for JSON compatibility (clean_for_db)

    Args:
        md_path (Path): Path to markdown file

    Returns:
        dict: {
            "structured_text": {...},
            "mapped_fields": {...}
        }
    """

    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    # ------------------------
    # STEP 1: READ FILE

    with open(md_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # ------------------------
    # STEP 2: STRUCTURE (LLM)

    structured_dict = structure_record(
        record_id="single_test",   # dummy ID
        markdown_text=markdown_text,
        model_name="qwen3.5:35b",
        base_url=IP_SERVER
    )

    # ------------------------
    # STEP 3: MAP TO CLEAN SCHEMA

    mapped_output = map_to_schema(structured_dict)

    # ------------------------
    # STEP 4: CLEAN (dates, times, etc.)

    clean_structured = clean_for_db(structured_dict)
    clean_mapped = clean_for_db(mapped_output)

    return {
        "structured_text": clean_structured,
        "mapped_fields": clean_mapped
    }


# ============================================================
# CLI TESTING
# ============================================================

if __name__ == "__main__":
    print(" Markdown → Structured JSON (using structuring_pipeline)")

    file_path = input("Enter path to .md file: ").strip().strip('"').strip("'")
    md_path = Path(file_path)

    try:
        result = markdown_to_structured_json(md_path)

        print("\n Structured Output:\n")
        print(json.dumps(result, indent=4))

    except Exception as e:
        print(f"\n Error: {e}")