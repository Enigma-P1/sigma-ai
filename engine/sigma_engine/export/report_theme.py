"""The shared page frame every one-page tool report is built from.

WHY A SHARED FRAME: the value of a report set is that reading one teaches
you to read all of them. Twenty-three independently-designed pages is
twenty-three things to learn. So the zones, their order, and their styling
live here, and a per-tool module only supplies content.

THE FIVE ZONES, in order down the page (docs/reports-plan.md):

  1. Header       project, tool, date, artifact version
  2. Answer       the chart / table / number -- most of the page
  3. Meaning      one or two plain sentences
  4. Report card  what would invalidate this
  5. Provenance   dataset, n, engine version, export time

Zone 4 is the differentiator and the reason the frame is rigid. Every one
of the 23 tools already computes its own checks (PRESCORE_REGISTRY covers
23/23, each result carrying a status and a plain-English detail); until now
those appeared only on screen. A one-page summary is exactly the format
that manufactures false confidence, and the report card is the guard
against this product doing that.

VERDICT AND RECOMMENDATION ARE DIFFERENT THINGS and the frame keeps them
visually apart. "The means differ" is computed. "Standardise the new
method" is advice. Rendered in one voice, advice reads as a computed fact
-- the exact failure the honesty architecture exists to prevent -- so
`verdict_banner` and `recommendation_block` are separate calls with
separate looks, and no tool module may merge them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, Spacer, Table, TableStyle

from . import pdf_theme as theme
from .charter_pdf_common import esc, kv_table

Tone = Literal["pass", "flag", "fail", "neutral"]

# Roughly 40% of an A4 page's usable height. Chosen by rendering the real
# Capability report: at full width the I-MR chart pushed the provenance zone
# onto page two, which defeats the point of a one-pager.
MAX_CHART_HEIGHT = 260.0

_TONE_COLOR: dict[Tone, Any] = {
    "pass": theme.PASS,
    "flag": theme.FLAG,
    "fail": theme.FAIL,
    "neutral": theme.TEXT_MUTED,
}

# The fill and edge behind each tone, matching the app's status pills.
_TONE_FILL: dict[Tone, tuple[Any, Any]] = {
    "pass": (theme.PASS_SOFT, theme.PASS_BORDER),
    "flag": (theme.FLAG_SOFT, theme.FLAG_BORDER),
    "fail": (theme.FAIL_SOFT, theme.FAIL_BORDER),
    "neutral": (theme.NEUTRAL_SOFT, theme.NEUTRAL_BORDER),
}

# THE TONE IN A SHAPE, NOT ONLY IN A COLOUR. These reports get printed on
# the office mono laser more often than they get read on a screen, and the
# four tone colours reduce to four grey values a reader cannot tell apart
# (PASS #1a7f37 and FLAG #9a6700 land within 4% of each other in
# greyscale). A glyph carries the same distinction with no colour at all,
# and it survives a photocopy, a fax and a colour-blind reader.
#
# All four are drawn by ReportLab's automatic Type1 substitution -- the
# same mechanism the previous single "■" already relied on -- so they add
# no font file and nothing for PyInstaller to ship. Hollow variants (○, □)
# are NOT available through it: they silently fall back to a filled box,
# which is why every mark here is a solid shape.
_TONE_MARK: dict[Tone, str] = {
    "pass": "✓",  # check
    "flag": "▲",  # up triangle -- the caution shape
    "fail": "✕",  # cross
    "neutral": "■",  # square: stated, neither good nor bad
}

# One vocabulary across all 23 reports. A label that means "estimate" on one
# page and "approximate" on the next teaches the reader nothing, and the
# whole point of these labels is that a reader learns them once and then
# trusts them everywhere.
LABELS = {
    "estimate": "ESTIMATE — not measured",
    "pilot_only": "PILOT ONLY — not yet proven at full scale",
    "unstable": "UNSTABLE PROCESS — capability not claimable",
    "msa_unqualified": "MEASUREMENT SYSTEM NOT QUALIFIED — treat the numbers below with caution",
    "insufficient_n": "SAMPLE TOO SMALL — see the report card",
}


def report_styles() -> dict[str, Any]:
    """The charter styles plus the few this frame adds. Built on top rather
    than beside, so a token change moves both documents."""
    styles = theme.build_styles()
    base = styles["body"]
    styles["report_title"] = theme.ParagraphStyle(
        "report_title", parent=styles["title"], fontSize=theme.TEXT_LG, leading=theme.TEXT_LG * 1.15
    )
    # ZONE LABELS ARE THE SPINE OF THE PAGE. At TEXT_FAINT they were the
    # lightest mark on the sheet, so the five zones read as one continuous
    # column of text and the reader had to parse the content to find out
    # where they were. TEXT_MUTED is still visibly subordinate to every
    # heading and every body line, and now actually divides the page.
    # The space above is what makes a zone a zone: SPACE_5 above against
    # SPACE_1 below binds the label to the block it introduces rather than
    # letting it float between two of them.
    styles["zone_label"] = theme.ParagraphStyle(
        "zone_label",
        parent=styles["label"],
        fontSize=theme.TEXT_XS,
        textColor=theme.TEXT_MUTED,
        spaceBefore=theme.SPACE_5,
        spaceAfter=theme.SPACE_1,
    )
    # The verdict. One step up the scale from where it was, which is the
    # smallest move that puts it above the body text it is competing with
    # (it was TEXT_MD, only 15% larger than body, so on a page of prose it
    # did not read as the answer). Leading is tight for a headline: at 1.15
    # a two-line verdict holds together as one statement.
    styles["headline"] = theme.ParagraphStyle(
        "headline",
        parent=base,
        fontName=theme.FONT_BOLD,
        fontSize=theme.TEXT_LG,
        leading=theme.TEXT_LG * 1.15,
    )
    styles["meaning"] = theme.ParagraphStyle(
        "meaning", parent=base, fontSize=theme.TEXT_BASE, leading=theme.TEXT_BASE * 1.5
    )
    styles["card_item"] = theme.ParagraphStyle(
        "card_item", parent=styles["table_cell"], fontSize=theme.TEXT_SM
    )
    return styles


def header(
    *, project_name: str, tool_id: str, tool_title: str, version: int | None, styles: dict, content_width: float
) -> list[Any]:
    """Zone 1."""
    meta = f"{tool_id}  ·  {project_name}"
    if version is not None:
        meta += f"  ·  v{version}"
    return [
        Paragraph(esc(tool_title), styles["report_title"]),
        Paragraph(esc(meta), styles["meta"]),
        Spacer(1, theme.SPACE_2),
        # A masthead rule, not a divider: full strength and RULE_STRONG, so
        # the title block reads as the letterhead of the sheet. Every other
        # rule in the document is lighter than this one, which is what makes
        # the top of the page findable when the sheet is on a desk among
        # others. It was a 0.75pt BORDER line and disappeared into the page.
        _rule(content_width, theme.TEXT, theme.RULE_STRONG),
        Spacer(1, theme.SPACE_4),
    ]


def _rule(width: float, color: Any = None, thickness: float = theme.RULE) -> Table:
    table = Table([[""]], colWidths=[width], rowHeights=[thickness])
    table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), thickness, color or theme.BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def verdict_banner(text: str, tone: Tone, styles: dict, content_width: float) -> list[Any]:
    """Zone 2's headline: the computed answer, stated once, in the tone the
    engine assigned. Never advice -- see recommendation_block."""
    color = _TONE_COLOR[tone]
    para = Paragraph(esc(text), styles["headline"])
    table = Table([[para]], colWidths=[content_width])
    table.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 2.5, color),
                ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("BACKGROUND", (0, 0), (-1, -1), theme.NEUTRAL_SOFT),
            ]
        )
    )
    return [table, Spacer(1, theme.SPACE_3)]


def chart(
    png_bytes: bytes | None, *, content_width: float, styles: dict, unavailable_reason: str | None = None
) -> list[Any]:
    """Zone 2's picture, or a stated reason there isn't one.

    A missing chart must never cost the page. Capture can fail for reasons
    the user cannot act on (the tab was never opened, the canvas had not
    painted), and a report that refuses to render over it is a worse
    outcome than a report that says why the picture is absent.

    Aspect ratio is taken from the image itself rather than assumed: the
    charts are 16:9-ish and the Konva canvases are not, and a hardcoded
    height silently distorts one of them.
    """
    if not png_bytes:
        reason = unavailable_reason or "Chart not captured — open the tool's screen and export again."
        return [Paragraph(esc(reason), styles["body_muted"]), Spacer(1, theme.SPACE_3)]
    from io import BytesIO

    reader = ImageReader(BytesIO(png_bytes))
    px_w, px_h = reader.getSize()
    height = content_width * (px_h / px_w) if px_w else content_width * 0.5
    # Cap the picture so it cannot push the rest of the report onto a second
    # page. A one-page report that spills is not a one-page report, and the
    # zone most likely to fall off the end is provenance -- the one that
    # answers "where did this number come from". Width shrinks with it so the
    # aspect ratio is preserved rather than squashed.
    if height > MAX_CHART_HEIGHT:
        content_width = content_width * (MAX_CHART_HEIGHT / height)
        height = MAX_CHART_HEIGHT
    return [Image(BytesIO(png_bytes), width=content_width, height=height), Spacer(1, theme.SPACE_3)]


def meaning(sentences: str, styles: dict) -> list[Any]:
    """Zone 3. Plain language, and deliberately not a restatement of the
    number already printed above it."""
    return [
        Paragraph("WHAT THIS MEANS", styles["zone_label"]),
        Paragraph(esc(sentences), styles["meaning"]),
    ]


def recommendation_block(text: str, styles: dict, content_width: float) -> list[Any]:
    """Advice, marked as advice. Kept apart from verdict_banner so a reader
    can always tell which sentence the engine computed and which one it is
    suggesting."""
    if not text:
        return []
    para = Paragraph(esc(text), styles["card_item"])
    table = Table([[para]], colWidths=[content_width])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.75, theme.ACCENT_BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), theme.ACCENT_SOFT),
                ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
            ]
        )
    )
    return [
        Paragraph("SUGGESTED NEXT STEP — not a computed result", styles["zone_label"]),
        table,
    ]


def report_card(items: list[tuple[Tone, str]], styles: dict, content_width: float) -> list[Any]:
    """Zone 4: what would invalidate this.

    Takes (tone, text) rows, typically built straight from the tool's own
    prescore results. An empty list still prints the zone with an explicit
    "nothing flagged" line -- a silent absence is indistinguishable from a
    report card that failed to run, and the reader cannot tell which.
    """
    if not items:
        items = [("pass", "No checks flagged on this tool.")]
    rows = []
    styling: list[tuple] = []
    for index, (tone, text) in enumerate(items):
        rows.append([Paragraph("■", _dot_style(tone, styles)), Paragraph(esc(text), styles["card_item"])])
        styling.append(("TEXTCOLOR", (0, index), (0, index), _TONE_COLOR[tone]))
    table = Table(rows, colWidths=[theme.SPACE_5, content_width - theme.SPACE_5])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_1),
                *styling,
            ]
        )
    )
    return [Paragraph("REPORT CARD — what would change this answer", styles["zone_label"]), table]


def _dot_style(tone: Tone, styles: dict) -> Any:
    return theme.ParagraphStyle(f"dot_{tone}", parent=styles["card_item"], textColor=_TONE_COLOR[tone])


def provenance(rows: list[tuple[str, str]], styles: dict, content_width: float, *, exported_at: str | None = None) -> list[Any]:
    """Zone 5: enough to answer "where did this number come from" without
    reaching for the full project record.

    `exported_at` is injected rather than read from the clock here so the
    same inputs render byte-identical output -- the tests and the golden
    harness both depend on that, and a wall-clock read inside the renderer
    would make every PDF differ from the last.
    """
    stamped = list(rows)
    if exported_at:
        stamped.append(("Exported", exported_at))
    return [
        Paragraph("PROVENANCE", styles["zone_label"]),
        kv_table(stamped, styles, content_width, label_frac=0.3),
    ]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def keep(flowables: list[Any]) -> KeepTogether:
    """Group a zone so it does not split mid-way across a page break."""
    return KeepTogether(flowables)


# What a table cell can hold before it stops being a cell. Chosen by
# rendering the real Control Plan: its "how often" field carried a
# 400-character sampling rationale, which turned one row into a full page of
# eight-character-wide columns and pushed the table off page one entirely.
DEFAULT_CELL_CHARS = 90


def clip(text: str, max_chars: int = DEFAULT_CELL_CHARS) -> str:
    """Cut a cell to a length a table can lay out, on a word boundary.

    WHY THIS IS NEEDED AT ALL. These artifacts hold free text with no length
    limit, because the schema is right not to impose one -- the full
    reasoning belongs in the record. But a report table is a fixed grid, and
    ReportLab splits BETWEEN rows and never within one: a cell taller than
    the frame does not wrap onto the next page, it forces a page break and
    then overflows anyway. So the choice is not "clip or print it all", it
    is "clip or wreck the page".

    The pointer matters as much as the cut. A reader who sees "…" needs to
    know the rest exists and where -- the whole-project export carries every
    field at full length, which is what it is for.
    """
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    cut = cleaned[: max_chars - 1]
    if " " in cut[max_chars // 2 :]:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "…"


__all__ = [
    "LABELS",
    "chart",
    "header",
    "keep",
    "meaning",
    "provenance",
    "recommendation_block",
    "report_card",
    "report_styles",
    "utc_stamp",
    "verdict_banner",
]
