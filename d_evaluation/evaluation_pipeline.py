import json
import os
import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict

from database_utils.db_utils import fetch_records
from database_utils.db_save import safe_save
from d_evaluation.field_accuracy import build_accuracy_table
from d_evaluation.field_accuracy import load_structured_outputs
from schemas.neonatal_admission_form.field_types import FIELD_TYPES, HOSPITAL_CODES, encode_hospital
from schemas.neonatal_admission_form.nar_full_schema import (
    FULL_SCHEMA_FIELDS,
    NAR_REQUIRED_FIELDS,
    inclusion_status,
)

gt_path = "/NAR_metadata.json"


def load_inclusion_maps(table_name="structured_Q"):
    """
    Load the per-record inclusion maps saved alongside full extractions.
    Falls back to computing from FULL_SCHEMA_FIELDS if not stored.
    """
    records = fetch_records(table_name)
    maps = {}
    for r in records:
        raw_id = r.get("id")
        if not raw_id:
            continue
        record_id = str(raw_id).split(":")[-1]
        inc_map = r.get("inclusion_map")
        if inc_map:
            maps[record_id] = inc_map
    return maps

# ------------------------
# LOAD + FILTER GROUND TRUTH

def load_and_process_meta(gt_path: str, predictions: dict):
    with open(gt_path) as f:
        raw_gt = json.load(f)

    if isinstance(raw_gt, dict):
        return {k: v for k, v in raw_gt.items() if k in predictions}

    gt_dict = {}
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
            if k not in gt_dict[base_id] or gt_dict[base_id][k] in [None, "", "null"]:
                gt_dict[base_id][k] = v
    return gt_dict


# ------------------------
# STRUCTURED COMPARISON/VALIDATION (qwen vs gemma)

def check_match(q, g) -> str:
    q_s = str(q).strip().lower() if q not in (None, "", "null") else ""
    g_s = str(g).strip().lower() if g not in (None, "", "null") else ""
    if not q_s and not g_s: return "both_empty"
    if not q_s or not g_s:  return "one_empty"
    return "match" if q_s == g_s else "mismatch"


def run_structured_comparison(
    qwen_table="structured",
    gemma_table="structured_gemma",
    output_table="comparison_structured",
    output_csv="structured_comparison.csv",
):
    print("\n" + "="*60)
    print("STRUCTURED COMPARISON: QWEN vs GEMMA")
    print("="*60)

    qwen_structured  = load_structured_outputs(qwen_table)
    gemma_structured = load_structured_outputs(gemma_table)
    all_ids = sorted(set(qwen_structured.keys()) | set(gemma_structured.keys()))
    all_fields = sorted(set(FIELD_TYPES.keys()) | FULL_SCHEMA_FIELDS)
    print(f"Records — qwen: {len(qwen_structured)}, gemma: {len(gemma_structured)}, total unique: {len(all_ids)}")

    csv_rows = [[
        "record_id", "field", "field_type", "nar_inclusion",
        "qwen_value", "gemma_value", "match_status",
    ]]

    for record_id in all_ids:
        print(f"\n--- {record_id} ---")
        q_fields = qwen_structured.get(record_id, {})
        g_fields = gemma_structured.get(record_id, {})
        field_results = {}

        for field in all_fields:
            field_type = FIELD_TYPES.get(field, "unknown")
            inc        = inclusion_status(field)
            q_val      = q_fields.get(field, "")
            g_val      = g_fields.get(field, "")

            # Encode filenames to hospital codes for display
            if field == "hospital":
                q_val = encode_hospital(q_val) or q_val
                g_val = encode_hospital(g_val) or g_val

            status = check_match(q_val, g_val)

            field_results[field] = {
                "field_type":    field_type,
                "nar_inclusion": inc,
                "qwen_value":    str(q_val) if q_val not in (None, "") else "",
                "gemma_value":   str(g_val) if g_val not in (None, "") else "",
                "match_status":  status,
            }

            if status != "both_empty":
                print(
                    f"  {field:<40} [{inc:<12}] "
                    f"qwen={str(q_val)!r:<15} gemma={str(g_val)!r:<15} → {status}"
                )

            csv_rows.append([record_id, field, field_type, inc, str(q_val), str(g_val), status])

        statuses     = [v["match_status"] for v in field_results.values()]
        n_total      = len(statuses)
        n_match      = statuses.count("match")
        n_mismatch   = statuses.count("mismatch")
        n_one_empty  = statuses.count("one_empty")
        n_both_empty = statuses.count("both_empty")
        agreement    = round(n_match / n_total * 100, 2) if n_total else 0

        type_counts = defaultdict(lambda: {"match": 0, "total": 0})
        inc_counts  = defaultdict(lambda: {"match": 0, "total": 0})

        for f, info in field_results.items():
            if info["match_status"] != "both_empty":
                type_counts[info["field_type"]]["total"] += 1
                inc_counts[info["nar_inclusion"]]["total"] += 1
                if info["match_status"] == "match":
                    type_counts[info["field_type"]]["match"] += 1
                    inc_counts[info["nar_inclusion"]]["match"] += 1

        safe_save(
            {
                "record_id":        record_id,
                "run_id":           datetime.now().isoformat(),
                "fields":           field_results,
                "by_field_type":    {ft: round(v["match"]/v["total"]*100,2) if v["total"] else 0 for ft,v in type_counts.items()},
                "by_nar_inclusion": {i:  round(v["match"]/v["total"]*100,2) if v["total"] else 0 for i,  v in inc_counts.items()},
                "summary": {
                    "total_fields": n_total, "matching": n_match,
                    "mismatching": n_mismatch, "one_empty": n_one_empty,
                    "both_empty": n_both_empty, "agreement_pct": agreement,
                },
            },
            output_table, record_id,
        )
        print(f"  → agreement {agreement}% | saved to {output_table}:{record_id}")

    with open(output_csv, "w", newline="") as f:
        csv.writer(f).writerows(csv_rows)
    print(f"\nCSV saved: {output_csv}")


# ------------------------
# EVALUATION AGAINST GROUND TRUTH

def run_evaluation(gt_path, structured_table="structured", model_label="qwen"):
    if not os.path.exists(gt_path):
        print("Ground truth file not found, skipping evaluation.")
        return None

    print(f"\n{'='*60}")
    print(f"EVALUATING: {model_label}  (table: {structured_table})")
    print(f"{'='*60}")

    predictions  = load_structured_outputs(structured_table)
    ground_truth = load_and_process_meta(gt_path, predictions)
    print(f"  Predictions: {len(predictions)} | GT matched: {len(ground_truth)}")

    df = build_accuracy_table(predictions, ground_truth)
    df["model"] = model_label

    # Scored subset: has GT AND is a scorable type (not redacted/text)
    df_scored = df[df["scorable"] & df["has_gt"]].copy()
    df.to_csv(f"field_accuracy_{model_label}.csv", index=False)

    # console summary
    print(f"\n  All extracted fields    : {df['field'].nunique()} unique")
    print(f"  Scored (GT + scorable)  : {df_scored['field'].nunique()}")
    print(f"  Unscored (text/redacted): {df[~df['scorable']]['field'].nunique()}")
    print(f"  No ground truth         : {df[~df['has_gt']]['field'].nunique()}")

    # full field table (all 120, all records)
    all_field_summary = (
        df.groupby(["field", "field_type", "nar_inclusion", "scorable", "has_gt"])
        .agg(avg_accuracy=("correct?", "mean"), n_records=("record_id", "nunique"))
        .reset_index()
        .sort_values(["nar_inclusion", "field_type", "avg_accuracy"],
                     ascending=[True, True, False])
    )
    print(f"\n  All fields ({len(all_field_summary)} rows, sorted by inclusion + type):")
    print(all_field_summary.to_string(index=False))
    all_field_summary.to_csv(f"all_fields_{model_label}.csv", index=False)

    # Field summary fo scored fields only
    field_summary = (
        df_scored.groupby(["field", "nar_inclusion"])["correct?"]
        .mean()
        .reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
        .sort_values("avg_accuracy", ascending=False)
    )
    print("\n  Field accuracy (top 10 scored fields):")
    print(field_summary.head(10).to_string(index=False))

    # Field-type summary
    type_summary = (
        df_scored.groupby("field_type")["correct?"]
        .mean()
        .reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
        .sort_values("avg_accuracy", ascending=False)
    )
    type_summary["avg_accuracy"] = type_summary["avg_accuracy"].round(3)
    print("\n  Accuracy by field type (scored only):")
    print(type_summary.to_string(index=False))

    # Inclusion based summary
    inclusion_summary = (
        df_scored.groupby("nar_inclusion")["correct?"]
        .mean()
        .reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
    )
    inclusion_summary["avg_accuracy"] = inclusion_summary["avg_accuracy"].round(3)
    print("\n  Accuracy by NAR inclusion (scored only):")
    print(inclusion_summary.to_string(index=False))

    # save to DB
    eval_table = f"evaluation_{model_label}"
    for record_id, group in df.groupby("record_id"):
        group_scored = group[group["scorable"] & group["has_gt"]]

        safe_save(
            {
                "record_id":        record_id,
                "model":            model_label,
                "average_accuracy": round(float(group_scored["correct?"].mean()), 3) if len(group_scored) else None,
                "by_field_type":    group_scored.groupby("field_type")["correct?"].mean().round(3).to_dict(),
                "by_nar_inclusion": group_scored.groupby("nar_inclusion")["correct?"].mean().round(3).to_dict(),
                "fields": group[[
                    "field", "correct?", "has_gt", "scorable",
                    "ground_truth_val", "predicted_val",
                    "field_type", "nar_inclusion",
                ]].to_dict(orient="records"),
            },
            eval_table, str(record_id),
        )
    print(f"\n  Saved {df['record_id'].nunique()} records to {eval_table}")
    return df


# ================================================================== #
# FULL METRICS — calls all 5 modules

from d_evaluation.classification_metrics import run_classification_metrics
from d_evaluation.text_metrics           import run_text_metrics
from d_evaluation.schema_compliance      import run_schema_compliance
from d_evaluation.runtime_analysis       import run_runtime_analysis
from d_evaluation.hallucination_detector import run_hallucination_detection


def run_full_metrics_suite(
    gt_path:       str,
    model_configs: list[dict],
) -> dict:
    """
    Run all five metric functions for every model and produce a combined report dict.

    Args:
        gt_path      : path to NAR_metadata.json ground truth file
        model_configs: list of dicts, each with:
                         model_label   — "qwen" / "gemma" / "medgemma"
                         eval_table    — DB table for accuracy eval (structured_required)
                         full_table    — DB table with full extraction (structured_Q)

    Example:
        run_full_metrics_suite(
            gt_path = "/NAR_metadata.json",
            model_configs = [
                {"model_label": "qwen",
                 "eval_table":  "structured_required",
                 "full_table":  "structured_Q"},
                {"model_label": "gemma",
                 "eval_table":  "structured_gemma",
                 "full_table":  "structured_gemma"},
                {"model_label": "medgemma",
                 "eval_table":  "structured_medgemma",
                 "full_table":  "structured_medgemma"},
            ]
        )
    """
    results = {}

    # ---------- Steps 1 + 2 per model (need accuracy df) ----------
    eval_dfs = {}
    for cfg in model_configs:
        label = cfg["model_label"]
        print(f"\n\n{'#'*60}")
        print(f"# MODEL: {label.upper()}")
        print(f"{'#'*60}")

        # Core accuracy df (reuse existing run_evaluation function)
        df = run_evaluation(gt_path,
                            structured_table=cfg["eval_table"],
                            model_label=label)
        eval_dfs[label] = df

        if df is not None:
            # Step 1 — F1 / Precision / Recall
            m1 = run_classification_metrics(df, model_label=label)

            # Step 2 — CER / WER
            m2 = run_text_metrics(df, model_label=label)

            results[label] = {"accuracy_df": df, "metrics": m1, "text": m2}

    # ---------- Step 3 — Check for schema compliance (per model, no GT needed) --
    for cfg in model_configs:
        label = cfg["model_label"]
        m3 = run_schema_compliance(
            structured_table=cfg["full_table"],
            model_label=label,
        )
        results.setdefault(label, {})["compliance"] = m3

    # ---------- Step 4 — Runtime comparison (all models together) ----------------
    runtime_cfgs = [
        {"model_label": c["model_label"], "table_name": c["full_table"]}
        for c in model_configs
    ]
    runtime_df = run_runtime_analysis(runtime_cfgs)
    results["runtime"] = runtime_df

    # ---------- Step 5 — Hallucination (per model) --------------------
    for cfg in model_configs:
        label = cfg["model_label"]
        m5 = run_hallucination_detection(
            structured_table=cfg["full_table"],
            model_label=label,
        )
        results.setdefault(label, {})["hallucination"] = m5

    # ---------- Cross-model F1 comparison table -----------------------
    print(f"\n\n{'='*60}")
    print("  CROSS-MODEL SUMMARY")
    print(f"{'='*60}")
    summary_rows = []
    for label, res in results.items():
        if label == "runtime" or "metrics" not in res:
            continue
        overall = res["metrics"]["summaries"]["overall"]
        comp    = res.get("compliance", {}).get("summary", {})
        hall    = res.get("hallucination", {})
        text    = res.get("text", {})
        summary_rows.append({
            "model":                   label,
            "macro_f1":                overall["macro_f1"].values[0],
            "macro_precision":         overall["macro_precision"].values[0],
            "macro_recall":            overall["macro_recall"].values[0],
            "avg_exact_acc":           overall["avg_exact_acc"].values[0],
            "schema_compliant_pct":    comp.get("schema_compliant_pct"),
            "mean_required_coverage":  comp.get("mean_required_coverage"),
            "hallucination_rate_pct":  hall.get("hallucination_rate_pct"),
            "overall_cer":             text.get("overall_cer"),
            "overall_wer":             text.get("overall_wer"),
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        print(summary_df.to_string(index=False))
        summary_df.to_csv("cross_model_summary.csv", index=False)
        print("\n  Saved: cross_model_summary.csv")

    return results


# ================================================================== #
# ENTRY POINT

if __name__ == "__main__":
    MODEL_CONFIGS = [
        {
            "model_label": "qwen",
            "eval_table":  "structured_required",   # 98 NARRecord fields
            "full_table":  "structured_Q",          # all 120 fields
        },
        {
            "model_label": "gemma",
            "eval_table":  "structured_gemma",
            "full_table":  "structured_gemma",
        },
        # For MedGemma (uncomment when MedGemma runs are complete)
        # {
        #     "model_label": "medgemma",
        #     "eval_table":  "structured_medgemma",
        #     "full_table":  "structured_medgemma",
        # },
    ]

    run_full_metrics_suite(gt_path=gt_path, model_configs=MODEL_CONFIGS)