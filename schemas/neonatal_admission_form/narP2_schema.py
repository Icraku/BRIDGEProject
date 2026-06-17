"""
schemas/neonatal_admission_form/narP1_schema.py
=======================================================
``NAR_P1Record`` — the 98 required fields for page 2 used for ground-truth evaluation.
"""

from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field


class NAR_P2Record(BaseModel):
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
    # SECTION F1: General examination

    skin: str = Field(
        description=(
            "Skin: Normal / Bruising / Rash / Pustules / Mottling / Dry-peeling-wrinkled"
        )
    )
    jaundice: str = Field(description="Jaundice: None / + / +++")
    appearance: str = Field(description="Appearance: Well / Sick / Dysmorphic")
    cry: str = Field(description="Cry: Normal / Weak-Absent / Hoarse")

    has_crackles: bool = Field(description="Crackles: Y/N")
    has_grunting: bool = Field(description="Grunting: Y/N")
    has_good_air_entry: bool = Field(description="Good bilateral air entry: Y/N")
    has_central_cyanosis: bool = Field(description="Central cyanosis: Y/N")
    chest_indrawing: bool = Field(description="Lower chest indrawing: Y/N")
    xiphoid_retraction: str = Field(
        description="Xiphoid retraction: None / Mild / Severe"
    )
    intercostal_retraction: str = Field(
        description="Intercostal retraction: None / Mild / Severe"
    )
    capillary_refill_in_seconds: float = Field(description="Capillary refill (seconds)")
    pallor: str = Field(description="Pallor/Anaemia: None / + / +++")
    has_murmur: bool = Field(description="Murmur: Y/N")

    has_bulging_fontanelle: bool = Field(description="Bulging fontanelle: Y/N")
    is_irritable: bool = Field(description="Irritable: Y/N")
    tone: str = Field(description="Tone: Normal / Increased / Reduced")

    is_distended: bool = Field(description="Abdominal distension: Y/N")
    umbilicus: str = Field(
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

class NARSchema(BaseModel):
    records: List[NAR_P2Record]