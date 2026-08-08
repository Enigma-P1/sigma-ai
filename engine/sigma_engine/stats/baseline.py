"""Baseline orchestrator: the enforced order for a continuous-data
baseline (task brief / PLAN §4.1 Baseline row): spec limits + operational
definition first -> I-MR stability -> capability. Stable gets full
capability (Cp/Cpk + Pp/Ppk, distinguished); not stable gets EXIT-04
(Pp/Ppk only, performance_not_capability=True, instability signals
attached). Normality is then assessed and attached regardless of the
stability branch; a "concern" reading adds the EXIT-05 supplement -- an
empirical-percentile Pp/Ppk at n>=100, or an observed-yield/DPMO fallback
below n=100 (matrix §4a EXIT-05, frozen exactly at n=100).

Reading of "caveat path, not a stop" (matrix EXIT-05 row) applied here,
flagged for director review as a doc-conflict resolution rather than
silent: the matrix's short EXIT-05 row plus "never a silent auto-gate"
read as the normal-theory Cp/Cpk/Pp/Ppk numbers from the stability branch
are NEVER suppressed by a normality concern -- only the OPTIONAL
percentile-method addition is gated on n>=100. The terser §4a phrase
"below 100 no [percentile] indices -- observed yield/DPMO + caveat only"
is read as naming what replaces the percentile addition specifically,
not as replacing the whole capability section. If the intended reading
was "suppress Cp/Cpk/Pp/Ppk too when non-normal and n<100," that is a
one-line change to _apply_normality_supplement below.

EXIT-02 consultation (T-12 capability-language block, matrix §4a / rubric
R-MEA-07): the caller (routes/stats.py) looks up the project's *latest*
T-12 verdict and passes it in as `msa_verdict` -- this module stays free
of file I/O, same as everywhere else in stats/. `msa_verdict == "fail"`
sets `measurement_check="failed"` on the result and suppresses every
capability-language field (capability, percentile_capability,
observed_yield, sigma) regardless of stability -- "the suite blocks the
capability-language automatically" (rubric R-MEA-07 Fail line), not just a
UI label. Descriptive stats and the I-MR stability read are NOT
suppressed: those describe process behavior, not a capability claim.
"""

from __future__ import annotations

from typing import Literal, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from . import capability as capability_mod
from . import descriptive as descriptive_mod
from . import imr as imr_mod
from . import normality as normality_mod
from . import sigma_level as sigma_level_mod
from .constants import (
    EXIT04_MIN_POINTS_TO_FREEZE_LIMITS,
    EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY,
    PERCENTILE_LOWER,
    PERCENTILE_MEDIAN,
    PERCENTILE_UPPER,
)


class PercentileCapabilityResult(BaseModel):
    """EXIT-05's n>=100 non-normal supplement: empirical-quantile
    performance indices, explicitly not normal-theory Ppk (matrix §4a)."""

    model_config = ConfigDict(frozen=True)

    n: int
    p_low: float
    p_median: float
    p_high: float
    pp_percentile: float | None
    ppk_percentile: float
    label: str = "percentile method — not normal-theory Ppk"


def compute_percentile_capability(
    data: Sequence[float], usl: float | None, lsl: float | None
) -> Computed[PercentileCapabilityResult]:
    n = len(data)
    if n < EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY:
        raise ValueError(f"percentile capability requires n >= {EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY} (matrix §4a EXIT-05)")
    if usl is None and lsl is None:
        raise ValueError("compute_percentile_capability requires at least one spec limit")
    p_low, p_median, p_high = (float(x) for x in np.percentile(data, [PERCENTILE_LOWER, PERCENTILE_MEDIAN, PERCENTILE_UPPER], method="linear"))

    pp_percentile = (usl - lsl) / (p_high - p_low) if (usl is not None and lsl is not None) else None
    ppk_terms = []
    if usl is not None:
        ppk_terms.append((usl - p_median) / (p_high - p_median))
    if lsl is not None:
        ppk_terms.append((p_median - lsl) / (p_median - p_low))

    result = PercentileCapabilityResult(
        n=n, p_low=p_low, p_median=p_median, p_high=p_high,
        pp_percentile=pp_percentile, ppk_percentile=min(ppk_terms),
    )
    return compute(
        result,
        method=f"empirical percentile capability (matrix §4a EXIT-05): Pp_perc=(USL-LSL)/(p{PERCENTILE_UPPER}-p{PERCENTILE_LOWER}), "
        f"Ppk_perc=min[(USL-p50)/(p{PERCENTILE_UPPER}-p50), (p50-LSL)/(p50-p{PERCENTILE_LOWER})], linear-interpolation quantiles",
        input_data={"data": list(data), "usl": usl, "lsl": lsl},
        assumptions_checked=[f"n >= {EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY}"],
        warnings=["percentile method — not normal-theory Ppk"],
    )


class ObservedYieldResult(BaseModel):
    """EXIT-05's n<100 non-normal fallback: no distributional or stability
    assumption, just what fraction of the actual sample was in spec."""

    model_config = ConfigDict(frozen=True)

    n: int
    in_spec_fraction: float
    dpmo: float


def compute_observed_yield(data: Sequence[float], lsl: float | None, usl: float | None) -> Computed[ObservedYieldResult]:
    n = len(data)
    fraction = sigma_level_mod.observed_yield_in_spec(data, lsl, usl)
    result = ObservedYieldResult(n=n, in_spec_fraction=fraction, dpmo=(1 - fraction) * 1_000_000.0)
    return compute(
        result,
        method="observed_yield = fraction of sample within spec limits; dpmo=(1-yield)*1e6 "
        "(matrix §4a EXIT-05 n<100 fallback: no normality or stability assumption)",
        input_data={"data": list(data), "lsl": lsl, "usl": usl},
        assumptions_checked=["none -- assumption-free empirical count"],
    )


class BaselineResult(BaseModel):
    """The one result T-13's future route/UI renders. gate_ok=False means
    the enforced-order precondition (specs + operational definition, or
    n>=2) failed and nothing downstream was computed -- every other field
    is then None, never a partially-computed guess."""

    model_config = ConfigDict(frozen=True)

    gate_ok: bool
    gate_message: str | None
    n: int | None
    # Set to "failed" whenever the project's latest T-12 (Measurement
    # Check) verdict reads "fail" (matrix §4a EXIT-02) -- the flag the UI
    # renders as "unreliable -- measurement system failed" (task brief).
    # None means either no T-12 has run yet, or its latest verdict isn't
    # "fail" -- this field is never anything other than "failed" or None.
    measurement_check: Literal["failed"] | None
    descriptive: Computed[descriptive_mod.DescriptiveStats] | None
    stability: Computed[imr_mod.ImrChartResult] | None
    stable: bool | None
    stability_note: str | None
    capability: Computed[capability_mod.CapabilityResult] | None
    normality: Computed[normality_mod.NormalityResult] | None
    percentile_capability: Computed[PercentileCapabilityResult] | None
    observed_yield: Computed[ObservedYieldResult] | None
    sigma: Computed[sigma_level_mod.SigmaLevelResult] | None
    exits: tuple[str, ...]


def _gate_failure(message: str, n: int | None, measurement_check: Literal["failed"] | None = None) -> BaselineResult:
    return BaselineResult(
        gate_ok=False, gate_message=message, n=n, measurement_check=measurement_check,
        descriptive=None, stability=None, stable=None, stability_note=None,
        capability=None, normality=None, percentile_capability=None, observed_yield=None,
        sigma=None, exits=(),
    )


def _stability_verdict(n: int, imr_result: imr_mod.ImrChartResult) -> tuple[bool, str, bool]:
    """(stable, note, is_exit04) -- matrix §4a EXIT-04: a default-rule
    signal (rule 1 or 4) OR fewer than the companion floor's point count
    both mean "not stable," and both are read here as EXIT-04 (the §4a
    row states the point-count floor as EXIT-04's own companion clause)."""
    reasons = []
    if imr_result.has_default_rule_signal:
        reasons.append("a default Western Electric rule (rule 1 and/or rule 4) signaled")
    if n < EXIT04_MIN_POINTS_TO_FREEZE_LIMITS:
        reasons.append(f"only {n} points (< {EXIT04_MIN_POINTS_TO_FREEZE_LIMITS}): limits cannot be frozen (matrix §4a EXIT-04 companion floor)")
    if reasons:
        return False, "not stable -- you don't have a baseline yet: " + "; ".join(reasons), True
    return True, f"stable: {n} points, no default-rule signal", False


def run_baseline(
    data: Sequence[float],
    *,
    usl: float | None = None,
    lsl: float | None = None,
    operational_definition_ok: bool = False,
    enable_rule2: bool = False,
    enable_rule3: bool = False,
    apply_sigma_shift: bool = True,
    msa_verdict: str | None = None,
) -> BaselineResult:
    """The T-13 orchestrator. Enforced order: specs + operational
    definition -> n>=2 -> I-MR stability -> capability -> normality ->
    EXIT-05 supplement -> EXIT-02 capability-language suppression. See
    module docstring for the EXIT-05 "caveat, not a stop" reading applied
    below, and for the EXIT-02 consultation contract. `msa_verdict` is the
    project's latest T-12 verdict as looked up by the caller ("acceptable"
    / "marginal" / "fail" / None) -- only "fail" has any effect here."""
    measurement_check: Literal["failed"] | None = "failed" if msa_verdict == "fail" else None
    if usl is None and lsl is None:
        return _gate_failure("at least one spec limit (USL or LSL) is required before a baseline can run", None, measurement_check)
    if not operational_definition_ok:
        return _gate_failure(
            "operational definition must be confirmed before a baseline can run (matrix III.F.1 / PLAN §4.1)",
            len(data) or None, measurement_check,
        )
    n = len(data)
    if n < 2:
        return _gate_failure("at least 2 observations are required (moving range needs 2 consecutive points)", n, measurement_check)

    descriptive = descriptive_mod.compute_descriptive_stats(data)
    stability = imr_mod.compute_imr_chart(data, enable_rule2=enable_rule2, enable_rule3=enable_rule3)
    stable, stability_note, is_exit04 = _stability_verdict(n, stability.value)

    cap = capability_mod.compute_capability(
        mean=descriptive.value.mean, sigma_within=stability.value.sigma_within, sigma_overall=descriptive.value.sd,
        usl=usl, lsl=lsl, n=n, stable=stable,
    )
    normality_result = normality_mod.assess_normality(data)

    exits: list[str] = ["EXIT-04"] if is_exit04 else []
    percentile_capability: Computed[PercentileCapabilityResult] | None = None
    observed_yield: Computed[ObservedYieldResult] | None = None
    if normality_result.value.advisory == "concern":
        exits.append("EXIT-05")
        if n >= EXIT05_MIN_N_FOR_PERCENTILE_CAPABILITY:
            percentile_capability = compute_percentile_capability(data, usl, lsl)
        else:
            observed_yield = compute_observed_yield(data, lsl, usl)

    # Sigma level from the always-available overall (Pp/Ppk) indices, so
    # it's present whether or not the process is stable. dpmo=0 (perfect
    # process under the normal model) has no finite sigma level -- omit
    # rather than raise.
    cpu_index = capability_mod.cpu(usl, descriptive.value.mean, descriptive.value.sd) if usl is not None else None
    cpl_index = capability_mod.cpl(descriptive.value.mean, lsl, descriptive.value.sd) if lsl is not None else None
    dpmo = sigma_level_mod.dpmo_from_capability(cpu_index, cpl_index)
    sigma = sigma_level_mod.compute_sigma_level(dpmo, apply_shift=apply_sigma_shift) if dpmo > 0 else None

    # EXIT-02 capability-language block (matrix §4a / rubric R-MEA-07): a
    # failed measurement check suppresses every capability-language field
    # -- computed above like any other run, then blanked here -- so a
    # caller can never read a capability number off a BaselineResult whose
    # measurement system is known to have failed. Descriptive/stability
    # stay: those aren't a capability claim.
    if measurement_check == "failed":
        exits.append("EXIT-02")
        cap = None
        percentile_capability = None
        observed_yield = None
        sigma = None

    return BaselineResult(
        gate_ok=True, gate_message=None, n=n, measurement_check=measurement_check,
        descriptive=descriptive, stability=stability, stable=stable, stability_note=stability_note,
        capability=cap, normality=normality_result,
        percentile_capability=percentile_capability, observed_yield=observed_yield,
        sigma=sigma, exits=tuple(exits),
    )
