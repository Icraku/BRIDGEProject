import re

def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from text.
    """
    return re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()