"""I-MR (individuals / moving-range) control chart math.

Limits: NIST/SEMATECH §6.3.2.2 "Individuals Control Charts" (individuals
chart: xbar +/- 3*(MRbar/d2)) and §6.3.2.1's constants table (moving-range
chart: D4*MRbar / D3*MRbar, n=2 row) -- both cited with values in
constants.py. Reference-tested in tests/test_stats_imr.py against NIST's
own worked flow-rate example on the individuals-chart page.

Western Electric rules: NIST/SEMATECH §6.3.2, "What are the WECO rules for
signaling Out of Control?" Frozen default per docs/traceability-matrix.md
§4a: rule 1 (beyond 3 sigma) + rule 4 (8 consecutive same side) always on;
rule 2 (2 of 3 beyond 2 sigma) and rule 3 (4 of 5 beyond 1 sigma) are
opt-in flags, default False (running all four roughly quadruples the
false-alarm rate -- NIST cites Champ and Woodall 1987, ARL ~371 -> ~91.75).
"""

from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed, compute
from .constants import (
    CONTROL_CHART_SIGMA_MULTIPLIER,
    D2_CONSTANT_N2,
    D3_CONSTANT_N2,
    D4_CONSTANT_N2,
    WE_RULE1_SIGMA,
    WE_RULE2_COUNT,
    WE_RULE2_WINDOW,
    WE_RULE2_ZONE_SIGMA,
    WE_RULE3_COUNT,
    WE_RULE3_WINDOW,
    WE_RULE3_ZONE_SIGMA,
    WE_RULE4_RUN_LENGTH,
)

Side = Literal["above", "below"]


def moving_ranges(data: Sequence[float]) -> list[float]:
    """MR_i = |x_i - x_(i-1)| for consecutive individuals."""
    if len(data) < 2:
        raise ValueError("moving_ranges requires at least 2 observations")
    return [abs(data[i] - data[i - 1]) for i in range(1, len(data))]


def mr_bar(data: Sequence[float]) -> float:
    mrs = moving_ranges(data)
    return sum(mrs) / len(mrs)


def within_sigma_from_mr(mr_bar_value: float) -> float:
    """sigma_hat = MRbar / d2 -- the within-process sigma estimate for
    individuals data (reused by capability.py for Cp/Cpk)."""
    return mr_bar_value / D2_CONSTANT_N2


def individuals_limits(xbar: float, mr_bar_value: float) -> tuple[float, float, float]:
    """(UCL, CL, LCL) for the individuals (X) chart."""
    spread = CONTROL_CHART_SIGMA_MULTIPLIER * within_sigma_from_mr(mr_bar_value)
    return xbar + spread, xbar, xbar - spread


def mr_chart_limits(mr_bar_value: float) -> tuple[float, float, float]:
    """(UCL, CL, LCL) for the moving-range chart."""
    return D4_CONSTANT_N2 * mr_bar_value, mr_bar_value, D3_CONSTANT_N2 * mr_bar_value


class Signal(BaseModel):
    """One Western Electric rule violation: which rule, which points, which
    side of center, and a plain-language description (task's output contract)."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    start_index: int
    end_index: int
    side: Side
    description: str


def rule1_beyond_3sigma(data: Sequence[float], xbar: float, sigma: float) -> list[Signal]:
    """WECO rule 1: any single point beyond +/-3 sigma."""
    ucl, lcl = xbar + WE_RULE1_SIGMA * sigma, xbar - WE_RULE1_SIGMA * sigma
    signals: list[Signal] = []
    for i, x in enumerate(data):
        if x > ucl:
            signals.append(Signal(rule_id="rule1", start_index=i, end_index=i, side="above",
                                   description=f"point {i} ({x:g}) is beyond the +3-sigma limit ({ucl:.4g})"))
        elif x < lcl:
            signals.append(Signal(rule_id="rule1", start_index=i, end_index=i, side="below",
                                   description=f"point {i} ({x:g}) is beyond the -3-sigma limit ({lcl:.4g})"))
    return signals


def _run_signal(start: int, end: int, side: Side) -> Signal:
    length = end - start + 1
    return Signal(
        rule_id="rule4", start_index=start, end_index=end, side=side,
        description=f"{length} consecutive points fall {side} the center line (indices {start}-{end})",
    )


def rule4_run_of_8(data: Sequence[float], xbar: float) -> list[Signal]:
    """WECO rule 4: 8+ consecutive points on the same side of the center
    line. Fires once per maximal run (the run's full index range is
    reported, not just its 8th, triggering point)."""
    signals: list[Signal] = []
    run_side: Side | None = None
    run_start = 0
    for i, x in enumerate(data):
        side: Side | None = "above" if x > xbar else "below" if x < xbar else None
        if side != run_side:
            if run_side is not None and i - run_start >= WE_RULE4_RUN_LENGTH:
                signals.append(_run_signal(run_start, i - 1, run_side))
            run_side, run_start = side, i
    if run_side is not None and len(data) - run_start >= WE_RULE4_RUN_LENGTH:
        signals.append(_run_signal(run_start, len(data) - 1, run_side))
    return signals


def _zone_rule(
    data: Sequence[float], xbar: float, sigma: float, *, zone_sigma: float, count: int, window: int, rule_id: str
) -> list[Signal]:
    """Generic 'k of last n points beyond the given zone boundary, same
    side' test -- shared by rule 2 (2 of 3 beyond 2 sigma) and rule 3
    (4 of 5 beyond 1 sigma). Reports one signal per qualifying window
    position (standard SPC-software behavior: the signal persists for as
    long as the window condition holds, it is not deduplicated to one
    signal per run)."""
    upper, lower = xbar + zone_sigma * sigma, xbar - zone_sigma * sigma
    signals: list[Signal] = []
    for end in range(window - 1, len(data)):
        chunk = data[end - window + 1 : end + 1]
        above = sum(1 for x in chunk if x > upper)
        below = sum(1 for x in chunk if x < lower)
        start = end - window + 1
        if above >= count:
            signals.append(Signal(rule_id=rule_id, start_index=start, end_index=end, side="above",
                                   description=f"{above} of last {window} points beyond +{zone_sigma:g} sigma ({upper:.4g})"))
        if below >= count:
            signals.append(Signal(rule_id=rule_id, start_index=start, end_index=end, side="below",
                                   description=f"{below} of last {window} points beyond -{zone_sigma:g} sigma ({lower:.4g})"))
    return signals


def rule2_two_of_three_beyond_2sigma(data: Sequence[float], xbar: float, sigma: float) -> list[Signal]:
    """WECO rule 2 (opt-in): 2 of the last 3 points beyond 2 sigma, same
    side. Public wrapper over `_zone_rule` (control_chart.py's T-21
    monitoring read needs this callable directly -- compute_imr_chart
    below is the T-13 baseline's own caller of the exact same rule, no
    duplicated math between the two callers)."""
    return _zone_rule(data, xbar, sigma, zone_sigma=WE_RULE2_ZONE_SIGMA, count=WE_RULE2_COUNT, window=WE_RULE2_WINDOW, rule_id="rule2")


def rule3_four_of_five_beyond_1sigma(data: Sequence[float], xbar: float, sigma: float) -> list[Signal]:
    """WECO rule 3 (opt-in): 4 of the last 5 points beyond 1 sigma, same
    side. Public wrapper over `_zone_rule` -- see rule2_two_of_three_
    beyond_2sigma's docstring."""
    return _zone_rule(data, xbar, sigma, zone_sigma=WE_RULE3_ZONE_SIGMA, count=WE_RULE3_COUNT, window=WE_RULE3_WINDOW, rule_id="rule3")


class ImrChartResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    n: int
    xbar: float
    mr_bar: float
    sigma_within: float
    i_ucl: float
    i_cl: float
    i_lcl: float
    mr_ucl: float
    mr_cl: float
    mr_lcl: float
    signals: tuple[Signal, ...]
    rule2_enabled: bool
    rule3_enabled: bool

    @property
    def has_default_rule_signal(self) -> bool:
        """True if any frozen-default rule (1 or 4) fired -- the EXIT-04
        trigger condition (matrix §4a), independent of whether the opt-in
        zone rules 2/3 also fired."""
        return any(s.rule_id in ("rule1", "rule4") for s in self.signals)


def compute_imr_chart(
    data: Sequence[float], *, enable_rule2: bool = False, enable_rule3: bool = False
) -> Computed[ImrChartResult]:
    """The one supported way to produce a provenance-stamped
    ImrChartResult. Rule 1 + rule 4 always run (frozen default); rule 2/3
    run only when explicitly enabled."""
    if len(data) < 2:
        raise ValueError("compute_imr_chart requires at least 2 observations")

    xbar = sum(data) / len(data)
    mrb = mr_bar(data)
    sigma = within_sigma_from_mr(mrb)
    i_ucl, i_cl, i_lcl = individuals_limits(xbar, mrb)
    mr_ucl, mr_cl, mr_lcl = mr_chart_limits(mrb)

    signals = rule1_beyond_3sigma(data, xbar, sigma) + rule4_run_of_8(data, xbar)
    if enable_rule2:
        signals += rule2_two_of_three_beyond_2sigma(data, xbar, sigma)
    if enable_rule3:
        signals += rule3_four_of_five_beyond_1sigma(data, xbar, sigma)
    signals.sort(key=lambda s: (s.start_index, s.rule_id))

    result = ImrChartResult(
        n=len(data), xbar=xbar, mr_bar=mrb, sigma_within=sigma,
        i_ucl=i_ucl, i_cl=i_cl, i_lcl=i_lcl, mr_ucl=mr_ucl, mr_cl=mr_cl, mr_lcl=mr_lcl,
        signals=tuple(signals), rule2_enabled=enable_rule2, rule3_enabled=enable_rule3,
    )
    return compute(
        result,
        method="I-MR: individuals xbar +/- 3(MRbar/d2), MR D4*MRbar/D3*MRbar (NIST §6.3.2.1/.2, "
        "n=2 table); WECO rule1+rule4 default, rule2/3 opt-in (NIST §6.3.2 WECO)",
        input_data={"data": list(data), "enable_rule2": enable_rule2, "enable_rule3": enable_rule3},
        assumptions_checked=["n >= 2", "moving range of 2 consecutive individuals (d2=1.128, D4=3.267, table n=2)"],
    )
