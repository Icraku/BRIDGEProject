"""
d_evaluation/evaluation_pipeline.py
=====================================
Stage C of the BRIDGE pipeline: evaluate structured LLM outputs against
ground truth and produce a comprehensive metrics report.

This is the main orchestrator for all five evaluation modules:

1. ``field_accuracy``         — fuzzy field-level accuracy (``correct?`` column)
2. ``classification_metrics`` — F1, Precision, Recall per field and field type
3. ``text_metrics``           — CER + WER for free-text fields
4. ``schema_compliance``      — field coverage and type validity (no GT needed)
5. ``runtime_analysis``       — LLM inference and total pipeline timing
6. ``hallucination_detector`` — out-of-allowlist / out-of-range / bad-format values

Running this file directly executes the full suite for Qwen and Gemma:

    python d_evaluation/evaluation_pipeline.py

Public API
----------
run_evaluation(gt_path, structured_table, model_label) -> pd.DataFrame
    Evaluate one model against ground truth.

run_full_metrics_suite(gt_path, model_configs) -> dict
    Run all five modules for every model and produce cross-model summaries.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import pandas as pd
from pandas import DataFrame

from d_evaluation.classification_metrics import run_classification_metrics
from d_evaluation.field_accuracy import build_accuracy_table, load_structured_outputs
from d_evaluation.hallucination_detector import run_hallucination_detection
from d_evaluation.runtime_analysis import run_runtime_analysis
from d_evaluation.schema_compliance import run_schema_compliance
from d_evaluation.text_metrics import run_text_metrics
from database_utils.db_utils import safe_save
from schemas.neonatal_admission_form.field_types import FIELD_TYPES, HOSPITAL_CODES
from schemas.neonatal_admission_form.nar_full_schema import (
    FULL_SCHEMA_FIELDS,
    NAR_REQUIRED_FIELDS,
    inclusion_status,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ground-truth loading

def load_and_process_meta(
    gt_path: str,
    predictions: dict,
) -> dict[str, dict]:
    """Load and filter the ground-truth JSON to records present in *predictions*.

    Handles both dict format (``{record_id: fields}``) and list format
    (``[{"_id": "NAR_40000001_page1", ...}, ...]``).  For the list format,
    page records are merged into a single base-ID record, giving precedence
    to non-empty values.

    Parameters
    ----------
    gt_path: Path to ``NAR_metadata.json``.
    predictions: ``{record_id: structured_dict}`` — used to filter GT to matched records.

    Returns
    -------
    dict[str, dict]
        ``{base_record_id: gt_fields_dict}``
    """
    with open(gt_path, encoding="utf-8") as f:
        raw_gt = json.load(f)

    if isinstance(raw_gt, dict):
        return {k: v for k, v in raw_gt.items() if k in predictions}

    gt_dict: dict[str, dict] = {}
    for item in raw_gt:
        file_id = item.get("_id", "")
        if not file_id.startswith("NAR_"):
            continue
        base_id = file_id.split("_page")[0]
        if base_id not in predictions:
            continue
        if base_id not in gt_dict:
            gt_dict[base_id] = {}
        for k, v in item.items():
            if k == "_id":
                continue
            if k not in gt_dict[base_id] or gt_dict[base_id][k] in (None, "", "null"):
                gt_dict[base_id][k] = v

    return gt_dict


# ---------------------------------------------------------------------------
# Single-model evaluation

def run_evaluation(
    gt_path: str,
    structured_table: str = "structured_qwen_required",
    model_label: str = "qwen",
) -> DataFrame | None:
    """Evaluate one model's structured outputs against ground truth.

    Loads predictions from *structured_table*, matches them against GT,
    calls ``build_accuracy_table``, writes per-record results to SurrealDB,
    and saves ``field_accuracy_{model}.csv`` and ``all_fields_{model}.csv``.

    Parameters
    ----------
    gt_path:
        Path to ``NAR_metadata.json``.
    structured_table:
        SurrealDB table containing the required 98-field structured outputs.
    model_label:
        Used for output filenames and DB table names.

    Returns
    -------
    pd.DataFrame | None
        The full accuracy table, or ``None`` if ground truth is unavailable.
    """
    if not Path(gt_path).exists():
        logger.warning("Ground truth not found at %s — skipping evaluation.", gt_path)
        return None

    logger.info("Evaluating: model=%s, table=%s", model_label, structured_table)

    predictions  = load_structured_outputs(structured_table)
    ground_truth = load_and_process_meta(gt_path, predictions)
    logger.info(
        "  Predictions: %d | GT matched: %d", len(predictions), len(ground_truth)
    )

    df = build_accuracy_table(predictions, ground_truth)
    df["model"] = model_label

    df.to_csv(f"field_accuracy_{model_label}.csv", index=False)

    df_scored = df[df["scorable"] & df["has_gt"]].copy()

    # All-fields summary (120 fields grouped by inclusion + GT availability)
    all_field_summary = (
        df.groupby(["field", "field_type", "nar_inclusion", "scorable", "has_gt"])
        .agg(avg_accuracy=("correct?", "mean"), n_records=("record_id", "nunique"))
        .reset_index()
        .sort_values(
            ["nar_inclusion", "field_type", "avg_accuracy"],
            ascending=[True, True, False],
        )
    )
    all_field_summary.to_csv(f"all_fields_{model_label}.csv", index=False)

    logger.info(
        "  Fields: %d total | %d scored | %d unscored | %d no GT",
        df["field"].nunique(),
        df_scored["field"].nunique(),
        df[~df["scorable"]]["field"].nunique(),
        df[~df["has_gt"]]["field"].nunique(),
    )

    # Persist per-record results to SurrealDB
    eval_table = f"evaluation_{model_label}"
    for record_id, group in df.groupby("record_id"):
        group_scored = group[group["scorable"] & group["has_gt"]]
        safe_save(
            {
                "record_id":        record_id,
                "model":            model_label,
                "average_accuracy": (
                    round(float(group_scored["correct?"].mean()), 3)
                    if len(group_scored) else None
                ),
                "by_field_type": (
                    group_scored.groupby("field_type")["correct?"]
                    .mean().round(3).to_dict()
                ),
                "by_nar_inclusion": (
                    group_scored.groupby("nar_inclusion")["correct?"]
                    .mean().round(3).to_dict()
                ),
                "fields": group[[
                    "field", "correct?", "has_gt", "scorable",
                    "ground_truth_val", "predicted_val",
                    "field_type", "nar_inclusion",
                ]].to_dict(orient="records"),
            },
            eval_table,
            str(record_id),
        )

    logger.info("  Saved %d records to %s.", df["record_id"].nunique(), eval_table)
    return df


# ---------------------------------------------------------------------------
# Full metrics calls

def run_full_metrics_suite(
    gt_path: str,
    model_configs: list[dict],
) -> dict:
    """Run all evaluation modules for every model and produce a cross-model report.

    Parameters
    ----------
    gt_path: Path to ``NAR_metadata.json`` ground-truth file.
    model_configs: List of dicts, each with:

        - ``model_label`` — ``"qwen"`` / ``"gemma"`` / ``"medgemma"``
        - ``eval_table``  — DB table for accuracy eval (98-field required subset)
        - ``full_table``  — DB table for compliance/hallucination (all 120 fields)

    Returns
    -------
    dict
        Nested dict keyed by model label, with sub-keys ``accuracy_df``,
        ``metrics``, ``text``, ``compliance``, ``hallucination``, plus a
        top-level ``"runtime"`` key.

    Example
    -------
    >>> run_full_metrics_suite(
    ...     gt_path="/data/NAR_metadata.json",
    ...     model_configs=[
    ...         {"model_label": "qwen",
    ...          "eval_table":  "structured_qwen_required",
    ...          "full_table":  "structured_qwen"},
    ...         {"model_label": "gemma",
    ...          "eval_table":  "structured_gemma_required",
    ...          "full_table":  "structured_gemma"},
    ...     ],
    ... )
    """
    results: dict = {}

    # Steps 1 + 2: accuracy and classification metrics
    for cfg in model_configs:
        label = cfg["model_label"]
        logger.info("=" * 60)
        logger.info("MODEL: %s", label.upper())
        logger.info("=" * 60)

        df = run_evaluation(gt_path, structured_table=cfg["eval_table"], model_label=label)
        results[label] = {"accuracy_df": df}

        if df is not None:
            results[label]["metrics"] = run_classification_metrics(df, model_label=label)
            results[label]["text"]    = run_text_metrics(df, model_label=label)

    # Step 3: schema compliance (no GT required)
    for cfg in model_configs:
        label = cfg["model_label"]
        results.setdefault(label, {})["compliance"] = run_schema_compliance(
            structured_table=cfg["full_table"],
            model_label=label,
        )

    # Step 4: runtime analysis (all models together)
    runtime_cfgs = [
        {"model_label": c["model_label"], "table_name": c["full_table"]}
        for c in model_configs
    ]
    results["runtime"] = run_runtime_analysis(runtime_cfgs)

    # Step 5: hallucination detection
    for cfg in model_configs:
        label = cfg["model_label"]
        results.setdefault(label, {})["hallucination"] = run_hallucination_detection(
            structured_table=cfg["full_table"],
            model_label=label,
        )

    # Cross-model summary
    summary_rows: list[dict] = []
    for label, res in results.items():
        if label == "runtime" or "metrics" not in res:
            continue
        overall = res["metrics"]["summaries"]["overall"]
        comp    = res.get("compliance", {}).get("summary", {})
        hall    = res.get("hallucination", {})
        text    = res.get("text", {})
        summary_rows.append({
            "model":                  label,
            "macro_f1":               overall["macro_f1"].values[0],
            "macro_precision":        overall["macro_precision"].values[0],
            "macro_recall":           overall["macro_recall"].values[0],
            "avg_exact_acc":          overall["avg_exact_acc"].values[0],
            "schema_compliant_pct":   comp.get("schema_compliant_pct"),
            "mean_required_coverage": comp.get("mean_required_coverage"),
            "hallucination_rate_pct": hall.get("hallucination_rate_pct"),
            "overall_cer":            text.get("overall_cer"),
            "overall_wer":            text.get("overall_wer"),
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv("cross_model_summary.csv", index=False)
        logger.info("Cross-model summary saved: cross_model_summary.csv")

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    GT_PATH = os.getenv("GT_PATH", "/data/NAR_metadata.json")

    MODEL_CONFIGS = [
        {
            "model_label": "qwen",
            "eval_table":  "structured_qwen_required",
            "full_table":  "structured_qwen",
        },
        {
            "model_label": "gemma",
            "eval_table":  "structured_gemma_required",
            "full_table":  "structured_gemma",
        },
        # Uncomment when MedGemma structuring runs are complete:
        # {
        #     "model_label": "medgemma",
        #     "eval_table":  "structured_medgemma_required",
        #     "full_table":  "structured_medgemma",
        # },
    ]

    run_full_metrics_suite(gt_path=GT_PATH, model_configs=MODEL_CONFIGS)