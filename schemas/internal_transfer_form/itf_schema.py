from typing import  List
from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator


class ITFRecord(BaseModel):
    """
    Internal Transfer Form (ITF) newborn + maternal + labour record
    """

    _id: str

    # =========================
    # MOTHER'S DETAILS
    # =========================
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
    mum_treated_for_tb: bool = Field(description="Treated for TB: True = Y, False = N, None = Unknown")
    mum_had_vdrl: bool = Field(description="VDRL: True = Pos, False = Neg, None = Unknown")
    mum_had_diabetes: bool = Field(description="Diabetes: True = Y, False = N, None = Unknown")
    mum_pmtct_status: bool = Field(description="PMTCT status: True = Pos, False = Neg, None = Unknown")
    mum_on_arvs: bool = Field(description="Mother on ARVs: True = Y, False = N, None = Unknown")
    mum_had_antepartum_haemorrhage: bool = Field(description="APH: True = Y, False = N, None = Unknown")
    prescribed_antibiotics: bool = Field(description="Antibiotics")
    multiple_pregnancy: bool = Field(description="Multiple PG")
    mum_had_hypertension_in_pregnancy: bool = Field(description="HTN in pregnancy: True = Y, False = N, None = Unknown")
    mum_had_pre_eclampsia: bool = Field(description="Pre-eclampsia")
    mum_had_eclampsia: bool = Field(description="Maternal eclampsia")


    # =========================
    # LABOUR & BIRTH
    # =========================

    rapture_of_membrane: str = Field(description="ROM (<18h, >=18h, unknown)")
    fetal_distress: bool = Field(description="Fetal distress")
    passed_meconium: bool= Field(description="Meconium")
    #meconium_present: bool = Field(description="Meconium")
    #meconium_grade: int= Field(description="If yes, grade")
    antenatal_steroids: bool = Field(description="Antenatal steroids")

    delivery_type: str = Field(description="Delivery")
    had_cs: str = Field(description="If CS, type")
    #cs_reason: str = Field(description="Reason for emergency CS")

    placenta_complete: bool = Field(description="Placenta Complete")
    abnormal_placenta: bool = Field(description="Abnormal placenta")
    was_resuscitated: bool = Field(description="BVM resuscitation")
    chest_compressions: bool = Field(description="Chest compressions?")

    given_vitamin_k: bool = Field(description="Vitamin K")
    given_teo: bool = Field(description="TEO")
    prescribed_opv: bool = Field(description="OPV")
    given_bcg: bool = Field(description="BCG")
    mum_had_hep_b: bool = Field(description="Hep B")
    prescribed_cpap: bool = Field(description="CPAP")
    prescribed_oxygen: bool = Field(description="Oxygen prescribed")
    given_chlorhexidine: bool = Field(description="Chlorhexidine applied")
    maternal_status: str = Field(description="Maternal Status")
    #oxygen_given: bool = Field(description="Whether oxygen was administered at birth")

    # =========================
    # INFANT DETAILS
    # =========================

    birth_date: date = Field(description="Date of birth")
    sex: str = Field(description="Sex of the newborn (male/female)")
    baby_age: int = Field(description="Age")
    birth_weight: int = Field(description="Birth weight (grams)")
    weight: int = Field(description="Weight now (grams)")
    pulse_oximetry: int= Field(description="O₂ Sat")
    pulse_rate: int = Field(description="Pulse rate")
    temperature: float = Field(description="Temp")
    respiratory_rate: int = Field(description="Resp rate")
    apgar_1m: int = Field(description="APGAR score at 1 minute")
    apgar_5m: int = Field(description="APGAR score at 5 minutes")
    apgar_10m: int = Field(description="APGAR score at 10 minutes")
    baby_from: str = Field(description="Baby from?")


    hospital: str = Field(description="Hospital identifier")
    record_type: str = Field(default="ITF", description="Record type (ITF)")


class ITFSchema(BaseModel):
    records: List[ITFRecord]

