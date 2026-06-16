"""
c_structuring/nar_schema_mapper.py
====================================
Maps a raw LLM-structured dict to a clean, flat schema dict.

Function
----------
``map_to_schema`` handles the key-name variants produced by different VLMs
so that downstream evaluation always works with consistent field names.

note::
    This mapper operates on the **required** 98-field subset
    (``NARRecord``), not the full 120-field schema.  It is called after
    ``nullify_unticked_bools`` and before DB persistence.

Public API
----------
map_to_schema(structured_output) -> dict
    Convert a structured LLM output dict to a flat schema-aligned dict.
"""

from __future__ import annotations

from utils.schema_helpers import get_true_option  # type: ignore[import]


def map_to_schema(structured_output: dict) -> dict:
    """Map a structured LLM output dict to flat, schema-aligned field names.

    Handles key-name variants across different VLM output styles by checking
    multiple candidate keys before falling back to ``None``.

    Parameters
    ----------
    structured_output: Dict produced by the LLM structuring step (required fields only).

    Returns
    -------
    dict
        Flat dict keyed by canonical schema field names.
    """
    # Section aliases — different VLMs use different key names for the same
    # section.  Each helper picks the first non-None candidate.
    infant: dict = (
        structured_output.get("A: Infant Details")
        or structured_output.get("Infant Details")
        or {}
    )

    section_ab: dict = (
        structured_output.get("A: B")
        or structured_output.get("A_B")
        or {}
    )

    symptoms: dict = (
        structured_output.get("E: History and examination", {}).get("Symptoms", {})
        or structured_output.get("History and examination", {}).get(
            "Symptoms & History", {}
        )
        or {}
    )

    # --- Sex ----------------------------------------------------------------
    sex: str | None = None
    if "Sex" in infant:
        sex = get_true_option(infant["Sex"])
    elif infant.get("Sex_F"):
        sex = "F"
    elif infant.get("Sex_M"):
        sex = "M"
    elif infant.get("Sex_I"):
        sex = "I"

    # --- Mode of delivery ---------------------------------------------------
    delivery: str | None = None
    if "Delivery" in infant:
        delivery = get_true_option(infant["Delivery"])
    else:
        for mode in ("SVD", "CS", "Vacuum", "Forceps", "Breech"):
            if infant.get(f"Delivery_{mode}"):
                delivery = mode
                break

    return {
        "sex": sex,
        "delivery": delivery,
        "born_outside": infant.get("Born_outside_facility_Y", False),
        "multiple_delivery": infant.get("Multiple_delivery_Y", False),
        "crackles": section_ab.get("Crackles_Y", False),
        "reduced_movement": symptoms.get("Reduced / Absent movement_Y", False),
    }