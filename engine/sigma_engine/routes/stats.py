"""POST /stats/descriptive, POST /stats/baseline, POST /stats/pareto,
POST /stats/sample-size -- stateless-by-default statistics endpoints (raw
data arrays + spec limits + flags in, provenance-stamped results out).
/stats/baseline additionally accepts a saved project dataset (dataset_id +
column) instead of a raw array -- the T-13 data path this milestone's
brief calls for -- while the plain raw-array path stays exactly as it was
for every existing caller and test. Whenever `project_id` is supplied
(dataset path or raw-array path), /stats/baseline also consults that
project's latest T-12 verdict (matrix §4a EXIT-02 capability-language
block) -- see _latest_msa_verdict below.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..datasets import DatasetStore
from ..project_store import ProjectStore
from ..provenance import Computed
from ..stats import sample_size as sample_size_mod
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


def _latest_msa_verdict(store: ProjectStore, project_id: str) -> str | None:
    """The project's latest T-12 (Measurement Check) verdict, if any T-12
    artifact has been saved -- routes/gates.py's _build_snapshot does the
    identical lookup for the gates.py hard block; duplicated here (rather
    than imported from routes/gates.py) so routes/stats.py's only
    dependency stays project_store, not another route module. None means
    either no T-12 has run yet, or the project itself doesn't exist --
    both are honest "nothing to consult" states, not errors."""
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError:
        return None
    for artifact_id, entry in meta.artifact_index.items():
        if entry.tool_id == "T-12":
            data = store.load_artifact(project_id, artifact_id, entry.latest_version)
            return (data.get("result") or {}).get("verdict")
    return None


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
        # Consulted whenever a project_id is given at all -- not only on
        # the dataset path -- so a raw-array request tied to a project
        # still honors that project's latest T-12 verdict (matrix §4a
        # EXIT-02 capability-language block).
        msa_verdict = _latest_msa_verdict(store, body.project_id) if body.project_id is not None else None
        result = run_baseline(
            data,
            usl=body.usl,
            lsl=body.lsl,
            operational_definition_ok=body.operational_definition_ok,
            enable_rule2=body.enable_rule2,
            enable_rule3=body.enable_rule3,
            apply_sigma_shift=body.apply_sigma_shift,
            msa_verdict=msa_verdict,
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


class SampleSizeRequest(BaseModel):
    """T-11's sample-size guidance panel: `calculator` is optional (the
    rule of thumb + bias warnings are always returned regardless), and
    when given, selects which margin-of-error formula runs."""

    calculator: Literal["mean", "proportion"] | None = None
    planning_sd: float | None = None
    planning_p: float | None = None
    margin_of_error: float | None = None
    confidence_level: float = sample_size_mod.SAMPLE_SIZE_DEFAULT_CONFIDENCE_LEVEL
    is_convenience_sample: bool = False
    single_shift_only: bool = False
    single_operator_only: bool = False
    short_collection_window: bool = False

    @model_validator(mode="after")
    def _calculator_inputs_present(self) -> "SampleSizeRequest":
        if self.calculator == "mean" and (self.planning_sd is None or self.margin_of_error is None):
            raise ValueError("calculator='mean' requires planning_sd and margin_of_error")
        if self.calculator == "proportion" and (self.planning_p is None or self.margin_of_error is None):
            raise ValueError("calculator='proportion' requires planning_p and margin_of_error")
        return self


@router.post("/sample-size")
def sample_size(body: SampleSizeRequest) -> dict[str, Any]:
    """Always returns the I-MR rule of thumb + applicable bias warnings;
    additionally runs the requested margin-of-error calculator, if any."""
    try:
        calc: dict[str, Any] | None = None
        if body.calculator == "mean":
            assert body.planning_sd is not None and body.margin_of_error is not None
            calc = sample_size_mod.sample_size_for_mean(
                body.planning_sd, body.margin_of_error, body.confidence_level
            ).model_dump(mode="json")
        elif body.calculator == "proportion":
            assert body.planning_p is not None and body.margin_of_error is not None
            calc = sample_size_mod.sample_size_for_proportion(
                body.planning_p, body.margin_of_error, body.confidence_level
            ).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    warnings = sample_size_mod.sampling_bias_warnings(
        is_convenience_sample=body.is_convenience_sample,
        single_shift_only=body.single_shift_only,
        single_operator_only=body.single_operator_only,
        short_collection_window=body.short_collection_window,
    )
    return {
        "rule_of_thumb": sample_size_mod.imr_baseline_rule_of_thumb().model_dump(mode="json"),
        "calculator": calc,
        "warnings": warnings,
    }
