"""
schemas/neonatal_admission_form/nar_schema_included.py
=======================================================
``NARRecord`` — the 98 required fields used for ground-truth evaluation.

Relationship to ``NARFullRecord`` (``nar_full_schema.py``)
----------------------------------------------------------
- ``NARRecord``     = this file: the *required* structured fields present in
                      the ground-truth (``NAR_metadata.json``).
                      Used by ``build_accuracy_table`` and ``map_to_schema``.
- ``NARFullRecord`` = the full 120-field schema the LLM extracts against.

Design note — strict non-Optional types
----------------------------------------
All fields here are non-Optional (no default values) so that Pydantic
raises a ``ValidationError`` if the structuring pipeline tries to create a
``NARRecord`` with missing required fields to make
incomplete extractions visible early.  The LLM extraction step uses
``NARFullRecord`` (all Optional) and only the final schema-mapped output
is validated against ``NARRecord``.

``NARSchema`` at the bottom is provided for batch-validation use and is not
used by the active pipeline.
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.neonatal_admission_form.categorical_Enums import (
    AntiDEnum, AppearanceEnum, BloodGroupEnum, BornWhereEnum, CSTypeEnum, CryEnum,
    DeliveryTypeEnum, GestationTypeEnum, JaundiceEnum, PallorEnum, RetractionSeverityEnum,
    RhesusEnum, ROMEnum, SexEnum, SkinEnum, ToneEnum, UmbilicusEnum,
)

class NARRecord(BaseModel):
    """Required NAR fields matched against ground truth.

    Type conventions
    ----------------
    bool    Y/N checkboxes (``None`` = blank / unknown, stored as ``"null"``
            in SurrealDB via ``clean_for_db`` to prevent coercion to ``false``)
    str     Coded strings and short categorical values
    int     Whole numbers
    float   Decimal numbers
    date    Calendar dates (``dd-mm-yyyy`` on the form)
    time    Clock times (24-hour)
    """

    # ------------------------------------------------------------------
    # SECTION A: Infant details

    admission_date: date = Field(description="Date of Admission")
    time_seen: time = Field(description="Time baby seen (24 hr clock)")
    sex: SexEnum = Field(description="Sex: F / M / I")

    birth_date: date = Field(description="DOB")
    time_birth: time = Field(description="Time of birth (24 hr clock)")
    gestation_in_weeks: int = Field(description="Gestation (in weeks)")
    baby_age_in_days: int = Field(description="Age (in days)")
    gestation_type: GestationTypeEnum = Field(description="Gestation age from: U/S or LMP")

    apgar_1m: int = Field(description="APGAR score at 1 minute")
    apgar_5m: int = Field(description="APGAR score at 5 minutes")
    apgar_10m: int = Field(description="APGAR score at 10 minutes")

    delivery_type: DeliveryTypeEnum = Field(
        description="Mode of Delivery: SVD / CS / Breach / Forceps / Vacuum"
    )
    had_cs: CSTypeEnum = Field(description="If CS, type: Emergency / Elective")
    was_resuscitated: bool = Field(
        description="BVM resus at birth: True=Y / False=N / None=Unknown"
    )
    rapture_of_membrane: ROMEnum = Field(description="ROM: <18h / >=18h / Unknown")

    is_multiple_delivery: bool = Field(description="Multiple delivery: Y/N")
    multiple_delivery_num: int = Field(description="If YES, number of babies")

    born_before_arrival: bool = Field(description="Born outside facility: Y/N")
    born_where: BornWhereEnum = Field(description="If yes, where: Home/roadside / Other facility")

    # ------------------------------------------------------------------
    # SECTION B: Mother's details

    mum_age_in_years: int = Field(description="Age (years)")
    parity_live: int = Field(description="Parity live births")
    parity_abortions: int = Field(description="Parity abortions/losses")
    date_estimated_delivery_date: date = Field(description="EDD")
    anc_visits: int = Field(description="ANC no. of visits")
    mum_has_anc_ultrasound: bool = Field(description="ANC U/S done: Y/N")
    blood_group: BloodGroupEnum = Field(description="Blood group: A / B / AB / O / Unknown")
    rhesus: RhesusEnum = Field(description="Rhesus: Positive / Negative / Unknown")
    given_anti_D_medication: AntiDEnum = Field(description="Anti D given: Y / N / Unknown")

    mum_had_vdrl: bool = Field(
        description="VDRL: Pos=True / Neg=False / Unknown=None"
    )
    mum_pmtct_status: bool = Field(
        description="PMTCT status: Pos=True / Neg=False / Unknown=None"
    )
    mum_on_arvs: bool = Field(
        description="Mother on ARVs: Y=True / N=False / Unknown=None"
    )
    mum_had_hepatitis_b: bool = Field(
        description="Hep B: Pos=True / Neg=False / Unknown=None"
    )
    mum_given_HBIG_treatment: bool = Field(
        description="Hep B IG given: Y=True / N=False / Unknown=None"
    )
    mum_had_hypertension_in_pregnancy: bool = Field(
        description="HTN in pregnancy: Y=True / N=False / Unknown=None"
    )
    mum_had_antepartum_haemorrhage: bool = Field(
        description="APH: Y=True / N=False / Unknown=None"
    )
    mum_had_diabetes: bool = Field(
        description="Diabetes: Y=True / N=False / Unknown=None"
    )
    prolonged_labour: bool = Field(
        description="Prolonged 2nd stage: Y=True / N=False / Unknown=None"
    )

    # ------------------------------------------------------------------
    # SECTION E: Anthropometry & Vital signs

    head_circumference: int = Field(description="Head circumference (cm)")
    length: int = Field(description="Length (cm)")
    temparature: float = Field(description="Temp (°C)")
    respiratory_rate: int = Field(description="Resp Rate (breaths/min)")
    systolic_blood_pressure: int = Field(description="Systolic BP (mmHg)")
    diastolic_blood_pressure: int = Field(description="Diastolic BP (mmHg)")
    pulse_rate: int = Field(description="Pulse (/min)")
    pulse_oximetry: int = Field(description="O₂ Sat (%)")
    birth_weight: int = Field(description="Birth Weight (grams)")
    weight: int = Field(description="Weight now (grams)")

    # Symptoms (checkboxes)
    has_fever: bool = Field(description="Fever: Y/N")
    passed_meconium: bool = Field(description="Passed meconium/stool: Y/N")
    has_difficulty_breathing: bool = Field(description="Difficulty breathing: Y/N")
    passed_urine: bool = Field(description="Passed urine in last 12 hours: Y/N")
    has_difficulty_feeding: bool = Field(description="Inability to feed: Y/N")
    has_convulsions: bool = Field(description="Convulsions / Twitching: Y/N")
    has_apnoea: bool = Field(description="Apnoea: Y/N")
    is_floppy: bool = Field(description="Reduced / Absent movement: Y/N")
    has_vomiting: bool = Field(description="Bilious Vomiting: Y/N")
    has_diarhoea: bool = Field(description="Bloody stool: Y/N")

    # ------------------------------------------------------------------
    # SECTION F1: General examination

    skin: SkinEnum = Field(
        description="Skin: Normal / Bruising / Rash / Pustules / Mottling / Dry-peeling-wrinkled"
    )
    jaundice: JaundiceEnum = Field(description="Jaundice severity: None / Mild(+) / Severe(+++)")
    appearance: AppearanceEnum = Field(description="Appearance: Well / Sick / Dysmorphic")
    cry: CryEnum = Field(description="Cry quality: Normal / Weak-Absent / Hoarse")

    has_crackles: bool = Field(description="Crackles: Y/N")
    has_grunting: bool = Field(description="Grunting: Y/N")
    has_good_air_entry: bool = Field(description="Good bilateral air entry: Y/N")
    has_central_cyanosis: bool = Field(description="Central cyanosis: Y/N")
    chest_indrawing: RetractionSeverityEnum = Field(description="Lower chest indrawing: None / Mild / Severe")
    xiphoid_retraction: RetractionSeverityEnum = Field(description="Xiphoid retraction: None / Mild / Severe")
    intercostal_retraction: RetractionSeverityEnum = Field(description="Intercostal retraction: None / Mild / Severe")
    capillary_refill_in_seconds: float = Field(description="Capillary refill (seconds)")
    pallor: PallorEnum = Field(description="Pallor/Anaemia: None / Mild(+) / Severe(+++)")
    has_murmur: bool = Field(description="Murmur: Y/N")

    has_bulging_fontanelle: bool = Field(description="Bulging fontanelle: Y/N")
    is_irritable: bool = Field(description="Irritable: Y/N")
    tone: ToneEnum = Field(description="Tone: Normal / Increased / Reduced")

    is_distended: bool = Field(description="Abdominal distension: Y/N")
    umbilicus: UmbilicusEnum = Field(
        description="Umbilicus: Clean / Local pus / Pus+Red skin / Others"
    )

    # ------------------------------------------------------------------
    # SECTION F2: Further examination

    has_birth_defects: bool = Field(description="Birth defects: Y/N")

    # ------------------------------------------------------------------
    # SECTION H: Investigations

    rbs_measured: bool = Field(description="RBS measured: Y/N")
    given_bilirubin: bool = Field(description="Bilirubin measured: Y/N")

    # ------------------------------------------------------------------
    # SECTION I: Diagnoses

    # Diagnoses are Optional in NARRecord because the GT may not always
    # include a coded diagnosis value for every record.
    primary_admission_diagnosis: Optional[str] = Field(
        None, description="Primary diagnosis (tick box '1')"
    )
    secondary_admission_diagnosis: Optional[str] = Field(
        None, description="Secondary diagnosis (tick box '2')"
    )

    # ------------------------------------------------------------------
    # SECTION J: Interventions

    given_vitamin_k: bool = Field(description="Vitamin K (& TEO) given: Y/N")
    given_bcg: bool = Field(description="BCG given: Y/N")
    given_chlorhexidine: bool = Field(description="Chlorhexidine given: Y/N")
    given_prophylaxis_pmtct: bool = Field(description="PMTCT prophylaxis given: Y/N")

    prescribed_transfusion: bool = Field(description="Transfusion prescribed: Y/N")
    prescribed_phototherapy: bool = Field(description="Phototherapy prescribed: Y/N")
    prescribed_cpap: bool = Field(description="CPAP prescribed: Y/N")
    prescribed_iv_fluids: bool = Field(description="IV fluids prescribed: Y/N")
    prescribed_antibiotics: bool = Field(description="Antibiotics prescribed: Y/N")
    prescribed_feeds: bool = Field(description="Feeds/Nutrition prescribed: Y/N")
    prescribed_opv: bool = Field(description="OPV prescribed: Y/N")
    prescribed_surfactant: bool = Field(description="Surfactant prescribed: Y/N")
    prescribed_caffeine_citrate: bool = Field(
        description="Caffeine citrate prescribed: Y/N"
    )
    prescribed_oxygen: bool = Field(description="Oxygen prescribed: Y/N")
    prescribed_kmc: bool = Field(description="KMC prescribed: Y/N")
    prescribed_incubator: bool = Field(description="Incubator/keep warm prescribed: Y/N")

    # ------------------------------------------------------------------
    # Internal / derived

    record_type: str = Field(default="NAR", description="Record type identifier")


# ---------------------------------------------------------------------------
# Batch validation wrapper (not used by the active pipeline)
# ---------------------------------------------------------------------------

class NARSchema(BaseModel):
    """Container for validating a list of NARRecord objects in batch."""

    records: List[NARRecord]