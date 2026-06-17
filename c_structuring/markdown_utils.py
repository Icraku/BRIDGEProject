"""
c_structuring/markdown_utils.py
================================
Utilities for converting between raw LLM text output and Python dicts.

The structuring stage needs the Markdown text from the extraction stage
    to be parsed into a dict before it can be passed to the schema.
    This module centralises both directions of that conversion.

Functions
---------
markdown_to_dict(text)
    Parse LLM output (JSON or key-value markdown) into a dict.

dict_to_markdown(data)
    Serialise a dict back to a simple Markdown list (used only when merging
    multi-prompt outputs into a single human-readable string).
"""

from __future__ import annotations

import json
import re


# ---------------------------------------------------------------------------
# markdown → dict
# ---------------------------------------------------------------------------


def _try_parse_json(text: str) -> dict | None:
    """Attempt to parse *text* as JSON, returning ``None`` on failure."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _parse_markdown_kv(text: str) -> dict:
    """Parse a markdown bullet list of ``- key: value`` pairs into a dict.

    Lines that do not match the pattern are silently ignored.  Values that
    look empty or missing (``""``, ``"-"``, ``"n/a"``, ``"na"``) are stored
    as the string ``"N/A"`` for downstream normalisation.

    .. note::
        The ``"N/A"`` sentinel is intentional here: it preserves the
        distinction between a field the LLM explicitly left blank versus a
        field it never mentioned.  Downstream normalisation in
        ``d_evaluation/normalizers.py`` maps ``"N/A"`` → ``None`` before
        any accuracy calculation.
    """
    data: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"-\s*(.*?):\s*(.*)", line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        if value.lower() in {"", "-", "n/a", "na"}:
            value = "N/A"
        data[key] = value
    return data


def markdown_to_dict(text: str) -> dict:
    """Parse raw LLM output into a Python dict.

    Tries JSON first (the preferred format); falls back to simple
    key-value markdown parsing if the output is not valid JSON.
    Code fences (`` ```json … ``` ``) are stripped before parsing.

    Parameters
    ----------
    text: Raw string returned by the VLM.

    Returns
    -------
    dict
        Parsed field-value mapping.
    """
    # Strip Markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"```(\w+)?", "", text).strip()

    json_result = _try_parse_json(text)
    if json_result is not None:
        return json_result

    return _parse_markdown_kv(text)


# ---------------------------------------------------------------------------
# dict → markdown
# ---------------------------------------------------------------------------


def dict_to_markdown(data: dict) -> str:
    """Serialise a field-value dict to a simple markdown bullet list.

    Used to produce a human-readable merged output when multiple prompts
        are run on the same image and their parsed dicts are combined.

    Parameters
    ----------
    data: Field-value mapping to serialise.

    Returns
    -------
    str
        Markdown string with one ``- field: value`` line per entry.
    """
    lines = ["## Final Extraction", ""]
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)