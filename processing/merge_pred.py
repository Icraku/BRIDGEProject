from collections import Counter
from typing import List, Dict, Any

def merge_predictions(pred_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple prediction dictionaries using majority voting.
    """

    merged = {}
    all_keys = set()

    for d in pred_dicts:
        all_keys.update(d.keys())

    for key in all_keys:
        values = [d.get(key, "N/A") for d in pred_dicts]

        # majority vote
        most_common_value = Counter(values).most_common(1)[0][0]
        merged[key] = most_common_value

    return merged