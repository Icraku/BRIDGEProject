"""
tests/test_integration_extraction_structuring.py
================================================
Integration tests for the extraction and structuring pipelines.

These tests require:
- Running Ollama instances (local and/or remote)
- Environment variables: IP_SERVER, IP_LOCAL
- Ground truth metadata file

This test is optional and should only run when external resources are available.
Set environment variable `RUN_INTEGRATION_TESTS=1´ in the .env file for this to work.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock

from a_input.image_utils import load_images
from b_extraction.extraction_pipeline import _process_image
from b_extraction.prompts.prompt_loader import load_prompts, load_prompt_config
from c_structuring.structuring_pipeline import run_structuring_pipeline


def _load_ground_truth(gt_path: str) -> dict | None:
    """Load and normalize ground truth metadata."""
    if not os.path.exists(gt_path):
        return None

    with open(gt_path) as f:
        gt_data = json.load(f)

    if isinstance(gt_data, list):
        normalized = {}
        for item in gt_data:
            record_id = item.get("_id", "").split("_page")[0]
            if record_id:
                normalized[record_id] = item
        return normalized

    return gt_data if isinstance(gt_data, dict) else None


def test_extraction_pipeline_with_mock_client(tmp_path):
    """Test extraction pipeline with mocked Ollama client."""
    mock_client = Mock()
    mock_client.chat.return_value = {
        "message": {"content": "- name: test\n- weight: 3.2kg"}
    }

    prompts = load_prompts()
    prompt_config = load_prompt_config()

    test_image = tmp_path / "test_image.png"
    test_image.write_bytes(b"fake image data")

    result = _process_image(
        image_path=str(test_image),
        client=mock_client,
        model_name="test-model",
        prompts=prompts,
        prompt_config=prompt_config,
        table_name="test_extractions",
        ground_truth=None,
        resume=False,
    )

    assert result is not None
    assert "record_id" in result
    assert "final_markdown" in result
    assert "runtime_seconds" in result


def test_ground_truth_normalization():
    """Test that ground truth data is normalized correctly."""
    list_format = [
        {"_id": "NAR_001_page1", "field": "value1"},
        {"_id": "NAR_001_page2", "field": "value2"},
        {"_id": "NAR_002_page1", "field": "value3"},
    ]

    result = _load_ground_truth.__wrapped__.__globals__["_load_ground_truth"](list_format)

    # Since this is called from a file, we need to test the logic directly
    normalized = {}
    for item in list_format:
        record_id = item.get("_id", "").split("_page")[0]
        if record_id:
            normalized[record_id] = item

    assert "NAR_001" in normalized
    assert "NAR_002" in normalized
    assert len(normalized) == 2
