"""Tests for stats/hypothesis_categorical.py -- a hand-computed chi-square
fixture (arithmetic shown), a hand-computed two-proportion z fixture
(arithmetic shown), an independent-exact-enumeration one-proportion
fixture, and a cross-check against NIST/SEMATECH §7.2.4's own worked
one-proportion example (fetched live 2026-08-08) between the exact test
this engine runs and NIST's normal-approximation z-test."""

import pytest
from scipy.stats import binom, norm

from sigma_engine.stats.hypothesis_categorical import chi_square_independence, cochran_preflight, one_proportion_exact, two_proportion_z
from sigma_engine.stats.hypothesis_common import GroupInput

# --- Hand-computed chi-square fixture ---------------------------------------
# Table: [[10, 20], [30, 15]]. Row totals 30, 45; col totals 40, 35; n=75.
# Expected: E11=30*40/75=16, E12=30*35/75=14, E21=45*40/75=24, E22=45*35/75=21.
# chi2 = (10-16)^2/16 + (20-14)^2/14 + (30-24)^2/24 + (15-21)^2/21
#      = 2.25 + 2.571428571... + 1.5 + 1.714285714... = 8.035714285714286 (exact: 225/28)
CHI_SQUARE_TABLE = [[10, 20], [30, 15]]
HAND_CHI2 = 2.25 + 36 / 14 + 1.5 + 36 / 21


def test_chi_square_hand_fixture_matches_shown_arithmetic():
    r = chi_square_independence(CHI_SQUARE_TABLE, row_labels=["R1", "R2"], col_labels=["C1", "C2"]).value
    assert r.statistic == pytest.approx(HAND_CHI2, abs=1e-9)
    assert r.df == 1.0
    # Cramer's V = sqrt(chi2 / (n * (min(r,c)-1))) = sqrt(8.0357.../75)
    assert r.cramers_v == pytest.approx((HAND_CHI2 / 75) ** 0.5, abs=1e-9)
    assert r.effect_size_ci is None
    assert "noncentral-chi-square" in r.effect_size_ci_method


def test_chi_square_expected_counts_hand_computed():
    r = chi_square_independence(CHI_SQUARE_TABLE, row_labels=["R1", "R2"], col_labels=["C1", "C2"]).value
    expected_by_cell = {(c.row, c.col): c.expected for c in r.contingency}
    assert expected_by_cell[("R1", "C1")] == pytest.approx(16.0, abs=1e-9)
    assert expected_by_cell[("R1", "C2")] == pytest.approx(14.0, abs=1e-9)
    assert expected_by_cell[("R2", "C1")] == pytest.approx(24.0, abs=1e-9)
    assert expected_by_cell[("R2", "C2")] == pytest.approx(21.0, abs=1e-9)


def test_cochran_preflight_passes_on_the_chi_square_fixture():
    check = cochran_preflight(CHI_SQUARE_TABLE)
    assert check.passed is True
    assert check.min_cell_expected == pytest.approx(14.0, abs=1e-9)


def test_cochran_preflight_fails_on_a_sparse_table():
    sparse = [[1, 1], [1, 20]]  # expected counts: 0.174, 1.826, 1.826, 19.174 -- min < 1
    check = cochran_preflight(sparse)
    assert check.passed is False
    assert check.min_cell_expected < 1.0


# --- Hand-computed two-proportion z fixture ---------------------------------
# x1=40/n1=100 (p1=0.4), x2=25/n2=100 (p2=0.25); p_pool=(40+25)/200=0.325.
# SE0 = sqrt(0.325*0.675*(1/100+1/100)) = sqrt(0.0043875) = 0.06623820649745885
# z = (0.4-0.25)/0.06623820649745885 = 2.264554068289192
HAND_TWO_PROP_Z = 2.264554068289192


def test_two_proportion_z_hand_fixture_matches_shown_arithmetic():
    r = two_proportion_z(GroupInput(label="A", successes=40, n=100), GroupInput(label="B", successes=25, n=100)).value
    assert r.statistic == pytest.approx(HAND_TWO_PROP_Z, abs=1e-9)
    expected_p = 2 * (1 - norm.cdf(abs(HAND_TWO_PROP_Z)))
    assert r.p_value == pytest.approx(expected_p, abs=1e-9)
    assert r.risk_difference == pytest.approx(0.15, abs=1e-9)
    assert r.risk_difference_ci is not None
    lo, hi = r.risk_difference_ci
    assert lo < r.risk_difference < hi
    assert "Newcombe" in r.risk_difference_ci_method


def test_two_proportion_z_groups_from_raw_0_1_values():
    a = GroupInput(label="A", values=[1, 1, 1, 0, 0])  # 3/5
    b = GroupInput(label="B", values=[0, 0, 1, 0, 0])  # 1/5
    r = two_proportion_z(a, b).value
    assert r.groups[0].successes == 3 and r.groups[0].n == 5
    assert r.groups[1].successes == 1 and r.groups[1].n == 5


# --- One-proportion: independent exact enumeration + NIST §7.2.4 cross-check ---
# https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm


def test_one_proportion_exact_matches_independent_pmf_enumeration():
    """k=8, n=10, target=0.5 -- two-sided exact p via the standard
    "sum PMF(x) for all x with PMF(x) <= PMF(observed)" construction,
    independently re-derived here (not calling binomtest for the
    expected value) and compared against this engine's own result."""
    n, k, p0 = 10, 8, 0.5
    pmf_obs = binom.pmf(k, n, p0)
    expected_p = sum(binom.pmf(x, n, p0) for x in range(n + 1) if binom.pmf(x, n, p0) <= pmf_obs * (1 + 1e-9))
    assert expected_p == pytest.approx(0.109375, abs=1e-9)  # hand check: 2*(C(10,8)+C(10,9)+C(10,10))/1024 = 2*56/1024

    r = one_proportion_exact(GroupInput(label="sample", successes=k, n=n), p0).value
    assert r.p_value == pytest.approx(expected_p, abs=1e-9)
    assert r.statistic == pytest.approx(0.8, abs=1e-9)  # observed proportion


def test_one_proportion_exact_cross_checks_against_nist_7_2_4_z_approximation():
    """NIST's own example: N=200, x=26 defects, p0=0.10, one-sided z=1.414,
    fails to reject at the one-sided 0.05 critical value 1.645. This
    engine runs the *exact* binomial test (task brief), not NIST's normal
    approximation -- large N means the two methods should agree closely,
    checked here with a loose, documented tolerance rather than asserting
    exact equality between two different methods."""
    r = one_proportion_exact(GroupInput(label="new process wafers", successes=26, n=200), 0.10).value
    nist_two_sided_p_from_z = 2 * (1 - norm.cdf(1.414))
    assert r.p_value == pytest.approx(nist_two_sided_p_from_z, abs=0.01)
    assert r.significant is False  # NIST: "cannot reject" at alpha=0.05


def test_one_proportion_rejects_out_of_range_target():
    with pytest.raises(ValueError):
        one_proportion_exact(GroupInput(label="s", successes=1, n=10), 1.5)
