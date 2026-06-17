"""
b_extraction/extraction_pipeline.py
====================================
First stage of the BRIDGE pipeline: extract structured markdown from NAR form
images using a Vision-Language Model (VLM) served via Ollama.

Pipeline
--------
1. Load images from *image_dir* (via ``a_input.image_utils.load_images``).
2. For each image, run every prompt in ``b_extraction/prompts/`` through the
   VLM and save the raw markdown output to SurrealDB.
3. If multiple prompts are configured, merge their parsed outputs by majority
   vote (``_merge_predictions``).
4. Return a list of processed record IDs so the caller can chain to Stage B.

Public API
----------
run_extraction_pipeline(image_dir, model_name, table_name, ...)
    Orchestrates the full extraction run.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

from tqdm import tqdm
from ollama import Client

from a_input.image_utils import load_images
from b_extraction.prompts.prompt_loader import load_prompt_config, load_prompts
from c_structuring.markdown_utils import dict_to_markdown
from c_structuring.markdown_utils import markdown_to_dict
from d_evaluation.field_accuracy import compute_accuracy
from database_utils.db_utils import fetch_record, safe_save
from a_input.image_encoding import image_to_base64

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _merge_predictions(pred_dicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge multiple prediction dicts into one using per-field majority vote.

    When the VLM is run with several prompts, each produces a parsed dict.
    This function combines them so the most common value wins for every field.

    Parameters
    ----------
    pred_dicts: List of field-value dicts, one per prompt run.

    Returns
    -------
    dict[str, Any]
        Merged dict with one value per field.
    """
    all_keys: set[str] = set()
    for d in pred_dicts:
        all_keys.update(d.keys())

    return {
        key: Counter(d.get(key, "N/A") for d in pred_dicts).most_common(1)[0][0]
        for key in all_keys
    }


def _run_prompt(
    client: Client,
    model_name: str,
    prompt_text: str,
    image_base64: str,
) -> dict[str, Any]:
    """Send one prompt + image to the VLM and return content + clock time.

    Parameters
    ----------
    client: Ollama client instance.
    model_name: Ollama model tag (e.g. ``"qwen2-vl:7b"``).
    prompt_text: Full prompt string.
    image_base64: Base-64 encoded image bytes.

    Returns
    -------
    dict with keys ``content`` (str) and ``runtime_seconds`` (float).
    """
    start = time.perf_counter()
    response = client.chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt_text,
                "images": [image_base64],
            }
        ],
        options={"seed": 42},
    )
    runtime = time.perf_counter() - start

    return {
        "content": response["message"]["content"],
        "runtime_seconds": runtime,
    }


# ---------------------------------------------------------------------------
# Per-image processing

def _process_image(
    image_path: str,
    client: Client,
    model_name: str,
    prompts: dict[str, str],
    prompt_config: dict[str, str],
    table_name: str,
    ground_truth: dict | None,
    resume: bool,
) -> dict[str, Any] | None:
    """Run all prompts on one image, save outputs to DB, and return a summary.

    Parameters
    ----------
    image_path: Path (Absolute) to the image file.
    client: Ollama client.
    model_name: VLM model tag.
    prompts: Mapping of prompt name to the prompt text.
    prompt_config: Mapping of prompt name to the ground-truth section key.
    table_name: SurrealDB table to write raw extractions to.
    ground_truth: Optional dict of ground-truth values for accuracy estimation.
    resume: If ``True``, skip images that already have a DB record.

    Returns
    -------
    dict | None
        Summary dict with ``record_id``, ``final_markdown``, ``accuracy``,
        ``model``, and ``runtime_seconds``; or ``None`` if skipped.
    """
    record_start = time.perf_counter()

    image_name = Path(image_path).name
    record_id = Path(image_path).stem

    logger.info("Processing %s", image_name)

    # --- Resume check -------------------------------------------------------
    if resume:
        existing = fetch_record(table_name, f"{record_id}_base")
        if existing:
            logger.info("Skipping %s -- already in DB.", record_id)
            return None

    image_base64 = image_to_base64(image_path)

    parsed_predictions: list[dict[str, Any]] = []
    markdown_outputs: list[str] = []
    accuracies: list[float] = []

    # --- Prompt loop --------------------------------------------------------
    for prompt_name, prompt_text in prompts.items():
        logger.info("  Running prompt: %s", prompt_name)

        result = _run_prompt(client, model_name, prompt_text, image_base64)
        md_output: str = result["content"]
        runtime: float = result["runtime_seconds"]

        markdown_outputs.append(md_output)

        # Save raw extraction to DB
        safe_save(
            {
                "model": model_name,
                "record_id": record_id,
                "extracted_text": md_output,
                "prompt": prompt_name,
                "runtime_seconds": runtime,
            },
            table_name,
            f"{record_id}_{prompt_name}",
        )
        logger.debug("  Saved: %s_%s to Database", record_id, prompt_name)

        # Parse markdown → dict
        parsed = markdown_to_dict(md_output)
        parsed_predictions.append(parsed)

        # Optional accuracy against ground truth
        if ground_truth:
            gt_key = prompt_config.get(prompt_name)
            truth = ground_truth.get(gt_key) if gt_key else None
            if truth:
                accuracies.append(compute_accuracy(parsed, truth))

    # --- Merge Prediction results if multiple prompts ------------------------------------------
    if len(parsed_predictions) == 1:
        merged = parsed_predictions[0]
        final_md = markdown_outputs[0]
    else:
        merged = _merge_predictions(parsed_predictions)
        final_md = dict_to_markdown(merged)

    total_runtime = time.perf_counter() - record_start
    overall_acc = round(sum(accuracies) / len(accuracies), 3) if accuracies else 0.0

    return {
        "record_id": record_id,
        "final_markdown": final_md,
        "accuracy": overall_acc,
        "model": model_name,
        "runtime_seconds": total_runtime,
    }


# ---------------------------------------------------------------------------
# Public API

def run_extraction_pipeline(
    image_dir: str,
    model_name: str,
    table_name: str,
    ground_truth: dict | None = None,
    resume: bool = True,
    report_path: str = "results.md",
) -> list[str]:
    """Run the full extraction pipeline over all images in *image_dir*.

    For each image the VLM is called with every configured prompt, raw
    outputs are saved to SurrealDB and a human-readable Markdown report
    is written to *report_path*.

    Parameters
    ----------
    image_dir: Directory containing NAR form images (PNG / JPG).
    model_name: Ollama model tag to use for extraction.
    table_name: SurrealDB table name for raw extraction records.
    ground_truth: Optional dict of known field values used for in-pipeline accuracy
        estimation (useful for spot-checking during development).
    resume: Skip images whose record already exists in *table_name*.
    report_path: Path for the Markdown summary report written at the end of the run.

    Returns
    -------
    list[str]
        Record IDs that were processed in this run (excludes skipped).
    """
    server_ip = os.getenv("IP_SERVER")
    if not server_ip:
        raise EnvironmentError("IP_SERVER environment variable is not set.")

    prompts = load_prompts()
    if not prompts:
        raise ValueError("No prompts loaded — check b_extraction/prompts/*.txt")

    prompt_config = load_prompt_config()
    images = load_images(image_dir)
    client = Client(host=server_ip)

    logger.info(
        "Starting extraction: model=%s, images=%d, table=%s",
        model_name,
        len(images),
        table_name,
    )

    report_lines: list[str] = []
    processed_ids: list[str] = []

    for image_path in tqdm(images, desc="Extracting"):
        result = _process_image(
            image_path=image_path,
            client=client,
            model_name=model_name,
            prompts=prompts,
            prompt_config=prompt_config,
            table_name=table_name,
            ground_truth=ground_truth,
            resume=resume,
        )

        if result is None:
            continue

        processed_ids.append(result["record_id"])

        report_lines += [
            f"# {result['record_id']}\n",
            result["final_markdown"],
            f"\n**Accuracy:** {result['accuracy']}\n",
            "---\n",
        ]

    # Write consolidated Markdown report
    Path(report_path).write_text("\n".join(report_lines), encoding="utf-8")
    logger.info("Report written to %s", report_path)
    logger.info("Processed %d image(s).", len(processed_ids))

    return processed_ids