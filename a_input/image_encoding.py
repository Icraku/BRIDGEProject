"""
a_input/image_encoding.py
=========================
Utilities for converting image files into base64-encoded strings for VLM input.

Public API
----------
image_to_base64(image_path)
    Read an image from disk and return a UTF-8 base64 string.
"""

import base64


# ---------------------------------------------------------------------------
# Image encoding

def image_to_base64(image_path: str) -> str:
    """Read an image file and return a base64-encoded string."""
    with open(image_path, "rb") as file_handle:
        return base64.b64encode(file_handle.read()).decode("utf-8")