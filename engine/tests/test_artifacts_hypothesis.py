"""Schema tests for T-17 HypothesisRunArtifact: the "routing/result are
always server-recomputed, never hand-typed" contract (mirrors
test_artifacts_msa.py's identical contract for MsaArtifact.result)."""

import pytest
from pydantic import ValidationError

from factories import make_hypothesis
from sigma_engine.artifacts.hypothesis import HypothesisRunArtifact


def test_accepts_a_complete_welch_question():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    assert artifact.refused is False
    assert artifact.routing.route == "welch_two_sample_t"
    assert artifact.result is not None
    assert artifact.result.value.statistic == pytest.approx(2.2694, abs=1e-4)


def test_exit06_question_produces_a_refused_artifact_with_no_result():
    body = make_hypothesis(question={
        "question_text": "tiny groups", "comparison_type": "two_independent",
        "groups": [{"label": "A", "values": [1, 2, 3]}, {"label": "B", "values": [4, 5, 6]}],
    })
    artifact = HypothesisRunArtifact.model_validate(body)
    assert artifact.refused is True
    assert artifact.result is None
    assert artifact.routing.exit.exit_id == "EXIT-06"


def test_posted_routing_and_result_are_discarded_and_recomputed():
    """A hand-typed/tampered routing+result can never survive validation
    -- exactly MsaArtifact.result's contract (test_artifacts_msa.py::
    test_posted_result_is_discarded_and_recomputed), applied here to
    routing/result/refused."""
    tampered = make_hypothesis()
    tampered["routing"] = {
        "question": "fake", "comparison_type": "two_independent", "decision_path": [],
        "route": None, "exit": {"exit_id": "EXIT-06", "message": "fake", "routes_to": "fake", "detail": "fake"},
        "switch_reason": None, "recommend_nonparametric": False,
    }
    tampered["result"] = None
    tampered["refused"] = True
    artifact = HypothesisRunArtifact.model_validate(tampered)
    # The tampered dict claimed EXIT-06/refused -- if either survived, the
    # tampered dict wasn't actually discarded and recomputed.
    assert artifact.refused is False
    assert artifact.routing.route == "welch_two_sample_t"
    assert artifact.result is not None


def test_multi_group_question_produces_anova_with_exit13():
    body = make_hypothesis(question={
        "question_text": "do the 3 temperatures differ?", "comparison_type": "multi_group",
        "groups": [
            {"label": "Level 1", "values": [6.9, 5.4, 5.8, 4.6, 4.0]},
            {"label": "Level 2", "values": [8.3, 6.8, 7.8, 9.2, 6.5]},
            {"label": "Level 3", "values": [8.0, 10.5, 8.1, 6.9, 9.3]},
        ],
    })
    artifact = HypothesisRunArtifact.model_validate(body)
    assert artifact.routing.route == "one_way_anova"
    assert artifact.result.value.exit13 is not None


def test_declared_primary_defaults_true_and_is_settable():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    assert artifact.declared_primary is True
    artifact2 = HypothesisRunArtifact.model_validate(make_hypothesis(declared_primary=False))
    assert artifact2.declared_primary is False


def test_malformed_question_structure_rejected_at_validation():
    body = make_hypothesis(question={
        "question_text": "bad", "comparison_type": "two_independent",
        "groups": [{"label": "only one group", "values": [1, 2, 3, 4, 5, 6, 7, 8]}],
    })
    with pytest.raises(ValidationError):
        HypothesisRunArtifact.model_validate(body)


def test_round_trip_via_model_dump():
    artifact = HypothesisRunArtifact.model_validate(make_hypothesis())
    round_tripped = HypothesisRunArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
