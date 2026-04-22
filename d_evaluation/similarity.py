from difflib import SequenceMatcher

def fuzzy_equal(a, b, threshold: float = 0.85) -> bool:
    """
    Returns True if similarity between a and b >= threshold.
    """
    return SequenceMatcher(None, str(a), str(b)).ratio() >= threshold