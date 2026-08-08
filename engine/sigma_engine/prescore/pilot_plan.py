"""T-19 prescore: rubric R-IMP-02's rule-checkable lines beyond the
schema-hard one-change rule (EXIT-10, artifacts/pilot_plan.py) -- the
pre-declaration honesty note on the success threshold (advisory only,
field-presence for now), a substance heuristic on the falsification line
(length + not-just-a-negation), and confounder-checklist completeness
(every note actually filled in, not just every box structurally present --
the schema already guarantees the five answers exist; this checks they
say something)."""

from __future__ import annotations

import re

from ..artifacts.pilot_plan import PilotPlanArtifact
from .common import PrescoreResult

# Rubric R-IMP-02's own example of a non-substantive falsification line
# ("if it doesn't work") -- one reviewable pattern, same idiom as
# prescore/charter.py's SOLUTION_LANGUAGE_KEYWORDS.
_TRIVIAL_FALSIFICATION_PATTERN = re.compile(
    r"^(if\s+)?(it|this)\s+(doesn'?t|does\s+not|won'?t|will\s+not)\s+work\.?$", re.IGNORECASE,
)
MIN_FALSIFICATION_LENGTH = 25


def _is_substantive_falsification(text: str) -> bool:
    t = text.strip()
    return len(t) >= MIN_FALSIFICATION_LENGTH and not _TRIVIAL_FALSIFICATION_PATTERN.match(t)


def run_pilot_plan_prescore(artifact: PilotPlanArtifact) -> list[PrescoreResult]:
    return [
        _threshold_before_data_advisory(artifact),
        _falsification_substance_heuristic(artifact),
        _checklist_completeness(artifact),
    ]


def _threshold_before_data_advisory(artifact: PilotPlanArtifact) -> PrescoreResult:
    # Advisory only, by rubric design (R-IMP-02's own pre-score note): a
    # record-entry timestamp shows entry order, never observation order --
    # a spreadsheet defeats it. This engine has no pilot dataset linked to
    # a PilotPlanArtifact yet (that arrives with T-20's before/after
    # proof), so today this is a field-presence check; once a linked
    # dataset exists the same check_id compares declared_at against the
    # dataset's earliest observation timestamp instead.
    declared_at = artifact.success_threshold.declared_at
    return PrescoreResult(
        check_id="threshold_before_data_advisory", tool_id="T-19", status="pass",
        detail=(
            f"success threshold declared at {declared_at} -- entry order only, not observation order "
            "(advisory: no linked pilot dataset to compare against yet; re-checked for real once T-20 runs)"
        ),
    )


def _falsification_substance_heuristic(artifact: PilotPlanArtifact) -> PrescoreResult:
    ok = _is_substantive_falsification(artifact.falsification_line)
    return PrescoreResult(
        check_id="falsification_substance_heuristic", tool_id="T-19", status="pass" if ok else "flag",
        detail=(
            "falsification line reads as substantive" if ok
            else f"falsification line is too short or reads as a bare negation (\"if it doesn't work\") -- "
            f"needs at least {MIN_FALSIFICATION_LENGTH} characters naming what specifically would count as failure"
        ),
    )


def _checklist_completeness(artifact: PilotPlanArtifact) -> PrescoreResult:
    cc = artifact.confounder_checklist
    entries = {"staffing": cc.staffing, "season": cc.season, "demand": cc.demand, "measurement": cc.measurement, "other": cc.other}
    blank = [name for name, ans in entries.items() if not ans.note.strip()]
    return PrescoreResult(
        check_id="checklist_completeness", tool_id="T-19", status="pass" if not blank else "flag",
        detail="all five confounder notes are filled in" if not blank else f"confounder note(s) left blank: {blank}",
    )
