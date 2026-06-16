"""
Computes F1, Precision, Recall, and Exact Accuracy from the
correct? column already produced by build_accuracy_table().

Definitions (per field, per record):
  TP — model extracted a value AND it matched GT (correct? == 1.0)
  FP — model extracted a value BUT it did NOT match GT (correct? == 0.0)
  FN — GT has a value BUT model returned None / empty (predicted_val is None)
  TN — both GT and prediction are None / empty  (scored separately as true_negative)

Outputs:
  metrics_{model}.csv        — per-field breakdown
  summary_metrics_{model}.csv — per field_type and per nar_inclusion rollup
"""

import pandas as pd
import numpy as np


# ------------------------
# CORE COUNTERS

def _classify_row(row) -> str:
    """
    Classify a single (record, field) row into TP / FP / FN / TN.
    Only called on rows where has_gt=True and scorable=True.
    """
    pred = row["norm_pred"] if "norm_pred" in row.index else row["predicted_val"]
    gt   = row["norm_gt"]   if "norm_gt"   in row.index else row["ground_truth_val"]

    pred_empty = pred in (None, "", "none", "null") or pd.isna(pred) if pred is not None else True
    gt_empty   = gt   in (None, "", "none", "null") or pd.isna(gt)   if gt   is not None else True

    correct = float(row["correct?"]) == 1.0 if pd.notna(row["correct?"]) else False

    if gt_empty and pred_empty:
        return "TN"
    if gt_empty and not pred_empty:
        return "FP"          # hallucinated a value when GT is blank
    if not gt_empty and pred_empty:
        return "FN"          # missed a value that exists in GT
    if correct:
        return "TP"
    return "FP"              # wrong value


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    return round(precision, 4), round(recall, 4), round(f1, 4)


# ------------------------
# FIELD-LEVEL METRICS

def compute_field_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input : full DataFrame from build_accuracy_table() (all fields, all records).
    Output: one row per field with TP/FP/FN/TN counts + P/R/F1 + exact_accuracy.
    """
    scored = df[df["scorable"] & df["has_gt"]].copy()

    # Use norm_pred / norm_gt if available, else fall back to raw
    pred_col = "norm_pred" if "norm_pred" in scored.columns else "predicted_val"
    gt_col   = "norm_gt"   if "norm_gt"   in scored.columns else "ground_truth_val"

    scored["_outcome"] = scored.apply(_classify_row, axis=1)

    rows = []
    for field, grp in scored.groupby("field"):
        counts = grp["_outcome"].value_counts().to_dict()
        tp = counts.get("TP", 0)
        fp = counts.get("FP", 0)
        fn = counts.get("FN", 0)
        tn = counts.get("TN", 0)
        n  = len(grp)

        precision, recall, f1 = _prf(tp, fp, fn)
        exact_acc = round((tp + tn) / n, 4) if n > 0 else 0.0
        avg_fuzzy = round(grp["correct?"].mean(), 4)

        rows.append({
            "field":         field,
            "field_type":    grp["field_type"].iloc[0],
            "nar_inclusion": grp["nar_inclusion"].iloc[0],
            "n_records":     n,
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision":     precision,
            "recall":        recall,
            "f1":            f1,
            "exact_accuracy": exact_acc,
            "fuzzy_accuracy": avg_fuzzy,
        })

    return pd.DataFrame(rows).sort_values("f1", ascending=False)


# ------------------------
# ROLLUP SUMMARIES

def _macro_avg(grp):
    """Macro-average P/R/F1 across fields in a group."""
    return pd.Series({
        "n_fields":        len(grp),
        "macro_precision": round(grp["precision"].mean(), 4),
        "macro_recall":    round(grp["recall"].mean(), 4),
        "macro_f1":        round(grp["f1"].mean(), 4),
        "micro_f1":        round(grp["f1"].median(), 4),
        "avg_exact_acc":   round(grp["exact_accuracy"].mean(), 4),
        "avg_fuzzy_acc":   round(grp["fuzzy_accuracy"].mean(), 4),
    })


def compute_summary_metrics(field_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Returns a dict of summary DataFrames:
      by_field_type    — macro P/R/F1 per field type (bool, int, str, …)
      by_nar_inclusion — macro P/R/F1 for included vs not included
      overall          — single-row overall summary
    """
    by_type = (
        field_df.groupby("field_type")
        .apply(_macro_avg, include_groups=False)
        .reset_index()
        .sort_values("macro_f1", ascending=False)
    )

    by_inclusion = (
        field_df.groupby("nar_inclusion")
        .apply(_macro_avg, include_groups=False)
        .reset_index()
        .sort_values("macro_f1", ascending=False)
    )

    overall = _macro_avg(field_df).to_frame().T
    overall.insert(0, "scope", "overall")

    return {
        "by_field_type":    by_type,
        "by_nar_inclusion": by_inclusion,
        "overall":          overall,
    }


# ------------------------
# ENTRY POINT

def run_classification_metrics(
    df: pd.DataFrame,
    model_label: str = "qwen",
) -> dict:
    """
    Main entry point called from run_evaluation.py.

    Args:
        df          : DataFrame from build_accuracy_table() — must include
                      scorable, has_gt, correct?, field_type, nar_inclusion columns.
        model_label : used for output filenames.

    Returns dict with keys: field_metrics, summaries (by_field_type,
    by_nar_inclusion, overall), and file paths written.
    """
    print(f"\n{'='*60}")
    print(f"  CLASSIFICATION METRICS — {model_label.upper()}")
    print(f"{'='*60}")

    field_df = compute_field_metrics(df)
    summaries = compute_summary_metrics(field_df)

    # ── console output ─────────────────────────────────────────────
    print("\n  Top 15 fields by F1:")
    print(field_df[["field", "field_type", "nar_inclusion",
                     "precision", "recall", "f1", "exact_accuracy"]]
          .head(15).to_string(index=False))

    print("\n  Bottom 10 fields by F1:")
    print(field_df[["field", "field_type", "nar_inclusion",
                     "precision", "recall", "f1", "exact_accuracy"]]
          .tail(10).to_string(index=False))

    print("\n  Metrics by field type:")
    print(summaries["by_field_type"].to_string(index=False))

    print("\n  Metrics by NAR inclusion:")
    print(summaries["by_nar_inclusion"].to_string(index=False))

    print("\n  Overall:")
    print(summaries["overall"].to_string(index=False))

    # ── save CSVs ─────────────────────────────────────────────────
    f1 = f"metrics_{model_label}.csv"
    f2 = f"summary_metrics_{model_label}.csv"

    field_df.to_csv(f1, index=False)

    summary_frames = []
    for scope, sdf in summaries.items():
        sdf = sdf.copy()
        sdf.insert(0, "summary_scope", scope)
        summary_frames.append(sdf)
    pd.concat(summary_frames, ignore_index=True).to_csv(f2, index=False)

    print(f"\n  Saved: {f1}, {f2}")

    return {"field_metrics": field_df, "summaries": summaries}