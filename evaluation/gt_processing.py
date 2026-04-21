import re
import json
from collections import defaultdict

# ------------------------

def load_and_process_meta(path: str):
    """
    Loads metadata and returns:
    {record_id: merged_record}
    """

    grouped = defaultdict(dict)

    with open(path, "r") as f:
        data = json.load(f)

    for item in data:
        file_id = item.get("_id", "")

        # ------------------------
        # KEEP ONLY NAR
        if not file_id.startswith("NAR_"):
            continue

        # ------------------------
        # EXTRACT BASE ID
        base_id = file_id.split("_page_")[0]

        # ------------------------
        # MERGE PAGE DATA
        for k, v in item.items():
            if k == "_id":
                continue

            if k not in grouped[base_id] or grouped[base_id][k] in [None, "", "null"]:
                grouped[base_id][k] = v

    return dict(grouped)










# ------------------------
# EXTRACT ID

def extract_base_id(file_id: str):
    match = re.match(r"(NAR_\d+)_page_\d+", file_id)
    return match.group(1) if match else None


# ------------------------
# FILTER ONLY NAR

def is_nar_record(file_id: str):
    return file_id.startswith("NAR_")


# ------------------------
# MERGE LOGIC

def merge_pages(d1, d2):
    merged = dict(d1)

    for k, v in d2.items():
        if k == "_id":
            continue

        if k not in merged or merged[k] in [None, "", "null"]:
            merged[k] = v

    return merged


# ------------------------
# MAIN FUNCTION

def combine_gt(raw_gt):
    """
    Filters + merges page-level GT → record-level GT
    """

    grouped = defaultdict(dict)

    for item in raw_gt:
        file_id = item.get("_id", "")

        if not is_nar_record(file_id):
            continue

        base_id = extract_base_id(file_id)

        if not base_id:
            continue

        grouped[base_id] = merge_pages(grouped[base_id], item)

    return dict(grouped)