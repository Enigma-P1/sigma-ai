"""Schema tests for T-01 PickerArtifact."""

import pytest
from pydantic import ValidationError

from factories import make_picker
from sigma_engine.artifacts.picker import PickerArtifact, route_is_consistent


def test_accepts_all_yes_full_dmaic():
    artifact = PickerArtifact.model_validate(make_picker())
    assert artifact.route == "full-DMAIC"
    assert artifact.criteria_answers() == [True, True, True, True, True]


def test_accepts_all_yes_pdca():
    artifact = PickerArtifact.model_validate(make_picker(route="PDCA"))
    assert artifact.route == "PDCA"


def test_accepts_one_no_routed_to_pdca():
    data = make_picker(route="PDCA")
    data["business_impact_plausible"] = {"answer": False, "detail": "Impact is tiny, but the fix is a two-minute change."}
    artifact = PickerArtifact.model_validate(data)
    assert artifact.criteria_answers().count(False) == 1


def test_accepts_one_no_routed_to_exit01():
    data = make_picker(route="EXIT-01")
    data["data_obtainable"] = {"answer": False, "detail": "No data source exists yet."}
    artifact = PickerArtifact.model_validate(data)
    assert artifact.route == "EXIT-01"


def test_rejects_route_inconsistent_with_criteria_no_routed_full_dmaic():
    """The exact scenario named in the M1 brief: any criterion No must not
    route full-DMAIC (matrix §4a)."""
    data = make_picker(route="full-DMAIC")
    data["process_owner_engaged"] = {"answer": False, "detail": "No owner has agreed to this yet."}
    with pytest.raises(ValidationError):
        PickerArtifact.model_validate(data)


def test_rejects_exit01_when_all_criteria_yes():
    with pytest.raises(ValidationError):
        PickerArtifact.model_validate(make_picker(route="EXIT-01"))


def test_rejects_missing_criterion_detail():
    data = make_picker()
    data["scope_narrow"] = {"answer": True, "detail": ""}
    with pytest.raises(ValidationError):
        PickerArtifact.model_validate(data)


@pytest.mark.parametrize(
    "criteria,route,expected",
    [
        ([True, True, True, True, True], "full-DMAIC", True),
        ([True, True, True, True, True], "PDCA", True),
        ([True, True, True, True, True], "EXIT-01", False),
        ([True, False, True, True, True], "full-DMAIC", False),
        ([True, False, True, True, True], "PDCA", True),
        ([True, False, True, True, True], "EXIT-01", True),
    ],
)
def test_route_is_consistent_matrix(criteria, route, expected):
    assert route_is_consistent(criteria, route) is expected
