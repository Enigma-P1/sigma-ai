"""Schema accept/reject + quadrant/weighted-total/ranked-fix-list
computation tests for T-18 SolutionMatrixArtifact -- includes the
hand-checkable ranking fixture, both weighted and unweighted (task brief)."""

import pytest
from pydantic import ValidationError

from factories import make_solution_matrix, make_solution_matrix_solutions, make_unweighted_solutions
from sigma_engine.artifacts.solution_matrix import SolutionMatrixArtifact, compute_quadrant


def test_accepts_a_complete_solution_matrix():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    assert len(artifact.solutions) == 3


def test_quadrant_boundaries_split_at_the_scale_midpoint():
    assert compute_quadrant(impact=5, effort=1) == "quick_win"
    assert compute_quadrant(impact=3, effort=3) == "major_project"  # midpoint counts as "high" on both axes
    assert compute_quadrant(impact=2, effort=2) == "fill_in"
    assert compute_quadrant(impact=1, effort=5) == "thankless_task"


def test_hand_checkable_weighted_totals_and_ranking():
    # cost(w=2)/speed(w=3): s-1 = 4*2+5*3=23, s-2 = 5*2+2*3=16 -- s-1 outranks
    # s-2 by weighted total despite s-2's higher impact/effort ratings.
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    by_id = {s.solution_id: s for s in artifact.scores.value}
    assert by_id["s-1"].weighted_total == 23.0
    assert by_id["s-2"].weighted_total == 16.0
    assert by_id["s-3"].weighted_total is None  # unscored
    ranked = artifact.ranked_fix_list.value.ranked
    assert [(r.solution_id, r.weighted_total) for r in ranked] == [("s-1", 23.0), ("s-2", 16.0)]
    assert [r.rank for r in ranked] == [1, 2]


def test_hand_checkable_unweighted_impact_desc_effort_asc_ranking():
    # No criteria at all -- s-a/s-b tie impact=5, s-a's lower effort (2<4)
    # ranks it first; s-c's impact=2 puts it last regardless of effort.
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=make_unweighted_solutions(), criteria=[]))
    ranked = artifact.ranked_fix_list.value.ranked
    assert [r.solution_id for r in ranked] == ["s-a", "s-b", "s-c"]
    assert all(r.weighted_total is None for r in ranked)


def test_unlinked_solution_excluded_from_ranked_list_and_flagged_separately():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    ranked_ids = {r.solution_id for r in artifact.ranked_fix_list.value.ranked}
    assert "s-3" not in ranked_ids
    unlinked = artifact.ranked_fix_list.value.unlinked
    assert [u.solution_id for u in unlinked] == ["s-3"]
    assert "not ranked" in unlinked[0].reason


def test_scores_and_ranked_fix_list_cannot_be_hand_typed():
    body = make_solution_matrix()
    body["scores"] = {"value": [], "provenance": {"input_hash": "x", "method": "tampered", "engine_version": "0", "assumptions_checked": [], "warnings": []}}
    body["ranked_fix_list"] = {"value": {"ranked": [], "unlinked": []}, "provenance": {"input_hash": "x", "method": "tampered", "engine_version": "0", "assumptions_checked": [], "warnings": []}}
    artifact = SolutionMatrixArtifact.model_validate(body)
    assert len(artifact.scores.value) == 3  # the real computed value, tampering had no effect
    assert len(artifact.ranked_fix_list.value.ranked) == 2


def test_empty_linked_cause_ids_is_a_legal_pending_state():
    solutions = make_solution_matrix_solutions()
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))
    assert artifact.solutions[2].linked_cause_ids == []  # s-3 -- saves fine, just unranked


def test_rejects_empty_linked_cause_id_string():
    solutions = make_solution_matrix_solutions()
    solutions[0]["linked_cause_ids"] = ["   "]
    with pytest.raises(ValidationError, match="blank"):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))


def test_rejects_duplicate_solution_ids():
    solutions = make_solution_matrix_solutions()
    solutions.append({**solutions[0], "solution_id": solutions[0]["solution_id"]})
    with pytest.raises(ValidationError, match="solution_id"):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))


def test_rejects_duplicate_criterion_ids():
    with pytest.raises(ValidationError, match="criterion_id"):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(criteria=[
            {"criterion_id": "cost", "name": "Cost", "weight": 1.0, "declared_at": "2026-08-07T00:00:00"},
            {"criterion_id": "cost", "name": "Cost again", "weight": 2.0, "declared_at": "2026-08-07T00:00:00"},
        ]))


def test_rejects_partial_criterion_scores():
    # Scored cost but not speed -- a partial set can't produce a
    # trustworthy weighted_total, so this is a schema-hard rejection.
    solutions = make_solution_matrix_solutions()
    solutions[0]["criterion_scores"] = [{"criterion_id": "cost", "score": 4, "scored_at": "2026-08-07T00:00:00"}]
    with pytest.raises(ValidationError, match="cover every declared criterion"):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))


def test_rejects_score_referencing_unknown_criterion():
    solutions = make_solution_matrix_solutions()
    solutions[0]["criterion_scores"] = [
        {"criterion_id": "cost", "score": 4, "scored_at": "2026-08-07T00:00:00"},
        {"criterion_id": "speed", "score": 5, "scored_at": "2026-08-07T00:00:00"},
        {"criterion_id": "nope", "score": 1, "scored_at": "2026-08-07T00:00:00"},
    ]
    with pytest.raises(ValidationError, match="undeclared criterion_id"):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))


def test_rejects_impact_and_effort_out_of_range():
    solutions = make_solution_matrix_solutions()
    solutions[0]["impact"] = 6
    with pytest.raises(ValidationError):
        SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))


def test_empty_solutions_list_is_legal():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=[], criteria=[]))
    assert artifact.ranked_fix_list.value.ranked == []
    assert artifact.ranked_fix_list.value.unlinked == []


def test_round_trip_via_model_dump():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    round_tripped = SolutionMatrixArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
