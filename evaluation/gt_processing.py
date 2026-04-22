import re
import json
from collections import defaultdict

from evaluation.run_evaluation import load_structured_outputs


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