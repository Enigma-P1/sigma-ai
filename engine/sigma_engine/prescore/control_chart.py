"""T-21 prescore: rubric R-CTL-01/02's rule-checkable lines.

  - family_matches_data: chart_type matches the selector's data_shape
    (schema already guarantees this at construction -- re-affirmed here
    as a visible check, same "re-affirm what the schema enforces" move
    prescore/hypothesis.py's route_tamper_check makes for T-17's route).
  - frozen_limits_present_before_signals (R-CTL-01 #2/#3): a chart with
    signals but no frozen baseline can't happen by construction (see
    control_chart.py's _compute_signals: signals stays None until a
    baseline exists) -- checked here as a visible guarantee, not a gap.
  - frozen_baseline_matches_window (R-CTL-01 #3 "never silently refit";
    tier-a-done-means "schema-enforced, not policy-hoped" -- critic
    finding): control_chart.py's own docstring justifies its one frozen-
    means-frozen exception by promising the freeze window's raw values are
    retained (frozen_window_*) specifically so prescore CAN recompute-and-
    compare -- nothing did, until this check. Recomputes compute_imr_chart/
    compute_p_chart fresh off the retained window and compares against the
    STORED center/limits (yield_calc.py's matches-recomputed idiom, same
    1e-9 relative tolerance) -- hard_flag on mismatch.
  - never_armed flag (R-CTL-02's own pre-score line: "a missing signal
    log because charting never ran is a Fail, not a thin Pass") --
    hard_flag, not a soft flag, when frozen but never armed.
  - signal_acknowledgment_completeness: every fired signal carries an
    acknowledgment (R-CTL-02 #1/#3 -- "no repeated signal left
    unacknowledged").
  - recalculation_log_has_reasons: every log entry's reason is non-blank
    (schema already guarantees this; re-affirmed the same way as above).
  - measurement_check_on_file (M6 eval fix, persona finding FL-07): a
    chart whose limits are FROZEN while the project has no T-12
    measurement check on file gets a flag -- the frozen limits and every
    signal judged against them rest on a measurement system nothing has
    checked, and the EXIT-02 hard gate can only catch a FAILED check,
    never a missing one. Flag-level, not hard: freezing is not blocked
    (charting your own data diagnostically or frozen is legitimate); the
    flag names the risk, and the capability-language gate keeps capability
    claims honest. This is the one check here that needs PROJECT state,
    which the registry's artifact-only call shape can't supply -- so it
    runs only when the caller passes `msa_on_file` (routes/prescore.py
    does, from the same gates.build_project_snapshot the gates consume,
    whenever the request names a project_id); an artifact-only call
    (registry/advisor path) omits the check rather than guessing.
"""

from __future__ import annotations

from ..artifacts.control_chart import ControlChartArtifact
from ..stats.imr import compute_imr_chart
from ..stats.p_chart import compute_p_chart
from .common import PrescoreResult

# Same idiom and tolerance as prescore/yield_calc.py's _close_enough --
# "matches a fresh recompute," not "matches to the last visible digit."
_RELATIVE_TOLERANCE = 1e-9


def _close_enough(a: float, b: float) -> bool:
    return abs(a - b) <= _RELATIVE_TOLERANCE * max(1.0, abs(a), abs(b))


def run_control_chart_prescore(
    artifact: ControlChartArtifact, *, msa_on_file: bool | None = None, msa_verdict: str | None = None,
) -> list[PrescoreResult]:
    """`msa_on_file`/`msa_verdict` are the project's T-12 state as
    gates.build_project_snapshot reports it (msa_on_file: any T-12 saved;
    msa_verdict: the latest one's verdict). None for msa_on_file means the
    caller has no project context (the registry's artifact-only shape) --
    the measurement_check_on_file check is then omitted, not guessed (see
    module docstring)."""
    checks = [
        _family_matches_data(artifact),
        _frozen_limits_present_before_signals(artifact),
        _frozen_baseline_matches_window(artifact),
        _never_armed(artifact),
        _signal_acknowledgment_completeness(artifact),
        _recalculation_log_has_reasons(artifact),
    ]
    if msa_on_file is not None:
        checks.append(_measurement_check_on_file(artifact, msa_on_file, msa_verdict))
    return checks


def _measurement_check_on_file(
    artifact: ControlChartArtifact, msa_on_file: bool, msa_verdict: str | None
) -> PrescoreResult:
    frozen = artifact.imr_baseline is not None or artifact.p_baseline is not None
    if not frozen:
        # Same honest not-yet-applicable shape as _never_armed: a
        # diagnostic chart makes no stability claim, so a missing T-12
        # is not yet this chart's problem.
        return PrescoreResult(
            check_id="measurement_check_on_file", tool_id="T-21", status="pass",
            detail="no frozen limits -- the chart runs diagnostically; this check applies once limits are frozen",
        )
    if not msa_on_file:
        return PrescoreResult(
            check_id="measurement_check_on_file", tool_id="T-21", status="flag",
            detail=(
                "limits are frozen but this project has no measurement check (T-12) on file -- the frozen "
                "limits and every signal judged against them rest on a measurement system nothing has checked. "
                "Freezing is not blocked; run T-12 (the EXIT-02 hard gate only catches a failed check, not a "
                "missing one)."
            ),
        )
    detail = (
        f"measurement check on file: latest T-12 verdict {msa_verdict!r}"
        if msa_verdict is not None
        else "measurement check on file, but its latest version records no verdict"
    )
    return PrescoreResult(check_id="measurement_check_on_file", tool_id="T-21", status="pass", detail=detail)


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


def _frozen_baseline_matches_window(artifact: ControlChartArtifact) -> PrescoreResult:
    frozen = artifact.imr_baseline is not None or artifact.p_baseline is not None
    if not frozen:
        # Honest skip: nothing is frozen yet, so there is nothing to
        # cross-check against a retained window (same "not yet applicable"
        # shape as _never_armed below, not an omitted check).
        return PrescoreResult(
            check_id="frozen_baseline_matches_window", tool_id="T-21", status="pass",
            detail="no frozen baseline yet -- nothing to cross-check",
        )

    if artifact.chart_type == "imr":
        assert artifact.imr_baseline is not None
        if not artifact.frozen_window_values:
            return PrescoreResult(
                check_id="frozen_baseline_matches_window", tool_id="T-21", status="hard_flag",
                detail="imr_baseline is frozen but frozen_window_values is empty -- cannot verify the stored "
                "limits against the window that supposedly produced them",
            )
        stored = artifact.imr_baseline.value
        # Fix (M4 rule2/3 opt-in): replay the STORED rule2_enabled/
        # rule3_enabled -- what was actually in effect at freeze time --
        # never artifact.rule2_enabled/rule3_enabled, which can legitimately
        # differ by now (the toggle applies live to MONITORING reads
        # without requiring a re-freeze; control_chart.py's module
        # docstring). Recomputing with the live fields instead would
        # false-flag an honestly opted-in-after-freeze chart as tampered.
        recomputed = compute_imr_chart(
            artifact.frozen_window_values, enable_rule2=stored.rule2_enabled, enable_rule3=stored.rule3_enabled,
        ).value
        # Note: comparing recomputed.rule2_enabled/rule3_enabled against
        # stored's would be vacuous -- they're fed in as the recompute's
        # own arguments above, so they're equal by construction. The
        # signals comparison is what actually catches a tampered
        # rule2_enabled/rule3_enabled (a flipped flag with no matching
        # change to the stored signal list disagrees with a same-flags
        # recompute) alongside a tampered center/limits.
        matches = (
            _close_enough(stored.xbar, recomputed.xbar)
            and _close_enough(stored.sigma_within, recomputed.sigma_within)
            and _close_enough(stored.i_ucl, recomputed.i_ucl)
            and _close_enough(stored.i_lcl, recomputed.i_lcl)
            and stored.signals == recomputed.signals
        )
        detail = (
            f"stored center/limits (xbar={stored.xbar:g}, sigma={stored.sigma_within:g}, UCL={stored.i_ucl:g}, "
            f"LCL={stored.i_lcl:g}) and its {len(stored.signals)} window signal(s) (rule2_enabled="
            f"{stored.rule2_enabled}, rule3_enabled={stored.rule3_enabled}) match a fresh recompute off "
            "frozen_window_values" if matches else
            f"stored xbar/sigma/UCL/LCL ({stored.xbar:g}/{stored.sigma_within:g}/{stored.i_ucl:g}/{stored.i_lcl:g}) "
            f"do NOT match a fresh recompute off the retained freeze window (recomputed "
            f"{recomputed.xbar:g}/{recomputed.sigma_within:g}/{recomputed.i_ucl:g}/{recomputed.i_lcl:g}) -- the "
            "frozen baseline was hand-edited after freezing (R-CTL-01 #3: never silently refit -- and never "
            "silently accepted un-recomputed either)"
        )
    else:
        assert artifact.p_baseline is not None
        if not artifact.frozen_window_subgroups:
            return PrescoreResult(
                check_id="frozen_baseline_matches_window", tool_id="T-21", status="hard_flag",
                detail="p_baseline is frozen but frozen_window_subgroups is empty -- cannot verify the stored "
                "limits against the window that supposedly produced them",
            )
        stored = artifact.p_baseline.value
        recomputed = compute_p_chart(artifact.frozen_window_subgroups).value
        matches = _close_enough(stored.p_bar, recomputed.p_bar) and len(stored.points) == len(recomputed.points) and all(
            _close_enough(sp.ucl, rp.ucl) and _close_enough(sp.lcl, rp.lcl)
            for sp, rp in zip(stored.points, recomputed.points)
        )
        detail = (
            f"stored p_bar={stored.p_bar:g} and every subgroup's UCL/LCL match a fresh recompute off "
            "frozen_window_subgroups" if matches else
            f"stored p_bar={stored.p_bar:g} (or a subgroup UCL/LCL) does NOT match a fresh recompute off the "
            f"retained freeze window (recomputed p_bar={recomputed.p_bar:g}) -- the frozen baseline was "
            "hand-edited after freezing (R-CTL-01 #3)"
        )

    return PrescoreResult(
        check_id="frozen_baseline_matches_window", tool_id="T-21", status="pass" if matches else "hard_flag", detail=detail,
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
