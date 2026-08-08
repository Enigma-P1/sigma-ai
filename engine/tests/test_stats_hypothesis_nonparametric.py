"""Tests for stats/hypothesis_nonparametric.py -- the NIST/SEMATECH §7.3.5
Mann-Whitney worked example (fetched live 2026-08-08), plus an
exact-enumeration Wilcoxon signed-rank fixture independently brute-forced
over all 2^n sign patterns (task brief's documented fallback for the
nonparametric family, since no NIST worked numeric example for the
signed-rank test was found in this handbook)."""

import itertools

import pytest
from scipy.stats import rankdata

from sigma_engine.stats.hypothesis_nonparametric import hodges_lehmann_one_sample, hodges_lehmann_two_sample, mann_whitney_u, wilcoxon_signed_rank

# --- NIST/SEMATECH §7.3.5 "Do two arbitrary processes have the same central tendency?" ---
# https://www.itl.nist.gov/div898/handbook/prc/section3/prc35.htm
# Wafer-cleaning particle counts (coded), two processing systems.
NIST_GROUP_A = [0.55, 0.67, 0.43, 0.51, 0.48, 0.60, 0.71, 0.53, 0.44, 0.65, 0.75]
NIST_GROUP_B = [0.49, 0.68, 0.59, 0.72, 0.67, 0.75, 0.65, 0.77, 0.62, 0.48, 0.59]


def test_mann_whitney_u_matches_nist_7_3_5_exactly():
    r = mann_whitney_u("Group A", NIST_GROUP_A, "Group B", NIST_GROUP_B).value
    # NIST's published U (the smaller of U_a=81, U_b=40) is exactly 40 --
    # deterministic given the data + tie handling, an exact match expected.
    assert r.statistic == 40.0


def test_mann_whitney_p_value_close_to_nist_z_approximation():
    """NIST's own page uses a *simplified*, non-tie-corrected normal
    approximation (z=-1.346 -> two-sided p~=0.1783); scipy's default
    'auto' method tie-corrects (this dataset has real ties: 0.48, 0.59,
    0.65, 0.67 each appear in both groups) and applies a continuity
    correction, so an exact match to NIST's simplified figure is not
    expected -- only close agreement, asserted with a loose tolerance and
    explained here rather than silently asserting a tight bound."""
    r = mann_whitney_u("Group A", NIST_GROUP_A, "Group B", NIST_GROUP_B).value
    from scipy.stats import norm

    nist_p = 2 * (1 - norm.cdf(1.346))
    assert r.p_value == pytest.approx(nist_p, abs=0.015)
    assert r.significant is False  # NIST: "we do not reject the null hypothesis"


def test_mann_whitney_rank_biserial_matches_u_formula_exactly():
    r = mann_whitney_u("Group A", NIST_GROUP_A, "Group B", NIST_GROUP_B).value
    # r = 1 - 2U/(n1*n2) = 1 - 2*40/121
    assert r.rank_biserial_r == pytest.approx(1 - 2 * 40 / 121, abs=1e-9)


def test_mann_whitney_hodges_lehmann_shift_is_the_median_of_pairwise_diffs():
    hl, ci = hodges_lehmann_two_sample(NIST_GROUP_A, NIST_GROUP_B, 0.95)
    import statistics

    diffs = sorted(x - y for x in NIST_GROUP_A for y in NIST_GROUP_B)
    assert hl == pytest.approx(statistics.median(diffs), abs=1e-9)
    assert ci[0] < hl < ci[1]


def test_mann_whitney_equal_shape_caveat_present():
    r = mann_whitney_u("A", NIST_GROUP_A, "B", NIST_GROUP_B).value
    assert "distributions, not medians" in r.equal_shape_caveat


# --- Exact-enumeration Wilcoxon signed-rank fixture (256 sign patterns) ----
# diffs chosen with no ties among |diffs| so ranks 1..8 are unambiguous.
WILCOXON_DIFFS = [3, -1, 4, 2, -1.5, 5, 2.5, -0.5]


def _brute_force_wilcoxon_two_sided_p(diffs: list[float]) -> tuple[float, float]:
    """Independent exact enumeration over all 2^n sign patterns -- returns
    (W = min(W+, W-) for the observed data, exact two-sided p). This does
    not call scipy at all; it is a from-scratch cross-check."""
    ranks = rankdata([abs(d) for d in diffs])
    signs = [1 if d > 0 else -1 for d in diffs]
    w_plus_obs = sum(r for r, s in zip(ranks, signs) if s > 0)
    w_minus_obs = sum(ranks) - w_plus_obs
    w_obs = min(w_plus_obs, w_minus_obs)

    total = 0
    count_le = 0
    for combo in itertools.product([1, -1], repeat=len(diffs)):
        total += 1
        wplus = sum(r for r, s in zip(ranks, combo) if s > 0)
        if wplus <= w_obs:
            count_le += 1
    p_two_sided = min(1.0, 2 * count_le / total)
    return w_obs, p_two_sided


def test_wilcoxon_statistic_and_p_match_independent_exact_enumeration():
    expected_w, expected_p = _brute_force_wilcoxon_two_sided_p(WILCOXON_DIFFS)
    assert expected_w == 6.0  # brute-force sanity: matches the hand-derived W below
    assert expected_p == pytest.approx(0.109375, abs=1e-9)  # 28/256

    r = wilcoxon_signed_rank("before-after", WILCOXON_DIFFS).value
    assert r.statistic == pytest.approx(expected_w, abs=1e-9)
    assert r.p_value == pytest.approx(expected_p, abs=1e-9)
    assert r.significant is False  # 0.109 > 0.05


def test_wilcoxon_rank_biserial_hand_computed():
    # Ranks of |diffs| for [3,-1,4,2,-1.5,5,2.5,-0.5]: [6,2,7,4,3,8,5,1]
    # (verified against scipy.stats.rankdata during development).
    # Positive diffs (3,4,2,5,2.5) -> ranks (6,7,4,8,5) -> W+ = 30
    # Negative diffs (-1,-1.5,-0.5) -> ranks (2,3,1) -> W- = 6
    # r_rb = (30-6)/(30+6) = 24/36 = 0.6667
    r = wilcoxon_signed_rank("before-after", WILCOXON_DIFFS).value
    assert r.rank_biserial_r == pytest.approx(24 / 36, abs=1e-9)


def test_wilcoxon_drops_zero_differences_and_notes_it():
    diffs_with_zero = WILCOXON_DIFFS + [0.0, 0.0]
    r = wilcoxon_signed_rank("before-after", diffs_with_zero).value
    assert any("zero difference" in a for a in r.assumptions_checked)
    # the statistic/p should be identical to the no-zeros fixture, since
    # zero_method='wilcox' discards zeros before ranking either way.
    r_no_zeros = wilcoxon_signed_rank("before-after", WILCOXON_DIFFS).value
    assert r.statistic == pytest.approx(r_no_zeros.statistic, abs=1e-9)
    assert r.p_value == pytest.approx(r_no_zeros.p_value, abs=1e-9)


def test_hodges_lehmann_one_sample_is_median_of_walsh_averages():
    hl, ci = hodges_lehmann_one_sample(WILCOXON_DIFFS, 0.95)
    import statistics

    n = len(WILCOXON_DIFFS)
    walsh = [(WILCOXON_DIFFS[i] + WILCOXON_DIFFS[j]) / 2 for i in range(n) for j in range(i, n)]
    assert hl == pytest.approx(statistics.median(walsh), abs=1e-9)
    assert ci[0] <= hl <= ci[1]
