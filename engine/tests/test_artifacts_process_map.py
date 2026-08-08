"""Schema + longest-step/constraint-step arithmetic tests for T-06
ProcessMapArtifact (fidelity fix: a pure-wait step can be the longest step
but can never be the constraint -- see artifacts/process_map.py)."""

import pytest
from pydantic import ValidationError

from factories import make_process_map, make_process_map_steps
from sigma_engine.artifacts.process_map import ProcessMapArtifact, compute_constraint_step, compute_longest_step
from sigma_engine.provenance import compute


def test_accepts_a_complete_map_with_no_demand():
    artifact = ProcessMapArtifact.model_validate(make_process_map())
    assert len(artifact.lanes) == 2
    assert len(artifact.steps) == 3
    # step-2 ("Wait for register", non_value_add, 4.0 min) is still the
    # longest step even with no demand block -- longest_step needs no pace.
    assert artifact.longest_step.value.step_id == "step-2"
    assert artifact.constraint_step is None  # no demand block -- nothing to judge pace against yet


def test_constraint_step_meets_pace():
    # available=480, demand=96 -> pace=5.0 min/unit. Step times: step-1
    # (value_add) 1.0, step-2 (non_value_add wait) 4.0, step-3 (value_add)
    # 3.0. The wait is excluded from constraint_step -- among PROCESSING
    # steps the longest is step-3 at 3.0, which is <= the 5.0 pace.
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    longest = artifact.longest_step.value
    assert longest.step_id == "step-2"
    assert longest.step_type == "non_value_add"
    assert longest.time_minutes == 4.0

    constraint = artifact.constraint_step.value
    assert constraint.step_id == "step-3"
    assert constraint.step_name == "Make drink"
    assert constraint.time_minutes == 3.0
    assert constraint.pace_minutes_per_unit == pytest.approx(5.0)
    assert constraint.meets_pace is True
    assert artifact.longest_step.provenance.method
    assert artifact.longest_step.provenance.input_hash
    assert artifact.constraint_step.provenance.method
    assert artifact.constraint_step.provenance.input_hash


def test_constraint_step_misses_pace():
    # available=200, demand=100 -> pace=2.0 min/unit; step-3's 3.0-minute
    # constraint exceeds it even though step-2's 4.0-minute wait is longer
    # still -- meets_pace is judged on the constraint, not the longest step.
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 200, "demand_units": 100}))
    constraint = artifact.constraint_step.value
    assert constraint.step_id == "step-3"
    assert constraint.pace_minutes_per_unit == pytest.approx(2.0)
    assert constraint.time_minutes == 3.0
    assert constraint.meets_pace is False


def test_constraint_step_none_when_demand_partial():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": None}))
    assert artifact.constraint_step is None
    # longest_step doesn't need a demand block at all -- still populated.
    assert artifact.longest_step is not None


def test_both_none_when_no_step_has_a_time():
    steps = [{**s, "time_minutes": None} for s in make_process_map_steps()]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert artifact.longest_step is None
    assert artifact.constraint_step is None


def test_constraint_step_none_when_no_processing_step_has_a_time():
    # Every PROCESSING step (value_add/enabling) has its time cleared;
    # only the non_value_add wait keeps one -- longest_step can still name
    # it, but constraint_step has nothing eligible to name.
    steps = make_process_map_steps()
    steps = [{**s, "time_minutes": None} if s["step_type"] != "non_value_add" else s for s in steps]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert artifact.longest_step.value.step_id == "step-2"
    assert artifact.constraint_step is None


def test_longest_step_tie_break_is_deterministic():
    steps = make_process_map_steps()
    # step-4 ties step-2's 4.0-minute max but sits in lane-1 (alphabetically
    # before lane-2) -- (lane_id, order, step_id) tie-break must pick it.
    # step-4 is itself enabling (a processing type), so this also exercises
    # longest_step and constraint_step picking DIFFERENT steps: step-4 ties
    # step-2 on raw time, but constraint_step only ever compares against
    # other processing steps (step-1, step-3), never against step-2 at all.
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
    assert artifact.longest_step.value.step_id == "step-4"
    assert artifact.constraint_step.value.step_id == "step-4"  # uniquely the longest PROCESSING step at 4.0


def test_constraint_step_tie_break_is_deterministic():
    # Two PROCESSING steps genuinely tie for the constraint (step-3 at 3.0
    # bumped up to tie a new step-4 at 3.0); step-2's 4.0-minute wait stays
    # the longest_step throughout and never enters this tie at all.
    steps = make_process_map_steps()
    steps[2]["time_minutes"] = 3.0  # step-3, already 3.0 -- explicit for clarity
    steps.append({
        "step_id": "step-4", "lane_id": "lane-1", "name": "Tie step", "order": 2,
        "step_type": "value_add", "reason": "x", "time_minutes": 3.0, "defect_point": False, "strata": [], "wastes": [],
    })
    connectors = [
        {"from_step": "step-1", "to_step": "step-4", "label": None},
        {"from_step": "step-2", "to_step": "step-3", "label": None},
    ]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, connectors=connectors, demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert artifact.longest_step.value.step_id == "step-2"  # the 4.0-minute wait, unaffected by the tie
    assert artifact.constraint_step.value.step_id == "step-4"  # lane-1 sorts before lane-2 (step-3)


def test_posted_bottleneck_fields_are_discarded_and_recomputed():
    """R-DEF-05-style guarantee, applied to T-06: hand-typed/tampered
    longest_step/constraint_step can never survive a save."""
    tampered_longest = compute(
        {"step_id": "nope", "step_name": "nope", "step_type": "value_add", "time_minutes": 999.0},
        method="tampered", input_data=[],
    )
    tampered_constraint = compute(
        {"step_id": "nope", "step_name": "nope", "time_minutes": 999.0, "pace_minutes_per_unit": 1.0, "meets_pace": False},
        method="tampered", input_data=[],
    )
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(
            demand={"available_time_minutes": 480, "demand_units": 96},
            longest_step=tampered_longest.model_dump(mode="json"),
            constraint_step=tampered_constraint.model_dump(mode="json"),
        )
    )
    assert artifact.longest_step.value.step_id == "step-2"
    assert artifact.constraint_step.value.step_id == "step-3"


def test_compute_longest_and_constraint_step_match_artifact_fields():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    assert compute_longest_step(artifact.steps).value == artifact.longest_step.value
    assert compute_constraint_step(artifact.steps, artifact.demand).value == artifact.constraint_step.value


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
