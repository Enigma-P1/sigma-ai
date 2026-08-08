"""Reference tests for stats/p_chart.py.

Two independent checks (module docstring): (1) NIST/SEMATECH §6.3.3.2's
own worked-example RAW DATA (30 wafer samples, n=50 chips each, dataset
MONITOR-6_3_3_2.DAT) -- the page states the CL/UCL/LCL formula in text
and the raw fraction-defective table in text, but its own computed
CL/UCL/LCL live only inside a chart image (not extractable) -- so this
test computes them here, from NIST's own raw numbers, via NIST's own
stated formula, and cross-checks the two out-of-control points (samples
15 and 23) that the classic version of this textbook example calls out.
(2) A small hand-computable VARYING-n fixture (arithmetic in comments),
since the NIST example's n is constant at 50 throughout and can't by
itself exercise the varying-n limits this v1 scope names.
"""

import math

import pytest

from sigma_engine.stats.imr import Signal
from sigma_engine.stats.p_chart import (
    Subgroup,
    compute_p_chart,
    p_bar,
    p_chart_limits,
    rule1_beyond_limits,
)

# --- NIST §6.3.3.2 worked example: raw fraction-defective data, n=50/sample ---
# https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc332.htm
NIST_N = 50
NIST_FRACTIONS = [
    0.24, 0.30, 0.16, 0.20, 0.08, 0.14, 0.32, 0.18, 0.28, 0.20,
    0.10, 0.12, 0.34, 0.24, 0.44, 0.16, 0.20, 0.10, 0.26, 0.22,
    0.40, 0.36, 0.48, 0.30, 0.18, 0.24, 0.14, 0.26, 0.18, 0.12,
]
NIST_DEFECTIVES = [round(f * NIST_N) for f in NIST_FRACTIONS]  # exact -- every fraction is a multiple of 1/50


def _nist_subgroups() -> list[Subgroup]:
    return [Subgroup(label=f"sample-{i + 1}", n=NIST_N, defective_count=d) for i, d in enumerate(NIST_DEFECTIVES)]


def test_pbar_matches_nist_raw_data():
    # pbar = sum(D_i) / (m*n) = 347 / 1500 -- NIST's own §6.3.3.2 formula,
    # applied to NIST's own raw table.
    assert p_bar(_nist_subgroups()) == pytest.approx(347 / 1500)


def test_p_chart_limits_hand_derived_from_nist_formula_and_raw_data():
    pbar = 347 / 1500
    ucl, lcl = p_chart_limits(pbar, NIST_N)
    expected_spread = 3 * math.sqrt(pbar * (1 - pbar) / NIST_N)
    assert ucl == pytest.approx(pbar + expected_spread)
    assert lcl == pytest.approx(pbar - expected_spread)
    assert ucl == pytest.approx(0.410239, abs=1e-6)
    assert lcl == pytest.approx(0.052428, abs=1e-6)


def test_compute_p_chart_flags_the_two_out_of_control_nist_samples():
    # This dataset is the well-known NIST wafer-defect p-chart example;
    # samples 15 (0.44) and 23 (0.48) are the two points that clear the
    # computed UCL (0.4102) -- both above, none below (LCL=0.0524).
    result = compute_p_chart(_nist_subgroups())
    assert result.value.p_bar == pytest.approx(347 / 1500)
    rule1_signals = [s for s in result.value.signals if s.rule_id == "rule1"]
    flagged_indices = sorted(s.start_index for s in rule1_signals)
    assert flagged_indices == [14, 22]  # 0-based: samples 15 and 23
    assert all(s.side == "above" for s in rule1_signals)
    assert result.value.meets_freeze_floor is True  # 30 subgroups >= the 20-point floor
    assert result.provenance.method


# --- Hand-computable VARYING-n fixture (arithmetic shown) -------------------
# 3 subgroups, n=20/40/10, defectives=4/6/1: pbar = (4+6+1)/(20+40+10) =
# 11/70 = 0.157143. Each point's own limits (3*sqrt(pbar(1-pbar)/n)):
#   n=20: spread=0.243935 -> ucl=0.401278, lcl=0 (floored, raw -0.0868)
#   n=40: spread=0.172630 -> ucl=0.329773, lcl=0 (floored, raw -0.0155)
#   n=10: spread=0.344899 -> ucl=0.502402, lcl=0 (floored, raw -0.1878)
# All three p_i (0.20, 0.15, 0.10) sit inside their own limits -- clean,
# no-signal fixture, proving the limits genuinely vary per n (widest at
# n=10, narrowest at n=40) rather than collapsing to one shared band.
VARYING_N_CLEAN = [Subgroup(label="day-1", n=20, defective_count=4), Subgroup(label="day-2", n=40, defective_count=6), Subgroup(label="day-3", n=10, defective_count=1)]


def test_varying_n_limits_are_hand_computable_and_widen_for_smaller_n():
    result = compute_p_chart(VARYING_N_CLEAN)
    assert result.value.p_bar == pytest.approx(11 / 70)
    by_label = {p.label: p for p in result.value.points}
    assert by_label["day-1"].ucl == pytest.approx(0.401278, abs=1e-6)
    assert by_label["day-2"].ucl == pytest.approx(0.329773, abs=1e-6)
    assert by_label["day-3"].ucl == pytest.approx(0.502402, abs=1e-6)
    assert by_label["day-1"].lcl == by_label["day-2"].lcl == by_label["day-3"].lcl == 0.0
    # Narrowest limits at the largest subgroup (n=40), widest at the
    # smallest (n=10) -- the varying-n behavior this fixture exists to prove.
    assert by_label["day-2"].ucl < by_label["day-1"].ucl < by_label["day-3"].ucl
    assert result.value.signals == ()
    assert result.value.meets_freeze_floor is False  # 3 subgroups < the 20-point floor


# --- Hand-computable signal fixture: a point beyond its OWN per-point UCL --
# 3 subgroups, all n=100: defectives 10, 10, 35. pbar = 55/300 = 0.183333.
# spread (n=100) = 3*sqrt(0.183333*0.816667/100) = 0.116082 -> ucl=0.299415.
# Points 1-2 (p=0.10) sit inside; point 3 (p=0.35) clears the UCL.
SIGNAL_FIXTURE = [Subgroup(label="a", n=100, defective_count=10), Subgroup(label="b", n=100, defective_count=10), Subgroup(label="c", n=100, defective_count=35)]


def test_rule1_beyond_limits_flags_only_the_out_of_control_point():
    result = compute_p_chart(SIGNAL_FIXTURE)
    assert result.value.p_bar == pytest.approx(55 / 300)
    assert result.value.points[2].ucl == pytest.approx(0.299415, abs=1e-6)
    signals = [s for s in result.value.signals if s.rule_id == "rule1"]
    assert len(signals) == 1
    assert signals[0] == Signal(
        rule_id="rule1", start_index=2, end_index=2, side="above",
        description="c: p=0.35 is beyond its UCL (0.2994) for n=100",
    )
    assert result.value.has_default_rule_signal is True


def test_rule4_run_of_8_is_reused_verbatim_from_imr_on_the_proportions_series():
    # 8 subgroups all pinned exactly at the center (p == pbar) never
    # signals rule 4 (imr.rule4_run_of_8 requires strictly above/below,
    # same tie rule as the I-MR chart) -- then 8 consecutive points pushed
    # to one side of center fires exactly once, over the full run.
    on_center = [Subgroup(label=f"g{i}", n=100, defective_count=20) for i in range(8)]  # p=0.20=pbar for all
    result_on_center = compute_p_chart(on_center)
    assert result_on_center.value.p_bar == pytest.approx(0.20)
    assert [s for s in result_on_center.value.signals if s.rule_id == "rule4"] == []

    above = [Subgroup(label=f"g{i}", n=100, defective_count=(30 if i < 8 else 10)) for i in range(9)]
    result_above = compute_p_chart(above)
    rule4_signals = [s for s in result_above.value.signals if s.rule_id == "rule4"]
    assert len(rule4_signals) == 1
    assert rule4_signals[0].start_index == 0
    assert rule4_signals[0].end_index == 7
    assert rule4_signals[0].side == "above"


def test_compute_p_chart_requires_at_least_one_subgroup():
    with pytest.raises(ValueError):
        compute_p_chart([])


def test_p_chart_limits_rejects_non_positive_n():
    with pytest.raises(ValueError):
        p_chart_limits(0.2, 0)


def test_rule1_beyond_limits_is_a_pure_function_of_points():
    # Direct unit test of the helper itself (not just via compute_p_chart),
    # matching imr.py's own test style (test_rule1_beyond_3sigma / rule4
    # tested standalone as well as through compute_imr_chart).
    from sigma_engine.stats.p_chart import PChartPoint

    points = [
        PChartPoint(label="x", n=100, defective_count=10, p=0.10, ucl=0.30, lcl=0.07),
        PChartPoint(label="y", n=100, defective_count=2, p=0.02, ucl=0.30, lcl=0.07),
    ]
    signals = rule1_beyond_limits(points)
    assert len(signals) == 1
    assert signals[0].side == "below"
    assert signals[0].start_index == 1
