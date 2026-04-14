import re

def normalize_json_quotes(raw_text: str) -> str:
    """
    Fix single quotes to double quotes for JSON compatibility
    for values and keys
    """

    fixed = re.sub(r":\s*'([^']*)'", r': "\1"', raw_text)
    fixed = re.sub(r"'([^']*)'\s*:", r'"\1":', fixed)

    return fixed