"""
schemas/neonatal_admission_form/field_types.py
===============================================
Maps every field in ``NARFullRecord`` to its data-type category, and
provides hospital code lookup utilities.

This mapping is used by the evaluation pipeline to:
- Break down accuracy metrics by field type (e.g. bool vs int vs str)
- Drive type-compliance checks in ``schema_compliance.py``
- Gate hallucination detection strategies in ``hallucination_detector.py``

Type categories
---------------
bool        Y/N checkboxes (``None`` = unknown / not ticked)
int         Whole numbers
float       Decimal numbers
str         Coded strings and short categorical values
text        Free-text fields (``Literal["text"]`` in schema)
date        Calendar dates
time        Clock times
redacted    Black-barred fields on real forms (``Literal["redacted"]``)
coded_int   Integer codes mapping to named values (e.g. hospital codes)
categorical Closed-vocabulary string fields enforced by Python Enum classes from nar_enums.py
"""

from __future__ import annotations

FIELD_TYPES: dict[str, str] = {

    # ------------------------------------------------------------------
    # SECTION A: Infant details
    "infant_name":              "redacted",
    "ip_no":                    "redacted",
    "admission_date":           "date",
    "time_seen":                "time",
    "sex":                            "categorical",
    "birth_date":               "date",
    "time_birth":               "time",
    "gestation_in_weeks":       "int",
    "baby_age_in_days":         "int",
    "gestation_type":                 "categorical",
    "apgar_1m":                 "int",
    "apgar_5m":                 "int",
    "apgar_10m":                "int",
    "delivery_type":                  "categorical",
    "had_cs":                         "categorical",
    "was_resuscitated":         "bool",
    "rapture_of_membrane":            "categorical",
    "is_multiple_delivery":     "bool",
    "multiple_delivery_num":    "int",
    "born_before_arrival":      "bool",
    "born_where":                     "categorical",

    # ------------------------------------------------------------------
    # SECTION B: Mother's details
    "mum_name":                             "redacted",
    "mum_ip_no":                            "redacted",
    "mum_age_in_years":                     "int",
    "parity_live":                          "int",
    "parity_abortions":                     "int",
    "parity_total":                         "int",
    "date_estimated_delivery_date":         "date",
    "anc_clinic_name":                      "redacted",
    "anc_visits":                           "int",
    "mum_has_anc_ultrasound":               "bool",
    "anc_us_trimester":                           "categorical",
    "us_findings":                          "text",
    "blood_group":                                "categorical",
    "rhesus":                                     "categorical",
    "given_anti_D_medication":                    "categorical",
    "mum_had_vdrl":                         "bool",
    "mum_pmtct_status":                     "bool",
    "mum_on_arvs":                          "bool",
    "mum_had_hepatitis_b":                  "bool",
    "mum_given_HBIG_treatment":             "bool",
    "mum_had_hypertension_in_pregnancy":    "bool",
    "mum_had_antepartum_haemorrhage":       "bool",
    "mum_had_diabetes":                     "bool",
    "prolonged_labour":                     "bool",

    # ------------------------------------------------------------------
    # SECTION C & D: Free text
    "maternal_illness_notes":       "text",
    "infant_presenting_problems":   "text",

    # ------------------------------------------------------------------
    # SECTION E: Anthropometry & Vital signs
    "head_circumference":           "int",
    "length":                       "int",
    "temparature":                  "float",
    "respiratory_rate":             "int",
    "systolic_blood_pressure":      "int",
    "diastolic_blood_pressure":     "int",
    "pulse_rate":                   "int",
    "pulse_oximetry":               "int",
    "birth_weight":                 "int",
    "weight":                       "int",
    "has_fever":                    "bool",
    "passed_meconium":              "bool",
    "has_difficulty_breathing":     "bool",
    "passed_urine":                 "bool",
    "has_difficulty_feeding":       "bool",
    "has_convulsions":              "bool",
    "has_apnoea":                   "bool",
    "is_floppy":                    "bool",
    "has_vomiting":                 "bool",
    "has_diarhoea":                 "bool",

    # ------------------------------------------------------------------
    # SECTION F1: General examination
    "skin":                               "categorical",
    "jaundice":                           "categorical",
    "appearance":                         "categorical",
    "cry":                                "categorical",
    "has_crackles":                 "bool",
    "has_grunting":                 "bool",
    "has_good_air_entry":           "bool",
    "has_central_cyanosis":         "bool",
    "chest_indrawing":                    "categorical",
    "xiphoid_retraction":                 "categorical",
    "intercostal_retraction":             "categorical",
    "capillary_refill_in_seconds":  "float",
    "pallor":                             "categorical",
    "has_murmur":                   "bool",
    "has_bulging_fontanelle":       "bool",
    "is_irritable":                 "bool",
    "tone":                               "categorical",
    "is_distended":                 "bool",
    "umbilicus":                          "categorical",

    # ------------------------------------------------------------------
    # SECTION F2: Further examination
    "neuro_examination":            "text",
    "further_examination":          "text",
    "has_birth_defects":            "bool",
    "birth_defect_types":                 "categorical",

    # ------------------------------------------------------------------
    # SECTION G: Problem list
    "problem_list":                 "text",

    # ------------------------------------------------------------------
    # SECTION H: Investigations
    "rbs_measured":                 "bool",
    "rbs_value":                    "float",
    "given_bilirubin":              "bool",
    "total_serum_bilirubin":        "float",
    "investigations_other":         "text",

    # ------------------------------------------------------------------
    # SECTION I: Diagnoses
    "primary_admission_diagnosis":   "text",
    "secondary_admission_diagnosis": "text",
    "other_diagnoses":               "text",

    # ------------------------------------------------------------------
    # SECTION J: Interventions
    "given_vitamin_k":              "bool",
    "given_bcg":                    "bool",
    "given_chlorhexidine":          "bool",
    "given_prophylaxis_pmtct":      "bool",
    "prescribed_transfusion":       "bool",
    "prescribed_phototherapy":      "bool",
    "prescribed_cpap":              "bool",
    "prescribed_iv_fluids":         "bool",
    "prescribed_antibiotics":       "bool",
    "prescribed_feeds":             "bool",
    "prescribed_opv":               "bool",
    "prescribed_surfactant":        "bool",
    "prescribed_caffeine_citrate":  "bool",
    "prescribed_oxygen":            "bool",
    "prescribed_kmc":               "bool",
    "prescribed_incubator":         "bool",

    # ------------------------------------------------------------------
    # SECTION K: Action plan
    "clinician_name":       "redacted",
    "clinician_signature":  "redacted",
    "action_plan_time":     "time",
    "action_plan_date":     "date",

    # ------------------------------------------------------------------
    # Internal / derived
    "hospital":     "coded_int",
    "record_type":  "str",
}

# ------------------------------------------------------------------
# Filename → hospital code lookup
# ------------------------------------------------------------------
# Extendable dict
# Key   = integer code stored in the ``hospital`` field
# Value = NAR filename prefix for records from that facility

HOSPITAL_CODES: dict[int, str] = {
    2:  "NAR_52000",
    3:  "NAR_53000",
    4:  "NAR_7200",
    5:  "NAR_41000",
    6:  "NAR_40000",
    7:  "NAR_63000",
    8:  "NAR_76000",
    17: "NAR_1700000",
}


def encode_hospital(filename: str) -> int | None:
    """Return the integer hospital code for a given NAR filename.

    Parameters
    ----------
    filename: A NAR record filename or ID string (e.g. ``"NAR_40000001_page1"``).

    Returns
    -------
    int | None
        The matching hospital code, or ``None`` if the prefix is not
        recognised.
    """
    for code, prefix in HOSPITAL_CODES.items():
        if filename.startswith(prefix):
            return code
    return None


def decode_hospital(code: int) -> str | None:
    """Return the filename prefix for a given integer hospital code.

    This is the inverse of ``encode_hospital``.  Used by
    ``run_evaluation.py`` when displaying structured comparison output.

    Parameters
    ----------
    code: Integer hospital code (e.g. ``6``).

    Returns
    -------
    str | None
        The filename prefix (e.g. ``"NAR_40000"``), or ``None`` if the
        code is not in ``HOSPITAL_CODES``.
    """
    return HOSPITAL_CODES.get(code)