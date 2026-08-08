"""stats/hypothesis_common.py -- T-17 Hypothesis Testing: shared request/
result types, plain-language builders, and the small cross-family math
utilities (lag-1 autocorrelation for EXIT-09, an advisory normality-concern
check for the nonparametric switch rule and EXIT-14) that every route
module (hypothesis_selector.py, hypothesis_parametric.py,
hypothesis_nonparametric.py, hypothesis_categorical.py, hypothesis_runner.py)
builds on. See docs/traceability-matrix.md §4a for the frozen exit
triggers and stats/constants.py for every named number, cited once.

Design note on `HypothesisTestResult`: one shared, heavily-Optional result
model carries every family's output (Welch t, paired t, one-sample t,
ANOVA, chi-square, two-proportion z, one-proportion, Mann-Whitney,
Wilcoxon signed-rank) rather than nine separate result types. This mirrors
BaselineResult's own multi-branch shape (stats/baseline.py) more than
MsaResult's two-branch one: T-17 has many more routes than T-12, and a
single result contract is what lets the runner, the artifact, and the
route layer treat "a hypothesis-test result" as one thing regardless of
which route produced it -- family-specific numbers (Cramer's V,
Hodges-Lehmann shift, risk difference, ...) simply stay None on the routes
that don't produce them.
"""

from __future__ import annotations

import math
from typing import Literal, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from . import normality as normality_mod
from .constants import (
    COHEN_D_LARGE,
    COHEN_D_MEDIUM,
    COHEN_D_SMALL,
    COHEN_ETA2_LARGE,
    COHEN_ETA2_MEDIUM,
    COHEN_ETA2_SMALL,
    COHEN_R_LARGE,
    COHEN_R_MEDIUM,
    COHEN_R_SMALL,
    CRAMERS_V_MODERATE,
    CRAMERS_V_STRONG,
    CRAMERS_V_WEAK,
    HYP_AUTOCORR_MATERIAL_MIN_ABS_R1,
    HYP_AUTOCORR_SIGNIFICANCE_NUMERATOR,
    MIN_N_FOR_ANDERSON_DARLING_STATISTIC,
    NORMALITY_CONCERN_ALPHA,
)

ComparisonType = Literal[
    "two_independent",
    "paired",
    "multi_group",
    "one_sample_vs_target",
    "proportions",
    "association_categorical",
    "relationship_continuous",
]
DeclaredDataType = Literal["continuous", "ordinal", "nominal_categorical", "count_rate"]
QuestionIntent = Literal["omnibus_any_group_differs", "which_groups_differ"]
RouteName = Literal[
    "welch_two_sample_t",
    "paired_t",
    "one_sample_t",
    "one_way_anova",
    "one_proportion",
    "two_proportion_z",
    "chi_square_independence",
    "mann_whitney_u",
    "wilcoxon_signed_rank",
]
# EXIT-13 is deliberately absent: it is a post-hoc annotation attached to a
# *successful* ANOVA result (matrix §4 registry row), never a routing
# refusal, so it never appears as a RoutingDecision.exit value.
ExitId = Literal["EXIT-06", "EXIT-07", "EXIT-08", "EXIT-09", "EXIT-11", "EXIT-12", "EXIT-14", "EXIT-15"]


class GroupInput(BaseModel):
    """One group/sample's raw input. `values` feeds the continuous/ordinal
    routes; `successes`/`n` feed the proportions route (n is only read
    when `values` is absent, so a proportions caller need not fabricate a
    fake per-unit array)."""

    label: str = "group"
    values: list[float] | None = None
    successes: int | None = None
    n: int | None = None


class HypothesisQuestion(BaseModel):
    """The routing input contract (T-17 build brief): comparison type,
    data arrays/counts, declared data types, optional shape-concern flag --
    plus every extra field an EXIT-06..15 check needs to be detectable
    from the inputs alone, never inferred and never silent."""

    question_text: str = Field(min_length=1)
    comparison_type: ComparisonType
    declared_data_type: DeclaredDataType = "continuous"

    groups: list[GroupInput] = Field(default_factory=list)  # two_independent / multi_group / proportions
    paired_before: list[float] | None = None
    paired_after: list[float] | None = None
    paired_before_label: str = "before"
    paired_after_label: str = "after"
    sample: list[float] | None = None  # one_sample_vs_target
    sample_label: str = "sample"
    target: float | None = None  # one_sample_vs_target: target value, or target proportion (0-1)
    contingency_table: list[list[int]] | None = None  # association_categorical: rows x cols observed counts
    row_labels: list[str] | None = None
    col_labels: list[str] | None = None

    time_ordered: bool = False  # EXIT-09 applicability: was this collected in time sequence?
    user_shape_concern: bool = False  # optional user-declared shape/outlier concern (switch-rule input)
    measurements_per_unit: int = 1  # EXIT-08: >1 beyond the paired design signals repeated measures
    question_intent: QuestionIntent | None = None  # multi_group only -- EXIT-13's declared-question gate
    comparisons_declared: int = 1  # EXIT-12
    tests_run_including_this_one: int = 1  # EXIT-12
    declared_primary: bool = True  # this comparison is the pre-declared primary one (rubric R-ANA-04 #4)


# --- Shared result shape -----------------------------------------------------


class GroupSummary(BaseModel):
    """One group's descriptive line in a result's `groups` table -- the
    "group means/medians table" EXIT-13's interim read (and every other
    route's plain-English comparison) renders from."""

    model_config = ConfigDict(frozen=True)

    label: str
    n: int
    mean: float | None = None
    sd: float | None = None
    median: float | None = None
    successes: int | None = None
    proportion: float | None = None


class ContingencyCell(BaseModel):
    model_config = ConfigDict(frozen=True)

    row: str
    col: str
    observed: int
    expected: float


class PlainLanguageBlock(BaseModel):
    """Rendered verbatim by the UI (task brief): what was compared, what
    the p-value does/doesn't mean here, effect size in words, and the
    practical-significance prompt."""

    model_config = ConfigDict(frozen=True)

    comparison_summary: str
    p_value_meaning: str
    effect_size_in_words: str
    practical_significance_prompt: str


class Exit13Payload(BaseModel):
    """matrix §4 registry row: ANOVA-significant canned next step, verbatim
    (PLAN §4.1 Hypothesis row), plus the honest interim read -- group
    means/medians, largest-vs-smallest named descriptively, no pairwise
    p-values. Attached to a *successful* HypothesisTestResult, never a
    routing refusal (see RouteName's module-level note)."""

    model_config = ConfigDict(frozen=True)

    exit_id: Literal["EXIT-13"] = "EXIT-13"
    message: str = (
        "These groups differ overall; comparing specific pairs fairly needs a correction -- guided pairwise "
        "comparisons ship in v1.1. Here's the honest interim read."
    )
    interim_read: tuple[GroupSummary, ...]
    largest_vs_smallest: str
    routes_to: str = "T-17 pairwise route (v1.1)."


class HypothesisTestResult(BaseModel):
    """The one result shape every T-17 route produces (module docstring).
    Always: statistic, two-sided p, effect size with its name, CI where
    standard, n's, assumptions/warnings, and a plain_language block (task
    brief) -- never a bare p-value."""

    model_config = ConfigDict(frozen=True)

    test_name: RouteName
    statistic_name: str
    statistic: float
    df: float | None = None
    df_between: float | None = None  # ANOVA only
    df_within: float | None = None  # ANOVA only
    p_value: float
    alpha: float
    two_sided: bool = True
    significant: bool

    effect_size_name: str
    effect_size_value: float
    effect_size_ci: tuple[float, float] | None = None
    effect_size_ci_method: str | None = None

    groups: tuple[GroupSummary, ...]
    contingency: tuple[ContingencyCell, ...] | None = None
    cramers_v: float | None = None
    hodges_lehmann_shift: float | None = None
    hodges_lehmann_ci: tuple[float, float] | None = None
    hodges_lehmann_ci_method: str | None = None
    rank_biserial_r: float | None = None
    risk_difference: float | None = None
    risk_difference_ci: tuple[float, float] | None = None
    risk_difference_ci_method: str | None = None
    equal_shape_caveat: str | None = None  # Mann-Whitney only

    assumptions_checked: tuple[str, ...]
    warnings: tuple[str, ...]
    plain_language: PlainLanguageBlock
    exit13: Exit13Payload | None = None


# --- Plain-language builders --------------------------------------------------
# Rubric R-ANA-05 Pass #2: "Non-significant is never narrated as 'no
# difference' -- the honest form is 'no difference shown at this sample
# size.'" Baked in here once so no family module can phrase it wrong.

PRACTICAL_SIGNIFICANCE_PROMPT = "Statistically detectable ≠ big enough to matter -- compare the effect size above against the goal."


def p_value_sentence(p_value: float, alpha: float, significant: bool) -> str:
    if significant:
        return (
            f"p = {p_value:.4f}, below the alpha={alpha:g} threshold: if there were truly no difference, a "
            f"result at least this far from 'no difference' would turn up by chance alone only about "
            f"{p_value * 100:.2g}% of the time. That makes the difference statistically detectable here -- it "
            "does not mean the null hypothesis is false with that probability, and it says nothing yet about "
            "whether the difference is big enough to matter."
        )
    return (
        f"p = {p_value:.4f}, at or above the alpha={alpha:g} threshold: no difference shown at this sample "
        "size. That is not proof there is no difference, and it is not the same claim as 'no difference "
        "exists' -- a smaller true difference, or the same difference measured with more data, could still "
        "turn up significant."
    )


def cohens_d_magnitude(value: float) -> str:
    d = abs(value)
    if d < COHEN_D_SMALL:
        return "negligible"
    if d < COHEN_D_MEDIUM:
        return "small"
    if d < COHEN_D_LARGE:
        return "medium"
    return "large"


def eta_squared_magnitude(value: float) -> str:
    v = abs(value)
    if v < COHEN_ETA2_SMALL:
        return "negligible"
    if v < COHEN_ETA2_MEDIUM:
        return "small"
    if v < COHEN_ETA2_LARGE:
        return "medium"
    return "large"


def correlation_r_magnitude(value: float) -> str:
    """Cohen (1988) r benchmarks -- shared by rank-biserial r (Mann-Whitney,
    Wilcoxon) since both are correlation-scaled (-1..1) effect sizes."""
    r = abs(value)
    if r < COHEN_R_SMALL:
        return "negligible"
    if r < COHEN_R_MEDIUM:
        return "small"
    if r < COHEN_R_LARGE:
        return "medium"
    return "large"


def cramers_v_magnitude(value: float) -> str:
    v = abs(value)
    if v < CRAMERS_V_WEAK:
        return "negligible"
    if v < CRAMERS_V_MODERATE:
        return "weak"
    if v < CRAMERS_V_STRONG:
        return "moderate"
    return "strong"


def two_sided_critical_z(confidence_level: float) -> float:
    from scipy import stats  # local import: keep this module scipy-light for callers that only need types

    if not (0.0 < confidence_level < 1.0):
        raise ValueError("confidence_level must be between 0 and 1 (exclusive)")
    return float(stats.norm.ppf(1 - (1 - confidence_level) / 2))


# --- EXIT-09: lag-1 autocorrelation ------------------------------------------


def lag1_autocorrelation(data: Sequence[float]) -> float | None:
    """r1, NIST/SEMATECH §1.3.3.1 "Autocorrelation Plot":
    https://www.itl.nist.gov/div898/handbook/eda/section3/eda331.htm

        r_h = sum_{i=1}^{N-h}(Y_i-Ybar)(Y_{i+h}-Ybar) / sum_{i=1}^{N}(Y_i-Ybar)^2

    None below n=2 (no lag-1 pair exists) or on constant data (the
    denominator is 0 -- undefined, not silently 0.0)."""
    n = len(data)
    if n < 2:
        return None
    arr = np.asarray(data, dtype=float)
    ybar = float(arr.mean())
    denom = float(np.sum((arr - ybar) ** 2))
    if denom == 0.0:
        return None
    numer = float(np.sum((arr[:-1] - ybar) * (arr[1:] - ybar)))
    return numer / denom


class AutocorrelationCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    n: int
    r1: float | None
    significance_threshold: float | None  # 2/sqrt(n); None when r1 is None
    is_significant: bool
    is_material: bool
    fires_exit09: bool  # matrix §4a EXIT-09: significant AND material -- the compound boundary


def check_autocorrelation(label: str, data: Sequence[float]) -> AutocorrelationCheck:
    n = len(data)
    r1 = lag1_autocorrelation(data)
    if r1 is None:
        return AutocorrelationCheck(
            label=label, n=n, r1=None, significance_threshold=None,
            is_significant=False, is_material=False, fires_exit09=False,
        )
    threshold = HYP_AUTOCORR_SIGNIFICANCE_NUMERATOR / math.sqrt(n)
    is_significant = abs(r1) > threshold
    is_material = abs(r1) >= HYP_AUTOCORR_MATERIAL_MIN_ABS_R1
    return AutocorrelationCheck(
        label=label, n=n, r1=r1, significance_threshold=threshold,
        is_significant=is_significant, is_material=is_material, fires_exit09=is_significant and is_material,
    )


# --- Switch-rule / EXIT-14 advisory normality concern ------------------------


def advisory_normality_concern(values: Sequence[float]) -> bool:
    """True iff scipy's Anderson-Darling test (normality.py's own
    statistic function) reads p < 0.05 (matrix §4a EXIT-05's concern
    threshold, NORMALITY_CONCERN_ALPHA, reused here -- the matrix names no
    separate threshold for T-17's switch rule or EXIT-14, so the natural
    reading is the same Anderson-Darling-p<0.05 criterion this engine
    already uses elsewhere).

    Deliberately does NOT call normality_mod.assess_normality(): that
    function's advisory_level() applies T-13's own MIN_N_FOR_NORMALITY_
    JUDGMENT=15 "too_few_to_judge" veto, which would make this check
    *vacuous* everywhere the switch rule (per-group n<15) or EXIT-14
    (group n<20) can actually fire -- a group with n<15 would always read
    "too_few_to_judge", never "concern", silently defeating the "OR
    advisory normality concern" disjunct in both frozen rules. constants.py
    already documents T-13 and EXIT-14 as deliberately-distinct n-floors
    for nominally the same concept; this function is the same divergence
    applied consistently -- it runs the raw AD statistic (which only needs
    MIN_N_FOR_ANDERSON_DARLING_STATISTIC=3 to compute at all) and lets each
    *caller* apply its own outer n-condition (switch: n<15; EXIT-14: n<20),
    so the disjunct can actually be true. Documented here, not silent, per
    this codebase's standing practice for an ambiguous-spec judgment call
    (see stats/baseline.py's EXIT-05 module docstring for the precedent)."""
    if len(values) < MIN_N_FOR_ANDERSON_DARLING_STATISTIC or len(set(values)) == 1:
        # Constant data has no shape to be concerned about -- short-circuit
        # rather than hand scipy's anderson() a zero-variance sample (it
        # emits a "divide by zero" RuntimeWarning internally and returns a
        # degenerate statistic; the honest answer here is simply "no
        # concern," decided before scipy ever sees the data).
        return False
    _, pvalue = normality_mod.anderson_darling_statistic(values)
    return pvalue is not None and pvalue < NORMALITY_CONCERN_ALPHA


def group_successes_n(group: GroupInput) -> tuple[int, int]:
    """A GroupInput's (successes, n) for the proportions family and the
    proportions branch of the selector: `values` (a list of 0/1 or
    truthy/falsy unit outcomes) if given, else the caller's own
    `successes`/`n` counts directly -- either is a valid way to state a
    proportions sample."""
    if group.values is not None:
        n = len(group.values)
        successes = int(sum(1 for v in group.values if v))
        return successes, n
    if group.successes is None or group.n is None:
        raise ValueError(f"group {group.label!r}: the proportions route requires either `values`, or both `successes` and `n`")
    return int(group.successes), int(group.n)


def nonzero_diff_count(diffs: Sequence[float]) -> int:
    """Count of non-zero differences -- the Wilcoxon signed-rank EXIT-06
    floor is stated in these (matrix §4a), not raw pair/sample count,
    because scipy's default zero_method='wilcox' discards zero
    differences before ranking (a zero carries no directional information
    for a signed-rank test)."""
    return sum(1 for d in diffs if d != 0)
