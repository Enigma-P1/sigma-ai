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
    and blow past the page margin."""
    label_w = content_width * label_frac
    value_w = content_width - label_w
    data = [[Paragraph(label.upper(), styles["label"]), Paragraph(value, styles["body"])] for label, value in rows]
    table = Table(data, colWidths=[label_w, value_w])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_3),
                ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, theme.BORDER),  # between rows, not after the last
            ]
        )
    )
    return table


def base_table_style(header_rows: int = 1, extra: list[tuple] | None = None) -> TableStyle:
    """The bordered-grid look every real table in the PDF shares (scope,
    team, timeline, risks): soft header background, thin grid, top-aligned
    wrapped cells. `extra` appends per-cell overrides (e.g. risk-level
    text color) on top of this shared base."""
    commands = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), theme.NEUTRAL_SOFT),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, theme.BORDER),
        ("BOX", (0, 0), (-1, -1), 0.75, theme.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
        ("RIGHTPADDING", (0, 0), (-1, -1), theme.SPACE_2),
        ("TOPPADDING", (0, 0), (-1, -1), theme.SPACE_2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), theme.SPACE_2),
    ]
    return TableStyle(commands + list(extra or []))
