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
from ..artifacts.a3 import A3Artifact
from ..artifacts.charter import CharterArtifact
from ..artifacts.control_chart import ControlChartArtifact
from ..artifacts.control_plan import ControlPlanArtifact
from ..artifacts.check_sheet import CheckSheetArtifact
from ..artifacts.copq import CopqArtifact
from ..artifacts.data_collection_plan import DataCollectionPlanArtifact
from ..artifacts.five_s import FiveSArtifact
from ..artifacts.fishbone import FishboneArtifact
from ..artifacts.fmea import FmeaArtifact
from ..artifacts.gage_rr import GageRRArtifact
from ..artifacts.hypothesis import HypothesisRunArtifact
from ..artifacts.msa import MsaArtifact
from ..artifacts.picker import PickerArtifact
from ..artifacts.process_map import ProcessMapArtifact
from ..artifacts.pilot_plan import PilotPlanArtifact
from ..artifacts.proof import ProofArtifact
from ..artifacts.sipoc import SipocArtifact
from ..artifacts.spaghetti import SpaghettiArtifact
from ..artifacts.solution_matrix import SolutionMatrixArtifact
from ..artifacts.standard_work import StandardWorkArtifact
from ..artifacts.time_study import TimeStudyArtifact
from ..artifacts.voc_ctq import VocCtqArtifact
from ..artifacts.yield_calc import YieldCalcArtifact
from ..datasets import DatasetStore
from ..export import pack_pdf, report_pdf, report_theme
from ..export.charter_pdf import render_charter_pdf
from ..export.project_pdf import render_project_pdf
from ..export.reports import a3 as a3_report_mod
from ..export.reports import capability as capability_report_mod
from ..export.reports import control_chart as control_chart_report_mod
from ..export.reports import control_plan as control_plan_report_mod
from ..export.reports import check_sheet as check_sheet_report_mod
from ..export.reports import copq as copq_report_mod
from ..export.reports import data_collection_plan as collection_plan_report_mod
from ..export.reports import five_s as five_s_report_mod
from ..export.reports import fishbone as fishbone_report_mod
from ..export.reports import fmea as fmea_report_mod
from ..export.reports import gage_rr as gage_rr_report_mod
from ..export.reports import hypothesis as hypothesis_report_mod
from ..export.reports import msa as msa_report_mod
from ..export.reports import picker as picker_report_mod
from ..export.reports import process_map as process_map_report_mod
from ..export.reports import pilot_plan as pilot_plan_report_mod
from ..export.reports import proof as proof_report_mod
from ..export.reports import sipoc as sipoc_report_mod
from ..export.reports import spaghetti as spaghetti_report_mod
from ..export.reports import solution_matrix as solution_matrix_report_mod
from ..export.reports import standard_work as standard_work_report_mod
from ..export.reports import summary as summary_report_mod
from ..export.reports import time_study as time_study_report_mod
from ..export.reports import voc_ctq as voc_ctq_report_mod
from ..export.reports import yield_calc as yield_calc_report_mod
from ..project_store import ProjectMetadata, ProjectStore
from ..stats.baseline import run_baseline
from ..stats.pareto import compute_pareto
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
    "T-01": (PickerArtifact, picker_report_mod, False),
    "T-02": (CopqArtifact, copq_report_mod, False),
    "T-04": (SipocArtifact, sipoc_report_mod, False),
    "T-05": (VocCtqArtifact, voc_ctq_report_mod, False),
    "T-06": (ProcessMapArtifact, process_map_report_mod, True),
    "T-07": (SpaghettiArtifact, spaghetti_report_mod, True),
    "T-08": (CheckSheetArtifact, check_sheet_report_mod, False),
    "T-09": (TimeStudyArtifact, time_study_report_mod, False),
    "T-10": (YieldCalcArtifact, yield_calc_report_mod, False),
    "T-11": (DataCollectionPlanArtifact, collection_plan_report_mod, False),
    "T-12": (MsaArtifact, msa_report_mod, False),
    "T-15": (FishboneArtifact, fishbone_report_mod, True),
    "T-16": (FmeaArtifact, fmea_report_mod, False),
    "T-17": (HypothesisRunArtifact, hypothesis_report_mod, True),
    "T-18": (SolutionMatrixArtifact, solution_matrix_report_mod, False),
    "T-19": (PilotPlanArtifact, pilot_plan_report_mod, False),
    "T-20": (ProofArtifact, proof_report_mod, True),
    "T-21": (ControlChartArtifact, control_chart_report_mod, True),
    "T-22": (ControlPlanArtifact, control_plan_report_mod, False),
    "T-23": (FiveSArtifact, five_s_report_mod, False),
    "T-24": (StandardWorkArtifact, standard_work_report_mod, False),
    "T-25": (A3Artifact, a3_report_mod, False),
    "T-35": (GageRRArtifact, gage_rr_report_mod, True),
}

# Bar order for T-35's components-of-variation chart. MUST match the
# client's CHART_COMPONENT_ORDER (tools/gagerr/gageRrLogic.ts) exactly:
# the same values in the same order are hashed on both sides, and a
# mismatch means the engine drops the picture. test_report_pdf.py pins the
# two orders against each other.
GRR_CHART_COMPONENT_ORDER = ("gage_rr", "repeatability", "reproducibility", "part_to_part")


def _grr_chart_series(artifact: Any) -> list[float] | None:
    """T-35's chart is a bar per variance component, not a data series, so
    the thing to fingerprint is the bars themselves: %study variation for
    each component, then %tolerance when the study has one. Including the
    tolerance half means a tolerance-only edit still moves the hash -- a
    stale chart would otherwise print tolerance bars that disagree with the
    verdict beside them."""
    result = getattr(artifact, "result", None)
    if result is None:
        return None
    by_name = {c.name: c for c in result.components}
    study = [by_name[name].percent_study_variation for name in GRR_CHART_COMPONENT_ORDER if name in by_name]
    if len(study) != len(GRR_CHART_COMPONENT_ORDER):
        return None
    tolerance = [by_name[name].percent_tolerance for name in GRR_CHART_COMPONENT_ORDER]
    if all(v is not None for v in tolerance):
        return study + [float(v) for v in tolerance]
    return study


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
    if tool_id == "T-35":
        return _grr_chart_series(artifact)
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


class PackRequest(BaseModel):
    """Captures for a whole pack, keyed by tool id.

    A pack can contain several chart-bearing reports and the client can only
    capture what is currently mounted -- typically one screen's worth. So
    this is best-effort by design: a report with no capture prints the same
    "chart not captured" line it prints anywhere else, which is already the
    honest, designed behaviour rather than a special case invented here.
    """

    charts: dict[str, ChartCapture] = {}


@router.post("/project/{project_id}/pack/{phase}/pdf")
def phase_pack(
    project_id: str, phase: str, body: PackRequest, store: ProjectStore = Depends(get_store)
) -> Response:
    """One phase's reports, with a cover and a verdict index.

    Deliberately built by CALLING the same per-tool report modules the
    single-report route uses, rather than by re-rendering their content: a
    pack that drifted from the report it claims to contain would be worse
    than no pack.
    """
    if phase not in pack_pdf.PACK_PHASES:
        raise HTTPException(
            status_code=404,
            detail=f"no pack defined for phase {phase!r} -- packs exist for {', '.join(pack_pdf.PACK_PHASES)}",
        )

    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    entries: list[tuple[str, Any, tuple[str, Any]]] = []
    missing: list[str] = []

    for tool_id in pack_pdf.tools_in_phase(phase):
        entry = ARTIFACT_REPORTS.get(tool_id)
        artifact_id = _find_artifact_id(meta, tool_id)
        if entry is None or artifact_id is None:
            # Either the tool was never done, or it has no report of its own
            # (T-03's charter has its own hand-laid PDF). Both are "not in
            # this pack", and both get named on the index rather than
            # silently dropped.
            missing.append(tool_id)
            continue

        model, module, wants_chart = entry
        try:
            data = store.load_artifact(project_id, artifact_id, None)
            artifact = model.model_validate(data)
        except (FileNotFoundError, ValueError):
            missing.append(tool_id)
            continue

        version = meta.artifact_index[artifact_id].latest_version
        kwargs: dict[str, Any] = {}
        if wants_chart:
            capture = body.charts.get(tool_id)
            series = _chart_series(tool_id, artifact)
            png, reason = report_pdf.check_chart(
                _decode_png(capture),
                capture.data_hash if capture else None,
                report_pdf.data_fingerprint(series) if series else None,
            )
            kwargs["chart_png"] = png
            kwargs["chart_unavailable_reason"] = reason

        rows = [("Artifact", f"{artifact_id} · v{version}"), ("Engine version", __version__)]

        def make_builder(module=module, artifact=artifact, version=version, rows=rows, kwargs=kwargs):
            def build(content_width: float):
                return module.build_story(
                    artifact=artifact,
                    project_name=meta.name,
                    version=version,
                    provenance_rows=rows,
                    exported_at=report_theme.utc_stamp(),
                    content_width=content_width,
                    **kwargs,
                )

            return build

        entries.append((tool_id, make_builder(), module.build_verdict(artifact)))

    if not entries:
        raise HTTPException(
            status_code=404,
            detail=f"no {phase} tools have been saved in project {project_id!r} yet",
        )

    pdf_bytes = pack_pdf.build_pack(
        phase=phase,
        project_name=meta.name,
        project_id=project_id,
        engine_version=__version__,
        entries=entries,
        missing=missing,
        exported_at=report_theme.utc_stamp(),
    )
    return _pdf_response(pdf_bytes, f"{_safe_filename(meta.name)}-{phase.lower()}-pack.pdf")


def _load_optional(
    store: ProjectStore, meta: ProjectMetadata, project_id: str, tool_id: str, model: Any
) -> tuple[Any, str, int] | None:
    """(validated artifact, its artifact_id, its version) for the project's
    saved TOOL_ID artifact, or None -- no artifact of that tool_id has ever
    been saved, or the one on disk no longer validates against the current
    schema. The second case is deliberately not an error: project_pdf.py's
    generic export already treats one stale artifact as a reason to skip
    it, not a reason to fail an export that covers several (its own
    docstring: "refusing the whole export over it would reproduce the
    exact 'you can't get your work out' failure this route exists to
    fix"). The summary route below calls this four times (T-03/T-15/T-18/
    T-08) plus a separate dataset lookup, any one of which may come back
    empty or stale -- the same stance, just five sources instead of one.
    """
    artifact_id = _find_artifact_id(meta, tool_id)
    if artifact_id is None:
        return None
    try:
        data = store.load_artifact(project_id, artifact_id)
    except FileNotFoundError:
        return None
    try:
        artifact = model.model_validate(data)
    except ValueError:
        return None
    version = meta.artifact_index[artifact_id].latest_version
    return artifact, artifact_id, version


class SummaryRequest(BaseModel):
    """The user's own T-14 chart selection (desktop/src/tools/chartset/
    chartSetViewStore.ts), so TOP CATEGORIES can print a tally over the
    SAME dataset column already on screen -- computed through the
    engine's own compute_pareto, never a column this route would have to
    guess (export/reports/summary.py's module docstring: guessing would
    be the second opinion the "quote, never re-derive" rule forbids).
    `chart` mirrors ReportRequest.chart above: the mounted T-14 Pareto
    picture, optional because the caller may be standing on a screen
    other than T-14, where nothing is mounted to capture. Every field
    optional and the whole body optional (route default None, handled
    there) -- a caller that sends nothing, every caller before this
    feature, gets exactly today's behavior."""

    dataset_id: str | None = None
    column: str | None = None
    chart: ChartCapture | None = None


def _resolve_dataset_pareto(
    store: ProjectStore, project_id: str, dataset_id: str | None, column: str | None
) -> summary_report_mod.DatasetParetoSource | None:
    """The user's own T-14 selection, rerun through the SAME compute_pareto
    the chart itself calls (stats/pareto.py) -- never a second,
    independently-invented tally. None for every "can't" case: no
    selection was sent, the dataset id doesn't resolve on this project,
    the column doesn't exist on that dataset, or the column turns out to
    have no non-blank values left to tally -- each is an honest "nothing
    to show" and none of them may 500 (task rule): an unknown dataset id
    or column degrades to the same "no categories" line an ordinary gap
    prints, it does not break the page a supervisor is trying to leave
    with.
    """
    if not dataset_id or not column:
        return None
    try:
        values, meta = DatasetStore(store).load_category_column(project_id, dataset_id, column)
    except (FileNotFoundError, KeyError):
        return None
    if not values:
        return None
    pareto = compute_pareto(values).value
    return summary_report_mod.DatasetParetoSource(source_filename=meta.source_filename, column=column, pareto=pareto)


def _dataset_pareto_chart(
    body: SummaryRequest, dataset_pareto: summary_report_mod.DatasetParetoSource | None
) -> tuple[bytes | None, str | None]:
    """(chart png to embed, reason it is absent) -- same contract as every
    other report's chart gate (report_pdf.check_chart). The fingerprint is
    the tally's own counts, in the exact order compute_pareto sorted them
    (the same order the bars render in, per charts/Pareto.tsx), which is
    the same shape T-35's _grr_chart_series above fingerprints its bars
    with. Deliberately NOT the category names alongside the counts: a
    category is free text a user typed into a spreadsheet, and mixing it
    into data_fingerprint's ensure_ascii=True JSON would silently diverge
    from the browser's plain JSON.stringify the moment a category held a
    non-ASCII character -- a chart quietly and wrongly refused on a part
    number some engineering as "Ecran" rather than "Écran" is a worse bug
    than the (very old, structural) integrity check this closes. Counts
    alone stay purely numeric, which is exactly the contract
    data_fingerprint/fingerprint() already guarantee to agree on.
    """
    if dataset_pareto is None:
        return None, None
    expected_hash = report_pdf.data_fingerprint([c.count for c in dataset_pareto.pareto.categories])
    return report_pdf.check_chart(
        _decode_png(body.chart), body.chart.data_hash if body.chart else None, expected_hash
    )


@router.post("/project/{project_id}/summary/pdf")
def project_summary_pdf(
    project_id: str, body: SummaryRequest | None = None, store: ProjectStore = Depends(get_store)
) -> Response:
    """The one-page project summary (docs/uat/PLAN.md 2.4): problem/goal,
    baseline, data imported, top categories, fishbone causes, next action
    -- from whatever the project actually has, gaps named rather than
    dropped (export/reports/summary.py's module docstring has the full
    case). The body is OPTIONAL and, unlike the per-tool reports, carries
    no computed value -- only the user's own T-14 dataset+column
    selection and its chart capture (SummaryRequest above), so a caller
    that sends nothing (every caller before this feature) gets exactly
    today's behavior: every input resolved from the project's own saved
    state, the same way the phase pack above resolves its entries.
    """
    try:
        meta = store.load_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    req = body or SummaryRequest()

    charter_hit = _load_optional(store, meta, project_id, "T-03", CharterArtifact)
    fishbone_hit = _load_optional(store, meta, project_id, "T-15", FishboneArtifact)
    matrix_hit = _load_optional(store, meta, project_id, "T-18", SolutionMatrixArtifact)
    check_sheet_hit = _load_optional(store, meta, project_id, "T-08", CheckSheetArtifact)
    datasets = DatasetStore(store).list_datasets(project_id)

    # The check sheet wins when one exists at all -- see
    # export/reports/summary.py's _categories_section docstring for the
    # full reasoning. Resolving (and fingerprint-checking a chart for) a
    # dataset selection that TOP CATEGORIES is about to ignore anyway
    # would just be wasted work on every request that has a check sheet.
    dataset_pareto = None if check_sheet_hit else _resolve_dataset_pareto(store, project_id, req.dataset_id, req.column)
    # The reason half of this pair is unused below on purpose: the chart
    # REPLACES the category table when present (summary.py's
    # _categories_section), so a refused/missing capture has a real
    # fallback already on the page and needs no apologetic placeholder
    # text the way a per-tool report's chart-only zone 2 would.
    chart_png, _chart_unavailable_reason = _dataset_pareto_chart(req, dataset_pareto)

    # ONE line naming everything this page drew from, not one row per
    # artifact. Both ship reviewers named the artifact ids, the SHA-256 and
    # the engine version as tool residue when they were four separate
    # labelled rows -- and at one kv_table row each, they were also the
    # single biggest reason the rich-project measurement
    # (test_project_summary.py) didn't fit on one page. The full detail
    # (every artifact id, every version) already lives in the whole-project
    # export (GET .../export/pdf) for anyone auditing this page; PROVENANCE
    # here only has to let a reader confirm what this specific page is
    # traceable to, in one line, before the export timestamp
    # rt.provenance() appends after it.
    used: list[str] = []
    for tool_id, hit in (("T-03", charter_hit), ("T-15", fishbone_hit), ("T-18", matrix_hit), ("T-08", check_sheet_hit)):
        if hit is not None:
            _, artifact_id, version = hit
            used.append(f"{tool_id} {artifact_id} v{version}")

    drawn_from: list[str] = []
    if used:
        drawn_from.append(", ".join(used))
    if datasets:
        latest_dataset = datasets[-1]
        # "rows"/"row", never "row(s)" -- this string lands in the summary
        # page's own footer, which is written for a manager rather than for
        # the analyst driving the tool (summary.py's _n).
        row_word = "row" if latest_dataset.row_count == 1 else "rows"
        drawn_from.append(
            f"dataset {latest_dataset.dataset_id} ({latest_dataset.row_count:,} {row_word}, sha256 {latest_dataset.sha256[:12]}…)"
        )
    drawn_from.append(f"engine v{__version__}")
    rows: list[tuple[str, str]] = [("Drawn from", " · ".join(drawn_from))]

    def story(content_width: float):
        return summary_report_mod.build_story(
            project_name=meta.name,
            charter=charter_hit[0] if charter_hit else None,
            fishbone=fishbone_hit[0] if fishbone_hit else None,
            solution_matrix=matrix_hit[0] if matrix_hit else None,
            check_sheet=check_sheet_hit[0] if check_sheet_hit else None,
            datasets=datasets,
            dataset_pareto=dataset_pareto,
            chart_png=chart_png,
            provenance_rows=rows,
            exported_at=report_theme.utc_stamp(),
            content_width=content_width,
        )

    pdf_bytes = report_pdf.render(
        story_builder=story,
        title=f"{meta.name} — Project Summary",
        project_id=project_id,
        engine_version=__version__,
    )
    return _pdf_response(pdf_bytes, f"{_safe_filename(meta.name)}-summary.pdf")
