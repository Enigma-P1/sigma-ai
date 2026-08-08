"""T-16 prescore: the rubric R-ANA-03 rule-checkable lines the M3 brief
names. `ratings_in_range` is always "pass" -- artifacts/fmea.py's
Field(ge=1, le=10) on severity/occurrence/detection already makes an
out-of-range rating impossible to construct -- rendered anyway
(prescore/process_map.py's step_type_tag_present idiom) so the rubric line
shows on the strip as checked, not silently assumed. `high_severity_
without_action` is deliberately broader than artifacts/fmea.py's
blocking_flags: blocking_flags only fires on a safety/regulatory-worded
effect (the R-WRAP-03 project-close blocker), while this flags EVERY
severity-9/10 row left unaddressed -- "the exact misuse the tool warns
about" (rubric R-ANA-03's Fail line) whether or not the effect text reads
safety/regulatory, so it is scored hard_flag here even on rows
blocking_flags never touches.
"""

from __future__ import annotations

from ..artifacts.fmea import HIGH_SEVERITY, FmeaArtifact
from .common import PrescoreResult


def run_fmea_prescore(artifact: FmeaArtifact) -> list[PrescoreResult]:
    return [
        _mode_specificity(artifact),
        _ratings_in_range(artifact),
        _anchors_consulted_confirmed(artifact),
        _high_severity_without_action(artifact),
        _action_owners_present(artifact),
    ]


def _mode_specificity(artifact: FmeaArtifact) -> PrescoreResult:
    # Rubric R-ANA-03 Needs-work line: "modes sit at whole-process
    # altitude." A single word ("Delay", "Defect") can't name a specific
    # failure of a specific step -- a cheap, honest floor, not a claim that
    # a 2+ word mode is automatically specific enough (that's the
    # judgment-only spot-check).
    generic = [r.row_id for r in artifact.rows if len(r.failure_mode.strip().split()) < 2]
    ok = not generic
    return PrescoreResult(
        check_id="mode_specificity", tool_id="T-16", status="pass" if ok else "flag",
        detail=(
            "every failure mode is more than one word" if ok
            else f"single-word (whole-process-altitude) failure mode(s): {generic}"
        ),
    )


def _ratings_in_range(artifact: FmeaArtifact) -> PrescoreResult:
    n = len(artifact.rows)
    return PrescoreResult(
        check_id="ratings_in_range", tool_id="T-16", status="pass",
        detail=f"all {n} row(s) carry severity/occurrence/detection in 1-10 (schema-guaranteed)",
    )


def _anchors_consulted_confirmed(artifact: FmeaArtifact) -> PrescoreResult:
    missing = [r.row_id for r in artifact.rows if not r.anchors_consulted]
    ok = not missing
    return PrescoreResult(
        check_id="anchors_consulted_confirmed", tool_id="T-16", status="pass" if ok else "flag",
        detail=(
            "every row confirms the anchor scale was consulted" if ok
            else f"row(s) rated without the anchor text confirmed shown: {missing}"
        ),
    )


def _high_severity_without_action(artifact: FmeaArtifact) -> PrescoreResult:
    bad = [r.row_id for r in artifact.rows if r.severity in HIGH_SEVERITY and not r.action.strip()]
    ok = not bad
    return PrescoreResult(
        check_id="high_severity_without_action", tool_id="T-16", status="pass" if ok else "hard_flag",
        detail=(
            "no severity-9/10 row is left without an action" if ok
            else f"severity-9/10 row(s) with no action -- unaddressed, the exact misuse the tool warns about: {bad}"
        ),
    )


def _action_owners_present(artifact: FmeaArtifact) -> PrescoreResult:
    missing = [r.row_id for r in artifact.rows if r.action.strip() and not r.action_owner.strip()]
    ok = not missing
    return PrescoreResult(
        check_id="action_owners_present", tool_id="T-16", status="pass" if ok else "flag",
        detail=(
            "every recorded action has a named owner" if ok
            else f"row(s) with an action but no owner: {missing}"
        ),
    )
