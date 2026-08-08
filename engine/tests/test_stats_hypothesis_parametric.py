"""Tests for stats/hypothesis_parametric.py -- NIST/SEMATECH worked
examples (fetched live 2026-08-08, transcribed verbatim below) for Welch
t, one-sample t, and one-way ANOVA, plus a hand-computed paired-t fixture
with the arithmetic shown. scipy cross-checks alone are not treated as
sufficient (task brief) -- every number below is checked against a
published or hand-derived value, not just "scipy agrees with itself."
"""

import pytest

from sigma_engine.stats.hypothesis_parametric import one_sample_t, one_way_anova, paired_t, welch_two_sample_t

# --- NIST/SEMATECH §7.3.1 "Do two processes have the same mean?" -----------
# https://www.itl.nist.gov/div898/handbook/prc/section3/prc31.htm
# "Example of unequal number of data points" -- assembly time, minutes.
NIST_PROCESS_1_OLD = [32, 37, 35, 28, 41, 44, 35, 31, 34, 38, 42]  # n=11
NIST_PROCESS_2_NEW = [36, 31, 30, 31, 34, 36, 29, 32, 31]  # n=9


def test_welch_t_matches_nist_7_3_1_worked_example():
    r = welch_two_sample_t("Process 1 (Old)", NIST_PROCESS_1_OLD, "Process 2 (New)", NIST_PROCESS_2_NEW).value
    # NIST's published values: mean1=36.0909, mean2=32.2222, sd1=4.9082,
    # sd2=2.5386, t=2.2694, df(Welch-Satterthwaite)=15.5.
    assert r.groups[0].mean == pytest.approx(36.0909, abs=1e-4)
    assert r.groups[1].mean == pytest.approx(32.2222, abs=1e-4)
    assert r.groups[0].sd == pytest.approx(4.9082, abs=1e-4)
    assert r.groups[1].sd == pytest.approx(2.5386, abs=1e-4)
    assert r.statistic == pytest.approx(2.2694, abs=1e-4)
    assert r.df == pytest.approx(15.5, abs=0.05)
    # NIST's one-sided test rejected at alpha=0.05 (critical 1.746 < t);
    # our two-sided p must therefore be < 0.10 (twice the one-sided bound).
    assert r.p_value < 0.10
    assert r.significant is True  # two-sided p ~= 0.0379 < 0.05 too


def test_welch_t_effect_size_and_ci_are_present_and_sane():
    r = welch_two_sample_t("A", NIST_PROCESS_1_OLD, "B", NIST_PROCESS_2_NEW).value
    assert r.effect_size_name.startswith("Cohen's d")
    assert r.effect_size_value == pytest.approx(0.990, abs=0.01)
    assert r.effect_size_ci is not None
    lo, hi = r.effect_size_ci
    assert lo < r.effect_size_value < hi
    assert "not an exact noncentral-t CI" in r.effect_size_ci_method


def test_welch_plain_language_never_bare_p_value():
    r = welch_two_sample_t("A", NIST_PROCESS_1_OLD, "B", NIST_PROCESS_2_NEW).value
    assert r.plain_language.comparison_summary
    assert r.plain_language.p_value_meaning
    assert r.plain_language.effect_size_in_words
    assert "≠" in r.plain_language.practical_significance_prompt or "compare the effect" in r.plain_language.practical_significance_prompt


# --- NIST/SEMATECH §7.2.2 "Are the data consistent with the assumed process mean?" ---
# https://www.itl.nist.gov/div898/handbook/prc/section2/prc22.htm
# Wafer particle counts, target (long-run process average) = 50.
NIST_WAFER_COUNTS = [50, 48, 44, 56, 61, 52, 53, 55, 67, 51]  # n=10


def test_one_sample_t_matches_nist_7_2_2_worked_example():
    r = one_sample_t("wafer particle counts", NIST_WAFER_COUNTS, 50).value
    # NIST's published values: mean=53.7, sd=6.567, t=1.782, df=9, fails to
    # reject at alpha=0.05 two-sided (critical t=2.262).
    assert r.groups[0].mean == pytest.approx(53.7, abs=1e-3)
    assert r.groups[0].sd == pytest.approx(6.567, abs=1e-3)
    assert r.statistic == pytest.approx(1.782, abs=1e-3)
    assert r.df == 9.0
    assert r.significant is False  # |t|=1.782 < critical 2.262


# --- NIST/SEMATECH §7.4.3.3 "The ANOVA table and tests of hypotheses about means" ---
# https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm
# Resistor temperature experiment, 3 levels, n=5 each.
NIST_ANOVA_LEVEL1 = [6.9, 5.4, 5.8, 4.6, 4.0]
NIST_ANOVA_LEVEL2 = [8.3, 6.8, 7.8, 9.2, 6.5]
NIST_ANOVA_LEVEL3 = [8.0, 10.5, 8.1, 6.9, 9.3]


def test_anova_matches_nist_7_4_3_3_worked_example():
    r = one_way_anova([("Level 1", NIST_ANOVA_LEVEL1), ("Level 2", NIST_ANOVA_LEVEL2), ("Level 3", NIST_ANOVA_LEVEL3)]).value
    # NIST's published ANOVA table: SST=27.897, DFT=2, MST=13.949;
    # SSE=17.452, DFE=12, MSE=1.454; F=9.59, p=0.00325.
    assert r.groups[0].mean == pytest.approx(5.34, abs=1e-2)
    assert r.groups[1].mean == pytest.approx(7.72, abs=1e-2)
    assert r.groups[2].mean == pytest.approx(8.56, abs=1e-2)
    assert r.statistic == pytest.approx(9.59, abs=0.01)
    assert r.df_between == 2.0
    assert r.df_within == 12.0
    assert r.p_value == pytest.approx(0.00325, abs=1e-4)
    assert r.significant is True


def test_anova_eta_squared_matches_ss_ratio():
    r = one_way_anova([("Level 1", NIST_ANOVA_LEVEL1), ("Level 2", NIST_ANOVA_LEVEL2), ("Level 3", NIST_ANOVA_LEVEL3)]).value
    # eta^2 = SST / (SST+SSE) = 27.897 / 45.349 (NIST's own SS table).
    assert r.effect_size_value == pytest.approx(27.897 / 45.349, abs=1e-3)
    assert r.effect_size_ci is None  # documented: no simple CI for eta^2 in v1
    assert "noncentral F" in r.effect_size_ci_method


def test_anova_exit13_attaches_on_significant_result_by_default():
    r = one_way_anova([("Level 1", NIST_ANOVA_LEVEL1), ("Level 2", NIST_ANOVA_LEVEL2), ("Level 3", NIST_ANOVA_LEVEL3)]).value
    assert r.exit13 is not None
    assert r.exit13.exit_id == "EXIT-13"
    assert "guided pairwise" in r.exit13.message
    assert "Level 3" in r.exit13.largest_vs_smallest and "Level 1" in r.exit13.largest_vs_smallest
    assert len(r.exit13.interim_read) == 3
    # no pairwise p-value anywhere in the interim read text:
    assert "p=" not in r.exit13.largest_vs_smallest and "p =" not in r.exit13.largest_vs_smallest


def test_anova_exit13_suppressed_when_question_is_declared_omnibus():
    r = one_way_anova(
        [("Level 1", NIST_ANOVA_LEVEL1), ("Level 2", NIST_ANOVA_LEVEL2), ("Level 3", NIST_ANOVA_LEVEL3)],
        question_intent="omnibus_any_group_differs",
    ).value
    assert r.exit13 is None


NOT_SIGNIFICANT_GROUPS = [("A", [10.0, 10.1, 9.9, 10.05]), ("B", [10.02, 9.98, 10.03, 10.0]), ("C", [9.95, 10.05, 10.0, 10.01])]


def test_anova_exit13_does_not_attach_on_nonsignificant_result():
    r = one_way_anova(NOT_SIGNIFICANT_GROUPS).value
    assert r.significant is False
    assert r.exit13 is None


# --- Hand-computed paired-t fixture (arithmetic shown; NIST §7.3.1.1 formula) ---
# https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm
# d_i = Y_i - Z_i; dbar = mean(d); s_d = sample sd of d (n-1); t = dbar/(s_d/sqrt(n)).
PAIRED_BEFORE = [10.0, 12.0, 9.0, 11.0, 10.0, 13.0, 8.0, 12.0]  # n=8
PAIRED_AFTER = [8.0, 9.0, 7.0, 9.0, 8.0, 10.0, 7.0, 9.0]
# diffs = [2, 3, 2, 2, 2, 3, 1, 3]; dbar = 18/8 = 2.25
# variance (n-1): deviations = [-0.25,0.75,-0.25,-0.25,-0.25,0.75,-1.25,0.75]
# sum of squares = 0.0625+0.5625+0.0625+0.0625+0.0625+0.5625+1.5625+0.5625 = 3.5
# s_d^2 = 3.5/7 = 0.5, s_d = 0.70710678; t = 2.25 / (0.70710678/sqrt(8)) = 2.25/0.25 = 9.0
HAND_DBAR = 2.25
HAND_SD = 0.7071067811865476
HAND_T = 9.0


def test_paired_t_hand_fixture_matches_shown_arithmetic():
    r = paired_t("before", PAIRED_BEFORE, "after", PAIRED_AFTER).value
    assert r.statistic == pytest.approx(HAND_T, abs=1e-6)
    assert r.df == 7.0
    # two-sided p for t=9.0, df=7 is tiny -- assert an exact scipy cross-check as a secondary confirmation.
    from scipy import stats as scipy_stats

    expected_p = 2 * scipy_stats.t.sf(HAND_T, 7)
    assert r.p_value == pytest.approx(expected_p, rel=1e-9)
    assert r.significant is True


def test_paired_t_cohens_dz_hand_computed():
    # d_z = dbar / s_d = 2.25 / 0.70710678 = 3.181980...
    r = paired_t("before", PAIRED_BEFORE, "after", PAIRED_AFTER).value
    assert r.effect_size_value == pytest.approx(HAND_DBAR / HAND_SD, abs=1e-6)


def test_paired_t_requires_equal_length_arrays():
    with pytest.raises(ValueError):
        paired_t("a", [1, 2, 3], "b", [1, 2])
