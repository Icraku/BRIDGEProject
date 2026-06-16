"""
Detects hallucinated values: predictions that are non-empty but fall
outside the known valid value space for that field.

Three detection strategies:
  1. ALLOWLIST   — field has a closed set of valid values (bool, coded str,
                   severity, sex, blood_group, etc.). Any value outside this
                   set is a hallucination.
  2. RANGE       — numeric fields (int, float) with physiologically plausible
                   bounds. Values outside the range are flagged.
  3. FORMAT      — date/time fields validated by regex. Malformed = hallucinated.

Fields of type "text", "redacted", or "unknown" are skipped
(open vocabulary — cannot define an allowlist).

Outputs:
  hallucinations_{model}.csv       — every flagged (record, field, value)
  hallucination_summary_{model}.csv — per-field hallucination rate
"""

import re
import pandas as pd
import numpy as np
from d_evaluation.field_accuracy import load_structured_outputs
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import FULL_SCHEMA_FIELDS, inclusion_status


# ------------------------------------------------------------------ #
# ALLOWLISTS — extend as more GT data is collected                    #
# ------------------------------------------------------------------ #

ALLOWLISTS: dict[str, set] = {
    # bool fields — only these string representations are valid
    **{f: {"true", "false", "none", "null", "", "1", "0", "yes", "no", "y", "n"}
       for f in [
           "was_resuscitated","is_multiple_delivery","born_before_arrival",
           "mum_has_anc_ultrasound","has_fever","passed_meconium",
           "has_difficulty_breathing","passed_urine","has_difficulty_feeding",
           "has_convulsions","has_apnoea","is_floppy","has_vomiting","has_diarhoea",
           "has_crackles","has_grunting","has_good_air_entry","has_central_cyanosis",
           "chest_indrawing","has_murmur","has_bulging_fontanelle","is_irritable",
           "is_distended","has_birth_defects","rbs_measured","given_bilirubin",
           "given_vitamin_k","given_bcg","given_chlorhexidine","given_prophylaxis_pmtct",
           "prescribed_transfusion","prescribed_phototherapy","prescribed_cpap",
           "prescribed_iv_fluids","prescribed_antibiotics","prescribed_feeds",
           "prescribed_opv","prescribed_surfactant","prescribed_caffeine_citrate",
           "prescribed_oxygen","prescribed_kmc","prescribed_incubator",
           "prolonged_labour",
       ]},
    # tri-state fields
    **{f: {"true","false","pos","neg","positive","negative","unkn","unknown","none","null",""}
       for f in [
           "mum_had_vdrl","mum_pmtct_status","mum_on_arvs","mum_had_hepatitis_b",
           "mum_given_HBIG_treatment","mum_had_hypertension_in_pregnancy",
           "mum_had_antepartum_haemorrhage","mum_had_diabetes","rhesus",
       ]},
    "sex":          {"m","f","i","male","female","indeterminate",""},
    "blood_group":  {"a","b","ab","o","unknown","unkn",""},
    "delivery_type":{"svd","cs","c/s","breach","breech","forceps","vacuum",
                     "normal","svd cs","cs svd",""},
    "had_cs":       {"emergency","elective","emcs","elcs",""},
    "gestation_type":{"us","u/s","lmp","ultrasound","us lmp","lmp us",""},
    "rapture_of_membrane":{"<18","lt18",">=18","gte18",">=18h","<18h",
                            "unknown","unkn",""},
    "given_anti_D_medication":{"y","n","yes","no",""},
    "jaundice":     {"none","no","+","mild","1+","++","moderate","2+",
                     "+++","severe","3+",""},
    "pallor":       {"none","no","+","mild","+++","severe",""},
    "xiphoid_retraction":   {"none","mild","severe",""},
    "intercostal_retraction":{"none","mild","severe",""},
    "appearance":   {"well","sick","ill","unwell","dysmorphic",""},
    "cry":          {"normal","weak","weak/absent","weak / absent",
                     "weak-absent","absent","hoarse",""},
    "tone":         {"normal","increased","reduced","high","low",
                     "hypertonic","hypotonic","floppy",""},
    "skin":         {"normal","bruising","bruised","rash","pustules",
                     "mottling","mottled","dry","peeling","wrinkled",
                     "dry/peeling","dry peeling","dry-peeling",""},
    "umbilicus":    {"clean","local pus","localpus","pus","pus + red skin",
                     "pus and red skin","pus+red skin","others","other",""},
}

# Plausible numeric ranges  {field: (min, max)}
RANGES: dict[str, tuple] = {
    "gestation_in_weeks":       (22,  44),
    "baby_age_in_days":         (0,   28),
    "apgar_1m":                 (0,   10),
    "apgar_5m":                 (0,   10),
    "apgar_10m":                (0,   10),
    "birth_weight":             (300, 6000),
    "weight":                   (300, 6000),
    "head_circumference":       (20,  45),
    "length":                   (25,  60),
    "temparature":              (34.0,42.0),
    "respiratory_rate":         (10,  120),
    "pulse_rate":               (40,  250),
    "pulse_oximetry":           (50,  100),
    "systolic_blood_pressure":  (30,  120),
    "diastolic_blood_pressure": (10,  80),
    "capillary_refill_in_seconds": (0, 10),
    "rbs_value":                (0.5, 30.0),
    "total_serum_bilirubin":    (0,   500),
    "mum_age_in_years":         (12,  60),
    "anc_visits":               (0,   20),
    "parity_live":              (0,   15),
    "parity_abortions":         (0,   10),
    "parity_total":             (0,   15),
    "multiple_delivery_num":    (1,   6),
}

DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$|^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


# ------------------------------------------------------------------ #
# DETECTION LOGIC                                                      #
# ------------------------------------------------------------------ #

def _is_empty(v) -> bool:
    return v in (None, "", "none", "null", "n/a", "na") or (
        isinstance(v, float) and np.isnan(v)
    )


def detect_hallucination(field: str, raw_value) -> tuple[bool, str]:
    """
    Returns (is_hallucination, reason).
    """
    if _is_empty(raw_value):
        return False, ""

    v = str(raw_value).strip().lower()
    ftype = FIELD_TYPES.get(field, "unknown")

    # Skip open-vocabulary fields
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

    # 3. Format check
    if ftype == "date":
        if not DATE_RE.match(v):
            return True, f"bad_date_format: {v!r}"
        return False, ""

    if ftype == "time":
        if not TIME_RE.match(v):
            return True, f"bad_time_format: {v!r}"
        return False, ""

    # 4. Bare type check for int/float not covered by range
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


def run_hallucination_detection(
    structured_table: str = "structured_Q",
    model_label:      str = "qwen",
) -> dict:
    """
    Main entry point called from run_evaluation.py.

    Returns dict with keys: row_df, summary_df.
    """
    print(f"\n{'='*60}")
    print(f"  HALLUCINATION DETECTION — {model_label.upper()}  (table: {structured_table})")
    print(f"{'='*60}")

    predictions = load_structured_outputs(structured_table)
    print(f"  Records loaded: {len(predictions)}")

    rows = []
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
        print("  No hallucinations detected.")
        return {"row_df": row_df, "summary_df": pd.DataFrame()}

    # Per-field summary
    summary_df = (
        row_df.groupby(["field", "field_type", "nar_inclusion"])
        .agg(
            n_hallucinations = ("record_id", "count"),
            n_records_affected = ("record_id", "nunique"),
            example_values = ("raw_value", lambda x: " | ".join(x.unique()[:3])),
            reasons = ("reason", lambda x: " | ".join(x.unique()[:3])),
        )
        .reset_index()
        .sort_values("n_hallucinations", ascending=False)
    )

    total_records = len(predictions)
    hall_rate = round(len(row_df) / total_checked * 100, 2) if total_checked > 0 else 0

    print(f"\n  Total field-values checked : {total_checked}")
    print(f"  Hallucinations detected    : {len(row_df)} ({hall_rate}%)")
    print(f"  Records affected           : {row_df['record_id'].nunique()} / {total_records}")
    print(f"\n  Top hallucinated fields:")
    print(summary_df.head(15).to_string(index=False))

    # By field type
    by_type = (
        row_df.groupby("field_type")["record_id"]
        .count().reset_index()
        .rename(columns={"record_id": "n_hallucinations"})
        .sort_values("n_hallucinations", ascending=False)
    )
    print(f"\n  Hallucinations by field type:")
    print(by_type.to_string(index=False))

    # By inclusion
    by_inc = (
        row_df.groupby("nar_inclusion")["record_id"]
        .count().reset_index()
        .rename(columns={"record_id": "n_hallucinations"})
    )
    print(f"\n  Hallucinations by NAR inclusion:")
    print(by_inc.to_string(index=False))

    f1 = f"hallucinations_{model_label}.csv"
    f2 = f"hallucination_summary_{model_label}.csv"
    row_df.to_csv(f1, index=False)
    summary_df.to_csv(f2, index=False)
    print(f"\n  Saved: {f1}, {f2}")

    return {
        "row_df":     row_df,
        "summary_df": summary_df,
        "total_checked":    total_checked,
        "n_hallucinations": len(row_df),
        "hallucination_rate_pct": hall_rate,
    }