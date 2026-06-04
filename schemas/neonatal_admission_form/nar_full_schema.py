"""
NARFullRecord — every field visible on the NAR form.

Relationship to NARRecord (nar_schema_included.py):
  - NARRecord  = the *required* structured fields used downstream
  - NARFullRecord = everything the LLM should attempt to extract,
                    including free-text, identifiers, and supplementary fields

The `FULL_SCHEMA_FIELDS` set and `NAR_REQUIRED_FIELDS` set at the bottom
of this file are used by the evaluation pipeline to tag each field as
"included" (in NARRecord) or "not included".
"""

from typing import Optional
from datetime import date, time
from pydantic import BaseModel, Field


class NARFullRecord(BaseModel):
    """
    Complete extraction schema for the Neonatal Admission Record.

    Y/N  → bool   (None = unknown / not ticked)
    text → str
    num  → int
    date → date
    time → time
    """

    # ------------------------------------------------------------------ #
    # SECTION A: Infant details                                           #
    # ------------------------------------------------------------------ #

    # Identifiers are redacted on real forms but present structurally
    infant_name: Optional[str] = Field(None, description="Infant name (redacted/black bar)")
    ip_no: Optional[str] = Field(None, description="IP number (redacted/black bar)")

    admission_date: Optional[date] = Field(None, description="Date of Admission")
    time_seen: Optional[time] = Field(None, description="Time baby seen (24 hr clock)")
    sex: Optional[str] = Field(None, description="Sex: F / M / I")

    birth_date: Optional[date] = Field(None, description="DOB")
    time_birth: Optional[time] = Field(None, description="Time of birth (24 hr clock)")
    gestation_in_weeks: Optional[int] = Field(None, description="Gestation (in weeks)")
    baby_age_in_days: Optional[int] = Field(None, description="Age (in days)")

    gestation_type: Optional[str] = Field(None, description="Gestation age from? U/S or LMP")
    gestation_lmp_weeks: Optional[int] = Field(None, description="LMP weeks value (number next to LMP tick)")

    apgar_1m: Optional[int] = Field(None, description="APGAR score at 1 minute")
    apgar_5m: Optional[int] = Field(None, description="APGAR score at 5 minutes")
    apgar_10m: Optional[int] = Field(None, description="APGAR score at 10 minutes")

    delivery_type: Optional[str] = Field(None, description="Delivery: SVD / CS / Breach / Forceps / Vacuum")
    had_cs: Optional[str] = Field(None, description="If CS, type: Emergency / Elective")
    was_resuscitated: Optional[bool] = Field(None, description="BVM resus at birth: Y/N")
    rapture_of_membrane: Optional[str] = Field(None, description="ROM: <18h / >=18h / Unknown")

    is_multiple_delivery: Optional[bool] = Field(None, description="Multiple delivery: Y/N")
    multiple_delivery_num: Optional[int] = Field(None, description="If YES, number of babies")

    born_before_arrival: Optional[bool] = Field(None, description="Born outside facility: Y/N")
    born_where: Optional[str] = Field(None, description="If yes, where: Home/roadside / Other facility")

    # ------------------------------------------------------------------ #
    # SECTION B: Mother's details                                         #
    # ------------------------------------------------------------------ #

    mum_name: Optional[str] = Field(None, description="Mother name (redacted/black bar)")
    mum_ip_no: Optional[str] = Field(None, description="Mother IP number (redacted/black bar)")

    mum_age_in_years: Optional[int] = Field(None, description="Age (years)")
    parity_live: Optional[int] = Field(None, description="Parity live births")
    parity_abortions: Optional[int] = Field(None, description="Parity abortions/losses")
    parity_total: Optional[str] = Field(None, description="Raw parity string as written, e.g. '2 + 1'")

    date_estimated_delivery_date: Optional[date] = Field(None, description="EDD")

    anc_clinic_name: Optional[str] = Field(None, description="ANC Clinic Name (redacted/black bar)")
    anc_visits: Optional[int] = Field(None, description="ANC no. of visits")

    mum_has_anc_ultrasound: Optional[bool] = Field(None, description="ANC U/S done: Y/N")
    anc_us_trimester: Optional[str] = Field(None, description="ANC U/S trimester if yes")
    us_findings: Optional[str] = Field(None, description="U/S findings free text")

    blood_group: Optional[str] = Field(None, description="Blood group: A / B / AB / O / Unknown")
    rhesus: Optional[str] = Field(None, description="Rhesus: Pos / Neg / Unknown")
    given_anti_D_medication: Optional[str] = Field(None, description="Anti D given: Y / N")

    mum_had_vdrl: Optional[bool] = Field(None, description="VDRL: Pos=True / Neg=False / Unknown=None")
    mum_pmtct_status: Optional[bool] = Field(None, description="PMTCT status: Pos=True / Neg=False / Unknown=None")
    mum_on_arvs: Optional[bool] = Field(None, description="Mother on ARVs: Y=True / N=False / Unknown=None")
    mum_had_hepatitis_b: Optional[bool] = Field(None, description="Hep B: Pos=True / Neg=False / Unknown=None")
    mum_given_HBIG_treatment: Optional[bool] = Field(None, description="Hep B IG given: Y=True / N=False / Unknown=None")
    mum_had_hypertension_in_pregnancy: Optional[bool] = Field(None, description="HTN in pregnancy: Y=True / N=False / Unknown=None")
    mum_had_antepartum_haemorrhage: Optional[bool] = Field(None, description="APH: Y=True / N=False / Unknown=None")
    mum_had_diabetes: Optional[bool] = Field(None, description="Diabetes: Y=True / N=False / Unknown=None")
    prolonged_labour: Optional[bool] = Field(None, description="Prolonged 2nd stage: Y=True / N=False / Unknown=None")

    # ------------------------------------------------------------------ #
    # SECTION C: Maternal illness free text                               #
    # ------------------------------------------------------------------ #

    maternal_illness_notes: Optional[str] = Field(
        None, description="Section C: any maternal illness / fever / TB / antibiotics (free text)"
    )

    # ------------------------------------------------------------------ #
    # SECTION D: Infant presenting problems free text                     #
    # ------------------------------------------------------------------ #

    infant_presenting_problems: Optional[str] = Field(
        None, description="Section D: infant presenting problems narrative (free text)"
    )

    # ------------------------------------------------------------------ #
    # SECTION E: Anthropometry & Vital signs                             #
    # ------------------------------------------------------------------ #

    head_circumference: Optional[int] = Field(None, description="Head circumference (cm)")
    length: Optional[int] = Field(None, description="Length (cm)")
    temparature: Optional[float] = Field(None, description="Temp (°C)")
    respiratory_rate: Optional[int] = Field(None, description="Resp Rate (breaths/min)")
    systolic_blood_pressure: Optional[int] = Field(None, description="Systolic BP (mmHg)")
    diastolic_blood_pressure: Optional[int] = Field(None, description="Diastolic BP (mmHg)")
    pulse_rate: Optional[int] = Field(None, description="Pulse (/min)")
    pulse_oximetry: Optional[int] = Field(None, description="O₂ Sat (%)")
    birth_weight: Optional[int] = Field(None, description="Birth Weight (grams)")
    weight: Optional[int] = Field(None, description="Weight now (grams)")

    # Symptoms (checkboxes)
    has_fever: Optional[bool] = Field(None, description="Fever: Y/N")
    passed_meconium: Optional[bool] = Field(None, description="Passed meconium/stool: Y/N")
    has_difficulty_breathing: Optional[bool] = Field(None, description="Difficulty breathing: Y/N")
    passed_urine: Optional[bool] = Field(None, description="Passed urine in last 12 hours: Y/N")
    has_difficulty_feeding: Optional[bool] = Field(None, description="Inability to feed: Y/N")
    has_convulsions: Optional[bool] = Field(None, description="Convulsions / Twitching: Y/N")
    has_apnoea: Optional[bool] = Field(None, description="Apnoea: Y/N")
    is_floppy: Optional[bool] = Field(None, description="Reduced / Absent movement: Y/N")
    has_vomiting: Optional[bool] = Field(None, description="Bilious Vomiting: Y/N")
    has_diarhoea: Optional[bool] = Field(None, description="Bloody stool: Y/N")

    # ------------------------------------------------------------------ #
    # SECTION F1: General examination                                     #
    # ------------------------------------------------------------------ #

    skin: Optional[str] = Field(None, description="Skin: Normal / Bruising / Rash / Pustules / Mottling / Dry-peeling-wrinkled")
    jaundice: Optional[str] = Field(None, description="Jaundice: None / + / +++")
    appearance: Optional[str] = Field(None, description="Appearance: Well / Sick / Dysmorphic")
    cry: Optional[str] = Field(None, description="Cry: Normal / Weak-Absent / Hoarse")

    # A & B
    has_crackles: Optional[bool] = Field(None, description="Crackles: Y/N")
    has_grunting: Optional[bool] = Field(None, description="Grunting: Y/N")
    has_good_air_entry: Optional[bool] = Field(None, description="Good bilateral air entry: Y/N")
    has_central_cyanosis: Optional[bool] = Field(None, description="Central cyanosis: Y/N")
    chest_indrawing: Optional[bool] = Field(None, description="Lower chest indrawing: Y/N")
    xiphoid_retraction: Optional[str] = Field(None, description="Xiphoid retraction: None / Mild / Severe")
    intercostal_retraction: Optional[str] = Field(None, description="Intercostal retraction: None / Mild / Severe")

    # C
    capillary_refill_in_seconds: Optional[float] = Field(None, description="Capillary refill (seconds)")
    pallor: Optional[str] = Field(None, description="Pallor/Anaemia: None / + / +++")
    has_murmur: Optional[bool] = Field(None, description="Murmur: Y/N")

    # D
    has_bulging_fontanelle: Optional[bool] = Field(None, description="Bulging fontanelle: Y/N")
    is_irritable: Optional[bool] = Field(None, description="Irritable: Y/N")
    tone: Optional[str] = Field(None, description="Tone: Normal / Increased / Reduced")

    # Abdomen
    is_distended: Optional[bool] = Field(None, description="Abdominal distension: Y/N")
    umbilicus: Optional[str] = Field(None, description="Umbilicus: Clean / Local pus / Pus+Red skin / Others")

    # ------------------------------------------------------------------ #
    # SECTION F2: Further examination                                     #
    # ------------------------------------------------------------------ #

    neuro_examination: Optional[str] = Field(
        None, description="F2 neuro: abnormal posture/movement and reflexes (free text)"
    )
    further_examination: Optional[str] = Field(
        None, description="F2 further exam of Resp/CVS/GIT/GU/Skin/Birth Trauma (free text)"
    )

    has_birth_defects: Optional[bool] = Field(None, description="Birth defects: Y/N")
    birth_defect_types: Optional[str] = Field(
        None,
        description=(
            "Birth defect types if yes (checkboxes that are comma-separated from: "
            "Major GI abnormality, Hydrocephalus, Cleft lip/palate, "
            "Microcephaly, Neural tube defects, Spina bifida, "
            "Limb abnormalities, Birth injury/abnormalities)"
        ),
    )

    # ------------------------------------------------------------------ #
    # SECTION G: Summary of presentation                                  #
    # ------------------------------------------------------------------ #

    problem_list: Optional[str] = Field(None, description="Section G: problem list free text (most important first)")

    # ------------------------------------------------------------------ #
    # SECTION H: Investigations                                           #
    # ------------------------------------------------------------------ #

    rbs_measured: Optional[bool] = Field(None, description="RBS: Y/N")
    rbs_value: Optional[float] = Field(None, description="RBS result value (µmol/L or mmol/L)")
    given_bilirubin: Optional[bool] = Field(None, description="Bilirubin: Y/N")
    total_serum_bilirubin: Optional[float] = Field(None, description="Total serum bilirubin value (µmol/L)")
    investigations_other: Optional[str] = Field(None, description="List other investigations ordered (free text)")

    # ------------------------------------------------------------------ #
    # SECTION I: Diagnoses                                                #
    # ------------------------------------------------------------------ #

    primary_admission_diagnosis: Optional[str] = Field(None, description="Primary diagnosis where the ticked box is tick box '1'")
    secondary_admission_diagnosis: Optional[str] = Field(None, description="Primary diagnosis where the ticked box is tick box '2'")

    # ------------------------------------------------------------------ #
    # SECTION J: Interventions                                            #
    # ------------------------------------------------------------------ #

    given_vitamin_k: Optional[bool] = Field(None, description="Vitamin K (& TEO) given: Y/N")
    given_bcg: Optional[bool] = Field(None, description="BCG given: Y/N")
    given_chlorhexidine: Optional[bool] = Field(None, description="Chlorhexidine given: Y/N")
    given_prophylaxis_pmtct: Optional[bool] = Field(None, description="PMTCT prophylaxis given: Y/N")

    prescribed_transfusion: Optional[bool] = Field(None, description="Transfusion prescribed: Y/N")
    prescribed_phototherapy: Optional[bool] = Field(None, description="Phototherapy prescribed: Y/N")
    prescribed_cpap: Optional[bool] = Field(None, description="CPAP prescribed: Y/N")
    prescribed_iv_fluids: Optional[bool] = Field(None, description="IV fluids prescribed: Y/N")
    prescribed_antibiotics: Optional[bool] = Field(None, description="Antibiotics prescribed: Y/N")
    prescribed_feeds: Optional[bool] = Field(None, description="Feeds/Nutrition prescribed: Y/N")
    prescribed_opv: Optional[bool] = Field(None, description="OPV prescribed: Y/N")
    prescribed_surfactant: Optional[bool] = Field(None, description="Surfactant prescribed: Y/N")
    prescribed_caffeine_citrate: Optional[bool] = Field(None, description="Caffeine citrate prescribed: Y/N")
    prescribed_oxygen: Optional[bool] = Field(None, description="Oxygen prescribed: Y/N")
    prescribed_kmc: Optional[bool] = Field(None, description="KMC prescribed: Y/N")
    prescribed_incubator: Optional[bool] = Field(None, description="Incubator/keep warm prescribed: Y/N")

    # ------------------------------------------------------------------ #
    # SECTION K: Action plan                                              #
    # ------------------------------------------------------------------ #

    clinician_name: Optional[str] = Field(None, description="Clinician name (redacted/black bar)")
    clinician_signature: Optional[str] = Field(None, description="Clinician signature (redacted/black bar)")
    action_plan_time: Optional[time] = Field(None, description="Action plan time (24 hr)")
    action_plan_date: Optional[date] = Field(None, description="Action plan date (dd-mm-yyyy)")

    # ------------------------------------------------------------------ #
    # Internal / derived                                                  #
    # ------------------------------------------------------------------ #

    record_type: str = "NAR"


# ------------------------------------------------------------------ #
# Field membership sets — used by the evaluation pipeline            #
# ------------------------------------------------------------------ #

from schemas.neonatal_admission_form.nar_schema_included import NARRecord as _NARRecord

# All fields the full extraction schema covers
FULL_SCHEMA_FIELDS: set[str] = set(NARFullRecord.model_fields.keys())

# Fields that are also in the required NARRecord
NAR_REQUIRED_FIELDS: set[str] = set(_NARRecord.model_fields.keys())

# Convenience: fields present in full schema but NOT required downstream
SUPPLEMENTARY_FIELDS: set[str] = FULL_SCHEMA_FIELDS - NAR_REQUIRED_FIELDS


def inclusion_status(field: str) -> str:
    """Return 'included' if the field is in NARRecord, else 'not included'."""
    return "included" if field in NAR_REQUIRED_FIELDS else "not included"