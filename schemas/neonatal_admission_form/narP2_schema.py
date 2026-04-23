import datetime
import time
from typing import Optional, List
from datetime import date, datetime, time

from pydantic import BaseModel, Field, field_validator


class NAR_P2Record(BaseModel):
    """
    Y/N - bool
    words - str
    numbers - int
    dates - date
    """
    _id: str

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
    records: List[NAR_P2Record]