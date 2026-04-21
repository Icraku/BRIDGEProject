import json
import os

from db.db_utils import fetch_records
from db.db_save import safe_save
from evaluation.gt_processing import load_and_process_meta
from evaluation.field_accuracy import build_accuracy_table

gt_path="/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/metadata/metadata.json"


# ------------------------
# LOAD STRUCTURED DATA FROM DB

def load_structured_outputs(table_name="structured_T3"):
    records = fetch_records(table_name)

    predictions = {}

    for r in records:
        record_id = str(r.get("id")).split(":")[1]

        structured = r.get("structured_text")

        if structured:
            predictions[record_id] = structured

    return predictions


# ------------------------
# MAIN EVALUATION RUNNER

def run_evaluation(gt_path, structured_table="structured"):
    """
    Runs field-level evaluation and saves results
    """

    if not os.path.exists(gt_path):
        print("Ground truth file not found, skipping evaluation.")
        return None

    print("\n📊 Running evaluation...\n")

    # Load GT
    ground_truth = load_and_process_meta(gt_path)

    # Load predictions
    predictions = load_structured_outputs(structured_table)

    # Compute table
    df = build_accuracy_table(predictions, ground_truth)

    # Save CSV
    df.to_csv("field_accuracy.csv", index=False)

    print(" Saved field_accuracy.csv")

    # Summary
    summary = df.mean(numeric_only=True)

    print("\n FIELD AVERAGES:\n")
    print(summary)

    for _, row in df.iterrows():
        record_id = row["record_id"]

        safe_save(
            row.to_dict(),
            "evaluation",
            record_id
        )

    return df