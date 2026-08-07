"""POST /stats/descriptive, POST /stats/baseline, POST /stats/pareto --
stateless-by-default statistics endpoints (raw data arrays + spec limits +
flags in, provenance-stamped results out). /stats/baseline additionally
accepts a saved project dataset (dataset_id + column) instead of a raw
array -- the T-13 data path this milestone's brief calls for -- while the
plain raw-array path stays exactly as it was for every existing caller
and test.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..datasets import DatasetStore
from ..project_store import ProjectStore
from ..provenance import Computed
from ..stats.baseline import BaselineResult, run_baseline
from ..stats.descriptive import DescriptiveStats, compute_descriptive_stats
from ..stats.pareto import ParetoResult, compute_pareto
from .deps import get_store

router = APIRouter(prefix="/stats", tags=["stats"])


class DescriptiveRequest(BaseModel):
    # sample_sd's denominator is n-1 (NIST §1.3.5.6) -- reject below 2 at
    # the schema level rather than letting compute_descriptive_stats raise.
    data: list[float] = Field(min_length=2)


@router.post("/descriptive", response_model=Computed[DescriptiveStats])
def descriptive(body: DescriptiveRequest) -> Computed[DescriptiveStats]:
    return compute_descriptive_stats(body.data)


class DatasetProvenance(BaseModel):
    """R-MEA-06's dataset -> BaselineResult hash chain, made explicit: the
    dataset's own file hash (datasets.py's DatasetMeta.sha256) alongside
    which column was pulled from it, so a reviewer can re-hash v1.csv and
    confirm it's the same file this BaselineResult came from."""

    dataset_id: str
    dataset_sha256: str
    column: str
    row_count_used: int


class BaselineRequest(BaseModel):
    data: list[float] | None = None
    project_id: str | None = None
    dataset_id: str | None = None
    column: str | None = None
    usl: float | None = None
    lsl: float | None = None
    operational_definition_ok: bool = False
    enable_rule2: bool = False
    enable_rule3: bool = False
    apply_sigma_shift: bool = True

    @model_validator(mode="after")
    def _exactly_one_data_source(self) -> "BaselineRequest":
        has_raw, has_dataset = self.data is not None, self.dataset_id is not None
        if has_raw == has_dataset:
            raise ValueError("provide either `data`, or `dataset_id` (+ `project_id` + `column`) -- not both, not neither")
        if has_dataset and (self.project_id is None or self.column is None):
            raise ValueError("`dataset_id` requires `project_id` and `column` too")
        return self


def _load_dataset_column(store: ProjectStore, project_id: str, dataset_id: str, column: str) -> tuple[list[float], DatasetProvenance]:
    data, meta = DatasetStore(store).load_numeric_column(project_id, dataset_id, column)
    return data, DatasetProvenance(dataset_id=dataset_id, dataset_sha256=meta.sha256, column=column, row_count_used=len(data))


@router.post("/baseline")
def baseline(body: BaselineRequest, store: ProjectStore = Depends(get_store)) -> dict[str, Any]:
    """Never 422s on "too little data" or "no specs yet" -- those are
    honest exits (gate_ok=False + gate_message), not client errors. A
    ValueError this route didn't anticipate (e.g. sigma=0 on constant
    data) still becomes a 422 rather than a raw 500. response_model is
    intentionally omitted (matching routes/artifacts.py's dynamic-shape
    routes) so the optional dataset_provenance key added below survives
    serialization instead of being silently stripped by response_model
    filtering -- the raw-array path's JSON shape is otherwise unchanged
    from BaselineResult's own field set, so existing tests still pass."""
    dataset_provenance: DatasetProvenance | None = None
    try:
        if body.dataset_id is not None:
            assert body.project_id is not None and body.column is not None  # enforced by the model_validator above
            data, dataset_provenance = _load_dataset_column(store, body.project_id, body.dataset_id, body.column)
        else:
            data = body.data or []
        result = run_baseline(
            data,
            usl=body.usl,
            lsl=body.lsl,
            operational_definition_ok=body.operational_definition_ok,
            enable_rule2=body.enable_rule2,
            enable_rule3=body.enable_rule3,
            apply_sigma_shift=body.apply_sigma_shift,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    payload = result.model_dump(mode="json")
    if dataset_provenance is not None:
        payload["dataset_provenance"] = dataset_provenance.model_dump(mode="json")
    return payload


class ParetoRequest(BaseModel):
    categories: list[str] = Field(min_length=1)


@router.post("/pareto", response_model=Computed[ParetoResult])
def pareto(body: ParetoRequest) -> Computed[ParetoResult]:
    """Raw-array-only, deliberately tiny (T-14 build brief): which column
    of which dataset feeds this is a client-side data-selection choice
    (routes/datasets.py already hands the desktop full dataset rows) --
    the counting/sorting/cumulative-share/vital-few math itself is 100%
    engine-side, same contract as /stats/descriptive."""
    try:
        return compute_pareto(body.categories)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
