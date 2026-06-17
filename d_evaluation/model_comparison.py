"""
d_evaluation/model_comparison.py
==================================
Compares raw markdown extraction outputs between two models
(e.g. Qwen vs Gemma) at the field level, **before** structured output
is produced.

This module operates on the ``extractions_*`` tables written by Stage A
(``b_extraction/extraction_pipeline.py``), not the structured output tables.
It parses each model's raw markdown independently and compares normalised
field values side-by-side.

Use this when you want to understand inter-model agreement at the extraction
stage, independently of ground truth.  For GT-based accuracy comparison use
``evaluation_pipeline.run_full_metrics_suite`` instead.

Outputs
-------
``extraction_comparison.csv``
    One row per ``(record_id, field)`` with both models' raw and normalised
    values and a ``match_status`` column.

SurrealDB table ``comparison``
    Per-record agreement summary and full field-level comparison dict,
    for interactive exploration.

Public API
----------
run_comparison(qwen_table, gemma_table, output_table, output_csv)
    Run the full extraction-level comparison.
"""

from __future__ import annotations

import csv
import logging
import re
from datetime import datetime
from pathlib import Path

from database_utils.db_utils import fetch_records, save_record
from schemas.neonatal_admission_form.field_types import FIELD_TYPES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration defaults

_DEFAULT_QWEN_TABLE   = "extractions"
_DEFAULT_GEMMA_TABLE  = "extractions_gemma"
_DEFAULT_OUTPUT_TABLE = "comparison"
_DEFAULT_OUTPUT_CSV   = "extraction_comparison.csv"

# ---------------------------------------------------------------------------
# Field alias map

# Maps each canonical schema field name to the label variants that appear in
# raw markdown output.  Multiple variants handle differences in how Qwen, Medgemma and
# Gemma render the same form label.

FIELD_ALIASES: dict[str, list[str]] = {
    "admission_date":                    ["date of admission"],
    "time_seen":                         ["time baby seen (24 hr clock)", "time baby seen"],
    "sex":                               ["sex"],
    "date_of_birth":                     ["dob", "date of birth"],
    "time_birth":                        ["time of birth (24 hr clock)", "time of birth"],
    "gestation_in_weeks":                ["gestation (in weeks)", "gestation"],
    "baby_age_in_days":                  ["age (in days)", "age in days"],
    "gestation_type":                    ["gestation age from?", "gestation age from"],
    "_apgar_combined":                   ["apgar"],
    "delivery_type":                     ["delivery"],
    "had_cs":                            ["if cs, type"],
    "was_resuscitated":                  ["bvm resus at birth?", "bvm resus at birth"],
    "rapture_of_membrane":               ["rom"],
    "is_multiple_delivery":              ["multiple delivery"],
    "multiple_delivery_num":             ["if yes, number"],
    "born_before_arrival":               ["born outside facility?", "born outside facility"],
    "born_where":                        ["if yes, where?"],
    "mum_age_in_years":                  ["age (years)"],
    "_parity_combined":                  ["parity"],
    "date_estimated_delivery_date":      ["edd"],
    "anc_visits":                        ["anc no. of visits", "anc no of visits"],
    "mum_has_anc_ultrasound":            ["anc u/s", "anc"],
    "blood_group":                       ["blood group"],
    "rhesus":                            ["rhesus"],
    "given_anti_D_medication":           ["anti d"],
    "mum_had_vdrl":                      ["vdrl"],
    "mum_pmtct_status":                  ["pmtct status"],
    "mum_on_arvs":                       ["mother on arvs"],
    "mum_had_hepatitis_b":               ["hep b"],
    "mum_given_HBIG_treatment":          ["hep b ig given"],
    "mum_had_hypertension_in_pregnancy": ["htn in pregnancy?", "htn in pregnancy"],
    "mum_had_antepartum_haemorrhage":    ["aph"],
    "mum_had_diabetes":                  ["diabetes"],
    "prolonged_labour":                  ["prolonged 2nd stage?", "prolonged 2nd stage"],
    "head_circumference":                ["head circumference (cm)", "head circumference"],
    "length":                            ["length (cm)", "length"],
    "temparature":                       ["temp"],
    "respiratory_rate":                  ["resp rate"],
    "_bp_combined":                      ["blood pressure"],
    "pulse_rate":                        ["pulse"],
    "pulse_oximetry":                    ["o2 sat (%)", "o2 sat"],
    "birth_weight":                      ["birth weight (grams)", "birth weight"],
    "weight":                            ["weight now (grams)", "weight now"],
    "has_fever":                         ["fever"],
    "passed_meconium":                   ["passed meconium/stool", "passed meconium"],
    "has_difficulty_breathing":          ["difficulty breathing"],
    "passed_urine":                      ["passed urine in the last 12 hours", "passed urine"],
    "has_difficulty_feeding":            ["inability to feed"],
    "has_convulsions":                   ["convulsions / twitching", "convulsions"],
    "has_apnoea":                        ["apnoea"],
    "has_vomiting":                      ["bilious vomiting"],
    "skin":                              ["skin"],
    "jaundice":                          ["jaundice"],
    "appearance":                        ["appearance"],
    "cry":                               ["cry"],
    "has_crackles":                      ["crackles", "cracles"],
    "has_grunting":                      ["grunting"],
    "has_good_air_entry":                ["good bilateral air entry"],
    "has_central_cyanosis":              ["central cyanosis"],
    "chest_indrawing":                   ["lower chest indrawing"],
    "xiphoid_retraction":                ["xiphoid retraction"],
    "intercostal_retraction":            ["intercostal retraction"],
    "capillary_refill_in_seconds":       ["capillary refill (sternal)", "capillary refill"],
    "pallor":                            ["pallor/anaemia", "pallor"],
    "has_murmur":                        ["murmur"],
    "has_bulging_fontanelle":            ["bulging fontanelle"],
    "is_irritable":                      ["irritable"],
    "tone":                              ["tone"],
    "is_distended":                      ["distension"],
    "umbilicus":                         ["umbilicus"],
    "has_birth_defects":                 ["birth defects?", "birth defects"],
    "given_bilirubin":                   ["bilirubin"],
    "rbs_measured":                      ["rbs"],
    "given_vitamin_k":                   ["vit k & teo", "vit k & theo", "vit k"],
    "prescribed_caffeine_citrate":       ["caffeine citrate"],
    "prescribed_oxygen":                 ["oxygen"],
    "given_prophylaxis_pmtct":           ["prophylaxis for pmtct"],
    "given_bcg":                         ["bcg"],
    "given_chlorhexidine":               ["chlorhexidine"],
    "prescribed_kmc":                    ["kmc"],
    "prescribed_incubator":              ["incubator/ keep warm", "incubator"],
    "prescribed_transfusion":            ["transfusion"],
    "prescribed_phototherapy":           ["phototherapy"],
    "prescribed_cpap":                   ["cpap"],
    "prescribed_iv_fluids":              ["iv fluids"],
    "prescribed_antibiotics":            ["antibiotics"],
    "prescribed_feeds":                  ["nutrition/feeds", "feeds"],
    "prescribed_opv":                    ["opv"],
    "prescribed_surfactant":             ["surfactant"],
}

# Reverse lookup: lowercased label → canonical field name
LABEL_TO_FIELD: dict[str, str] = {
    label: canonical
    for canonical, labels in FIELD_ALIASES.items()
    for label in labels
}

# Section headings whose content is a bullet list of options (not a KV pair)
_BULLET_SECTION_MAP: dict[str, str] = {
    "skin": "skin",
    "jaundice": "jaundice",
    "appearance": "appearance",
    "cry": "cry",
}

# ---------------------------------------------------------------------------
# Label and cell helpers

def _clean_label(raw: str) -> str:
    """Strip Markdown syntax and normalise whitespace from a label string."""
    s = re.sub(r"[*_`#\[\]]", "", raw)
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"[:\.,]+$", "", s).strip()
    return s


def _get_canonical(label: str) -> str | None:
    """Return the canonical field name for *label*, or ``None`` if unknown."""
    return LABEL_TO_FIELD.get(_clean_label(label))


def _checked_label_from_cell(cell: str) -> str:
    """Find the label associated with ``[x]`` in a Markdown table cell.

    Handles both VLM output orderings:

    - Qwen:  ``A [ ]  B [ ]  AB [ ]  O [x]  Unkn [ ]``  → label *before* ``[x]`` → ``"O"``
    - Gemma: ``[ ] A  [ ] B  [ ] AB  [x] O  [ ] Unkn``  → label *after*  ``[x]`` → ``"O"``

    Returns
    -------
    str
        The selected label (normalised to ``Y`` / ``N`` / ``Unkn`` where
        applicable), or ``""`` if nothing was ticked.
    """
    cell = cell.strip()
    if re.match(r"^[YN]$", cell, re.IGNORECASE):
        return cell.upper()

    tokens: list[tuple[str, str, int]] = []
    for m in re.finditer(
        r"\[([xX ])\]|([A-Za-z][A-Za-z0-9+/\-]*(?:\s+[A-Za-z0-9+/\-]+)*)", cell
    ):
        if m.group(1) is not None:
            tokens.append(("bracket", m.group(1), m.start()))
        elif m.group(2):
            tokens.append(("label", m.group(2).strip(), m.start()))

    checked_idx = next(
        (i for i, (kind, val, _) in enumerate(tokens)
         if kind == "bracket" and val.lower() == "x"),
        None,
    )
    if checked_idx is None:
        return ""

    candidate = ""
    if checked_idx > 0 and tokens[checked_idx - 1][0] == "label":
        candidate = tokens[checked_idx - 1][1]
    elif checked_idx + 1 < len(tokens) and tokens[checked_idx + 1][0] == "label":
        candidate = tokens[checked_idx + 1][1]

    if not candidate:
        return ""

    lab = candidate.strip().upper()
    if lab in ("Y", "YES") or lab in ("POS", "POSITIVE"):
        return "Y"
    if lab in ("N", "NO") or lab in ("NEG", "NEGATIVE"):
        return "N"
    if "UNKN" in lab:
        return "Unkn"
    return candidate.strip()


def _yn_from_cell(cell: str) -> str:
    return _checked_label_from_cell(cell)


def _severity_from_cell(cell: str) -> str:
    result = _checked_label_from_cell(cell)
    return result if result and result.upper() not in ("Y", "N") else ""


def _is_placeholder(val: str) -> bool:
    v = val.strip()
    if not v:
        return True
    if re.fullmatch(r"[\[\]\s\:HhMmDdYy/\-\.\?]+", v):
        return True
    return v.lower() in ("[blank]", "blank", "[ ]", "n/a", "-", "—")


# ---------------------------------------------------------------------------
# Composite-field parsers

def _parse_apgar(cell: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for minute, score in re.findall(r"(\d+)M\s*[\[\(](\d+)[\]\)]", cell, re.IGNORECASE):
        out[f"apgar_{minute}m"] = score
    for minute, score in re.findall(r"(\d+)M\s+(\d+)", cell, re.IGNORECASE):
        out.setdefault(f"apgar_{minute}m", score)
    return out


def _parse_parity(cell: str) -> dict[str, str]:
    m = re.match(r"(\d+)\s*[\+/]\s*(\d+)", cell.strip())
    return {"parity_live": m.group(1), "parity_abortions": m.group(2)} if m else {}


def _parse_bp(cell: str) -> dict[str, str]:
    m = re.search(r"(\d+)\s*/\s*(\d+)", cell)
    return (
        {"systolic_blood_pressure": m.group(1), "diastolic_blood_pressure": m.group(2)}
        if m else {}
    )


# ---------------------------------------------------------------------------
# Markdown parsers

def _parse_table_rows(lines: list[str], fields: dict) -> None:
    """Extract field values from Markdown table rows into *fields*."""
    for line in lines:
        if "|" not in line:
            continue
        if re.match(r"^\s*\|[\s:\-|]+\|\s*$", line):
            continue  # separator row

        cells = [
            re.sub(r"\*+", "", c).strip()
            for c in line.strip().strip("|").split("|")
        ]
        if len(cells) < 2:
            continue

        # Symptom table: Symptom | Y | N | Symptom | Y | N
        def _is_yn_cell(c: str) -> bool:
            return bool(re.search(r"\[[ xX]\]|^[YN]$", c)) or c.strip() == ""

        if len(cells) >= 3 and _is_yn_cell(cells[1]) and _is_yn_cell(cells[2]):
            for i in range(0, len(cells) - 2, 3):
                canonical = _get_canonical(cells[i])
                if not canonical:
                    continue
                y_hit = bool(re.search(r"\[x\]|^Y$", cells[i + 1], re.IGNORECASE))
                n_hit = bool(re.search(r"\[x\]|^N$", cells[i + 2], re.IGNORECASE))
                if y_hit:
                    fields[canonical] = "Y"
                elif n_hit:
                    fields[canonical] = "N"
            continue

        # Diagnosis table: Label | [x]/[ ] | [x]/[ ]
        def _looks_diag(c: str) -> bool:
            return bool(re.match(r"^\[[ x12]\]$", c.strip()))

        if len(cells) >= 3 and _looks_diag(cells[1]):
            for i in range(0, len(cells) - 2, 3):
                diag_label = _clean_label(cells[i])
                if not diag_label:
                    continue
                p_cell = cells[i + 1] if i + 1 < len(cells) else ""
                s_cell = cells[i + 2] if i + 2 < len(cells) else ""
                if re.search(r"\[1\]|\[x\]", p_cell, re.IGNORECASE):
                    fields["primary_admission_diagnosis"] = diag_label.title()
                elif re.search(r"\[2\]|\[x\]", s_cell, re.IGNORECASE):
                    existing = fields.get("secondary_admission_diagnosis", "")
                    fields["secondary_admission_diagnosis"] = (
                        (existing + ", " + diag_label.title()).lstrip(", ")
                    )
            continue

        # Intervention table: label | Y-cell | N-cell
        canonical0 = _get_canonical(cells[0])
        if canonical0 and len(cells) >= 3:
            yn_val = _yn_from_cell(cells[1] + " " + cells[2])
            if yn_val:
                fields[canonical0] = yn_val
            for i in range(3, len(cells) - 1, 3):
                can_n = _get_canonical(cells[i])
                if can_n and i + 2 < len(cells):
                    v = _yn_from_cell(cells[i + 1] + " " + cells[i + 2])
                    if v:
                        fields[can_n] = v
            continue

        # Standard Field | Value pairs
        for i in range(0, len(cells) - 1, 2):
            canonical = _get_canonical(cells[i])
            val = cells[i + 1].strip() if i + 1 < len(cells) else ""
            if not canonical or _is_placeholder(val):
                continue
            if canonical == "_apgar_combined":
                fields.update(_parse_apgar(val))
            elif canonical == "_parity_combined":
                fields.update(_parse_parity(val))
            elif canonical == "_bp_combined":
                fields.update(_parse_bp(val))
            elif "[" in val:
                sev = _severity_from_cell(val)
                if sev:
                    fields[canonical] = sev
                else:
                    yn = _yn_from_cell(val)
                    if yn:
                        fields[canonical] = yn
            else:
                fields[canonical] = val.strip()


def _parse_bullet_and_plain(lines: list[str], fields: dict) -> None:
    """Extract field values from bullet lists and plain key-value lines."""
    current_section: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Section heading
        h = re.match(r"^#{1,4}\s+(.+)$", stripped)
        if h:
            heading = _clean_label(h.group(1))
            heading = re.sub(r"\s*[\|/].*$", "", heading).strip()
            heading = re.sub(r"\s*\(.*\)", "", heading).strip()
            current_section = _BULLET_SECTION_MAP.get(heading)
            continue

        # Bullet section item: [x] Normal
        if current_section:
            bm = re.match(r"^[-*]?\s*\[([xX ])\]\s+(.+)$", stripped)
            if bm and bm.group(1).lower() == "x":
                fields[current_section] = bm.group(2).strip()
                current_section = None
                continue

        # Bold / plain key-value: **Label**: value  or  Label: value
        kv = re.match(r"^\*{0,2}(.+?)\*{0,2}\s*:\s*(.+)$", stripped)
        if kv:
            canonical = _get_canonical(kv.group(1).strip())
            val_raw = kv.group(2).strip()
            if canonical:
                if canonical == "_apgar_combined":
                    fields.update(_parse_apgar(val_raw))
                elif canonical == "_parity_combined":
                    fields.update(_parse_parity(val_raw))
                elif canonical == "_bp_combined":
                    fields.update(_parse_bp(val_raw))
                elif "[" in val_raw:
                    sev = _severity_from_cell(val_raw)
                    if sev:
                        fields[canonical] = sev
                    else:
                        yn = _yn_from_cell(val_raw)
                        if yn:
                            fields[canonical] = yn
                elif not _is_placeholder(val_raw):
                    fields[canonical] = val_raw.strip()
            continue

        # Bullet KV: * Blood group: [ ] A [ ] B [x] O
        bkv = re.match(r"^[*\-]\s+(.+?)\s*:\s*(.+)$", stripped)
        if bkv:
            canonical = _get_canonical(bkv.group(1).strip())
            val_raw = bkv.group(2).strip()
            if canonical and "[" in val_raw:
                sev = _severity_from_cell(val_raw)
                fields[canonical] = sev if sev else _yn_from_cell(val_raw)
            continue

        # Plain Y/N bullet (Gemma page 2): [ ] Y [x] N Fever
        plain_yn = re.match(
            r"^[*\-]?\s*\[([xX ])\]\s*Y\s+\[([xX ])\]\s*N\s+(.+)$", stripped
        )
        if plain_yn:
            y_mark, n_mark, label = plain_yn.groups()
            canonical = _get_canonical(label.strip())
            if canonical:
                if y_mark.lower() == "x":
                    fields[canonical] = "Y"
                elif n_mark.lower() == "x":
                    fields[canonical] = "N"
            continue

        # Diagnosis line: Birth Asphyxia: [ ] 1 [ ] 2
        diag = re.match(r"^(.+?)\s*:\s*\[([xX ])\]\s*1\s+\[([xX ])\]\s*2$", stripped)
        if diag:
            diag_label, p_mark, s_mark = diag.groups()
            if p_mark.lower() == "x":
                fields["primary_admission_diagnosis"] = diag_label.strip().title()
            elif s_mark.lower() == "x":
                existing = fields.get("secondary_admission_diagnosis", "")
                fields["secondary_admission_diagnosis"] = (
                    (existing + ", " + diag_label.strip().title()).lstrip(", ")
                )
            continue

        # Others diagnosis: Others diagnoses...: [x] 1 [ ] 2 | TTN
        others = re.match(
            r"^others diagnoses.*:\s*\[([xX ])\]\s*1\s+\[([xX ])\]\s*2\s*\|\s*(.+)$",
            stripped,
            re.IGNORECASE,
        )
        if others:
            p_mark, s_mark, label = others.groups()
            if p_mark.lower() == "x":
                fields["primary_admission_diagnosis"] = label.strip().title()
            elif s_mark.lower() == "x":
                existing = fields.get("secondary_admission_diagnosis", "")
                fields["secondary_admission_diagnosis"] = (
                    (existing + ", " + label.strip().title()).lstrip(", ")
                )


def _parse_markdown(text: str) -> dict:
    """Parse raw markdown into a flat field-value dict."""
    fields: dict = {}
    lines = text.splitlines()
    _parse_table_rows(lines, fields)
    _parse_bullet_and_plain(lines, fields)
    return fields


# ---------------------------------------------------------------------------
# Value normalisation

def _normalize_date(val: str) -> str:
    val = re.sub(r"[^\d/\-]", "", val).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(val, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return val


def _normalize_int(val: str) -> str:
    m = re.search(r"\d+", val)
    return m.group() if m else ""


def _normalize_float(val: str) -> str:
    m = re.search(r"[\d.]+", val)
    return m.group() if m else ""


def _normalize_bool(val: str) -> str:
    v = val.strip().upper()
    if v in ("Y", "YES", "TRUE", "1", "POS", "POSITIVE"):
        return "Y"
    if v in ("N", "NO", "FALSE", "0", "NEG", "NEGATIVE"):
        return "N"
    if "UNKN" in v:
        return "Unkn"
    return val


def _normalize_time(val: str) -> str:
    val = re.sub(r"[^\d:]", "", val)
    m = re.match(r"(\d{1,2}):?(\d{2})", val)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else ""


def _normalize_value(val: str, field_type: str) -> str:
    """Normalise *val* according to its *field_type*."""
    if not val:
        return ""
    val = val.strip()
    if field_type == "date":   return _normalize_date(val)
    if field_type == "int":    return _normalize_int(val)
    if field_type == "float":  return _normalize_float(val)
    if field_type == "bool":   return _normalize_bool(val)
    if field_type == "time":   return _normalize_time(val)
    return val.upper() if len(val) <= 5 else val.title()


def _check_match(q: str, g: str) -> str:
    if not q and not g:
        return "both_empty"
    if not q or not g:
        return "one_empty"
    return "match" if q.lower() == g.lower() else "mismatch"


# ---------------------------------------------------------------------------
# Record-level helpers
# ---------------------------------------------------------------------------


def _get_base_id(record: dict) -> str:
    raw = str(record.get("id", "")).split(":")[-1]
    raw = re.sub(r"_page_\d+.*$", "", raw)
    raw = re.sub(r"_base$", "", raw)
    return raw


def _combine_pages(records_list: list[dict]) -> str:
    return "\n\n".join(
        r["extracted_text"]
        for r in sorted(records_list, key=lambda x: str(x.get("id", "")))
        if r.get("extracted_text")
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_comparison(
    qwen_table:   str = _DEFAULT_QWEN_TABLE,
    gemma_table:  str = _DEFAULT_GEMMA_TABLE,
    output_table: str = _DEFAULT_OUTPUT_TABLE,
    output_csv:   str = _DEFAULT_OUTPUT_CSV,
) -> None:
    """Compare raw extraction outputs from Qwen and Gemma field-by-field.

    Parameters
    ----------
    qwen_table: SurrealDB table containing Qwen extraction records.
    gemma_table: SurrealDB table containing Gemma extraction records.
    output_table: SurrealDB table to write per-record comparison summaries to.
    output_csv: Path for the flat CSV output.
    """
    logger.info("Fetching records from '%s' and '%s'...", qwen_table, gemma_table)
    qwen_records  = fetch_records(qwen_table)
    gemma_records = fetch_records(gemma_table)

    def _index(records: list[dict]) -> dict[str, list[dict]]:
        idx: dict[str, list[dict]] = {}
        for r in records:
            idx.setdefault(_get_base_id(r), []).append(r)
        return idx

    qwen_idx  = _index(qwen_records)
    gemma_idx = _index(gemma_records)
    all_ids   = sorted(set(qwen_idx) | set(gemma_idx))

    logger.info("Unique records found: %d", len(all_ids))

    csv_header = [
        "record_id", "field", "field_type",
        "qwen_raw", "gemma_raw",
        "qwen_normalized", "gemma_normalized",
        "match_status",
    ]
    csv_rows: list[list] = [csv_header]

    for base_id in all_ids:
        qwen_text  = _combine_pages(qwen_idx.get(base_id, []))
        gemma_text = _combine_pages(gemma_idx.get(base_id, []))

        qwen_fields  = _parse_markdown(qwen_text)
        gemma_fields = _parse_markdown(gemma_text)

        record_comparison: dict[str, dict] = {}
        statuses: list[str] = []

        for field in sorted(FIELD_TYPES.keys()):
            ftype  = FIELD_TYPES[field]
            q_raw  = qwen_fields.get(field, "")
            g_raw  = gemma_fields.get(field, "")
            q_norm = _normalize_value(q_raw, ftype)
            g_norm = _normalize_value(g_raw, ftype)
            status = _check_match(q_norm, g_norm)
            statuses.append(status)

            record_comparison[field] = {
                "field_type":       ftype,
                "qwen_raw":         q_raw,
                "gemma_raw":        g_raw,
                "qwen_normalized":  q_norm,
                "gemma_normalized": g_norm,
                "match_status":     status,
            }
            csv_rows.append(
                [base_id, field, ftype, q_raw, g_raw, q_norm, g_norm, status]
            )

        n_total   = len(statuses)
        n_match   = statuses.count("match")
        agreement = round(n_match / n_total * 100, 1) if n_total else 0.0

        save_record(
            {
                "record_id": base_id,
                "run_id":    datetime.now().isoformat(),
                "fields":    record_comparison,
                "summary": {
                    "total_fields":  n_total,
                    "matching":      n_match,
                    "mismatching":   statuses.count("mismatch"),
                    "one_empty":     statuses.count("one_empty"),
                    "both_empty":    statuses.count("both_empty"),
                    "agreement_pct": agreement,
                },
            },
            output_table,
            base_id,
        )
        logger.info("  %s — agreement %.1f%%", base_id, agreement)

    Path(output_csv).write_text(
        "\n".join(",".join(str(c) for c in row) for row in csv_rows),
        encoding="utf-8",
    )
    logger.info("CSV saved: %s | DB table: %s | Records: %d",
                output_csv, output_table, len(all_ids))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run_comparison()