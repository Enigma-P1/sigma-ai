"""T-18 prescore: rubric R-IMP-01's rule-checkable lines -- which solutions
never made it into the ranked list and why (unlinked_solution_flags), that
the ranked list actually has something in it (ranked_list_exists), and a
recompute-and-compare tamper guard on the artifact's own quadrant/ranking
math (quadrant_vs_rank_consistency) -- prescore/hypothesis.py's
route_tamper_check idiom applied here: always "pass" for a freshly-
validated artifact (SolutionMatrixArtifact._recompute already guarantees
it), but kept live in code rather than hand-waved, same stance
prescore/fishbone.py's verified_causes_have_evidence documents for its own
schema-guaranteed check.
"""

from __future__ import annotations

from ..artifacts.solution_matrix import SolutionMatrixArtifact, compute_quadrant, compute_ranked_fix_list, compute_solution_scores
from .common import PrescoreResult


def run_solution_matrix_prescore(artifact: SolutionMatrixArtifact) -> list[PrescoreResult]:
    return [
        _unlinked_solution_flags(artifact),
        _ranked_list_exists(artifact),
        _quadrant_vs_rank_consistency(artifact),
    ]


def _unlinked_solution_flags(artifact: SolutionMatrixArtifact) -> PrescoreResult:
    unlinked = artifact.ranked_fix_list.value.unlinked
    return PrescoreResult(
        check_id="unlinked_solution_flags", tool_id="T-18", status="pass" if not unlinked else "flag",
        detail=(
            "every solution links to at least one cause" if not unlinked
            else f"{len(unlinked)} solution(s) not linked to any cause, excluded from the ranked list: "
            f"{[u.solution_id for u in unlinked]} (rubric R-IMP-01 #2)"
        ),
    )


def _ranked_list_exists(artifact: SolutionMatrixArtifact) -> PrescoreResult:
    ranked = artifact.ranked_fix_list.value.ranked
    return PrescoreResult(
        check_id="ranked_list_exists", tool_id="T-18", status="pass" if ranked else "flag",
        detail=(
            f"{len(ranked)} linked solution(s) ranked -- #1 is {ranked[0].name!r}" if ranked
            else "nothing ranked yet -- no solution has been linked to a cause (PLAN §4.1's ranked fix list is empty)"
        ),
    )


def _quadrant_vs_rank_consistency(artifact: SolutionMatrixArtifact) -> PrescoreResult:
    # Always "pass" for a freshly-validated artifact -- see module
    # docstring. Recomputed from the raw solutions/criteria fields (not
    # read back off artifact.scores/ranked_fix_list) so this is a real
    # tamper guard against a hand-edited on-disk JSON, not a tautology.
    recomputed_scores = compute_solution_scores(artifact.solutions, artifact.criteria).value
    recomputed_ranked = compute_ranked_fix_list(artifact.solutions, recomputed_scores).value
    scores_match = recomputed_scores == artifact.scores.value
    ranked_match = recomputed_ranked == artifact.ranked_fix_list.value
    quadrants_match = all(compute_quadrant(s.impact, s.effort) == next(sc.quadrant for sc in recomputed_scores if sc.solution_id == s.solution_id) for s in artifact.solutions)
    ok = scores_match and ranked_match and quadrants_match
    return PrescoreResult(
        check_id="quadrant_vs_rank_consistency", tool_id="T-18", status="pass" if ok else "hard_flag",
        detail=(
            "stored quadrants, weighted totals, and ranking all re-derive from the stored solutions/criteria"
            if ok else "stored scores/ranking do not match a fresh recomputation -- the file may have been hand-edited"
        ),
    )
