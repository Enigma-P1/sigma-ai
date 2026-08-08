"""T-06 prescore: the rubric R-MEA-01/02 pre-scorable lines this milestone
builds (M2 brief) -- content-completeness flags for fields the schema
deliberately leaves loose (Lane.owner, ProcessStepModel.reason,
WasteEntry.note; see artifacts/process_map.py's docstring), plus structural
counts and the bottleneck hand-edited-JSON safety net (mirrors
prescore/copq.py's total_matches_rows / prescore/msa.py's
result_matches_inputs -- the live validator always recomputes `bottleneck`,
so this only catches a saved file that was hand-edited after the fact).

Two checks beyond the M2 brief's explicit list are added because the
rubric names them directly and they cost nothing extra to compute from the
artifact alone: lane_count_minimum (R-MEA-01's "≥2 lanes") and
step_type_tag_present (R-MEA-02's "tag present on 100% of steps" -- always
true by schema construction since step_type is a required field, so this
renders as a visible pass rather than an unstated assumption). Two rubric
lines are deliberately deferred -- see the build report: SIPOC-boundary
matching and the defect-metric/no-rework-loop advisory both need another
artifact's data, and prescore functions in this milestone take only the
one artifact being scored (registry.py's PRESCORE_REGISTRY shape, matching
every other tool's prescore module); an NVA time/step-share rollup isn't
in the M2 schema brief's field list.
"""

from __future__ import annotations

from ..artifacts.process_map import ProcessMapArtifact, compute_bottleneck
from .common import PrescoreResult

MIN_LANES = 2
MIN_STEPS = 3
TAGGED_TYPES = {"value_add", "non_value_add"}


def run_process_map_prescore(artifact: ProcessMapArtifact) -> list[PrescoreResult]:
    return [
        _lane_count(artifact),
        _lane_owner_present(artifact),
        _step_count(artifact),
        _step_type_tag_present(artifact),
        _reason_required_for_tagged_steps(artifact),
        _times_present_half(artifact),
        _orphan_steps(artifact),
        _waste_notes_present(artifact),
        _bottleneck_fields_consistency(artifact),
    ]


def _lane_count(artifact: ProcessMapArtifact) -> PrescoreResult:
    n = len(artifact.lanes)
    ok = n >= MIN_LANES
    return PrescoreResult(
        check_id="lane_count_minimum", tool_id="T-06", status="pass" if ok else "flag",
        detail=f"{n} lane(s)" + ("" if ok else f" -- fewer than the {MIN_LANES} a swimlane map needs to show a handoff"),
    )


def _lane_owner_present(artifact: ProcessMapArtifact) -> PrescoreResult:
    blank = [l.lane_id for l in artifact.lanes if not l.owner.strip()]
    return PrescoreResult(
        check_id="lane_owner_present", tool_id="T-06", status="pass" if not blank else "flag",
        detail="every lane has a named owner" if not blank else f"lane(s) with no owner: {blank}",
    )


def _step_count(artifact: ProcessMapArtifact) -> PrescoreResult:
    n = len(artifact.steps)
    ok = n >= MIN_STEPS
    return PrescoreResult(
        check_id="step_count_minimum", tool_id="T-06", status="pass" if ok else "flag",
        detail=f"{n} step(s)" + ("" if ok else f" -- fewer than the {MIN_STEPS}-step floor for a real process"),
    )


def _step_type_tag_present(artifact: ProcessMapArtifact) -> PrescoreResult:
    # Always true -- step_type is a required field (schema, not prescore),
    # so every saved step is tagged by construction (rubric R-MEA-02: "tag
    # present on 100% of steps"). Rendered anyway so the strip shows this
    # rubric line as checked, not silently assumed.
    n = len(artifact.steps)
    return PrescoreResult(
        check_id="step_type_tag_present", tool_id="T-06", status="pass",
        detail=f"all {n} step(s) carry a value_add/non_value_add/enabling tag",
    )


def _reason_required_for_tagged_steps(artifact: ProcessMapArtifact) -> PrescoreResult:
    missing = [s.step_id for s in artifact.steps if s.step_type in TAGGED_TYPES and not s.reason.strip()]
    return PrescoreResult(
        check_id="reason_required_for_tagged_steps", tool_id="T-06", status="pass" if not missing else "flag",
        detail=(
            "every value-add/non-value-add step has a reason" if not missing
            else f"value-add/non-value-add step(s) with no reason: {missing}"
        ),
    )


def _times_present_half(artifact: ProcessMapArtifact) -> PrescoreResult:
    n = len(artifact.steps)
    timed = sum(1 for s in artifact.steps if s.time_minutes is not None)
    ok = n > 0 and timed >= n / 2
    return PrescoreResult(
        check_id="times_present_half", tool_id="T-06", status="pass" if ok else "flag",
        detail=f"{timed}/{n} steps carry a time" + ("" if ok else " -- fewer than half"),
    )


def _orphan_steps(artifact: ProcessMapArtifact) -> PrescoreResult:
    touched = {c.from_step for c in artifact.connectors} | {c.to_step for c in artifact.connectors}
    orphans = [s.step_id for s in artifact.steps if s.step_id not in touched]
    return PrescoreResult(
        check_id="orphan_steps", tool_id="T-06", status="pass" if not orphans else "flag",
        detail="every step has at least one connector" if not orphans else f"step(s) with no connector: {orphans}",
    )


def _waste_notes_present(artifact: ProcessMapArtifact) -> PrescoreResult:
    missing = [(s.step_id, w.waste_id) for s in artifact.steps for w in s.wastes if not w.note.strip()]
    return PrescoreResult(
        check_id="waste_notes_present", tool_id="T-06", status="pass" if not missing else "flag",
        detail=(
            "every checked waste has a concrete note" if not missing
            else f"checked waste(s) with no note (step, waste_id): {missing}"
        ),
    )


def _bottleneck_fields_consistency(artifact: ProcessMapArtifact) -> PrescoreResult:
    """Mirrors prescore/copq.py's total_matches_rows: the live validator
    always recomputes `bottleneck`, so this only catches a saved artifact
    file that was hand-edited on disk after the fact (routes/artifacts.py's
    GET path returns the stored dict verbatim, unvalidated)."""
    recomputed = compute_bottleneck(artifact.steps, artifact.demand)
    stored, fresh = artifact.bottleneck, recomputed
    if stored is None and fresh is None:
        matches, detail = True, "no bottleneck expected yet (demand incomplete or no step has a time)"
    elif stored is None or fresh is None:
        matches, detail = False, "stored bottleneck presence doesn't match what the current steps/demand recompute to"
    else:
        matches = stored.value == fresh.value
        detail = (
            "stored bottleneck matches recomputed" if matches
            else f"stored {stored.value!r} != recomputed {fresh.value!r} -- the file may have been hand-edited"
        )
    return PrescoreResult(check_id="bottleneck_fields_consistency", tool_id="T-06", status="pass" if matches else "flag", detail=detail)
