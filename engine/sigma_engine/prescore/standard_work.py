"""T-24 prescore: rubric R-CTL-06's rule-checkable lines. `_step_schema_
present`/`_metadata_present` re-affirm what the schema already guarantees
(fmea.py's `_ratings_in_range` idiom) so the rubric line shows on the
prescore strip as checked, not silently assumed."""

from __future__ import annotations

import re

from ..artifacts.standard_work import StandardWorkArtifact
from .common import PrescoreResult

# Rubric R-CTL-06 Needs-work line: "steps are written as policy ('ensure
# quality') instead of actions" -- a heuristic keyword screen, the same
# "one reviewable list" idiom as prescore/charter.py's solution-language
# scan and fmea.py's safety/regulatory keyword scan.
POLICY_LANGUAGE_KEYWORDS: tuple[str, ...] = ("ensure", "make sure", "be sure", "should", "properly", "as needed", "appropriately")
_POLICY_PATTERN = re.compile(r"\b(" + "|".join(re.escape(k) for k in POLICY_LANGUAGE_KEYWORDS) + r")\b", re.IGNORECASE)


def run_standard_work_prescore(artifact: StandardWorkArtifact) -> list[PrescoreResult]:
    return [
        _step_schema_present(artifact),
        _metadata_present(artifact),
        _changed_steps_marked(artifact),
        _steps_read_as_actions(artifact),
    ]


def _step_schema_present(artifact: StandardWorkArtifact) -> PrescoreResult:
    return PrescoreResult(
        check_id="step_schema_present", tool_id="T-24", status="pass",
        detail=f"all {len(artifact.steps)} step(s) carry an action and a standard (schema-guaranteed)",
    )


def _metadata_present(artifact: StandardWorkArtifact) -> PrescoreResult:
    return PrescoreResult(
        check_id="metadata_present", tool_id="T-24", status="pass",
        detail=f"version {artifact.version}, owner {artifact.owner!r}, effective {artifact.effective_date} (schema-guaranteed)",
    )


def _changed_steps_marked(artifact: StandardWorkArtifact) -> PrescoreResult:
    if not artifact.supersedes:
        return PrescoreResult(
            check_id="changed_steps_marked", tool_id="T-24", status="pass",
            detail="no prior instruction named -- change-marking not applicable yet",
        )
    ok = any(s.changed_from_prior for s in artifact.steps)
    return PrescoreResult(
        check_id="changed_steps_marked", tool_id="T-24", status="pass" if ok else "flag",
        detail=(
            "at least one step is marked changed from the prior method" if ok
            else f"supersedes {artifact.supersedes!r} but no step is marked changed -- the changed points aren't highlighted (R-CTL-06 Needs-work line)"
        ),
    )


def _steps_read_as_actions(artifact: StandardWorkArtifact) -> PrescoreResult:
    policy = [s.step_id for s in artifact.steps if _POLICY_PATTERN.search(s.action)]
    ok = not policy
    return PrescoreResult(
        check_id="steps_read_as_actions", tool_id="T-24", status="pass" if ok else "flag",
        detail=(
            "every step reads as an action" if ok
            else f"step(s) written as policy rather than an action (R-CTL-06 Needs-work line, e.g. 'ensure quality'): {policy}"
        ),
    )
