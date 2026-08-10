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


class ProjectSummary(BaseModel):
    """One row of the project list. Deliberately more than a name: a list
    that only names projects makes you open each one to remember where you
    were."""

    project_id: str
    name: str
    updated_at: str
    artifact_count: int
    tools_done: list[str]
    latest_phase: str


# tool_id -> phase, for the "where was I" column. Mirrors the export module's
# TOOL_TITLES rather than duplicating a third copy of the phase map.
def _phase_for(tool_id: str) -> str:
    from ..export.project_pdf import TOOL_TITLES

    entry = TOOL_TITLES.get(tool_id)
    return entry[0] if entry else "Intake"


_PHASE_ORDER = ("Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap")


@router.get("s", response_model=list[ProjectSummary])
def list_projects(store: ProjectStore = Depends(get_store)) -> list[ProjectSummary]:
    """GET /projects -- what is actually on disk.

    Registered as "s" on the /project prefix so the path is /projects; a
    separate router would have been the tidier route but would also put this
    somewhere a reader of projects.py would not look for it.

    Ordered newest-updated first, which is what "where was I" wants.
    """
    summaries: list[ProjectSummary] = []
    for meta in store.list_projects():
        tools = sorted({entry.tool_id for entry in meta.artifact_index.values()})
        phases = [_phase_for(tool_id) for tool_id in tools]
        latest = max(phases, key=_PHASE_ORDER.index) if phases else "Intake"
        summaries.append(
            ProjectSummary(
                project_id=meta.project_id,
                name=meta.name,
                updated_at=meta.updated_at,
                artifact_count=len(meta.artifact_index),
                tools_done=tools,
                latest_phase=latest,
            )
        )
    return summaries


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
