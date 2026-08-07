"""Renders a validated CharterArtifact (T-03) to a one-to-two-page PDF via
ReportLab platypus (PLAN §4.5 / §8 M1: "PDF export for one artifact").

`build_charter_story()` is exposed separately from `render_charter_pdf()`
so tests can walk the built flowables and extract their text directly --
no pypdf dependency needed to prove the right content made it in (M1
export brief). The per-page footer is canvas-drawn chrome, not a flowable
in that story (ReportLab's standard way to repeat content on every page,
via SimpleDocTemplate's onFirstPage/onLaterPages hooks); `footer_text()`
is its own pure function for the same reason -- tests assert its output
directly instead of scraping canvas draw calls.
"""

from __future__ import annotations

import io
from typing import Any

from reportlab.platypus import Paragraph, SimpleDocTemplate

from ..artifacts.charter import CharterArtifact
from . import pdf_theme as theme
from .charter_pdf_sections import build_business_impact, build_goal, build_problem_statement, build_title_block
from .charter_pdf_tables import build_risks, build_scope, build_team, build_timeline


def build_charter_story(artifact: CharterArtifact, *, project_name: str, version: int, content_width: float) -> list[Any]:
    """The ordered body content -- everything except the per-page footer.
    A plain function of its inputs (no I/O, no wall clock) so it's cheap
    to call from tests as many times as needed."""
    styles = theme.build_styles()
    story: list[Any] = []
    story += build_title_block(artifact, project_name, version, styles)
    story += build_problem_statement(artifact.problem_statement, styles, content_width)
    story += build_goal(artifact.goal, styles, content_width)
    story += build_scope(artifact.scope, styles, content_width)
    story += build_team(artifact.team, artifact.process_owner, styles, content_width)
    story += build_timeline(artifact.timeline, styles, content_width)
    story += build_business_impact(artifact.business_impact, styles, content_width)
    story += build_risks(artifact.risks, styles, content_width)
    return story


def footer_text(artifact_id: str, version: int, schema_version: int, engine_version: str) -> tuple[str, str]:
    """The two lines drawn in the page footer of every page: artifact id +
    version + schema version + engine version on one line, the PLAN §1
    non-certification policy sentence on the next (M1 export brief)."""
    meta = f"{artifact_id}  ·  v{version}  ·  schema v{schema_version}  ·  engine v{engine_version}"
    return meta, theme.FOOTER_POLICY_SENTENCE


def _draw_footer(canvas_obj: Any, doc: SimpleDocTemplate, *, artifact_id: str, version: int, schema_version: int, engine_version: str) -> None:
    styles = theme.build_styles()
    meta_line, policy_line = footer_text(artifact_id, version, schema_version, engine_version)

    canvas_obj.saveState()
    canvas_obj.setStrokeColor(theme.BORDER)
    canvas_obj.setLineWidth(0.75)
    rule_y = theme.MARGIN_BOTTOM - 4
    canvas_obj.line(theme.MARGIN_LEFT, rule_y, theme.MARGIN_LEFT + doc.width, rule_y)

    meta_para = Paragraph(meta_line, styles["footer_meta"])
    _, meta_h = meta_para.wrap(doc.width, rule_y)
    y = rule_y - meta_h - 2
    meta_para.drawOn(canvas_obj, theme.MARGIN_LEFT, y)

    policy_para = Paragraph(policy_line, styles["footer_policy"])
    _, policy_h = policy_para.wrap(doc.width, y)
    y -= policy_h
    policy_para.drawOn(canvas_obj, theme.MARGIN_LEFT, y)
    canvas_obj.restoreState()


def render_charter_pdf(artifact: CharterArtifact, *, project_name: str, version: int, engine_version: str) -> bytes:
    """Build the full PDF for one charter version and return its bytes.
    Platypus flows onto a second page automatically if the content
    overruns the first -- no manual page-break logic needed for the
    one-to-two-page budget (M1 export brief)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=theme.PAGE_SIZE,
        topMargin=theme.MARGIN_TOP,
        bottomMargin=theme.MARGIN_BOTTOM,
        leftMargin=theme.MARGIN_LEFT,
        rightMargin=theme.MARGIN_RIGHT,
        title=f"{project_name} — Project Charter v{version}",
        author="Sigma AI",
        # Uncompressed content streams: this is a short, occasionally-
        # downloaded working document, not a hot-path asset, and plain-text
        # streams mean the exact charter text is grep-able straight out of
        # the .pdf bytes -- one less "trust me" between what was rendered
        # and what a reviewer can independently see (the same reproducible-
        # output spirit as provenance.py, PLAN §4.5).
        pageCompression=0,
    )
    story = build_charter_story(artifact, project_name=project_name, version=version, content_width=doc.width)

    def _footer(canvas_obj: Any, doc_: SimpleDocTemplate) -> None:
        _draw_footer(
            canvas_obj,
            doc_,
            artifact_id=artifact.artifact_id,
            version=version,
            schema_version=artifact.schema_version,
            engine_version=engine_version,
        )

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
