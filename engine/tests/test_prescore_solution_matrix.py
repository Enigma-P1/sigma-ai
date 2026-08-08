"""Prescore tests for T-18: each of the 3 checks, driven to both pass and
flag at least once."""

from factories import make_solution_matrix, make_solution_matrix_solutions, make_unweighted_solutions
from sigma_engine.artifacts.solution_matrix import SolutionMatrixArtifact
from sigma_engine.prescore.solution_matrix import run_solution_matrix_prescore

EXPECTED_CHECK_IDS = {"unlinked_solution_flags", "ranked_list_exists", "quadrant_vs_rank_consistency"}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_default_fixture_flags_the_deliberately_unlinked_solution():
    # make_solution_matrix()'s s-3 is deliberately unlinked -- this is the
    # flag fixture for unlinked_solution_flags; every other check passes.
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    assert results["unlinked_solution_flags"].status == "flag"
    assert "s-3" in results["unlinked_solution_flags"].detail
    assert results["ranked_list_exists"].status == "pass"
    assert results["quadrant_vs_rank_consistency"].status == "pass"


def test_unlinked_solution_flags_passes_once_every_solution_is_linked():
    solutions = make_solution_matrix_solutions()
    solutions[2]["linked_cause_ids"] = ["c-3"]  # link the formerly-unlinked s-3
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert results["unlinked_solution_flags"].status == "pass"


def test_ranked_list_exists_flags_when_nothing_is_linked_yet():
    solutions = make_solution_matrix_solutions()
    for s in solutions:
        s["linked_cause_ids"] = []
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=solutions))
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert results["ranked_list_exists"].status == "flag"
    assert "nothing ranked" in results["ranked_list_exists"].detail


def test_ranked_list_exists_passes_and_names_the_top_pick():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert results["ranked_list_exists"].status == "pass"
    assert "s-1" in results["ranked_list_exists"].detail or "Add fixture" in results["ranked_list_exists"].detail


def test_quadrant_vs_rank_consistency_passes_on_the_unweighted_fixture_too():
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix(solutions=make_unweighted_solutions(), criteria=[]))
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert results["quadrant_vs_rank_consistency"].status == "pass"


def test_quadrant_vs_rank_consistency_flags_a_tampered_computed_field():
    # Bypass the schema's own unconditional recompute by hand-constructing
    # an artifact object, then mutating scores.value in place -- exactly
    # the "hand-edited on-disk JSON reloaded elsewhere" scenario the
    # tamper guard exists for (Computed is frozen at the top level, but
    # nothing stops mutating a plain list's contents in place).
    artifact = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    artifact.scores.value[0].weighted_total = 999.0
    results = _by_id(run_solution_matrix_prescore(artifact))
    assert results["quadrant_vs_rank_consistency"].status == "hard_flag"
    assert "hand-edited" in results["quadrant_vs_rank_consistency"].detail
