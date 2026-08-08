"""T-21 prescore: rubric R-CTL-01/02's rule-checkable lines.

  - family_matches_data: chart_type matches the selector's data_shape
    (schema already guarantees this at construction -- re-affirmed here
    as a visible check, same "re-affirm what the schema enforces" move
    prescore/hypothesis.py's route_tamper_check makes for T-17's route).
  - frozen_limits_present_before_signals (R-CTL-01 #2/#3): a chart with
    signals but no frozen baseline can't happen by construction (see
    control_chart.py's _compute_signals: signals stays None until a
    baseline exists) -- checked here as a visible guarantee, not a gap.
  - never_armed flag (R-CTL-02's own pre-score line: "a missing signal
    log because charting never ran is a Fail, not a thin Pass") --
    hard_flag, not a soft flag, when frozen but never armed.
  - signal_acknowledgment_completeness: every fired signal carries an
    acknowledgment (R-CTL-02 #1/#3 -- "no repeated signal left
    unacknowledged").
  - recalculation_log_has_reasons: every log entry's reason is non-blank
    (schema already guarantees this; re-affirmed the same way as above).
"""

from __future__ import annotations

from ..artifacts.control_chart import ControlChartArtifact
from .common import PrescoreResult


def run_control_chart_prescore(artifact: ControlChartArtifact) -> list[PrescoreResult]:
    return [
        _family_matches_data(artifact),
        _frozen_limits_present_before_signals(artifact),
        _never_armed(artifact),
        _signal_acknowledgment_completeness(artifact),
        _recalculation_log_has_reasons(artifact),
    ]


def _family_matches_data(artifact: ControlChartArtifact) -> PrescoreResult:
    expected = "imr" if artifact.selector.data_shape == "continuous" else "p"
    ok = artifact.chart_type == expected
    return PrescoreResult(
        check_id="family_matches_data", tool_id="T-21", status="pass" if ok else "hard_flag",
        detail=(
            f"chart_type={artifact.chart_type!r} matches the selector (data_shape={artifact.selector.data_shape!r})"
            if ok else f"chart_type={artifact.chart_type!r} does not match data_shape={artifact.selector.data_shape!r}"
        ),
    )


def _frozen_limits_present_before_signals(artifact: ControlChartArtifact) -> PrescoreResult:
    frozen = artifact.imr_baseline is not None or artifact.p_baseline is not None
    has_signals_field = artifact.signals is not None
    ok = frozen or not has_signals_field
    return PrescoreResult(
        check_id="frozen_limits_present_before_signals", tool_id="T-21", status="pass" if ok else "hard_flag",
        detail=(
            f"limits frozen at {artifact.frozen_at}" if frozen
            else "no frozen limits yet -- chart runs diagnostically, no signal log (as expected)" if ok
            else "signals present with no frozen baseline -- should be unreachable"
        ),
    )


def _never_armed(artifact: ControlChartArtifact) -> PrescoreResult:
    frozen = artifact.imr_baseline is not None or artifact.p_baseline is not None
    if not frozen:
        return PrescoreResult(check_id="never_armed", tool_id="T-21", status="pass", detail="not frozen yet -- armed state not yet applicable")
    armed = artifact.armed.monitoring_started
    return PrescoreResult(
        check_id="never_armed", tool_id="T-21", status="pass" if armed else "hard_flag",
        detail=(
            "monitoring is armed (armed.monitoring_started=true)" if armed
            else "limits are frozen but monitoring was never armed -- a missing signal log because charting never "
            "ran is a Fail, not a thin Pass (rubric R-CTL-02)"
        ),
    )


def _signal_acknowledgment_completeness(artifact: ControlChartArtifact) -> PrescoreResult:
    if artifact.signals is None or not artifact.signals.value:
        return PrescoreResult(check_id="signal_acknowledgment_completeness", tool_id="T-21", status="pass", detail="no signals fired yet")
    unacknowledged = [ts for ts in artifact.signals.value if not ts.acknowledgment.acknowledged]
    ok = not unacknowledged
    return PrescoreResult(
        check_id="signal_acknowledgment_completeness", tool_id="T-21", status="pass" if ok else "flag",
        detail=(
            "every fired signal is acknowledged" if ok
            else f"{len(unacknowledged)} of {len(artifact.signals.value)} fired signal(s) are not yet acknowledged"
        ),
    )


def _recalculation_log_has_reasons(artifact: ControlChartArtifact) -> PrescoreResult:
    blank = [e for e in artifact.recalculation_log if not e.reason.strip()]
    ok = not blank  # schema already forbids this (Field(min_length=1)) -- re-affirmed as a visible guarantee
    return PrescoreResult(
        check_id="recalculation_log_has_reasons", tool_id="T-21", status="pass" if ok else "hard_flag",
        detail=(
            f"{len(artifact.recalculation_log)} log entry(ies), every reason non-blank" if ok
            else f"{len(blank)} log entry(ies) with a blank reason -- should be unreachable (schema-enforced)"
        ),
    )
