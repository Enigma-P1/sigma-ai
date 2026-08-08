"""Prescore tests for T-06: each of the 9 checks, driven to both pass and
flag at least once (the clean default fixture passes all 9)."""

from factories import make_process_map, make_process_map_steps
from sigma_engine.artifacts.process_map import ProcessMapArtifact
from sigma_engine.prescore.process_map import run_process_map_prescore

EXPECTED_CHECK_IDS = {
    "lane_count_minimum", "lane_owner_present", "step_count_minimum", "step_type_tag_present",
    "reason_required_for_tagged_steps", "times_present_half", "orphan_steps",
    "waste_notes_present", "bottleneck_fields_consistency",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_map_passes_every_check():
    artifact = ProcessMapArtifact.model_validate(make_process_map())
    results = _by_id(run_process_map_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id, r in results.items():
        assert r.status == "pass", f"{check_id}: expected pass, got {r.status} ({r.detail})"


def test_lane_count_flags_single_lane():
    lanes = [make_process_map()["lanes"][0]]
    steps = [{**s, "lane_id": "lane-1"} for s in make_process_map_steps()]
    artifact = ProcessMapArtifact.model_validate(make_process_map(lanes=lanes, steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["lane_count_minimum"].status == "flag"


def test_lane_owner_flags_blank_owner():
    lanes = make_process_map()["lanes"]
    lanes[0]["owner"] = "  "
    artifact = ProcessMapArtifact.model_validate(make_process_map(lanes=lanes))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["lane_owner_present"].status == "flag"
    assert "lane-1" in results["lane_owner_present"].detail


def test_step_count_flags_below_three():
    steps = make_process_map_steps()[:2]
    artifact = ProcessMapArtifact.model_validate(
        make_process_map(steps=steps, connectors=[{"from_step": "step-1", "to_step": "step-2", "label": None}])
    )
    results = _by_id(run_process_map_prescore(artifact))
    assert results["step_count_minimum"].status == "flag"


def test_step_type_tag_present_always_passes():
    artifact = ProcessMapArtifact.model_validate(make_process_map())
    results = _by_id(run_process_map_prescore(artifact))
    assert results["step_type_tag_present"].status == "pass"
    assert "3" in results["step_type_tag_present"].detail


def test_reason_required_flags_blank_reason_on_tagged_step():
    steps = make_process_map_steps()
    steps[0]["reason"] = "   "  # step-1 is value_add
    artifact = ProcessMapArtifact.model_validate(make_process_map(steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["reason_required_for_tagged_steps"].status == "flag"
    assert "step-1" in results["reason_required_for_tagged_steps"].detail


def test_reason_not_required_for_enabling_step():
    steps = make_process_map_steps()
    steps[0]["step_type"] = "enabling"
    steps[0]["reason"] = ""
    artifact = ProcessMapArtifact.model_validate(make_process_map(steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["reason_required_for_tagged_steps"].status == "pass"


def test_times_present_half_flags_when_fewer_than_half_are_timed():
    steps = make_process_map_steps()
    steps[1]["time_minutes"] = None
    steps[2]["time_minutes"] = None
    artifact = ProcessMapArtifact.model_validate(make_process_map(steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["times_present_half"].status == "flag"
    assert results["times_present_half"].detail.startswith("1/3")


def test_orphan_steps_flags_a_disconnected_step():
    steps = make_process_map_steps()
    steps.append({
        "step_id": "step-4", "lane_id": "lane-1", "name": "Floating step", "order": 3,
        "step_type": "enabling", "reason": "", "time_minutes": None, "defect_point": False, "strata": [], "wastes": [],
    })
    # connectors deliberately left as the default two -- step-4 touches none.
    artifact = ProcessMapArtifact.model_validate(make_process_map(steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["orphan_steps"].status == "flag"
    assert "step-4" in results["orphan_steps"].detail


def test_waste_notes_present_flags_a_blank_note():
    steps = make_process_map_steps()
    steps[1]["wastes"] = [{"waste_id": "waiting", "note": "   "}]
    artifact = ProcessMapArtifact.model_validate(make_process_map(steps=steps))
    results = _by_id(run_process_map_prescore(artifact))
    assert results["waste_notes_present"].status == "flag"
    assert "step-2" in results["waste_notes_present"].detail


def test_bottleneck_fields_consistency_passes_with_and_without_demand():
    no_demand = ProcessMapArtifact.model_validate(make_process_map())
    with_demand = ProcessMapArtifact.model_validate(
        make_process_map(demand={"available_time_minutes": 480, "demand_units": 96})
    )
    assert _by_id(run_process_map_prescore(no_demand))["bottleneck_fields_consistency"].status == "pass"
    assert _by_id(run_process_map_prescore(with_demand))["bottleneck_fields_consistency"].status == "pass"


def test_bottleneck_fields_consistency_flags_a_tampered_stored_value():
    artifact = ProcessMapArtifact.model_validate(make_process_map(demand={"available_time_minutes": 480, "demand_units": 96}))
    tampered = artifact.model_copy(
        update={"bottleneck": artifact.bottleneck.model_copy(
            update={"value": artifact.bottleneck.value.model_copy(update={"bottleneck_time_minutes": 999.0})}
        )}
    )
    results = _by_id(run_process_map_prescore(tampered))
    assert results["bottleneck_fields_consistency"].status == "flag"
    assert "hand-edited" in results["bottleneck_fields_consistency"].detail
