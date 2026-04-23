import pandas as pd
from difflib import SequenceMatcher

# ------------------------
# FUZZY MATCH

def fuzzy_match(a, b, threshold=0.85):
    """
        Returns True if similarity between a and b >= threshold.
        """
    if a is None or b is None:
        return 0.0

    return 1.0 if SequenceMatcher(None, str(a), str(b)).ratio() >= threshold else 0.0


# ------------------------
# NORMALIZE VALUES

def normalize(value):
    if value is None:
        return None

    return str(value).strip().lower()


# ------------------------
# FLATTEN JSON

def flatten_dict(d, parent_key="", sep="."):
    """
    Flatten nested JSON into flat key-value pairs
    """
    items = {}

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v

    return items


# ------------------------
# FIELD-LEVEL ACCURACY

def compute_field_accuracy(pred: dict, truth: dict):
    """
    Returns dict: field -> accuracy (not accurate-0 or accurate-1)
    """

    pred_flat = flatten_dict(pred)
    truth_flat = flatten_dict(truth)

    results = {}

    for key in truth_flat:
        pred_val = normalize(pred_flat.get(key))
        truth_val = normalize(truth_flat.get(key))

        results[key] = fuzzy_match(pred_val, truth_val)

    return results


# ------------------------
# BUILD TABLE

def build_accuracy_table(predictions: dict, ground_truth: dict):
    """
    predictions: {record_id: dict}
    ground_truth: {record_id: dict}

    returns: pandas DataFrame
    """

    rows = []

    for record_id, truth in ground_truth.items():
        pred = predictions.get(record_id)

        if not pred:
            continue

        field_acc = compute_field_accuracy(pred, truth)

        for field, acc in field_acc.items():
            rows.append({
                "record_id": record_id,
                "field": field,
                "correct?": acc
            })

    df = pd.DataFrame(rows)

    return df