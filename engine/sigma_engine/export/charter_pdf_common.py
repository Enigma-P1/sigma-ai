"""Formatting and table helpers shared by charter_pdf_sections.py and
charter_pdf_tables.py -- kept in one place so the two section files don't
grow two slightly-different copies of the same "label: value" row or table
border style.
"""

from __future__ import annotations

from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from . import pdf_theme as theme


def esc(text: str) -> str:
    """Escape free-text user input before it reaches a Paragraph, whose
    body is parsed as a small XML dialect. An unescaped '&', '<', or '>'
    doesn't always raise -- '&' silently mangles the text (observed:
    "R&D" renders as "R&D;") -- so every user-authored artifact field goes
    through this before Paragraph() ever sees it. Static strings this
    module writes itself (headings, connectors) don't need it."""
    return _xml_escape(str(text))


def fmt_date(value: str) -> str:
    """ISO8601 date or datetime -> "Aug 21, 2026". Falls back to the raw
    string on a format this doesn't recognize rather than raising --
    schema validation already guarantees parseability for every date field
    this renders, so the fallback is a belt-and-braces, not a load-bearing
    path. Built field-by-field (not strftime's "%-d") because the
    no-leading-zero-day flag is a glibc extension: it raises on Windows'
    strftime, and the PDF export has to run clean on the same Windows box
    the packaging gate tests (PLAN §7)."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return f"{dt.strftime('%b')} {dt.day}, {dt.year}"


def fmt_number(n: float) -> str:
    """8.4 stays "8.4"; 5.0 becomes "5"; 16084 becomes "16,084" -- these
    are magnitudes and dollar amounts a reader compares at a glance, not
    values needing fixed decimal places."""
    if float(n).is_integer():
        return f"{int(n):,}"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def kv_table(rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle], content_width: float, label_frac: float = 0.24) -> Table:
    """A borderless "LABEL: value" table -- the paper equivalent of the
    app's Field component (design/components/Field.tsx). Explicit column
    widths (not colWidths=None) because the value column holds wrapping
    Paragraphs; an unconstrained column would size to one un-wrapped line
    and blow past the page margin.

    THE TWO COLUMNS SIT ON ONE BASELINE. ReportLab draws a top-aligned
    paragraph's first baseline exactly `fontSize` below the top of the cell
    (paragraph.py: `cur_y = self.height - f.fontSize`), so an 8.6pt label
    beside a 12pt value floated 3.4pt above the word it labels -- on every
    row of every report that uses this. The label column is padded down by
    that difference instead, which is a geometry correction, not a spacing
    choice: it is exactly the two font sizes subtracted.
    """
    label_w = content_width * label_frac
    value_w = content_width - label_w
    value_style = styles["body"]
    label_style = styles["label"]
    baseline_offset = max(0.0, value_style.fontSize - label_style.fontSize)
    data = [[Paragraph(label.upper(), label_style), Paragraph(value, value_style)] for label, value in rows]
    table = Table(data, colWidths=[label_w, value_w])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                # Even padding above and below: the old 3pt/6pt split was
                # compensating for the baseline drift corrected just below,
                # and read as rows sagging away from their labels.
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("TOPPADDING", (0, 0), (0, -1), theme.SPACE_2 + baseline_offset),
                # Between rows, not after the last -- a trailing rule reads as
                # a table edge and this is a list of fields, not a table.
                ("LINEBELOW", (0, 0), (-1, -2), theme.HAIRLINE, theme.BORDER),
            ]
        )
    )
    return table


def base_table_style(header_rows: int = 1, extra: list[tuple] | None = None) -> TableStyle:
    """The bordered-grid look every real table in the PDF shares (scope,
    team, timeline, risks): a ruled header, a hairline grid, top-aligned
    wrapped cells. `extra` appends per-cell overrides (e.g. risk-level
    text color) on top of this shared base.

    THE HEADER IS RULED, NOT FILLED. A grey fill was doing the same job the
    bold dark header type already does, and it cost more than it looked: it
    is the heaviest mark on the page, so on a table of six columns of prose
    the eye landed on the header band instead of on the first row of data.
    A single RULE_STRONG line under the header separates the two just as
    clearly and leaves the type as the only thing with weight. It also
    stops mis-declaring a header where there isn't one -- a caller passing
    the default header_rows=1 for a grid of equal panels (the A3 sheet) got
    its whole top row shaded for no reason, and a rule there reads as one
    more grid line rather than as a mistake.

    Grid lines are HAIRLINE rather than 0.5pt for the same reason: at 0.5pt
    a nine-column FMEA is a page of lines with text between them. The grid
    only has to be findable, not visible.
    """
    commands = [
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), theme.RULE_STRONG, theme.TEXT_MUTED),
        ("INNERGRID", (0, 0), (-1, -1), theme.HAIRLINE, theme.BORDER),
        ("BOX", (0, 0), (-1, -1), theme.RULE, theme.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        # Cells were 6pt on all four sides, which reads as cramped once the
        # text inside wraps: the gutter between two columns of wrapped prose
        # was 12pt while the line gap inside a cell was 15.5pt, so columns
        # ran together vertically. 9pt horizontal opens the gutter past the
        # line gap; 6pt vertical is left alone because every landscape
        # report is height-budgeted and rows are the thing there is least
        # room for.
        ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
        ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
        ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
        # The rule belongs to the header, so the header keeps its words tight
        # against it (3pt) and the 6pt below the rule belongs to the first
        # data row. Indices stay inside the header block on purpose: a
        # single-row table (the charter's process-owner band) is styled with
        # this same default, and a command addressing row header_rows would
        # be off the end of it.
        ("BOTTOMPADDING", (0, header_rows - 1), (-1, header_rows - 1), theme.SPACE_1),
    ]
    return TableStyle(commands + list(extra or []))
