"""Process capability: Cp/Cpk (within-sigma) and Pp/Ppk (overall-sigma).

Formulas: NIST/SEMATECH §6.1.6 "What is Process Capability?"
  https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm
    Cp  = (USL-LSL) / 6s        Cpu = (USL-xbar) / 3s
    Cpk = min(Cpu, Cpl)         Cpl = (xbar-LSL) / 3s
One-sided: only the applicable one-sided index is reported and Cp/Pp are
None (matrix III.F.1: "Cp/Pp not reported without both limits").

Within-vs-overall sigma (task brief / PLAN §4.1 Baseline row): Cp/Cpk use
sigma_within (individuals data: MRbar/d2, from imr.within_sigma_from_mr);
Pp/Ppk use sigma_overall (the plain sample sd). Both indices share the
exact same formula shape above -- only which sigma feeds it differs -- so
one set of functions computes both, parameterized by sigma.

Reference-tested (tests/test_stats_capability.py) against NIST's own
worked example on the §6.1.6 page (USL=20, LSL=8, xbar=16, s=2 ->
Cp=1.0, Cpu=0.6667, Cpl=1.3333, Cpk=0.6667) and against NIST's
"Translating capability into rejects" table (a centered process at
Cp=1.00/1.33/1.66/2.00 yields 2700/64/0.6/0.002 ppm two-sided -- used in
sigma_level.py's dpmo_from_capability reference test).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from .constants import CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER, CAPABILITY_TWO_SIDED_SIGMA_MULTIPLIER


def cpu(usl: float, mean: float, sigma: float) -> float:
    return (usl - mean) / (CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER * sigma)


def cpl(mean: float, lsl: float, sigma: float) -> float:
    return (mean - lsl) / (CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER * sigma)


def cp(usl: float, lsl: float, sigma: float) -> float:
    return (usl - lsl) / (CAPABILITY_TWO_SIDED_SIGMA_MULTIPLIER * sigma)


def cpk(usl: float | None, lsl: float | None, mean: float, sigma: float) -> float:
    """min(Cpu, Cpl); one-sided falls back to whichever limit exists."""
    if usl is not None and lsl is not None:
        return min(cpu(usl, mean, sigma), cpl(mean, lsl, sigma))
    if usl is not None:
        return cpu(usl, mean, sigma)
    if lsl is not None:
        return cpl(mean, lsl, sigma)
    raise ValueError("cpk requires at least one spec limit")


class CapabilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    mean: float
    sigma_within: float
    sigma_overall: float
    usl: float | None
    lsl: float | None
    one_sided: bool
    # Cp/Cpk: None whenever the process is not stable (EXIT-04 -- capability
    # is a claim only a stability check can license, PLAN §4.2).
    cp_index: float | None
    cpk_index: float | None
    # Pp/Ppk: always populated when spec limits exist, stable or not --
    # this is the EXIT-04 "performance, not capability" fallback view.
    pp_index: float | None
    ppk_index: float
    performance_not_capability: bool


def compute_capability(
    *,
    mean: float,
    sigma_within: float,
    sigma_overall: float,
    usl: float | None,
    lsl: float | None,
    n: int,
    stable: bool,
) -> Computed[CapabilityResult]:
    """The one supported way to produce a provenance-stamped
    CapabilityResult. Cp/Cpk are only populated when `stable` is True
    (matrix EXIT-04); Pp/Ppk are always populated -- PLAN's "not stable ->
    Pp/Ppk only, labeled performance-not-capability."""
    if usl is None and lsl is None:
        raise ValueError("compute_capability requires at least one spec limit")
    one_sided = usl is None or lsl is None
    both = not one_sided

    ppk_index = cpk(usl, lsl, mean, sigma_overall)
    pp_index = cp(usl, lsl, sigma_overall) if both else None

    cp_index = cp(usl, lsl, sigma_within) if (both and stable) else None
    cpk_index = cpk(usl, lsl, mean, sigma_within) if stable else None

    result = CapabilityResult(
        n=n, mean=mean, sigma_within=sigma_within, sigma_overall=sigma_overall,
        usl=usl, lsl=lsl, one_sided=one_sided,
        cp_index=cp_index, cpk_index=cpk_index, pp_index=pp_index, ppk_index=ppk_index,
        performance_not_capability=not stable,
    )
    warnings: list[str] = []
    if n < 50:
        warnings.append(f"n={n} < 50: NIST §6.1.6 calls 50 the minimum 'large enough' sample for capability indices")
    elif n < 100:
        warnings.append(f"n={n} < 100: NIST §6.1.6 recommends n>=100 for capability studies")
    input_data: dict[str, Any] = {
        "mean": mean, "sigma_within": sigma_within, "sigma_overall": sigma_overall,
        "usl": usl, "lsl": lsl, "n": n, "stable": stable,
    }
    return compute(
        result,
        method="Cp/Cpk (sigma_within), Pp/Ppk (sigma_overall) per NIST §6.1.6; "
        "Cpk=min(Cpu,Cpl), one-sided uses the applicable index only",
        input_data=input_data,
        assumptions_checked=["at least one spec limit present", "process assumed normal (NIST §6.1.6)"],
        warnings=warnings,
    )
