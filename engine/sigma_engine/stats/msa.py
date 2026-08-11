"""stats/msa.py -- T-12 Measurement Check: the narrow, honestly-named MSA
this suite runs (matrix III.E / §4a EXIT-02, EXIT-03; rubric R-MEA-07).

Two independent paths, chosen by data type:

  continuous -- resolution pre-check first (does the gauge see the
  process at all?), then test/retest **repeatability%** (NOT "%EV" and
  NOT "GRR" -- Belt-panel round 2: this is a single-operator study, so
  reproducibility is absent by design; EV names a component of a full
  variance-decomposed study this narrow check is not).

  attribute -- two-rater judgment agreement: Cohen's kappa (chance-
  corrected) reported alongside plain % agreement, never kappa alone and
  never % agreement alone (a low-defect process can fake high % agreement
  by chance -- kappa corrects for that).

Everything a caller needs to route past this narrow check honestly (multi-
operator reproducibility, bias, linearity, stability-over-time) is named,
not computed -- see EXIT03_INFO below and the traceability matrix's EXIT-03
row: this tool recognizes the case and routes out, it does not improvise.

Every frozen number here is cited to docs/traceability-matrix.md §4a in
stats/constants.py -- nothing in this module chooses its own thresholds.
"""

from __future__ import annotations

import math
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from . import descriptive as descriptive_mod
from .constants import (
    MSA_KAPPA_ACCEPTABLE_MIN,
    MSA_KAPPA_MARGINAL_MIN,
    MSA_MIN_REPEATS_PER_ITEM,
    MSA_REPEATABILITY_ACCEPTABLE_MAX_PERCENT,
    MSA_REPEATABILITY_EV_SIGMA_MULTIPLIER,
    MSA_REPEATABILITY_MARGINAL_MAX_PERCENT,
    MSA_REPEATABILITY_ONLY_CAVEAT,
    MSA_RESOLUTION_MAX_INCREMENT_FRACTION_OF_SPAN,
    MSA_RESOLUTION_MIN_DISTINCT_VALUES,
)

Verdict = Literal["acceptable", "marginal", "fail"]
DataType = Literal["continuous", "attribute"]
SpanBasis = Literal["tolerance", "observed_spread"]
Denominator = Literal["tolerance", "study_variation"]


# --- Resolution pre-check (continuous only) ---------------------------------

class ResolutionCheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    gauge_increment: float
    span: float
    span_basis: SpanBasis
    increment_to_span_ratio: float | None
    distinct_value_count: int
    passed: bool
    reasons: tuple[str, ...]


def _resolution_span(data: Sequence[float], usl: float | None, lsl: float | None) -> tuple[float, SpanBasis]:
    """Span the gauge must resolve: spec width when both limits exist
    (matrix §4a), else the observed spread of the readings collected."""
    if usl is not None and lsl is not None:
        return float(usl - lsl), "tolerance"
    return float(max(data) - min(data)), "observed_spread"


def check_resolution(
    data: Sequence[float], gauge_increment: float, *, usl: float | None = None, lsl: float | None = None
) -> ResolutionCheckResult:
    """Both criteria, automatic fail on either (matrix §4a EXIT-02
    continuous): gauge increment <= 1/10 of the span, AND >=5 distinct
    recorded values. Whichever fails, the reason is named plainly -- this
    is the pre-check whose whole point is "the gauge can't see the
    process," so a silent boolean would defeat it."""
    if gauge_increment <= 0:
        raise ValueError("gauge_increment must be > 0")
    if len(data) == 0:
        raise ValueError("check_resolution requires at least one reading")

    span, basis = _resolution_span(data, usl, lsl)
    distinct = len(set(data))
    reasons: list[str] = []

    ratio: float | None = None
    if span <= 0:
        reasons.append(f"the {basis.replace('_', ' ')} span is {span:g} -- no measurable span for the gauge to resolve")
    else:
        ratio = gauge_increment / span
        if ratio > MSA_RESOLUTION_MAX_INCREMENT_FRACTION_OF_SPAN:
            reasons.append(
                f"gauge increment {gauge_increment:g} is {ratio:.1%} of the {basis.replace('_', ' ')} span "
                f"{span:g} -- more than the 1/10 ceiling (matrix §4a): the gauge can't see the process"
            )
    if distinct < MSA_RESOLUTION_MIN_DISTINCT_VALUES:
        reasons.append(
            f"only {distinct} distinct recorded value(s) (< {MSA_RESOLUTION_MIN_DISTINCT_VALUES} required): "
            "the gauge can't see the process"
        )

    return ResolutionCheckResult(
        gauge_increment=gauge_increment, span=span, span_basis=basis, increment_to_span_ratio=ratio,
        distinct_value_count=distinct, passed=not reasons, reasons=tuple(reasons),
    )


# --- Repeatability% (continuous) --------------------------------------------

class ItemRepeats(BaseModel):
    """One item's repeat readings for the test/retest design (matrix §4a:
    "same operator, same procedure, blind to prior readings where
    practical"). A `None` slot is a missing/invalid repeat -- excluded,
    never treated as zero."""

    model_config = ConfigDict(frozen=True)

    item_id: str
    readings: tuple[float | None, ...]


class PooledRepeatabilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    s_repeat: float
    s_study: float
    items_used: int
    items_excluded: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]
    total_valid_readings: int


def pooled_within_item_sd(items: Sequence[ItemRepeats]) -> PooledRepeatabilityResult:
    """s_repeat = sqrt( sum_i[(n_i-1)*s_i^2] / sum_i[n_i-1] ) -- the pooled
    (equal-weight-by-degrees-of-freedom) within-item standard deviation,
    i.e. the standard one-way-ANOVA within-group variance estimate (NIST/
    SEMATECH §7.4.3.1's SSE/MSE construction:
    https://www.itl.nist.gov/div898/handbook/prc/section4/prc431.htm),
    applied here with each *item* as a "group" instead of a treatment
    group. Items with fewer than MSA_MIN_REPEATS_PER_ITEM valid (non-null)
    readings can't contribute a within-item variance term and are
    excluded -- logged by item_id, never silently dropped (matrix §4a
    round-3 lock fix: "items with missing/invalid repeats are excluded
    and the exclusion logged")."""
    weighted_variances: list[tuple[int, float]] = []
    excluded: list[str] = []
    exclusion_reasons: list[str] = []
    all_valid: list[float] = []

    for item in items:
        valid = [r for r in item.readings if r is not None]
        if len(valid) < MSA_MIN_REPEATS_PER_ITEM:
            excluded.append(item.item_id)
            exclusion_reasons.append(
                f"{item.item_id}: only {len(valid)} valid repeat reading(s) (< {MSA_MIN_REPEATS_PER_ITEM} required)"
            )
            continue
        all_valid.extend(valid)
        item_mean = sum(valid) / len(valid)
        item_var = sum((x - item_mean) ** 2 for x in valid) / (len(valid) - 1)
        weighted_variances.append((len(valid), item_var))

    if not weighted_variances:
        raise ValueError(f"pooled_within_item_sd requires >=1 item with >= {MSA_MIN_REPEATS_PER_ITEM} valid repeat readings")

    dof_total = sum(n - 1 for n, _ in weighted_variances)
    pooled_var = sum((n - 1) * var for n, var in weighted_variances) / dof_total if dof_total > 0 else 0.0
    s_study = descriptive_mod.sample_sd(all_valid) if len(all_valid) >= 2 else 0.0

    return PooledRepeatabilityResult(
        s_repeat=math.sqrt(pooled_var), s_study=s_study, items_used=len(weighted_variances),
        items_excluded=tuple(excluded), exclusion_reasons=tuple(exclusion_reasons), total_valid_readings=len(all_valid),
    )


def repeatability_verdict(repeatability_percent: float) -> Verdict:
    """Exclusive-exhaustive banding (matrix §4a, round-3 lock fix): boundary
    goldens live at exactly 10.0 (acceptable) and exactly 30.0 (marginal)."""
    if repeatability_percent <= MSA_REPEATABILITY_ACCEPTABLE_MAX_PERCENT:
        return "acceptable"
    if repeatability_percent <= MSA_REPEATABILITY_MARGINAL_MAX_PERCENT:
        return "marginal"
    return "fail"


class RepeatabilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    s_repeat: float
    denominator_value: float
    denominator: Denominator
    repeatability_percent: float
    verdict: Verdict
    items_used: int
    items_excluded: tuple[str, ...]
    exclusion_reasons: tuple[str, ...]


def compute_repeatability(items: Sequence[ItemRepeats], *, usl: float | None, lsl: float | None) -> Computed[RepeatabilityResult]:
    """repeatability% = 6*s_repeat / denominator * 100 (matrix §4a):
    denominator is tolerance width when both spec limits exist, else
    6*s_study -- and the output states which one, by name (III.E:
    "denominator named as which it is," so a flatter number can't get
    quietly shopped). Named `repeatability_percent`, not "%EV" or "GRR"
    (module docstring): a single-operator test/retest study has no
    reproducibility component, so "EV" (a variance-decomposed study's own
    term) would overclaim what this narrow check actually measured."""
    pooled = pooled_within_item_sd(items)
    denominator: Denominator
    if usl is not None and lsl is not None:
        denominator_value, denominator = float(usl - lsl), "tolerance"
    else:
        denominator_value = MSA_REPEATABILITY_EV_SIGMA_MULTIPLIER * pooled.s_study
        denominator = "study_variation"
    if denominator_value <= 0:
        raise ValueError(f"compute_repeatability: denominator ({denominator}) is {denominator_value:g} -- can't be <= 0")

    repeatability_percent = (MSA_REPEATABILITY_EV_SIGMA_MULTIPLIER * pooled.s_repeat / denominator_value) * 100.0
    verdict = repeatability_verdict(repeatability_percent)
    result = RepeatabilityResult(
        s_repeat=pooled.s_repeat, denominator_value=denominator_value, denominator=denominator,
        repeatability_percent=repeatability_percent, verdict=verdict, items_used=pooled.items_used,
        items_excluded=pooled.items_excluded, exclusion_reasons=pooled.exclusion_reasons,
    )
    warnings = [MSA_REPEATABILITY_ONLY_CAVEAT]
    if pooled.items_excluded:
        warnings.append(f"{len(pooled.items_excluded)} item(s) excluded for missing/invalid repeats: {list(pooled.items_excluded)}")
    return compute(
        result,
        method=f"repeatability_percent = {MSA_REPEATABILITY_EV_SIGMA_MULTIPLIER:g}*s_repeat/denominator*100; "
        f"s_repeat = pooled within-item SD (NIST §7.4.3.1 SSE/MSE construction); denominator={denominator} (matrix §4a EXIT-02 continuous)",
        input_data={"items": [i.model_dump(mode="json") for i in items], "usl": usl, "lsl": lsl},
        assumptions_checked=[f">= {MSA_MIN_REPEATS_PER_ITEM} valid repeats per included item"],
        warnings=warnings,
    )


# --- Two-rater attribute agreement (kappa + % agreement) --------------------

class AttributeRating(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    rater_a: bool  # True = "pass"/conforming judgment
    rater_b: bool


def kappa_verdict(kappa: float) -> Verdict:
    """Exclusive-exhaustive banding (matrix §4a, round-3 lock fix): the
    boundary golden lives at exactly kappa=0.75 (acceptable)."""
    if kappa >= MSA_KAPPA_ACCEPTABLE_MIN:
        return "acceptable"
    if kappa >= MSA_KAPPA_MARGINAL_MIN:
        return "marginal"
    return "fail"


class AttributeAgreementResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    percent_agreement: float
    kappa: float
    p_observed: float
    p_expected: float
    verdict: Verdict


def cohens_kappa(ratings: Sequence[AttributeRating]) -> Computed[AttributeAgreementResult]:
    """Cohen's kappa, direct formula -- scipy/numpy ship no kappa
    implementation (sklearn's cohen_kappa_score is the usual library home
    and isn't a dependency here), so this is the plain textbook formula,
    cited: Cohen, J. (1960). "A coefficient of agreement for nominal
    scales." Educational and Psychological Measurement, 20(1), 37-46.

        kappa = (p_o - p_e) / (1 - p_e)

    p_o = observed proportion agreement; p_e = chance-expected proportion
    agreement = sum over each category of (rater A's marginal proportion
    for that category) * (rater B's marginal proportion for that
    category) -- the two-category (pass/fail) case here. % agreement
    (p_o) is always reported alongside kappa, never alone (matrix III.E:
    chance agreement can flatter a low-defect process)."""
    n = len(ratings)
    if n == 0:
        raise ValueError("cohens_kappa requires at least one rating pair")

    agree = sum(1 for r in ratings if r.rater_a == r.rater_b)
    p_o = agree / n
    a_pass = sum(1 for r in ratings if r.rater_a) / n
    b_pass = sum(1 for r in ratings if r.rater_b) / n
    p_e = a_pass * b_pass + (1 - a_pass) * (1 - b_pass)
    # p_e == 1.0 only when both raters are constant AND agree on every item
    # (a_pass, b_pass both 0 or both 1) -- p_o is then trivially also 1.0;
    # kappa is conventionally read as 1.0 (perfect, if trivial, agreement)
    # rather than an undefined 0/0.
    kappa = 1.0 if p_e >= 1.0 else (p_o - p_e) / (1 - p_e)

    result = AttributeAgreementResult(
        n=n, percent_agreement=p_o * 100.0, kappa=kappa, p_observed=p_o, p_expected=p_e, verdict=kappa_verdict(kappa),
    )
    return compute(
        result,
        method="Cohen's kappa (Cohen 1960) = (p_o - p_e)/(1 - p_e), two-rater binary pass/fail; "
        "% agreement reported alongside per matrix §4a EXIT-02 (attribute), never alone",
        input_data=[r.model_dump(mode="json") for r in ratings],
        assumptions_checked=["two raters, binary (pass/fail) judgment per item"],
    )


# --- EXIT-02 / EXIT-03 ------------------------------------------------------

class Exit02Payload(BaseModel):
    """matrix §4 registry row: what the suite says/does on a failed check."""

    model_config = ConfigDict(frozen=True)

    exit_id: Literal["EXIT-02"] = "EXIT-02"
    message: str = (
        "Stop -- fix your measurement first. Capability-claim language is blocked, and downstream results "
        'render as "unreliable -- measurement system failed" until this is fixed.'
    )
    routes_to: str = "Rework the operational definition / gauge (T-11), then re-run this check (T-12)."


class Exit03Payload(BaseModel):
    """matrix §4 registry row: the named self-service route out for a
    measurement question beyond this narrow check."""

    model_config = ConfigDict(frozen=True)

    exit_id: Literal["EXIT-03"] = "EXIT-03"
    message: str = (
        "This question is beyond the narrow check this tool runs (test/retest repeatability, "
        "or two-rater attribute agreement)."
    )
    # Multi-operator reproducibility used to head this list. T-35 now runs
    # that study, so it is no longer out of scope -- it is a screen in this
    # app, and routes_to says which one. The three below are still
    # genuinely not studies this suite runs.
    out_of_scope_examples: tuple[str, ...] = (
        "gauge bias -- is the gauge systematically off from a known reference/standard?",
        "linearity -- does bias change across the measurement range?",
        "gauge stability over time -- does repeatability drift across weeks or months?",
    )
    routes_to: str = (
        "For multi-operator reproducibility, run T-35 (Gage R&R, full crossed study) -- it is in this app, in "
        "Measure. For bias, linearity or stability over time, a human quality engineer or certified Belt: this "
        "suite does not run those studies."
    )


EXIT03_INFO = Exit03Payload()


class MsaResult(BaseModel):
    """The one result T-12's route/UI renders, and what gates.py / T-13's
    baseline consult by `verdict` (matrix III.E; rubric R-MEA-07)."""

    model_config = ConfigDict(frozen=True)

    data_type: DataType
    verdict: Verdict
    resolution_check: ResolutionCheckResult | None  # continuous only
    repeatability: Computed[RepeatabilityResult] | None  # continuous only (None if resolution failed first)
    attribute_agreement: Computed[AttributeAgreementResult] | None  # attribute only
    caveat: str | None  # repeatability-only caveat text, continuous verdicts only
    exit02: Exit02Payload | None  # populated iff verdict == "fail"


def run_continuous_msa(
    items: Sequence[ItemRepeats], *, gauge_increment: float, usl: float | None = None, lsl: float | None = None
) -> MsaResult:
    """Resolution pre-check first, automatic-fail path if it doesn't pass
    (matrix §4a: repeatability% is not even computed in that case) --
    then repeatability%. EXIT-02 payload attaches iff the final verdict is
    'fail', from either branch."""
    if len(items) == 0:
        raise ValueError("run_continuous_msa requires at least one item")
    all_valid = [r for item in items for r in item.readings if r is not None]
    if len(all_valid) == 0:
        raise ValueError("run_continuous_msa requires at least one valid reading across all items")

    resolution = check_resolution(all_valid, gauge_increment, usl=usl, lsl=lsl)
    if not resolution.passed:
        return MsaResult(
            data_type="continuous", verdict="fail", resolution_check=resolution, repeatability=None,
            attribute_agreement=None, caveat=MSA_REPEATABILITY_ONLY_CAVEAT, exit02=Exit02Payload(),
        )

    repeatability = compute_repeatability(items, usl=usl, lsl=lsl)
    verdict = repeatability.value.verdict
    return MsaResult(
        data_type="continuous", verdict=verdict, resolution_check=resolution, repeatability=repeatability,
        attribute_agreement=None, caveat=MSA_REPEATABILITY_ONLY_CAVEAT,
        exit02=Exit02Payload() if verdict == "fail" else None,
    )


def run_attribute_msa(ratings: Sequence[AttributeRating]) -> MsaResult:
    """Two-rater kappa + % agreement -- no resolution pre-check (that's a
    continuous-gauge concept; matrix §4a only lists it under the
    continuous row)."""
    agreement = cohens_kappa(ratings)
    verdict = agreement.value.verdict
    return MsaResult(
        data_type="attribute", verdict=verdict, resolution_check=None, repeatability=None,
        attribute_agreement=agreement, caveat=None, exit02=Exit02Payload() if verdict == "fail" else None,
    )
