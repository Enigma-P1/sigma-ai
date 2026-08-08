"""Prescore tests for T-15: each of the 5 checks, driven to both pass and
flag (or hard_flag) at least once. The clean default fixture passes 4 of
5 -- branch_coverage_minimum and cause_count_minimum both pass at 2
branches/4 causes... wait, see the fixture-shape note on each test below,
since make_fishbone()'s default fixture is deliberately UNDER both
breadth floors (2 branches, 4 causes) to make the flag path the default
and the pass path the one that needs a bigger fixture."""

from factories import make_fishbone, make_fishbone_causes
from sigma_engine.artifacts.fishbone import FishboneArtifact
from sigma_engine.prescore.fishbone import run_fishbone_prescore

EXPECTED_CHECK_IDS = {
    "branch_coverage_minimum", "cause_count_minimum", "absent_solution_language",
    "verified_causes_have_evidence", "ruled_out_causes_retained",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def _wide_fishbone():
    """>=2 branches, >=6 causes, no absent-solution phrasing -- the fixture
    that clears every flag-capable check at once."""
    causes = make_fishbone_causes()  # 2 branches (method, machine), 4 causes
    causes += [
        {"cause_id": "c-4", "branch": "measurement", "text": "Scale not calibrated this quarter",
         "parent_cause_id": None, "status": "candidate", "why_chain_position": None, "evidence": None},
        {"cause_id": "c-5", "branch": "environment", "text": "Ambient humidity swings during summer shifts",
         "parent_cause_id": None, "status": "candidate", "why_chain_position": None, "evidence": None},
    ]
    return make_fishbone(causes=causes)


def test_all_checks_present_and_wide_fixture_passes_every_flag_capable_check():
    artifact = FishboneArtifact.model_validate(_wide_fishbone())
    results = _by_id(run_fishbone_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id in ("branch_coverage_minimum", "cause_count_minimum", "absent_solution_language", "verified_causes_have_evidence"):
        assert results[check_id].status == "pass", f"{check_id}: {results[check_id].detail}"


def test_branch_coverage_flags_a_single_branch():
    causes = [c for c in make_fishbone_causes() if c["branch"] == "method"]
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["branch_coverage_minimum"].status == "flag"
    assert "1/6" in results["branch_coverage_minimum"].detail


def test_branch_coverage_flags_below_four_branches():
    # Rubric R-ANA-01: 4 of 6 categories genuinely explored is the bar.
    artifact = FishboneArtifact.model_validate(make_fishbone())  # default fixture: method + machine only
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["branch_coverage_minimum"].status == "flag"


def test_branch_coverage_passes_at_four_branches():
    causes = make_fishbone()["causes"]
    extra = [
        dict(causes[0], cause_id="c-extra-1", branch="people", text="New barista on drink queue during peak"),
        dict(causes[0], cause_id="c-extra-2", branch="environment", text="Espresso station crowded at rush"),
    ]
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes + extra))
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["branch_coverage_minimum"].status == "pass"


def test_cause_count_flags_below_six():
    artifact = FishboneArtifact.model_validate(make_fishbone())  # default fixture: 4 causes
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["cause_count_minimum"].status == "flag"
    assert results["cause_count_minimum"].detail.startswith("4 ")


def test_cause_count_passes_at_six_or_more():
    artifact = FishboneArtifact.model_validate(_wide_fishbone())
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["cause_count_minimum"].status == "pass"


def test_absent_solution_language_flags_no_x_phrasing():
    causes = make_fishbone_causes()
    causes[2]["text"] = "No barcode scanner installed at the fixture station"
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["absent_solution_language"].status == "flag"
    assert "c-2" in results["absent_solution_language"].detail


def test_absent_solution_language_flags_lack_of_phrasing():
    causes = make_fishbone_causes()
    causes[2]["text"] = "Lack of a preventive maintenance schedule"
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["absent_solution_language"].status == "flag"


def test_verified_causes_have_evidence_always_passes_by_schema_construction():
    for body in (make_fishbone(), _wide_fishbone(), make_fishbone(causes=[])):
        artifact = FishboneArtifact.model_validate(body)
        results = _by_id(run_fishbone_prescore(artifact))
        assert results["verified_causes_have_evidence"].status == "pass"


def test_ruled_out_causes_retained_reports_the_count():
    artifact = FishboneArtifact.model_validate(make_fishbone())  # default fixture has c-3 ruled_out
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["ruled_out_causes_retained"].status == "pass"
    assert "1 ruled-out" in results["ruled_out_causes_retained"].detail


def test_ruled_out_causes_retained_reports_zero_when_none():
    causes = [c for c in make_fishbone_causes() if c["status"] != "ruled_out"]
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    results = _by_id(run_fishbone_prescore(artifact))
    assert results["ruled_out_causes_retained"].status == "pass"
    assert "no ruled-out" in results["ruled_out_causes_retained"].detail
