from enum import Enum

import pytest
from schemas.f_admission_investigation import (
    AdmissionInvestigation,
    RandomBloodSugarNar,
    BilirubinNar
)

EMPTY_VALUES = [None, "", -1, "-1"]

def sample_admission_data(overrides=None):
    data = dict(
        rbs_nar=None,
        rbs_measure_nar="3.9",
        bilirubin_nar=None,
        serum_measure_nar="5.1"
    )
    if overrides:
        data.update(overrides)
    return data

@pytest.mark.parametrize("val", EMPTY_VALUES)
def test_empty_normalization(val):
    obj = AdmissionInvestigation(**sample_admission_data({
        "rbs_nar":val,
        "rbs_measure_nar":val,
        "bilirubin_nar":val,
        "serum_measure_nar":val
    }))

    assert obj.rbs_nar == RandomBloodSugarNar.EMPTY
    assert obj.bilirubin_nar == BilirubinNar.EMPTY

def test_serialization_empty():
    obj = AdmissionInvestigation(**sample_admission_data())
    data = obj.model_dump()
    for field, value in data.items():
        if isinstance(value, Enum):
            assert value.value != "-1" or data[field] == -1  # serialized correctly

def test_valid_values():
    obj = AdmissionInvestigation(**sample_admission_data({
        "rbs_nar": "Yes",
        "bilirubin_nar": "Yes",
    }))

    assert obj.rbs_nar == RandomBloodSugarNar.Yes
    assert obj.bilirubin_nar == BilirubinNar.Yes
