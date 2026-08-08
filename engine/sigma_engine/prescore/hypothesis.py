"""T-17 prescore: rubric R-ANA-04's rule-checkable lines --
  - routing inputs recorded (routing_recorded)
  - route-tamper check: the stored route re-derives from the stored
    question (route_tamper_check) -- mirrors prescore/msa.py's
    result_matches_inputs safety net for a hand-edited on-disk JSON file
    (the GET .../artifacts/{id} path returns the stored dict verbatim,
    without re-running HypothesisRunArtifact's validator).
  - declared-primary flag present (declared_primary_present)
  - exit honored: no result stored past a raised ROUTING exit
    (exit_honored) -- EXIT-13 is excluded from this check by design: it
    is a post-hoc annotation on a *successful* ANOVA result
    (hypothesis_common.RouteName's module note), not a routing refusal,
    so a stored result with `exit13` set is not "past an exit" here.
  - count of tests run vs declared primary (tests_run_vs_declared_primary)
    -- EXIT-12's multiplicity discipline, visible in the stored artifact.
"""

from __future__ import annotations

from ..artifacts.hypothesis import HypothesisRunArtifact
from ..stats.hypothesis_runner import run_hypothesis
from .common import PrescoreResult


def run_hypothesis_prescore(artifact: HypothesisRunArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    if artifact.routing is None:
        # _recompute always sets this on a valid artifact -- stay honest
        # about the unexpected state rather than crash the route.
        results.append(PrescoreResult(check_id="routing_recorded", tool_id="T-17", status="flag", detail="no routing decision on the artifact"))
        return results

    exit_id = artifact.routing.exit.exit_id if artifact.routing.exit else None
    results.append(PrescoreResult(
        check_id="routing_recorded", tool_id="T-17", status="pass",
        detail=f"route={artifact.routing.route!r}, exit={exit_id!r}, {len(artifact.routing.decision_path)} decision-path node(s) recorded",
    ))

    recomputed = run_hypothesis(artifact.question)
    recomputed_exit_id = recomputed.routing.exit.exit_id if recomputed.routing.exit else None
    route_matches = recomputed.routing.route == artifact.routing.route and recomputed_exit_id == exit_id
    results.append(PrescoreResult(
        check_id="route_tamper_check", tool_id="T-17", status="pass" if route_matches else "flag",
        detail=(
            "stored route/exit re-derives from the stored question" if route_matches
            else f"stored route={artifact.routing.route!r}/exit={exit_id!r} != recomputed route="
            f"{recomputed.routing.route!r}/exit={recomputed_exit_id!r} -- the file may have been hand-edited"
        ),
    ))

    results.append(PrescoreResult(
        check_id="declared_primary_present", tool_id="T-17", status="pass", detail=f"declared_primary={artifact.declared_primary}",
    ))

    exit_honored = not (artifact.routing.exit is not None and artifact.result is not None)
    results.append(PrescoreResult(
        check_id="exit_honored", tool_id="T-17", status="pass" if exit_honored else "flag",
        detail=(
            "no result stored past a raised routing exit" if exit_honored
            else f"a result is stored despite raised routing exit {exit_id!r} -- an EXIT-06..15 gate was pushed past"
        ),
    ))

    within_declared = artifact.question.tests_run_including_this_one <= artifact.question.comparisons_declared
    results.append(PrescoreResult(
        check_id="tests_run_vs_declared_primary", tool_id="T-17", status="pass" if within_declared else "flag",
        detail=(
            f"tests_run_including_this_one={artifact.question.tests_run_including_this_one} <= "
            f"comparisons_declared={artifact.question.comparisons_declared}" if within_declared
            else f"tests_run_including_this_one={artifact.question.tests_run_including_this_one} > "
            f"comparisons_declared={artifact.question.comparisons_declared} -- EXIT-12 should have fired"
        ),
    ))

    return results
