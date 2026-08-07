"""Reference tests for stats/imr.py.

Individuals-chart limits are reference-tested against NIST/SEMATECH's own
worked example on §6.3.2.2 "Individuals Control Charts" (flow-rate data,
n=10): https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm
NIST states xbar=50.81, MRbar=1.8778, UCL=55.8041, LCL=45.8159, and "the
process is in control, since none of the plotted points fall outside
either the UCL or LCL" -- reproduced here to NIST's own 4-decimal
precision. The MR-chart limits are not printed on that page; UCL is
hand-derived here from the D4=3.267 constant (constants.py, cited to
NIST §6.3.2.1's n=2 table row): 3.267 * (16.9/9) = 6.1347.
"""

import pytest

from sigma_engine.stats.imr import (
    Signal,
    compute_imr_chart,
    individuals_limits,
    mr_bar,
    mr_chart_limits,
    moving_ranges,
    rule1_beyond_3sigma,
    rule4_run_of_8,
)

NIST_FLOW_RATE = [49.6, 47.6, 49.9, 51.3, 47.8, 51.2, 52.6, 52.4, 53.6, 52.1]
NIST_TOLERANCE = 1e-3  # NIST's own worked numbers are printed to 4 decimals


def test_moving_ranges_and_mr_bar_match_nist_worked_example():
    mrs = moving_ranges(NIST_FLOW_RATE)
    assert mrs == pytest.approx([2.0, 2.3, 1.4, 3.5, 3.4, 1.4, 0.2, 1.2, 1.5])
    assert mr_bar(NIST_FLOW_RATE) == pytest.approx(1.8778, abs=NIST_TOLERANCE)


def test_individuals_limits_match_nist_worked_example():
    ucl, cl, lcl = individuals_limits(xbar=50.81, mr_bar_value=1.8778)
    assert cl == pytest.approx(50.81)
    assert ucl == pytest.approx(55.8041, abs=NIST_TOLERANCE)
    assert lcl == pytest.approx(45.8159, abs=NIST_TOLERANCE)


def test_mr_chart_limits_hand_derived_from_nist_d4():
    # 3.267 * 1.877778 = 6.1347 (D3=0 for n=2, per the same table).
    ucl, cl, lcl = mr_chart_limits(mr_bar_value=16.9 / 9)
    assert ucl == pytest.approx(6.1347, abs=NIST_TOLERANCE)
    assert lcl == 0.0


def test_compute_imr_chart_matches_nist_worked_example_and_reports_in_control():
    result = compute_imr_chart(NIST_FLOW_RATE)
    assert result.value.xbar == pytest.approx(50.81)
    assert result.value.mr_bar == pytest.approx(1.8778, abs=NIST_TOLERANCE)
    assert result.value.i_ucl == pytest.approx(55.8041, abs=NIST_TOLERANCE)
    assert result.value.i_lcl == pytest.approx(45.8159, abs=NIST_TOLERANCE)
    # NIST: "the process is in control" -- no signals from any default rule.
    assert result.value.signals == ()
    assert result.value.has_default_rule_signal is False
    assert result.provenance.method


# --- Boundary golden: a point exactly at 3 sigma (§4a requirement) --------

def test_rule1_point_exactly_on_the_limit_does_not_signal():
    """Tie-handling choice, documented: 'beyond' the limit means strictly
    outside it (NIST §6.3.1: "a point falls outside these limits"), so a
    point sitting exactly ON the UCL is read as in-control, not a signal.
    rule1_beyond_3sigma uses > / < (never >=, <=) for this reason."""
    xbar, sigma = 100.0, 2.0
    ucl = xbar + 3 * sigma  # exactly 106.0
    on_the_limit = [100, 101, 99, ucl, 100]
    assert rule1_beyond_3sigma(on_the_limit, xbar, sigma) == []

    just_beyond = [100, 101, 99, ucl + 1e-9, 100]
    signals = rule1_beyond_3sigma(just_beyond, xbar, sigma)
    assert len(signals) == 1
    assert signals[0].side == "above"
    assert signals[0].start_index == 3


def test_rule1_point_exactly_on_lower_limit_does_not_signal():
    xbar, sigma = 100.0, 2.0
    lcl = xbar - 3 * sigma  # exactly 94.0
    assert rule1_beyond_3sigma([100, lcl, 101], xbar, sigma) == []


# --- Boundary golden: rule 4's run length (7 does not signal, 8 does) -----

def test_rule4_run_of_exactly_7_does_not_signal():
    data = [1, 1, 1, 1, 1, 1, 1, -1]  # 7 consecutive above xbar=0, then below
    assert rule4_run_of_8(data, xbar=0.0) == []


def test_rule4_run_of_exactly_8_signals_once_over_the_full_run():
    data = [1, 1, 1, 1, 1, 1, 1, 1, -1]  # 8 consecutive above xbar=0
    signals = rule4_run_of_8(data, xbar=0.0)
    assert len(signals) == 1
    assert signals[0] == Signal(
        rule_id="rule4", start_index=0, end_index=7, side="above",
        description="8 consecutive points fall above the center line (indices 0-7)",
    )


# --- WECO rules 2/3: opt-in, verified default-off (docs/traceability-
# matrix.md §4a / §VI.A.1) -------------------------------------------------

# n=20 (clears the EXIT-04 companion floor), tightly alternating baseline
# (MR always 0.4) so sigma_within is small and predictable, then 2 of the
# last 3 points pushed to 2-3 sigma above center (zone-A territory) --
# verified by construction (see this task's research) to trigger rule 2
# alone: xbar=50.11, sigma_within=0.41993, zone-A upper=50.95, and no
# point ever reaches the 3-sigma UCL (51.37), so rule 1 never fires.
RULE2_ONLY_DATA = [
    50, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2,
    49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8,
    51.0, 50.2, 51.0,
]

# Same baseline shape; last 5 points are 4-of-5 beyond 1-sigma (zone-B),
# never reaching zone-A or the 3-sigma UCL -- rule 3 alone.
RULE3_ONLY_DATA = [
    50, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2,
    49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8,
    50.5, 50.5, 50.5, 50.5, 49.8,
]


def test_rule2_and_rule3_are_off_by_default():
    result = compute_imr_chart(RULE2_ONLY_DATA)
    assert result.value.signals == ()
    assert result.value.rule2_enabled is False

    result3 = compute_imr_chart(RULE3_ONLY_DATA)
    assert result3.value.signals == ()
    assert result3.value.rule3_enabled is False


def test_rule2_signals_only_when_enabled():
    result = compute_imr_chart(RULE2_ONLY_DATA, enable_rule2=True)
    rule2_signals = [s for s in result.value.signals if s.rule_id == "rule2"]
    assert len(rule2_signals) == 1
    assert rule2_signals[0].side == "above"
    assert rule2_signals[0].end_index == 19  # last index of the 20-point series


def test_rule3_signals_only_when_enabled():
    result = compute_imr_chart(RULE3_ONLY_DATA, enable_rule3=True)
    rule3_signals = [s for s in result.value.signals if s.rule_id == "rule3"]
    assert len(rule3_signals) >= 1
    assert all(s.side == "above" for s in rule3_signals)


def test_compute_imr_chart_requires_at_least_two_observations():
    with pytest.raises(ValueError):
        compute_imr_chart([1.0])
