"""Normality advisory via the Anderson-Darling test (scipy) -- n-aware,
never a gate: it informs the EXIT-05 caveat path in baseline.py, it never
blocks a computation by itself.

Test: NIST/SEMATECH §1.3.5.14 "Anderson-Darling Test"
  https://www.itl.nist.gov/div898/handbook/eda/section3/eda35e.htm
  (A^2 statistic; "the hypothesis...is rejected if A^2 is greater than
  the critical value," critical values from Stephens 1974/76/77/79 --
  NIST does not tabulate them itself and defers to statistical software).
scipy.stats.anderson(..., method="interpolate") implements exactly that:
statistic plus a p-value interpolated from the Stephens tables, clipped
to [0.01, 0.15] (the tabulated range) -- an "approximate p-band" by
construction, never a false-precision point estimate.

Concern threshold p<0.05 and the "n-aware framing" instruction are frozen
in docs/traceability-matrix.md §4a, EXIT-05 row. The n<15
too-few-to-judge floor is this M2 brief's own threshold (see
constants.py's note on why it's deliberately distinct from EXIT-14's
n<20).
"""

from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict
from scipy import stats

from ..provenance import Computed, compute
from .constants import MIN_N_FOR_ANDERSON_DARLING_STATISTIC, MIN_N_FOR_NORMALITY_JUDGMENT, NORMALITY_CONCERN_ALPHA

Advisory = Literal["no_concern", "concern", "too_few_to_judge"]


def anderson_darling_statistic(data: Sequence[float]) -> tuple[float | None, float | None]:
    """(statistic, approx_pvalue), or (None, None) below the numerical
    floor where scipy's variance estimate degenerates."""
    if len(data) < MIN_N_FOR_ANDERSON_DARLING_STATISTIC:
        return None, None
    result = stats.anderson(list(data), dist="norm", method="interpolate")
    return float(result.statistic), float(result.pvalue)


def p_band(approx_pvalue: float | None) -> str:
    """Human-readable band, not false precision -- matches the
    interpolation table's own clipped range."""
    if approx_pvalue is None:
        return "not computed"
    if approx_pvalue >= 0.15:
        return "p >= 0.15"
    if approx_pvalue <= 0.01:
        return "p <= 0.01"
    return f"p ~= {approx_pvalue:.3f}"


def advisory_level(n: int, approx_pvalue: float | None) -> Advisory:
    if n < MIN_N_FOR_NORMALITY_JUDGMENT:
        return "too_few_to_judge"
    if approx_pvalue is not None and approx_pvalue < NORMALITY_CONCERN_ALPHA:
        return "concern"
    return "no_concern"


class NormalityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    statistic: float | None
    approx_pvalue: float | None
    p_band: str
    advisory: Advisory


def assess_normality(data: Sequence[float]) -> Computed[NormalityResult]:
    """The one supported way to produce a provenance-stamped
    NormalityResult. Never raises on small n -- returns
    advisory='too_few_to_judge' instead, per "never a silent auto-gate"."""
    n = len(data)
    statistic, pvalue = anderson_darling_statistic(data)
    result = NormalityResult(
        n=n, statistic=statistic, approx_pvalue=pvalue,
        p_band=p_band(pvalue), advisory=advisory_level(n, pvalue),
    )
    warnings = []
    if result.advisory == "too_few_to_judge":
        warnings.append(f"n={n} < {MIN_N_FOR_NORMALITY_JUDGMENT}: too few points to judge normality")
    return compute(
        result,
        method="Anderson-Darling (scipy.stats.anderson, method='interpolate', "
        "Stephens tables per NIST §1.3.5.14); concern iff p<0.05 and n>=15",
        input_data=list(data),
        assumptions_checked=[f"n >= {MIN_N_FOR_ANDERSON_DARLING_STATISTIC} for a computable statistic"],
        warnings=warnings,
    )
