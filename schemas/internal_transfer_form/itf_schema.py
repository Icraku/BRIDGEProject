"""
schemas/internal_transfer_form/itf_schema.py
=============================================
``ITFRecord`` — structured schema for the Internal Transfer Form (ITF).

The ITF captures maternal, labour, and neonatal details at the point of
intra-facility transfer.  It is structurally similar to the NAR but covers
the birth episode rather than the admission assessment.

.. note::
    The ITF pipeline is not yet active.  This schema is provided for
    completeness and future extension.  When ITF extraction is enabled,
    ``ITFRecord`` will be used the same way ``NARFullRecord`` is used in the
    NAR pipeline — as the structured-output target for the LLM.
"""

from __future__ import annotations

from datetime import date, time
from typing import List

from pydantic import BaseModel, Field


class ITFRecord(BaseModel):
    """Structured fields for the Internal Transfer Form.

    Type conventions match ``NARRecord``: bool = Y/N checkbox,
    str = coded string, int = whole number, float = decimal, date/time as typed.
    """

    # ------------------------------------------------------------------
    # Mother's details

    mum_age_in_years: int = Field(description="Age (in years)")
    parity_live: int = Field(description="Parity live")
    parity_abortions: int = Field(description="Parity abortions")
    gravida: int = Field(description="Gravida")
    gestation_in_weeks: int = Field(description="Gestation (in weeks)")

    attended_anc: bool = Field(description="Attended ANC?")
    anc_visits: int = Field(description="ANC no. of visits")
    mum_has_anc_ultrasound: bool = Field(description="ANC U/S")

    date_estimated_delivery_date: date = Field(description="EDD")
    date_last_menstrual_period: date = Field(description="LMP")

    blood_group: str = Field(description="Blood group")
    rhesus: str = Field(description="Rhesus")

    has_fever: bool = Field(description="Fever")
    mum_treated_for_tb: bool = Field(
        description="Treated for TB: True=Y / False=N / None=Unknown"
    )
    mum_had_vdrl: bool = Field(
        description="VDRL: Pos=True / Neg=False / Unknown=None"
    )
    mum_had_diabetes: bool = Field(
        description="Diabetes: True=Y / False=N / None=Unknown"
    )
    mum_pmtct_status: bool = Field(
        description="PMTCT status: Pos=True / Neg=False / Unknown=None"
    )
    mum_on_arvs: bool = Field(
        description="Mother on ARVs: True=Y / False=N / None=Unknown"
    )
    mum_had_antepartum_haemorrhage: bool = Field(
        description="APH: True=Y / False=N / None=Unknown"
    )
    prescribed_antibiotics: bool = Field(description="Antibiotics prescribed")
    multiple_pregnancy: bool = Field(description="Multiple pregnancy")
    mum_had_hypertension_in_pregnancy: bool = Field(
        description="HTN in pregnancy: True=Y / False=N / None=Unknown"
    )
    mum_had_pre_eclampsia: bool = Field(description="Pre-eclampsia")
    mum_had_eclampsia: bool = Field(description="Maternal eclampsia")

    # ------------------------------------------------------------------
    # Labour & birth

    rapture_of_membrane: str = Field(description="ROM: <18h / >=18h / Unknown")
    fetal_distress: bool = Field(description="Fetal distress")
    passed_meconium: bool = Field(description="Meconium present")
    antenatal_steroids: bool = Field(description="Antenatal steroids given")

    delivery_type: str = Field(description="Delivery: SVD / CS / Breach / etc.")
    had_cs: str = Field(description="If CS, type: Emergency / Elective")

    placenta_complete: bool = Field(description="Placenta complete")
    abnormal_placenta: bool = Field(description="Abnormal placenta")
    was_resuscitated: bool = Field(description="BVM resuscitation at birth")
    chest_compressions: bool = Field(description="Chest compressions performed")

    given_vitamin_k: bool = Field(description="Vitamin K given")
    given_teo: bool = Field(description="TEO given")
    prescribed_opv: bool = Field(description="OPV prescribed")
    given_bcg: bool = Field(description="BCG given")
    mum_had_hep_b: bool = Field(description="Hep B")
    prescribed_cpap: bool = Field(description="CPAP prescribed")
    prescribed_oxygen: bool = Field(description="Oxygen prescribed")
    given_chlorhexidine: bool = Field(description="Chlorhexidine applied")
    maternal_status: str = Field(description="Maternal status at transfer")

    # ------------------------------------------------------------------
    # Infant details

    birth_date: date = Field(description="Date of birth")
    sex: str = Field(description="Sex of the newborn: M / F")
    baby_age: int = Field(description="Age (in days)")
    birth_weight: int = Field(description="Birth weight (grams)")
    weight: int = Field(description="Weight now (grams)")
    pulse_oximetry: int = Field(description="O₂ Sat (%)")
    pulse_rate: int = Field(description="Pulse rate (/min)")
    temperature: float = Field(description="Temp (°C)")
    respiratory_rate: int = Field(description="Resp rate (breaths/min)")
    apgar_1m: int = Field(description="APGAR score at 1 minute")
    apgar_5m: int = Field(description="APGAR score at 5 minutes")
    apgar_10m: int = Field(description="APGAR score at 10 minutes")
    baby_from: str = Field(description="Baby transferred from")

    # ------------------------------------------------------------------
    # Internal / derived

    hospital: str = Field(description="Hospital identifier")
    record_type: str = Field(default="ITF", description="Record type identifier")


# ---------------------------------------------------------------------------
# Batch validation wrapper
# ---------------------------------------------------------------------------

class ITFSchema(BaseModel):
    """Container for validating a list of ITFRecord objects in batch."""

    records: List[ITFRecord]