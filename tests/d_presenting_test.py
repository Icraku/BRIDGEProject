import pytest
from schemas.d_presenting_problems import PresentingProblems, YesNoEnum

# ------------------------
# Normalization tests

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_empty_normalization(input_val):
    obj = PresentingProblems(
        fever_nar=input_val,
        diff_breath_nar=input_val,
        inability_feed_nar=input_val,
        convulsions_nar=input_val,
        apnoea_nar=input_val,
        floppy_nar=input_val,
        vomits_nar=input_val,
        passed_stool_nar=input_val,
        passed_urine_nar=input_val
    )

    for field in [
        "fever_nar", "diff_breath_nar", "inability_feed_nar",
        "convulsions_nar", "apnoea_nar", "floppy_nar",
        "vomits_nar", "passed_stool_nar", "passed_urine_nar"
    ]:
        assert getattr(obj, field) == YesNoEnum.EMPTY

# ------------------------
# Valid input tests


def test_valid_yes_no():
    obj = PresentingProblems(
        fever_nar="Yes",
        diff_breath_nar="No"
    )
    assert obj.fever_nar == YesNoEnum.Yes
    assert obj.diff_breath_nar == YesNoEnum.No

# ------------------------
# Serialization tests

def test_serialize_empty_yes_no():
    obj = PresentingProblems(
        fever_nar=None,
        diff_breath_nar=None
    )
    data = obj.model_dump()
    assert data["fever_nar"] == -1
    assert data["diff_breath_nar"] == -1

def test_serialize_valid_yes_no():
    obj = PresentingProblems(
        fever_nar="Yes",
        diff_breath_nar="No"
    )
    data = obj.model_dump()
    assert data["fever_nar"] == "Yes"
    assert data["diff_breath_nar"] == "No"
