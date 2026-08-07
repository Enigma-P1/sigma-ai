"""/project/create, /project/{project_id} (open), and /project/{project_id}/info."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..project_store import ArtifactIndexEntry, ProjectMetadata, ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project", tags=["project"])


class ProjectCreateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    created_at: str  # ISO8601, passed in by the caller -- never now() here


@router.post("/create", response_model=ProjectMetadata)
def create_project(body: ProjectCreateRequest, store: ProjectStore = Depends(get_store)) -> ProjectMetadata:
    try:
        return store.create_project(body.project_id, body.name, body.created_at)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{project_id}", response_model=ProjectMetadata)
def open_project(project_id: str, store: ProjectStore = Depends(get_store)) -> ProjectMetadata:
    try:
        return store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class ProjectInfoResponse(BaseModel):
    project_id: str
    name: str
    # Real, absolute on-disk folder (ProjectStore.resolved_project_path) --
    # closes the gap the desktop shell's project/path.ts flagged: no engine
    # endpoint reported a project's real path, so it rendered a documented-
    # default guess instead.
    folder_path: str
    artifact_count: int
    artifact_index: dict[str, ArtifactIndexEntry]


@router.get("/{project_id}/info", response_model=ProjectInfoResponse)
def project_info(project_id: str, store: ProjectStore = Depends(get_store)) -> ProjectInfoResponse:
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProjectInfoResponse(
        project_id=meta.project_id,
        name=meta.name,
        folder_path=str(store.resolved_project_path(project_id)),
        artifact_count=len(meta.artifact_index),
        artifact_index=meta.artifact_index,
    )
