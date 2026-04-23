from typing import Optional, List
from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator


class NARRecord(BaseModel):
    """
    Y/N - bool
    words - str
    numbers - int
    dates - date
    """
    _id: str

    anc_visits: int= Field(description="ANC no. of visits")
    apgar_10m: int= Field(description="APGAR score at 10 minutes")
    apgar_1m: int= Field(description="APGAR score at 1 minute")
    apgar_5m:  int= Field(description="APGAR score at 5 minutes")
    baby_age_in_days:  int= Field(description="Age (in days)")
    birth_date:  date= Field(description="DOB")
    birth_weight: int= Field(description="Birth Weight (grams)")
    blood_group: str= Field(description="Blood group")

    born_before_arrival: bool= Field(description="Born outside facility?")
    born_where: str= Field(description="If yes, where?")
    admission_date: date= Field(description="DOB")
    date_estimated_delivery_date: date= Field(description="EDD")
    delivery_type: str= Field(description="Delivery")

    diastolic_blood_pressure: int= Field(description="Diastolic Blood pressure")
    gestation_in_weeks: int= Field(description="Gestation (in weeks)")
    gestation_type: str= Field(description="Gestation age from?")
    given_anti_D_medication: str= Field(description="Anti D") ############## check if str returns null and change for mothers section
    had_cs: str= Field(description="If yes, type")

    has_apnoea: bool= Field(description="Apnoea")
    has_convulsions:  bool= Field(description="Convulsions / Twitching")
    has_diarhoea:  bool= Field(description="Bloody stool")
    has_difficulty_breathing:  bool= Field(description="Difficulty breathing")
    has_difficulty_feeding:  bool= Field(description="Inability to feed")
    has_fever:  bool= Field(description="Fever")
    has_vomiting: bool= Field(description="Bilious Vomiting")

    head_circumference: int= Field(description="Head circumference (cm)")
    #hospital: str= None#??? will come from the record name/record id #####################################
    is_floppy: bool= Field(description="Reduced / Absent movement")
    is_multiple_delivery: bool= Field(description="Multiple delivery")
    length: int= Field(description="Length (cm)")
    multiple_delivery_num: int= Field(description="If YES, number")

    mum_age_in_years: int= Field(description="Age (years)")
    mum_given_HBIG_treatment: bool= Field(description="Hep B IG given: True = Y, False = N, None = Unknown")
    mum_had_antepartum_haemorrhage: bool= Field(description="APH: True = Y, False = N, None = Unknown")
    mum_had_diabetes: bool= Field(description="Diabetes: True = Y, False = N, None = Unknown")
    mum_had_hepatitis_b: bool= Field(description="Hep B: True = Pos, False = Neg, None = Unknown")
    mum_had_hypertension_in_pregnancy: bool= Field(description="HTN in pregnancy?: True = Y, False = N, None = Unknown")
    mum_had_vdrl: bool= Field(description="VDRL: True = Pos, False = Neg, None = Unknown")
    mum_has_anc_ultrasound: bool= Field(description="ANC U/S")
    mum_on_arvs: bool= Field(description="Mother on ARVs: True = Y, False = N, None = Unknown")
    mum_pmtct_status: bool= Field(description="PMTCT status: True = Pos, False = Neg, None = Unknown")

    parity_abortions: int=Field(description="Parity abortions")
    parity_live: int=Field(description="Parity live")
    passed_meconium: bool= Field(description="Passed meconium/stool")
    passed_urine: bool= Field(description="Passed urine in the last 12 hours")

    #primary_admission_diagnosis: str= None#number/strD ################################
    prolonged_labour: bool= Field(description="Diabetes")
    pulse_oximetry: int= Field(description="O₂ Sat")
    pulse_rate: int= Field(description="Pulse")
    rapture_of_membrane: str= Field(description="ROM")

    record_type: str= "NAR" ################################33333333333
    respiratory_rate: int= Field(description="Resp Rate")
    rhesus: str= Field(description="Rhesus")
    #secondary_admission_diagnosis: str= None#number/strD
    sex: str= Field(description="Sex")

    systolic_blood_pressure: int= Field(description="Systolic Blood Pressure")
    temparature: float= Field(description="Temp")
    time_birth: time= Field(description="Time of birth (24 hr clock)")
    time_seen: time= Field(description="Time baby seen (24 hr clock)")
    was_resuscitated: bool= Field(description="BVM resus at birth: True = Y, False = N, None = Unknown")
    weight: int= Field(description="Weight now (grams)")

    # ----- PAGE 2 -----

    # General examination
    skin: str= Field(description="Skin")
    jaundice: str= Field(description="Jaundice")
    appearance: str= Field(description="Appearance")
    cry: str= Field(description="Cry")

    # A & B
    has_crackles: bool= Field(description="Crackles")
    has_grunting: bool= Field(description="Grunting")
    has_good_air_entry: bool= Field(description="Good bilateral air entry")
    has_central_cyanosis: bool= Field(description="Central cyanosis")
    chest_indrawing: bool= Field(description="Lower chest indrawing")
    xiphoid_retraction: str= Field(description="Xiphoid retraction: none/mild/severe")
    intercostal_retraction: str= Field(description="Intercostal retraction: none/mild/severe")

    # C
    capillary_refill_in_seconds: float= Field(description="Capillary refill (seconds)")
    pallor: str= Field(description="Pallor/Anaemia")
    has_murmur: bool= Field(description="Murmur")

    # D
    has_bulging_fontanelle: bool= Field(description="Bulging fontanelle")
    is_irritable: bool= Field(description="Irritable")
    tone: str= Field(description="Tone")

    # Abdomen
    is_distended: bool= Field(description="Abdominal distension")
    umbilicus: str= Field(description="Umbilicus")

    # F2
    has_birth_defects: bool= Field(description="Birth defects")

    # Investigations
    rbs_measured: bool= Field(description="RBS measured")
    given_bilirubin: bool= Field(description="Bilirubin measured")

    # Diagnoses
    primary_admission_diagnosis: str= Field(description="Primary diagnosis")
    secondary_admission_diagnosis: str= Field(description="Secondary diagnosis")

    # Interventions (given)
    given_vitamin_k: bool= Field(description="Vitamin K given")
    given_bcg: bool= Field(description="BCG given")
    given_chlorhexidine: bool= Field(description="Chlorhexidine given")
    given_prophylaxis_pmtct: bool= Field(description="PMTCT prophylaxis given")

    # Interventions (prescribed)
    prescribed_transfusion: bool= Field(description="Transfusion prescribed")
    prescribed_phototherapy: bool= Field(description="Phototherapy prescribed")
    prescribed_cpap: bool= Field(description="CPAP prescribed")
    prescribed_iv_fluids: bool= Field(description="IV fluids prescribed")
    prescribed_antibiotics: bool= Field(description="Antibiotics prescribed")
    prescribed_feeds: bool= Field(description="Feeds prescribed")
    prescribed_opv: bool= Field(description="OPV prescribed")
    prescribed_surfactant: bool= Field(description="Surfactant prescribed")
    prescribed_caffeine_citrate: bool= Field(description="Caffeine citrate prescribed")
    prescribed_oxygen: bool= Field(description="Oxygen prescribed")
    prescribed_kmc: bool= Field(description="KMC prescribed")
    prescribed_incubator: bool= Field(description="Incubator/keep warm")



class NARSchema(BaseModel):
    records: List[NARRecord]