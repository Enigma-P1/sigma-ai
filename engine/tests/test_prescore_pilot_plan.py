"""Prescore tests for T-19: each of the 3 checks, driven to both pass and
flag at least once."""

from factories import make_pilot_plan, make_pilot_plan_confounder_checklist
from sigma_engine.artifacts.pilot_plan import PilotPlanArtifact
from sigma_engine.prescore.pilot_plan import MIN_FALSIFICATION_LENGTH, run_pilot_plan_prescore

EXPECTED_CHECK_IDS = {"threshold_before_data_advisory", "falsification_substance_heuristic", "checklist_completeness"}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_pilot_plan_passes_every_check():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id, r in results.items():
        assert r.status == "pass", f"{check_id}: expected pass, got {r.status} ({r.detail})"


def test_threshold_before_data_advisory_always_pass_and_names_entry_order():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    results = _by_id(run_pilot_plan_prescore(artifact))
    detail = results["threshold_before_data_advisory"].detail
    assert results["threshold_before_data_advisory"].status == "pass"
    assert "entry order" in detail and "observation order" in detail


def test_falsification_substance_heuristic_flags_the_rubrics_own_bad_example():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan(falsification_line="If it doesn't work"))
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["falsification_substance_heuristic"].status == "flag"


def test_falsification_substance_heuristic_flags_a_too_short_line():
    short = "x" * (MIN_FALSIFICATION_LENGTH - 1)
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan(falsification_line=short))
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["falsification_substance_heuristic"].status == "flag"


def test_falsification_substance_heuristic_passes_a_specific_line():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan(
        falsification_line="If scrap rate stays above 4.5% for two full weeks after rollout, the checklist did not fix it.",
    ))
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["falsification_substance_heuristic"].status == "pass"


def test_checklist_completeness_flags_a_blank_note():
    checklist = make_pilot_plan_confounder_checklist()
    checklist["demand"]["note"] = ""
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan(confounder_checklist=checklist))
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["checklist_completeness"].status == "flag"
    assert "demand" in results["checklist_completeness"].detail


def test_checklist_completeness_passes_when_every_note_is_filled_in():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["checklist_completeness"].status == "pass"
