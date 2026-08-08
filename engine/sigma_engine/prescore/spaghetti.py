"""T-07 prescore: R-MEA-03's rule-checkable lines -- calibration presence
plus a plausibility floor on the drawn line's pixel span, at least one
route with a real (3+-point) trace rather than a single straight hop,
frequencies present (schema-guaranteed, rendered anyway per T-06's
step_type_tag_present precedent), operator labels that aren't placeholder
text (R-DEF-04's owner-name blocklist, reused here), the observation-
window fields the rubric's own "Pre-scored in code" line names explicitly,
and a tamper-detection check mirroring T-06's bottleneck_fields_consistency.

Two rubric lines are deliberately left to the grader/advisor, matching
R-MEA-03's own "Judgment-only" line: whether the tracing reflects observed
movement, and whether the window is representative -- no schema field can
see either.
"""

from __future__ import annotations

import math

from ..artifacts.spaghetti import MIN_CALIBRATION_PIXEL_SPAN, SpaghettiArtifact, compute_spaghetti_metrics
from .common import PrescoreResult

MIN_ROUTE_POINTS_FOR_A_REAL_TRACE = 3

# Mirrors prescore/charter.py's PLACEHOLDER_OWNER_NAMES (R-DEF-04): the
# same narrow exact-match-on-trimmed-lowercase approach, plus a couple of
# operator-specific placeholders a color-indexed "who is this" field tends
# to attract from a default-filled form.
PLACEHOLDER_OPERATOR_NAMES = frozenset({"tbd", "team", "management", "n/a", "none", "unassigned", "operator", "unnamed"})


def run_spaghetti_prescore(artifact: SpaghettiArtifact) -> list[PrescoreResult]:
    return [
        _calibration_present(artifact),
        _calibration_span_plausible(artifact),
        _route_count_minimum(artifact),
        _route_with_real_trace(artifact),
        _frequencies_present(artifact),
        _operator_labels_non_placeholder(artifact),
        _observation_window_stated(artifact),
        _metrics_consistency(artifact),
    ]


def _calibration_present(artifact: SpaghettiArtifact) -> PrescoreResult:
    ok = artifact.calibration is not None
    return PrescoreResult(
        check_id="calibration_present", tool_id="T-07", status="pass" if ok else "flag",
        detail="calibration line drawn with a stated real length" if ok else "no calibration line drawn yet",
    )


def _calibration_span_plausible(artifact: SpaghettiArtifact) -> PrescoreResult:
    cal = artifact.calibration
    if cal is None:
        return PrescoreResult(
            check_id="calibration_span_plausible", tool_id="T-07", status="flag",
            detail="no calibration yet -- calibrate before this can be checked",
        )
    span = math.hypot(cal.point_b.x - cal.point_a.x, cal.point_b.y - cal.point_a.y)
    ok = span >= MIN_CALIBRATION_PIXEL_SPAN
    return PrescoreResult(
        check_id="calibration_span_plausible", tool_id="T-07", status="pass" if ok else "flag",
        detail=(
            f"{span:.1f}px calibration line" if ok
            else f"{span:.1f}px calibration line -- shorter than the {MIN_CALIBRATION_PIXEL_SPAN:.0f}px floor a trustworthy scale reference needs"
        ),
    )


def _route_count_minimum(artifact: SpaghettiArtifact) -> PrescoreResult:
    n = len(artifact.routes)
    return PrescoreResult(
        check_id="route_count_minimum", tool_id="T-07", status="pass" if n >= 1 else "flag",
        detail=f"{n} route(s)" if n >= 1 else "no routes traced yet",
    )


def _route_with_real_trace(artifact: SpaghettiArtifact) -> PrescoreResult:
    real = [r.route_id for r in artifact.routes if len(r.points) >= MIN_ROUTE_POINTS_FOR_A_REAL_TRACE]
    ok = len(real) >= 1
    return PrescoreResult(
        check_id="route_with_three_plus_points", tool_id="T-07", status="pass" if ok else "flag",
        detail=(
            f"{len(real)} route(s) with {MIN_ROUTE_POINTS_FOR_A_REAL_TRACE}+ points" if ok
            else f"every route is a straight 2-point hop -- trace at least one real path with {MIN_ROUTE_POINTS_FOR_A_REAL_TRACE}+ points"
        ),
    )


def _frequencies_present(artifact: SpaghettiArtifact) -> PrescoreResult:
    # Always true -- frequency_per_day is a required, gt=0 field (schema,
    # not prescore), so every saved route carries one by construction
    # (rubric's "trip count > 0" line). Rendered anyway, same reasoning as
    # T-06's step_type_tag_present.
    n = len(artifact.routes)
    return PrescoreResult(
        check_id="frequencies_present", tool_id="T-07", status="pass",
        detail=f"all {n} route(s) carry a frequency_per_day > 0" if n else "no routes yet to check",
    )


def _operator_labels_non_placeholder(artifact: SpaghettiArtifact) -> PrescoreResult:
    placeholders = [o.operator_id for o in artifact.operators if o.name.strip().lower() in PLACEHOLDER_OPERATOR_NAMES]
    return PrescoreResult(
        check_id="operator_labels_non_placeholder", tool_id="T-07", status="flag" if placeholders else "pass",
        detail=(
            f"operator(s) with a placeholder-looking name: {placeholders}" if placeholders
            else "every operator has a real name" if artifact.operators else "no operators defined yet"
        ),
    )


def _observation_window_stated(artifact: SpaghettiArtifact) -> PrescoreResult:
    w = artifact.observation_window
    missing = [name for name, val in (("when", w.when), ("duration", w.duration), ("shift", w.shift)) if not val.strip()]
    return PrescoreResult(
        check_id="observation_window_stated", tool_id="T-07", status="pass" if not missing else "flag",
        detail="when/duration/shift all stated" if not missing else f"observation window missing: {missing}",
    )


def _metrics_consistency(artifact: SpaghettiArtifact) -> PrescoreResult:
    """Mirrors prescore/process_map.py's _bottleneck_fields_consistency:
    the live validator always recomputes `metrics`, so this only catches a
    saved artifact file that was hand-edited on disk after the fact."""
    fresh = compute_spaghetti_metrics(artifact.calibration, artifact.operators, artifact.routes, artifact.walk_speed_override_per_minute)
    stored = artifact.metrics
    if stored is None and fresh is None:
        matches, detail = True, "no metrics expected yet (calibration missing or degenerate)"
    elif stored is None or fresh is None:
        matches, detail = False, "stored metrics presence doesn't match what the current inputs recompute to"
    else:
        matches = stored.value == fresh.value
        detail = "stored metrics match recomputed" if matches else "stored metrics != recomputed -- the file may have been hand-edited"
    return PrescoreResult(check_id="metrics_consistency", tool_id="T-07", status="pass" if matches else "flag", detail=detail)
