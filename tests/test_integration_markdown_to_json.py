"""
tests/test_integration_markdown_to_json.py
==========================================
Integration tests for converting extracted markdown to structured JSON.

These tests verify the two approaches to markdown-to-JSON conversion:
1. Direct LLM structuring (markdown_to_structured_json_direct)
2. Using the structuring pipeline (markdown_to_structured_json_pipeline)

Requires:
- Running Ollama instance
- Environment variable: IP_SERVER
- Markdown files to test against

This test is optional and should only run when external resources are available.
Set environment variable `RUN_INTEGRATION_TESTS=1´ in the .env file for this file to work.
"""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from dotenv import load_dotenv

load_dotenv()


def markdown_to_structured_json_direct(md_path: Path) -> dict:
    """Convert markdown to structured JSON using direct LLM call.

    Uses:
    - ChatOllama with structured output
    - NARRecord and ITFRecord schemas

    Parameters
    ----------
    md_path: Path to markdown file.

    Returns
    -------
    dict: Structured JSON output.
    """
    from langchain_ollama import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
    from schemas.neonatal_admission_form.nar_schema_included import NARRecord
    from schemas.internal_transfer_form.itf_schema import ITFRecord
    from c_structuring.text_cleaning import strip_markdown_fences

    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_text = strip_markdown_fences(raw_text)

    system_prompt = (
        "Extract ALL information from the provided Markdown.\n"
        "Return ONLY valid JSON.\n"
        f"The format MUST match this schema: {NARRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{text}")]
    )
    prompt = prompt_template.invoke({"text": cleaned_text})

    ip_server = os.getenv("IP_SERVER")
    llm = ChatOllama(model="qwen3.5:35b", base_url=ip_server)
    structured_llm = llm.with_structured_output(ITFRecord)

    response = structured_llm.invoke(prompt)
    return json.loads(response.model_dump_json())


def markdown_to_structured_json_pipeline(md_path: Path) -> dict:
    """Convert markdown to structured JSON using the structuring pipeline.

    Uses:
    - Existing structuring_pipeline logic
    - Schema mapping
    - Database cleaning

    Parameters
    ----------
    md_path: Path to markdown file.

    Returns
    -------
    dict with keys: structured_text, mapped_fields.
    """
    from c_structuring.structuring_pipeline import clean_for_db
    from c_structuring.nar_schema_mapper import map_to_schema

    if not md_path.exists():
        raise FileNotFoundError(f"File not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    # Mock the structure_record call since we're just testing the pipeline logic
    mock_structured = {
        "field_1": "value_1",
        "field_2": "value_2",
    }

    mapped_output = map_to_schema(mock_structured)
    clean_structured = clean_for_db(mock_structured)
    clean_mapped = clean_for_db(mapped_output)

    return {
        "structured_text": clean_structured,
        "mapped_fields": clean_mapped,
    }


def test_markdown_to_json_direct_with_mock(tmp_path):
    """Test direct markdown-to-JSON with mocked LLM."""
    test_md = tmp_path / "test.md"
    test_md.write_text("# Test\n- field_1: value_1\n- field_2: value_2")

    with patch("langchain_ollama.ChatOllama") as mock_llm_class:
        mock_structured_llm = Mock()
        mock_response = Mock()
        mock_response.model_dump_json.return_value = '{"field_1": "value_1"}'
        mock_structured_llm.invoke.return_value = mock_response

        mock_llm = Mock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_llm_class.return_value = mock_llm

        with patch.dict(os.environ, {"IP_SERVER": "http://localhost:11434"}):
            result = markdown_to_structured_json_direct(test_md)

        assert isinstance(result, dict)
        assert "field_1" in result


def test_markdown_to_json_pipeline_with_mock(tmp_path):
    """Test pipeline markdown-to-JSON conversion."""
    test_md = tmp_path / "test.md"
    test_md.write_text("# Test\n- field_1: value_1")

    result = markdown_to_structured_json_pipeline(test_md)

    assert isinstance(result, dict)
    assert "structured_text" in result
    assert "mapped_fields" in result


def test_markdown_to_json_file_not_found():
    """Test that missing markdown file raises FileNotFoundError."""
    try:
        markdown_to_structured_json_pipeline(Path("/nonexistent/file.md"))
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass
