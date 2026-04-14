import pytest
from schemas.e_newborn_admission import NewbornAdmission, SpecificBirthDefects
from schemas.e_newborn_admission import SkinNar, AppearanceNar, JaundiceNar, PallorNar, CryNar
from schemas.e_newborn_admission import XiphoidNar, IntercostalNar, BulgingFontanelleNar, IrritableNar
from schemas.e_newborn_admission import ToneNar, UmbilicusNar, BirthDefectsNar, SelectedEnum, BirthDefectLimbNar


def test_normalization_empty():
    # Fields set to None, -1, "EMPTY" should become Enum.EMPTY
    data = {
        "temp_nar": "36.5",
        "resp_rate_nar": "40",
        "pulse_rate_nar": "120",
        "oximetry_nar": "95",
        "birth_weight_nar": "3.0",
        "weight_now_nar": "3.1",
        "head_circ_nar": "34",
        "length_nar": "50",
        "blood_pressure_nar": "70/40",
        "cap_refill_nar": "2",
        "birth_defects_nar": None,
        "skin_nar": "EMPTY",
        "appearance_nar": None,
        "jaundice_nar": -1,
        "pallor_nar": None,
        "cry_nar": "EMPTY",
        "xiphoid_nar": None,
        "intercostal_nar": "EMPTY",
        "bulging_fontanelle_nar": None,
        "irritable_nar": None,
        "tone_nar": None,
        "umbilicus_nar": None,
        "specific_defects": None
    }

    newborn = NewbornAdmission(**data)

    assert newborn.skin_nar == SkinNar.EMPTY
    assert newborn.appearance_nar == AppearanceNar.EMPTY
    assert newborn.jaundice_nar == JaundiceNar.EMPTY
    assert newborn.pallor_nar == PallorNar.EMPTY
    assert newborn.cry_nar == CryNar.EMPTY
    assert newborn.xiphoid_nar == XiphoidNar.EMPTY
    assert newborn.intercostal_nar == IntercostalNar.EMPTY
    assert newborn.bulging_fontanelle_nar == BulgingFontanelleNar.EMPTY
    assert newborn.irritable_nar == IrritableNar.EMPTY
    assert newborn.tone_nar == ToneNar.EMPTY
    assert newborn.umbilicus_nar == UmbilicusNar.EMPTY
    assert newborn.birth_defects_nar == BirthDefectsNar.EMPTY


def test_normalization_valid_values():
    data = {
        "temp_nar": "36.5",
        "resp_rate_nar": "40",
        "pulse_rate_nar": "120",
        "oximetry_nar": "95",
        "birth_weight_nar": "3.0",
        "weight_now_nar": "3.1",
        "head_circ_nar": "34",
        "length_nar": "50",
        "blood_pressure_nar": "70/40",
        "cap_refill_nar": "2",
        "birth_defects_nar": "Yes",
        "skin_nar": "Bruising",
        "appearance_nar": "Sick",
        "jaundice_nar": "+",
        "pallor_nar": "+",
        "cry_nar": "Weak/Absent",
        "xiphoid_nar": "Mild",
        "intercostal_nar": "Severe",
        "bulging_fontanelle_nar": "Yes",
        "irritable_nar": "No",
        "tone_nar": "Decreased",
        "umbilicus_nar": "Pus + Red Skin", #------- fails if the value is Pus ------
        "specific_defects": {
            "birth_defect_limb_nar": "Selected", #--------fails if the value is Yes -------
            "birth_defect_gi_nar": "Selected"
        }
    }

    newborn = NewbornAdmission(**data)
    assert newborn.skin_nar == SkinNar.Bruising
    assert newborn.appearance_nar == AppearanceNar.Sick
    assert newborn.jaundice_nar == JaundiceNar.Mild
    assert newborn.pallor_nar == PallorNar.Mild
    assert newborn.cry_nar == CryNar.Weak
    assert newborn.xiphoid_nar == XiphoidNar.Mild
    assert newborn.intercostal_nar == IntercostalNar.Severe
    assert newborn.bulging_fontanelle_nar == BulgingFontanelleNar.Yes
    assert newborn.irritable_nar == IrritableNar.No
    assert newborn.tone_nar == ToneNar.Decreased
    assert newborn.umbilicus_nar == UmbilicusNar.Pus
    assert newborn.birth_defects_nar == BirthDefectsNar.Yes
    assert newborn.specific_defects.birth_defect_limb_nar == BirthDefectLimbNar.Yes
    assert newborn.specific_defects.birth_defect_gi_nar == SelectedEnum.Selected


def test_serialization():
    data = {
        "temp_nar": "36.5",
        "resp_rate_nar": "40",
        "pulse_rate_nar": "120",
        "oximetry_nar": "95",
        "birth_weight_nar": "3.0",
        "weight_now_nar": "3.1",
        "head_circ_nar": "34",
        "length_nar": "50",
        "blood_pressure_nar": "70/40",
        "cap_refill_nar": "2",
        "birth_defects_nar": "EMPTY",
        "skin_nar": "EMPTY",
        "appearance_nar": "EMPTY",
        "jaundice_nar": "EMPTY",
        "pallor_nar": "EMPTY",
        "cry_nar": "EMPTY",
        "xiphoid_nar": "EMPTY",
        "intercostal_nar": "EMPTY",
        "bulging_fontanelle_nar": "EMPTY",
        "irritable_nar": "EMPTY",
        "tone_nar": "EMPTY",
        "umbilicus_nar": "EMPTY",
        "specific_defects": None
    }

    newborn = NewbornAdmission(**data)
    serialized = newborn.model_dump()

    # EMPTY Enums should serialize to -1
    assert serialized["skin_nar"] == -1
    assert serialized["appearance_nar"] == -1
    assert serialized["jaundice_nar"] == -1
    assert serialized["pallor_nar"] == -1
    assert serialized["cry_nar"] == -1
    assert serialized["xiphoid_nar"] == -1
    assert serialized["intercostal_nar"] == -1
    assert serialized["bulging_fontanelle_nar"] == -1
    assert serialized["irritable_nar"] == -1
    assert serialized["tone_nar"] == -1
    assert serialized["umbilicus_nar"] == -1
    assert serialized["birth_defects_nar"] == -1
