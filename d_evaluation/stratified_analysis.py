"""
d_evaluation/stratified_analysis.py
=====================================
Produces three stratified accuracy comparison tables for the thesis:

1. **By field type**    — accuracy broken down by bool / int / str / float / date / time
2. **By facility**      — accuracy per hospital, decoded from the record ID prefix
3. **By scan period**   — accuracy per month/quarter, from admission_date in structured output

All three tables are derived from CSVs already produced by the main pipeline
(``field_accuracy_{model}.csv``) and from the structured DB table.  No
re-running of the LLM is needed.

Usage
-----
Run after ``main.py`` has completed at least one model:

    python d_evaluation/stratified_analysis.py

Or import and call directly:

    from d_evaluation.stratified_analysis import run_stratified_analysis
    run_stratified_analysis(model_label="qwen")

Outputs (saved to working directory)
--------------------------------------
``table1_by_field_type_{model}.csv``
    Mean accuracy, F1 proxy, and record count per field type.
``table2_by_facility_{model}.csv``
    Mean accuracy per hospital, with facility name and record count.
``table3_by_scan_period_{model}.csv``
    Mean accuracy per month (and per quarter) across the date range.
``table_combined_{model}.csv``
    All three tables stacked, suitable for a single thesis appendix table.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from database_utils.db_utils import fetch_records
from schemas.neonatal_admission_form.field_types import HOSPITAL_CODES, decode_hospital

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hospital code → readable name
# ---------------------------------------------------------------------------
# Edit these display names to match the anonymised facility labels in your
# thesis (e.g. "Facility A", "Facility B") if required by ethics approval.

FACILITY_LABELS: dict[int, str] = {
    2:  "Facility 2  (NAR_52000)",
    3:  "Facility 3  (NAR_53000)",
    4:  "Facility 4  (NAR_7200)",
    5:  "Facility 5  (NAR_41000)",
    6:  "Facility 6  (NAR_40000)",
    7:  "Facility 7  (NAR_63000)",
    8:  "Facility 8  (NAR_76000)",
    17: "Facility 17 (NAR_1700000)",
}


def _decode_facility_from_record_id(record_id: str) -> str:
    """Return a human-readable facility label from a NAR record ID.

    Uses the numeric prefix in the record ID to match ``HOSPITAL_CODES``.
    Falls back to ``"Unknown"`` if the prefix is not recognised.
    """
    for code, prefix in HOSPITAL_CODES.items():
        # record_id looks like "NAR_40000015" — prefix is "NAR_40000"
        if record_id.startswith(prefix):
            return FACILITY_LABELS.get(code, f"Facility {code}")
    return "Unknown"


# ---------------------------------------------------------------------------
# Load admission dates from the structured DB table

def _load_admission_dates(structured_table: str) -> dict[str, str | None]:
    """Fetch ``admission_date`` for every record from the structured DB table.

    Returns
    -------
    dict[str, str | None]
        ``{record_id: admission_date_string}``  (date may be ``None`` if missing)
    """
    records = fetch_records(structured_table)
    dates: dict[str, str | None] = {}
    for r in records:
        raw_id = r.get("id")
        if not raw_id:
            continue
        record_id = str(raw_id).split(":")[-1]
        structured = r.get("structured_text") or {}
        dates[record_id] = structured.get("admission_date")
    return dates


# ---------------------------------------------------------------------------
# Table 1: accuracy by field type

def table_by_field_type(df: pd.DataFrame, model_label: str) -> pd.DataFrame:
    """Compute mean accuracy, record count and field count per field type.

    Only scored rows (``has_gt=True`` and ``scorable=True``) are included.

    Parameters
    ----------
    df: Full accuracy DataFrame from ``field_accuracy_{model}.csv``.
    model_label: Used for the ``model`` column in the output.

    Returns
    -------
    pd.DataFrame
        One row per field type, sorted by mean accuracy descending.
    """
    scored = df[df["scorable"] & df["has_gt"]].copy()
    scored["correct?"] = pd.to_numeric(scored["correct?"], errors="coerce")

    summary = (
        scored.groupby("field_type")
        .agg(
            n_records    =("record_id", "nunique"),
            n_fields     =("field",     "nunique"),
            n_observations=("correct?", "count"),
            mean_accuracy=("correct?",  "mean"),
            std_accuracy =("correct?",  "std"),
        )
        .reset_index()
    )
    summary["mean_accuracy"] = summary["mean_accuracy"].round(3)
    summary["std_accuracy"]  = summary["std_accuracy"].round(3)
    summary["model"]         = model_label
    summary = summary.sort_values("mean_accuracy", ascending=False)

    logger.info("Table 1 (field type): %d rows", len(summary))
    return summary


# ---------------------------------------------------------------------------
# Table 2: accuracy by facility

def table_by_facility(df: pd.DataFrame, model_label: str) -> pd.DataFrame:
    """Compute mean accuracy per hospital facility.

    Facility is decoded from the record ID prefix using ``HOSPITAL_CODES``.

    Parameters
    ----------
    df: Full accuracy DataFrame.
    model_label: Used for the ``model`` column.

    Returns
    -------
    pd.DataFrame
        One row per facility, sorted by mean accuracy descending.
    """
    scored = df[df["scorable"] & df["has_gt"]].copy()
    scored["correct?"] = pd.to_numeric(scored["correct?"], errors="coerce")

    scored["facility"] = scored["record_id"].apply(_decode_facility_from_record_id)

    summary = (
        scored.groupby("facility")
        .agg(
            n_records     =("record_id", "nunique"),
            n_observations=("correct?",  "count"),
            mean_accuracy =("correct?",  "mean"),
            std_accuracy  =("correct?",  "std"),
        )
        .reset_index()
    )
    summary["mean_accuracy"] = summary["mean_accuracy"].round(3)
    summary["std_accuracy"]  = summary["std_accuracy"].round(3)
    summary["model"]         = model_label
    summary = summary.sort_values("mean_accuracy", ascending=False)

    logger.info("Table 2 (facility): %d facilities", len(summary))
    return summary


# ---------------------------------------------------------------------------
# Table 3: accuracy by scan period (month / quarter)

def table_by_scan_period(
    df: pd.DataFrame,
    admission_dates: dict[str, str | None],
    model_label: str,
) -> pd.DataFrame:
    """Compute mean accuracy per admission month and quarter.

    Records with no parseable ``admission_date`` are grouped under
    ``"Unknown period"`` so they are not silently dropped.

    Parameters
    ----------
    df: Full accuracy DataFrame.
    admission_dates: ``{record_id: date_string}`` from ``_load_admission_dates``.
    model_label: Used for the ``model`` column.

    Returns
    -------
    pd.DataFrame
        One row per month, with a ``quarter`` column for rollup.
        Sorted chronologically.
    """
    scored = df[df["scorable"] & df["has_gt"]].copy()
    scored["correct?"] = pd.to_numeric(scored["correct?"], errors="coerce")

    # Attach admission date to every row
    scored["admission_date_raw"] = scored["record_id"].map(admission_dates)

    # Parse dates — try the dd-mm-yyyy format used by clean_for_db, then ISO
    def _parse(val: str | None) -> pd.Timestamp | None:
        if not val:
            return None
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return pd.to_datetime(val, format=fmt)
            except (ValueError, TypeError):
                continue
        return None

    scored["admission_dt"] = scored["admission_date_raw"].apply(_parse)

    # Derive month and quarter labels
    scored["year_month"] = scored["admission_dt"].apply(
        lambda d: d.strftime("%Y-%m") if pd.notna(d) else "Unknown period"
    )
    scored["quarter"] = scored["admission_dt"].apply(
        lambda d: f"{d.year}-Q{d.quarter}" if pd.notna(d) else "Unknown period"
    )

    summary = (
        scored.groupby(["year_month", "quarter"])
        .agg(
            n_records     =("record_id", "nunique"),
            n_observations=("correct?",  "count"),
            mean_accuracy =("correct?",  "mean"),
            std_accuracy  =("correct?",  "std"),
        )
        .reset_index()
    )
    summary["mean_accuracy"] = summary["mean_accuracy"].round(3)
    summary["std_accuracy"]  = summary["std_accuracy"].round(3)
    summary["model"]         = model_label

    # Sort chronologically (Unknown period goes to end)
    known   = summary[summary["year_month"] != "Unknown period"].sort_values("year_month")
    unknown = summary[summary["year_month"] == "Unknown period"]
    summary = pd.concat([known, unknown], ignore_index=True)

    logger.info("Table 3 (scan period): %d months", len(summary))
    return summary


# ---------------------------------------------------------------------------
# Bonus: facility × field_type cross-tab

def table_facility_by_field_type(df: pd.DataFrame, model_label: str) -> pd.DataFrame:
    """Cross-tabulation of mean accuracy: facility (rows) × field type (columns).

    Useful for spotting whether a particular facility struggles specifically
    with, say, date fields or boolean fields.

    Parameters
    ----------
    df: Full accuracy DataFrame.
    model_label: Used for logging only.

    Returns
    -------
    pd.DataFrame
        Pivot table — facilities as index, field types as columns.
    """
    scored = df[df["scorable"] & df["has_gt"]].copy()
    scored["correct?"] = pd.to_numeric(scored["correct?"], errors="coerce")
    scored["facility"] = scored["record_id"].apply(_decode_facility_from_record_id)

    pivot = (
        scored.groupby(["facility", "field_type"])["correct?"]
        .mean()
        .round(3)
        .unstack(fill_value=None)
        .reset_index()
    )
    logger.info("Bonus table (facility × field_type): %d facilities", len(pivot))
    return pivot


# ---------------------------------------------------------------------------
# Public entry point

def run_stratified_analysis(
    model_label: str = "qwen",
    accuracy_csv: str | None = None,
    structured_table: str | None = None,
    output_dir: str = ".",
) -> dict[str, pd.DataFrame]:
    """Run all three stratified comparisons and save CSVs.

    Parameters
    ----------
    model_label: Model whose outputs to analyse (``"qwen"``, ``"gemma"``, etc.).
    accuracy_csv: Path to ``field_accuracy_{model}.csv``.  Defaults to
        ``field_accuracy_{model_label}.csv`` in the working directory.
    structured_table: SurrealDB table containing structured outputs (for admission dates).
        Defaults to ``"structured_qwen_required"`` for Qwen, or
        ``"structured_{model_label}"`` for others.
    output_dir: Directory to write output CSVs.  Defaults to working directory.

    Returns
    -------
    dict with keys ``field_type``, ``facility``, ``scan_period``,
    ``facility_x_field_type``.
    """
    # ── Resolve paths ────────────────────────────────────────────────────
    if accuracy_csv is None:
        accuracy_csv = f"field_accuracy_{model_label}.csv"
    if structured_table is None:
        structured_table = (
            "structured_qwen_required" if model_label == "qwen"
            else f"structured_{model_label}"
        )

    csv_path = Path(accuracy_csv)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Accuracy CSV not found: {csv_path}\n"
            f"Run main.py first to generate it."
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger.info("Loading accuracy data from %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("  Rows: %d | Records: %d", len(df), df["record_id"].nunique())

    # ── Admission dates from DB ──────────────────────────────────────────
    logger.info("Loading admission dates from DB table: %s", structured_table)
    try:
        admission_dates = _load_admission_dates(structured_table)
        logger.info("  Dates loaded for %d records", len(admission_dates))
    except Exception:
        logger.warning(
            "Could not load admission dates from DB — scan period table will "
            "show 'Unknown period' for all records.",
            exc_info=True,
        )
        admission_dates = {}

    # ── Build tables ─────────────────────────────────────────────────────
    t1 = table_by_field_type(df, model_label)
    t2 = table_by_facility(df, model_label)
    t3 = table_by_scan_period(df, admission_dates, model_label)
    t4 = table_facility_by_field_type(df, model_label)

    # ── Save individual CSVs ─────────────────────────────────────────────
    paths = {
        "field_type":           out / f"table1_by_field_type_{model_label}.csv",
        "facility":             out / f"table2_by_facility_{model_label}.csv",
        "scan_period":          out / f"table3_by_scan_period_{model_label}.csv",
        "facility_x_field_type": out / f"table4_facility_x_field_type_{model_label}.csv",
    }
    t1.to_csv(paths["field_type"],            index=False)
    t2.to_csv(paths["facility"],              index=False)
    t3.to_csv(paths["scan_period"],           index=False)
    t4.to_csv(paths["facility_x_field_type"], index=False)

    # ── Combined table (for a single appendix) ───────────────────────────
    def _tag(frame: pd.DataFrame, label: str) -> pd.DataFrame:
        f = frame.copy()
        f.insert(0, "comparison", label)
        return f

    combined = pd.concat(
        [
            _tag(t1, "By field type"),
            _tag(t2, "By facility"),
            _tag(t3, "By scan period"),
        ],
        ignore_index=True,
    )
    combined_path = out / f"table_combined_{model_label}.csv"
    combined.to_csv(combined_path, index=False)

    # ── Console ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  STRATIFIED ANALYSIS — {model_label.upper()}")
    print(f"{'='*60}")

    print("\n  TABLE 1: Accuracy by field type")
    print(t1[["field_type", "n_records", "n_fields", "mean_accuracy", "std_accuracy"]]
          .to_string(index=False))

    print("\n  TABLE 2: Accuracy by facility")
    print(t2[["facility", "n_records", "mean_accuracy", "std_accuracy"]]
          .to_string(index=False))

    print("\n  TABLE 3: Accuracy by scan period")
    print(t3[["year_month", "quarter", "n_records", "mean_accuracy"]]
          .to_string(index=False))

    print(f"\n  Saved:")
    for label, path in paths.items():
        print(f"    {path}")
    print(f"    {combined_path}")

    return {
        "field_type":            t1,
        "facility":              t2,
        "scan_period":           t3,
        "facility_x_field_type": t4,
    }


# ---------------------------------------------------------------------------
# CLI

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(
        description="Generate stratified accuracy tables from BRIDGE pipeline outputs."
    )
    parser.add_argument(
        "--model", default="qwen",
        help="Model label matching the CSV filename (default: qwen)."
    )
    parser.add_argument(
        "--csv", default=None,
        help="Path to field_accuracy_{model}.csv (default: auto-detected)."
    )
    parser.add_argument(
        "--table", default=None,
        help="SurrealDB structured table name (default: auto-detected)."
    )
    parser.add_argument(
        "--out", default=".",
        help="Output directory for CSVs (default: working directory)."
    )
    args = parser.parse_args()

    run_stratified_analysis(
        model_label=args.model,
        accuracy_csv=args.csv,
        structured_table=args.table,
        output_dir=args.out,
    )