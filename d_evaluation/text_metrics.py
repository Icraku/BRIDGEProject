"""
d_evaluation/text_metrics.py
========================================
Character Error Rate (CER) and Word Error Rate (WER) for free-text fields.

This module evaluates text extraction quality by comparing predictions
against ground truth for rows where:
    - field_type == "text"
    - has_gt == True

Metrics
-------
CER = edit_distance(characters) / len(reference_characters)
WER = edit_distance(words) / len(reference_words)

.. note::
- Division by zero is handled by returning 0.0 when reference is empty.

Outputs
-------
``cer_wer_{model}.csv``
    Per (record_id, field) CER and WER scores.

``text_field_summary_{model}.csv``
    Aggregated mean metrics per field.
"""

import logging

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

try:
    from jiwer import cer, wer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    logger.warning("jiwer not installed — text metrics will be skipped. Run: pip install jiwer")


# ------------------------
# HELPERS

def _safe_str(v) -> str:
    """Normalise value to a plain string; treat None/null/nan as empty string."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip().lower()
    return s if s not in ("none", "null", "n/a", "na") else ""


def compute_cer(reference: str, hypothesis: str) -> float | None:
    if not JIWER_AVAILABLE:
        return None
    ref = _safe_str(reference)
    hyp = _safe_str(hypothesis)
    if not ref:
        return None          # no reference → undefined
    if not hyp:
        return 1.0           # full deletion
    try:
        return round(float(cer(ref, hyp)), 4)
    except Exception:
        return None


def compute_wer(reference: str, hypothesis: str) -> float | None:
    if not JIWER_AVAILABLE:
        return None
    ref = _safe_str(reference)
    hyp = _safe_str(hypothesis)
    if not ref:
        return None
    if not hyp:
        return 1.0
    try:
        return round(float(wer(ref, hyp)), 4)
    except Exception:
        return None


# ------------------------
# ROW-LEVEL COMPUTATION

def compute_text_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to text fields with GT and compute CER + WER per (record, field).

    Input : full DataFrame from build_accuracy_table().
    Output: DataFrame with columns
            record_id, field, nar_inclusion, ground_truth_val,
            predicted_val, cer, wer, gt_len_chars, gt_len_words
    """
    text_df = df[
        (df["field_type"] == "text") & (df["has_gt"])
    ].copy()

    if text_df.empty:
        logger.warning("  [text_metrics] No text fields with GT found.")
        return pd.DataFrame()

    # Use norm columns if available
    gt_col   = "norm_gt"   if "norm_gt"   in text_df.columns else "ground_truth_val"
    pred_col = "norm_pred" if "norm_pred" in text_df.columns else "predicted_val"

    text_df["cer"] = text_df.apply(
        lambda r: compute_cer(r[gt_col], r[pred_col]), axis=1
    )
    text_df["wer"] = text_df.apply(
        lambda r: compute_wer(r[gt_col], r[pred_col]), axis=1
    )

    # Reference lengths (for context in the paper)
    text_df["gt_len_chars"] = text_df[gt_col].apply(lambda v: len(_safe_str(v)))
    text_df["gt_len_words"] = text_df[gt_col].apply(
        lambda v: len(_safe_str(v).split()) if _safe_str(v) else 0
    )

    return text_df[[
        "record_id", "field", "nar_inclusion",
        "ground_truth_val", "predicted_val",
        "cer", "wer", "gt_len_chars", "gt_len_words",
    ]]


# ------------------------
# FIELD-LEVEL SUMMARY

def summarise_text_metrics(text_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate CER + WER per field, with counts and reference length context.
    """
    if text_df.empty:
        return pd.DataFrame()

    summary = (
        text_df.groupby(["field", "nar_inclusion"])
        .agg(
            n_records    = ("record_id", "nunique"),
            mean_cer     = ("cer",  lambda x: round(x.dropna().mean(), 4) if x.notna().any() else None),
            median_cer   = ("cer",  lambda x: round(x.dropna().median(), 4) if x.notna().any() else None),
            mean_wer     = ("wer",  lambda x: round(x.dropna().mean(), 4) if x.notna().any() else None),
            median_wer   = ("wer",  lambda x: round(x.dropna().median(), 4) if x.notna().any() else None),
            avg_gt_chars = ("gt_len_chars", "mean"),
            avg_gt_words = ("gt_len_words", "mean"),
        )
        .reset_index()
        .sort_values("mean_cer")
    )

    return summary


# ------------------------
# ENTRY POINT

def run_text_metrics(
    df: pd.DataFrame,
    model_label: str = "qwen",
) -> dict:
    """
    Main entry point called from run_evaluation.py.

    Returns dict with keys: row_df, summary_df, file paths written.
    """
    logger.info("\n" + "=" * 60)
    logger.info(f"  TEXT METRICS (CER + WER) — {model_label.upper()}")
    logger.info("=" * 60)

    if not JIWER_AVAILABLE:
        logger.warning("Skipped — install jiwer first: pip install jiwer")
        return {}

    row_df     = compute_text_metrics(df)
    summary_df = summarise_text_metrics(row_df)

    if summary_df.empty:
        logger.warning("No text fields with ground truth — nothing to score.")
        return {}

    logger.info(f"\nText fields with GT: {summary_df['field'].nunique()}")
    logger.info(f"Records scored     : {row_df['record_id'].nunique()}")
    logger.info("\nPer-field CER / WER:")
    logger.info("\n" + summary_df.to_string(index=False))

    overall_cer = round(row_df["cer"].dropna().mean(), 4)
    overall_wer = round(row_df["wer"].dropna().mean(), 4)
    logger.info(f"\nOverall mean CER: {overall_cer}")
    logger.info(f"Overall mean WER: {overall_wer}")

    f1 = f"cer_wer_{model_label}.csv"
    f2 = f"text_field_summary_{model_label}.csv"
    row_df.to_csv(f1, index=False)
    summary_df.to_csv(f2, index=False)
    logger.info(f"\nSaved: {f1}, {f2}")

    return {
        "row_df":     row_df,
        "summary_df": summary_df,
        "overall_cer": overall_cer,
        "overall_wer": overall_wer,
    }