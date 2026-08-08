"""stats/hypothesis_categorical.py -- T-17's count-data family: chi-square
independence (+ Cramer's V; EXIT-07 Cochran preflight), two-proportion z
(+ risk-difference CI), and one-proportion exact binomial vs target.

Formula sources (NIST/SEMATECH e-Handbook, fetched live 2026-08-08):
  - Two-proportion z: §7.3.3 "How can we determine whether two processes
    produce the same proportion of defectives?" (Case 1, large-sample
    normal approximation) -- the pooled-variance z-test:
    https://www.itl.nist.gov/div898/handbook/prc/section3/prc33.htm
  - One-proportion vs target: §7.2.4 "Does the proportion of defectives
    meet requirements?" -- states the analogous small-sample restriction
    matrix EXIT-06 also uses (there stated on p0; here on the sample's own
    p-hat, per the frozen matrix wording -- see EXIT-06 note below):
    https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm
    NIST's own page tests via the z-approximation; this build brief calls
    for the *exact* binomial test instead (scipy.stats.binomtest) -- more
    defensible right at EXIT-06's small-n floor, where z-approximation
    error is largest. NIST §7.2.4's own example (N=200, x=26, p0=0.10) is
    reused in tests/test_stats_hypothesis_categorical.py as an approximate
    cross-check between the two methods, not an exact-match assertion.
  - Chi-square independence: standard Pearson chi-square-of-independence
    construction (Pearson, K. (1900). "On the criterion that a given
    system of deviations..." Philosophical Magazine, 50(302), 157-175);
    NIST/SEMATECH's chi-square material in this handbook is goodness-of-
    fit framed (§1.3.5.15), not contingency-table-independence framed, so
    the family is verified here against a fully hand-computed fixture
    instead of a fetched worked example (task brief's documented fallback).

CI methods (risk difference): Newcombe's Method 10 (Newcombe, R.G. (1998).
"Interval estimation for the difference between independent proportions:
comparison of eleven methods." Statistics in Medicine, 17(8), 873-890) --
built from two per-sample Wilson score intervals (Wilson, E.B. (1927).
"Probable inference, the law of succession, and statistical inference."
JASA, 22(158), 209-212). Chosen over the plain normal-approximation CI
because it stays sane at the small n this suite's floors allow (EXIT-06:
n*phat>=5), where the normal approximation can overshoot [0,1].
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict
from scipy import stats

from ..provenance import Computed, compute
from .constants import (
    CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR,
    CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION,
    CHI_SQUARE_COCHRAN_MIN_EXPECTED,
    HYP_ALPHA_TWO_SIDED,
    HYP_CI_CONFIDENCE_LEVEL,
)
from .hypothesis_common import (
    PRACTICAL_SIGNIFICANCE_PROMPT,
    ContingencyCell,
    GroupInput,
    GroupSummary,
    HypothesisTestResult,
    PlainLanguageBlock,
    cramers_v_magnitude,
    group_successes_n,
    p_value_sentence,
    two_sided_critical_z,
)


def wilson_score_interval(successes: int, n: int, confidence_level: float = HYP_CI_CONFIDENCE_LEVEL) -> tuple[float, float]:
    """Wilson (1927) score interval for a single proportion -- see module
    docstring. Clipped to [0, 1] (the closed-form can graze past either
    bound by float error at p-hat in {0, 1})."""
    if n <= 0:
        raise ValueError("wilson_score_interval requires n > 0")
    phat = successes / n
    z = two_sided_critical_z(confidence_level)
    denom = 1.0 + (z**2) / n
    center = (phat + (z**2) / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + (z**2) / (4 * n**2)) ** 0.5)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def newcombe_difference_ci(
    x1: int, n1: int, x2: int, n2: int, confidence_level: float = HYP_CI_CONFIDENCE_LEVEL
) -> tuple[float, float]:
    """Newcombe (1998) Method 10 CI for p1-p2, built from each sample's own
    Wilson interval -- see module docstring."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson_score_interval(x1, n1, confidence_level)
    l2, u2 = wilson_score_interval(x2, n2, confidence_level)
    d = p1 - p2
    lo = d - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5
    hi = d + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5
    return max(-1.0, lo), min(1.0, hi)


# --- EXIT-07: Cochran's rule preflight ---------------------------------------


class CochranCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    expected: tuple[tuple[float, ...], ...]
    cell_count: int
    cells_below_min_expected: int
    fraction_at_or_above_min_expected: float
    min_cell_expected: float
    passed: bool  # matrix §4a EXIT-07: >=80% of cells expected>=5 AND no cell expected<1


def expected_counts(observed: Sequence[Sequence[int]]) -> list[list[float]]:
    arr = np.asarray(observed, dtype=float)
    row_totals = arr.sum(axis=1, keepdims=True)
    col_totals = arr.sum(axis=0, keepdims=True)
    grand_total = arr.sum()
    if grand_total <= 0:
        raise ValueError("expected_counts requires at least one observation in the table")
    return (row_totals @ col_totals / grand_total).tolist()


def cochran_preflight(observed: Sequence[Sequence[int]]) -> CochranCheck:
    """Cochran's rule (matrix §4a EXIT-07): expected count >= 5 in >= 80%
    of cells, AND no cell's expected count < 1 -- else the table is too
    sparse for a trustworthy chi-square, and the route exits rather than
    computing a number the method itself can't stand behind."""
    expected = expected_counts(observed)
    flat = [c for row in expected for c in row]
    cell_count = len(flat)
    below_min = sum(1 for c in flat if c < CHI_SQUARE_COCHRAN_MIN_EXPECTED)
    fraction_ok = (cell_count - below_min) / cell_count
    min_cell = min(flat)
    passed = fraction_ok >= CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION and min_cell >= CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR
    return CochranCheck(
        expected=tuple(tuple(row) for row in expected), cell_count=cell_count,
        cells_below_min_expected=below_min, fraction_at_or_above_min_expected=fraction_ok,
        min_cell_expected=min_cell, passed=passed,
    )


# --- Chi-square independence --------------------------------------------------


def chi_square_independence(
    observed: Sequence[Sequence[int]],
    *,
    row_labels: Sequence[str] | None = None,
    col_labels: Sequence[str] | None = None,
    alpha: float = HYP_ALPHA_TWO_SIDED,
) -> Computed[HypothesisTestResult]:
    """Assumes the EXIT-07 Cochran preflight already passed (the selector's
    job, not this function's -- same "the check runs, then the math runs"
    separation as msa.py's resolution pre-check before repeatability%)."""
    arr = np.asarray(observed, dtype=float)
    r, c = arr.shape
    rows = list(row_labels) if row_labels else [f"row {i + 1}" for i in range(r)]
    cols = list(col_labels) if col_labels else [f"col {j + 1}" for j in range(c)]
    n = int(arr.sum())

    chi2, p_value, dof, expected = stats.chi2_contingency(observed, correction=False)
    cramers_v = float(np.sqrt(chi2 / (n * (min(r, c) - 1)))) if min(r, c) > 1 and n > 0 else 0.0
    significant = bool(p_value < alpha)

    cells = tuple(
        ContingencyCell(row=rows[i], col=cols[j], observed=int(arr[i, j]), expected=float(expected[i][j]))
        for i in range(r) for j in range(c)
    )

    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Tested whether the row categories ({', '.join(rows)}) and column categories ({', '.join(cols)}) "
            f"are associated -- a {r}x{c} contingency table, n={n}, chi-square test of independence."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Cramer's V = {cramers_v:.3f} -- a {cramers_v_magnitude(cramers_v)} association between the row "
            "and column categories (0 = no association, 1 = perfect association)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="chi_square_independence", statistic_name="chi-square", statistic=float(chi2), df=float(dof),
        p_value=float(p_value), alpha=alpha, significant=significant,
        effect_size_name="Cramer's V", effect_size_value=cramers_v, effect_size_ci=None,
        effect_size_ci_method=(
            "not computed -- no simple closed-form CI for Cramer's V (a bootstrap or noncentral-chi-square CI "
            "is out of scope for this v1 route); the point estimate is reported plainly."
        ),
        groups=(), contingency=cells, cramers_v=cramers_v,
        assumptions_checked=[
            f"Cochran's rule cleared before this test ran (matrix §4a EXIT-07): >= "
            f"{CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION:.0%} of cells expected >= {CHI_SQUARE_COCHRAN_MIN_EXPECTED:g}, "
            f"no cell expected < {CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR:g}",
            "counts are independent observations (one per unit, not repeated measures)",
        ],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method=(
            "Pearson chi-square test of independence (Pearson 1900; no Yates continuity correction -- standard "
            "practice for r x c tables, applied uniformly here) + Cramer's V = sqrt(chi2/(n*(min(r,c)-1)))"
        ),
        input_data={"observed": [list(row) for row in observed], "row_labels": rows, "col_labels": cols},
        assumptions_checked=["Cochran's rule cleared (matrix §4a EXIT-07)"],
    )


# --- Proportions: two-sample and one-sample-vs-target ------------------------


def two_proportion_z(group_a: GroupInput, group_b: GroupInput, *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    x1, n1 = group_successes_n(group_a)
    x2, n2 = group_successes_n(group_b)
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se0 = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    z = (p1 - p2) / se0 if se0 > 0 else 0.0
    p_value = float(2 * (1 - stats.norm.cdf(abs(z))))
    significant = bool(p_value < alpha)

    risk_diff = p1 - p2
    ci = newcombe_difference_ci(x1, n1, x2, n2, HYP_CI_CONFIDENCE_LEVEL)
    groups = (
        GroupSummary(label=group_a.label, n=n1, successes=x1, proportion=p1),
        GroupSummary(label=group_b.label, n=n2, successes=x2, proportion=p2),
    )
    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Compared the proportion for {group_a.label} ({x1}/{n1} = {p1:.1%}) against {group_b.label} "
            f"({x2}/{n2} = {p2:.1%}) using a two-proportion z-test."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Risk difference = {risk_diff:+.1%} ({group_a.label} minus {group_b.label}), 95% CI "
            f"[{ci[0]:+.1%}, {ci[1]:+.1%}] (Newcombe's method)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="two_proportion_z", statistic_name="z", statistic=float(z), p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="risk difference (p1 - p2)", effect_size_value=risk_diff,
        effect_size_ci=ci, effect_size_ci_method="Newcombe (1998) method 10, built from per-sample Wilson score intervals",
        groups=groups, risk_difference=risk_diff, risk_difference_ci=ci, risk_difference_ci_method="Newcombe (1998) method 10",
        assumptions_checked=["n*phat >= 5 and n*(1-phat) >= 5 per sample cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method="two-proportion pooled z-test (NIST/SEMATECH §7.3.3, Case 1) + Newcombe (1998) method-10 risk-difference CI",
        input_data={"a": {"successes": x1, "n": n1}, "b": {"successes": x2, "n": n2}},
        assumptions_checked=["n*phat>=5 and n*(1-phat)>=5 per sample"],
    )


def one_proportion_exact(group: GroupInput, target: float, *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    if not (0.0 <= target <= 1.0):
        raise ValueError("one_proportion_exact: target must be a proportion in [0, 1]")
    x, n = group_successes_n(group)
    phat = x / n
    test = stats.binomtest(x, n, p=target, alternative="two-sided")
    p_value = float(test.pvalue)
    significant = bool(p_value < alpha)
    wilson_ci = test.proportion_ci(confidence_level=HYP_CI_CONFIDENCE_LEVEL, method="wilson")
    ci_lo, ci_hi = float(wilson_ci.low), float(wilson_ci.high)
    diff = phat - target

    groups = (GroupSummary(label=group.label, n=n, successes=x, proportion=phat),)
    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Compared {group.label}'s observed proportion ({x}/{n} = {phat:.1%}) against the target "
            f"{target:.1%} using the exact binomial test."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Observed proportion is {diff:+.1%} away from the target; 95% CI on the observed proportion "
            f"[{ci_lo:.1%}, {ci_hi:.1%}] (Wilson score interval)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="one_proportion", statistic_name="observed proportion", statistic=phat, p_value=p_value,
        alpha=alpha, significant=significant, effect_size_name="proportion difference (observed - target)",
        effect_size_value=diff, effect_size_ci=(ci_lo - target, ci_hi - target),
        effect_size_ci_method="Wilson score interval on the observed proportion (scipy.stats.binomtest), recentered on the target",
        groups=groups, risk_difference=diff, risk_difference_ci=(ci_lo - target, ci_hi - target),
        risk_difference_ci_method="Wilson score interval, recentered",
        assumptions_checked=["n*phat >= 5 and n*(1-phat) >= 5 cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method="exact binomial test vs target (scipy.stats.binomtest, two-sided) + Wilson score CI on the observed proportion",
        input_data={"successes": x, "n": n, "target": target},
        assumptions_checked=["n*phat>=5 and n*(1-phat)>=5"],
    )
