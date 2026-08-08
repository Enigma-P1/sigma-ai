"""T-23 prescore: rubric R-CTL-05's rule-checkable lines.

`uniform_scores_honesty` is the task brief's "advisory" flag rendered at
this engine's "flag" (needs-work) tier -- prescore/common.py's Status has
no separate advisory tier, and rubric R-CTL-05's own Needs-work line ("all
categories scored identical") already places this exactly there, not at
Fail (R-CTL-05 carries no Fail/invalidates condition at all: "5S theater
degrades sustainment but fakes no project number").
"""

from __future__ import annotations

from ..artifacts.five_s import FiveSArtifact
from .common import PrescoreResult


def run_five_s_prescore(artifact: FiveSArtifact) -> list[PrescoreResult]:
    return [
        _scores_in_range(artifact),
        _photos_present(artifact),
        _uniform_scores_honesty(artifact),
        _recurrence_present(artifact),
        _min_category_action_present(artifact),
    ]


def _scores_in_range(artifact: FiveSArtifact) -> PrescoreResult:
    n = sum(len(r.scores) for r in artifact.rounds)
    return PrescoreResult(
        check_id="scores_in_range", tool_id="T-23", status="pass",
        detail=f"all {n} category score(s) across {len(artifact.rounds)} round(s) are 0-5 (schema-guaranteed)",
    )


def _photos_present(artifact: FiveSArtifact) -> PrescoreResult:
    missing = [r.round_id for r in artifact.rounds if not r.photos]
    ok = not missing
    return PrescoreResult(
        check_id="photos_present", tool_id="T-23", status="pass" if ok else "flag",
        detail=(
            "every round carries at least one photo" if ok
            else f"round(s) with no photo attached -- physical state should carry the score (R-CTL-05 #1): {missing}"
        ),
    )


def _uniform_scores_honesty(artifact: FiveSArtifact) -> PrescoreResult:
    uniform = [r.round_id for r in artifact.rounds if len({s.score for s in r.scores}) == 1]
    ok = not uniform
    return PrescoreResult(
        check_id="uniform_scores_honesty", tool_id="T-23", status="pass" if ok else "flag",
        detail=(
            "no round scores every category identically" if ok
            else f"round(s) scoring all five categories identically -- advisory honesty check, spot-check against "
            f"the photos (R-CTL-05 Needs-work line): {uniform}"
        ),
    )


def _recurrence_present(artifact: FiveSArtifact) -> PrescoreResult:
    ok = artifact.schedule is not None or len(artifact.rounds) >= 2
    return PrescoreResult(
        check_id="recurrence_present", tool_id="T-23", status="pass" if ok else "flag",
        detail=(
            "a recurrence schedule or >=2 trend points exist" if ok
            else "one audit, no schedule, and no second round yet -- recurrence is not yet real (R-CTL-05 #3)"
        ),
    )


def _min_category_action_present(artifact: FiveSArtifact) -> PrescoreResult:
    missing = [r.round_id for r in artifact.rounds if not r.improvement_action.strip()]
    ok = not missing
    return PrescoreResult(
        check_id="min_category_action_present", tool_id="T-23", status="pass" if ok else "flag",
        detail=(
            "every round's lowest-scoring category carries an action" if ok
            else f"round(s) with no action recorded for the lowest-scoring category: {missing}"
        ),
    )
