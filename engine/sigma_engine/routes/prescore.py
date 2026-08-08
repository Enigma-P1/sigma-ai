"""/prescore/{tool_id}: validate the posted artifact, then run its rule-
based rubric pre-score checks (PLAN §5.1 -- "deterministic pre-score first,"
the model's job is judgment on top of this, not rediscovering it).

/prescore/cross/{project_id}: the reconciliation checks that need two
tools' saved data at once (prescore/cross_checks.py) -- a project-keyed
sibling of the tool-keyed route above, not a tool_id itself."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError, model_validator

from ..prescore.common import PrescoreResult
from ..prescore.cross_checks import CrossCheckResult, run_cross_checks
from ..project_store import ProjectStore
from ..registry import ARTIFACT_REGISTRY, PRESCORE_REGISTRY
from .deps import get_store

router = APIRouter(tags=["prescore"])


@router.post("/prescore/{tool_id}", response_model=list[PrescoreResult])
def run_prescore(tool_id: str, body: dict[str, Any]) -> list[PrescoreResult]:
    model = ARTIFACT_REGISTRY.get(tool_id)
    prescore_fn = PRESCORE_REGISTRY.get(tool_id)
    if model is None or prescore_fn is None:
        raise HTTPException(status_code=404, detail=f"unknown tool_id {tool_id!r}")

    try:
        artifact = model.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc

    return prescore_fn(artifact)


class CrossCheckRequest(BaseModel):
    """Both optional; when given together they name the saved project
    dataset column whose mean the engine computes fresh (never a client-
    supplied number) to stand in for check (b)'s "measured baseline"."""

    dataset_id: str | None = None
    column: str | None = None

    @model_validator(mode="after")
    def _column_requires_dataset(self) -> "CrossCheckRequest":
        if (self.dataset_id is None) != (self.column is None):
            raise ValueError("dataset_id and column must be given together, or neither at all")
        return self


@router.post("/prescore/cross/{project_id}", response_model=list[CrossCheckResult])
def run_prescore_cross(
    project_id: str, body: CrossCheckRequest = CrossCheckRequest(), store: ProjectStore = Depends(get_store)
) -> list[CrossCheckResult]:
    try:
        return run_cross_checks(store, project_id, dataset_id=body.dataset_id, column=body.column)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
