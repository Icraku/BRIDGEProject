from d_evaluation.similarity import fuzzy_equal

def compute_accuracy(pred: dict, truth: dict) -> float:
    """
    Computes field-level accuracy between prediction and ground truth.
    """
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return 0.0

    if len(truth) == 0:
        return 0.0

    correct = 0

    for key, true_value in truth.items():
        pred_value = pred.get(key)

        if pred_value is None:
            continue

        if pred_value == true_value or fuzzy_equal(pred_value, true_value):
            correct += 1

    return correct / len(truth)