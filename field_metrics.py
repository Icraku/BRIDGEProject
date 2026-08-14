"""
utils/field_metrics_summary.py
================================
Builds a comprehensive per-field metrics table combining:
  - F1, Precision, Recall, TP, FP, FN, TN  (from metrics_{model}.csv)
  - Mean accuracy, Fuzzy accuracy           (from field_accuracy_{model}.csv)
  - Field type, NAR inclusion               (from FIELD_TYPES)

Rows = all 98 NARRecord fields, split into Page 1 then Page 2
Columns = field metadata + metrics for each model side by side

Usage
-----
    python -m utils.field_metrics_summary
    python -m utils.field_metrics_summary --models qwen gemma --out results/

Outputs
-------
    field_metrics_by_page.csv      — full table (both pages combined)
    field_metrics_page1.csv        — page 1 fields only
    field_metrics_page2.csv        — page 2 fields only
    field_metrics_by_page.xlsx     — Excel workbook with three sheets
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas.neonatal_admission_form.field_types import FIELD_TYPES

# ---------------------------------------------------------------------------
# NAR form page layout — matches physical form sections
# ---------------------------------------------------------------------------

PAGE1_FIELDS = [
    # Section A — Infant details
    "admission_date", "time_seen", "sex", "birth_date", "time_birth",
    "gestation_in_weeks", "baby_age_in_days", "gestation_type",
    "apgar_1m", "apgar_5m", "apgar_10m", "delivery_type", "had_cs",
    "was_resuscitated", "rapture_of_membrane", "is_multiple_delivery",
    "multiple_delivery_num", "born_before_arrival", "born_where",
    # Section B — Mother's details
    "mum_age_in_years", "parity_live", "parity_abortions",
    "date_estimated_delivery_date", "anc_visits", "mum_has_anc_ultrasound",
    "anc_us_trimester", "blood_group", "rhesus", "given_anti_D_medication",
    "mum_had_vdrl", "mum_pmtct_status", "mum_on_arvs",
    "mum_had_hepatitis_b", "mum_given_HBIG_treatment",
    "mum_had_hypertension_in_pregnancy", "mum_had_antepartum_haemorrhage",
    "mum_had_diabetes", "prolonged_labour",
    # Section E — Anthropometry & Vital signs + Symptoms
    "head_circumference", "length", "temparature", "respiratory_rate",
    "systolic_blood_pressure", "diastolic_blood_pressure",
    "pulse_rate", "pulse_oximetry", "birth_weight", "weight",
    "has_fever", "passed_meconium", "has_difficulty_breathing",
    "passed_urine", "has_difficulty_feeding", "has_convulsions",
    "has_apnoea", "is_floppy", "has_vomiting", "has_diarhoea",
]

PAGE2_FIELDS = [
    # Section F1 — General examination
    "skin", "jaundice", "appearance", "cry",
    "has_crackles", "has_grunting", "has_good_air_entry",
    "has_central_cyanosis", "chest_indrawing", "xiphoid_retraction",
    "intercostal_retraction", "capillary_refill_in_seconds",
    "pallor", "has_murmur", "has_bulging_fontanelle",
    "is_irritable", "tone", "is_distended", "umbilicus",
    # Section F2 — Further examination
    "has_birth_defects",
    # Section H — Investigations
    "rbs_measured", "given_bilirubin",
    # Section I — Diagnoses
    "primary_admission_diagnosis", "secondary_admission_diagnosis",
    # Section J — Interventions
    "given_vitamin_k", "given_bcg", "given_chlorhexidine",
    "given_prophylaxis_pmtct", "prescribed_transfusion",
    "prescribed_phototherapy", "prescribed_cpap", "prescribed_iv_fluids",
    "prescribed_antibiotics", "prescribed_feeds", "prescribed_opv",
    "prescribed_surfactant", "prescribed_caffeine_citrate",
    "prescribed_oxygen", "prescribed_kmc", "prescribed_incubator",
]

ALL_FIELDS_ORDERED = PAGE1_FIELDS + PAGE2_FIELDS


# ---------------------------------------------------------------------------
# Section labels for readability
# ---------------------------------------------------------------------------

SECTION_MAP = {
    "admission_date": "A: Infant details",
    "time_seen": "A: Infant details",
    "sex": "A: Infant details",
    "birth_date": "A: Infant details",
    "time_birth": "A: Infant details",
    "gestation_in_weeks": "A: Infant details",
    "baby_age_in_days": "A: Infant details",
    "gestation_type": "A: Infant details",
    "apgar_1m": "A: Infant details",
    "apgar_5m": "A: Infant details",
    "apgar_10m": "A: Infant details",
    "delivery_type": "A: Infant details",
    "had_cs": "A: Infant details",
    "was_resuscitated": "A: Infant details",
    "rapture_of_membrane": "A: Infant details",
    "is_multiple_delivery": "A: Infant details",
    "multiple_delivery_num": "A: Infant details",
    "born_before_arrival": "A: Infant details",
    "born_where": "A: Infant details",
    "mum_age_in_years": "B: Mother details",
    "parity_live": "B: Mother details",
    "parity_abortions": "B: Mother details",
    "date_estimated_delivery_date": "B: Mother details",
    "anc_visits": "B: Mother details",
    "mum_has_anc_ultrasound": "B: Mother details",
    "anc_us_trimester": "B: Mother details",
    "blood_group": "B: Mother details",
    "rhesus": "B: Mother details",
    "given_anti_D_medication": "B: Mother details",
    "mum_had_vdrl": "B: Mother details",
    "mum_pmtct_status": "B: Mother details",
    "mum_on_arvs": "B: Mother details",
    "mum_had_hepatitis_b": "B: Mother details",
    "mum_given_HBIG_treatment": "B: Mother details",
    "mum_had_hypertension_in_pregnancy": "B: Mother details",
    "mum_had_antepartum_haemorrhage": "B: Mother details",
    "mum_had_diabetes": "B: Mother details",
    "prolonged_labour": "B: Mother details",
    "head_circumference": "E: Vital signs",
    "length": "E: Vital signs",
    "temparature": "E: Vital signs",
    "respiratory_rate": "E: Vital signs",
    "systolic_blood_pressure": "E: Vital signs",
    "diastolic_blood_pressure": "E: Vital signs",
    "pulse_rate": "E: Vital signs",
    "pulse_oximetry": "E: Vital signs",
    "birth_weight": "E: Vital signs",
    "weight": "E: Vital signs",
    "has_fever": "E: Symptoms",
    "passed_meconium": "E: Symptoms",
    "has_difficulty_breathing": "E: Symptoms",
    "passed_urine": "E: Symptoms",
    "has_difficulty_feeding": "E: Symptoms",
    "has_convulsions": "E: Symptoms",
    "has_apnoea": "E: Symptoms",
    "is_floppy": "E: Symptoms",
    "has_vomiting": "E: Symptoms",
    "has_diarhoea": "E: Symptoms",
    "skin": "F1: Examination",
    "jaundice": "F1: Examination",
    "appearance": "F1: Examination",
    "cry": "F1: Examination",
    "has_crackles": "F1: Respiratory",
    "has_grunting": "F1: Respiratory",
    "has_good_air_entry": "F1: Respiratory",
    "has_central_cyanosis": "F1: Respiratory",
    "chest_indrawing": "F1: Respiratory",
    "xiphoid_retraction": "F1: Respiratory",
    "intercostal_retraction": "F1: Respiratory",
    "capillary_refill_in_seconds": "F1: CVS",
    "pallor": "F1: CVS",
    "has_murmur": "F1: CVS",
    "has_bulging_fontanelle": "F1: Neuro",
    "is_irritable": "F1: Neuro",
    "tone": "F1: Neuro",
    "is_distended": "F1: Abdomen",
    "umbilicus": "F1: Abdomen",
    "has_birth_defects": "F2: Birth defects",
    "rbs_measured": "H: Investigations",
    "given_bilirubin": "H: Investigations",
    "primary_admission_diagnosis": "I: Diagnoses",
    "secondary_admission_diagnosis": "I: Diagnoses",
    "given_vitamin_k": "J: Interventions",
    "given_bcg": "J: Interventions",
    "given_chlorhexidine": "J: Interventions",
    "given_prophylaxis_pmtct": "J: Interventions",
    "prescribed_transfusion": "J: Interventions",
    "prescribed_phototherapy": "J: Interventions",
    "prescribed_cpap": "J: Interventions",
    "prescribed_iv_fluids": "J: Interventions",
    "prescribed_antibiotics": "J: Interventions",
    "prescribed_feeds": "J: Interventions",
    "prescribed_opv": "J: Interventions",
    "prescribed_surfactant": "J: Interventions",
    "prescribed_caffeine_citrate": "J: Interventions",
    "prescribed_oxygen": "J: Interventions",
    "prescribed_kmc": "J: Interventions",
    "prescribed_incubator": "J: Interventions",
}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_metrics(model: str) -> pd.DataFrame:
    """Load per-field classification metrics from metrics_{model}.csv."""
    path = Path(f"metrics_{model}.csv")
    if not path.exists():
        print(f"  Warning: {path} not found — classification metrics will be empty for {model}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Normalise column names (different runs may vary slightly)
    df.columns = [c.lower().strip() for c in df.columns]
    return df.set_index("field") if "field" in df.columns else df


def load_accuracy(model: str) -> pd.DataFrame:
    """Load per-field accuracy from field_accuracy_{model}.csv."""
    path = Path(f"field_accuracy_{model}.csv")
    if not path.exists():
        print(f"  Warning: {path} not found — accuracy metrics will be empty for {model}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    # Aggregate per field (average across all records)
    scored = df[df.get("scorable", pd.Series([True]*len(df))) & df.get("has_gt", pd.Series([True]*len(df)))]
    agg = (
        scored.groupby("field")
        .agg(
            mean_accuracy  =("correct?", "mean"),
            n_records      =("record_id", "nunique"),
        )
        .round(4)
    )
    return agg


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_summary(models: list[str]) -> pd.DataFrame:
    """Build the per-field summary table."""

    # Base frame — all 98 fields in page order
    base = pd.DataFrame({
        "field":     ALL_FIELDS_ORDERED,
        "page":      ["Page 1"] * len(PAGE1_FIELDS) + ["Page 2"] * len(PAGE2_FIELDS),
        "section":   [SECTION_MAP.get(f, "Other") for f in ALL_FIELDS_ORDERED],
        "field_type":[FIELD_TYPES.get(f, "unknown") for f in ALL_FIELDS_ORDERED],
    }).set_index("field")

    for model in models:
        label = model.upper()
        print(f"  Loading {model}...")

        # --- Classification metrics -----------------------------------------
        met = load_metrics(model)

        if not met.empty:
            # Common column names to try
            col_map = {
                "f1":        ["f1", "macro_f1", "f1_score"],
                "precision": ["precision", "macro_precision", "prec"],
                "recall":    ["recall", "macro_recall", "rec"],
                "tp":        ["tp", "true_positives", "true_positive"],
                "fp":        ["fp", "false_positives", "false_positive"],
                "fn":        ["fn", "false_negatives", "false_negative"],
                "tn":        ["tn", "true_negatives", "true_negative"],
            }
            def get_col(df, candidates):
                for c in candidates:
                    if c in df.columns:
                        return df[c]
                return pd.Series(dtype=float, name="missing")

            for metric, candidates in col_map.items():
                col = get_col(met, candidates)
                base[f"{label}_{metric}"] = base.index.map(
                    col.to_dict() if not col.empty else {}
                )
        else:
            for metric in ["f1", "precision", "recall", "tp", "fp", "fn", "tn"]:
                base[f"{label}_{metric}"] = None

        # --- Accuracy metrics -----------------------------------------------
        acc = load_accuracy(model)
        if not acc.empty:
            base[f"{label}_mean_acc"] = base.index.map(
                acc["mean_accuracy"].to_dict()
            )
            base[f"{label}_n_records"] = base.index.map(
                acc["n_records"].to_dict()
            )
        else:
            base[f"{label}_mean_acc"]   = None
            base[f"{label}_n_records"]  = None

    # Round numeric columns
    for col in base.columns:
        if base[col].dtype == float:
            base[col] = base[col].round(4)

    return base.reset_index()


# ---------------------------------------------------------------------------
# Excel writer with formatting
# ---------------------------------------------------------------------------

def write_excel(df: pd.DataFrame, out_path: Path, models: list[str]) -> None:
    """Write the summary to an Excel workbook with three sheets."""
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("  openpyxl not installed — skipping Excel output (pip install openpyxl)")
        return

    page1 = df[df["page"] == "Page 1"]
    page2 = df[df["page"] == "Page 2"]

    # Color fills
    hdr_fill  = PatternFill("solid", fgColor="1F4E79")
    p1_fill   = PatternFill("solid", fgColor="D6E4F0")
    p2_fill   = PatternFill("solid", fgColor="E2EFDA")
    sec_fill  = PatternFill("solid", fgColor="BDD7EE")
    alt_fill  = PatternFill("solid", fgColor="F2F7FB")
    hdr_font  = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
    bold_font = Font(bold=True, size=10, name="Calibri")
    norm_font = Font(size=10, name="Calibri")
    thin = Side(style="thin", color="AAAAAA")
    thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for sheet_name, data in [
            ("All fields", df),
            ("Page 1", page1),
            ("Page 2", page2),
        ]:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]

            # Header row styling
            for cell in ws[1]:
                cell.fill    = hdr_fill
                cell.font    = hdr_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border  = thin_border

            ws.row_dimensions[1].height = 36

            # Data rows
            prev_section = None
            for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
                section_val = ws.cell(row=row_idx, column=3).value  # section col
                is_new_section = section_val != prev_section
                prev_section = section_val

                for cell in row:
                    cell.font   = norm_font
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                    if is_new_section:
                        cell.fill = sec_fill
                    elif row_idx % 2 == 0:
                        cell.fill = alt_fill

                    # Right-align numeric columns
                    try:
                        float(cell.value)
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    except (TypeError, ValueError):
                        pass

            # Column widths
            col_widths = {
                "field": 32, "page": 8, "section": 18, "field_type": 12,
            }
            for col_idx, col in enumerate(ws.iter_cols(min_row=1, max_row=1), start=1):
                header = col[0].value or ""
                width = col_widths.get(header.lower(), 12)
                ws.column_dimensions[get_column_letter(col_idx)].width = width

            # Freeze header + first two columns
            ws.freeze_panes = "E2"

    print(f"  Excel saved: {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build per-field metrics summary table by NAR form page."
    )
    parser.add_argument(
        "--models", nargs="+", default=["qwen", "gemma"],
        help="Model labels to include (default: qwen gemma)"
    )
    parser.add_argument(
        "--out", default=".",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--no-excel", action="store_true",
        help="Skip Excel output (CSV only)"
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Building field metrics summary for models: {args.models}")
    df = build_summary(args.models)

    # Save CSVs
    csv_all  = out / "field_metrics_by_page.csv"
    csv_p1   = out / "field_metrics_page1.csv"
    csv_p2   = out / "field_metrics_page2.csv"

    df.to_csv(csv_all, index=False)
    df[df["page"]=="Page 1"].to_csv(csv_p1, index=False)
    df[df["page"]=="Page 2"].to_csv(csv_p2, index=False)

    print(f"  CSV saved: {csv_all}")
    print(f"  CSV saved: {csv_p1}")
    print(f"  CSV saved: {csv_p2}")

    # Print preview
    print(f"\n{'='*70}")
    print(f"  FIELD METRICS SUMMARY PREVIEW")
    print(f"  Rows: {len(df)} fields  |  Models: {args.models}")
    print(f"  Columns: {list(df.columns)}")
    print(f"{'='*70}")
    for page in ["Page 1", "Page 2"]:
        sub = df[df["page"]==page]
        print(f"\n  {page} ({len(sub)} fields):")
        for model in args.models:
            col = f"{model.upper()}_f1"
            if col in sub.columns:
                valid = sub[col].dropna()
                if not valid.empty:
                    best  = sub.loc[sub[col].idxmax(), ["field", col]]
                    worst = sub.loc[sub[col].idxmin(), ["field", col]]
                    print(f"    {model} — mean F1: {valid.mean():.3f} | "
                          f"best: {best['field']} ({best[col]:.3f}) | "
                          f"worst: {worst['field']} ({worst[col]:.3f})")

    # Excel
    if not args.no_excel:
        write_excel(df, out / "field_metrics_by_page.xlsx", args.models)

    print(f"\nDone. Files in: {out}/")


if __name__ == "__main__":
    main()