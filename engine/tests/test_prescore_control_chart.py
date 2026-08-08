"""Prescore tests for T-21: family-matches-data, frozen-before-signals,
never-armed (hard_flag, not a thin pass), acknowledgment completeness,
and the recalculation log's reason discipline."""

from factories import make_control_chart_imr, make_control_chart_p
from sigma_engine.artifacts.control_chart import ControlChartArtifact
from sigma_engine.prescore.control_chart import run_control_chart_prescore

EXPECTED_CHECK_IDS = {
    "family_matches_data", "frozen_limits_present_before_signals", "frozen_baseline_matches_window", "never_armed",
    "signal_acknowledgment_completeness", "recalculation_log_has_reasons",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_frozen_but_never_armed_is_a_hard_flag_not_a_thin_pass():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    results = _by_id(run_control_chart_prescore(a))
    assert set(results) == EXPECTED_CHECK_IDS
    assert results["never_armed"].status == "hard_flag"
    assert "never armed" in results["never_armed"].detail.lower()


def test_armed_chart_passes_never_armed_check():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["armed"] = {"monitoring_started": True, "cadence_note": "Weekly"}
    b = ControlChartArtifact.model_validate(dumped)
    results = _by_id(run_control_chart_prescore(b))
    assert results["never_armed"].status == "pass"


def test_diagnostic_unfrozen_chart_never_armed_check_passes_as_not_applicable():
    a = ControlChartArtifact.model_validate(make_control_chart_imr(freeze_requested=False, action_at=None))
    results = _by_id(run_control_chart_prescore(a))
    assert results["never_armed"].status == "pass"
    assert "not yet applicable" in results["never_armed"].detail


def test_family_matches_data_passes_for_both_chart_types():
    imr = ControlChartArtifact.model_validate(make_control_chart_imr())
    p = ControlChartArtifact.model_validate(make_control_chart_p())
    assert _by_id(run_control_chart_prescore(imr))["family_matches_data"].status == "pass"
    assert _by_id(run_control_chart_prescore(p))["family_matches_data"].status == "pass"


def test_signal_acknowledgment_completeness_flags_an_unacknowledged_signal():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["imr_values"] = dumped["imr_values"] + [40.0]  # a new out-of-control reading, unacknowledged
    b = ControlChartArtifact.model_validate(dumped)
    results = _by_id(run_control_chart_prescore(b))
    assert results["signal_acknowledgment_completeness"].status == "flag"


def test_signal_acknowledgment_completeness_passes_once_acknowledged():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["imr_values"] = dumped["imr_values"] + [40.0]
    b = ControlChartArtifact.model_validate(dumped)
    sig = b.signals.value[0].signal
    key = f"{sig.rule_id}:{sig.start_index}:{sig.end_index}:{sig.side}"
    dumped2 = b.model_dump(mode="json")
    dumped2["acknowledgments"] = {key: {"acknowledged": True, "response_note": "Investigated.", "at": "2026-08-08T00:00:00"}}
    c = ControlChartArtifact.model_validate(dumped2)
    results = _by_id(run_control_chart_prescore(c))
    assert results["signal_acknowledgment_completeness"].status == "pass"


def test_signal_acknowledgment_completeness_passes_with_no_signals_yet():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    results = _by_id(run_control_chart_prescore(a))
    assert results["signal_acknowledgment_completeness"].status == "pass"


def test_recalculation_log_has_reasons_passes_after_a_logged_recalculation():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["recalculate_reason"] = "process changed after the fixture rollout"
    dumped["action_at"] = "2026-08-08T00:00:00"
    dumped["imr_values"] = [50.0 + (i % 3) for i in range(24)]
    b = ControlChartArtifact.model_validate(dumped)
    results = _by_id(run_control_chart_prescore(b))
    assert results["recalculation_log_has_reasons"].status == "pass"
    assert "2 log entry" in results["recalculation_log_has_reasons"].detail


# ---------------------------------------------------------------------------
# Fix 2 (critic-confirmed, R-CTL-01 #3 "never silently refit"; tier-a-done-
# means "schema-enforced, not policy-hoped"): the module docstring's own
# promise -- frozen_window_* is retained "so prescore CAN recompute-and-
# compare" -- had nothing reading it. frozen_baseline_matches_window
# recomputes off the retained window and compares against the stored
# center/limits, both ways: untampered passes, a hand-edited baseline
# hard_flags.
# ---------------------------------------------------------------------------


def test_frozen_baseline_matches_window_passes_on_untampered_imr_freeze():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    results = _by_id(run_control_chart_prescore(a))
    assert results["frozen_baseline_matches_window"].status == "pass"
    assert "match a fresh recompute" in results["frozen_baseline_matches_window"].detail


def test_frozen_baseline_matches_window_passes_on_untampered_p_chart_freeze():
    a = ControlChartArtifact.model_validate(make_control_chart_p())
    results = _by_id(run_control_chart_prescore(a))
    assert results["frozen_baseline_matches_window"].status == "pass"


def test_frozen_baseline_matches_window_passes_as_not_applicable_when_unfrozen():
    a = ControlChartArtifact.model_validate(make_control_chart_imr(freeze_requested=False, action_at=None))
    results = _by_id(run_control_chart_prescore(a))
    assert results["frozen_baseline_matches_window"].status == "pass"
    assert "no frozen baseline yet" in results["frozen_baseline_matches_window"].detail


def test_frozen_baseline_matches_window_survives_new_monitoring_points_appended():
    """frozen_window_values stays pinned to the ORIGINAL freeze window even
    as imr_values legitimately grows with new monitoring readings (frozen
    means frozen) -- the check must keep passing against that unchanged
    window, not the ever-growing current data."""
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["imr_values"] = dumped["imr_values"] + [40.0]
    dumped["freeze_requested"] = False
    dumped["action_at"] = None
    b = ControlChartArtifact.model_validate(dumped)
    assert len(b.frozen_window_values) == 24  # unchanged by the appended 25th point
    results = _by_id(run_control_chart_prescore(b))
    assert results["frozen_baseline_matches_window"].status == "pass"


def test_frozen_baseline_matches_window_hard_flags_the_critics_reproduction():
    """The critic's exact reproduction: a hand-edited imr_baseline (xbar 50,
    sigma 200, UCL 650) on an untouched freeze window -- previously
    accepted, stored, and passing all five prescore checks. Now hard_flags."""
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    tampered_baseline_value = a.imr_baseline.value.model_copy(update={"xbar": 50.0, "sigma_within": 200.0, "i_ucl": 650.0})
    tampered = a.model_copy(update={"imr_baseline": a.imr_baseline.model_copy(update={"value": tampered_baseline_value})})
    results = _by_id(run_control_chart_prescore(tampered))
    assert results["frozen_baseline_matches_window"].status == "hard_flag"
    assert "hand-edited" in results["frozen_baseline_matches_window"].detail
    assert "50" in results["frozen_baseline_matches_window"].detail


def test_frozen_baseline_matches_window_hard_flags_a_tampered_p_chart_pbar():
    a = ControlChartArtifact.model_validate(make_control_chart_p())
    tampered_baseline_value = a.p_baseline.value.model_copy(update={"p_bar": 0.9})
    tampered = a.model_copy(update={"p_baseline": a.p_baseline.model_copy(update={"value": tampered_baseline_value})})
    results = _by_id(run_control_chart_prescore(tampered))
    assert results["frozen_baseline_matches_window"].status == "hard_flag"
