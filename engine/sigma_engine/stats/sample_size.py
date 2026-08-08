"""stats/sample_size.py -- T-11's sample-size guidance half (PLAN §4.1 Data
Collection Plan row: "sample-size guidance as a first-class output ... n-
for-stable-baseline rules of thumb + a calculator with plain-English
framing, bias/convenience-sample warnings"). Rubric R-MEA-05 Pass #4:
"planned n stated with the rule-of-thumb or calculator rationale attached."

Three honest pieces, deliberately kept separate rather than blurred into
one number:
  1. A rule of thumb for an I-MR baseline -- convention, not a derived
     law, stated as such.
  2. Two textbook margin-of-error calculators (means, proportions) --
     real formulas, solved for n, with a plain-English sentence attached.
  3. Bias / convenience-sample warning strings (rubric R-MEA-05 Pass #5).
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict
from scipy import stats

from ..provenance import Computed, compute
from .constants import (
    EXIT04_MIN_POINTS_TO_FREEZE_LIMITS,
    IMR_BASELINE_MIN_N_CONVENTION,
    IMR_BASELINE_RECOMMENDED_N_CONVENTION,
    SAMPLE_SIZE_DEFAULT_CONFIDENCE_LEVEL,
)


# --- 1. I-MR baseline rule of thumb -----------------------------------------

class RuleOfThumbResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    context: Literal["imr_baseline"]
    minimum_n: int
    recommended_n: int
    rationale: str


def imr_baseline_rule_of_thumb() -> RuleOfThumbResult:
    """n ~= 25-30 individual observations for a usable I-MR baseline --
    convention, not a derived formula, stated as such (task brief).
    Anchored a little above this engine's own EXIT-04 floor for freezing
    control limits (matrix §4a: >=20 points AND no default-rule signal --
    constants.EXIT04_MIN_POINTS_TO_FREEZE_LIMITS), with headroom for a few
    points to be legitimately excluded as special causes and the baseline
    still clear that hard floor. More is better; fewer than this rule of
    thumb specifically is a named, honest shortfall (rubric R-MEA-05: "a
    small sample with the shortfall named" is thin-but-honest, not
    invalidating) -- never a hard stop the way the EXIT-04 floor is.
    """
    return RuleOfThumbResult(
        context="imr_baseline",
        minimum_n=IMR_BASELINE_MIN_N_CONVENTION,
        recommended_n=IMR_BASELINE_RECOMMENDED_N_CONVENTION,
        rationale=(
            f"Convention, not a derived law: {IMR_BASELINE_MIN_N_CONVENTION}-{IMR_BASELINE_RECOMMENDED_N_CONVENTION} "
            "individual readings, in true time order, is the commonly-taught rule of thumb for a usable I-MR "
            f"baseline -- a little above the {EXIT04_MIN_POINTS_TO_FREEZE_LIMITS}-point floor this suite's own "
            "baseline tool (T-13) requires before it will freeze control limits, leaving room for a few points to "
            "be legitimately excluded as special causes. Collecting fewer is an honest, named shortfall -- not a "
            "hard stop the way T-13's own floor is."
        ),
    )


# --- 2. Margin-of-error calculators -----------------------------------------

def _two_sided_z(confidence_level: float) -> float:
    if not (0.0 < confidence_level < 1.0):
        raise ValueError("confidence_level must be between 0 and 1 (exclusive)")
    return float(stats.norm.ppf(1 - (1 - confidence_level) / 2))


class MeanSampleSizeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    n_exact: float
    z: float
    confidence_level: float
    planning_sd: float
    margin_of_error: float
    plain_english: str


def sample_size_for_mean(
    planning_sd: float, margin_of_error: float, confidence_level: float = SAMPLE_SIZE_DEFAULT_CONFIDENCE_LEVEL
) -> Computed[MeanSampleSizeResult]:
    """n = (z * s / E)^2, rounded UP to the next whole observation (a
    sample size is never fractional, and rounding down would under-shoot
    the stated margin of error). z is the two-sided standard-normal
    critical value at the caller's chosen confidence level (scipy, not a
    hardcoded 1.96), from NIST/SEMATECH §7.2.1's CI-for-a-mean formula
    solved for n: https://www.itl.nist.gov/div898/handbook/prc/section2/prc221.htm
    `planning_sd` is a planning estimate of the process spread (pilot
    data, history, or a documented guess) -- the calculator can't supply
    one honestly, so it's a required input, not a default."""
    if planning_sd <= 0:
        raise ValueError("planning_sd must be > 0")
    if margin_of_error <= 0:
        raise ValueError("margin_of_error must be > 0")
    z = _two_sided_z(confidence_level)
    n_exact = (z * planning_sd / margin_of_error) ** 2
    n = math.ceil(n_exact)
    result = MeanSampleSizeResult(
        n=n, n_exact=n_exact, z=z, confidence_level=confidence_level, planning_sd=planning_sd, margin_of_error=margin_of_error,
        plain_english=(
            f"To estimate the average within +/-{margin_of_error:g} (your data's units) at "
            f"{confidence_level * 100:.0f}% confidence -- using a planning estimate of spread (SD) of "
            f"{planning_sd:g} -- collect at least {n} data points."
        ),
    )
    return compute(
        result,
        method="n = (z*s/E)^2, rounded up (NIST/SEMATECH §7.2.1 CI-for-a-mean, solved for n)",
        input_data={"planning_sd": planning_sd, "margin_of_error": margin_of_error, "confidence_level": confidence_level},
        assumptions_checked=["planning_sd is a reasonable estimate of the true process spread (pilot data, history, or a stated guess)"],
    )


class ProportionSampleSizeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    n_exact: float
    z: float
    confidence_level: float
    planning_p: float
    margin_of_error: float
    plain_english: str


def sample_size_for_proportion(
    planning_p: float, margin_of_error: float, confidence_level: float = SAMPLE_SIZE_DEFAULT_CONFIDENCE_LEVEL
) -> Computed[ProportionSampleSizeResult]:
    """n = z^2 * p_hat * (1 - p_hat) / E^2, rounded up (NIST/SEMATECH
    §7.2.4's CI-for-a-proportion formula solved for n:
    https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
    `planning_p` is the caller's planning estimate of the true proportion
    (0.5 -- the conservative, maximum-variance choice most texts recommend
    absent any prior estimate -- is the caller's choice to pass, never
    hardcoded here: forcing an explicit input keeps the "state your
    planning assumption" discipline the plain-English output narrates)."""
    if not (0.0 < planning_p < 1.0):
        raise ValueError("planning_p must be between 0 and 1 (exclusive)")
    if margin_of_error <= 0:
        raise ValueError("margin_of_error must be > 0")
    z = _two_sided_z(confidence_level)
    n_exact = (z**2) * planning_p * (1 - planning_p) / (margin_of_error**2)
    n = math.ceil(n_exact)
    result = ProportionSampleSizeResult(
        n=n, n_exact=n_exact, z=z, confidence_level=confidence_level, planning_p=planning_p, margin_of_error=margin_of_error,
        plain_english=(
            f"To estimate a proportion (e.g. a defect rate) within +/-{margin_of_error:.1%} at "
            f"{confidence_level * 100:.0f}% confidence -- using a planning estimate of {planning_p:.1%} -- "
            f"collect at least {n} units."
        ),
    )
    return compute(
        result,
        method="n = z^2*p*(1-p)/E^2, rounded up (NIST/SEMATECH §7.2.4 CI-for-a-proportion, solved for n)",
        input_data={"planning_p": planning_p, "margin_of_error": margin_of_error, "confidence_level": confidence_level},
        assumptions_checked=["planning_p is a reasonable planning estimate (0.5 if nothing better is known)"],
    )


# --- 3. Bias / convenience-sample warnings (rubric R-MEA-05 Pass #5) -------

CONVENIENCE_SAMPLE_WARNING = (
    "A convenience sample (whatever's easiest to grab -- the first N units off the line, one shift only, "
    "one operator only) can look fine on paper while badly misrepresenting the process. Name it as a "
    "convenience sample if that's what it is, and say what's left out."
)
SINGLE_SHIFT_WARNING = (
    "Data from one shift only won't show shift-to-shift differences -- name this limitation if the process "
    "runs more than one shift."
)
SINGLE_OPERATOR_WARNING = (
    "Data from one operator only won't show operator-to-operator differences -- name this limitation if more "
    "than one operator runs this process."
)
SHORT_WINDOW_WARNING = (
    "A short collection window can miss real process variation (day-of-week effects, startup/shutdown, "
    "seasonal swings) -- state the window and what it might be missing."
)


def sampling_bias_warnings(
    *,
    is_convenience_sample: bool = False,
    single_shift_only: bool = False,
    single_operator_only: bool = False,
    short_collection_window: bool = False,
) -> list[str]:
    """Named-and-checked, not vibes: R-MEA-05 Pass #5 asks the plan to
    state "is this a convenience sample? -- says so if so." Each flag maps
    to one plain-English warning string; none fire silently."""
    warnings: list[str] = []
    if is_convenience_sample:
        warnings.append(CONVENIENCE_SAMPLE_WARNING)
    if single_shift_only:
        warnings.append(SINGLE_SHIFT_WARNING)
    if single_operator_only:
        warnings.append(SINGLE_OPERATOR_WARNING)
    if short_collection_window:
        warnings.append(SHORT_WINDOW_WARNING)
    return warnings
