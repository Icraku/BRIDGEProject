import re

# ------------------------
# BOOL FIELD → MARKDOWN LABEL MAP
# Maps each bool field in NARRecord to the label(s) as they appear in the markdown

BOOL_FIELD_LABELS = {
    "born_before_arrival":              ["born outside facility?", "born outside facility"],
    "was_resuscitated":                 ["bvm resus at birth?", "bvm resus at birth"],
    "is_multiple_delivery":             ["multiple delivery"],
    "has_apnoea":                       ["apnoea"],
    "has_convulsions":                  ["convulsions / twitching", "convulsions"],
    "has_diarhoea":                     ["diarhoea"],
    "has_difficulty_breathing":         ["difficulty breathing"],
    "has_difficulty_feeding":           ["inability to feed"],
    "has_fever":                        ["fever"],
    "has_vomiting":                     ["bilious vomiting"],
    "is_floppy":                        ["floppy", "reduced / absent movement"],
    "passed_meconium":                  ["passed meconium/stool", "passed meconium"],
    "passed_urine":                     ["passed urine in the last 12 hours", "passed urine"],
    "prolonged_labour":                 ["prolonged 2nd stage?", "prolonged 2nd stage"],
    "mum_given_HBIG_treatment":         ["hep b ig given"],
    "mum_had_antepartum_haemorrhage":   ["aph"],
    "mum_had_diabetes":                 ["diabetes"],
    "mum_had_hepatitis_b":              ["hep b"],
    "mum_had_hypertension_in_pregnancy":["htn in pregnancy?", "htn in pregnancy"],
    "mum_had_vdrl":                     ["vdrl"],
    "mum_has_anc_ultrasound":           ["anc u/s", "anc"],
    "mum_on_arvs":                      ["mother on arvs"],
    "mum_pmtct_status":                 ["pmtct status"],
    "has_crackles":                     ["crackles", "cracles"],
    "has_grunting":                     ["grunting"],
    "has_good_air_entry":               ["good bilateral air entry"],
    "has_central_cyanosis":             ["central cyanosis"],
    "chest_indrawing":                  ["lower chest indrawing"],
    "has_murmur":                       ["murmur"],
    "has_bulging_fontanelle":           ["bulging fontanelle"],
    "is_irritable":                     ["irritable"],
    "is_distended":                     ["distension"],
    "has_birth_defects":                ["birth defects?", "birth defects"],
    "rbs_measured":                     ["rbs"],
    "given_bilirubin":                  ["bilirubin"],
    "given_vitamin_k":                  ["vit k & teo", "vit k & theo", "vit k"],
    "given_bcg":                        ["bcg"],
    "given_chlorhexidine":              ["chlorhexidine"],
    "given_prophylaxis_pmtct":          ["prophylaxis for pmtct"],
    "prescribed_transfusion":           ["transfusion"],
    "prescribed_phototherapy":          ["phototherapy"],
    "prescribed_cpap":                  ["cpap"],
    "prescribed_iv_fluids":             ["iv fluids"],
    "prescribed_antibiotics":           ["antibiotics"],
    "prescribed_feeds":                 ["nutrition/feeds", "feeds"],
    "prescribed_opv":                   ["opv"],
    "prescribed_surfactant":            ["surfactant"],
    "prescribed_caffeine_citrate":      ["caffeine citrate"],
    "prescribed_oxygen":                ["oxygen"],
    "prescribed_kmc":                   ["kmc"],
    "prescribed_incubator":             ["incubator/ keep warm", "incubator"],
}


def _adjacent_label(line: str) -> str | None:
    """
    Tokenise a line and return the label token immediately adjacent to [x].
    Checks token before [x] first (qwen: N [x]), then after (gemma: [x] N).
    Returns the label string, or None if nothing checked / ambiguous.
    """
    tokens = []
    for m in re.finditer(r"\[([xX ])\]|([A-Za-z][A-Za-z0-9+/\-]*)", line):
        if m.group(1) is not None:
            tokens.append(("bracket", m.group(1), m.start()))
        elif m.group(2):
            tokens.append(("label", m.group(2).strip(), m.start()))

    checked_idx = next(
        (i for i, (kind, val, _) in enumerate(tokens)
         if kind == "bracket" and val.lower() == "x"),
        None
    )
    if checked_idx is None:
        return None  # nothing ticked on this line

    # prefer label immediately before [x], fall back to after
    if checked_idx > 0 and tokens[checked_idx - 1][0] == "label":
        return tokens[checked_idx - 1][1].upper()
    if checked_idx + 1 < len(tokens) and tokens[checked_idx + 1][0] == "label":
        return tokens[checked_idx + 1][1].upper()
    return None


def _field_is_ticked(field_labels: list, markdown_text: str) -> bool | None:
    """
    Searches the markdown for a line/cell containing the field label.
    Returns:
      True  — [x] found adjacent to Y / Pos
      False — [x] found adjacent to N / Neg
      None  — label found but no [x] on the line (blank / unfilled)
      None  — label not found in markdown at all
    """
    POSITIVE = {"Y", "YES", "POS", "POSITIVE"}
    NEGATIVE = {"N", "NO", "NEG", "NEGATIVE"}

    for label in field_labels:
        for line in markdown_text.split("\n"):
            if label not in line.lower():
                continue

            adjacent = _adjacent_label(line)

            if adjacent is None:
                # Line contains the label but nothing is ticked
                return None

            if adjacent in POSITIVE:
                return True
            if adjacent in NEGATIVE:
                return False

            # [x] found but adjacent label is not Y/N (e.g. severity word)
            # — not a blank field, but not a bool either; leave as-is
            return None

    # Label not found anywhere in markdown
    return None


def nullify_unticked_bools(structured_dict: dict, markdown_text: str) -> dict:
    """
    For every bool field in structured_dict:
      - If the LLM returned False but the markdown shows the field was
        never ticked (blank [ ] [ ]), override with None.
      - If the LLM returned False and the markdown confirms N [x], keep False.
      - If the LLM returned True, always keep True (trust the LLM on positives).

    Returns a new dict with corrections applied.
    """
    result = dict(structured_dict)

    for field, labels in BOOL_FIELD_LABELS.items():
        current_val = result.get(field)

        # Only intervene when the LLM said False — True and None are fine as-is
        if current_val is not False:
            continue

        ticked = _field_is_ticked(labels, markdown_text)

        if ticked is None:
            # Blank field in markdown — override False → None
            result[field] = None
            print(f"    [nullify] {field}: false → None (blank in markdown)")
        # ticked=True  → LLM was wrong to say False, but we leave it
        # ticked=False → LLM correctly said False, keep it

    return result