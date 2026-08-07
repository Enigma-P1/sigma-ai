"""T-01 prescore: routing-consistency (matrix §4a frozen rule).

Because artifacts/picker.py's schema validator already hard-rejects an
inconsistent route at construction, this check will always read "pass" for
any PickerArtifact that exists. It stays as a real, independently-callable
check anyway (not a stub returning a constant) so it keeps working the same
way if a future schema_version ever loosens that constructor-time rule, and
so `run_picker_prescore` matches the shape of every other tool's prescore
module for the /prescore/{tool_id} route.
"""

from __future__ import annotations

from ..artifacts.picker import PickerArtifact, route_is_consistent
from .common import PrescoreResult


def run_picker_prescore(artifact: PickerArtifact) -> list[PrescoreResult]:
    consistent = route_is_consistent(artifact.criteria_answers(), artifact.route)
    detail = (
        "route matches the five intake criteria per the frozen §4a rule"
        if consistent
        else f"route {artifact.route!r} is inconsistent with criteria {artifact.criteria_answers()}"
    )
    return [
        PrescoreResult(
            check_id="routing_consistency",
            tool_id="T-01",
            status="pass" if consistent else "flag",
            detail=detail,
        )
    ]
