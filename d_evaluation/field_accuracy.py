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

# Field types where accuracy scoring is not meaningful
UNSCORABLE_TYPES = {"redacted", "text"}

def compute_field_accuracy(pred: dict, truth: dict):
    """
    Compare predicted vs ground-truth for every field in the union of:
      - FULL_SCHEMA_FIELDS
      - predicted keys
      - ground-truth keys

    Returns dict: field → {accuracy, ground_truth_val, predicted_val, has_gt, scorable}

    accuracy is None when:
      - has_gt is False (no ground truth to judge against), OR
      - scorable is False (field type is redacted or text)
    """
    pred_flat  = flatten_dict(pred)
    truth_flat = flatten_dict(truth)

    # All fields we want to report on
    all_keys = FULL_SCHEMA_FIELDS | set(pred_flat.keys()) | set(truth_flat.keys())

    results = {}
    for key in all_keys:
        pred_val  = normalize(pred_flat.get(key))
        truth_val = normalize(truth_flat.get(key))

        has_gt   = key in truth_flat and truth_flat[key] not in (None, "", "null")
        ftype    = FIELD_TYPES.get(key, "unknown")
        scorable = ftype not in UNSCORABLE_TYPES

        if has_gt and scorable:
            accuracy = fuzzy_match(pred_val, truth_val)
        else:
            accuracy = None

        results[key] = {
            "accuracy":         accuracy,
            "ground_truth_val": truth_val,
            "predicted_val":    pred_val,
            "has_gt":           has_gt,
            "scorable":         scorable,
        }

    return results


# ------------------------
# BUILD TABLE

def build_accuracy_table(predictions: dict, ground_truth: dict) -> pd.DataFrame:
    """
    Returns a DataFrame with one row per (record_id, field).

    Columns:
      record_id, field, field_type, nar_inclusion,
      correct?,        # fuzzy accuracy 0/1, or None if no GT
      has_gt,          # True if ground truth exists for this field
      scorable         — False for redacted/text fields
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
                "scorable":         info["scorable"],
                "ground_truth_val": info["ground_truth_val"],
                "predicted_val":    info["predicted_val"],
            })

    df = pd.DataFrame(rows)

    # ─────────────────────────────────────────────────────────────────
    scored      = df[df["scorable"] & df["has_gt"]]
    unscored_gt = df[~df["scorable"] & df["has_gt"]]
    no_gt       = df[~df["has_gt"]]

    print(f"\n[build_accuracy_table] {len(ground_truth)} GT records matched")
    print(f"  Total rows              : {len(df)}")
    print(f"  Scored (has_gt+scorable): {len(scored)}  ← accuracy computed")
    print(f"  Unscorable type (text/redacted) with GT: {len(unscored_gt)}  ← value shown, no score")
    print(f"  No ground truth         : {len(no_gt)}  ← supplementary fields")
    print(f"  Unique fields total     : {df['field'].nunique()}")
    print(f"  NARRecord (included)    : {df[df['nar_inclusion']=='included']['field'].nunique()}")
    print(f"  Supplementary           : {df[df['nar_inclusion']=='not included']['field'].nunique()}")
    print(f"  Columns                 : {df.columns.tolist()}\n")
    # ─────────────────────────────────────────────────────────────────

    return df