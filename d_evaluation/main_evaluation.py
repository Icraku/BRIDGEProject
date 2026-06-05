import json
import os
import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict

from database_utils.db_utils import fetch_records
from database_utils.db_save import safe_save
from d_evaluation.field_accuracy import build_accuracy_table
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import (
    FULL_SCHEMA_FIELDS,
    NAR_REQUIRED_FIELDS,
    inclusion_status,
)

gt_path = "/NAR_metadata.json"

# ------------------------
# LOAD STRUCTURED DATA FROM DB

def load_structured_outputs(table_name="structured"):
    """
    Load structured outputs from DB.
    Works for both the full extraction table and the required-only table.
    """
    records = fetch_records(table_name)
    predictions = {}
    for r in records:
        raw_id = r.get("id")
        if not raw_id:
            continue
        record_id = str(raw_id).split(":")[-1]
        structured = r.get("structured_text")
        if structured:
            predictions[record_id] = structured
    return predictions

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
    print(f"Records — qwen: {len(qwen_structured)}, gemma: {len(gemma_structured)}, total unique: {len(all_ids)}")

    # Use all fields present across both models
    all_fields = sorted(
        set(FIELD_TYPES.keys()) | FULL_SCHEMA_FIELDS
    )

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
            inc        = inclusion_status(field)          # "included" / "not included"

            q_val  = q_fields.get(field, "")
            g_val  = g_fields.get(field, "")
            status = check_match(q_val, g_val)

            field_results[field] = {
                "field_type":    field_type,
                "nar_inclusion": inc,
                "qwen_value":    str(q_val) if q_val not in (None, "") else "",
                "gemma_value":   str(g_val) if g_val not in (None, "") else "",
                "match_status":  status,
            }

            if status != "both_empty":
                print(f"  {field:<40} [{inc:<12}] "
                    f"qwen={str(q_val)!r:<15} gemma={str(g_val)!r:<15} → {status}"
                )

            csv_rows.append([
                record_id, field, field_type, inc, str(q_val), str(g_val), status,
            ])

        statuses     = [v["match_status"] for v in field_results.values()]
        n_total      = len(statuses)
        n_match      = statuses.count("match")
        n_mismatch   = statuses.count("mismatch")
        n_one_empty  = statuses.count("one_empty")
        n_both_empty = statuses.count("both_empty")
        agreement    = round(n_match / n_total * 100, 2) if n_total else 0

        # Agreement by field type
        type_counts = defaultdict(lambda: {"match": 0, "total": 0})
        for f, info in field_results.items():
            ft = info["field_type"]
            if info["match_status"] != "both_empty":
                type_counts[ft]["total"] += 1
                if info["match_status"] == "match":
                    type_counts[ft]["match"] += 1

        type_agreement = {
            ft: round(v["match"] / v["total"] * 100, 2) if v["total"] else 0
            for ft, v in type_counts.items()
        }

        # Agreement by inclusion status
        inc_counts = defaultdict(lambda: {"match": 0, "total": 0})
        for f, info in field_results.items():
            inc = info["nar_inclusion"]
            if info["match_status"] != "both_empty":
                inc_counts[inc]["total"] += 1
                if info["match_status"] == "match":
                    inc_counts[inc]["match"] += 1

        inclusion_agreement = {
            inc: round(v["match"] / v["total"] * 100, 2) if v["total"] else 0
            for inc, v in inc_counts.items()
        }

        safe_save(
            {
                "record_id":           record_id,
                "run_id":              datetime.now().isoformat(),
                "fields":              field_results,
                "by_field_type":       type_agreement,
                "by_nar_inclusion":    inclusion_agreement,
                "summary": {
                    "total_fields":  n_total,
                    "matching":      n_match,
                    "mismatching":   n_mismatch,
                    "one_empty":     n_one_empty,
                    "both_empty":    n_both_empty,
                    "agreement_pct": agreement,
                },
            },
            output_table,
            record_id,
        )
        print(f"  → agreement {agreement}% | saved to {output_table}:{record_id}")

    with open(output_csv, "w", newline="") as f:
        csv.writer(f).writerows(csv_rows)

    print(f"\nCSV saved: {output_csv}")


# ------------------------
# EVALUATION AGAINST GROUND TRUTH (one model)

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
    df["nar_inclusion"] = df["field"].apply(inclusion_status)
    df.to_csv(f"field_accuracy_{model_label}.csv", index=False)

    # Field summary
    field_summary = (
        df.groupby(["field", "nar_inclusion"])["correct?"]
        .mean()
        .reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
        .sort_values("avg_accuracy", ascending=False)
    )
    print("\n  Field accuracy (top 10):")
    print(field_summary.head(10).to_string(index=False))

    # Field-type summary
    type_summary = (
        df.groupby("field_type")["correct?"]
        .mean().reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
        .sort_values("avg_accuracy", ascending=False)
    )
    type_summary["avg_accuracy"] = type_summary["avg_accuracy"].round(3)
    print("\n  Accuracy by field type:")
    print(type_summary.to_string(index=False))

    # Inclusion based summary
    inclusion_summary = (
        df.groupby("nar_inclusion")["correct?"]
        .mean()
        .reset_index()
        .rename(columns={"correct?": "avg_accuracy"})
    )
    inclusion_summary["avg_accuracy"] = inclusion_summary["avg_accuracy"].round(3)
    print("\n  Accuracy by NAR inclusion:")
    print(inclusion_summary.to_string(index=False))

    eval_table = f"evaluation_{model_label}"
    for record_id, group in df.groupby("record_id"):
        type_breakdown = (
            group.groupby("field_type")["correct?"]
            .mean().round(3).to_dict()
        )
        # Inclusion breakdown
        inclusion_breakdown = (
            group.groupby("nar_inclusion")["correct?"]
            .mean().round(3).to_dict()
        )
        safe_save(
            {
                "record_id":             record_id,
                "model":                 model_label,
                "average_accuracy":      round(float(group["correct?"].mean()), 3),
                "by_field_type":         type_breakdown,
                "by_nar_inclusion":      inclusion_breakdown,
                "fields": group[[
                    "field", "correct?",
                    "ground_truth_val", "predicted_val",
                    "field_type", "nar_inclusion",
                ]].to_dict(orient="records"),
            },
            eval_table,
            record_id,
        )
    print(f"\n  Saved {df['record_id'].nunique()} records to {eval_table}")
    return df


# ------------------------
# ENTRY POINT

if __name__ == "__main__":

    # 1. Compare qwen vs gemma structured outputs
    run_structured_comparison(
        qwen_table="structured",
        gemma_table="structured_gemma",
    )

    # 2. Evaluate each model against ground truth
    df_qwen  = run_evaluation(gt_path, structured_table="structured",        model_label="qwen")
    df_gemma = run_evaluation(gt_path, structured_table="structured_gemma",  model_label="gemma")

    # 3. Side-by-side field-type comparison
    if df_qwen is not None and df_gemma is not None:
        import pandas as pd
        merged = (
            df_qwen.groupby("field_type")["correct?"].mean().round(3).reset_index()
            .rename(columns={"correct?": "qwen_accuracy"})
            .merge(
                df_gemma.groupby("field_type")["correct?"].mean().round(3).reset_index()
                .rename(columns={"correct?": "gemma_accuracy"}),
                on="field_type", how="outer"
            )
        )
        merged["diff"] = (merged["qwen_accuracy"] - merged["gemma_accuracy"]).round(3)
        print("\n" + "="*60)
        print("FIELD TYPE COMPARISON: QWEN vs GEMMA")
        print("="*60)
        print(merged.sort_values("qwen_accuracy", ascending=False).to_string(index=False))
        merged.to_csv("field_type_comparison.csv", index=False)
        print("\nSaved: field_type_comparison.csv")