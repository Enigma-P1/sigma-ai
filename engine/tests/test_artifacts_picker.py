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


# --- Golden pin (matrix golden-coverage rule; evals/goldens/golden-id-map
# greps this literal id into its unit-test home) ----------------------------


def test_G_picker_02_pdca_quick_path_routing_through_t01():
    """G-picker-02 golden (matrix V.C.3 / VI.B.5: the T-01 PDCA quick path
    for small problems): the frozen routing rule (matrix §4a) makes PDCA
    legal on BOTH sides of the intake criteria -- an all-Yes project may
    still take the quick path (full rigor isn't warranted for a small
    win), and a one-No project routes PDCA instead of being forced to
    EXIT-01 -- while full-DMAIC stays impossible past any No. All three
    arms exercise the same route_is_consistent() rule the schema
    validator and prescore/picker.py's routing-consistency check share."""
    # Arm 1: all-Yes + PDCA validates (quick path chosen, not forced).
    all_yes_pdca = PickerArtifact.model_validate(make_picker(route="PDCA"))
    assert all_yes_pdca.route == "PDCA"
    assert all_yes_pdca.criteria_answers() == [True] * 5

    # Arm 2: one-No + PDCA validates -- the small-problem quick path.
    data = make_picker(route="PDCA")
    data["business_impact_plausible"] = {"answer": False, "detail": "Impact is tiny; the fix is a two-minute change worth doing as PDCA."}
    one_no_pdca = PickerArtifact.model_validate(data)
    assert one_no_pdca.route == "PDCA"
    assert one_no_pdca.criteria_answers().count(False) == 1

    # Arm 3: the same one-No answers can never route full-DMAIC.
    assert route_is_consistent(one_no_pdca.criteria_answers(), "PDCA") is True
    assert route_is_consistent(one_no_pdca.criteria_answers(), "full-DMAIC") is False
