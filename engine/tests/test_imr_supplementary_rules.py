"""Supplementary run tests (rules 5-8) on the I-MR chart.

Western Electric defines FOUR rules. These four are the standard
supplementary tests published by Lloyd Nelson (JQT, 1984). Nelson numbers
his own set 1-8 in a different order from WECO's, so this module's ids
continue the WECO sequence rather than claiming Nelson's numbering -- a
report citing "rule 5" must not mean something different from the reader's
own reference book.
"""

from __future__ import annotations

from sigma_engine.stats.imr import (
    compute_imr_chart,
    rule5_trend,
    rule6_hugging,
    rule7_alternating,
    rule8_mixture,
)


def _ids(signals) -> set[str]:
    return {s.rule_id for s in signals}


# ------------------------------------------------------------------ rule 5


def test_trend_fires_on_six_steadily_increasing_points():
    assert len(rule5_trend([1, 2, 3, 4, 5, 6], 3.5)) == 1


def test_trend_fires_on_six_steadily_decreasing_points():
    signals = rule5_trend([6, 5, 4, 3, 2, 1], 3.5)
    assert len(signals) == 1
    assert signals[0].side == "below"


def test_five_rising_points_are_not_a_trend():
    assert rule5_trend([1, 2, 3, 4, 5], 3.0) == []


def test_a_flat_step_breaks_a_trend_rather_than_continuing_it():
    """Ties break the run. Treating equal consecutive readings as
    continuation lets a coarse measurement scale manufacture trends out of
    noise -- on data rounded to whole minutes, half the 'trends' would be
    repeats."""
    assert rule5_trend([1, 2, 3, 3, 4, 5, 6], 3.5) == []


def test_trend_does_not_need_points_outside_the_limits():
    """The whole value of this test: a drift inside the limits is invisible
    to rules 1-4."""
    data = [10.0 + i * 0.001 for i in range(6)]
    assert len(rule5_trend(data, 10.0025)) == 1


# ------------------------------------------------------------------ rule 6


def test_hugging_fires_when_fifteen_points_sit_inside_one_sigma():
    assert len(rule6_hugging([0.1] * 15, 0.0, 1.0)) == 1


def test_hugging_does_not_fire_on_fourteen():
    assert rule6_hugging([0.1] * 14, 0.0, 1.0) == []


def test_hugging_does_not_fire_when_one_point_escapes_the_zone():
    data = [0.1] * 14 + [2.0]
    assert rule6_hugging(data, 0.0, 1.0) == []


def test_hugging_description_says_it_is_not_a_one_sided_pattern():
    """`side` is reported because the Signal model requires one, but hugging
    is two-sided; the description has to stop a reader over-reading it."""
    signal = rule6_hugging([0.1] * 15, 0.0, 1.0)[0]
    assert "Not a one-sided pattern" in signal.description
    assert "limits are too wide" in signal.description


# ------------------------------------------------------------------ rule 7


def test_alternating_fires_on_fourteen_alternating_points():
    data = [1.0 if i % 2 == 0 else 2.0 for i in range(14)]
    assert len(rule7_alternating(data, 1.5)) >= 1


def test_alternating_does_not_fire_on_a_short_zigzag():
    data = [1.0 if i % 2 == 0 else 2.0 for i in range(6)]
    assert rule7_alternating(data, 1.5) == []


def test_alternating_does_not_fire_on_a_monotone_run():
    assert rule7_alternating(list(range(20)), 9.5) == []


# ------------------------------------------------------------------ rule 8


def test_mixture_fires_when_eight_points_straddle_center_avoiding_the_middle():
    data = [10.0, -10.0] * 4
    signals = rule8_mixture(data, 0.0, 1.0)
    assert len(signals) >= 1
    assert "two populations" in signals[0].description


def test_mixture_does_not_fire_when_points_are_all_on_one_side():
    assert rule8_mixture([10.0] * 8, 0.0, 1.0) == []


def test_mixture_does_not_fire_when_a_point_sits_near_center():
    data = [10.0, -10.0, 10.0, 0.2, 10.0, -10.0, 10.0, -10.0]
    assert rule8_mixture(data, 0.0, 1.0) == []


# --------------------------------------------------------------- wiring


def test_supplementary_rules_are_off_by_default():
    """Every extra test shortens the in-control ARL. Running all eight turns
    false alarms into routine, and a chart that cries wolf trains its reader
    to ignore it."""
    result = compute_imr_chart(list(range(1, 11))).value
    assert "rule5" not in _ids(result.signals)
    assert result.rule5_enabled is False


def test_each_supplementary_rule_can_be_enabled_independently():
    result = compute_imr_chart(list(range(1, 11)), enable_rule5=True).value
    assert "rule5" in _ids(result.signals)
    assert result.rule5_enabled is True
    assert result.rule6_enabled is False


def test_enabled_flags_are_recorded_on_the_result_and_change_the_provenance_hash():
    """ProvenanceRecord stores a HASH of the inputs, not the inputs -- so the
    check that the flags really are part of the recorded input is that
    toggling one changes the hash. Two runs with different rules enabled must
    not be able to claim identical provenance."""
    on = compute_imr_chart([1.0, 2.0, 3.0], enable_rule7=True)
    off = compute_imr_chart([1.0, 2.0, 3.0])
    assert on.value.rule7_enabled is True
    assert off.value.rule7_enabled is False
    assert on.provenance.input_hash != off.provenance.input_hash
    assert "Nelson 1984" in on.provenance.method
