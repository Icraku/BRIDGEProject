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
    ANCTrimesterEnum, AppearanceEnum, BloodGroupEnum, #AntiDEnum,
    BornWhereEnum, CSTypeEnum, CryEnum, DeliveryTypeEnum,
    GestationTypeEnum, JaundiceEnum, PallorEnum, RetractionSeverityEnum,
    RhesusEnum, ROMEnum, SexEnum, YesNoEnum, YesNoUnknownEnum, PositiveNegativeUnknownEnum,
    SkinEnum, ToneEnum, UmbilicusEnum, BirthDefectsEnum,

)

# NARRecord is imported here (not at the bottom) so the dependency is
# explicit and linters can resolve it correctly.
from schemas.neonatal_admission_form.nar_schema_included import NARRecord as _NARRecord

class NARFullRecord(BaseModel):
    """Complete extraction schema for the two-page NAR form.

    Type conventions
    ----------------
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
        ..., description="Infant name"
    )
    ip_no: Optional[Literal["redacted"]] = Field(
        ..., description="IP number"
    )

    admission_date: Optional[date] = Field(..., description="Date of Admission")
    time_seen: Optional[time] = Field(..., description="Time baby seen (24 hr clock)")
    sex: Optional[SexEnum] = Field(..., description="Sex of the infant")

    birth_date: Optional[date] = Field(..., description="DOB")
    time_birth: Optional[time] = Field(..., description="Time of birth (24 hr clock)")
    gestation_in_weeks: Optional[int] = Field(..., description="Gestation (in weeks)")
    baby_age_in_days: Optional[int] = Field(..., description="Age (in days)")

    gestation_type: Optional[GestationTypeEnum] = Field(
        ..., description="Gestation age from"
    )
    apgar_1m: Optional[int] = Field(..., description="APGAR score at 1 minute")
    apgar_5m: Optional[int] = Field(..., description="APGAR score at 5 minutes")
    apgar_10m: Optional[int] = Field(..., description="APGAR score at 10 minutes")

    delivery_type: Optional[DeliveryTypeEnum] = Field(
        ..., description="Mode of delivery"
    )
    had_cs: Optional[CSTypeEnum] = Field(..., description="If CS, type")
    was_resuscitated: Optional[YesNoEnum] = Field(..., description="BVM resus at birth")
    rapture_of_membrane: Optional[ROMEnum] = Field(
        ..., description="ROM"
    )

    is_multiple_delivery: Optional[YesNoEnum] = Field(..., description="Multiple delivery")
    multiple_delivery_num: Optional[int] = Field(
        ..., description="If YES, number of babies"
    )

    born_before_arrival: Optional[YesNoEnum] = Field(
        ..., description="Born outside facility"
    )
    born_where: Optional[BornWhereEnum] = Field(
        ..., description="If born outside facility"
    )

    # ------------------------------------------------------------------
    # SECTION B: Mother's details

    mum_name: Optional[Literal["redacted"]] = Field(
        ..., description="Mother name"
    )
    mum_ip_no: Optional[Literal["redacted"]] = Field(
        ..., description="Mother IP number"
    )

    mum_age_in_years: Optional[int] = Field(..., description="Age (years)")
    parity_live: Optional[int] = Field(..., description="Parity live births")
    parity_abortions: Optional[int] = Field(..., description="Parity abortions/losses")

    date_estimated_delivery_date: Optional[date] = Field(..., description="EDD")

    anc_clinic_name: Optional[Literal["redacted"]] = Field(
        ..., description="ANC Clinic Name (redacted on real form)"
    )
    anc_visits: Optional[int] = Field(..., description="ANC no. of visits")

    mum_has_anc_ultrasound: Optional[YesNoEnum] = Field(..., description="ANC U/S done")
    anc_us_trimester: Optional[ANCTrimesterEnum] = Field(
        ..., description="ANC U/S trimester"
    )
    us_findings: Optional[Literal["text"]] = Field(
        ..., description="U/S findings free text"
    )

    blood_group: Optional[BloodGroupEnum] = Field(
        ..., description="Blood group type"
    )
    rhesus: Optional[RhesusEnum] = Field(..., description="Rhesus")
    given_anti_D_medication: Optional[YesNoEnum] = Field(..., description="Anti D given")

    mum_had_vdrl: Optional[PositiveNegativeUnknownEnum] = Field(
        ..., description="VDRL"
    )
    mum_pmtct_status: Optional[PositiveNegativeUnknownEnum] = Field(
        ..., description="PMTCT status"
    )
    mum_on_arvs: Optional[YesNoUnknownEnum] = Field(
        ..., description="Mother on ARVs"
    )
    mum_had_hepatitis_b: Optional[PositiveNegativeUnknownEnum] = Field(
        ..., description="Hep B"
    )
    mum_given_HBIG_treatment: Optional[YesNoUnknownEnum] = Field(
        ..., description="Hep B IG given"
    )
    mum_had_hypertension_in_pregnancy: Optional[YesNoUnknownEnum] = Field(
        ..., description="HTN in pregnancy"
    )
    mum_had_antepartum_haemorrhage: Optional[YesNoUnknownEnum] = Field(
        ..., description="APH"
    )
    mum_had_diabetes: Optional[YesNoUnknownEnum] = Field(
        ..., description="Diabetes"
    )
    prolonged_labour: Optional[YesNoUnknownEnum] = Field(
        ..., description="Prolonged 2nd stage"
    )

    # ------------------------------------------------------------------
    # SECTION C: Maternal illness free text

    maternal_illness_notes: Optional[str] = Field(
        ...,
        description=(
            "Section C: Mother's problems during pregnancy/labour & relevant maternal treatment"
        ),
    )

    # ------------------------------------------------------------------
    # SECTION D: Infant presenting problems free text

    infant_presenting_problems: Optional[str] = Field(
        ...,
        description="Section D: Infant presenting problems & any treatment given",
    )

    # ------------------------------------------------------------------
    # SECTION E: Anthropometry & Vital signs

    head_circumference: Optional[int] = Field(..., description="Head circumference (cm)")
    length: Optional[int] = Field(..., description="Length (cm)")
    temparature: Optional[float] = Field(..., description="Temp (°C)")
    respiratory_rate: Optional[int] = Field(..., description="Resp Rate (bpm)")
    blood_pressure: Optional[int] = Field(..., description="Blood Pressure (mmHg)")
    #diastolic_blood_pressure: Optional[int] = Field(..., description="Diastolic BP (mmHg)")
    pulse_rate: Optional[int] = Field(..., description="Pulse (/min)")
    pulse_oximetry: Optional[int] = Field(..., description="O₂ Sat (%)")
    birth_weight: Optional[int] = Field(..., description="Birth Weight (grams)")
    weight: Optional[int] = Field(..., description="Weight now (grams)")

    # Symptoms (checkboxes)
    has_fever: Optional[YesNoEnum] = Field(..., description="Fever")
    passed_meconium: Optional[YesNoEnum] = Field(..., description="Passed meconium/stool")
    has_difficulty_breathing: Optional[YesNoEnum] = Field(
        ..., description="Difficulty breathing"
    )
    passed_urine: Optional[YesNoEnum] = Field(
        ..., description="Passed urine in last 12 hours"
    )
    has_difficulty_feeding: Optional[YesNoEnum] = Field(
        ..., description="Inability to feed"
    )
    has_convulsions: Optional[YesNoEnum] = Field(
        ..., description="Convulsions / Twitching"
    )
    has_apnoea: Optional[YesNoEnum] = Field(..., description="Apnoea")
    is_floppy: Optional[YesNoEnum] = Field(
        ..., description="Reduced / Absent movement"
    )
    has_vomiting: Optional[YesNoEnum] = Field(..., description="Bilious Vomiting")
    has_diarhoea: Optional[YesNoEnum] = Field(..., description="Bloody stool")

    # ------------------------------------------------------------------
    # SECTION F1: General examination

    skin: Optional[SkinEnum] = Field(
        ...,
        description="Skin appearance",
    )
    jaundice: Optional[JaundiceEnum] = Field(..., description="Jaundice severity")
    appearance: Optional[AppearanceEnum] = Field(
        ..., description="Appearance"
    )
    cry: Optional[CryEnum] = Field(
        ..., description="Cry"
    )

    # A & B (Respiratory)
    has_crackles: Optional[YesNoEnum] = Field(..., description="Crackles")
    has_grunting: Optional[YesNoEnum] = Field(..., description="Grunting")
    has_good_air_entry: Optional[YesNoEnum] = Field(
        ..., description="Good bilateral air entry"
    )
    has_central_cyanosis: Optional[YesNoEnum] = Field(
        ..., description="Central cyanosis"
    )
    chest_indrawing: Optional[YesNoEnum] = Field(
        ..., description="Lower chest indrawing"
    )
    xiphoid_retraction: Optional[RetractionSeverityEnum] = Field(
        ..., description="Xiphoid retraction"
    )
    intercostal_retraction: Optional[RetractionSeverityEnum] = Field(
        ..., description="Intercostal retraction"
    )

    # C (Cardiovascular)
    capillary_refill_in_seconds: Optional[float] = Field(
        ..., description="Capillary refill (Sternal) in seconds"
    )
    pallor: Optional[PallorEnum] = Field(..., description="Pallor/Anaemia severity")
    has_murmur: Optional[YesNoEnum] = Field(..., description="Murmur")

    # D (Neurological)
    has_bulging_fontanelle: Optional[YesNoEnum] = Field(
        ..., description="Bulging fontanelle"
    )
    is_irritable: Optional[YesNoEnum] = Field(..., description="Irritable")
    tone: Optional[ToneEnum] = Field(
        ..., description="Tone"
    )

    # Abdomen
    is_distended: Optional[YesNoEnum] = Field(
        ..., description="Abdominal distension"
    )
    umbilicus: Optional[UmbilicusEnum] = Field(
        ...,
        description="Umbilicus",
    )

    # ------------------------------------------------------------------
    # SECTION F2: Further examination

    neuro_examination: Optional[str] = Field(
        ...,
        description=(
            "F2 neuro: abnormal posture / movement and reflexes"
        ),
    )
    further_examination: Optional[str] = Field(
        ...,
        description=(
            "F2 further exam of Resp / CVS / GIT / GU / Skin / Birth Trauma"
        ),
    )

    has_birth_defects: Optional[YesNoEnum] = Field(..., description="Birth defects")
    birth_defect_types: Optional[BirthDefectsEnum] = Field(
        ...,
        description=(
            "Birth defect types if yes"
        ),
    )

    # ------------------------------------------------------------------
    # SECTION G: Summary of presentation

    problem_list: Optional[str] = Field(
        ...,
        description="Section G: Presentation and problem list (most important first)",
    )

    # ------------------------------------------------------------------
    # SECTION H: Investigations

    rbs_measured: Optional[YesNoEnum] = Field(..., description="RBS measured")
    rbs_value: Optional[float] = Field(..., description="RBS result value (mmol/L)")
    given_bilirubin: Optional[YesNoEnum] = Field(..., description="Bilirubin measured")
    total_serum_bilirubin: Optional[float] = Field(
        ..., description="Total serum bilirubin value (µmol/L)"
    )
    investigations_other: Optional[str] = Field(
        ..., description="Other investigations ordered"
    )

    # ------------------------------------------------------------------
    # SECTION I: Diagnoses

    primary_admission_diagnosis: Optional[str] = Field(
        ..., description="Primary diagnosis (tick box '1')"
    )
    secondary_admission_diagnosis: Optional[str] = Field(
        ..., description="Secondary diagnosis (tick box '2')"
    )
    other_diagnoses: Optional[str] = Field(
        ..., description="Other diagnoses (free text, listed below tick boxes)"
    )

    # ------------------------------------------------------------------
    # SECTION J: Interventions

    given_vitamin_k: Optional[YesNoEnum] = Field(
        ..., description="Vitamin K (& TEO) given"
    )
    given_bcg: Optional[YesNoEnum] = Field(..., description="BCG given")
    given_chlorhexidine: Optional[YesNoEnum] = Field(
        ..., description="Chlorhexidine given"
    )
    given_prophylaxis_pmtct: Optional[YesNoEnum] = Field(
        ..., description="PMTCT prophylaxis given"
    )
    prescribed_transfusion: Optional[YesNoEnum] = Field(
        ..., description="Transfusion prescribed"
    )
    prescribed_phototherapy: Optional[YesNoEnum] = Field(
        ..., description="Phototherapy prescribed"
    )
    prescribed_cpap: Optional[YesNoEnum] = Field(..., description="CPAP prescribed")
    prescribed_iv_fluids: Optional[YesNoEnum] = Field(
        ..., description="IV fluids prescribed"
    )
    prescribed_antibiotics: Optional[YesNoEnum] = Field(
        ..., description="Antibiotics prescribed"
    )
    prescribed_feeds: Optional[YesNoEnum] = Field(
        ..., description="Feeds/Nutrition prescribed"
    )
    prescribed_opv: Optional[YesNoEnum] = Field(..., description="OPV prescribed")
    prescribed_surfactant: Optional[YesNoEnum] = Field(
        ..., description="Surfactant prescribed"
    )
    prescribed_caffeine_citrate: Optional[YesNoEnum] = Field(
        ..., description="Caffeine citrate prescribed"
    )
    prescribed_oxygen: Optional[YesNoEnum] = Field(..., description="Oxygen prescribed")
    prescribed_kmc: Optional[YesNoEnum] = Field(..., description="KMC prescribed")
    prescribed_incubator: Optional[YesNoEnum] = Field(
        ..., description="Incubator/keep warm prescribed"
    )

    # ------------------------------------------------------------------
    # SECTION K: Action plan

    action_plan: Optional[str] = Field(
        ..., description="Listed action plans"
    )

    clinician_name: Optional[Literal["redacted"]] = Field(
        ..., description="Clinician name"
    )
    clinician_signature: Optional[Literal["redacted"]] = Field(
        ..., description="Clinician signature"
    )
    action_plan_time: Optional[time] = Field(..., description="Action plan time (24 hr)")
    action_plan_date: Optional[date] = Field(
        ..., description="Action plan date (dd-mm-yyyy)"
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