"""
field_types.py

Maps every field in NARFullRecord to its data type category.
Used by the evaluation pipeline for accuracy breakdowns by type.

Categories:
  bool        — Y/N checkboxes (None = unknown/not ticked)
  int         — whole numbers
  float       — decimal numbers
  str         — coded strings, short categorical values
  text        — free-text fields (Literal["text"] in schema)
  date        — calendar dates
  time        — clock times
  redacted    — fields that are black-barred on real forms (Literal["redacted"])
  coded_int   — integer codes mapping to named values (e.g. hospital codes)
"""

FIELD_TYPES: dict[str, str] = {

    # ------------------------------------------------------------------ #
    # SECTION A: Infant details                                           #
    # ------------------------------------------------------------------ #
    "infant_name":              "redacted",
    "ip_no":                    "redacted",
    "admission_date":           "date",
    "time_seen":                "time",
    "sex":                      "str",
    "birth_date":               "date",
    "time_birth":               "time",
    "gestation_in_weeks":       "int",
    "baby_age_in_days":         "int",
    "gestation_type":           "str",
    "apgar_1m":                 "int",
    "apgar_5m":                 "int",
    "apgar_10m":                "int",
    "delivery_type":            "str",
    "had_cs":                   "str",
    "was_resuscitated":         "bool",
    "rapture_of_membrane":      "str",
    "is_multiple_delivery":     "bool",
    "multiple_delivery_num":    "int",
    "born_before_arrival":      "bool",
    "born_where":               "str",

    # ------------------------------------------------------------------ #
    # SECTION B: Mother's details                                         #
    # ------------------------------------------------------------------ #
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
    "anc_us_trimester":                     "str",
    "us_findings":                          "text",
    "blood_group":                          "str",
    "rhesus":                               "str",
    "given_anti_D_medication":              "str",
    "mum_had_vdrl":                         "bool",
    "mum_pmtct_status":                     "bool",
    "mum_on_arvs":                          "bool",
    "mum_had_hepatitis_b":                  "bool",
    "mum_given_HBIG_treatment":             "bool",
    "mum_had_hypertension_in_pregnancy":    "bool",
    "mum_had_antepartum_haemorrhage":       "bool",
    "mum_had_diabetes":                     "bool",
    "prolonged_labour":                     "bool",

    # ------------------------------------------------------------------ #
    # SECTION C & D: Free text                                            #
    # ------------------------------------------------------------------ #
    "maternal_illness_notes":       "text",
    "infant_presenting_problems":   "text",

    # ------------------------------------------------------------------ #
    # SECTION E: Anthropometry & Vital signs                             #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # SECTION F1: General examination                                     #
    # ------------------------------------------------------------------ #
    "skin":                         "str",
    "jaundice":                     "str",
    "appearance":                   "str",
    "cry":                          "str",
    "has_crackles":                 "bool",
    "has_grunting":                 "bool",
    "has_good_air_entry":           "bool",
    "has_central_cyanosis":         "bool",
    "chest_indrawing":              "bool",
    "xiphoid_retraction":           "str",
    "intercostal_retraction":       "str",
    "capillary_refill_in_seconds":  "int",
    "pallor":                       "str",
    "has_murmur":                   "bool",
    "has_bulging_fontanelle":       "bool",
    "is_irritable":                 "bool",
    "tone":                         "str",
    "is_distended":                 "bool",
    "umbilicus":                    "str",

    # ------------------------------------------------------------------ #
    # SECTION F2: Further examination                                     #
    # ------------------------------------------------------------------ #
    "neuro_examination":            "text",
    "further_examination":          "text",
    "has_birth_defects":            "bool",
    "birth_defect_types":           "str",

    # ------------------------------------------------------------------ #
    # SECTION G: Problem list                                             #
    # ------------------------------------------------------------------ #
    "problem_list":                 "text",

    # ------------------------------------------------------------------ #
    # SECTION H: Investigations                                           #
    # ------------------------------------------------------------------ #
    "rbs_measured":                 "bool",
    "rbs_value":                    "float",
    "given_bilirubin":              "bool",
    "total_serum_bilirubin":        "float",
    "investigations_other":         "text",

    # ------------------------------------------------------------------ #
    # SECTION I: Diagnoses                                                #
    # ------------------------------------------------------------------ #
    "primary_admission_diagnosis":      "text",
    "secondary_admission_diagnosis":    "text",
    "other_diagnoses": "text",

    # ------------------------------------------------------------------ #
    # SECTION J: Interventions                                            #
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    # SECTION K: Action plan                                              #
    # ------------------------------------------------------------------ #
    "clinician_name":       "redacted",
    "clinician_signature":  "redacted",
    "action_plan_time":     "time",
    "action_plan_date":     "date",

    # ------------------------------------------------------------------ #
    # Internal / derived                                                  #
    # ------------------------------------------------------------------ #
    "hospital":         "coded_int",    # integer code → facility name
    "record_type":      "str",
}

# ------------------------------------------------------------------ #
# Hospital code → name lookup                                         #
# ------------------------------------------------------------------ #
HOSPITAL_CODES: dict[int, str] = {
    8: "63000002_NAR_",
    9: "64000002_NAR_",
}


def decode_hospital(code: int | None) -> str | None:
    """Return the name(facility code) for a code(hospital record_name), or None if unknown."""
    if code is None:
        return None
    return HOSPITAL_CODES.get(int(code))