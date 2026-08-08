"""Tests for stats/hypothesis_common.py: the shared plain-language honesty
rule (rubric R-ANA-05 #2), the NIST-formula lag-1 autocorrelation check
(EXIT-09), and the switch-rule/EXIT-14 advisory normality concern."""

import math

import pytest

from sigma_engine.stats.hypothesis_common import (
    advisory_normality_concern,
    check_autocorrelation,
    correlation_r_magnitude,
    cohens_d_magnitude,
    cramers_v_magnitude,
    eta_squared_magnitude,
    group_successes_n,
    lag1_autocorrelation,
    nonzero_diff_count,
    p_value_sentence,
)
from sigma_engine.stats.hypothesis_common import GroupInput


# --- R-ANA-05 #2: never "no difference," always "no difference shown at this sample size" ---


def test_significant_p_value_sentence_does_not_conclude_no_difference():
    # "no difference" may legitimately appear inside the null-hypothesis
    # explanation ("if there were truly no difference...") -- the banned
    # move is *concluding* a significant result as "no difference shown."
    s = p_value_sentence(0.001, 0.05, True)
    assert "no difference shown" not in s
    assert "statistically detectable" in s.lower()


def test_nonsignificant_p_value_sentence_uses_the_honest_phrase():
    s = p_value_sentence(0.4, 0.05, False)
    assert "no difference shown at this sample size" in s
    # the banned phrasing -- a flat, unqualified "no difference" claim:
    assert "no difference exists" not in s or "not the same claim as 'no difference exists'" in s


# --- lag-1 autocorrelation (NIST/SEMATECH §1.3.3.1) -------------------------


def test_lag1_autocorrelation_hand_computed():
    # y = [1,2,3,4,5]; ybar=3; deviations=[-2,-1,0,1,2]
    # numerator = (-2*-1)+(-1*0)+(0*1)+(1*2) = 2+0+0+2 = 4
    # denominator = 4+1+0+1+4 = 10 -> r1 = 0.4
    r1 = lag1_autocorrelation([1, 2, 3, 4, 5])
    assert r1 == pytest.approx(0.4)


def test_lag1_autocorrelation_none_on_constant_data():
    assert lag1_autocorrelation([5, 5, 5, 5]) is None


def test_lag1_autocorrelation_none_below_n2():
    assert lag1_autocorrelation([5]) is None


# --- EXIT-09 compound boundary: significant AND material, independently ----


def test_exit09_fires_only_when_both_significant_and_material():
    # Strong, perfectly alternating anti-correlation: r1 approx -1,
    # |r1|=1 > 2/sqrt(n) and >= 0.3 -- both conditions true.
    data = [0, 10] * 10
    check = check_autocorrelation("x", data)
    assert check.is_significant and check.is_material
    assert check.fires_exit09 is True


def test_exit09_does_not_fire_when_significant_but_not_material():
    # Construct r1 just above the significance threshold but below 0.3.
    # threshold(n=100) = 2/10 = 0.2; target r1 ~= 0.25 (significant, <0.3).
    import numpy as np

    rng = np.random.default_rng(7)
    n = 100
    # AR(1)-ish small-signal series with a modest positive lag-1 correlation.
    x = [0.0]
    for _ in range(n - 1):
        x.append(0.25 * x[-1] + rng.normal(0, 1))
    check = check_autocorrelation("x", x)
    assert check.significance_threshold == pytest.approx(2.0 / math.sqrt(n))
    # Whatever r1 lands at, the compound rule (not either alone) governs fires_exit09:
    assert check.fires_exit09 == (check.is_significant and check.is_material)


def test_exit09_does_not_fire_when_material_but_not_significant():
    # Tiny n: 2/sqrt(n) is a large threshold, so even a "material" (>=0.3)
    # r1 will often fail significance at very small n.
    data = [1, 2, 1.5]  # n=3, threshold = 2/sqrt(3) = 1.1547 > any |r1| <= 1
    check = check_autocorrelation("x", data)
    assert check.significance_threshold == pytest.approx(2.0 / math.sqrt(3))
    assert check.is_significant is False
    assert check.fires_exit09 is False


# --- advisory_normality_concern: deliberately NOT assess_normality's n>=15 gate ---


def test_advisory_normality_concern_can_fire_below_n15():
    """The whole point of this function (see its docstring): it must be
    able to return True for n<15, or the switch rule's third disjunct
    (n<15 AND ... OR advisory normality concern) would be vacuous."""
    # A strongly right-skewed tiny sample -- extreme outlier against a tight cluster.
    skewed = [1.0, 1.1, 1.0, 1.05, 0.95, 1.0, 1.1, 50.0]
    assert len(skewed) < 15
    assert advisory_normality_concern(skewed) is True


def test_advisory_normality_concern_false_below_ad_floor():
    assert advisory_normality_concern([1.0, 2.0]) is False  # n=2 < MIN_N_FOR_ANDERSON_DARLING_STATISTIC


def test_advisory_normality_concern_false_on_clean_normal_ish_data():
    clean = [10.0, 10.1, 9.9, 10.05, 9.95, 10.02, 9.98, 10.03]
    assert advisory_normality_concern(clean) is False


# --- nonzero_diff_count / group_successes_n ---------------------------------


def test_nonzero_diff_count_drops_zeros():
    assert nonzero_diff_count([1, 0, -2, 0, 0, 3]) == 3


def test_group_successes_n_from_values():
    g = GroupInput(label="g", values=[1, 0, 1, 1, 0])
    assert group_successes_n(g) == (3, 5)


def test_group_successes_n_from_successes_and_n():
    g = GroupInput(label="g", successes=7, n=20)
    assert group_successes_n(g) == (7, 20)


def test_group_successes_n_requires_one_or_the_other():
    g = GroupInput(label="g")
    with pytest.raises(ValueError):
        group_successes_n(g)


# --- magnitude-word helpers (boundary-aware, no crashes at the edges) ------


@pytest.mark.parametrize("value,expected", [(0.1, "negligible"), (0.2, "small"), (0.5, "medium"), (0.8, "large"), (1.2, "large")])
def test_cohens_d_magnitude_bands(value, expected):
    assert cohens_d_magnitude(value) == expected


@pytest.mark.parametrize("value,expected", [(0.005, "negligible"), (0.01, "small"), (0.06, "medium"), (0.14, "large")])
def test_eta_squared_magnitude_bands(value, expected):
    assert eta_squared_magnitude(value) == expected


@pytest.mark.parametrize("value,expected", [(0.05, "negligible"), (0.1, "small"), (0.3, "medium"), (0.5, "large")])
def test_correlation_r_magnitude_bands(value, expected):
    assert correlation_r_magnitude(value) == expected


@pytest.mark.parametrize("value,expected", [(0.05, "negligible"), (0.1, "weak"), (0.3, "moderate"), (0.5, "strong")])
def test_cramers_v_magnitude_bands(value, expected):
    assert cramers_v_magnitude(value) == expected
