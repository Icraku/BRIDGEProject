"""
c_structuring/bool_nullifier.py
================================
Post-processing step that corrects boolean fields in the structured output.

Problem
-------
LLMs with structured output (``with_structured_output``) default missing
booleans to ``False``.  On a Neonatal Admission Record form, an unchecked
checkbox should be ``None`` (unknown / not assessed), not ``False``
(explicitly negative).  Without correction, every blank checkbox inflates
the true-negative count and deflates recall metrics.

Solution
--------
After the LLM produces a structured dict, ``nullify_unticked_bools`` reads
back the raw markdown and checks each bool field:

- If the LLM returned ``False`` **and** the markdown shows the field was
  blank (no ``[x]`` in either the Y or N column), override → ``None``.
- If the LLM returned ``False`` **and** the markdown confirms ``N [x]``,
  keep ``False`` (explicit negative).
- If the LLM returned ``True``, always trust it (positives are reliable).

Public API
----------
nullify_unticked_bools(structured_dict, markdown_text) -> dict
    Returns a corrected copy of *structured_dict*.

BOOL_FIELD_LABELS : dict[str, list[str]]
    Maps every bool field name to the label(s) it appears under in the
    extracted markdown.  Imported by ``structuring_pipeline.py`` to build
    the ``BOOL_FIELDS`` set used by ``clean_for_db``.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label map

# Maps each bool field in NARRecord to the label(s) as they appear in the
# extracted markdown.  Multiple variants handle VLM-specific capitalisation
# or abbreviation differences (e.g. Qwen vs Gemma vs Medgemma output styles).

BOOL_FIELD_LABELS: dict[str, list[str]] = {
    "born_before_arrival":               ["born outside facility?", "born outside facility"],
    "was_resuscitated":                  ["bvm resus at birth?", "bvm resus at birth"],
    "is_multiple_delivery":              ["multiple delivery"],
    "has_apnoea":                        ["apnoea"],
    "has_convulsions":                   ["convulsions / twitching", "convulsions"],
    "has_diarhoea":                      ["diarhoea"],
    "has_difficulty_breathing":          ["difficulty breathing"],
    "has_difficulty_feeding":            ["inability to feed"],
    "has_fever":                         ["fever"],
    "has_vomiting":                      ["bilious vomiting"],
    "is_floppy":                         ["floppy", "reduced / absent movement"],
    "passed_meconium":                   ["passed meconium/stool", "passed meconium"],
    "passed_urine":                      ["passed urine in the last 12 hours", "passed urine"],
    "prolonged_labour":                  ["prolonged 2nd stage?", "prolonged 2nd stage"],
    "mum_given_HBIG_treatment":          ["hep b ig given"],
    "mum_had_antepartum_haemorrhage":    ["aph"],
    "mum_had_diabetes":                  ["diabetes"],
    "mum_had_hepatitis_b":               ["hep b"],
    "mum_had_hypertension_in_pregnancy": ["htn in pregnancy?", "htn in pregnancy"],
    "mum_had_vdrl":                      ["vdrl"],
    "mum_has_anc_ultrasound":            ["anc u/s", "anc"],
    "mum_on_arvs":                       ["mother on arvs"],
    "mum_pmtct_status":                  ["pmtct status"],
    "has_crackles":                      ["crackles", "cracles"],
    "has_grunting":                      ["grunting"],
    "has_good_air_entry":                ["good bilateral air entry"],
    "has_central_cyanosis":              ["central cyanosis"],
    "has_murmur":                        ["murmur"],
    "has_bulging_fontanelle":            ["bulging fontanelle"],
    "is_irritable":                      ["irritable"],
    "is_distended":                      ["distension"],
    "has_birth_defects":                 ["birth defects?", "birth defects"],
    "rbs_measured":                      ["rbs"],
    "given_bilirubin":                   ["bilirubin"],
    "given_vitamin_k":                   ["vit k & teo", "vit k & theo", "vit k"],
    "given_bcg":                         ["bcg"],
    "given_chlorhexidine":               ["chlorhexidine"],
    "given_prophylaxis_pmtct":           ["prophylaxis for pmtct"],
    "prescribed_transfusion":            ["transfusion"],
    "prescribed_phototherapy":           ["phototherapy"],
    "prescribed_cpap":                   ["cpap"],
    "prescribed_iv_fluids":              ["iv fluids"],
    "prescribed_antibiotics":            ["antibiotics"],
    "prescribed_feeds":                  ["nutrition/feeds", "feeds"],
    "prescribed_opv":                    ["opv"],
    "prescribed_surfactant":             ["surfactant"],
    "prescribed_caffeine_citrate":       ["caffeine citrate"],
    "prescribed_oxygen":                 ["oxygen"],
    "prescribed_kmc":                    ["kmc"],
    "prescribed_incubator":              ["incubator/ keep warm", "incubator"],
}

# ---------------------------------------------------------------------------
# Internal helpers

_POSITIVE_TOKENS: frozenset[str] = frozenset({"Y", "y", "YES", "yes", "POS", "pos", "POSITIVE", "positive"})
_NEGATIVE_TOKENS: frozenset[str] = frozenset({"N", "n", "NO", "NEG", "neg", "neg", "NEGATIVE", "negative"})


def _adjacent_label(line: str) -> str | None:
    """Return the label token immediately adjacent to a ticked ``[x]`` marker.

    Scans *line* for bracket tokens ``[x]`` / ``[X]`` and word tokens, then
    returns the word directly before (Qwen style: ``N [x]``) or after
    (Gemma style: ``[x] N``) the tick.

    Parameters
    ----------
    line: A single line of extracted markdown.

    Returns
    -------
    str | None
        The adjacent label in upper case, or ``None`` if no ``[x]`` was
        found on this line.
    """
    tokens: list[tuple[str, str, int]] = []  # (kind, value, position)
    for match in re.finditer(r"\[([xX ])\]|([A-Za-z][A-Za-z0-9+/\-]*)", line):
        if match.group(1) is not None:
            tokens.append(("bracket", match.group(1), match.start()))
        elif match.group(2):
            tokens.append(("label", match.group(2).strip(), match.start()))

    ticked_idx = next(
        (i for i, (kind, val, _) in enumerate(tokens)
         if kind == "bracket" and val.lower() == "x"),
        None,
    )
    if ticked_idx is None:
        return None  # nothing ticked on this line

    # Prefer the token immediately before [x]; fall back to after
    if ticked_idx > 0 and tokens[ticked_idx - 1][0] == "label":
        return tokens[ticked_idx - 1][1].upper()
    if ticked_idx + 1 < len(tokens) and tokens[ticked_idx + 1][0] == "label":
        return tokens[ticked_idx + 1][1].upper()
    return None


def _field_is_ticked(field_labels: list[str], markdown_text: str) -> bool | None:
    """Determine whether a form field was ticked Yes, No or left blank.

    Parameters
    ----------
    field_labels: All label variants for this field (from ``BOOL_FIELD_LABELS``).
    markdown_text: Full extracted markdown for the record.

    Returns
    -------
    True
        ``[x]`` found adjacent to a positive token (Y / Yes / Pos).
    False
        ``[x]`` found adjacent to a negative token (N / No / Neg).
    None
        Label found in markdown but no ``[x]`` on its line (blank field),
        or label not found at all.
    """
    for label in field_labels:
        for line in markdown_text.splitlines():
            if label not in line.lower():
                continue

            adjacent = _adjacent_label(line)
            if adjacent is None:
                return None  # label found, nothing ticked
            if adjacent in _POSITIVE_TOKENS:
                return True
            if adjacent in _NEGATIVE_TOKENS:
                return False
            # [x] found but adjacent token is not Y/N (e.g. a severity word)
            return None

    return None  # label not found anywhere


# ---------------------------------------------------------------------------
# Public API

def nullify_unticked_bools(structured_dict: dict, markdown_text: str) -> dict:
    """Override LLM ``False`` values with ``None`` for blank form checkboxes.

    The LLM's structured-output layer coerces missing booleans to ``False``.
    This function re-examines the raw markdown to distinguish an explicit
    "No" tick (keep ``False``) from a blank field (override → ``None``).

    Only fields where the LLM returned ``False`` are touched; ``True`` and
    existing ``None`` values are left unchanged.

    Parameters
    ----------
    structured_dict: The dict produced by ``NARFullRecord.model_dump()`` after LLM
        extraction.
    markdown_text: The raw markdown string the LLM read from (used to re-check ticks).

    Returns
    -------
    dict
        A corrected copy of *structured_dict*.
    """
    result = dict(structured_dict)

    for field, labels in BOOL_FIELD_LABELS.items():
        if result.get(field) is not False:
            continue  # True and None are trusted as-is

        ticked = _field_is_ticked(labels, markdown_text)
        if ticked is None:
            result[field] = None
            logger.debug("nullify: %s  false → None  (blank in markdown)", field)
        # ticked is False → confirmed negative, keep False
        # ticked is True  → LLM contradicted markdown, leave LLM value

    return result