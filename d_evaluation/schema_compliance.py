"""
d_evaluation/schema_compliance.py
===================================
Checks every structured output record against ``NARFullRecord`` for:

1. **Field coverage** — fraction of expected fields that are present (not
   ``None`` / ``null``).
2. **Type compliance** — does each value match its declared ``field_type``?
3. **Schema compliance** — a record passes when required-field coverage ≥ 80 %
   AND type errors = 0.

Does **not** need ground truth — reads directly from a structured DB table.

Outputs
-------
``compliance_report_{model}.csv``
    Per-record field coverage, required coverage, and type compliance.
``compliance_summary_{model}.csv``
    Per-field presence rate across all records.
"""

from __future__ import annotations

import logging
import re

import pandas as pd

from d_evaluation.field_accuracy import load_structured_outputs
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import (
    FULL_SCHEMA_FIELDS,
    NAR_REQUIRED_FIELDS,
    inclusion_status,
)

logger = logging.getLogger(__name__)

_EMPTY_VALUES: frozenset = frozenset({None, "", "null", "none", "n/a"})

# ---------------------------------------------------------------------------
# Type validators
# ---------------------------------------------------------------------------

_DATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),
]
_TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
_BOOL_VALID: frozenset[str] = frozenset(
    {"true", "false", "1", "0", "yes", "no", "y", "n", "null"}
)


def _is_valid_type(value: object, field_type: str) -> bool | None:
    """Check whether *value* matches the expected *field_type*.

    Returns
    -------
    True
        Value is present and passes the type check.
    False
        Value is present but fails the type check.
    None
        Value is absent — not a type error, just missing.
    """
    if value in _EMPTY_VALUES:
        return None

    s = str(value).strip()

    if field_type == "bool":
        return s.lower() in _BOOL_VALID

    if field_type in ("int", "coded_int"):
        try:
            int(float(s))
            return True
        except (ValueError, TypeError):
            return False

    if field_type == "float":
        try:
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    if field_type == "date":
        return any(p.match(s) for p in _DATE_PATTERNS)

    if field_type == "time":
        return bool(_TIME_PATTERN.match(s))

    # str, text, redacted — any non-empty string is valid
    return True


# ---------------------------------------------------------------------------
# Per-record compliance check
# ---------------------------------------------------------------------------


def _check_record_compliance(record_id: str, structured: dict) -> dict:
    """Evaluate one structured record against the full schema.

    Parameters
    ----------
    record_id: Identifier for logging.
    structured: ``structured_text`` dict from SurrealDB.

    Returns
    -------
    dict
        Per-record summary plus a ``field_detail`` list for the field-level
        DataFrame.
    """
    n_expected  = len(FULL_SCHEMA_FIELDS)
    n_required  = len(NAR_REQUIRED_FIELDS)

    field_detail: list[dict] = []
    n_present      = 0
    n_req_present  = 0
    n_type_errors  = 0
    n_type_checked = 0

    for field in sorted(FULL_SCHEMA_FIELDS):
        ftype   = FIELD_TYPES.get(field, "unknown")
        inc     = inclusion_status(field)
        value   = structured.get(field)
        present = value not in _EMPTY_VALUES

        if present:
            n_present += 1
            if inc == "included":
                n_req_present += 1

        type_ok: bool | None = None
        if present and ftype not in ("redacted", "text", "unknown"):
            type_ok = _is_valid_type(value, ftype)
            n_type_checked += 1
            if type_ok is False:
                n_type_errors += 1

        field_detail.append({
            "field":         field,
            "field_type":    ftype,
            "nar_inclusion": inc,
            "value_present": present,
            "raw_value":     str(value)[:80] if value is not None else "",
            "type_valid":    type_ok,
        })

    coverage_pct     = round(n_present     / n_expected * 100, 2)
    req_coverage_pct = round(n_req_present / n_required * 100, 2)
    type_compliance  = (
        round((n_type_checked - n_type_errors) / n_type_checked * 100, 2)
        if n_type_checked > 0 else 100.0
    )
    schema_compliant = (n_type_errors == 0 and req_coverage_pct >= 80.0)

    return {
        "record_id":              record_id,
        "json_valid":             True,
        "n_fields_expected":      n_expected,
        "n_fields_present":       n_present,
        "n_required_present":     n_req_present,
        "field_coverage_pct":     coverage_pct,
        "required_coverage_pct":  req_coverage_pct,
        "n_type_checked":         n_type_checked,
        "n_type_errors":          n_type_errors,
        "type_compliance_pct":    type_compliance,
        "schema_compliant":       schema_compliant,
        "field_detail":           field_detail,
    }


# ---------------------------------------------------------------------------
# Public API

def run_schema_compliance(
    structured_table: str = "structured_qwen",
    model_label: str = "qwen",
) -> dict:
    """Check schema compliance for all records in *structured_table*.

    Called by ``evaluation_pipeline.run_full_metrics_suite``.

    Parameters
    ----------
    structured_table: SurrealDB table containing full 120-field structured outputs.
    model_label: Used for output CSV filenames.

    Returns
    -------
    dict with keys ``record_df``, ``field_df``, ``summary``.
    """
    logger.info(
        "Schema compliance: model=%s, table=%s", model_label, structured_table
    )

    predictions = load_structured_outputs(structured_table)
    logger.info("  Records loaded: %d", len(predictions))

    record_rows: list[dict] = []
    field_rows:  list[dict] = []

    for record_id, structured in predictions.items():
        result = _check_record_compliance(record_id, structured)
        record_rows.append({k: v for k, v in result.items() if k != "field_detail"})
        for fd in result["field_detail"]:
            field_rows.append({"record_id": record_id, **fd})

    record_df = pd.DataFrame(record_rows)
    field_df  = pd.DataFrame(field_rows)

    if record_df.empty:
        logger.warning("  No records found in %s.", structured_table)
        return {"record_df": record_df, "field_df": field_df, "summary": {}}

    compliant_n   = int(record_df["schema_compliant"].sum())
    compliant_pct = round(record_df["schema_compliant"].mean() * 100, 1)

    logger.info(
        "  Schema compliant: %d / %d (%.1f%%) | "
        "Mean required coverage: %.1f%% | Mean type compliance: %.1f%%",
        compliant_n, len(record_df), compliant_pct,
        record_df["required_coverage_pct"].mean(),
        record_df["type_compliance_pct"].mean(),
    )

    presence_summary = (
        field_df.groupby(["field", "field_type", "nar_inclusion"])["value_present"]
        .mean()
        .mul(100)
        .round(1)
        .reset_index()
        .rename(columns={"value_present": "presence_pct"})
        .sort_values("presence_pct")
    )

    type_errors = (
        field_df[field_df["type_valid"] == False]
        .groupby("field")["record_id"]
        .count()
        .reset_index()
        .rename(columns={"record_id": "n_type_errors"})
        .sort_values("n_type_errors", ascending=False)
    )

    sparse = presence_summary[presence_summary["presence_pct"] < 50]
    if not sparse.empty:
        logger.info(
            "  Fields with < 50%% presence (%d): %s",
            len(sparse), sparse["field"].tolist(),
        )
    if not type_errors.empty:
        logger.info(
            "  Fields with type errors (%d): %s",
            len(type_errors), type_errors["field"].tolist(),
        )

    summary = {
        "n_records":              len(record_df),
        "schema_compliant_n":     compliant_n,
        "schema_compliant_pct":   compliant_pct,
        "mean_field_coverage":    round(record_df["field_coverage_pct"].mean(), 1),
        "mean_required_coverage": round(record_df["required_coverage_pct"].mean(), 1),
        "mean_type_compliance":   round(record_df["type_compliance_pct"].mean(), 1),
    }

    f1 = f"compliance_report_{model_label}.csv"
    f2 = f"compliance_summary_{model_label}.csv"
    record_df.to_csv(f1, index=False)
    presence_summary.to_csv(f2, index=False)
    logger.info("  Saved: %s, %s", f1, f2)

    return {"record_df": record_df, "field_df": field_df, "summary": summary}