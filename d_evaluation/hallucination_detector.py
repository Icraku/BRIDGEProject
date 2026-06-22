"""
d_evaluation/hallucination_detector.py
========================================
Detects hallucinated values: predictions that are non-empty but fall
outside the known valid value space for that field.

Three detection strategies
--------------------------
1. **Allowlist** — fields with a closed set of valid values (booleans, coded
   strings, severity levels, sex, blood group, etc.).  Any value outside the
   allowlist is flagged.
2. **Range** — numeric fields (``int``, ``float``) with physiologically
   plausible bounds.  Values outside the range are flagged.
3. **Format** — ``date`` and ``time`` fields validated by regex.  Values that
   do not match the expected format are flagged.

Fields of type ``"text"``, ``"redacted"``, or ``"unknown"`` are skipped
because they have an open vocabulary and cannot define an allowlist.

.. note::
    After the first real evaluation run, review ``hallucinations_{model}.csv``
    for false positives and extend ``ALLOWLISTS`` if needed.

Outputs
-------
``hallucinations_{model}.csv``
    Every flagged ``(record_id, field, raw_value, reason)`` triple.
``hallucination_summary_{model}.csv``
    Per-field hallucination rate with example values.
"""

from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

from d_evaluation.field_accuracy import load_structured_outputs
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import FULL_SCHEMA_FIELDS, inclusion_status

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Allowlists — extend after reviewing false positives

_BOOL_FIELDS: list[str] = [
    "was_resuscitated", "is_multiple_delivery", "born_before_arrival",
    "mum_has_anc_ultrasound", "has_fever", "passed_meconium",
    "has_difficulty_breathing", "passed_urine", "has_difficulty_feeding",
    "has_convulsions", "has_apnoea", "is_floppy", "has_vomiting", "has_diarhoea",
    "has_crackles", "has_grunting", "has_good_air_entry", "has_central_cyanosis",
    "chest_indrawing", "has_murmur", "has_bulging_fontanelle", "is_irritable",
    "is_distended", "has_birth_defects", "rbs_measured", "given_bilirubin",
    "given_vitamin_k", "given_bcg", "given_chlorhexidine", "given_prophylaxis_pmtct",
    "prescribed_transfusion", "prescribed_phototherapy", "prescribed_cpap",
    "prescribed_iv_fluids", "prescribed_antibiotics", "prescribed_feeds",
    "prescribed_opv", "prescribed_surfactant", "prescribed_caffeine_citrate",
    "prescribed_oxygen", "prescribed_kmc", "prescribed_incubator",
    "prolonged_labour",
]

_TRISTATE_FIELDS: list[str] = [
    "mum_had_vdrl", "mum_pmtct_status", "mum_on_arvs", "mum_had_hepatitis_b",
    "mum_given_HBIG_treatment", "mum_had_hypertension_in_pregnancy",
    "mum_had_antepartum_haemorrhage", "mum_had_diabetes", "rhesus",
]

_BOOL_VALID: set[str] = {
    "true", "false", "none", "null", "", "1", "0", "yes", "no", "y", "n",
}

_TRISTATE_VALID: set[str] = {
        "true", "false", "pos", "neg", "positive", "negative", "unkn", "unknown", "none", "null", "",
}

ALLOWLISTS: dict[str, set[str]] = {
    **{f: _BOOL_VALID    for f in _BOOL_FIELDS},
    **{f: _TRISTATE_VALID for f in _TRISTATE_FIELDS},
    "sex":           {"m", "f", "i", "male", "female", "indeterminate", ""},
    "blood_group":   {"a", "b", "ab", "o", "unknown", "unkn", "unk", ""},
    "delivery_type": {
        "svd", "cs", "c/s", "breach", "breech", "forceps", "vacuum",
        "normal", "svd cs", "cs svd", "",
    },
    "had_cs":              {
        "emergency", "elective", "emcs", "elcs",
        "emergency cs", "elective cs", "emergency c/s", "elective c/s", "",
    },
    "gestation_type":      {"us", "u/s", "lmp", "ultrasound", "us lmp", "lmp us", "u/s lmp", "lmp u/s", "unknown", "unkn", "unk", ""},
    "rapture_of_membrane": {
        "<18", "lt18", ">=18", "gte18", ">=18h", "<18h", "unknown", "unkn", "",
    },
    "given_anti_D_medication": {"y", "n", "yes", "no", "unknown", "unkn", "unk", "n/a", "",},
    "jaundice": {
        "none", "no", "+", "mild", "1+", "++", "moderate",
        "2+", "+++", "severe", "3+", "",
    },
    "pallor":                 {"none", "no", "+", "mild", "+++", "severe", ""},
    "xiphoid_retraction":     {"none", "mild", "severe", ""},
    "intercostal_retraction": {"none", "mild", "severe", ""},
    "appearance": {"well", "sick", "ill", "unwell", "dysmorphic", ""},
    "cry": {
        "normal", "normal/strong", "strong",
        "weak", "weak/absent", "weak / absent",
        "weak-absent", "absent", "hoarse", "",
    },
    "tone": {
        "normal", "increased", "reduced", "high", "low",
        "hypertonic", "hypotonic", "floppy", "",
    },
    "skin": {
        # Standard values
        "normal", "bruising", "bruised", "rash", "pustules", "mottling",
        "mottled", "dry", "peeling", "wrinkled",
        # Compound dry/peeling variants — all separator styles are valid
        "dry/peeling", "dry peeling", "dry-peeling",
        "dry/peeling/wrinkled", "dry peeling wrinkled", "dry-peeling-wrinkled",
        "dry/peeling-wrinkled", "dry-peeling/wrinkled",
        "",
    },
    "umbilicus": {
        # Standard values
        "clean", "clear",           # clear is a common synonym for clean
        "local pus", "localpus", "pus",
        "pus + red skin", "pus and red skin", "pus+red skin",
        "pus + redness", "pus with redness",
        "others", "other", "",
    },
    "rhesus": {
        # Standard tri-state
        "positive", "negative", "unknown", "unkn", "unk",
        "pos", "neg",
        # Short forms seen on forms
        "+", "-", "rh+", "rh-", "",
    },
}

# Physiologically plausible numeric ranges {field: (min, max)}
RANGES: dict[str, tuple[float, float]] = {
    "gestation_in_weeks":          (22,   44),
    "baby_age_in_days":            (0,    28),
    "apgar_1m":                    (0,    10),
    "apgar_5m":                    (0,    10),
    "apgar_10m":                   (0,    10),
    "birth_weight":                (300,  6000),
    "weight":                      (300,  6000),
    "head_circumference":          (20,   45),
    "length":                      (25,   60),
    "temparature":                 (34.0, 42.0),
    "respiratory_rate":            (10,   120),
    "pulse_rate":                  (40,   250),
    "pulse_oximetry":              (50,   100),
    "systolic_blood_pressure":     (30,   120),
    "diastolic_blood_pressure":    (10,   80),
    "capillary_refill_in_seconds": (0,    10),
    "rbs_value":                   (0.5,  30.0),
    "total_serum_bilirubin":       (0,    500),
    "mum_age_in_years":            (12,   60),
    "anc_visits":                  (0,    20),
    "parity_live":                 (0,    15),
    "parity_abortions":            (0,    10),
    "parity_total":                (0,    15),
    "multiple_delivery_num":       (1,    6),
}

_DATE_RE = re.compile(
    r"^\d{2}-\d{2}-\d{4}$|^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$"
)
_TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")

# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------


def _is_empty(value: object) -> bool:
    """Return ``True`` if *value* is semantically absent."""
    return value in (None, "", "none", "null", "n/a", "na") or (
        isinstance(value, float) and np.isnan(value)
    )


def detect_hallucination(field: str, raw_value: object) -> tuple[bool, str]:
    """Check a single field value against its allowlist / range / format.

    Parameters
    ----------
    field: Schema field name.
    raw_value: The value produced by the LLM for this field.

    Returns
    -------
    tuple[bool, str]
        ``(is_hallucination, reason)`` — reason is an empty string when not
        flagged.
    """
    if _is_empty(raw_value):
        return False, ""

    v = str(raw_value).strip().lower()
    ftype = FIELD_TYPES.get(field, "unknown")

    if ftype in ("text", "redacted", "unknown"):
        return False, ""

    # 1. Allowlist check
    if field in ALLOWLISTS:
        if v not in ALLOWLISTS[field]:
            return True, f"out_of_allowlist: {v!r}"
        return False, ""

    # 2. Range check
    if field in RANGES:
        lo, hi = RANGES[field]
        try:
            num = float(v)
            if not (lo <= num <= hi):
                return True, f"out_of_range: {num} not in [{lo}, {hi}]"
        except (ValueError, TypeError):
            if ftype in ("int", "float", "coded_int"):
                return True, f"non_numeric: {v!r}"
        return False, ""

    # 3. Format check — date
    if ftype == "date":
        if not _DATE_RE.match(v):
            return True, f"bad_date_format: {v!r}"
        return False, ""

    # 4. Format check — time
    if ftype == "time":
        if not _TIME_RE.match(v):
            return True, f"bad_time_format: {v!r}"
        return False, ""

    # 5. Bare type check for int/float not covered by a range
    if ftype in ("int", "coded_int"):
        try:
            int(float(v))
        except (ValueError, TypeError):
            return True, f"non_integer: {v!r}"

    if ftype == "float":
        try:
            float(v)
        except (ValueError, TypeError):
            return True, f"non_float: {v!r}"

    return False, ""


# ---------------------------------------------------------------------------
# Public API

def run_hallucination_detection(
    structured_table: str = "structured_qwen",
    model_label: str = "qwen",
) -> dict:
    """Scan all structured outputs for hallucinated values.

    Called by ``run_evaluation.run_full_metrics_suite``.

    Parameters
    ----------
    structured_table: SurrealDB table containing full 120-field structured outputs.
    model_label: Used for output CSV filenames.

    Returns
    -------
    dict with keys:
        ``row_df``, ``summary_df``, ``total_checked``,
        ``n_hallucinations``, ``hallucination_rate_pct``.
    """
    logger.info(
        "Hallucination detection: model=%s, table=%s", model_label, structured_table
    )

    predictions = load_structured_outputs(structured_table)
    logger.info("  Records loaded: %d", len(predictions))

    rows: list[dict] = []
    total_checked = 0

    for record_id, structured in predictions.items():
        for field in sorted(FULL_SCHEMA_FIELDS):
            ftype = FIELD_TYPES.get(field, "unknown")
            if ftype in ("text", "redacted", "unknown"):
                continue

            raw_value = structured.get(field)
            is_hall, reason = detect_hallucination(field, raw_value)
            total_checked += 1

            if is_hall:
                rows.append({
                    "record_id":     record_id,
                    "field":         field,
                    "field_type":    ftype,
                    "nar_inclusion": inclusion_status(field),
                    "raw_value":     str(raw_value)[:120],
                    "reason":        reason,
                })

    row_df = pd.DataFrame(rows)

    if row_df.empty:
        logger.info("  No hallucinations detected.")
        return {
            "row_df": row_df,
            "summary_df": pd.DataFrame(),
            "total_checked": total_checked,
            "n_hallucinations": 0,
            "hallucination_rate_pct": 0.0,
        }

    summary_df = (
        row_df.groupby(["field", "field_type", "nar_inclusion"])
        .agg(
            n_hallucinations   =("record_id", "count"),
            n_records_affected =("record_id", "nunique"),
            example_values     =("raw_value", lambda x: " | ".join(x.unique()[:3])),
            reasons            =("reason",    lambda x: " | ".join(x.unique()[:3])),
        )
        .reset_index()
        .sort_values("n_hallucinations", ascending=False)
    )

    hall_rate = (
        round(len(row_df) / total_checked * 100, 2) if total_checked > 0 else 0.0
    )

    logger.info(
        "  Checked: %d | Hallucinations: %d (%.2f%%) | Records affected: %d / %d",
        total_checked, len(row_df), hall_rate,
        row_df["record_id"].nunique(), len(predictions),
    )

    f1 = f"hallucinations_{model_label}.csv"
    f2 = f"hallucination_summary_{model_label}.csv"
    row_df.to_csv(f1, index=False)
    summary_df.to_csv(f2, index=False)
    logger.info("  Saved: %s, %s", f1, f2)

    return {
        "row_df":                 row_df,
        "summary_df":             summary_df,
        "total_checked":          total_checked,
        "n_hallucinations":       len(row_df),
        "hallucination_rate_pct": hall_rate,
    }