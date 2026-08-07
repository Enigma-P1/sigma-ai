"""/project/create and /project/{project_id} (open)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..project_store import ProjectMetadata, ProjectStore
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
