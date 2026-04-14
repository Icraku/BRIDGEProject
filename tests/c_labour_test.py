import pytest
from schemas.c_labour_and_birth import (
    LabourAndBirth,
    DeliveryItf,
    CsTypeItf,
    YesNoEnum,
    MaternalStatusItf,
)

# --------------------------------------------------------
# Helper: Check EMPTY normalization

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_empty_normalization_yes_no(input_val):
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        meconium_itf=input_val,
    )
    assert obj.meconium_itf == YesNoEnum.EMPTY


@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_empty_normalization_delivery(input_val):
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        delivery_itf=input_val,
    )
    assert obj.delivery_itf == DeliveryItf.EMPTY


@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_empty_normalization_maternal(input_val):
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        maternal_status_itf=input_val,
    )
    assert obj.maternal_status_itf == MaternalStatusItf.EMPTY


# --------------------------------------------------------
# Valid Input → Correct Enum

def test_valid_yes_normalizes():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        cpap_itf="Yes",
    )
    assert obj.cpap_itf == YesNoEnum.Yes


def test_valid_delivery_normalizes():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        delivery_itf="SVD",
    )
    assert obj.delivery_itf == DeliveryItf.SVD


def test_valid_cs_type_normalizes():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        cs_type_itf="Emergency",
    )
    assert obj.cs_type_itf == CsTypeItf.Emergency


# --------------------------------------------------------
# Serialization tests

def test_serialize_empty_yes_no():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        oxygen_itf=None,
    )
    data = obj.model_dump()
    assert data["oxygen_itf"] == -1


def test_serialize_valid_yes_no():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        oxygen_itf="No",
    )
    data = obj.model_dump()
    assert data["oxygen_itf"] == "No"


def test_serialize_delivery_empty():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        delivery_itf=None,
    )
    data = obj.model_dump()
    assert data["delivery_itf"] == -1


def test_serialize_delivery_valid():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        delivery_itf="Vacuum",
    )
    data = obj.model_dump()
    assert data["delivery_itf"] == "Vacuum"


def test_serialize_maternal():
    obj = LabourAndBirth(
        no_doses_itf="0",
        resuscitation_itf="None",
        maternal_status_itf="Well",
    )
    data = obj.model_dump()
    assert data["maternal_status_itf"] == "Well"


# --------------------------------------------------------
# Ensure required text fields are untouched

def test_string_fields_pass_through():
    obj = LabourAndBirth(
        no_doses_itf="3 doses",
        resuscitation_itf="Bag-mask ventilation",
    )
    assert obj.no_doses_itf == "3 doses"
    assert obj.resuscitation_itf == "Bag-mask ventilation"
