"""stats/hypothesis_parametric.py -- T-17's parametric family: Welch
two-sample t (scipy, equal_var=False -- the default the selector routes to,
no equal-variance assumption to trip on), paired t, one-sample t vs target,
and one-way ANOVA (+ eta-squared).

Formula / reference sources (NIST/SEMATECH e-Handbook, fetched live
2026-08-08 -- see tests/test_stats_hypothesis_parametric.py for the
transcribed worked examples and hand-verified fixtures):
  - Welch t: §7.3.1 "Do two processes have the same mean?" (unequal-
    variance form + Welch-Satterthwaite df):
    https://www.itl.nist.gov/div898/handbook/prc/section3/prc31.htm
  - Paired t: §7.3.1.1 "Analysis of paired observations":
    https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm
  - One-sample t: §7.2.2 "Are the data consistent with the assumed
    process mean?":
    https://www.itl.nist.gov/div898/handbook/prc/section2/prc22.htm
  - One-way ANOVA: §7.4.3.3 "The ANOVA table and tests of hypotheses
    about means":
    https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm

Effect sizes:
  - Welch t -> Cohen's d using the *unweighted average* variance (not the
    equal-variance pooled SD), per Delacre, M., Lakens, D., & Leys, C.
    (2017). "Why Psychologists Should by Default Use Welch's t-test
    Instead of Student's t-test." International Review of Social
    Psychology, 30(1), 92-101 -- the effect size that actually pairs with
    a Welch test. d = (m1-m2) / sqrt((s1^2+s2^2)/2).
  - Paired / one-sample t -> Cohen's d_z = mean(diff) / sd(diff), per
    Cohen, J. (1988). Statistical Power Analysis for the Behavioral
    Sciences (2nd ed.), Lawrence Erlbaum.
  - ANOVA -> eta-squared = SS_between / SS_total (standard construction,
    matches NIST's own ANOVA-table SS decomposition above).
  - d / d_z confidence intervals: the large-sample approximate SE, Hedges,
    L.V., & Olkin, I. (1985). Statistical Methods for Meta-Analysis,
    Academic Press (two-sample form); Borenstein, M., Hedges, L.V.,
    Higgins, J.P.T., & Rothstein, H.R. (2009). Introduction to
    Meta-Analysis, Wiley (paired/one-sample d_z form). Labeled
    "approximate" throughout -- never sold as an exact noncentral-t CI.
  - Eta-squared carries no CI here: a correct CI needs the noncentral F
    distribution, which is out of scope for this v1 route (documented,
    not silently skipped -- effect_size_ci_method says so on the result).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import stats

from ..provenance import Computed, compute
from .constants import HYP_ALPHA_TWO_SIDED, HYP_CI_CONFIDENCE_LEVEL
from .descriptive import mean as sample_mean
from .descriptive import sample_sd
from .hypothesis_common import (
    PRACTICAL_SIGNIFICANCE_PROMPT,
    Exit13Payload,
    GroupSummary,
    HypothesisTestResult,
    PlainLanguageBlock,
    QuestionIntent,
    cohens_d_magnitude,
    eta_squared_magnitude,
    p_value_sentence,
    two_sided_critical_z,
)


def _cohens_d_two_sample_ci(d: float, n1: int, n2: int, confidence_level: float) -> tuple[float, float]:
    """Hedges & Olkin (1985) large-sample approximate SE of d."""
    se = ((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2))) ** 0.5
    z = two_sided_critical_z(confidence_level)
    return d - z * se, d + z * se


def _cohens_dz_one_sample_ci(dz: float, n: int, confidence_level: float) -> tuple[float, float]:
    """Borenstein et al. (2009) large-sample approximate SE of d_z."""
    se = (1.0 / n + (dz**2) / (2 * n)) ** 0.5
    z = two_sided_critical_z(confidence_level)
    return dz - z * se, dz + z * se


def welch_two_sample_t(
    label_a: str, a: Sequence[float], label_b: str, b: Sequence[float], *, alpha: float = HYP_ALPHA_TWO_SIDED
) -> Computed[HypothesisTestResult]:
    n1, n2 = len(a), len(b)
    m1, m2 = sample_mean(a), sample_mean(b)
    s1, s2 = sample_sd(a), sample_sd(b)

    test = stats.ttest_ind(a, b, equal_var=False)
    t_stat, p_value, df = float(test.statistic), float(test.pvalue), float(test.df)
    significant = bool(p_value < alpha)

    d = (m1 - m2) / (((s1**2 + s2**2) / 2) ** 0.5)
    ci = _cohens_d_two_sample_ci(d, n1, n2, HYP_CI_CONFIDENCE_LEVEL)

    groups = (GroupSummary(label=label_a, n=n1, mean=m1, sd=s1), GroupSummary(label=label_b, n=n2, mean=m2, sd=s2))
    plain = PlainLanguageBlock(
        comparison_summary=(
            f"Compared {label_a} (n={n1}, mean={m1:.4g}) against {label_b} (n={n2}, mean={m2:.4g}) using "
            "Welch's two-sample t-test (unequal variances assumed by default -- no equal-variance check to trip on)."
        ),
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Cohen's d = {d:.2f} -- a {cohens_d_magnitude(d)} difference (Cohen 1988 conventional bands: "
            "negligible<0.2, small<0.5, medium<0.8, large>=0.8)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="welch_two_sample_t", statistic_name="t", statistic=t_stat, df=df, p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="Cohen's d (Welch/unequal-variance form)", effect_size_value=d,
        effect_size_ci=ci, effect_size_ci_method="Hedges & Olkin (1985) large-sample approximate SE -- not an exact noncentral-t CI",
        groups=groups,
        assumptions_checked=[f"n >= 8 per sample cleared (matrix §4a EXIT-06); groups independent"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method="Welch's two-sample t-test (scipy.stats.ttest_ind, equal_var=False; NIST/SEMATECH §7.3.1 unequal-variance "
        "form + Welch-Satterthwaite df) + Cohen's d on the unweighted-average SD (Delacre, Lakens & Leys 2017)",
        input_data={"a": {"label": label_a, "values": list(a)}, "b": {"label": label_b, "values": list(b)}},
        assumptions_checked=["n >= 8 per sample", "independent groups"],
    )


def paired_t(label_a: str, a: Sequence[float], label_b: str, b: Sequence[float], *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    """diffs = a - b, matching NIST §7.3.1.1's d_i = Y_i - Z_i (first
    sample minus second) -- caller order fixes the sign of dbar/d_z."""
    if len(a) != len(b):
        raise ValueError("paired_t requires equal-length paired arrays")
    n = len(a)
    diffs = [x - y for x, y in zip(a, b)]
    dbar = sample_mean(diffs)
    sd = sample_sd(diffs)
    t_stat = dbar / (sd / (n**0.5)) if sd > 0 else 0.0
    df = n - 1
    p_value = float(2 * stats.t.sf(abs(t_stat), df))
    significant = bool(p_value < alpha)

    dz = dbar / sd if sd > 0 else 0.0
    ci = _cohens_dz_one_sample_ci(dz, n, HYP_CI_CONFIDENCE_LEVEL)

    groups = (
        GroupSummary(label=label_a, n=n, mean=sample_mean(a), sd=sample_sd(a)),
        GroupSummary(label=label_b, n=n, mean=sample_mean(b), sd=sample_sd(b)),
    )
    plain = PlainLanguageBlock(
        comparison_summary=f"Compared {n} paired observations, {label_a} vs {label_b} (mean difference={dbar:+.4g}), using a paired t-test.",
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Cohen's d_z = {dz:.2f} -- a {cohens_d_magnitude(dz)} difference relative to the pair-to-pair spread "
            "(Cohen 1988 conventional bands)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="paired_t", statistic_name="t", statistic=t_stat, df=float(df), p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="Cohen's d_z (paired)", effect_size_value=dz, effect_size_ci=ci,
        effect_size_ci_method="Borenstein et al. (2009) large-sample approximate SE -- not an exact noncentral-t CI",
        groups=groups, assumptions_checked=["n (pairs) >= 8 cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method=f"paired t-test (NIST/SEMATECH §7.3.1.1: d_i={label_a}-{label_b}, t=dbar/(s_d/sqrt(n)), df=n-1) + Cohen's d_z (Cohen 1988)",
        input_data={"a": {"label": label_a, "values": list(a)}, "b": {"label": label_b, "values": list(b)}},
        assumptions_checked=["n (pairs) >= 8"],
    )


def one_sample_t(label: str, sample: Sequence[float], target: float, *, alpha: float = HYP_ALPHA_TWO_SIDED) -> Computed[HypothesisTestResult]:
    n = len(sample)
    m = sample_mean(sample)
    sd = sample_sd(sample)
    t_stat = (m - target) / (sd / (n**0.5)) if sd > 0 else 0.0
    df = n - 1
    p_value = float(2 * stats.t.sf(abs(t_stat), df))
    significant = bool(p_value < alpha)

    d = (m - target) / sd if sd > 0 else 0.0
    ci = _cohens_dz_one_sample_ci(d, n, HYP_CI_CONFIDENCE_LEVEL)

    groups = (GroupSummary(label=label, n=n, mean=m, sd=sd),)
    plain = PlainLanguageBlock(
        comparison_summary=f"Compared {label} (n={n}, mean={m:.4g}) against the target {target:.4g} using a one-sample t-test.",
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=f"Cohen's d = {d:.2f} -- a {cohens_d_magnitude(d)} difference from the target (Cohen 1988 conventional bands).",
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    result = HypothesisTestResult(
        test_name="one_sample_t", statistic_name="t", statistic=t_stat, df=float(df), p_value=p_value, alpha=alpha,
        significant=significant, effect_size_name="Cohen's d (vs target)", effect_size_value=d, effect_size_ci=ci,
        effect_size_ci_method="Borenstein et al. (2009) large-sample approximate SE -- not an exact noncentral-t CI",
        groups=groups, assumptions_checked=["n >= 8 cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain,
    )
    return compute(
        result,
        method="one-sample t-test (NIST/SEMATECH §7.2.2: t=(mean-target)/(s/sqrt(n)), df=n-1) + Cohen's d (Cohen 1988)",
        input_data={"label": label, "values": list(sample), "target": target},
        assumptions_checked=["n >= 8"],
    )


def _exit13_payload(groups: Sequence[GroupSummary]) -> Exit13Payload:
    """matrix §4 EXIT-13: attached to a *significant* ANOVA result when the
    caller's question asks which groups differ (hypothesis_runner.py /
    hypothesis_parametric.one_way_anova's own question_intent gate decides
    *whether* to call this; this function only builds the payload).
    Largest-vs-smallest is named descriptively -- no pairwise p-value."""
    ranked = sorted(groups, key=lambda g: (g.mean if g.mean is not None else float("-inf")))
    lo, hi = ranked[0], ranked[-1]
    return Exit13Payload(
        interim_read=tuple(groups),
        largest_vs_smallest=(
            f"{hi.label} reads highest (mean {hi.mean:.4g}); {lo.label} reads lowest (mean {lo.mean:.4g}) -- "
            "a descriptive comparison only, no pairwise p-value is reported here."
        ),
    )


def one_way_anova(
    groups: Sequence[tuple[str, Sequence[float]]], *, alpha: float = HYP_ALPHA_TWO_SIDED, question_intent: QuestionIntent | None = None
) -> Computed[HypothesisTestResult]:
    """`groups` is (label, values) pairs, >=3 groups. `question_intent`
    gates EXIT-13 (matrix §4a round-2 correction): None or
    "which_groups_differ" attaches it on a significant result;
    "omnibus_any_group_differs" does not -- the honest default leans
    toward naming the limitation (see hypothesis_runner.py's module
    docstring for the documented reasoning)."""
    k = len(groups)
    labels = [g[0] for g in groups]
    values = [list(g[1]) for g in groups]
    ns = [len(v) for v in values]
    means = [sample_mean(v) for v in values]
    sds = [sample_sd(v) if n >= 2 else 0.0 for v, n in zip(values, ns)]
    medians = [float(np.median(v)) for v in values]
    all_values = [x for v in values for x in v]
    grand_mean = sample_mean(all_values)
    n_total = len(all_values)

    ss_between = sum(n * (m - grand_mean) ** 2 for n, m in zip(ns, means))
    ss_within = sum(sum((x - m) ** 2 for x in v) for v, m in zip(values, means))
    ss_total = ss_between + ss_within
    df_between, df_within = k - 1, n_total - k

    f_stat, p_value = (float(x) for x in stats.f_oneway(*values))
    significant = bool(p_value < alpha)
    eta2 = ss_between / ss_total if ss_total > 0 else 0.0

    group_summaries = tuple(GroupSummary(label=lab, n=n, mean=m, sd=s, median=med) for lab, n, m, s, med in zip(labels, ns, means, sds, medians))
    plain = PlainLanguageBlock(
        comparison_summary=f"Compared {k} groups ({', '.join(labels)}, total n={n_total}) using one-way ANOVA.",
        p_value_meaning=p_value_sentence(p_value, alpha, significant),
        effect_size_in_words=(
            f"Eta-squared = {eta2:.3f} -- {eta_squared_magnitude(eta2)} share of the total variation is "
            "explained by group membership (Cohen 1988 conventional bands: small=0.01, medium=0.06, large=0.14)."
        ),
        practical_significance_prompt=PRACTICAL_SIGNIFICANCE_PROMPT,
    )
    exit13 = _exit13_payload(group_summaries) if significant and question_intent != "omnibus_any_group_differs" else None
    result = HypothesisTestResult(
        test_name="one_way_anova", statistic_name="F", statistic=f_stat, df_between=float(df_between), df_within=float(df_within),
        p_value=p_value, alpha=alpha, significant=significant, effect_size_name="eta-squared", effect_size_value=eta2,
        effect_size_ci=None,
        effect_size_ci_method=(
            "not computed -- a correct 95% CI for eta-squared needs the noncentral F distribution, out of scope "
            "for this v1 route; the point estimate is reported plainly, never with a false CI."
        ),
        groups=group_summaries,
        assumptions_checked=[f">= {k} groups (>=3) and >= 4 per group cleared (matrix §4a EXIT-06)"],
        warnings=(), plain_language=plain, exit13=exit13,
    )
    return compute(
        result,
        method="one-way ANOVA (scipy.stats.f_oneway; NIST/SEMATECH §7.4.3.3 SS/DF/MS/F construction) + eta-squared = SS_between/SS_total",
        input_data={"groups": [{"label": lab, "values": v} for lab, v in zip(labels, values)]},
        assumptions_checked=[">= 3 groups", ">= 4 per group"],
    )
