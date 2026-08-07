"""DPMO, sigma level (with the 1.5-sigma shift convention), FPY/RTY/DPU.

DPMO<->sigma-level formula and the 1.5-sigma shift convention are
industry (Motorola/Six Sigma) convention, not a NIST quantity. Cross-
checked live 2026-08-07 against two independently published tables
(tests/test_stats_sigma_level.py):
  Wikipedia "Six Sigma", section "Sigma levels" -- states the formula
  DPMO = 1,000,000 x (1 - Phi(level - 1.5)) explicitly and tabulates it:
    https://en.wikipedia.org/wiki/Six_Sigma
  MoreSteam.com "Six Sigma Conversion Table" (independent source, same
  1/2/3/4/5/6-sigma DPMO figures):
    https://www.moresteam.com/toolbox/six-sigma-conversion-table
`dpmo_from_capability` is not a third convention lookup -- it is derived
directly from NIST §6.1.6's own Cpu/Cpl definitions under the normal
model Cp/Cpk already assumes: 3*Cpu is exactly the mean-to-USL distance
in sigma units, so P(nonconforming, upper side) = Phi(-3*Cpu). Reference-
tested against NIST §6.1.6's own "Translating capability into rejects"
table (a centered process, Cp=1.00/1.33/1.66/2.00 -> ~2700/64/0.6/0.002
ppm two-sided).

FPY/DPU/RTY: standard Six Sigma definitions (traceability matrix II.E.1:
"cross-checked vs DMAIC.io + Qualica templates"). FPY here is the
Poisson-yield model (FPY = e^-DPU) -- the DPU-driven estimate used when
rolling several steps' yields together; a units-in/units-good observed
yield is a different, non-Poisson quantity, provided separately as
observed_yield_in_spec for baseline.py's EXIT-04/05 fallback (fraction of
a continuous sample actually inside spec limits, no model assumed).
"""

from __future__ import annotations

import math
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict
from scipy import stats

from ..provenance import Computed, compute
from .constants import (
    CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER,
    CONVENTION_WITH_SHIFT,
    CONVENTION_WITHOUT_SHIFT,
    SIGMA_SHIFT_DEFAULT,
)

Convention = Literal["with 1.5σ shift", "without shift"]


def dpu(defects: float, units: float) -> float:
    if units <= 0:
        raise ValueError("units must be > 0")
    return defects / units


def fpy_from_dpu(dpu_value: float) -> float:
    """Poisson yield model: FPY = e^-DPU."""
    return math.exp(-dpu_value)


def rty(fpys: Sequence[float]) -> float:
    """Rolled throughput yield = product of per-step FPYs."""
    if len(fpys) == 0:
        raise ValueError("rty requires at least one FPY")
    result = 1.0
    for f in fpys:
        result *= f
    return result


def dpmo_from_defects(defects: float, units: float, opportunities_per_unit: float = 1.0) -> float:
    if units <= 0 or opportunities_per_unit <= 0:
        raise ValueError("units and opportunities_per_unit must be > 0")
    return 1_000_000.0 * defects / (units * opportunities_per_unit)


def dpmo_from_capability(cpu_index: float | None, cpl_index: float | None) -> float:
    """Expected DPMO implied by one or two one-sided capability indices,
    derived from NIST §6.1.6's Cpu/Cpl definitions under the assumed-
    normal model: P(nonconforming, one side) = Phi(-3*Cp[u|l]).

    Known float64 floor, not a bug: norm.sf(3*Cp) underflows to exactly
    0.0 once Cp exceeds ~12.5 (z=3*Cp > ~37.5) -- a process ~37+ sigma
    from its nearer spec limit, never seen in real Green Belt data. When
    that happens this returns 0.0 (a true statement: the tail probability
    genuinely rounds to zero at double precision) and callers should treat
    dpmo<=0 as "no finite sigma level to report" rather than fabricating
    one -- see sigma_level_from_dpmo's own dpmo<=0 guard and baseline.py's
    `if dpmo > 0 else None`."""
    if cpu_index is None and cpl_index is None:
        raise ValueError("dpmo_from_capability requires at least one of cpu_index/cpl_index")
    total = 0.0
    if cpu_index is not None:
        total += stats.norm.sf(CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER * cpu_index)
    if cpl_index is not None:
        total += stats.norm.sf(CAPABILITY_ONE_SIDED_SIGMA_MULTIPLIER * cpl_index)
    return 1_000_000.0 * total


def observed_yield_in_spec(data: Sequence[float], lsl: float | None, usl: float | None) -> float:
    """Assumption-free fraction of the sample actually within spec limits
    -- the EXIT-04/05 fallback that needs no normality or stability claim."""
    if lsl is None and usl is None:
        raise ValueError("observed_yield_in_spec requires at least one spec limit")
    if len(data) == 0:
        raise ValueError("observed_yield_in_spec requires at least one observation")
    in_spec = sum(1 for x in data if (lsl is None or x >= lsl) and (usl is None or x <= usl))
    return in_spec / len(data)


def sigma_level_from_dpmo(dpmo: float, *, apply_shift: bool = True) -> tuple[float, Convention]:
    """z = Phi^-1(1 - dpmo/1e6); sigma_level = z (+1.5 if apply_shift).
    Always returns the convention label alongside the number."""
    if dpmo <= 0:
        raise ValueError("dpmo must be > 0 (use a very small positive value for 'zero defects observed')")
    z = float(stats.norm.ppf(1 - dpmo / 1_000_000.0))
    shift = SIGMA_SHIFT_DEFAULT if apply_shift else 0.0
    convention: Convention = CONVENTION_WITH_SHIFT if apply_shift else CONVENTION_WITHOUT_SHIFT  # type: ignore[assignment]
    return z + shift, convention


class SigmaLevelResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    dpmo: float
    sigma_level: float
    convention: Convention


def compute_sigma_level(dpmo: float, *, apply_shift: bool = True) -> Computed[SigmaLevelResult]:
    """The one supported way to produce a provenance-stamped
    SigmaLevelResult -- "the number never travels without its label" is
    enforced by the return type carrying `convention` alongside the value."""
    sigma_level, convention = sigma_level_from_dpmo(dpmo, apply_shift=apply_shift)
    result = SigmaLevelResult(dpmo=dpmo, sigma_level=sigma_level, convention=convention)
    return compute(
        result,
        method="sigma_level = Phi^-1(1 - dpmo/1e6)" + (" + 1.5 (shift applied)" if apply_shift else " (no shift)"),
        input_data={"dpmo": dpmo, "apply_shift": apply_shift},
        assumptions_checked=["1.5-sigma shift is reporting convention, not physics (matrix III.F.4)"],
    )
