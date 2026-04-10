import pytest
from schemas.a_infant_details import InfantDetails, SexNar, AgeUnits, BabyFrom

# ----------------------------------------
# Normalization tests

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_normalize_sex_nar(input_val):
    obj = InfantDetails(
        infant_ipno_nar="123",
        doa_date_nar="2025-01-01",
        time_seen_nar="10:00",
        dob_date_nar="2025-01-01",
        time_birth_nar="09:00",
        gestation_nar="38",
        gest_type_nar="LMP",
        infant_age_itf="0",
        apgar_1m_itf="8",
        apgar_5m_itf="9",
        apgar_10m_itf="10",
        sex_nar=input_val
    )
    assert obj.sex_nar == SexNar.EMPTY

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_normalize_age_units(input_val):
    obj = InfantDetails(
        infant_ipno_nar="123",
        doa_date_nar="2025-01-01",
        time_seen_nar="10:00",
        dob_date_nar="2025-01-01",
        time_birth_nar="09:00",
        gestation_nar="38",
        gest_type_nar="LMP",
        infant_age_itf="0",
        apgar_1m_itf="8",
        apgar_5m_itf="9",
        apgar_10m_itf="10",
        age_units_itf=input_val
    )
    assert obj.age_units_itf == AgeUnits.EMPTY

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_normalize_baby_from(input_val):
    obj = InfantDetails(
        infant_ipno_nar="123",
        doa_date_nar="2025-01-01",
        time_seen_nar="10:00",
        dob_date_nar="2025-01-01",
        time_birth_nar="09:00",
        gestation_nar="38",
        gest_type_nar="LMP",
        infant_age_itf="0",
        apgar_1m_itf="8",
        apgar_5m_itf="9",
        apgar_10m_itf="10",
        baby_from_itf=input_val
    )
    assert obj.baby_from_itf == BabyFrom.EMPTY

# ----------------------------------------
# Valid inputs normalize correctly

def test_valid_age_units():
    for val, enum_val in [("days", AgeUnits.days), ("hours", AgeUnits.hours)]:
        obj = InfantDetails(
            infant_ipno_nar="123",
            doa_date_nar="2025-01-01",
            time_seen_nar="10:00",
            dob_date_nar="2025-01-01",
            time_birth_nar="09:00",
            gestation_nar="38",
            gest_type_nar="LMP",
            infant_age_itf="0",
            apgar_1m_itf="8",
            apgar_5m_itf="9",
            apgar_10m_itf="10",
            age_units_itf=val
        )
        assert obj.age_units_itf == enum_val

def test_valid_sex_nar():
    for val, enum_val in [("F", SexNar.F), ("M", SexNar.M), ("I", SexNar.I)]:
        obj = InfantDetails(
            infant_ipno_nar="123",
            doa_date_nar="2025-01-01",
            time_seen_nar="10:00",
            dob_date_nar="2025-01-01",
            time_birth_nar="09:00",
            gestation_nar="38",
            gest_type_nar="LMP",
            infant_age_itf="0",
            apgar_1m_itf="8",
            apgar_5m_itf="9",
            apgar_10m_itf="10",
            sex_nar=val
        )
        assert obj.sex_nar == enum_val

# ----------------------------------------
# Serialization tests (REDcap)

def test_serialize_empty_enum():
    obj = InfantDetails(
        infant_ipno_nar="123",
        doa_date_nar="2025-01-01",
        time_seen_nar="10:00",
        dob_date_nar="2025-01-01",
        time_birth_nar="09:00",
        gestation_nar="38",
        gest_type_nar="LMP",
        infant_age_itf="0",
        apgar_1m_itf="8",
        apgar_5m_itf="9",
        apgar_10m_itf="10",
        sex_nar=None,
        age_units_itf=None,
        baby_from_itf=None
    )
    data = obj.model_dump()
    assert data["sex_nar"] == -1
    assert data["age_units_itf"] == -1
    assert data["baby_from_itf"] == -1

def test_serialize_valid_enum():
    obj = InfantDetails(
        infant_ipno_nar="123",
        doa_date_nar="2025-01-01",
        time_seen_nar="10:00",
        dob_date_nar="2025-01-01",
        time_birth_nar="09:00",
        gestation_nar="38",
        gest_type_nar="LMP",
        infant_age_itf="0",
        apgar_1m_itf="8",
        apgar_5m_itf="9",
        apgar_10m_itf="10",
        sex_nar="F",
        age_units_itf="days",
        baby_from_itf="Labour"
    )
    data = obj.model_dump()
    assert data["sex_nar"] == "F"
    assert data["age_units_itf"] == "days"
    assert data["baby_from_itf"] == "Labour"
