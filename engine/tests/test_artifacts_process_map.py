"""Schema + bottleneck-arithmetic tests for T-06 ProcessMapArtifact."""

import pytest
from pydantic import ValidationError

from factories import make_process_map, make_process_map_steps
from sigma_engine.artifacts.process_map import ProcessMapArtifact, compute_bottleneck
from sigma_engine.provenance import compute


def test_accepts_a_complete_map_with_no_demand():
    artifact = ProcessMapArtifact.model_validate(make_process_map())
    assert len(artifact.lanes) == 2
    assert len(artifact.steps) == 3
    assert artifact.bottleneck is None  # no demand block -- nothing to name yet


def test_bottleneck_hand_checked_meets_pace():
    # available=480, demand=96 -> pace=5.0 min/unit. Step times: 1.0, 4.0,
    # 3.0 -- the longest is step-2 at 4.0, which is <= the 5.0 pace.
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    result = artifact.bottleneck.value
    assert result.bottleneck_step_id == "step-2"
    assert result.bottleneck_step_name == "Wait for register"
    assert result.bottleneck_time_minutes == 4.0
    assert result.pace_minutes_per_unit == pytest.approx(5.0)
    assert result.meets_pace is True
    assert artifact.bottleneck.provenance.method
    assert artifact.bottleneck.provenance.input_hash


def test_bottleneck_hand_checked_misses_pace():
    # available=200, demand=100 -> pace=2.0 min/unit; the 4.0-minute
    # bottleneck step exceeds it.
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 200, "demand_units": 100}))
    result = artifact.bottleneck.value
    assert result.pace_minutes_per_unit == pytest.approx(2.0)
    assert result.bottleneck_time_minutes == 4.0
    assert result.meets_pace is False


def test_bottleneck_none_when_demand_partial():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": None}))
    assert artifact.bottleneck is None


def test_bottleneck_none_when_no_step_has_a_time():
    steps = [{**s, "time_minutes": None} for s in make_process_map_steps()]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert artifact.bottleneck is None


def test_bottleneck_tie_break_is_deterministic():
    steps = make_process_map_steps()
    # step-4 ties step-2's 4.0-minute max but sits in lane-1 (alphabetically
    # before lane-2) -- (lane_id, order, step_id) tie-break must pick it.
    steps.append({
        "step_id": "step-4", "lane_id": "lane-1", "name": "Tie step", "order": 2,
        "step_type": "enabling", "reason": "", "time_minutes": 4.0, "defect_point": False, "strata": [], "wastes": [],
    })
    connectors = [
        {"from_step": "step-1", "to_step": "step-4", "label": None},
        {"from_step": "step-2", "to_step": "step-3", "label": None},
    ]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, connectors=connectors, demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert artifact.bottleneck.value.bottleneck_step_id == "step-4"


def test_posted_bottleneck_is_discarded_and_recomputed():
    """R-DEF-05-style guarantee, applied to T-06: a hand-typed/tampered
    bottleneck can never survive a save."""
    tampered = compute({"bottleneck_step_id": "nope", "bottleneck_step_name": "nope", "bottleneck_time_minutes": 999.0,
                         "pace_minutes_per_unit": 1.0, "meets_pace": False}, method="tampered", input_data=[])
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}, bottleneck=tampered.model_dump(mode="json"))
    )
    assert artifact.bottleneck.value.bottleneck_step_id == "step-2"


def test_compute_bottleneck_matches_artifact_field():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    recomputed = compute_bottleneck(artifact.steps, artifact.demand)
    assert recomputed.value == artifact.bottleneck.value


def test_round_trip_via_model_dump():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    round_tripped = ProcessMapArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


def test_rejects_empty_lanes():
    with pytest.raises(ValidationError):
        ProcessMapArtifact.model_validate(make_process_map(lanes=[]))


def test_rejects_empty_steps():
    with pytest.raises(ValidationError):
        ProcessMapArtifact.model_validate(make_process_map(steps=[]))


def test_rejects_duplicate_lane_ids():
    lanes = make_process_map()["lanes"]
    lanes.append({"lane_id": "lane-1", "name": "Duplicate", "owner": "Someone"})
    with pytest.raises(ValidationError, match="lane_id"):
        ProcessMapArtifact.model_validate(make_process_map(lanes=lanes))


def test_rejects_duplicate_step_ids():
    steps = make_process_map_steps()
    steps.append({**steps[0], "step_id": "step-1"})
    with pytest.raises(ValidationError, match="step_id"):
        ProcessMapArtifact.model_validate(make_process_map(steps=steps))


def test_rejects_step_referencing_unknown_lane():
    steps = make_process_map_steps()
    steps[0]["lane_id"] = "no-such-lane"
    with pytest.raises(ValidationError, match="unknown lane_id"):
        ProcessMapArtifact.model_validate(make_process_map(steps=steps))


def test_rejects_connector_referencing_unknown_step():
    with pytest.raises(ValidationError, match="unknown from_step"):
        ProcessMapArtifact.model_validate(
            make_process_map(connectors=[{"from_step": "no-such-step", "to_step": "step-1", "label": None}])
        )


def test_rejects_negative_time_minutes():
    steps = make_process_map_steps()
    steps[0]["time_minutes"] = -1.0
    with pytest.raises(ValidationError):
        ProcessMapArtifact.model_validate(make_process_map(steps=steps))


def test_rejects_duplicate_waste_on_same_step():
    steps = make_process_map_steps()
    steps[1]["wastes"] = [{"waste_id": "waiting", "note": "a"}, {"waste_id": "waiting", "note": "b"}]
    with pytest.raises(ValidationError, match="checked more than once"):
        ProcessMapArtifact.model_validate(make_process_map(steps=steps))


def test_reason_and_owner_and_note_may_be_blank_at_schema_level():
    """PLAN §4.2's soft/hard split: content-completeness lives in prescore
    (test_prescore_process_map.py), not here."""
    lanes = [{"lane_id": "lane-1", "name": "Customer", "owner": ""}]
    steps = [{
        "step_id": "step-1", "lane_id": "lane-1", "name": "Order", "order": 1, "step_type": "non_value_add",
        "reason": "", "time_minutes": None, "defect_point": False, "strata": [],
        "wastes": [{"waste_id": "waiting", "note": ""}],
    }]
    artifact = ProcessMapArtifact.model_validate(make_process_map(lanes=lanes, steps=steps, connectors=[]))
    assert artifact.lanes[0].owner == ""
    assert artifact.steps[0].reason == ""
    assert artifact.steps[0].wastes[0].note == ""
