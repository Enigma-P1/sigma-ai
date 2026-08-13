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
from reportlab.pdfbase.pdfmetrics import stringWidth
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
    # The space above is what makes a zone a zone: 12pt above against 3pt
    # below binds the label to the block it introduces rather than letting
    # it float between two of them. 18pt above was tried and is better
    # looking, but a five-zone report has four of these gaps and it cost
    # the Measurement Check report its single page.
    styles["zone_label"] = theme.ParagraphStyle(
        "zone_label",
        parent=styles["label"],
        fontSize=theme.TEXT_XS,
        textColor=theme.TEXT_MUTED,
        spaceBefore=theme.SPACE_4,
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
        Spacer(1, theme.SPACE_3),
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
    engine assigned. Never advice -- see recommendation_block.

    This is the one element on the sheet that has to be legible from the far
    side of a desk, and it was a flat grey box with a 2.5pt coloured edge --
    quieter than the table under it. It is now built the way the app builds
    a status pill, from the same three token values: the tone's soft fill,
    its hairline border, and the full-strength colour on the marker and the
    spine. Nothing is decorative; each of the three says the same thing.

    THE MARKER EARNS ITS COLUMN. Fill, spine and text colour all collapse to
    the same near-grey on a mono printer, so without a glyph a printed
    verdict has no tone at all -- the reader would have to infer it from the
    words, which is exactly the inference this frame exists to remove.
    """
    color = _TONE_COLOR[tone]
    fill, edge = _TONE_FILL[tone]
    headline = styles["headline"]
    # Sized against the marker at headline size rather than guessed: the
    # widest of the four glyphs sets the column, so pass/flag/fail/neutral
    # banners all break their text at the same place.
    mark_w = max(_string_width(m, headline) for m in _TONE_MARK.values()) + 2 * theme.SPACE_3
    text_w = content_width - mark_w - theme.SPACE_4
    headline = _fitted_headline(text, headline, text_w)
    mark = Paragraph(
        _TONE_MARK[tone],
        theme.ParagraphStyle(f"verdict_mark_{tone}", parent=headline, textColor=color),
    )
    para = Paragraph(esc(text), headline)
    table = Table([[mark, para]], colWidths=[mark_w, content_width - mark_w])
    table.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), theme.RULE_STRONG * 3, color),
                ("BOX", (0, 0), (-1, -1), theme.RULE, edge),
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), theme.SPACE_3),
                ("RIGHTPADDING", (0, 0), (0, -1), theme.SPACE_3),
                ("LEFTPADDING", (1, 0), (-1, -1), 0),
                ("RIGHTPADDING", (1, 0), (-1, -1), theme.SPACE_4),
                # Padding is most of what makes this read as the answer
                # rather than as another row: 9pt above and below against
                # the 6pt every table cell gets. 12pt looked better still
                # and is what the A3 sheet could not afford.
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_3),
            ]
        )
    )
    return [table, Spacer(1, theme.SPACE_3)]


def _string_width(text: str, style: Any) -> float:
    return stringWidth(text, style.fontName, style.fontSize)


# A verdict of three lines or more is no longer a headline, it is a
# paragraph, and setting a paragraph at headline size makes it shout
# without making it clearer. The 23 verdicts split cleanly into two
# populations -- "Repeatability 8.94% of study variation — acceptable."
# against T-17's five-line recital of which test was run against which
# split -- so the banner has two sizes, chosen by measuring the text, not
# by guessing at its length. The short ones get the size that reads across
# a desk; the long ones stay at body-heading size and stay a block a
# person can actually read. Both keep the tone, the marker and the fill,
# which is what a reader learns to recognise; only the point size moves.
_HEADLINE_MAX_LINES = 2


def _fitted_headline(text: str, headline: Any, text_width: float) -> Any:
    if text_width <= 0:
        return headline
    probe = Paragraph(esc(text), headline)
    _, height = probe.wrap(text_width, 10_000)
    if height <= _HEADLINE_MAX_LINES * headline.leading + 0.5:
        return headline
    return theme.ParagraphStyle(
        "headline_long",
        parent=headline,
        fontSize=theme.TEXT_MD,
        leading=theme.TEXT_MD * 1.3,
    )


def chart(
    png_bytes: bytes | None,
    *,
    content_width: float,
    styles: dict,
    unavailable_reason: str | None = None,
    max_height: float = MAX_CHART_HEIGHT,
) -> list[Any]:
    """Zone 2's picture, or a stated reason there isn't one.

    A missing chart must never cost the page. Capture can fail for reasons
    the user cannot act on (the tab was never opened, the canvas had not
    painted), and a report that refuses to render over it is a worse
    outcome than a report that says why the picture is absent.

    Aspect ratio is taken from the image itself rather than assumed: the
    charts are 16:9-ish and the Konva canvases are not, and a hardcoded
    height silently distorts one of them.

    `max_height` defaults to MAX_CHART_HEIGHT (a whole report's own zone-2
    budget) but is a parameter, not a constant, because that budget assumes
    the chart IS zone 2 -- true for every per-tool report, false for
    export/reports/summary.py's TOP CATEGORIES, which fits a chart beside
    four other zones on one page and measured its own, smaller cap
    (SUMMARY_CHART_MAX_HEIGHT) the same rendered-and-measured way.
    """
    if not png_bytes:
        reason = unavailable_reason or "Chart not captured — open the tool's screen and export again."
        # A bare italic line where the picture should be reads as an error
        # message that leaked into the document. A dashed frame the width of
        # the chart it replaces reads as what it is: a reserved space, and a
        # stated reason it is empty. Dashes, not a solid rule, because a
        # solid box would look like a chart with nothing plotted in it.
        placeholder = Table([[Paragraph(esc(reason), styles["body_muted"])]], colWidths=[content_width])
        placeholder.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), theme.RULE, theme.BORDER_STRONG, None, (3, 3)),
                    ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                    ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_4),
                ]
            )
        )
        return [placeholder, Spacer(1, theme.SPACE_3)]
    from io import BytesIO

    reader = ImageReader(BytesIO(png_bytes))
    px_w, px_h = reader.getSize()
    height = content_width * (px_h / px_w) if px_w else content_width * 0.5
    # Cap the picture so it cannot push the rest of the report onto a second
    # page. A one-page report that spills is not a one-page report, and the
    # zone most likely to fall off the end is provenance -- the one that
    # answers "where did this number come from". Width shrinks with it so the
    # aspect ratio is preserved rather than squashed.
    if height > max_height:
        content_width = content_width * (max_height / height)
        height = max_height
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
                # Same construction as the verdict banner -- fill, hairline
                # edge, padded -- deliberately in the accent rather than in
                # any tone colour, and deliberately at card-item size rather
                # than headline size. A reader who has learned that the tone
                # colours mean "computed" must not find one wrapped around
                # a suggestion.
                ("BOX", (0, 0), (-1, -1), theme.RULE, theme.ACCENT_BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), theme.ACCENT_SOFT),
                ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_3),
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
        rows.append([Paragraph(_TONE_MARK[tone], _dot_style(tone, styles)), Paragraph(esc(text), styles["card_item"])])
        styling.append(("TEXTCOLOR", (0, index), (0, index), _TONE_COLOR[tone]))
    # Every marker was the same square in four colours, so the whole card
    # was one grey column once printed. Same four tones, four shapes --
    # see _TONE_MARK. The column is measured off the widest of them plus a
    # gutter, rather than the old fixed 18pt that left the triangle and the
    # check sitting at visibly different distances from their text.
    mark_w = max(_string_width(m, styles["card_item"]) for m in _TONE_MARK.values()) + theme.SPACE_3
    table = Table(rows, colWidths=[mark_w, content_width - mark_w])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                # 3pt was one third of the line gap inside a wrapped item, so
                # a two-line item and the item under it ran together. At 4.5pt
                # a row is separated from its neighbour by more than its own
                # lines are separated from each other, which is what makes a
                # list scannable.
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_1 * 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_1 * 1.5),
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
        kv_table(stamped, _provenance_styles(styles), content_width, label_frac=0.3),
    ]


def _provenance_styles(styles: dict) -> dict:
    """Provenance in the same 12pt as the answer made an artifact id look
    like a finding. It is reference matter -- the reader goes to it only
    when they are checking something -- so it takes the table-cell size and
    muted colour, which is the difference between a footnote and a result.
    Overriding a copy of the two styles kv_table reads means the shared
    helper stays generic; it is used by tools where the value IS the
    answer (T-02's total, T-12's repeatability) and must stay full size
    there."""
    quiet = dict(styles)
    quiet["body"] = theme.ParagraphStyle(
        "provenance_value", parent=styles["table_cell"], textColor=theme.TEXT_MUTED
    )
    quiet["label"] = theme.ParagraphStyle(
        "provenance_label", parent=styles["label"], textColor=theme.TEXT_FAINT
    )
    return quiet


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
