"""/gates/check and /gates/override."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import gates as gates_module
from ..project_store import OverrideLogEntry, ProjectStore
from .deps import get_store

router = APIRouter(prefix="/gates", tags=["gates"])


def _build_snapshot(project_id: str, store: ProjectStore) -> gates_module.ProjectSnapshot:
    meta = store.load_project(project_id)
    tool_ids = {entry.tool_id for entry in meta.artifact_index.values()}

    # ProjectStore.latest_artifact_for_tool -- the shared lookup also used
    # by routes/stats.py's _latest_msa_verdict and prescore/cross_checks.py
    # (critic-confirmed defect: this loop used to keep overwriting on every
    # match with no break, landing on whichever artifact_id sorted last
    # alphabetically -- not necessarily the latest by any timestamp, and
    # not necessarily the same pick routes/stats.py's own old first-match
    # loop made for the same project).
    picker_data = store.latest_artifact_for_tool(project_id, meta, "T-01")
    msa_data = store.latest_artifact_for_tool(project_id, meta, "T-12")
    picker_route = picker_data.get("route") if picker_data is not None else None
    msa_verdict = (msa_data.get("result") or {}).get("verdict") if msa_data is not None else None

    return gates_module.ProjectSnapshot(artifact_tool_ids=tool_ids, picker_route=picker_route, msa_verdict=msa_verdict)


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
