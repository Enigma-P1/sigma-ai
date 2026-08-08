"""Schema/behavior tests for T-21 ControlChartArtifact: selector ->
EXIT-11, chart_type/data-shape consistency, freeze floor + frozen-means-
frozen persistence, recalculate discipline, and signal/acknowledgment
tracking against the coffee-bar (imr) and print-shop-style (p) fixtures."""

import pytest
from pydantic import ValidationError

from factories import TS, make_control_chart_imr, make_control_chart_p, make_control_chart_p_subgroups
from sigma_engine.artifacts.control_chart import ControlChartArtifact


def test_accepts_a_complete_imr_chart_and_freezes_on_first_save():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    assert a.chart_type == "imr"
    assert a.imr_baseline is not None
    assert a.p_baseline is None
    assert a.frozen_at == TS
    assert len(a.recalculation_log) == 1
    assert a.recalculation_log[0].triggered_by == "initial_freeze"
    assert a.signals is not None and a.signals.value == []  # coffee-bar fixture is stable, no signal


def test_accepts_a_complete_p_chart_and_freezes_on_first_save():
    a = ControlChartArtifact.model_validate(make_control_chart_p())
    assert a.chart_type == "p"
    assert a.p_baseline is not None
    assert a.p_baseline.value.p_bar == pytest.approx(0.20)
    assert a.imr_baseline is None


def test_exit11_fires_on_defects_answer_and_names_the_exit():
    body = make_control_chart_p(selector={"data_shape": "attribute", "defectives_or_defects": "defects"})
    with pytest.raises(ValidationError, match="EXIT-11"):
        ControlChartArtifact.model_validate(body)


def test_attribute_selector_requires_the_defectives_or_defects_answer():
    body = make_control_chart_p(selector={"data_shape": "attribute"})
    with pytest.raises(ValidationError):
        ControlChartArtifact.model_validate(body)


def test_chart_type_must_match_selector_data_shape():
    body = make_control_chart_imr(chart_type="p")
    with pytest.raises(ValidationError, match="does not match"):
        ControlChartArtifact.model_validate(body)


def test_imr_chart_type_rejects_p_subgroups_payload():
    body = make_control_chart_imr()
    body["p_subgroups"] = make_control_chart_p_subgroups()
    with pytest.raises(ValidationError):
        ControlChartArtifact.model_validate(body)


def test_freeze_refused_below_the_20_point_floor():
    body = make_control_chart_imr(imr_values=[95.0, 91.0, 98.0, 93.0, 97.0])
    with pytest.raises(ValidationError, match="EXIT-04"):
        ControlChartArtifact.model_validate(body)


def test_freeze_refused_when_the_window_itself_signals():
    # 8 consecutive points on one side of the mean fires rule 4 within the
    # freeze window itself -- refused even though n clears the 20-floor.
    unstable = [100.0] * 8 + [50.0] * 8 + [75.0] * 4
    body = make_control_chart_imr(imr_values=unstable)
    with pytest.raises(ValidationError, match="EXIT-04"):
        ControlChartArtifact.model_validate(body)


def test_diagnostic_chart_with_no_freeze_requested_has_no_baseline_or_signals():
    body = make_control_chart_imr(freeze_requested=False, action_at=None)
    a = ControlChartArtifact.model_validate(body)
    assert a.imr_baseline is None
    assert a.signals is None
    assert a.frozen_at is None


def test_frozen_limits_persist_unchanged_while_new_monitoring_points_are_appended():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["imr_values"] = dumped["imr_values"] + [40.0]  # a clearly out-of-control new reading
    dumped["freeze_requested"] = False
    dumped["action_at"] = None
    b = ControlChartArtifact.model_validate(dumped)
    assert b.imr_baseline.value.xbar == a.imr_baseline.value.xbar  # frozen means frozen
    assert b.frozen_at == a.frozen_at
    new_signals = [ts for ts in b.signals.value if ts.signal.rule_id == "rule1"]
    assert len(new_signals) == 1
    assert new_signals[0].signal.start_index == 24  # the newly-appended point


def test_recalculate_requires_a_non_empty_reason():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["recalculate_reason"] = "   "
    dumped["action_at"] = TS
    with pytest.raises(ValidationError, match="non-empty"):
        ControlChartArtifact.model_validate(dumped)


def test_recalculate_still_honors_the_freeze_floor():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["recalculate_reason"] = "process changed after the fixture rollout"
    dumped["action_at"] = TS
    dumped["imr_values"] = dumped["imr_values"][:5]
    with pytest.raises(ValidationError, match="EXIT-04"):
        ControlChartArtifact.model_validate(dumped)


def test_recalculate_with_a_reason_and_qualifying_data_relogs_and_updates_baseline():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["recalculate_reason"] = "process changed after the fixture rollout"
    dumped["action_at"] = TS
    dumped["imr_values"] = [50.0 + (i % 3) for i in range(24)]  # a genuinely different, still-stable series
    b = ControlChartArtifact.model_validate(dumped)
    assert b.imr_baseline.value.xbar != a.imr_baseline.value.xbar
    assert len(b.recalculation_log) == 2
    assert [e.triggered_by for e in b.recalculation_log] == ["initial_freeze", "recalculate"]
    assert b.recalculation_log[1].reason == "process changed after the fixture rollout"


def test_armed_state_defaults_false_and_round_trips():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    assert a.armed.monitoring_started is False
    dumped = a.model_dump(mode="json")
    dumped["armed"] = {"monitoring_started": True, "cadence_note": "Weekly, every Monday morning"}
    dumped["freeze_requested"] = False
    dumped["action_at"] = None
    b = ControlChartArtifact.model_validate(dumped)
    assert b.armed.monitoring_started is True
    assert b.armed.cadence_note == "Weekly, every Monday morning"


def test_signal_acknowledgment_round_trips_by_signal_key():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    dumped = a.model_dump(mode="json")
    dumped["imr_values"] = dumped["imr_values"] + [40.0]
    dumped["freeze_requested"] = False
    dumped["action_at"] = None
    b = ControlChartArtifact.model_validate(dumped)
    sig = b.signals.value[0].signal
    key = f"{sig.rule_id}:{sig.start_index}:{sig.end_index}:{sig.side}"

    dumped2 = b.model_dump(mode="json")
    dumped2["acknowledgments"] = {key: {"acknowledged": True, "response_note": "New hire mis-timed the register.", "at": TS}}
    c = ControlChartArtifact.model_validate(dumped2)
    assert c.signals.value[0].acknowledgment.acknowledged is True
    assert c.signals.value[0].acknowledgment.response_note == "New hire mis-timed the register."


def test_action_at_is_a_one_shot_trigger_cleared_after_the_freeze():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    assert a.action_at is None  # consumed by the freeze it triggered, same as freeze_requested/recalculate_reason


def test_round_trip_via_model_dump():
    a = ControlChartArtifact.model_validate(make_control_chart_imr())
    b = ControlChartArtifact.model_validate(a.model_dump(mode="json"))
    assert b == a
