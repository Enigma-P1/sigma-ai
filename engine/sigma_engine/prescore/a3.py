"""T-25 prescore: rubric R-WRAP-01/02/03's rule-checkable lines.
`close_blocked_surfaced` renders `closure.close_check` (a3.py's reuse of
fmea.py's blocking_flags) as the task brief's own "close_blocked
surfaced" prescore line."""

from __future__ import annotations

from ..artifacts.a3 import A3Artifact
from .common import PrescoreResult


def run_a3_prescore(artifact: A3Artifact) -> list[PrescoreResult]:
    return [
        _panels_seeded_or_narrated(artifact),
        _realized_benefits_present(artifact),
        _tollgates_answered(artifact),
        _lessons_substantive(artifact),
        _open_items_have_owners(artifact),
        _close_blocked_surfaced(artifact),
    ]


def _panels_seeded_or_narrated(artifact: A3Artifact) -> PrescoreResult:
    empty = [p.panel for p in artifact.panels if p.seeded_from is None and not p.narrative.strip()]
    ok = not empty
    return PrescoreResult(
        check_id="panels_seeded_or_narrated", tool_id="T-25", status="pass" if ok else "hard_flag",
        detail=(
            "every panel is seeded from an artifact or carries narrative text" if ok
            else f"panel(s) with neither a seed nor any narrative -- the story has a gap (R-WRAP-01 #2): {empty}"
        ),
    )


def _realized_benefits_present(artifact: A3Artifact) -> PrescoreResult:
    rb = artifact.realized_benefits
    ok = rb is not None and rb.window.strip() != "" and rb.copq_rerun_artifact_id.strip() != ""
    return PrescoreResult(
        check_id="realized_benefits_present", tool_id="T-25", status="pass" if ok else "flag",
        detail=(
            "the realized-benefits panel names its COPQ re-run and a stated window" if ok
            else "the realized-benefits panel is missing its COPQ re-run reference or stated window (R-WRAP-02 #1)"
        ),
    )


def _tollgates_answered(artifact: A3Artifact) -> PrescoreResult:
    incomplete = []
    for tg in artifact.tollgates:
        answered_ids = {a.question_id for a in tg.answers if a.answered}
        if len(answered_ids) < len(tg.questions):
            incomplete.append(tg.phase)
    ok = not incomplete
    return PrescoreResult(
        check_id="tollgates_answered", tool_id="T-25", status="pass" if ok else "flag",
        detail=(
            "every phase's tollgate checklist is fully answered" if ok
            else f"phase(s) with an unanswered tollgate question: {incomplete}"
        ),
    )


def _lessons_substantive(artifact: A3Artifact) -> PrescoreResult:
    lessons = artifact.closure.lessons
    has_went_wrong = any(l.went_wrong for l in lessons)
    ok = len(lessons) >= 2 and has_went_wrong
    return PrescoreResult(
        check_id="lessons_substantive", tool_id="T-25", status="pass" if ok else "flag",
        detail=(
            "at least two lessons recorded, including something that went wrong" if ok
            else f"{len(lessons)} lesson(s) recorded, a went-wrong lesson present={has_went_wrong} -- a lessons "
            "panel of only wins is not lessons (R-WRAP-03 #2)"
        ),
    )


def _open_items_have_owners(artifact: A3Artifact) -> PrescoreResult:
    missing = [i.item_id for i in artifact.closure.open_items if not i.owner.strip()]
    ok = not missing
    return PrescoreResult(
        check_id="open_items_have_owners", tool_id="T-25", status="pass" if ok else "flag",
        detail=(
            "every open item has a named owner" if ok else f"open item(s) with no owner (R-WRAP-03 #3): {missing}"
        ),
    )


def _close_blocked_surfaced(artifact: A3Artifact) -> PrescoreResult:
    assert artifact.closure.close_check is not None
    blocked = artifact.closure.close_check.value.close_blocked
    return PrescoreResult(
        check_id="close_blocked_surfaced", tool_id="T-25", status="pass" if not blocked else "hard_flag",
        detail=artifact.closure.close_check.value.reason,
    )
