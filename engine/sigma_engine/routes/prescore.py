"""/prescore/{tool_id}: validate the posted artifact, then run its rule-
based rubric pre-score checks (PLAN §5.1 -- "deterministic pre-score first,"
the model's job is judgment on top of this, not rediscovering it)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from ..prescore.common import PrescoreResult
from ..registry import ARTIFACT_REGISTRY, PRESCORE_REGISTRY

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
