import json
import os

from database_utils.db_utils import fetch_records
from database_utils.db_save import safe_save
from d_evaluation.field_accuracy import build_accuracy_table

gt_path="/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/metadata/NAR_metadata.json"

# ------------------------
# LOAD STRUCTURED DATA FROM DB

def load_structured_outputs(table_name="structured"):
    records = fetch_records(table_name)

    predictions = {}

    for r in records:
        raw_id = r.get("id")

        if not raw_id:
            continue

        # SurrealDB format: "structured:NAR_630001"
        record_id = str(raw_id).split(":")[-1]

        structured = r.get("structured_text")

        if structured:
            predictions[record_id] = structured

    return predictions

# ------------------------

def load_and_process_meta(gt_path: str):
    """
    Loads metadata and returns:
    {record_id: merged_record}
    """
    predictions = load_structured_outputs(table_name="structured")
    with open(gt_path) as f:
        raw_gt = json.load(f)

    # ------------------------
    # CASE 1: Already dict → just filter
    if isinstance(raw_gt, dict):
        return {
            k: v for k, v in raw_gt.items()
            if k in predictions  #this is the structured data
        }

    # ------------------------
    # CASE 2: list → convert
    gt_dict = {}

    for item in raw_gt:
        file_id = item.get("_id", "")

        # keep only NAR
        if not file_id.startswith("NAR_"):
            continue

        base_id = file_id.split("_page_")[0]

        # only keep if we actually predicted it
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
# MAIN EVALUATION RUNNER

def run_evaluation(gt_path, structured_table="structured"):
    """
    Runs field-level d_evaluation and saves results
    """

    if not os.path.exists(gt_path):
        print("Ground truth file not found, skipping d_evaluation.")
        return None

    print("\n Running evaluation...\n")

    # Load predictions
    predictions = load_structured_outputs(structured_table)

    # Load GT
    ground_truth = load_and_process_meta(gt_path)

    # Compute table
    df = build_accuracy_table(predictions, ground_truth)
    print(df.head())

    # Save raw table
    df.to_csv("field_accuracy.csv", index=False)

    # -------- summaries --------
    field_summary = (
        df.groupby("field")["correct?"]
        .mean()
        .reset_index()
        .sort_values(by="correct?", ascending=False)
    )

    print("\n FIELD ACCURACY:\n")
    print(field_summary)

    record_summary = (
        df.groupby("record_id")["correct?"]
        .mean()
        .reset_index()
    )
 #########################################################################################################
    print("\n RECORD ACCURACY:\n")
    print(record_summary.head())

    # -------- save per record --------
    print(f"Total rows in df: {len(df)}")

    for record_id, group in df.groupby("record_id"):
        print(f"Saving record: {record_id}, fields: {len(group)}")

    for record_id, group in df.groupby("record_id"):
        safe_save(
            {
                "record_id": record_id,
                "average_accuracy": group["correct?"].mean(),
                "fields": group[["field", "correct?"]].to_dict(orient="records")
            },
            "evaluation",
            record_id
        )

    return df