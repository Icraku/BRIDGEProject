"""
d_evaluation/field_accuracy.py
================================
Core accuracy utilities for the BRIDGE evaluation pipeline.

This module provides three things:

1. ``fuzzy_match`` / ``fuzzy_equal``
   Similarity-based comparison of two string values using ``SequenceMatcher``.
   Used everywhere a normalised string comparison is needed.

2. ``compute_accuracy``
   Quick field-level accuracy between a prediction dict and a ground-truth
   dict.  Used by the extraction pipeline for in-loop spot-checking.

3. ``build_accuracy_table``
   The main evaluation function.  Compares every field in every record and
   returns a tidy ``pd.DataFrame`` with one row per ``(record_id, field)``.
   All downstream metric modules (classification, text, hallucination) read
   from this table.

4. ``load_structured_outputs``
   Shared helper that loads structured text from any SurrealDB table.
   Centralised here so schema_compliance and hallucination_detector can both
   import it instead of each keeping a private copy.

Public API
----------
fuzzy_equal(a, b, threshold) -> bool
compute_accuracy(pred, truth) -> float
build_accuracy_table(predictions, ground_truth) -> pd.DataFrame
load_structured_outputs(table_name) -> dict[str, dict]
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher

import pandas as pd

from database_utils.db_utils import fetch_records
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import FULL_SCHEMA_FIELDS, inclusion_status

logger = logging.getLogger(__name__)

# Field types where accuracy scoring is not meaningful
_UNSCORABLE_TYPES: frozenset[str] = frozenset({"redacted", "text"})


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------


def fuzzy_equal(a: object, b: object, threshold: float = 0.85) -> bool:
    """Return ``True`` if the string similarity of *a* and *b* meets *threshold*.

    Parameters
    ----------
    a, b: Values to compare.  Both are coerced to ``str`` before comparison.
    threshold: Minimum ``SequenceMatcher`` ratio required to count as a match
        (default ``0.85``).

    Returns
    -------
    bool
    """
    return SequenceMatcher(None, str(a), str(b)).ratio() >= threshold


def fuzzy_match(a: object, b: object, threshold: float = 0.85) -> float:
    """Return ``1.0`` if *a* and *b* are similar enough, else ``0.0``.

    A thin wrapper around ``fuzzy_equal`` that returns a numeric score
    compatible with the ``correct?`` column in ``build_accuracy_table``.

    Returns ``0.0`` when either value is ``None`` or empty.
    """
    if a is None or b is None:
        return 0.0
    a_s, b_s = str(a).strip(), str(b).strip()
    if not a_s and not b_s:
        return 1.0  # both empty → both correct
    if not a_s or not b_s:
        return 0.0  # one empty → wrong
    return 1.0 if fuzzy_equal(a_s, b_s, threshold) else 0.0


# ---------------------------------------------------------------------------
# In-pipeline spot-check accuracy

def compute_accuracy(pred: dict, truth: dict) -> float:
    """Compute a simple field-level accuracy score between two dicts.

    Used by ``extraction_pipeline.py`` for quick in-loop accuracy estimation
    during development runs.  Not used by the formal evaluation suite.

    Parameters
    ----------
    pred: Predicted field-value dict from the VLM.
    truth: Ground-truth field-value dict.

    Returns
    -------
    float
        Fraction of truth fields correctly predicted (0.0 – 1.0).
        Returns ``0.0`` if either argument is not a dict or truth is empty.
    """
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return 0.0
    if not truth:
        return 0.0

    correct = sum(
        1
        for key, true_val in truth.items()
        if pred.get(key) is not None
        and (pred[key] == true_val or fuzzy_equal(pred[key], true_val))
    )
    return correct / len(truth)


# ---------------------------------------------------------------------------
# Shared DB loader

def load_structured_outputs(table_name: str) -> dict[str, dict]:
    """Load structured text records from a SurrealDB table.

    This function is the single authoritative loader for structured outputs.
    It is imported by ``run_evaluation``, ``schema_compliance``, and
    ``hallucination_detector`` to avoid code duplication.

    Parameters
    ----------
    table_name: SurrealDB table containing structured extraction records.

    Returns
    -------
    dict[str, dict]
        Mapping of ``record_id → structured_text dict``.
    """
    records = fetch_records(table_name)
    output: dict[str, dict] = {}
    for r in records:
        raw_id = r.get("id")
        if not raw_id:
            continue
        record_id = str(raw_id).split(":")[-1]
        structured = r.get("structured_text")
        if structured:
            output[record_id] = structured
    return output


# ---------------------------------------------------------------------------
# Core field-level helpers

def _normalize(value: object) -> str | None:
    """Collapse a value to a lowercase stripped string, or ``None`` if empty."""
    if value is None:
        return None
    cleaned = str(value).strip().lower().rstrip(";").strip()
    return cleaned if cleaned else None


def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a nested dict into dot-separated keys.

    Parameters
    ----------
    d: Nested dict to flatten.
    parent_key: Prefix accumulated so far (used in recursion).
    sep: Separator between key levels.

    Returns
    -------
    dict
        Flat ``{dotted.key: value}`` mapping.
    """
    items: dict = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items


def _compute_field_accuracy(pred: dict, truth: dict) -> dict[str, dict]:
    """Compare predicted vs ground-truth values for every known field.

    Iterates over the union of ``FULL_SCHEMA_FIELDS``, prediction keys and
    ground-truth keys.  Returns a per-field accuracy dict.

    Parameters
    ----------
    pred: Structured prediction dict (from the LLM).
    truth: Ground-truth dict for this record.

    Returns
    -------
    dict[str, dict]
        ``{field: {accuracy, ground_truth_val, predicted_val, has_gt, scorable}}``
        ``accuracy`` is ``None`` when ``has_gt`` is ``False`` or ``scorable``
        is ``False``.
    """
    pred_flat  = _flatten_dict(pred)
    truth_flat = _flatten_dict(truth)
    all_keys   = FULL_SCHEMA_FIELDS | set(pred_flat.keys()) | set(truth_flat.keys())

    results: dict[str, dict] = {}
    for key in all_keys:
        pred_val  = _normalize(pred_flat.get(key))
        truth_val = _normalize(truth_flat.get(key))

        has_gt   = key in truth_flat and truth_flat[key] not in (None, "", "null")
        ftype    = FIELD_TYPES.get(key, "unknown")
        scorable = ftype not in _UNSCORABLE_TYPES

        accuracy = fuzzy_match(pred_val, truth_val) if (has_gt and scorable) else None

        results[key] = {
            "accuracy":         accuracy,
            "ground_truth_val": truth_val,
            "predicted_val":    pred_val,
            "has_gt":           has_gt,
            "scorable":         scorable,
        }
    return results


# ---------------------------------------------------------------------------
# Public: build the main accuracy table

def build_accuracy_table(
    predictions: dict[str, dict],
    ground_truth: dict[str, dict],
) -> pd.DataFrame:
    """Build an accuracy DataFrame with one row per ``(record_id, field)``.

    This is the central data structure with all five evaluation
    modules (classification metrics, text metrics, schema compliance,
    runtime analysis, hallucination detection).

    Parameters
    ----------
    predictions: ``{record_id: structured_dict}`` — output of ``load_structured_outputs``.
    ground_truth: ``{record_id: gt_dict}`` — output of ``load_and_process_meta``.

    Returns
    -------
    pd.DataFrame
        Columns: ``record_id``, ``field``, ``field_type``, ``nar_inclusion``,
        ``correct?``, ``has_gt``, ``scorable``, ``ground_truth_val``,
        ``predicted_val``.

        ``correct?`` is a fuzzy accuracy score (0.0 or 1.0), or ``None``
        when the field has no ground truth or is an unscorable type
        (``text`` / ``redacted``).
    """
    rows: list[dict] = []

    for record_id, truth in ground_truth.items():
        pred = predictions.get(record_id)
        if pred is None:
            logger.warning("No prediction found for GT record: %s", record_id)
            continue

        for field, info in _compute_field_accuracy(pred, truth).items():
            rows.append({
                "record_id":        record_id,
                "field":            field,
                "field_type":       FIELD_TYPES.get(field, "unknown"),
                "nar_inclusion":    inclusion_status(field),
                "correct?":         info["accuracy"],
                "has_gt":           info["has_gt"],
                "scorable":         info["scorable"],
                "ground_truth_val": info["ground_truth_val"],
                "predicted_val":    info["predicted_val"],
            })

    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("build_accuracy_table: no rows produced — check predictions/GT overlap.")
        return df

    # Diagnostic summary
    scored      = df[df["scorable"] & df["has_gt"]]
    unscored_gt = df[~df["scorable"] & df["has_gt"]]
    no_gt       = df[~df["has_gt"]]

    logger.info(
        "build_accuracy_table: %d GT records | %d total rows | %d scored | %d unscorable with GT | %d no GT",
        len(ground_truth), len(df), len(scored), len(unscored_gt), len(no_gt),
    )
    logger.info(
        "Unique fields: %d total | %d included | %d supplementary",
        df["field"].nunique(),
        df[df["nar_inclusion"] == "included"]["field"].nunique(),
        df[df["nar_inclusion"] == "not included"]["field"].nunique(),
    )

    return df