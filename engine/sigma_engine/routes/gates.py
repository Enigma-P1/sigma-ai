"""/gates/check and /gates/override."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import gates as gates_module
from ..project_store import OverrideLogEntry, ProjectStore
from .deps import get_store

router = APIRouter(prefix="/gates", tags=["gates"])


def _build_snapshot(project_id: str, store: ProjectStore) -> gates_module.ProjectSnapshot:
    # Thin wrapper -- the real logic is gates_module.build_project_snapshot
    # (promoted there at M5 unit 2 so advisor/modes.py's tollgate context
    # selector can build the identical snapshot without a second,
    # independently-maintained copy). Kept as a local name since every
    # call site in this file already reads `_build_snapshot(...)`.
    return gates_module.build_project_snapshot(store, project_id)


class GateCheckRequest(BaseModel):
    gate_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)


@router.post("/check", response_model=gates_module.GateResult)
def check_gate(body: GateCheckRequest, store: ProjectStore = Depends(get_store)) -> gates_module.GateResult:
    try:
        snapshot = _build_snapshot(body.project_id, store)
        overrides = store.list_overrides(body.project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        return gates_module.check(body.gate_id, snapshot, overrides)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class GateOverrideRequest(BaseModel):
    gate_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    timestamp: str


@router.post("/override", response_model=OverrideLogEntry)
def override_gate(body: GateOverrideRequest, store: ProjectStore = Depends(get_store)) -> OverrideLogEntry:
    try:
        snapshot = _build_snapshot(body.project_id, store)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        return gates_module.override(body.gate_id, body.project_id, body.reason, body.timestamp, store, snapshot)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
