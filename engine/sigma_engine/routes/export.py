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

import base64
import binascii
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from .. import __version__
from ..artifacts.charter import CharterArtifact
from ..artifacts.control_chart import ControlChartArtifact
from ..artifacts.fmea import FmeaArtifact
from ..artifacts.gage_rr import GageRRArtifact
from ..artifacts.hypothesis import HypothesisRunArtifact
from ..artifacts.msa import MsaArtifact
from ..artifacts.proof import ProofArtifact
from ..export import report_pdf, report_theme
from ..export.charter_pdf import render_charter_pdf
from ..export.project_pdf import render_project_pdf
from ..export.reports import capability as capability_report_mod
from ..export.reports import control_chart as control_chart_report_mod
from ..export.reports import fmea as fmea_report_mod
from ..export.reports import gage_rr as gage_rr_report_mod
from ..export.reports import hypothesis as hypothesis_report_mod
from ..export.reports import msa as msa_report_mod
from ..export.reports import proof as proof_report_mod
from ..project_store import ProjectMetadata, ProjectStore
from ..stats.baseline import run_baseline
from .deps import get_store
from .stats import _latest_msa_verdict, _load_dataset_column

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


class ChartCapture(BaseModel):
    """A chart image lifted off the user's screen, with the fingerprint of
    the data it was drawn from so a stale image cannot be paired with fresh
    numbers (export/report_pdf.py explains why this matters)."""

    png_base64: str
    data_hash: str | None = None


class ReportRequest(BaseModel):
    """Everything a report needs that the engine cannot look up itself.

    Note what is NOT here: any computed value. The client sends the chart
    picture and the inputs; every number printed is recomputed server-side.
    A client that could post its own statistics could put an unverified
    figure on a page carrying the engine's name in the footer.
    """

    chart: ChartCapture | None = None
    # T-13 only -- the baseline is computed from a dataset, not stored as an
    # artifact, so the report has to be told which dataset and which specs.
    dataset_id: str | None = None
    column: str | None = None
    usl: float | None = None
    lsl: float | None = None
    enable_rule2: bool = False
    enable_rule3: bool = False
    # Mirrors the baseline screen's own confirmation. Without it the engine's
    # gate refuses to compute a baseline at all (matrix III.F.1) -- correctly,
    # but the report would then always print "cannot be answered yet" even for
    # a project whose screen shows a finished capability study.
    operational_definition_ok: bool = False


def _decode_png(capture: ChartCapture | None) -> bytes | None:
    if capture is None or not capture.png_base64:
        return None
    raw = capture.png_base64
    if "," in raw[:64] and raw.lstrip().startswith("data:"):
        raw = raw.split(",", 1)[1]  # strip a data: URI preamble if one came along
    try:
        return base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        return None


@router.post("/project/{project_id}/report/T-13/pdf")
def capability_report(
    project_id: str, body: ReportRequest, store: ProjectStore = Depends(get_store)
) -> Response:
    """The Process Capability one-pager."""
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not body.dataset_id or not body.column:
        raise HTTPException(status_code=422, detail="dataset_id and column are required for the T-13 report")

    try:
        values, provenance = _load_dataset_column(store, project_id, body.dataset_id, body.column)
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = run_baseline(
        values,
        usl=body.usl,
        lsl=body.lsl,
        enable_rule2=body.enable_rule2,
        enable_rule3=body.enable_rule3,
        operational_definition_ok=body.operational_definition_ok,
        msa_verdict=_latest_msa_verdict(store, project_id),
    )

    png, reason = report_pdf.check_chart(
        _decode_png(body.chart),
        body.chart.data_hash if body.chart else None,
        report_pdf.data_fingerprint(values),
    )

    rows = [
        ("Dataset", f"{body.dataset_id} · column '{body.column}'"),
        ("Observations", str(len(values))),
        ("Specification", _spec_text(body.lsl, body.usl)),
        ("Engine version", __version__),
    ]
    if provenance is not None:
        source = getattr(provenance, "source_filename", None)
        if source:
            rows.insert(1, ("Source file", str(source)))

    def story(content_width: float):
        return capability_report_mod.build_story(
            result=result,
            project_name=meta.name,
            chart_png=png,
            chart_unavailable_reason=reason,
            provenance_rows=rows,
            exported_at=report_theme.utc_stamp(),
            content_width=content_width,
        )

    pdf_bytes = report_pdf.render(
        story_builder=story,
        title=f"{meta.name} — Process Capability",
        project_id=project_id,
        engine_version=__version__,
    )
    return _pdf_response(pdf_bytes, f"{_safe_filename(meta.name)}-T13-capability.pdf")


def _spec_text(lsl: float | None, usl: float | None) -> str:
    if lsl is None and usl is None:
        return "none given"
    low = "—" if lsl is None else f"{lsl:g}"
    high = "—" if usl is None else f"{usl:g}"
    return f"LSL {low} / USL {high}"


def _find_artifact_id(meta: ProjectMetadata, tool_id: str) -> str | None:
    for artifact_id, entry in meta.artifact_index.items():
        if entry.tool_id == tool_id:
            return artifact_id
    return None


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# tool_id -> (artifact model, report module, wants a chart image, page size).
# One row per artifact-backed report, so adding the next one is a table entry
# rather than another near-copy of the same route body. T-13 stays separate
# above: it is computed from a dataset, not stored as an artifact, so it needs
# inputs this generic path has nowhere to put.
ARTIFACT_REPORTS: dict[str, tuple[Any, Any, bool]] = {
    "T-12": (MsaArtifact, msa_report_mod, False),
    "T-16": (FmeaArtifact, fmea_report_mod, False),
    "T-17": (HypothesisRunArtifact, hypothesis_report_mod, True),
    "T-20": (ProofArtifact, proof_report_mod, True),
    "T-21": (ControlChartArtifact, control_chart_report_mod, True),
    "T-35": (GageRRArtifact, gage_rr_report_mod, False),
}


def _chart_series(tool_id: str, artifact: Any) -> list[float] | None:
    """The series a tool's chart is drawn from, for the fingerprint check.

    None means "this report has no single underlying series", and
    report_pdf.check_chart then takes the image on trust -- there is nothing
    to compare it against, and inventing a comparison would be theatre.
    """
    if tool_id == "T-21":
        return artifact.frozen_window_values or artifact.imr_values
    if tool_id == "T-20":
        return list(artifact.after.values) if artifact.after else None
    return None


@router.post("/project/{project_id}/report/{tool_id}/pdf")
def artifact_report(
    project_id: str, tool_id: str, body: ReportRequest, store: ProjectStore = Depends(get_store)
) -> Response:
    """One route for every artifact-backed report (see ARTIFACT_REPORTS)."""
    entry = ARTIFACT_REPORTS.get(tool_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"no report defined for {tool_id!r}")
    model, module, wants_chart = entry

    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact_id = _find_artifact_id(meta, tool_id)
    if artifact_id is None:
        raise HTTPException(status_code=404, detail=f"no {tool_id} saved in project {project_id!r}")

    data = store.load_artifact(project_id, artifact_id, None)
    artifact = model.model_validate(data)
    version = meta.artifact_index[artifact_id].latest_version

    kwargs: dict[str, Any] = {}
    if wants_chart:
        series = _chart_series(tool_id, artifact)
        png, reason = report_pdf.check_chart(
            _decode_png(body.chart),
            body.chart.data_hash if body.chart else None,
            report_pdf.data_fingerprint(series) if series else None,
        )
        kwargs["chart_png"] = png
        kwargs["chart_unavailable_reason"] = reason

    rows = [("Artifact", f"{artifact_id} · v{version}"), ("Engine version", __version__)]

    def story(content_width: float):
        return module.build_story(
            artifact=artifact,
            project_name=meta.name,
            version=version,
            provenance_rows=rows,
            exported_at=report_theme.utc_stamp(),
            content_width=content_width,
            **kwargs,
        )

    page_size = getattr(module, "PAGE_SIZE", None)
    pdf_bytes = report_pdf.render(
        story_builder=story,
        title=f"{meta.name} — {module.TOOL_TITLE}",
        project_id=project_id,
        engine_version=__version__,
        page_size=page_size,
    )
    return _pdf_response(pdf_bytes, f"{_safe_filename(meta.name)}-{tool_id}-report.pdf")
