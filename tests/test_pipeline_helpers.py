"""
tests/test_pipeline_helpers.py
==============================
Tests for helper functions used by the pipelines.
"""

from unittest.mock import Mock

from a_input.image_encoding import image_to_base64
from b_extraction.extraction_pipeline import _merge_predictions, _run_prompt
from c_structuring.markdown_utils import dict_to_markdown, markdown_to_dict
from c_structuring.nar_schema_mapper import map_to_schema
from c_structuring.schema_helpers import get_boolean_from_suffix, get_true_option
from c_structuring.text_cleaning import strip_markdown_fences


def test_strip_markdown_fences_removes_code_blocks():
    text = "```json\n{\n  \"name\": \"Baby A\"\n}\n```"

    assert strip_markdown_fences(text) == '{\n  "name": "Baby A"\n}'


def test_markdown_to_dict_handles_json_and_key_values():
    assert markdown_to_dict('{"name": "Baby A"}') == {"name": "Baby A"}
    assert markdown_to_dict("- name: Baby A\n- weight: 3.2kg") == {"name": "Baby A", "weight": "3.2kg"}


def test_dict_to_markdown_formats_a_bullet_list():
    rendered = dict_to_markdown({"name": "Baby A", "weight": "3.2kg"})

    assert rendered.startswith("## Final Extraction")
    assert "- name: Baby A" in rendered
    assert "- weight: 3.2kg" in rendered


def test_get_true_option_returns_true_key():
    assert get_true_option({"F": False, "M": True, "I": False}) == "M"


def test_get_boolean_from_suffix_reads_flag():
    assert get_boolean_from_suffix({"flag_Y": True}, "flag") is True
    assert get_boolean_from_suffix({}, "flag") is False


def test_map_to_schema_handles_key_variants():
    structured = {
        "A: Infant Details": {
            "Sex": {"F": False, "M": True},
            "Delivery": {"SVD": True},
            "Born_outside_facility_Y": True,
            "Multiple_delivery_Y": False,
        },
        "A: B": {"Crackles_Y": True},
        "E: History and examination": {"Symptoms": {"Reduced / Absent movement_Y": True}},
    }

    assert map_to_schema(structured) == {
        "sex": "M",
        "delivery": "SVD",
        "born_outside": True,
        "multiple_delivery": False,
        "crackles": True,
        "reduced_movement": True,
    }


def test_merge_predictions_uses_majority_vote():
    merged = _merge_predictions([
        {"name": "Baby A", "weight": "3.2kg"},
        {"name": "Baby A", "weight": "3.4kg"},
        {"name": "Baby B", "weight": "3.2kg"},
    ])

    assert merged == {"name": "Baby A", "weight": "3.2kg"}


def test_run_prompt_returns_content_and_runtime():
    fake_client = Mock()
    fake_client.chat.return_value = {"message": {"content": "hello"}}

    result = _run_prompt(fake_client, "demo-model", "prompt text", "base64-image")

    assert result["content"] == "hello"
    assert result["runtime_seconds"] >= 0
    fake_client.chat.assert_called_once()


def test_image_to_base64_encodes_file(tmp_path):
    image_path = tmp_path / "sample.bin"
    image_path.write_bytes(b"abc")

    assert image_to_base64(str(image_path)) == "YWJj"
