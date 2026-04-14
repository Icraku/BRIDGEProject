import pytest
from schemas.b_mother_details import MotherDetails, BloodGroupNar, PosNegUnknEnum, YesNoEnum, YesNoUnknEnum

@pytest.mark.parametrize("input_val", [None, "", -1, "-1", "EMPTY"])
def test_empty_normalization(input_val):
    obj = MotherDetails(
        mum_ip_no_nar="123",
        mum_age_years_nar="30",
        parity_nar="2",
        edd_date_nar="2025-01-01",
        blood_group_nar=input_val,
        rhesus_nar=input_val,
        anti_d_nar=input_val,
        anc_visits_nar="3",
        anc_us_nar=input_val,
        anc_trimester_nar="2",
        vdrl_nar=input_val,
        pmtct_nar=input_val,
        mum_arvs_nar=input_val,
        hepb_nar=input_val,
        hepb_ig_nar=input_val,
        htn_pregnancy_nar=input_val,
        aph_nar=input_val,
        diabetes_nar=input_val,
        prolonged_stage_nar=input_val
    )

    assert obj.blood_group_nar == BloodGroupNar.EMPTY
    assert obj.rhesus_nar == PosNegUnknEnum.EMPTY
    assert obj.anti_d_nar == YesNoEnum.EMPTY
    assert obj.anc_us_nar == YesNoEnum.EMPTY
    assert obj.vdrl_nar == PosNegUnknEnum.EMPTY
    assert obj.pmtct_nar == PosNegUnknEnum.EMPTY
    assert obj.mum_arvs_nar == YesNoUnknEnum.EMPTY
    assert obj.hepb_nar == PosNegUnknEnum.EMPTY
    assert obj.hepb_ig_nar == YesNoUnknEnum.EMPTY
    assert obj.htn_pregnancy_nar == YesNoUnknEnum.EMPTY
    assert obj.aph_nar == YesNoUnknEnum.EMPTY
    assert obj.diabetes_nar == YesNoUnknEnum.EMPTY
    assert obj.prolonged_stage_nar == YesNoUnknEnum.EMPTY

def test_serialization_empty():
    obj = MotherDetails(
        mum_ip_no_nar="123",
        mum_age_years_nar="30",
        parity_nar="2",
        edd_date_nar="2025-01-01",
        blood_group_nar=None,
        rhesus_nar=None,
        anti_d_nar=None,
        anc_visits_nar="3",
        anc_us_nar=None,
        anc_trimester_nar="2",
        vdrl_nar=None,
        pmtct_nar=None,
        mum_arvs_nar=None,
        hepb_nar=None,
        hepb_ig_nar=None,
        htn_pregnancy_nar=None,
        aph_nar=None,
        diabetes_nar=None,
        prolonged_stage_nar=None
    )

    data = obj.model_dump()
    for field in data:
        if field in [
            "blood_group_nar", "rhesus_nar", "anti_d_nar", "anc_us_nar", "vdrl_nar",
            "pmtct_nar", "mum_arvs_nar", "hepb_nar", "hepb_ig_nar", "htn_pregnancy_nar",
            "aph_nar", "diabetes_nar", "prolonged_stage_nar"
        ]:
            assert data[field] == -1

def test_valid_values():
    obj = MotherDetails(
        mum_ip_no_nar="123",
        mum_age_years_nar="30",
        parity_nar="2",
        edd_date_nar="2025-01-01",
        blood_group_nar="A",
        rhesus_nar="Pos",
        anti_d_nar="Yes",
        anc_visits_nar="3",
        anc_us_nar="No",
        anc_trimester_nar="2",
        vdrl_nar="Unkn",
        pmtct_nar="Neg",
        mum_arvs_nar="Yes",
        hepb_nar="Pos",
        hepb_ig_nar="No",
        htn_pregnancy_nar="Unkn",
        aph_nar="Yes",
        diabetes_nar="No",
        prolonged_stage_nar="Yes"
    )

    assert obj.blood_group_nar == BloodGroupNar.A
    assert obj.rhesus_nar == PosNegUnknEnum.Pos
    assert obj.anti_d_nar == YesNoEnum.Yes
    assert obj.anc_us_nar == YesNoEnum.No
    assert obj.vdrl_nar == PosNegUnknEnum.Unkn
    assert obj.pmtct_nar == PosNegUnknEnum.Neg
    assert obj.mum_arvs_nar == YesNoUnknEnum.Yes
    assert obj.hepb_nar == PosNegUnknEnum.Pos
    assert obj.hepb_ig_nar == YesNoUnknEnum.No
    assert obj.htn_pregnancy_nar == YesNoUnknEnum.Unkn
    assert obj.aph_nar == YesNoUnknEnum.Yes
    assert obj.diabetes_nar == YesNoUnknEnum.No
    assert obj.prolonged_stage_nar == YesNoUnknEnum.Yes
