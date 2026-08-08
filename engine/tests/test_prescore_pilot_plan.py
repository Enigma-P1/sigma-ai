"""Prescore tests for T-19: each of the 4 checks, driven to both pass and
flag at least once."""

from factories import make_declared_package, make_pilot_plan, make_pilot_plan_confounder_checklist, make_pilot_plan_with_package
from sigma_engine.artifacts.pilot_plan import PilotPlanArtifact
from sigma_engine.prescore.pilot_plan import MIN_FALSIFICATION_LENGTH, MIN_PACKAGE_COMPONENTS, run_pilot_plan_prescore

EXPECTED_CHECK_IDS = {
    "threshold_before_data_advisory", "falsification_substance_heuristic", "checklist_completeness",
    "package_declaration_quality",
}


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


# ---------------------------------------------------------------------------
# M4 addition: package_declaration_quality.
# ---------------------------------------------------------------------------


def test_package_declaration_quality_not_applicable_and_passes_with_no_package():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["package_declaration_quality"].status == "pass"
    assert "not applicable" in results["package_declaration_quality"].detail


def test_package_declaration_quality_passes_a_real_two_component_package():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan_with_package())
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["package_declaration_quality"].status == "pass"
    assert "real package" in results["package_declaration_quality"].detail


def test_package_declaration_quality_flags_a_one_component_package():
    package = make_declared_package(components=["fixture head"])
    body = make_pilot_plan_with_package(declared_package=package, changes=[
        {"change_id": "ch-1", "text": "Replace the fixture head"},
    ])
    artifact = PilotPlanArtifact.model_validate(body)
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["package_declaration_quality"].status == "flag"
    assert "just a change" in results["package_declaration_quality"].detail
    assert str(MIN_PACKAGE_COMPONENTS) in results["package_declaration_quality"].detail


def test_package_declaration_quality_flags_a_whitespace_only_rationale():
    """Field(min_length=1) alone lets a whitespace-only rationale through
    schema (it counts characters, not stripped content) -- prescore is
    where the substance bar actually lives, same soft-check idiom as the
    falsification line."""
    package = make_declared_package(rationale="   ")
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan_with_package(declared_package=package))
    results = _by_id(run_pilot_plan_prescore(artifact))
    assert results["package_declaration_quality"].status == "flag"
    assert "rationale" in results["package_declaration_quality"].detail.lower()
