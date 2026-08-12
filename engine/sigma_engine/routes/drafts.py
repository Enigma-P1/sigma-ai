"""PUT/GET/DELETE .../project/{project_id}/drafts/{tool_id}, GET
.../project/{project_id}/drafts -- per-tool in-progress typing, saved so
navigating away never loses it (docs/uat/PLAN.md Phase 4.1: a supervisor
typed a charter's problem statement and goal, navigated away, and found
both gone -- Save sat behind eleven other required fields he had not
filled in yet).

A DRAFT IS NOT AN ARTIFACT (drafts.py's module docstring has the full
reasoning). This router only ever reads and writes drafts/ -- it does not
touch artifact_index, is never consulted by gates.py or export/, and does
not itself promote anything into a saved artifact. That promotion is the
desktop shell's job: the real T-XX save already goes through
routes/artifacts.py, and the shell is expected to DELETE the matching
draft the instant that save succeeds.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..drafts import DraftRecord, DraftStore
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project/{project_id}/drafts", tags=["drafts"])


class DraftSaveRequest(BaseModel):
    # Caller-supplied, like ProjectCreateRequest.created_at -- never
    # datetime.now() on the server, so callers (and tests) control it.
    updated_at: str
    # Deliberately untyped -- see drafts.py's module docstring for why a
    # draft's payload is never inspected or validated here.
    payload: Any = None


@router.put("/{tool_id}", response_model=DraftRecord)
def save_draft(
    project_id: str, tool_id: str, body: DraftSaveRequest, store: ProjectStore = Depends(get_store)
) -> DraftRecord:
    """Upsert. Returns the stored record, same shape GET returns."""
    try:
        return DraftStore(store).save_draft(project_id, tool_id, body.payload, body.updated_at)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{tool_id}", response_model=DraftRecord)
def get_draft(project_id: str, tool_id: str, store: ProjectStore = Depends(get_store)) -> DraftRecord:
    try:
        return DraftStore(store).load_draft(project_id, tool_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class DraftDeleteResponse(BaseModel):
    deleted: bool


@router.delete("/{tool_id}", response_model=DraftDeleteResponse)
def delete_draft(project_id: str, tool_id: str, store: ProjectStore = Depends(get_store)) -> DraftDeleteResponse:
    """Idempotent: 200 with deleted=True whether or not a draft was there
    to remove. The client deletes on a successful artifact save and must
    not have to care whether one existed (drafts.py's DraftStore.delete_draft)."""
    try:
        DraftStore(store).delete_draft(project_id, tool_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return DraftDeleteResponse(deleted=True)


class DraftSummary(BaseModel):
    """One row of the drafts list -- tool_id and freshness, not the
    payload. Cheap enough for a project screen to call on every open
    (DraftStore.list_drafts)."""

    tool_id: str
    updated_at: str


@router.get("", response_model=list[DraftSummary])
def list_drafts(project_id: str, store: ProjectStore = Depends(get_store)) -> list[DraftSummary]:
    try:
        drafts = DraftStore(store).list_drafts(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [DraftSummary(tool_id=d.tool_id, updated_at=d.updated_at) for d in drafts]
