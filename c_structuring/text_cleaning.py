"""
c_structuring/text_cleaning.py
==============================
Text cleanup helpers used before and after markdown parsing.

Public API
----------
strip_markdown_fences(text)
    Remove fenced code block markers from markdown-like text.
"""

import re


# ---------------------------------------------------------------------------
# Markdown cleanup

def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from *text* and trim surrounding space."""
    return re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()