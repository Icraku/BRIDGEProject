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
int         Whole numbers
float       Decimal numbers
str         Coded strings and short categorical values
text        Free-text fields extracted as actual text, not accuracy-scored
date        Calendar dates
time        Clock times
redacted    Black-barred fields on real forms (``Literal["redacted"]``)
coded_int   Integer codes mapping to named values (e.g. hospital codes)
categorical Closed-vocabulary string fields enforced by Python Enum classes from nar_enums.py (Y/N, Y/N/Unknown, Pos/Neg/Unknown)
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
    "was_resuscitated":               "categorical",
    "rapture_of_membrane":            "categorical",
    "is_multiple_delivery":           "categorical",
    "multiple_delivery_num":    "int",
    "born_before_arrival":            "categorical",
    "born_where":                     "categorical",

    # ------------------------------------------------------------------
    # SECTION B: Mother's details
    "mum_name":                             "redacted",
    "mum_ip_no":                            "redacted",
    "mum_age_in_years":                     "int",
    "parity_live":                          "int",
    "parity_abortions":                     "int",
    "date_estimated_delivery_date":         "date",
    "anc_clinic_name":                      "redacted",
    "anc_visits":                           "int",
    "mum_has_anc_ultrasound":                     "categorical",
    "anc_us_trimester":                           "categorical",
    "us_findings":                          "text",
    "blood_group":                                "categorical",
    "rhesus":                                     "categorical",
    "given_anti_D_medication":                    "categorical",
    "mum_had_vdrl":                               "categorical",
    "mum_pmtct_status":                           "categorical",
    "mum_on_arvs":                                "categorical",
    "mum_had_hepatitis_b":                        "categorical",
    "mum_given_HBIG_treatment":                   "categorical",
    "mum_had_hypertension_in_pregnancy":          "categorical",
    "mum_had_antepartum_haemorrhage":             "categorical",
    "mum_had_diabetes":                           "categorical",
    "prolonged_labour":                           "categorical",

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
    "has_fever":                          "categorical",
    "passed_meconium":                    "categorical",
    "has_difficulty_breathing":           "categorical",
    "passed_urine":                       "categorical",
    "has_difficulty_feeding":             "categorical",
    "has_convulsions":                    "categorical",
    "has_apnoea":                         "categorical",
    "is_floppy":                          "categorical",
    "has_vomiting":                       "categorical",
    "has_diarhoea":                       "categorical",

    # ------------------------------------------------------------------
    # SECTION F1: General examination
    "skin":                               "categorical",
    "jaundice":                           "categorical",
    "appearance":                         "categorical",
    "cry":                                "categorical",
    "has_crackles":                       "categorical",
    "has_grunting":                       "categorical",
    "has_good_air_entry":                 "categorical",
    "has_central_cyanosis":               "categorical",
    "chest_indrawing":                    "categorical",
    "xiphoid_retraction":                 "categorical",
    "intercostal_retraction":             "categorical",
    "capillary_refill_in_seconds":  "float",
    "pallor":                             "categorical",
    "has_murmur":                         "categorical",
    "has_bulging_fontanelle":             "categorical",
    "is_irritable":                       "categorical",
    "tone":                               "categorical",
    "is_distended":                       "categorical",
    "umbilicus":                          "categorical",

    # ------------------------------------------------------------------
    # SECTION F2: Further examination
    "neuro_examination":            "text",
    "further_examination":          "text",
    "has_birth_defects":                  "categorical",
    "birth_defect_types":                 "categorical",

    # ------------------------------------------------------------------
    # SECTION G: Problem list
    "problem_list":                 "text",

    # ------------------------------------------------------------------
    # SECTION H: Investigations
    "rbs_measured":                       "categorical",
    "rbs_value":                    "float",
    "given_bilirubin":                    "categorical",
    "total_serum_bilirubin":        "float",
    "investigations_other":         "text",

    # ------------------------------------------------------------------
    # SECTION I: Diagnoses
    "primary_admission_diagnosis":   "text",
    "secondary_admission_diagnosis": "text",
    "other_diagnoses":               "text",

    # ------------------------------------------------------------------
    # SECTION J: Interventions
    "given_vitamin_k":                    "categorical",
    "given_bcg":                          "categorical",
    "given_chlorhexidine":                "categorical",
    "given_prophylaxis_pmtct":            "categorical",
    "prescribed_transfusion":             "categorical",
    "prescribed_phototherapy":            "categorical",
    "prescribed_cpap":                    "categorical",
    "prescribed_iv_fluids":               "categorical",
    "prescribed_antibiotics":             "categorical",
    "prescribed_feeds":                   "categorical",
    "prescribed_opv":                     "categorical",
    "prescribed_surfactant":              "categorical",
    "prescribed_caffeine_citrate":        "categorical",
    "prescribed_oxygen":                  "categorical",
    "prescribed_kmc":                     "categorical",
    "prescribed_incubator":               "categorical",

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