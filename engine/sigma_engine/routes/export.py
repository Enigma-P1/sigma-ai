"""GET /project/{project_id}/artifacts/T-03/pdf -- PDF export for the
Project Charter (PLAN §8 M1: "PDF export for one artifact"). One route, one
artifact type; broader per-tool_id export is later-milestone scope, not
this brief.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from .. import __version__
from ..artifacts.charter import CharterArtifact
from ..export.charter_pdf import render_charter_pdf
from ..project_store import ProjectMetadata, ProjectStore
from .deps import get_store

router = APIRouter(tags=["export"])

CHARTER_TOOL_ID = "T-03"


def _find_charter_artifact_id(meta: ProjectMetadata) -> str | None:
    """A project's charter can be saved under any artifact_id (the desktop
    app always uses "charter" -- CharterForm.tsx -- but the demo fixture
    uses "coffee-charter", and nothing in the schema forces one name), so
    this looks up by tool_id the same way gates.py's _build_snapshot finds
    the picker artifact, instead of assuming a fixed id."""
    for artifact_id, entry in meta.artifact_index.items():
        if entry.tool_id == CHARTER_TOOL_ID:
            return artifact_id
    return None


@router.get("/project/{project_id}/artifacts/T-03/pdf")
def charter_pdf(project_id: str, version: int | None = None, store: ProjectStore = Depends(get_store)) -> Response:
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact_id = _find_charter_artifact_id(meta)
    if artifact_id is None:
        raise HTTPException(status_code=404, detail=f"no {CHARTER_TOOL_ID} charter saved in project {project_id!r}")

    try:
        data = store.load_artifact(project_id, artifact_id, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact = CharterArtifact.model_validate(data)
    resolved_version = version if version is not None else meta.artifact_index[artifact_id].latest_version
    pdf_bytes = render_charter_pdf(artifact, project_name=meta.name, version=resolved_version, engine_version=__version__)

    filename = f"{artifact.artifact_id}-v{resolved_version}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
