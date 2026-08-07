"""POST /stats/descriptive, POST /stats/baseline -- stateless statistics
endpoints (raw data arrays + spec limits + flags in, provenance-stamped
results out). No project store involved: these compute, they don't
persist -- T-13's future save/version flow is a later-milestone route,
per the M2 brief ("Returns one BaselineResult the future T-13 route/UI
will render").
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..provenance import Computed
from ..stats.baseline import BaselineResult, run_baseline
from ..stats.descriptive import DescriptiveStats, compute_descriptive_stats

router = APIRouter(prefix="/stats", tags=["stats"])


class DescriptiveRequest(BaseModel):
    # sample_sd's denominator is n-1 (NIST §1.3.5.6) -- reject below 2 at
    # the schema level rather than letting compute_descriptive_stats raise.
    data: list[float] = Field(min_length=2)


@router.post("/descriptive", response_model=Computed[DescriptiveStats])
def descriptive(body: DescriptiveRequest) -> Computed[DescriptiveStats]:
    return compute_descriptive_stats(body.data)


class BaselineRequest(BaseModel):
    data: list[float]
    usl: float | None = None
    lsl: float | None = None
    operational_definition_ok: bool = False
    enable_rule2: bool = False
    enable_rule3: bool = False
    apply_sigma_shift: bool = True


@router.post("/baseline", response_model=BaselineResult)
def baseline(body: BaselineRequest) -> BaselineResult:
    """Never 422s on "too little data" or "no specs yet" -- those are
    honest exits (gate_ok=False + gate_message), not client errors. A
    ValueError this route didn't anticipate (e.g. sigma=0 on constant
    data) still becomes a 422 rather than a raw 500."""
    try:
        return run_baseline(
            body.data,
            usl=body.usl,
            lsl=body.lsl,
            operational_definition_ok=body.operational_definition_ok,
            enable_rule2=body.enable_rule2,
            enable_rule3=body.enable_rule3,
            apply_sigma_shift=body.apply_sigma_shift,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
