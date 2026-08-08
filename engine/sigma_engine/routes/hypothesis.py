"""POST /stats/hypothesis/route, POST /stats/hypothesis/run -- T-17's
routing-only and route+compute endpoints (build brief). Raw-array-only by
default (the request's `question` fully populated), OR one or more named
HypothesisQuestion array slots sourced from a saved project dataset column
instead -- the same dataset-provenance contract as /stats/baseline
(routes/stats.py's DatasetProvenance: dataset_id, dataset_sha256, column,
row_count_used), extended to a *list* since T-17's question shape can pull
from more than one column at once (two group columns, a before/after
pair, ...), where baseline only ever pulls one.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..datasets import DatasetStore
from ..project_store import ProjectStore
from ..stats.hypothesis_common import HypothesisQuestion
from ..stats.hypothesis_runner import run_hypothesis
from ..stats.hypothesis_selector import route_hypothesis
from .deps import get_store
from .stats import DatasetProvenance

router = APIRouter(prefix="/stats/hypothesis", tags=["hypothesis"])


class DatasetColumnRef(BaseModel):
    dataset_id: str
    column: str


class HypothesisRequestBody(BaseModel):
    """`question` is used as-is unless a *_column ref below overrides one
    of its array slots with a loaded dataset column -- `project_id` is
    required whenever any ref is given."""

    question: HypothesisQuestion
    project_id: str | None = None
    group_columns: dict[int, DatasetColumnRef] | None = None  # question.groups index -> column ref
    paired_before_column: DatasetColumnRef | None = None
    paired_after_column: DatasetColumnRef | None = None
    sample_column: DatasetColumnRef | None = None


def _load_column(store: ProjectStore, project_id: str, ref: DatasetColumnRef) -> tuple[list[float], DatasetProvenance]:
    data, meta = DatasetStore(store).load_numeric_column(project_id, ref.dataset_id, ref.column)
    return data, DatasetProvenance(dataset_id=ref.dataset_id, dataset_sha256=meta.sha256, column=ref.column, row_count_used=len(data))


def _resolve_question(store: ProjectStore, body: HypothesisRequestBody) -> tuple[HypothesisQuestion, list[DatasetProvenance]]:
    refs_given = bool(body.group_columns or body.paired_before_column or body.paired_after_column or body.sample_column)
    if not refs_given:
        return body.question, []
    if body.project_id is None:
        raise ValueError("a dataset column ref was given but project_id is missing")

    provenance: list[DatasetProvenance] = []
    question = body.question

    if body.group_columns:
        groups = list(question.groups)
        for idx, ref in body.group_columns.items():
            if idx < 0 or idx >= len(groups):
                raise ValueError(f"group_columns index {idx} is out of range for {len(groups)} group(s)")
            data, prov = _load_column(store, body.project_id, ref)
            groups[idx] = groups[idx].model_copy(update={"values": data})
            provenance.append(prov)
        question = question.model_copy(update={"groups": groups})

    for field, ref in (("paired_before", body.paired_before_column), ("paired_after", body.paired_after_column), ("sample", body.sample_column)):
        if ref is not None:
            data, prov = _load_column(store, body.project_id, ref)
            question = question.model_copy(update={field: data})
            provenance.append(prov)

    return question, provenance


@router.post("/route")
def route(body: HypothesisRequestBody, store: ProjectStore = Depends(get_store)) -> dict[str, Any]:
    """Routing only -- the printed decision tree the UI will render. Never
    computes a test statistic, so this is safe to call speculatively
    (e.g. as the user fills in the form) before any data is finalized."""
    try:
        question, dataset_provenance = _resolve_question(store, body)
        decision = route_hypothesis(question)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    payload = decision.model_dump(mode="json")
    if dataset_provenance:
        payload["dataset_provenance"] = [p.model_dump(mode="json") for p in dataset_provenance]
    return payload


@router.post("/run")
def run(body: HypothesisRequestBody, store: ProjectStore = Depends(get_store)) -> dict[str, Any]:
    """Route + compute in one call. Refuses with the named EXIT when one
    fires (`refused: true`, `result: null`) -- never a formally-computed-
    but-wrong answer for a case the tree knows it can't handle."""
    try:
        question, dataset_provenance = _resolve_question(store, body)
        result = run_hypothesis(question)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    payload = result.model_dump(mode="json")
    if dataset_provenance:
        payload["dataset_provenance"] = [p.model_dump(mode="json") for p in dataset_provenance]
    return payload
