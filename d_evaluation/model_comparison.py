import os
import re
import csv
from datetime import datetime
from dotenv import load_dotenv

from database_utils.db_utils import fetch_records, save_record
from schemas.neonatal_admission_form.field_types import FIELD_TYPES

load_dotenv()

# ------------------------
# CONFIG

QWEN_TABLE   = "extractions"
GEMMA_TABLE  = "extractions_gemma"
OUTPUT_TABLE = "comparison"
OUTPUT_CSV   = "extraction_comparison.csv"

# canonical field → all label variants (lowercased, stripped of punctuation/markdown)
FIELD_ALIASES = {
    "admission_date":                   ["date of admission"],
    "time_seen":                        ["time baby seen (24 hr clock)", "time baby seen"],
    "sex":                              ["sex"],
    "date_of_birth":                    ["dob", "date of birth"],
    "time_birth":                       ["time of birth (24 hr clock)", "time of birth"],
    "gestation_in_weeks":               ["gestation (in weeks)", "gestation"],
    "baby_age_in_days":                 ["age (in days)", "age in days"],
    "gestation_type":                   ["gestation age from?", "gestation age from"],
    "_apgar_combined":                  ["apgar"],
    "delivery_type":                    ["delivery"],
    "had_cs":                           ["if cs, type"],
    "was_resuscitated":                 ["bvm resus at birth?", "bvm resus at birth"],
    "rapture_of_membrane":              ["rom"],
    "is_multiple_delivery":             ["multiple delivery"],
    "multiple_delivery_num":            ["if yes, number"],
    "born_before_arrival":              ["born outside facility?", "born outside facility"],
    "born_where":                       ["if yes, where?"],
    "mum_age_in_years":                 ["age (years)"],
    "_parity_combined":                 ["parity"],
    "date_estimated_delivery_date":     ["edd"],
    "anc_visits":                       ["anc no. of visits", "anc no of visits"],
    "mum_has_anc_ultrasound":           ["anc u/s", "anc"],
    "blood_group":                      ["blood group"],
    "rhesus":                           ["rhesus"],
    "given_anti_D_medication":          ["anti d"],
    "mum_had_vdrl":                     ["vdrl"],
    "mum_pmtct_status":                 ["pmtct status"],
    "mum_on_arvs":                      ["mother on arvs"],
    "mum_had_hepatitis_b":              ["hep b"],
    "mum_given_HBIG_treatment":         ["hep b ig given"],
    "mum_had_hypertension_in_pregnancy":["htn in pregnancy?", "htn in pregnancy"],
    "mum_had_antepartum_haemorrhage":   ["aph"],
    "mum_had_diabetes":                 ["diabetes"],
    "prolonged_labour":                 ["prolonged 2nd stage?", "prolonged 2nd stage"],
    "head_circumference":               ["head circumference (cm)", "head circumference"],
    "length":                           ["length (cm)", "length"],
    "temparature":                      ["temp"],
    "respiratory_rate":                 ["resp rate"],
    "_bp_combined":                     ["blood pressure"],
    "pulse_rate":                       ["pulse"],
    "pulse_oximetry":                   ["o2 sat (%)", "o2 sat"],
    "birth_weight":                     ["birth weight (grams)", "birth weight"],
    "weight":                           ["weight now (grams)", "weight now"],
    "has_fever":                        ["fever"],
    "passed_meconium":                  ["passed meconium/stool", "passed meconium"],
    "has_difficulty_breathing":         ["difficulty breathing"],
    "passed_urine":                     ["passed urine in the last 12 hours", "passed urine"],
    "has_difficulty_feeding":           ["inability to feed"],
    "has_convulsions":                  ["convulsions / twitching", "convulsions"],
    "has_apnoea":                       ["apnoea"],
    "has_vomiting":                     ["bilious vomiting"],
    # Page 2
    "skin":                             ["skin"],
    "jaundice":                         ["jaundice"],
    "appearance":                       ["appearance"],
    "cry":                              ["cry"],
    "has_crackles":                     ["crackles", "cracles"],
    "has_grunting":                     ["grunting"],
    "has_good_air_entry":               ["good bilateral air entry"],
    "has_central_cyanosis":             ["central cyanosis"],
    "chest_indrawing":                  ["lower chest indrawing"],
    "xiphoid_retraction":               ["xiphoid retraction"],
    "intercostal_retraction":           ["intercostal retraction"],
    "capillary_refill_in_seconds":      ["capillary refill (sternal)", "capillary refill"],
    "pallor":                           ["pallor/anaemia", "pallor"],
    "has_murmur":                       ["murmur"],
    "has_bulging_fontanelle":           ["bulging fontanelle"],
    "is_irritable":                     ["irritable"],
    "tone":                             ["tone"],
    "is_distended":                     ["distension"],
    "umbilicus":                        ["umbilicus"],
    "has_birth_defects":                ["birth defects?", "birth defects"],
    "given_bilirubin":                  ["bilirubin"],
    "rbs_measured":                     ["rbs"],
    "given_vitamin_k":                  ["vit k & teo", "vit k & theo", "vit k"],
    "prescribed_caffeine_citrate":      ["caffeine citrate"],
    "prescribed_oxygen":                ["oxygen"],
    "given_prophylaxis_pmtct":          ["prophylaxis for pmtct"],
    "given_bcg":                        ["bcg"],
    "given_chlorhexidine":              ["chlorhexidine"],
    "prescribed_kmc":                   ["kmc"],
    "prescribed_incubator":             ["incubator/ keep warm", "incubator"],
    "prescribed_transfusion":           ["transfusion"],
    "prescribed_phototherapy":          ["phototherapy"],
    "prescribed_cpap":                  ["cpap"],
    "prescribed_iv_fluids":             ["iv fluids"],
    "prescribed_antibiotics":           ["antibiotics"],
    "prescribed_feeds":                 ["nutrition/feeds", "feeds"],
    "prescribed_opv":                   ["opv"],
    "prescribed_surfactant":            ["surfactant"],
}

# Reverse lookup: label → canonical
LABEL_TO_FIELD = {}
for canonical, labels in FIELD_ALIASES.items():
    for label in labels:
        LABEL_TO_FIELD[label] = canonical

# Bullet-list section headings → field
BULLET_SECTION_MAP = {
    "skin": "skin", "jaundice": "jaundice",
    "appearance": "appearance", "cry": "cry",
}


# ------------------------
# HELPERS

def clean_label(raw: str) -> str:
    s = re.sub(r"[*_`#\[\]]", "", raw)
    s = re.sub(r"\s+", " ", s).strip().lower()
    # strip trailing punctuation except ? which matters for some aliases
    s = re.sub(r"[:\.,]+$", "", s).strip()
    return s


def get_canonical(label: str) -> str | None:
    return LABEL_TO_FIELD.get(clean_label(label))


def checked_label_from_cell(cell: str) -> str:
    """
    Find the label associated with [x] in a cell containing multiple options.

    Handles both orderings:
      qwen:  A [ ] B [ ] AB [ ] O [x] Unkn [ ]  → label BEFORE [x] → 'O'
      gemma: [ ] A [ ] B [ ] AB [x] O [ ] Unkn  → label AFTER  [x] → 'O'

    Strategy: tokenise the cell into (label | bracket) tokens, find the [x]
    bracket, then pick the nearest adjacent label token. The label token that
    is IMMEDIATELY adjacent to [x] (before or after) is the selected value.
    Ties go to the token before the bracket (qwen style).
    """
    cell = cell.strip()

    # bare Y/N shortcut
    if re.match(r"^[YN]$", cell, re.IGNORECASE):
        return cell.upper()

    # Tokenise: split into (position, kind, text) where kind = 'bracket' or 'label'
    tokens = []
    for m in re.finditer(r"\[([xX ])\]|([A-Za-z][A-Za-z0-9+/\-]*(?:\s+[A-Za-z0-9+/\-]+)*)", cell):
        if m.group(1) is not None:
            tokens.append(("bracket", m.group(1), m.start()))
        elif m.group(2):
            tokens.append(("label", m.group(2).strip(), m.start()))

    # Find index of the [x] bracket
    checked_idx = None
    for i, (kind, val, _) in enumerate(tokens):
        if kind == "bracket" and val.lower() == "x":
            checked_idx = i
            break

    if checked_idx is None:
        return ""  # nothing checked

    # Prefer the label token immediately BEFORE the bracket (qwen: O [x])
    # Fall back to immediately AFTER the bracket (gemma: [x] O)
    candidate = ""
    if checked_idx > 0 and tokens[checked_idx - 1][0] == "label":
        candidate = tokens[checked_idx - 1][1]
    elif checked_idx + 1 < len(tokens) and tokens[checked_idx + 1][0] == "label":
        candidate = tokens[checked_idx + 1][1]

    if not candidate:
        return ""

    # Normalise semantic values
    lab = candidate.strip().upper()
    if lab in ("Y", "YES"):          return "Y"
    if lab in ("N", "NO"):           return "N"
    if "UNKN" in lab:                return "Unkn"
    if lab in ("POS", "POSITIVE"):   return "Y"
    if lab in ("NEG", "NEGATIVE"):   return "N"
    return candidate.strip()


def yn_from_cell(cell: str) -> str:
    """Wrapper: returns Y/N/Unkn/'' for boolean fields."""
    return checked_label_from_cell(cell)


def severity_from_cell(cell: str) -> str:
    """
    Return categorical label (not Y/N) adjacent to [x].
    Used for fields like chest_indrawing (None/Mild/Severe), tone, skin, etc.
    """
    result = checked_label_from_cell(cell)
    if result and result.upper() not in ("Y", "N"):
        return result
    return ""


def parse_apgar(cell: str) -> dict:
    out = {}
    for minute, score in re.findall(r"(\d+)M\s*[\[\(](\d+)[\]\)]", cell, re.IGNORECASE):
        out[f"apgar_{minute}m"] = score
    # gemma plain format: 1M 5 5M 9 10M 10
    for minute, score in re.findall(r"(\d+)M\s+(\d+)", cell, re.IGNORECASE):
        key = f"apgar_{minute}m"
        if key not in out:
            out[key] = score
    return out


def parse_parity(cell: str) -> dict:
    m = re.match(r"(\d+)\s*[\+/]\s*(\d+)", cell.strip())
    if m:
        return {"parity_live": m.group(1), "parity_abortions": m.group(2)}
    return {}


def parse_bp(cell: str) -> dict:
    m = re.search(r"(\d+)\s*/\s*(\d+)", cell)
    if m:
        return {"systolic_blood_pressure": m.group(1),
                "diastolic_blood_pressure": m.group(2)}
    return {}


def is_placeholder(val: str) -> bool:
    """True if value is a blank placeholder like HH:MM, [ ], [blank], etc."""
    v = val.strip()
    if not v:
        return True
    if re.fullmatch(r"[\[\]\s\:HhMmDdYy/\-\.\?]+", v):
        return True
    if v.lower() in ("[blank]", "blank", "[ ]", "n/a", "-", "—"):
        return True
    return False


# ------------------------
# TABLE ROW PARSER

def parse_table_rows(lines: list, fields: dict):
    for line in lines:
        if "|" not in line:
            continue
        if re.match(r"^\s*\|[\s:\-|]+\|\s*$", line):
            continue  # separator

        cells = [re.sub(r"\*+", "", c).strip()
                 for c in line.strip().strip("|").split("|")]

        if len(cells) < 2:
            continue

        # ── Symptom table (6-col): Symptom | Y | N | Symptom | Y | N
        if len(cells) >= 3:
            def is_yn_cell(c):
                return bool(re.search(r"\[[ xX]\]|^[YN]$", c)) or c.strip() == ""

            if is_yn_cell(cells[1]) and (len(cells) < 3 or is_yn_cell(cells[2])):
                for i in range(0, len(cells) - 2, 3):
                    label = cells[i]
                    y_cell = cells[i+1] if i+1 < len(cells) else ""
                    n_cell = cells[i+2] if i+2 < len(cells) else ""
                    canonical = get_canonical(label)
                    if not canonical:
                        continue
                    y_hit = bool(re.search(r"\[x\]|^Y$", y_cell, re.IGNORECASE))
                    n_hit = bool(re.search(r"\[x\]|^N$", n_cell, re.IGNORECASE))
                    if y_hit:   fields[canonical] = "Y"
                    elif n_hit: fields[canonical] = "N"
                continue

        # ── Diagnosis table: rows with cells[1] matching [ ]/[x]/[1]/[2]
        def looks_diag(c):
            return bool(re.match(r"^\[[ x12]\]$", c.strip()))

        if len(cells) >= 3 and looks_diag(cells[1]):
            for i in range(0, len(cells) - 2, 3):
                diag_label = clean_label(cells[i])
                p_cell = cells[i+1] if i+1 < len(cells) else ""
                s_cell = cells[i+2] if i+2 < len(cells) else ""
                if not diag_label:
                    continue
                if bool(re.search(r"\[1\]|\[x\]", p_cell, re.IGNORECASE)):
                    fields["primary_admission_diagnosis"] = diag_label.title()
                elif bool(re.search(r"\[2\]|\[x\]", s_cell, re.IGNORECASE)):
                    existing = fields.get("secondary_admission_diagnosis", "")
                    fields["secondary_admission_diagnosis"] = (
                        (existing + ", " + diag_label.title()).lstrip(", ")
                    )
            continue

        # ── Intervention table: label | Y-cell | N-cell  (repeated)
        canonical0 = get_canonical(cells[0])
        if canonical0 and len(cells) >= 3:
            yn_val = yn_from_cell(cells[1] + " " + cells[2])
            if yn_val:
                fields[canonical0] = yn_val
            # check remaining pairs in same row
            for i in range(3, len(cells) - 1, 3):
                canN = get_canonical(cells[i])
                if canN and i+2 < len(cells):
                    v = yn_from_cell(cells[i+1] + " " + cells[i+2])
                    if v:
                        fields[canN] = v
            continue

        # ── Standard Field | Value (repeated pairs)
        for i in range(0, len(cells) - 1, 2):
            label = cells[i]
            val   = cells[i+1].strip() if i+1 < len(cells) else ""
            canonical = get_canonical(label)
            if not canonical:
                continue
            if is_placeholder(val):
                continue

            if canonical == "_apgar_combined":
                fields.update(parse_apgar(val))
            elif canonical == "_parity_combined":
                fields.update(parse_parity(val))
            elif canonical == "_bp_combined":
                fields.update(parse_bp(val))
            elif "[" in val:
                # categorical: find checked label
                sev = severity_from_cell(val)
                if sev:
                    fields[canonical] = sev
                else:
                    yn = yn_from_cell(val)
                    # Only store if something was actually checked
                    if yn:
                        fields[canonical] = yn
            else:
                fields[canonical] = val.strip()


# ------------------------
# BULLET / PLAIN LINE PARSER

def parse_bullet_and_plain(lines: list, fields: dict):
    current_section = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Section heading
        h = re.match(r"^#{1,4}\s+(.+)$", stripped)
        if h:
            heading = clean_label(h.group(1))
            heading = re.sub(r"\s*[\|/].*$", "", heading).strip()  # strip "| F2" suffixes
            heading = re.sub(r"\s*\(.*\)", "", heading).strip()
            current_section = BULLET_SECTION_MAP.get(heading)
            continue

        # ── Bullet section items: [x] Normal  or  - [x] Normal
        if current_section:
            bm = re.match(r"^[-*]?\s*\[([xX ])\]\s+(.+)$", stripped)
            if bm and bm.group(1).lower() == "x":
                fields[current_section] = bm.group(2).strip()
                current_section = None  # take first checked only
                continue

        # ── Bold inline: **Crackles**: [x] Y, [ ] N
        # or plain:       Crackles: [x] Y  [ ] N
        kv = re.match(r"^\*{0,2}(.+?)\*{0,2}\s*:\s*(.+)$", stripped)
        if kv:
            label = kv.group(1).strip()
            val_raw = kv.group(2).strip()
            canonical = get_canonical(label)
            if canonical:
                if canonical == "_apgar_combined":
                    fields.update(parse_apgar(val_raw))
                elif canonical == "_parity_combined":
                    fields.update(parse_parity(val_raw))
                elif canonical == "_bp_combined":
                    fields.update(parse_bp(val_raw))
                elif "[" in val_raw:
                    sev = severity_from_cell(val_raw)
                    if sev:
                        fields[canonical] = sev
                    else:
                        yn = yn_from_cell(val_raw)
                        if yn:
                            fields[canonical] = yn
                elif not is_placeholder(val_raw):
                    fields[canonical] = val_raw.strip()
            continue

        # ── Bullet key-value: * Blood group: [ ] A [ ] B [x] O
        bkv = re.match(r"^[*\-]\s+(.+?)\s*:\s*(.+)$", stripped)
        if bkv:
            label = bkv.group(1).strip()
            val_raw = bkv.group(2).strip()
            canonical = get_canonical(label)
            if canonical and "[" in val_raw:
                sev = severity_from_cell(val_raw)
                if sev:
                    fields[canonical] = sev
                else:
                    yn = yn_from_cell(val_raw)
                    if yn:
                        fields[canonical] = yn
            continue

        # ── Plain Y/N bullet (gemma page 2 symptoms): [ ] Y [x] N Fever
        plain_yn = re.match(r"^[*\-]?\s*\[([xX ])\]\s*Y\s+\[([xX ])\]\s*N\s+(.+)$", stripped)
        if plain_yn:
            y_mark, n_mark, label = plain_yn.groups()
            canonical = get_canonical(label.strip())
            if canonical:
                if y_mark.lower() == "x":   fields[canonical] = "Y"
                elif n_mark.lower() == "x": fields[canonical] = "N"
            continue

        # ── Diagnosis plain line: Birth Asphyxia: [ ] 1 [ ] 2
        diag_line = re.match(r"^(.+?)\s*:\s*\[([xX ])\]\s*1\s+\[([xX ])\]\s*2$", stripped)
        if diag_line:
            diag_label, p_mark, s_mark = diag_line.groups()
            if p_mark.lower() == "x":
                fields["primary_admission_diagnosis"] = diag_label.strip().title()
            elif s_mark.lower() == "x":
                existing = fields.get("secondary_admission_diagnosis", "")
                fields["secondary_admission_diagnosis"] = (
                    (existing + ", " + diag_label.strip().title()).lstrip(", ")
                )
            continue

        # ── Others diagnosis plain: Others diagnoses (List below): [x] 1 [ ] 2 | TTN
        others = re.match(r"^others diagnoses.*:\s*\[([xX ])\]\s*1\s+\[([xX ])\]\s*2\s*\|\s*(.+)$",
                          stripped, re.IGNORECASE)
        if others:
            p_mark, s_mark, label = others.groups()
            if p_mark.lower() == "x":
                fields["primary_admission_diagnosis"] = label.strip().title()
            elif s_mark.lower() == "x":
                existing = fields.get("secondary_admission_diagnosis", "")
                fields["secondary_admission_diagnosis"] = (
                    (existing + ", " + label.strip().title()).lstrip(", ")
                )
            continue


# ------------------------
# MASTER PARSER

def parse_markdown(text: str) -> dict:
    fields = {}
    lines = text.split("\n")
    parse_table_rows(lines, fields)
    parse_bullet_and_plain(lines, fields)
    return fields


# ------------------------
# NORMALIZERS

def normalize_date(val: str) -> str:
    val = re.sub(r"[^\d/\-]", "", val).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(val, fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    return val

def normalize_int(val: str) -> str:
    m = re.search(r"\d+", val)
    return m.group() if m else ""

def normalize_float(val: str) -> str:
    m = re.search(r"[\d.]+", val)
    return m.group() if m else ""

def normalize_bool(val: str) -> str:
    v = val.strip().upper()
    if v in ("Y", "YES", "TRUE", "1", "POS", "POSITIVE"): return "Y"
    if v in ("N", "NO", "FALSE", "0", "NEG", "NEGATIVE"):  return "N"
    if "UNKN" in v: return "Unkn"
    return val

def normalize_time(val: str) -> str:
    val = re.sub(r"[^\d:]", "", val)
    m = re.match(r"(\d{1,2}):?(\d{2})", val)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return ""   # empty if no real time found

def normalize_value(val: str, field_type: str) -> str:
    if not val:
        return ""
    val = val.strip()
    if field_type == "date":  return normalize_date(val)
    if field_type == "int":   return normalize_int(val)
    if field_type == "float": return normalize_float(val)
    if field_type == "bool":  return normalize_bool(val)
    if field_type == "time":  return normalize_time(val)
    return val.upper() if len(val) <= 5 else val.title()


# ------------------------
# MATCH

def check_match(q: str, g: str) -> str:
    if not q and not g: return "both_empty"
    if not q or not g:  return "one_empty"
    return "match" if q.lower() == g.lower() else "mismatch"


# ------------------------
# RECORD HELPERS

def get_base_id(record: dict) -> str:
    raw = str(record.get("id", "")).split(":")[-1]
    raw = re.sub(r"_page_\d+.*$", "", raw)
    raw = re.sub(r"_base$", "", raw)
    return raw

def combine_pages(records_list: list) -> str:
    return "\n\n".join(
        r.get("extracted_text", "")
        for r in sorted(records_list, key=lambda x: str(x.get("id", "")))
        if r.get("extracted_text")
    )


# ------------------------
# MAIN

def run_comparison():
    print("Fetching records...")
    qwen_records  = fetch_records(QWEN_TABLE)
    gemma_records = fetch_records(GEMMA_TABLE)

    def index_records(records):
        idx = {}
        for r in records:
            base = get_base_id(r)
            idx.setdefault(base, []).append(r)
        return idx

    qwen_idx  = index_records(qwen_records)
    gemma_idx = index_records(gemma_records)

    all_ids = sorted(set(list(qwen_idx.keys()) + list(gemma_idx.keys())))
    print(f"Found {len(all_ids)} unique records\n")

    csv_rows = [[
        "record_id", "field", "field_type",
        "qwen_raw", "gemma_raw",
        "qwen_normalized", "gemma_normalized",
        "match_status",
    ]]

    for base_id in all_ids:
        print(f"--- {base_id} ---")

        qwen_text  = combine_pages(qwen_idx.get(base_id, []))
        gemma_text = combine_pages(gemma_idx.get(base_id, []))

        qwen_fields  = parse_markdown(qwen_text)
        gemma_fields = parse_markdown(gemma_text)

        record_comparison = {}

        for field in sorted(FIELD_TYPES.keys()):
            ftype  = FIELD_TYPES[field]
            q_raw  = qwen_fields.get(field, "")
            g_raw  = gemma_fields.get(field, "")
            q_norm = normalize_value(q_raw, ftype)
            g_norm = normalize_value(g_raw, ftype)
            status = check_match(q_norm, g_norm)

            if status != "both_empty":
                print(f"  {field:<35} qwen={q_norm!r:<12} gemma={g_norm!r:<12} → {status}")

            csv_rows.append([
                base_id, field, ftype,
                q_raw, g_raw,
                q_norm, g_norm,
                status,
            ])

            record_comparison[field] = {
                "field_type":       ftype,
                "qwen_raw":         q_raw,
                "gemma_raw":        g_raw,
                "qwen_normalized":  q_norm,
                "gemma_normalized": g_norm,
                "match_status":     status,
            }

        statuses    = [v["match_status"] for v in record_comparison.values()]
        n_total     = len(statuses)
        n_match     = statuses.count("match")
        n_mismatch  = statuses.count("mismatch")
        n_one_empty = statuses.count("one_empty")
        n_both      = statuses.count("both_empty")
        agreement   = round(n_match / n_total * 100, 1) if n_total else 0

        save_record({
            "record_id": base_id,
            "run_id":    datetime.now().isoformat(),
            "fields":    record_comparison,
            "summary": {
                "total_fields":  n_total,
                "matching":      n_match,
                "mismatching":   n_mismatch,
                "one_empty":     n_one_empty,
                "both_empty":    n_both,
                "agreement_pct": agreement,
            },
        }, OUTPUT_TABLE, base_id)

        print(f"  → agreement {agreement}% | saved to {OUTPUT_TABLE}:{base_id}\n")

    with open(OUTPUT_CSV, "w", newline="") as f:
        csv.writer(f).writerows(csv_rows)

    print(f"CSV:  {OUTPUT_CSV}")
    print(f"DB:   {OUTPUT_TABLE}")
    print(f"Records compared: {len(all_ids)}")


if __name__ == "__main__":
    run_comparison()