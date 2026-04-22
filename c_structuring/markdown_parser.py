import json
import re


def try_parse_json(text: str) -> dict | None:
    """
    Safely parse JSON string.
    """
    try:
        return json.loads(text)
    except Exception:
        return None


def parse_markdown_kv(text: str) -> dict:
    """
    Parse simple markdown key-value pairs.
    """
    data = {}

    for line in text.split("\n"):
        match = re.match(r"-\s*(.*?):\s*(.*)", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            if value.lower() in ["", "-", "n/a", "na"]:
                value = "N/A"

            data[key] = value

    return data


def markdown_to_dict(text: str) -> dict:
    """
    Unified parser: JSON first, fallback to markdown.
    """
    text = re.sub(r"```(\w+)?", "", text).strip()

    json_data = try_parse_json(text)
    if json_data:
        return json_data

    return parse_markdown_kv(text)