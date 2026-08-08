"""Tests for prescore/hypothesis.py: rubric R-ANA-04's rule-checkable
lines -- routing recorded, route-tamper check, declared-primary present,
exit honored, tests-run-vs-declared-primary."""

from factories import make_hypothesis
from sigma_engine.artifacts.hypothesis import HypothesisRunArtifact
from sigma_engine.prescore.hypothesis import run_hypothesis_prescore
from sigma_engine.stats.hypothesis_selector import HypothesisExitPayload


def _check(results, check_id):
    return next(r for r in results if r.check_id == check_id)


def test_all_checks_pass_on_a_clean_welch_artifact():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    results = run_hypothesis_prescore(artifact)
    check_ids = {r.check_id for r in results}
    assert check_ids == {"routing_recorded", "route_tamper_check", "declared_primary_present", "exit_honored", "tests_run_vs_declared_primary"}
    assert all(r.status == "pass" for r in results)


def test_all_checks_pass_on_a_clean_refused_artifact():
    body = make_hypothesis(question={
        "question_text": "tiny groups", "comparison_type": "two_independent",
        "groups": [{"label": "A", "values": [1, 2, 3]}, {"label": "B", "values": [4, 5, 6]}],
    })
    artifact = HypothesisRunArtifact.model_validate(body)
    results = run_hypothesis_prescore(artifact)
    assert all(r.status == "pass" for r in results)
    assert "EXIT-06" in _check(results, "routing_recorded").detail


def test_route_tamper_check_flags_a_hand_edited_route():
    """Mirrors test_prescore_msa.py::test_tampered_result_flags_result_
    matches_inputs: model_copy(update=...) makes a shallow, non-
    revalidating copy -- simulating a hand-edited on-disk JSON file loaded
    back without re-running HypothesisRunArtifact's validator (exactly the
    GET .../artifacts/{id} path both docstrings describe)."""
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    tampered_routing = artifact.routing.model_copy(update={"route": "paired_t"})
    tampered = artifact.model_copy(update={"routing": tampered_routing})
    results = run_hypothesis_prescore(tampered)
    check = _check(results, "route_tamper_check")
    assert check.status == "flag"
    assert "hand-edited" in check.detail


def test_exit_honored_flags_a_result_stored_past_a_raised_exit():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    fake_exit_routing = artifact.routing.model_copy(update={
        "route": None,
        "exit": HypothesisExitPayload(exit_id="EXIT-06", message="m", routes_to="r", detail="d"),
    })
    # artifact.result stays the real computed Welch result -- exactly "a
    # result stored despite a raised exit," the case this check exists for.
    tampered = artifact.model_copy(update={"routing": fake_exit_routing})
    results = run_hypothesis_prescore(tampered)
    check = _check(results, "exit_honored")
    assert check.status == "flag"
    assert "EXIT-06" in check.detail


def test_tests_run_vs_declared_primary_flags_multiplicity_mismatch():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    # EXIT-12 would have fired had this been in the artifact from the
    # start; simulate a stale/hand-edited question field slipping past
    # that (the prescore check is a second line of defense, not the only one).
    tampered_question = artifact.question.model_copy(update={"tests_run_including_this_one": 2})
    tampered = artifact.model_copy(update={"question": tampered_question})
    results = run_hypothesis_prescore(tampered)
    check = _check(results, "tests_run_vs_declared_primary")
    assert check.status == "flag"


def test_declared_primary_present_reflects_the_field():
    artifact_false = HypothesisRunArtifact.model_validate(make_hypothesis(declared_primary=False))
    check = _check(run_hypothesis_prescore(artifact_false), "declared_primary_present")
    assert check.status == "pass"
    assert "declared_primary=False" in check.detail
