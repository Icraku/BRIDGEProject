"""
schemas/neonatal_admission_form/nar_full_schema.py
====================================================
``NARFullRecord`` — the complete extraction schema for the Neonatal
Admission Record (NAR) form.

Relationship to ``NARRecord`` (``nar_schema_included.py``)
----------------------------------------------------------
- ``NARRecord``    = the 98 *required* fields used for ground-truth
                     evaluation and further analysis.
- ``NARFullRecord`` = all 120 fields the LLM is asked to extract,
                      including redacted identifiers, free-text sections
                      and 22 supplementary fields not present in the GT.

All fields are ``Optional`` with a default of ``None`` so that the LLM's
structured-output layer never raises a validation error for missing values.

The sets ``FULL_SCHEMA_FIELDS``, ``NAR_REQUIRED_FIELDS``, and
``SUPPLEMENTARY_FIELDS`` at the bottom of this file are imported by every
evaluation module to tag fields as ``"included"`` or ``"not included"``.
"""

from __future__ import annotations

from datetime import date, time
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field

from schemas.neonatal_admission_form.categorical_Enums import (
    ANCTrimesterEnum, AntiDEnum, AppearanceEnum, BloodGroupEnum,
    BornWhereEnum, CSTypeEnum, CryEnum, DeliveryTypeEnum,
    GestationTypeEnum, JaundiceEnum, PallorEnum, RetractionSeverityEnum,
    RhesusEnum, ROMEnum, SexEnum, SkinEnum, ToneEnum, UmbilicusEnum, BirthDefectsEnum,
)

# NARRecord is imported here (not at the bottom) so the dependency is
# explicit and linters can resolve it correctly.
from schemas.neonatal_admission_form.nar_schema_included import NARRecord as _NARRecord

class NARFullRecord(BaseModel):
    """Complete extraction schema for the two-page NAR form.

    Type conventions
    ----------------
    ``Optional[bool]``              Y/N checkboxes  (``None`` = blank / unknown)
    ``Optional[int]``               Whole numbers
    ``Optional[float]``             Decimal numbers
    ``Optional[FieldEnum]``.        Categorical fields with constrained valid values from see nar_enums.py
    ``Optional[str]``   Free-text fields (not accuracy-scored vs GT)
    ``Optional[Literal["text"]]``   Free-text fields (not accuracy-scored vs GT)
    ``Optional[Literal["redacted"]]`` Black-barred identifiers on real forms
    ``Optional[date]``              Calendar dates
    ``Optional[time]``              Clock times
    """

    # ------------------------------------------------------------------
    # SECTION A: Infant details

    # Identifiers are physically redacted (black bar) on real forms
    infant_name: Optional[Literal["redacted"]] = Field(
        None, description="Infant name (redacted on real form)"
    )
    ip_no: Optional[Literal["redacted"]] = Field(
        None, description="IP number (redacted on real form)"
    )

    admission_date: Optional[date] = Field(..., description="Date of Admission")
    time_seen: Optional[time] = Field(None, description="Time baby seen (24 hr clock)")
    sex: Optional[SexEnum] = Field(None, description="Sex of the infant: F / M / I")

    birth_date: Optional[date] = Field(None, description="DOB")
    time_birth: Optional[time] = Field(None, description="Time of birth (24 hr clock)")
    gestation_in_weeks: Optional[int] = Field(None, description="Gestation (in weeks)")
    baby_age_in_days: Optional[int] = Field(None, description="Age (in days)")

    gestation_type: Optional[GestationTypeEnum] = Field(
        None, description="Gestation age from: U/S or LMP"
    )
    apgar_1m: Optional[int] = Field(None, description="APGAR score at 1 minute")
    apgar_5m: Optional[int] = Field(None, description="APGAR score at 5 minutes")
    apgar_10m: Optional[int] = Field(None, description="APGAR score at 10 minutes")

    delivery_type: Optional[DeliveryTypeEnum] = Field(
        None, description="Mode of delivery: SVD / CS / Breach / Forceps / Vacuum"
    )
    had_cs: Optional[CSTypeEnum] = Field(None, description="If CS, type: Emergency / Elective")
    was_resuscitated: Optional[bool] = Field(None, description="BVM resus at birth: Y/N")
    rapture_of_membrane: Optional[ROMEnum] = Field(
        None, description="ROM: <18h (less than 18 hours) / >=18h (greater than 18 hours) / Unknown"
    )

    is_multiple_delivery: Optional[bool] = Field(None, description="Multiple delivery: Y/N")
    multiple_delivery_num: Optional[int] = Field(
        None, description="If YES, number of babies"
    )

    born_before_arrival: Optional[bool] = Field(
        None, description="Born outside facility: Y/N"
    )
    born_where: Optional[BornWhereEnum] = Field(
        None, description="If born outside facility: 1) Home or roadside / 2) Other facility"
    )

    # ------------------------------------------------------------------
    # SECTION B: Mother's details

    mum_name: Optional[Literal["redacted"]] = Field(
        None, description="Mother name (redacted on real form)"
    )
    mum_ip_no: Optional[Literal["redacted"]] = Field(
        None, description="Mother IP number (redacted on real form)"
    )

    mum_age_in_years: Optional[int] = Field(None, description="Age (years)")
    parity_live: Optional[int] = Field(None, description="Parity live births")
    parity_abortions: Optional[int] = Field(None, description="Parity abortions/losses")
    parity_total: Optional[int] = Field(
        None, description="Total parity as written on form, e.g. '2 + 1'"
    )

    date_estimated_delivery_date: Optional[date] = Field(None, description="EDD")

    anc_clinic_name: Optional[Literal["redacted"]] = Field(
        None, description="ANC Clinic Name (redacted on real form)"
    )
    anc_visits: Optional[int] = Field(None, description="ANC no. of visits")

    mum_has_anc_ultrasound: Optional[bool] = Field(None, description="ANC U/S done: Y/N")
    anc_us_trimester: Optional[ANCTrimesterEnum] = Field(
        None, description="ANC U/S trimester: 1st / 2nd / 3rd"
    )
    us_findings: Optional[Literal["text"]] = Field(
        None, description="U/S findings free text"
    )

    blood_group: Optional[BloodGroupEnum] = Field(
        None, description="Blood group type: A / B / AB / O / Unknown"
    )
    rhesus: Optional[RhesusEnum] = Field(None, description="Rhesus: Positive / Negative / Unknown")
    given_anti_D_medication: Optional[AntiDEnum] = Field(None, description="Anti D given: Y / N / Unknown")

    mum_had_vdrl: Optional[bool] = Field(
        None, description="VDRL: Pos=True / Neg=False / Unknown=None"
    )
    mum_pmtct_status: Optional[bool] = Field(
        None, description="PMTCT status: Pos=True / Neg=False / Unknown=None"
    )
    mum_on_arvs: Optional[bool] = Field(
        None, description="Mother on ARVs: Y=True / N=False / Unknown=None"
    )
    mum_had_hepatitis_b: Optional[bool] = Field(
        None, description="Hep B: Pos=True / Neg=False / Unknown=None"
    )
    mum_given_HBIG_treatment: Optional[bool] = Field(
        None, description="Hep B IG given: Y=True / N=False / Unknown=None"
    )
    mum_had_hypertension_in_pregnancy: Optional[bool] = Field(
        None, description="HTN in pregnancy: Y=True / N=False / Unknown=None"
    )
    mum_had_antepartum_haemorrhage: Optional[bool] = Field(
        None, description="APH: Y=True / N=False / Unknown=None"
    )
    mum_had_diabetes: Optional[bool] = Field(
        None, description="Diabetes: Y=True / N=False / Unknown=None"
    )
    prolonged_labour: Optional[bool] = Field(
        None, description="Prolonged 2nd stage: Y=True / N=False / Unknown=None"
    )

    # ------------------------------------------------------------------
    # SECTION C: Maternal illness free text

    maternal_illness_notes: Optional[str] = Field(
        None,
        description=(
            "Section C: any maternal illness / fever / TB / antibiotics (free text)"
        ),
    )

    # ------------------------------------------------------------------
    # SECTION D: Infant presenting problems free text

    infant_presenting_problems: Optional[str] = Field(
        None,
        description="Section D: infant presenting problems narrative (free text)",
    )

    # ------------------------------------------------------------------
    # SECTION E: Anthropometry & Vital signs

    head_circumference: Optional[int] = Field(None, description="Head circumference (cm)")
    length: Optional[int] = Field(None, description="Length (cm)")
    temparature: Optional[float] = Field(None, description="Temp (°C)")
    respiratory_rate: Optional[int] = Field(None, description="Resp Rate (breaths/min)")
    systolic_blood_pressure: Optional[int] = Field(None, description="Systolic BP (mmHg)")
    diastolic_blood_pressure: Optional[int] = Field(
        None, description="Diastolic BP (mmHg)"
    )
    pulse_rate: Optional[int] = Field(None, description="Pulse (/min)")
    pulse_oximetry: Optional[int] = Field(None, description="O₂ Sat (%)")
    birth_weight: Optional[int] = Field(None, description="Birth Weight (grams)")
    weight: Optional[int] = Field(None, description="Weight now (grams)")

    # Symptoms (checkboxes)
    has_fever: Optional[bool] = Field(None, description="Fever: Y/N")
    passed_meconium: Optional[bool] = Field(None, description="Passed meconium/stool: Y/N")
    has_difficulty_breathing: Optional[bool] = Field(
        None, description="Difficulty breathing: Y/N"
    )
    passed_urine: Optional[bool] = Field(
        None, description="Passed urine in last 12 hours: Y/N"
    )
    has_difficulty_feeding: Optional[bool] = Field(
        None, description="Inability to feed: Y/N"
    )
    has_convulsions: Optional[bool] = Field(
        None, description="Convulsions / Twitching: Y/N"
    )
    has_apnoea: Optional[bool] = Field(None, description="Apnoea: Y/N")
    is_floppy: Optional[bool] = Field(
        None, description="Reduced / Absent movement: Y/N"
    )
    has_vomiting: Optional[bool] = Field(None, description="Bilious Vomiting: Y/N")
    has_diarhoea: Optional[bool] = Field(None, description="Bloody stool: Y/N")

    # ------------------------------------------------------------------
    # SECTION F1: General examination

    skin: Optional[SkinEnum] = Field(
        None,
        description="Skin appearance: Normal / Bruising / Rash / Pustules / Mottling / Dry-peeling-wrinkled",
    )
    jaundice: Optional[JaundiceEnum] = Field(None, description="Jaundice severity: None / Mild(+) / Severe(+++)")
    appearance: Optional[AppearanceEnum] = Field(
        None, description="General appearance: Well / Sick / Dysmorphic"
    )
    cry: Optional[CryEnum] = Field(
        None, description="Cry quality: Normal / Weak-Absent / Hoarse"
    )

    # A & B (Respiratory)
    has_crackles: Optional[bool] = Field(None, description="Crackles: Y/N")
    has_grunting: Optional[bool] = Field(None, description="Grunting: Y/N")
    has_good_air_entry: Optional[bool] = Field(
        None, description="Good bilateral air entry: Y/N"
    )
    has_central_cyanosis: Optional[bool] = Field(
        None, description="Central cyanosis: Y/N"
    )
    chest_indrawing: Optional[RetractionSeverityEnum] = Field(
        None, description="Lower chest indrawing: None / Mild / Severe"
    )
    xiphoid_retraction: Optional[RetractionSeverityEnum] = Field(
        None, description="Xiphoid retraction: None / Mild / Severe"
    )
    intercostal_retraction: Optional[RetractionSeverityEnum] = Field(
        None, description="Intercostal retraction: None / Mild / Severe"
    )

    # C (Cardiovascular)
    capillary_refill_in_seconds: Optional[float] = Field(
        None, description="Capillary refill (seconds)"
    )
    pallor: Optional[PallorEnum] = Field(None, description="Pallor/Anaemia severity: None / Mild(+) / Severe(++)")
    has_murmur: Optional[bool] = Field(None, description="Murmur: Y/N")

    # D (Neurological)
    has_bulging_fontanelle: Optional[bool] = Field(
        None, description="Bulging fontanelle: Y/N"
    )
    is_irritable: Optional[bool] = Field(None, description="Irritable: Y/N")
    tone: Optional[ToneEnum] = Field(
        None, description="Tone: Normal / Increased / Reduced"
    )

    # Abdomen
    is_distended: Optional[bool] = Field(
        None, description="Abdominal distension: Y/N"
    )
    umbilicus: Optional[UmbilicusEnum] = Field(
        None,
        description="Umbilicus: Clean / Local pus / Pus+Red skin / Others",
    )

    # ------------------------------------------------------------------
    # SECTION F2: Further examination

    neuro_examination: Optional[str] = Field(
        None,
        description=(
            "F2 neuro: abnormal posture / movement and reflexes (free text)"
        ),
    )
    further_examination: Optional[str] = Field(
        None,
        description=(
            "F2 further exam of Resp / CVS / GIT / GU / Skin / Birth Trauma (free text)"
        ),
    )

    has_birth_defects: Optional[bool] = Field(None, description="Birth defects: Y/N")
    birth_defect_types: Optional[BirthDefectsEnum] = Field(
        None,
        description=(
            "Birth defect types if yes (comma-separated from: Major GI abnormality, "
            "Hydrocephalus, Cleft lip/palate, Microcephaly, Neural tube defects, "
            "Spina bifida, Limb abnormalities, Birth injury/abnormalities)"
        ),
    )

    # ------------------------------------------------------------------
    # SECTION G: Summary of presentation

    problem_list: Optional[str] = Field(
        None,
        description="Section G: problem list free text (most important first)",
    )

    # ------------------------------------------------------------------
    # SECTION H: Investigations

    rbs_measured: Optional[bool] = Field(None, description="RBS measured: Y/N")
    rbs_value: Optional[float] = Field(None, description="RBS result value (mmol/L)")
    given_bilirubin: Optional[bool] = Field(None, description="Bilirubin measured: Y/N")
    total_serum_bilirubin: Optional[float] = Field(
        None, description="Total serum bilirubin value (µmol/L)"
    )
    investigations_other: Optional[str] = Field(
        None, description="Other investigations ordered (free text)"
    )

    # ------------------------------------------------------------------
    # SECTION I: Diagnoses

    primary_admission_diagnosis: Optional[str] = Field(
        None, description="Primary diagnosis (tick box '1')"
    )
    secondary_admission_diagnosis: Optional[str] = Field(
        None, description="Secondary diagnosis (tick box '2')"
    )
    other_diagnoses: Optional[str] = Field(
        None, description="Other diagnoses (free text, listed below tick boxes)"
    )

    # ------------------------------------------------------------------
    # SECTION J: Interventions

    given_vitamin_k: Optional[bool] = Field(
        None, description="Vitamin K (& TEO) given: Y/N"
    )
    given_bcg: Optional[bool] = Field(None, description="BCG given: Y/N")
    given_chlorhexidine: Optional[bool] = Field(
        None, description="Chlorhexidine given: Y/N"
    )
    given_prophylaxis_pmtct: Optional[bool] = Field(
        None, description="PMTCT prophylaxis given: Y/N"
    )
    prescribed_transfusion: Optional[bool] = Field(
        None, description="Transfusion prescribed: Y/N"
    )
    prescribed_phototherapy: Optional[bool] = Field(
        None, description="Phototherapy prescribed: Y/N"
    )
    prescribed_cpap: Optional[bool] = Field(None, description="CPAP prescribed: Y/N")
    prescribed_iv_fluids: Optional[bool] = Field(
        None, description="IV fluids prescribed: Y/N"
    )
    prescribed_antibiotics: Optional[bool] = Field(
        None, description="Antibiotics prescribed: Y/N"
    )
    prescribed_feeds: Optional[bool] = Field(
        None, description="Feeds/Nutrition prescribed: Y/N"
    )
    prescribed_opv: Optional[bool] = Field(None, description="OPV prescribed: Y/N")
    prescribed_surfactant: Optional[bool] = Field(
        None, description="Surfactant prescribed: Y/N"
    )
    prescribed_caffeine_citrate: Optional[bool] = Field(
        None, description="Caffeine citrate prescribed: Y/N"
    )
    prescribed_oxygen: Optional[bool] = Field(None, description="Oxygen prescribed: Y/N")
    prescribed_kmc: Optional[bool] = Field(None, description="KMC prescribed: Y/N")
    prescribed_incubator: Optional[bool] = Field(
        None, description="Incubator/keep warm prescribed: Y/N"
    )

    # ------------------------------------------------------------------
    # SECTION K: Action plan

    clinician_name: Optional[Literal["redacted"]] = Field(
        None, description="Clinician name (redacted on real form)"
    )
    clinician_signature: Optional[Literal["redacted"]] = Field(
        None, description="Clinician signature (redacted on real form)"
    )
    action_plan_time: Optional[time] = Field(None, description="Action plan time (24 hr)")
    action_plan_date: Optional[date] = Field(
        None, description="Action plan date (dd-mm-yyyy)"
    )

    # ------------------------------------------------------------------
    # Internal / derived

    record_type: str = Field(default="NAR", description="Record type identifier")


# ---------------------------------------------------------------------------
# Fields membership in schemas — imported by every evaluation module
# ---------------------------------------------------------------------------

# All fields extracted (120 fields)
FULL_SCHEMA_FIELDS: set[str] = set(NARFullRecord.model_fields.keys())

# Fields required in the NARRecord (98 fields)
# NAR_REQUIRED_FIELDS is derived from NARRecord at import time, adding
# or removing a field from nar_schema_included.py updates this automatically.
NAR_REQUIRED_FIELDS: set[str] = set(_NARRecord.model_fields.keys())

# Fields present in full schema but NOT required downstream (22 supplementary)
SUPPLEMENTARY_FIELDS: set[str] = FULL_SCHEMA_FIELDS - NAR_REQUIRED_FIELDS


def inclusion_status(field: str) -> str:
    """Return ``"included"`` if *field* is in ``NARRecord``, else ``"not included"``."""
    return "included" if field in NAR_REQUIRED_FIELDS else "not included"