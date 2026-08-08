"""stats/p_chart.py -- p-chart math (T-21, the attribute half of Control
Charts): per-subgroup proportion defective, pooled center line p-bar, and
VARYING-n control limits per point -- UCL_i/LCL_i = pbar +/- 3*sqrt(pbar*
(1-pbar)/n_i) -- because unlike the I-MR chart's fixed 3-sigma band, a
p-chart's limits breathe with each subgroup's own sample size.

Source: NIST/SEMATECH e-Handbook of Statistical Methods §6.3.3.2 "p Chart
and np Chart": https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc332.htm
states exactly this formula --
    CL  = pbar = (sum D_i) / (sum n_i)
    UCL = pbar + 3*sqrt(pbar(1-pbar)/n)
    LCL = pbar - 3*sqrt(pbar(1-pbar)/n)
-- and its own worked example (dataset MONITOR-6_3_3_2.DAT: 30 wafer
samples, n=50 chips each, fraction defective 0.08-0.48) is reference-
tested in tests/test_stats_p_chart.py using that page's own raw data
(NIST states the formula and the raw table in plain text; the page's
computed CL/UCL/LCL are rendered only inside a chart image, not
extractable as text, so this engine computes them itself, from NIST's own
numbers, via NIST's own stated formula -- the same "hand-derived from a
NIST-cited constant/formula" precedent as stats/imr.py's MR-chart-limits
test). A second, small hand-computable fixture with VARYING n is also
reference-tested, since the NIST example happens to use constant n=50
throughout and so cannot by itself exercise the varying-n case this v1
scope names (matrix VI.A.2: "p-chart subgroup size handled the same way"
as I-MR's rational-subgrouping read).

LCL is floored at 0 and UCL is capped at 1 -- a proportion cannot leave
[0, 1] (NIST's own convention: a negative LCL is reported as 0).

Western Electric rule 1 (a point beyond ITS OWN per-point limits) and
rule 4 (8 consecutive points on one side of center) are the frozen
default (matrix §4a / §VI.A.1), matching imr.py's I-MR chart exactly.
Rule 4 is pure center-line/run-length logic, indifferent to whether the
series is individuals data or proportions -- stats/imr.py's own
rule4_run_of_8(data, xbar) is reused verbatim here (`don't duplicate`),
called with `data=[point.p for point in points]` and `xbar=pbar`. Rule 1
is NOT reusable as-is (imr.py's version assumes one fixed sigma band for
every point; a p-chart's limits vary per point), so it gets its own,
p-chart-specific implementation below. The `Signal` result shape is
imported from imr.py unchanged -- same reuse move.
"""

from __future__ import annotations

import math
from typing import Sequence

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from . import imr as imr_mod
from .constants import CONTROL_CHART_SIGMA_MULTIPLIER, EXIT04_MIN_POINTS_TO_FREEZE_LIMITS
from .imr import Signal

PCHART_FREEZE_FLOOR = EXIT04_MIN_POINTS_TO_FREEZE_LIMITS  # matrix §4a companion floor -- shared with I-MR, not chart-specific


class Subgroup(BaseModel):
    """One subgroup's raw input: how many units inspected (`n`) and how
    many were defective (pass/fail units -- EXIT-11 already refused
    counts-per-unit data by the time this module ever sees a Subgroup;
    see artifacts/control_chart.py's selector)."""

    model_config = ConfigDict(frozen=True)

    label: str
    n: int
    defective_count: int


class PChartPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    n: int
    defective_count: int
    p: float
    ucl: float
    lcl: float


class PChartResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    k: int  # number of subgroups
    total_defectives: int
    total_n: int
    p_bar: float
    points: tuple[PChartPoint, ...]
    signals: tuple[Signal, ...]
    # matrix §4a companion floor: >=20 subgroups AND (checked by the
    # caller, e.g. control_chart.py) no default-rule signal in the window
    # -- this field states the point-count half only; the caller combines
    # it with has_default_rule_signal, exactly baseline.py's own EXIT-04
    # read on the I-MR side.
    meets_freeze_floor: bool

    @property
    def has_default_rule_signal(self) -> bool:
        return any(s.rule_id in ("rule1", "rule4") for s in self.signals)


def p_bar(subgroups: Sequence[Subgroup]) -> float:
    total_n = sum(s.n for s in subgroups)
    if total_n <= 0:
        raise ValueError("p_bar requires total subgroup n > 0")
    return sum(s.defective_count for s in subgroups) / total_n


def p_chart_limits(pbar: float, n: int) -> tuple[float, float]:
    """(UCL, LCL) for one subgroup of size n. NIST §6.3.3.2: pbar +/-
    3*sqrt(pbar(1-pbar)/n); LCL floored at 0, UCL capped at 1 (a
    proportion can't leave [0, 1] -- NIST states the LCL floor; the UCL
    cap is this engine's own symmetric completion of that same rule,
    stated here since NIST's own worked example never reaches it)."""
    if n <= 0:
        raise ValueError("p_chart_limits requires n > 0")
    if not (0.0 <= pbar <= 1.0):
        raise ValueError(f"p_chart_limits requires 0 <= pbar <= 1, got {pbar!r}")
    spread = CONTROL_CHART_SIGMA_MULTIPLIER * math.sqrt(pbar * (1 - pbar) / n)
    return min(pbar + spread, 1.0), max(pbar - spread, 0.0)


def rule1_beyond_limits(points: Sequence[PChartPoint]) -> list[Signal]:
    """WECO rule 1, p-chart form: a point beyond ITS OWN per-point UCL/LCL
    (not a shared fixed band -- see module docstring)."""
    signals: list[Signal] = []
    for i, pt in enumerate(points):
        if pt.p > pt.ucl:
            signals.append(Signal(
                rule_id="rule1", start_index=i, end_index=i, side="above",
                description=f"{pt.label}: p={pt.p:.4g} is beyond its UCL ({pt.ucl:.4g}) for n={pt.n}",
            ))
        elif pt.p < pt.lcl:
            signals.append(Signal(
                rule_id="rule1", start_index=i, end_index=i, side="below",
                description=f"{pt.label}: p={pt.p:.4g} is below its LCL ({pt.lcl:.4g}) for n={pt.n}",
            ))
    return signals


def compute_p_chart(subgroups: Sequence[Subgroup]) -> Computed[PChartResult]:
    """The one supported way to produce a provenance-stamped PChartResult
    -- mirrors compute_imr_chart's contract exactly (imr.py)."""
    if len(subgroups) < 1:
        raise ValueError("compute_p_chart requires at least 1 subgroup")
    pbar = p_bar(subgroups)

    points = []
    for s in subgroups:
        ucl, lcl = p_chart_limits(pbar, s.n)
        points.append(PChartPoint(label=s.label, n=s.n, defective_count=s.defective_count, p=s.defective_count / s.n, ucl=ucl, lcl=lcl))
    signals = rule1_beyond_limits(points) + imr_mod.rule4_run_of_8([pt.p for pt in points], pbar)
    signals.sort(key=lambda s: (s.start_index, s.rule_id))

    result = PChartResult(
        k=len(subgroups), total_defectives=sum(s.defective_count for s in subgroups), total_n=sum(s.n for s in subgroups),
        p_bar=pbar, points=tuple(points), signals=tuple(signals),
        meets_freeze_floor=len(subgroups) >= PCHART_FREEZE_FLOOR,
    )
    return compute(
        result,
        method=(
            "p-chart: CL=pbar (pooled proportion, sum(defectives)/sum(n)); UCL_i/LCL_i = pbar +/- "
            "3*sqrt(pbar(1-pbar)/n_i) per subgroup, LCL floored at 0 / UCL capped at 1 (NIST/SEMATECH §6.3.3.2); "
            "WECO rule1 (beyond own per-point limits) + rule4 (8 consecutive same side of pbar) default per matrix §4a"
        ),
        input_data=[s.model_dump(mode="json") for s in subgroups],
        assumptions_checked=["n_i > 0 for every subgroup", "defective_count_i <= n_i for every subgroup"],
    )
