import pandas as pd
from difflib import SequenceMatcher
from schemas.neonatal_admission_form.field_types import FIELD_TYPES
from schemas.neonatal_admission_form.nar_full_schema import FULL_SCHEMA_FIELDS, inclusion_status

# ------------------------
# FUZZY MATCH

def fuzzy_match(a, b, threshold=0.85):
    """
    Returns 1.0 if similarity between a and b >= threshold, else 0.0.
    Returns 0.0 if either value is None/empty (no prediction or no truth).
    """
    if a is None or b is None:
        return 0.0
    a_s = str(a).strip()
    b_s = str(b).strip()
    if not a_s and not b_s:
        return 1.0   # both empty → correct
    if not a_s or not b_s:
        return 0.0   # one empty → wrong
    return 1.0 if SequenceMatcher(None, a_s, b_s).ratio() >= threshold else 0.0


# ------------------------
# NORMALIZE VALUES

def normalize(value):
    if value is None:
        return None

    return str(value).strip().lower().rstrip(";").strip()


# ------------------------
# FLATTEN JSON

def flatten_dict(d, parent_key="", sep="."):
    """Flatten nested JSON into flat key-value pairs."""
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
    Compare predicted vs ground-truth for every field in the
    UNION of predicted keys, ground-truth keys, and FULL_SCHEMA_FIELDS.

    Fields missing from ground truth are treated as None (no GT available).
    Fields missing from predictions are treated as None (not extracted).

    Returns dict: field -> {accuracy, ground_truth_val, predicted_val, has_gt}
    """
    pred_flat  = flatten_dict(pred)
    truth_flat = flatten_dict(truth)

    # All fields we want to report on
    all_keys = FULL_SCHEMA_FIELDS | set(pred_flat.keys()) | set(truth_flat.keys())

    results = {}
    for key in all_keys:
        pred_val  = normalize(pred_flat.get(key))
        truth_val = normalize(truth_flat.get(key))
        has_gt    = key in truth_flat and truth_flat[key] not in (None, "", "null")

        results[key] = {
            "accuracy":          fuzzy_match(pred_val, truth_val) if has_gt else None,
            "ground_truth_val":  truth_val,
            "predicted_val":     pred_val,
            "has_gt":            has_gt,
        }

    return results


# ------------------------
# BUILD TABLE

def build_accuracy_table(predictions: dict, ground_truth: dict) -> pd.DataFrame:
    """
    predictions:  {record_id: dict}
    ground_truth: {record_id: dict}

    Returns a DataFrame with one row per (record_id, field).

    Columns:
      record_id, field, field_type, nar_inclusion,
      correct?,        # fuzzy accuracy 0/1, or None if no GT
      has_gt,          # True if ground truth exists for this field
      ground_truth_val, predicted_val
    """
    rows = []

    for record_id, truth in ground_truth.items():
        pred = predictions.get(record_id)
        if not pred:
            continue

        field_acc = compute_field_accuracy(pred, truth)

        for field, info in field_acc.items():
            rows.append({
                "record_id":        record_id,
                "field":            field,
                "field_type":       FIELD_TYPES.get(field, "unknown"),
                "nar_inclusion":    inclusion_status(field),
                "correct?":         info["accuracy"],   # None if no GT available
                "has_gt":           info["has_gt"],
                "ground_truth_val": info["ground_truth_val"],
                "predicted_val":    info["predicted_val"],
            })

    df = pd.DataFrame(rows)

    # ────────────────────────────────────────────────────
    total      = len(df["field"].unique())
    with_gt    = df[df["has_gt"]]["field"].nunique()
    without_gt = df[~df["has_gt"]]["field"].nunique()
    included   = df[df["nar_inclusion"] == "included"]["field"].nunique()
    not_inc    = df[df["nar_inclusion"] == "not included"]["field"].nunique()

    print(f"\n[build_accuracy_table] {len(ground_truth)} GT records matched")
    print(f"  Unique fields total    : {total}")
    print(f"  Fields with GT         : {with_gt}")
    print(f"  Fields without GT      : {without_gt}  ← now shown, accuracy=None")
    print(f"  NARRecord (included)   : {included}")
    print(f"  Supplementary (not inc): {not_inc}")
    print(f"  DataFrame shape        : {df.shape}")
    print(f"  Columns                : {df.columns.tolist()}\n")
    # ─────────────────────────────────────────────────────────────────

    return df