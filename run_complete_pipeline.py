from pathlib import Path
import json
import re
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Your schema
from schemas.nar_schema import NARRecord


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()
IP_SERVER = os.getenv("IP_SERVER")


# ============================================================
# UTILITY: CLEAN MARKDOWN
# ============================================================

def strip_markdown_fences(text: str) -> str:
    """
    Removes markdown code fences like ```json ... ```
    """
    return re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()


# ============================================================
# MAIN FUNCTION
# ============================================================

def markdown_to_structured_json(md_path: Path) -> dict:
    """
    Converts a Markdown file into structured JSON using an LLM.

    This uses:
    - ChatOllama (your model)
    - NARRecord schema enforcement
    - Structured output (guaranteed JSON)

    Args:
        md_path (Path): Path to markdown file

    Returns:
        dict: Structured JSON output
    """

    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    # ------------------------
    # STEP 1: READ FILE
    with open(md_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # ------------------------
    # STEP 2: CLEAN MARKDOWN
    cleaned_text = strip_markdown_fences(raw_text)

    # ------------------------
    # STEP 3: BUILD PROMPT

    system_prompt = (
        "Extract ALL information from the provided Markdown.\n"
        "Return ONLY valid JSON.\n"
        f"The format MUST match this schema: {NARRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "{text}")
        ]
    )

    prompt = prompt_template.invoke({"text": cleaned_text})

    # ------------------------
    # STEP 4: INITIALIZE MODEL

    llm = ChatOllama(
        model="qwen3.5:35b",
        base_url=IP_SERVER
    )

    structured_llm = llm.with_structured_output(NARRecord)

    # ------------------------
    # STEP 5: RUN STRUCTURING

    response = structured_llm.invoke(prompt)

    # Convert to JSON
    result_json = json.loads(response.model_dump_json())

    return result_json


# ============================================================
# CLI TESTING
# ============================================================

if __name__ == "__main__":
    file_path = input("Enter path to .md file: ").strip().strip('"').strip("'")
    md_path = Path(file_path)

    try:
        result = markdown_to_structured_json(md_path)

        print("\n Structured JSON:\n")
        print(json.dumps(result, indent=4))

    except Exception as e:
        print(f"\n Error: {e}")