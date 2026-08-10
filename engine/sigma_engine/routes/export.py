"""PDF exports.

Two routes, deliberately different in kind:

* `/project/{id}/artifacts/T-03/pdf` -- the Project Charter, hand-laid
  (PLAN §8 M1: "PDF export for one artifact"). The charter's layout IS the
  deliverable; it goes in front of a sponsor on its own.

* `/project/{id}/export/pdf` -- the whole project, every saved tool in DMAIC
  order, via the generic renderer in export/project_pdf.py. Added because
  until it existed, 22 of the 23 tools could not leave the app in any form:
  a user did the entire project and had nothing to hand anybody. "Broader
  per-tool export is later-milestone scope" turned out to be the difference
  between a tool people can use and one they cannot.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from .. import __version__
from ..artifacts.charter import CharterArtifact
from ..export.charter_pdf import render_charter_pdf
from ..export.project_pdf import render_project_pdf
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


def _safe_filename(name: str) -> str:
    """A project name becomes a download filename, and project names are
    free text -- slashes, quotes, newlines and non-ASCII all arrive here.
    Content-Disposition is a header, so an unfiltered name is both a broken
    download and a header-injection shape. Keep it to characters that are
    safe in a filename on Windows and POSIX alike, and fall back to a fixed
    stem when nothing survives."""
    kept = [c if (c.isalnum() or c in " -_") else "-" for c in name]
    cleaned = "-".join("".join(kept).split())
    cleaned = cleaned.strip("-")[:60]
    return cleaned or "sigma-project"


@router.get("/project/{project_id}/export/pdf")
def project_pdf(project_id: str, store: ProjectStore = Depends(get_store)) -> Response:
    """Every saved tool in one PDF.

    Loads each artifact defensively: a project that has run through a schema
    change may hold one artifact the current models no longer accept, and
    refusing the whole export over it would reproduce the exact "you can't
    get your work out" failure this route exists to fix. A tool that cannot
    be read is skipped, and the remainder still exports.
    """
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifacts: list[tuple[str, dict, int]] = []
    for artifact_id, entry in meta.artifact_index.items():
        try:
            data = store.load_artifact(project_id, artifact_id, None)
        except (FileNotFoundError, ValueError):
            continue
        artifacts.append((entry.tool_id, data, entry.latest_version))

    if not artifacts:
        raise HTTPException(
            status_code=404,
            detail=f"project {project_id!r} has no saved tools yet -- fill in at least one before exporting",
        )

    pdf_bytes = render_project_pdf(
        project_name=meta.name,
        project_id=meta.project_id,
        artifacts=artifacts,
        engine_version=__version__,
    )
    filename = f"{_safe_filename(meta.name)}-project-record.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
