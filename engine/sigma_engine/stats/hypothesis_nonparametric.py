"""stats/hypothesis_nonparametric.py -- T-17's rank-based family: Mann-
Whitney U (the nonparametric switch target for two_independent) and
Wilcoxon signed-rank (the switch target for paired AND one_sample_vs_target
-- the latter runs signed-rank on `sample - target` differences, which is
exactly the paired case against a constant "second sample").

Formula / reference sources (NIST/SEMATECH e-Handbook, fetched live
2026-08-08 -- see tests/test_stats_hypothesis_nonparametric.py for the
transcribed NIST worked example and hand-built exact-enumeration fixture):
  - Mann-Whitney U: §7.3.5 "Do two arbitrary processes have the same
    central tendency?" -- procedure, large-sample z-approximation, and a
    full worked numeric example (wafer particle-count data) reused here:
    https://www.itl.nist.gov/div898/handbook/prc/section3/prc35.htm
  - Wilcoxon signed-rank: no NIST/SEMATECH worked numeric example was
    found in this handbook (its paired-data page, §7.3.1.1, is the
    *parametric* paired-t case) -- verified instead against a hand-built,
    exact-enumeration-checkable tiny-n fixture (task brief's documented
    fallback for the nonparametric family).

Effect sizes:
  - Rank-biserial r, Mann-Whitney: r = 1 - 2U/(n1*n2), Kerby, D.S. (2014).
    "The simple difference formula: An approach to teaching nonparametric
    correlation." Comprehensive Psychology, 3, 11.IT.3.1.
  - Matched-pairs rank-biserial r, Wilcoxon: r = (W+ - W-)/(W+ + W-), King,
    B.M., & Minium, E.W. (2008). Statistical Reasoning in the Behavioral
    Sciences (5th ed.), Wiley -- computed here from the signed ranks
    directly (scipy's own `statistic` doesn't expose W+ and W- separately).
  - Hodges-Lehmann shift estimate + CI (both routes): Hodges, J.L., &
    Lehmann, E.L. (1963). "Estimates of location based on rank tests."
    Annals of Mathematical Statistics, 34(2), 598-611 -- the median of
    pairwise differences (two-sample) or Walsh averages (one-sample/
    paired), with a normal-approximation CI per Conover, W.J. (1999).
    Practical Nonparametric Statistics (3rd ed.), Wiley, §5.1. Labeled
    "normal approximation" throughout, not sold as exact.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from scipy import stats

from ..provenance import Computed, compute
from .constants import HYP_ALPHA_TWO_SIDED, HYP_CI_CONFIDENCE_LEVEL
from .descriptive import mean as sample_mean
from .descriptive import sample_sd
from .hypothesis_common import (
    PRACTICAL_SIGNIFICANCE_PROMPT,
    GroupSummary,
    HypothesisTestResult,
    PlainLanguageBlock,
    correlation_r_magnitude,
    nonzero_diff_count,
    p_value_sentence,
    two_sided_critical_z,
)

MANN_WHITNEY_EQUAL_SHAPE_CAVEAT = (
    "With very different group shapes, this test compares whole distributions, not medians -- read the shift "
    "estimate with that caveat (PLAN §4.1's switch-rule note)."
)


def hodges_lehmann_two_sample(a: Sequence[float], b: Sequence[float], confidence_level: float) -> tuple[float, tuple[float, float]]:
    """Median of all pairwise differences a_i - b_j, with the Conover
    (1999) normal-approximation CI (module docstring)."""
    n1, n2 = len(a), len(b)
    diffs = sorted(x - y for x in a for y in b)
    n_pairs = n1 * n2
    hl = float(np.median(diffs))
    z = two_sided_critical_z(confidence_level)
    c = z * math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    k = max(1, min(math.floor(n_pairs / 2 - c), n_pairs))
    lower, upper = diffs[k - 1], diffs[n_pairs - k]
    if upper < lower:
        lower, upper = upper, lower
    return hl, (lower, upper)


def hodges_lehmann_one_sample(diffs: Sequence[float], confidence_level: float) -> tuple[float, tuple[float, float]]:
    """Median of the Walsh averages (d_i+d_j)/2, i<=j, with the Conover
    (1999) normal-approximation CI built on the Wilcoxon signed-rank
    statistic's own null mean/sd."""
    n = len(diffs)
    walsh = sorted((diffs[i] + diffs[j]) / 2 for i in range(n) for j in range(i, n))
    n_walsh = len(walsh)  # n(n+1)/2
    hl = float(np.median(walsh))
    z = two_sided_critical_z(confidence_level)
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    c = z * sd
    k = max(1, min(math.floor(n_walsh / 2 - c), n_walsh))
    lower, upper = walsh[k - 1], walsh[n_walsh - k]
    if upper < lower:
        lower, upper = upper, lower
    return hl, (lower, upper)


def mann_whitney_u(label_a: str, a: Sequence[float], label_b: str, b: Sequence[float], *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    n1, n2 = len(a), len(b)
    test = stats.mannwhitneyu(a, b, alternative="two-sided", method="auto")
    u_stat, p_value = float(test.statistic), float(test.pvalue)
    significant = bool(p_value < alpha)

    r_rb = 1 - (2 * u_stat) / (n1 * n2)
    hl, hl_ci = hodges_lehmann_two_sample(a, b, HYP_CI_CONFIDENCE_LEVEL)
    med_a, med_b = float(np.median(a)), float(np.median(b))

    groups = (
        GroupSummary(label=label_a, n=n1, mean=sample_mean(a), sd=sample_sd(a) if n1 >= 2 else None, median=med_a),
        GroupSummary(label=label_b, n=n2, mean=sample_mean(b), sd=sample_sd(b) if n2 >= 2 else None, median=med_b),
    )
    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Compared {label_a} (n={n1}, median={med_a:.4g}) against {label_b} (n={n2}, median={med_b:.4g}) "
            "using the Mann-Whitney U test (the rank-based route, used here in place of Welch's t)."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Rank-biserial r = {r_rb:.2f} -- a {correlation_r_magnitude(r_rb)} effect. Hodges-Lehmann shift "
            f"estimate = {hl:+.4g}, 95% CI [{hl_ci[0]:+.4g}, {hl_ci[1]:+.4g}]."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="mann_whitney_u", statistic_name="U", statistic=u_stat, p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="rank-biserial correlation r", effect_size_value=r_rb,
        effect_size_ci=None,
        effect_size_ci_method="not computed for r itself -- this route's CI-bearing effect size is the Hodges-Lehmann shift below",
        groups=groups, hodges_lehmann_shift=hl, hodges_lehmann_ci=hl_ci,
        hodges_lehmann_ci_method="normal approximation to the Mann-Whitney null distribution (Hodges & Lehmann 1963; Conover 1999, §5.1)",
        rank_biserial_r=r_rb, equal_shape_caveat=MANN_WHITNEY_EQUAL_SHAPE_CAVEAT,
        assumptions_checked=["n >= 4 per group cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method=(
            "Mann-Whitney U (scipy.stats.mannwhitneyu, method='auto': exact for min(n)<=8 and no ties, else "
            "normal approximation; NIST/SEMATECH §7.3.5) + rank-biserial r=1-2U/(n1*n2) (Kerby 2014) + "
            "Hodges-Lehmann shift/CI (Hodges & Lehmann 1963)"
        ),
        input_data={"a": {"label": label_a, "values": list(a)}, "b": {"label": label_b, "values": list(b)}},
        assumptions_checked=["n >= 4 per group"],
    )


def wilcoxon_signed_rank(label: str, diffs: Sequence[float], *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    """`diffs` is either paired-a-minus-paired-b, or sample-minus-target
    for the one-sample-vs-target route -- both are "one array of signed
    differences" to this function (module docstring)."""
    n_total = len(diffs)
    n_nonzero = nonzero_diff_count(diffs)
    test = stats.wilcoxon(diffs, zero_method="wilcox", alternative="two-sided", method="auto")
    w_stat, p_value = float(test.statistic), float(test.pvalue)
    significant = bool(p_value < alpha)

    nonzero = [d for d in diffs if d != 0]
    ranks = stats.rankdata([abs(d) for d in nonzero])
    w_pos = float(sum(r for r, d in zip(ranks, nonzero) if d > 0))
    w_neg = float(sum(r for r, d in zip(ranks, nonzero) if d < 0))
    r_rb = (w_pos - w_neg) / (w_pos + w_neg) if (w_pos + w_neg) > 0 else 0.0

    hl, hl_ci = hodges_lehmann_one_sample(diffs, HYP_CI_CONFIDENCE_LEVEL)
    median_diff = float(np.median(diffs))
    dropped = n_total - n_nonzero
    zero_note = f"; {dropped} zero difference(s) dropped before ranking (zero_method='wilcox')" if dropped else ""

    groups = (GroupSummary(label=label, n=n_total, median=median_diff),)
    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Compared {label} ({n_total} differences, {n_nonzero} non-zero, median difference={median_diff:+.4g}) "
            "using the Wilcoxon signed-rank test."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Matched rank-biserial r = {r_rb:.2f} -- a {correlation_r_magnitude(r_rb)} effect. Hodges-Lehmann "
            f"shift estimate = {hl:+.4g}, 95% CI [{hl_ci[0]:+.4g}, {hl_ci[1]:+.4g}]."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="wilcoxon_signed_rank", statistic_name="W", statistic=w_stat, p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="matched-pairs rank-biserial correlation r", effect_size_value=r_rb,
        effect_size_ci=None,
        effect_size_ci_method="not computed for r itself -- this route's CI-bearing effect size is the Hodges-Lehmann shift below",
        groups=groups, hodges_lehmann_shift=hl, hodges_lehmann_ci=hl_ci,
        hodges_lehmann_ci_method="normal approximation to the Wilcoxon signed-rank null distribution (Hodges & Lehmann 1963; Conover 1999)",
        rank_biserial_r=r_rb,
        assumptions_checked=[f">= 6 non-zero differences cleared (matrix §4a EXIT-06){zero_note}"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method=(
            "Wilcoxon signed-rank (scipy.stats.wilcoxon, zero_method='wilcox', method='auto') + matched-pairs "
            "rank-biserial r=(W+-W-)/(W++W-) (King & Minium 2008) + Hodges-Lehmann shift/CI on the Walsh averages "
            "(Hodges & Lehmann 1963; Conover 1999)"
        ),
        input_data={"label": label, "diffs": list(diffs)},
        assumptions_checked=[">= 6 non-zero differences"],
    )
