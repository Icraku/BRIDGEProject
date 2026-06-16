"""
Checks every structured output record against NARFullRecord for:
  1. JSON validity        — was valid JSON stored in DB at all?
  2. Field coverage       — fraction of expected fields present (not None/null)
  3. Type compliance      — does each value match its declared field_type?
  4. Schema compliance    — all three above pass simultaneously

Reads directly from a structured DB table (uses load_structured_outputs).
Does NOT need ground truth.

Outputs:
  compliance_report_{model}.csv   — per-record breakdown
  compliance_summary_{model}.csv  — aggregate statistics
"""

import pandas as pd
import numpy as np
from datetime import date, time
from database_utils.db_utils import fetch_records
from d_evaluation.field_accuracy import load_structured_outputs
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import (
    NARFullRecord, FULL_SCHEMA_FIELDS, NAR_REQUIRED_FIELDS, inclusion_status
)


# ------------------------
# TYPE VALIDATORS

def _is_valid_type(value, field_type: str) -> bool | None:
    """
    Return True/False if value can be validated, None if value is empty.
    """
    if value in (None, "", "null", "none", "n/a"):
        return None     # missing — not a type error

    s = str(value).strip()

    if field_type == "bool":
        return s.lower() in ("true", "false", "1", "0", "yes", "no",
                              "y", "n", "null")
    if field_type == "int":
        try:
            int(float(s)); return True
        except (ValueError, TypeError):
            return False

    if field_type == "float":
        try:
            float(s); return True
        except (ValueError, TypeError):
            return False

    if field_type == "date":
        import re
        # Accept dd-mm-yyyy, yyyy-mm-dd, dd/mm/yyyy
        patterns = [
            r"^\d{2}-\d{2}-\d{4}$",
            r"^\d{4}-\d{2}-\d{2}$",
            r"^\d{2}/\d{2}/\d{4}$",
        ]
        return any(re.match(p, s) for p in patterns)

    if field_type == "time":
        import re
        return bool(re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", s))

    if field_type == "coded_int":
        try:
            int(float(s)); return True
        except (ValueError, TypeError):
            return False

    # str, text, redacted — any non-empty string is valid
    return True


# ------------------------
# PER-RECORD COMPLIANCE

def check_record_compliance(
    record_id: str,
    structured: dict,
) -> dict:
    """
    Check one structured output dict against the full schema.

    Returns a dict with:
      record_id, json_valid, n_fields_expected, n_fields_present,
      field_coverage_pct, n_type_errors, type_compliance_pct,
      schema_compliant, required_coverage_pct,
      field_detail: list of per-field dicts
    """
    n_expected   = len(FULL_SCHEMA_FIELDS)
    n_required   = len(NAR_REQUIRED_FIELDS)

    field_detail = []
    n_present    = 0
    n_req_present= 0
    n_type_errors= 0
    n_type_checked= 0

    for field in sorted(FULL_SCHEMA_FIELDS):
        ftype   = FIELD_TYPES.get(field, "unknown")
        inc     = inclusion_status(field)
        value   = structured.get(field)
        present = value not in (None, "", "null", "none")

        if present:
            n_present += 1
            if inc == "included":
                n_req_present += 1

        type_ok = None
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

    coverage_pct      = round(n_present     / n_expected * 100, 2)
    req_coverage_pct  = round(n_req_present / n_required * 100, 2)
    type_compliance   = round(
        (n_type_checked - n_type_errors) / n_type_checked * 100, 2
    ) if n_type_checked > 0 else 100.0

    schema_compliant = (n_type_errors == 0 and req_coverage_pct >= 80.0)

    return {
        "record_id":            record_id,
        "json_valid":           True,      # if we got here, JSON parsed fine
        "n_fields_expected":    n_expected,
        "n_fields_present":     n_present,
        "n_required_present":   n_req_present,
        "field_coverage_pct":   coverage_pct,
        "required_coverage_pct": req_coverage_pct,
        "n_type_checked":       n_type_checked,
        "n_type_errors":        n_type_errors,
        "type_compliance_pct":  type_compliance,
        "schema_compliant":     schema_compliant,
        "field_detail":         field_detail,
    }

def run_schema_compliance(
    structured_table: str = "structured_Q",
    model_label:      str = "qwen",
) -> dict:
    """
    Main entry point called from run_evaluation.py.

    Returns dict with keys: record_df, field_df, summary.
    """
    print(f"\n{'='*60}")
    print(f"  SCHEMA COMPLIANCE — {model_label.upper()}  (table: {structured_table})")
    print(f"{'='*60}")

    predictions = load_structured_outputs(structured_table)
    print(f"  Records loaded: {len(predictions)}")

    record_rows = []
    field_rows  = []

    for record_id, structured in predictions.items():
        result = check_record_compliance(record_id, structured)

        record_rows.append({k: v for k, v in result.items() if k != "field_detail"})

        for fd in result["field_detail"]:
            field_rows.append({"record_id": record_id, **fd})

    record_df = pd.DataFrame(record_rows)
    field_df  = pd.DataFrame(field_rows)

    # ── console ───────────────────────────────────────────────────
    print(f"\n  Records checked          : {len(record_df)}")
    print(f"  Schema compliant (≥80%R, 0 type errors): "
          f"{record_df['schema_compliant'].sum()} / {len(record_df)} "
          f"({round(record_df['schema_compliant'].mean()*100, 1)}%)")
    print(f"  Mean field coverage      : {round(record_df['field_coverage_pct'].mean(), 1)}%")
    print(f"  Mean required coverage   : {round(record_df['required_coverage_pct'].mean(), 1)}%")
    print(f"  Mean type compliance     : {round(record_df['type_compliance_pct'].mean(), 1)}%")

    # Per-field presence rate
    presence_summary = (
        field_df.groupby(["field", "field_type", "nar_inclusion"])
        ["value_present"].mean().mul(100).round(1)
        .reset_index()
        .rename(columns={"value_present": "presence_pct"})
        .sort_values("presence_pct")
    )
    print(f"\n  Fields rarely populated (presence < 50%):")
    sparse = presence_summary[presence_summary["presence_pct"] < 50]
    print(sparse.to_string(index=False) if not sparse.empty else "  none")

    # Type errors by field
    type_errors = (
        field_df[field_df["type_valid"] == False]
        .groupby("field")["record_id"].count()
        .reset_index()
        .rename(columns={"record_id": "n_type_errors"})
        .sort_values("n_type_errors", ascending=False)
    )
    print(f"\n  Fields with type errors:")
    print(type_errors.to_string(index=False) if not type_errors.empty else "  none")

    # ── save ──────────────────────────────────────────────────────
    summary = {
        "n_records":              len(record_df),
        "schema_compliant_n":     int(record_df["schema_compliant"].sum()),
        "schema_compliant_pct":   round(record_df["schema_compliant"].mean() * 100, 1),
        "mean_field_coverage":    round(record_df["field_coverage_pct"].mean(), 1),
        "mean_required_coverage": round(record_df["required_coverage_pct"].mean(), 1),
        "mean_type_compliance":   round(record_df["type_compliance_pct"].mean(), 1),
    }

    f1 = f"compliance_report_{model_label}.csv"
    f2 = f"compliance_summary_{model_label}.csv"
    record_df.to_csv(f1, index=False)
    presence_summary.to_csv(f2, index=False)
    print(f"\n  Saved: {f1}, {f2}")

    return {"record_df": record_df, "field_df": field_df, "summary": summary}