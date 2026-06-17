"""
c_structuring/schema_helpers.py
===============================
Helpers for reading schema-shaped dictionaries produced by the structuring
pipeline.

Public API
----------
get_true_option(field_dict)
    Return the first key whose value is ``True``.

get_boolean_from_suffix(data, base_key)
    Read a ``*_Y`` boolean flag from a structured record.
"""


# ---------------------------------------------------------------------------
# Option and boolean helpers

def get_true_option(field_dict: dict) -> str | None:
    """Return the first dictionary key whose value is ``True``."""
    if not isinstance(field_dict, dict):
        return None

    for key, value in field_dict.items():
        if value is True:
            return key

    return None


def get_boolean_from_suffix(data: dict, base_key: str) -> bool:
    """Extract a boolean flag from suffixed keys such as ``*_Y``."""
    return data.get(f"{base_key}_Y", False)