"""Generic per-artifact-type CRUD: validate/save/load/list-versions, driven
by the tool_id -> model registry rather than five copy-pasted route sets.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from ..project_store import ProjectStore
from ..registry import ARTIFACT_REGISTRY, collect_standing_hard_flags, refresh_computed_fields
from .deps import get_store

router = APIRouter(tags=["artifacts"])


def _model_for(tool_id: str):
    model = ARTIFACT_REGISTRY.get(tool_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"unknown tool_id {tool_id!r}")
    return model


def _validation_error_detail(exc: ValidationError) -> Any:
    # exc.errors() can carry non-JSON-safe values (e.g. a `ctx` holding the
    # raised exception object); exc.json() is guaranteed JSON-safe.
    return json.loads(exc.json())


@router.post("/artifacts/{tool_id}/validate")
def validate_artifact(tool_id: str, body: dict[str, Any]) -> dict[str, Any]:
    model = _model_for(tool_id)
    try:
        validated = model.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_validation_error_detail(exc)) from exc
    return {"valid": True, "artifact": validated.model_dump(mode="json")}


@router.post("/project/{project_id}/artifacts/{tool_id}")
def save_artifact(
    project_id: str, tool_id: str, body: dict[str, Any], store: ProjectStore = Depends(get_store)
) -> dict[str, Any]:
    """Validate then save a new version. Version 1 if this artifact_id is
    new to the project, version N+1 otherwise -- "create" and "save" are
    the same operation here because every save is versioned (PLAN §4.5)."""
    model = _model_for(tool_id)

    if tool_id == "T-25":
        # M6 fidelity-panel fix 7: the A3 close check honors standing
        # prescore hard flags across this project's saved artifacts. The
        # sweep runs SERVER-side through the same registries this route
        # set uses (registry.collect_standing_hard_flags), and whatever
        # the caller posted in closure.standing_hard_flags is overwritten
        # wholesale -- server-computed, never client-supplied, the same
        # discipline as the engine-stamped tollgate questions. The A3's
        # own artifact_id is excluded: its prior stored version describes
        # a state this very save may be fixing. A malformed `closure`
        # falls through untouched so model validation reports the real
        # error.
        raw_closure = body.get("closure", {})
        if isinstance(raw_closure, dict):
            try:
                standing = collect_standing_hard_flags(
                    store, project_id, exclude_artifact_id=body.get("artifact_id"),
                )
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            closure = dict(raw_closure)
            closure["standing_hard_flags"] = [f.model_dump(mode="json") for f in standing]
            body = {**body, "closure": closure}

    try:
        validated = model.model_validate(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_validation_error_detail(exc)) from exc

    try:
        version = store.save_artifact(
            project_id, validated.artifact_id, tool_id, validated.model_dump(mode="json"), validated.updated_at
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"artifact_id": validated.artifact_id, "tool_id": tool_id, "version": version}


@router.get("/project/{project_id}/artifacts/{artifact_id}")
def load_artifact(
    project_id: str, artifact_id: str, version: int | None = None, store: ProjectStore = Depends(get_store)
) -> dict[str, Any]:
    try:
        data = store.load_artifact(project_id, artifact_id, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    # Re-derive computed fields on read (registry.refresh_computed_fields):
    # they are produced by model validators that only run on save, so an
    # artifact stored before a computed field existed would otherwise come
    # back without it forever and its screen would show an empty state on a
    # finished project.
    tool_id = data.get("tool_id")
    return refresh_computed_fields(tool_id, data) if isinstance(tool_id, str) else data


@router.get("/project/{project_id}/artifacts/{artifact_id}/versions")
def list_artifact_versions(
    project_id: str, artifact_id: str, store: ProjectStore = Depends(get_store)
) -> dict[str, Any]:
    return {"artifact_id": artifact_id, "versions": store.list_versions(project_id, artifact_id)}
