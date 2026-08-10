"""Renders a single tool report to PDF bytes.

Holds the two things every report shares and no report should re-implement:
the page setup (size, margins, footer) and the chart-image gate.

THE CHART GATE. Images arrive from the browser, because the app's charts are
Plotly and Konva and the engine cannot draw them. That buys fidelity -- the
printed chart is by construction the one the user was looking at -- and it
costs a risk: a stale image can be attached to fresh numbers, putting a
picture and a verdict that disagree on the same page, over a footer that
says the engine produced it.

So every image is submitted with the hash of the data it was drawn from,
and `check_chart` compares that against a hash of the data actually being
rendered. A mismatch is refused, never quietly used. The report still
prints -- with the chart area replaced by a stated reason -- because a
missing picture is a far smaller harm than a wrong one, and refusing the
whole export would recreate the "you can't get your work out" problem this
feature exists to solve.
"""

from __future__ import annotations

import hashlib
import io
import json
from typing import Any, Sequence

from reportlab.platypus import Paragraph, SimpleDocTemplate

from . import pdf_theme as theme
from . import report_theme as rt


def data_fingerprint(values: Sequence[Any]) -> str:
    """The hash both sides compute over the data behind a chart.

    Deliberately over the VALUES, not over the rendered image or the
    request body: the client and the engine only agree about the data, and
    anything else would drift on formatting differences alone. Floats are
    normalised through JSON's repr so 5.0 and 5 hash alike, matching what
    the browser will have serialised.
    """
    # Whole floats are emitted as integers so this agrees with JavaScript.
    # json.dumps(5.0) is "5.0"; JSON.stringify(5.0) is "5". Left alone, every
    # dataset containing a round number fails the check for a formatting
    # difference no human could see, and the chart silently disappears from
    # the report. Non-whole floats already agree: both languages use the
    # shortest round-tripping representation.
    normalised = [
        int(v) if isinstance(v, float) and v.is_integer() else v
        for v in values
    ]
    payload = json.dumps(normalised, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ChartRejected(Exception):
    """Raised only where it is caught and turned into a printed reason."""


def check_chart(png_bytes: bytes | None, claimed_hash: str | None, expected_hash: str | None) -> tuple[bytes | None, str | None]:
    """Returns (image_to_use, reason_it_is_absent).

    No hash expected (a report whose picture has no single underlying
    series) means the image is taken on trust -- there is nothing to check
    it against, and pretending otherwise would be theatre.
    """
    if png_bytes is None:
        return None, "Chart not captured — open this tool's screen, then export again."
    if expected_hash is None:
        return png_bytes, None
    if claimed_hash != expected_hash:
        return (
            None,
            "Chart was not used: it was drawn from different data than this report. "
            "Reopen the tool's screen so the chart matches, then export again.",
        )
    return png_bytes, None


def _footer(canvas_obj: Any, doc: SimpleDocTemplate, *, project_id: str, engine_version: str) -> None:
    styles = rt.report_styles()
    line = f"{project_id}  ·  engine v{engine_version}  ·  page {canvas_obj.getPageNumber()}"
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(theme.BORDER)
    canvas_obj.setLineWidth(0.75)
    rule_y = theme.MARGIN_BOTTOM - 4
    canvas_obj.line(theme.MARGIN_LEFT, rule_y, theme.MARGIN_LEFT + doc.width, rule_y)

    meta = Paragraph(line, styles["footer_meta"])
    _, meta_h = meta.wrap(doc.width, rule_y)
    y = rule_y - meta_h - 2
    meta.drawOn(canvas_obj, theme.MARGIN_LEFT, y)

    policy = Paragraph(theme.FOOTER_POLICY_SENTENCE, styles["footer_policy"])
    _, policy_h = policy.wrap(doc.width, y)
    policy.drawOn(canvas_obj, theme.MARGIN_LEFT, y - policy_h)
    canvas_obj.restoreState()


def content_width_for(page_size: tuple[float, float]) -> float:
    return page_size[0] - theme.MARGIN_LEFT - theme.MARGIN_RIGHT


def render(
    *,
    story_builder,
    title: str,
    project_id: str,
    engine_version: str,
    page_size: tuple[float, float] | None = None,
) -> bytes:
    """`story_builder(content_width)` returns the flowables. Passing a
    callable rather than a built story means the per-tool module never has
    to know the page geometry it is being rendered into -- which is what
    lets the FMEA report go landscape without every other report caring."""
    size = page_size or theme.PAGE_SIZE
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=size,
        topMargin=theme.MARGIN_TOP,
        bottomMargin=theme.MARGIN_BOTTOM,
        leftMargin=theme.MARGIN_LEFT,
        rightMargin=theme.MARGIN_RIGHT,
        title=title,
        author="Sigma AI",
        pageCompression=1,
    )

    def footer(canvas_obj: Any, doc_: SimpleDocTemplate) -> None:
        _footer(canvas_obj, doc_, project_id=project_id, engine_version=engine_version)

    doc.build(story_builder(doc.width), onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
