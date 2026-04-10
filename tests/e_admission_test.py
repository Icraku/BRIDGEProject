from enum import Enum

import pytest
from schemas.e_newborn_admission import (
    NewbornAdmission,
    SkinNar,
    AppearanceNar,
    JaundiceNar,
    PallorNar,
    CryNar,
    XiphoidNar,
    IntercostalNar,
    BulgingFontanelleNar,
    IrritableNar,
    ToneNar,
    UmbilicusNar,
    BirthDefectsNar,
    SelectedEnum,
    SpecificBirthDefects,
)

EMPTY_VALUES = [None, "", -1, "-1"]

def sample_newborn_data(overrides=None):
    data = dict(
        temp_nar="36.5",
        resp_rate_nar="40",
        pulse_rate_nar="120",
        oximetry_nar="98",
        birth_weight_nar="3.0",
        weight_now_nar="2.9",
        head_circ_nar="34",
        length_nar="50",
        blood_pressure_nar="80/50",
        skin_nar=None,
        appearance_nar=None,
        jaundice_nar=None,
        pallor_nar=None,
        cry_nar=None,
        xiphoid_nar=None,
        intercostal_nar=None,
        cap_refill_nar="2",
        bulging_fontanelle_nar=None,
        irritable_nar=None,
        tone_nar=None,
        umbilicus_nar=None,
        birth_defects_nar=None,
        specific_defects=None
    )
    if overrides:
        data.update(overrides)
    return data

@pytest.mark.parametrize("val", EMPTY_VALUES)
def test_empty_normalization(val):
    obj = NewbornAdmission(**sample_newborn_data({
        "skin_nar": val,
        "appearance_nar": val,
        "jaundice_nar": val,
        "pallor_nar": val,
        "cry_nar": val,
        "xiphoid_nar": val,
        "intercostal_nar": val,
        "bulging_fontanelle_nar": val,
        "irritable_nar": val,
        "tone_nar": val,
        "umbilicus_nar": val,
        "birth_defects_nar": val,
    }))

    assert obj.skin_nar == SkinNar.EMPTY
    assert obj.appearance_nar == AppearanceNar.EMPTY
    assert obj.jaundice_nar == JaundiceNar.EMPTY
    assert obj.pallor_nar == PallorNar.EMPTY
    assert obj.cry_nar == CryNar.EMPTY
    assert obj.xiphoid_nar == XiphoidNar.EMPTY
    assert obj.intercostal_nar == IntercostalNar.EMPTY
    assert obj.bulging_fontanelle_nar == BulgingFontanelleNar.EMPTY
    assert obj.irritable_nar == IrritableNar.EMPTY
    assert obj.tone_nar == ToneNar.EMPTY
    assert obj.umbilicus_nar == UmbilicusNar.EMPTY
    assert obj.birth_defects_nar == BirthDefectsNar.EMPTY

def test_serialization_empty():
    obj = NewbornAdmission(**sample_newborn_data())
    data = obj.model_dump()
    for field, value in data.items():
        if isinstance(value, Enum):
            assert value.value != "-1" or data[field] == -1  # serialized correctly

def test_valid_values():
    specific_defects = SpecificBirthDefects(
        birth_defect_gi_nar=SelectedEnum.Selected,
        birth_defect_tube_nar=SelectedEnum.Selected,
    )
    obj = NewbornAdmission(**sample_newborn_data({
        "skin_nar": "Normal",
        "appearance_nar": "Well",
        "jaundice_nar": "None",
        "pallor_nar": "None",
        "cry_nar": "Normal",
        "xiphoid_nar": "Mild",
        "intercostal_nar": "Severe",
        "bulging_fontanelle_nar": "Yes",
        "irritable_nar": "No",
        "tone_nar": "Normal",
        "umbilicus_nar": "Clean",
        "birth_defects_nar": "Yes",
        "specific_defects": specific_defects
    }))

    assert obj.skin_nar == SkinNar.Normal
    assert obj.appearance_nar == AppearanceNar.Well
    assert obj.jaundice_nar == JaundiceNar.None_
    assert obj.pallor_nar == PallorNar.None_
    assert obj.cry_nar == CryNar.Normal
    assert obj.xiphoid_nar == XiphoidNar.Mild
    assert obj.intercostal_nar == IntercostalNar.Severe
    assert obj.bulging_fontanelle_nar == BulgingFontanelleNar.Yes
    assert obj.irritable_nar == IrritableNar.No
    assert obj.tone_nar == ToneNar.Normal
    assert obj.umbilicus_nar == UmbilicusNar.Clean
    assert obj.birth_defects_nar == BirthDefectsNar.Yes
    assert obj.specific_defects.birth_defect_gi_nar == SelectedEnum.Selected
    assert obj.specific_defects.birth_defect_tube_nar == SelectedEnum.Selected
