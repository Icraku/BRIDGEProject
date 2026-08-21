"""
schemas/neonatal_admission_form/narP1_schema.py
=======================================================
``NAR_P1Record`` — the 98 required fields for page 1 used for ground-truth evaluation.
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.neonatal_admission_form.categorical_Enums import (
    ANCTrimesterEnum, AppearanceEnum, BloodGroupEnum, #AntiDEnum,
    BornWhereEnum, CSTypeEnum, CryEnum, DeliveryTypeEnum,
    GestationTypeEnum, JaundiceEnum, PallorEnum, RetractionSeverityEnum,
    RhesusEnum, ROMEnum, SexEnum, YesNoEnum, YesNoUnknownEnum, PositiveNegativeUnknownEnum,
    SkinEnum, ToneEnum, UmbilicusEnum, BirthDefectsEnum,

)

class NAR_P1Record(BaseModel):
    """Required NAR fields matched against ground truth.

    Type conventions
    ----------------
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
    sex: str = Field(description="Sex: F / M / I")

    birth_date: date = Field(description="DOB")
    time_birth: time = Field(description="Time of birth (24 hr clock)")
    gestation_in_weeks: int = Field(description="Gestation (in weeks)")
    baby_age_in_days: int = Field(description="Age (in days)")
    gestation_type: str = Field(description="Gestation age from: U/S or LMP")

    apgar_1m: int = Field(description="APGAR score at 1 minute")
    apgar_5m: int = Field(description="APGAR score at 5 minutes")
    apgar_10m: int = Field(description="APGAR score at 10 minutes")

    delivery_type: str = Field(
        description="Delivery: SVD / CS / Breach / Forceps / Vacuum"
    )
    had_cs: str = Field(description="If CS, type: Emergency / Elective")
    was_resuscitated: YesNoEnum  = Field(
        description="BVM resus at birth: True=Y / False=N / None=Unknown"
    )
    rapture_of_membrane: str = Field(description="ROM: <18h / >=18h / Unknown")

    is_multiple_delivery: YesNoEnum  = Field(description="Multiple delivery: Y/N")
    multiple_delivery_num: int = Field(description="If YES, number of babies")

    born_before_arrival: YesNoEnum  = Field(description="Born outside facility: Y/N")
    born_where: str = Field(description="If yes, where: Home/roadside / Other facility")

    # ------------------------------------------------------------------
    # SECTION B: Mother's details

    mum_age_in_years: int = Field(description="Age (years)")
    parity_live: int = Field(description="Parity live births")
    parity_abortions: int = Field(description="Parity abortions/losses")
    date_estimated_delivery_date: date = Field(description="EDD")
    anc_visits: int = Field(description="ANC no. of visits")
    mum_has_anc_ultrasound: YesNoEnum  = Field(description="ANC U/S done: Y/N")
    blood_group: str = Field(description="Blood group: A / B / AB / O / Unknown")
    rhesus: str = Field(description="Rhesus: Pos / Neg / Unknown")
    given_anti_D_medication: str = Field(description="Anti D given: Y / N")

    mum_had_vdrl: YesNoEnum  = Field(
        description="VDRL: Pos=True / Neg=False / Unknown=None"
    )
    mum_pmtct_status: YesNoEnum  = Field(
        description="PMTCT status: Pos=True / Neg=False / Unknown=None"
    )
    mum_on_arvs: YesNoEnum  = Field(
        description="Mother on ARVs: Y=True / N=False / Unknown=None"
    )
    mum_had_hepatitis_b: YesNoEnum  = Field(
        description="Hep B: Pos=True / Neg=False / Unknown=None"
    )
    mum_given_HBIG_treatment: YesNoEnum  = Field(
        description="Hep B IG given: Y=True / N=False / Unknown=None"
    )
    mum_had_hypertension_in_pregnancy: YesNoEnum  = Field(
        description="HTN in pregnancy: Y=True / N=False / Unknown=None"
    )
    mum_had_antepartum_haemorrhage: YesNoEnum  = Field(
        description="APH: Y=True / N=False / Unknown=None"
    )
    mum_had_diabetes: YesNoEnum  = Field(
        description="Diabetes: Y=True / N=False / Unknown=None"
    )
    prolonged_labour: YesNoEnum  = Field(
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
    has_fever: YesNoEnum  = Field(description="Fever: Y/N")
    passed_meconium: YesNoEnum  = Field(description="Passed meconium/stool: Y/N")
    has_difficulty_breathing: YesNoEnum  = Field(description="Difficulty breathing: Y/N")
    passed_urine: YesNoEnum  = Field(description="Passed urine in last 12 hours: Y/N")
    has_difficulty_feeding: YesNoEnum  = Field(description="Inability to feed: Y/N")
    has_convulsions: YesNoEnum  = Field(description="Convulsions / Twitching: Y/N")
    has_apnoea: YesNoEnum  = Field(description="Apnoea: Y/N")
    is_floppy: YesNoEnum  = Field(description="Reduced / Absent movement: Y/N")
    has_vomiting: YesNoEnum  = Field(description="Bilious Vomiting: Y/N")
    has_diarhoea: YesNoEnum  = Field(description="Bloody stool: Y/N")


class NARSchema(BaseModel):
    records: List[NAR_P1Record]