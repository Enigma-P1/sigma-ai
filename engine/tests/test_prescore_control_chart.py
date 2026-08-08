"""Prescore tests for T-21: family-matches-data, frozen-before-signals,
never-armed (hard_flag, not a thin pass), acknowledgment completeness,
and the recalculation log's reason discipline."""

from factories import make_control_chart_imr, make_control_chart_p
from sigma_engine.artifacts.control_chart import ControlChartArtifact
from sigma_engine.prescore.control_chart import run_control_chart_prescore

EXPECTED_CHECK_IDS = {
    "family_matches_data", "frozen_limits_present_before_signals", "never_armed",
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
