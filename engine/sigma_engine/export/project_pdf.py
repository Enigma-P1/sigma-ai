"""Renders an ENTIRE project to one PDF -- every saved artifact, in DMAIC
order, as a document a person can hand to someone.

WHY THIS EXISTS: until now the only thing that left this app as a file was
the T-03 charter. A finished project held 22 other artifacts that existed
only as screens and as .json on disk, so the answer to "I did the work, now
give me the deliverable" was "screenshot it or retype it." The whole product
is a paper trail, and the paper trail could not leave the building.

The charter export already solved the hard parts -- ReportLab with base-14
fonts (no font files to bundle, PLAN §4.5/§7), a theme derived from
tokens.css, escaping, the policy footer. This reuses all of it and adds the
one missing piece: a renderer that needs no per-tool layout code.

Per-tool layout is deliberately NOT what this does. Twenty-three bespoke
section builders would be twenty-three things to keep in sync with
twenty-three evolving schemas, and the ones that drifted would fail silently
by omitting a field -- the worst failure mode for a document whose whole
value is completeness. Instead this walks the artifact's own validated
structure: mappings become label/value rows, lists of mappings become
tables, and anything carrying a `provenance` block is marked engine-computed
rather than typed. A field added to a schema appears here for free; a field
renamed appears under its new name instead of vanishing.

The charter keeps its dedicated hand-laid export (charter_pdf.py): it is the
one artifact whose layout is itself the deliverable, and it is what goes in
front of a sponsor on its own.
"""

from __future__ import annotations

import io
from typing import Any

from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table

from . import pdf_theme as theme
from .charter_pdf_common import base_table_style, esc, fmt_number, kv_table

# tool_id -> (phase, human title). Pinned to registry.ARTIFACT_REGISTRY by
# test_project_pdf.py, so adding a tool to the registry without naming it
# here fails a test instead of silently exporting a section headed "T-26".
TOOL_TITLES: dict[str, tuple[str, str]] = {
    "T-01": ("Intake", "Project Picker"),
    "T-02": ("Define", "COPQ / Benefit Case"),
    "T-03": ("Define", "Project Charter"),
    "T-04": ("Define", "SIPOC"),
    "T-05": ("Define", "VoC to CTQ Tree"),
    "T-06": ("Measure", "Process Map"),
    "T-07": ("Measure", "Spaghetti Diagram"),
    "T-08": ("Measure", "Check Sheet"),
    "T-09": ("Measure", "Time Study"),
    "T-10": ("Measure", "Yield Calculator"),
    "T-11": ("Measure", "Data Collection Plan"),
    "T-12": ("Measure", "Measurement Check (MSA)"),
    "T-15": ("Analyze", "Fishbone + 5 Whys"),
    "T-16": ("Analyze", "FMEA"),
    "T-17": ("Analyze", "Hypothesis Test"),
    "T-18": ("Improve", "Solution Selection Matrix"),
    "T-19": ("Improve", "Pilot Plan"),
    "T-20": ("Improve", "Before / After Proof"),
    "T-21": ("Control", "Control Chart"),
    "T-22": ("Control", "Control Plan"),
    "T-23": ("Control", "5S Audit"),
    "T-24": ("Control", "Standard Work"),
    "T-25": ("Wrap", "A3 Final Report"),
}

PHASE_ORDER = ("Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap")

# Bookkeeping the reader did not write and cannot act on. Artifact id, tool
# id and version already appear in the section header and page footer, so
# repeating them as body rows is noise; hashes and canvas coordinates are
# machine state, not content.
SKIP_KEYS = frozenset(
    {
        "artifact_id",
        "tool_id",
        "schema_version",
        "created_at",
        "updated_at",
        "input_hash",
        "dataset_sha256",
        "layout",
        "engine_version",
    }
)

# Raw sample vectors -- a baseline's 120 readings, a control chart's series.
# Printing them costs pages and tells a reader nothing actionable; the count
# does. The numbers remain in the project .json and the CSV exports.
BULK_KEYS = frozenset({"values", "data", "observations", "series", "paired_before", "paired_after"})

# Beyond this many columns an A4 table stops being readable, so the list is
# rendered as one labelled block per item instead. This is exactly the
# failure the on-screen FMEA has (fixed-width columns clipping every cell,
# docs/field-notes.md) and it is not worth reproducing on paper.
MAX_TABLE_COLUMNS = 6

# A table row splits between rows but never WITHIN one, so a single cell
# taller than the frame is an unrecoverable LayoutError -- ReportLab raises
# rather than overflowing. The A3's narrative panels hit exactly this: four
# columns, one cell ~2000pt tall against a ~710pt frame, and the whole
# export died on page 127. Long prose therefore never goes in a table; it
# becomes labelled blocks, where each Paragraph splits across pages on its
# own. Sized generously -- this is a "does it fit in a cell" bound, not a
# style rule.
MAX_CELL_CHARS = 180

MAX_NESTING = 4  # deeper than this, emit a compact summary rather than recurse


def label_for(key: str) -> str:
    """`charter_baseline_value` -> `Charter baseline value`. Field names are
    the only labels available -- the schemas carry no display names -- so
    they are de-snaked rather than mapped, which keeps a renamed field
    readable instead of silently unlabelled."""
    return key.replace("_", " ").strip().capitalize()


def is_computed(value: Any) -> bool:
    """`{"value": ..., "provenance": {...}}` is the engine's mark for "this
    was derived, not typed" -- the distinction the whole product rests on,
    so it survives into the export instead of being flattened away."""
    return isinstance(value, dict) and "value" in value and "provenance" in value


def is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def fmt_scalar(value: Any) -> str:
    if value is None:
        return "--"
    if isinstance(value, bool):  # before the numeric branch: bool IS an int
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return fmt_number(value)
    return str(value)


def _is_scalar(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def _para(text: str, style: Any) -> Paragraph:
    return Paragraph(esc(text), style)


def _bulk_summary(value: list[Any]) -> str:
    return f"{len(value)} values (kept in the project data, not printed)"


def _long_text_block(label: str, text: str, styles: dict) -> list[Any]:
    """A label above free-flowing prose. Used instead of a table row
    whenever the text is long: a Paragraph splits across pages by itself,
    while a table cell cannot split at all (MAX_CELL_CHARS)."""
    return [_para(label, styles["label"]), _para(text, styles["body"]), Spacer(1, theme.SPACE_2)]


def _dict_table(rows: list[tuple[str, Any]], styles: dict, width: float) -> list[Any]:
    """Scalar fields of one mapping. Short values share a label/value table
    (reusing the charter export's kv_table, so both exports set rows the
    same way); long ones are lifted out into prose blocks first.

    Splitting them is not cosmetic. kv_table builds a table like any other,
    so one 5,000-character narrative field makes a single row taller than
    the page frame and ReportLab raises LayoutError -- the same crash the
    A3's panels caused, reached through the scalar path instead of the
    list-of-mappings path."""
    short: list[tuple[str, str]] = []
    blocks: list[Any] = []
    for key, value in rows:
        text = fmt_scalar(value)
        if len(text) > MAX_CELL_CHARS:
            blocks += _long_text_block(label_for(key), text, styles)
        else:
            short.append((label_for(key), text))
    out: list[Any] = []
    if short:
        out.append(kv_table(short, styles, width))
    return out + blocks


def _rows_table(items: list[dict], styles: dict, width: float) -> Table:
    """A list of same-shaped mappings as a real table. Columns are the union
    of keys in first-seen order, dropping any that are empty in every row --
    printing a column of dashes wastes the width the populated columns
    need."""
    cols: list[str] = []
    for item in items:
        for key in item:
            if key not in cols and key not in SKIP_KEYS and key not in BULK_KEYS:
                cols.append(key)
    cols = [c for c in cols if any(not is_empty(item.get(c)) for item in items)]

    header = [_para(label_for(c), styles["table_header"]) for c in cols]
    body = [
        [_para(_cell_text(item.get(c)), styles["table_cell"]) for c in cols]
        for item in items
    ]
    col_width = width / max(len(cols), 1)
    table = Table([header, *body], colWidths=[col_width] * len(cols), repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def _cell_text(value: Any) -> str:
    """One table cell. Nested structure inside a cell gets flattened rather
    than dropped -- a cell that silently loses its contents is the exact
    failure this renderer exists to avoid."""
    if is_computed(value):
        return _cell_text(value["value"])
    if is_empty(value):
        return "--"
    if _is_scalar(value):
        return fmt_scalar(value)
    if isinstance(value, list):
        return "; ".join(_cell_text(v) for v in value)
    return "; ".join(f"{label_for(k)}: {_cell_text(v)}" for k, v in value.items() if k not in SKIP_KEYS and not is_empty(v))


def render_value(key: str, value: Any, styles: dict, width: float, depth: int = 0) -> list[Any]:
    """The generic walker. Returns flowables for one field, choosing a shape
    from the data rather than from a per-tool template."""
    if is_empty(value):
        return []

    if is_computed(value):
        # Keep the derivation visible: the method string is the engine's own
        # record of HOW a number was reached, and it is the difference
        # between a report and an assertion.
        inner = render_value(key, value["value"], styles, width, depth)
        method = (value.get("provenance") or {}).get("method") or ""
        if method:
            inner.append(_para(f"Engine-computed — {method}", styles["body_muted"]))
        else:
            inner.append(_para("Engine-computed", styles["body_muted"]))
        return inner

    if key in BULK_KEYS and isinstance(value, list):
        return [_para(f"{label_for(key)}: {_bulk_summary(value)}", styles["body_muted"])]

    if _is_scalar(value):
        return _dict_table([(key, value)], styles, width)

    if isinstance(value, list):
        if all(isinstance(v, dict) for v in value):
            if can_tabulate(value):
                return [_para(label_for(key), styles["label"]), _rows_table(value, styles, width)]
            # Too wide to tabulate: one labelled block per item, so nothing
            # gets clipped to fit a column.
            out: list[Any] = [_para(label_for(key), styles["label"])]
            for index, item in enumerate(value, start=1):
                out.append(_para(f"{label_for(key)} {index}", styles["body_muted"]))
                out += render_mapping(item, styles, width - theme.SPACE_4, depth + 1)
                out.append(Spacer(1, theme.SPACE_2))
            return out
        if all(_is_scalar(v) for v in value):
            joined = "; ".join(fmt_scalar(v) for v in value)
            # Through _dict_table, not kv_table directly: a long list of
            # strings joins into exactly the oversized cell MAX_CELL_CHARS
            # exists to prevent.
            return _dict_table([(key, joined)], styles, width)
        out = [_para(label_for(key), styles["label"])]
        for item in value:
            out += render_value(key, item, styles, width, depth + 1)
        return out

    # mapping
    if depth >= MAX_NESTING:
        return _dict_table([(key, _cell_text(value))], styles, width)
    return [_para(label_for(key), styles["label"]), *render_mapping(value, styles, width, depth + 1)]


def can_tabulate(items: list[dict]) -> bool:
    """A list of mappings is safe to render as a table only if it is narrow
    enough to read AND every cell is short enough to fit in one. See
    MAX_CELL_CHARS: a cell taller than the page frame is a hard LayoutError,
    not a cosmetic overflow, so this is a correctness guard rather than a
    preference."""
    if len(_union_keys(items)) > MAX_TABLE_COLUMNS:
        return False
    return all(
        len(_cell_text(item.get(key))) <= MAX_CELL_CHARS
        for item in items
        for key in _union_keys(items)
    )


def _union_keys(items: list[dict]) -> list[str]:
    keys: list[str] = []
    for item in items:
        for key in item:
            if key not in keys and key not in SKIP_KEYS and key not in BULK_KEYS:
                keys.append(key)
    return keys


def render_mapping(data: dict, styles: dict, width: float, depth: int = 0) -> list[Any]:
    """One mapping. Scalars are gathered into a single label/value table
    first so a document does not open with twenty one-row tables; the
    structured fields follow in their original order."""
    scalars: list[tuple[str, Any]] = []
    structured: list[tuple[str, Any]] = []
    for key, value in data.items():
        if key in SKIP_KEYS or is_empty(value):
            continue
        if key in BULK_KEYS or is_computed(value) or not _is_scalar(value):
            structured.append((key, value))
        else:
            scalars.append((key, value))

    out: list[Any] = []
    if scalars:
        out += _dict_table(scalars, styles, width)
    for key, value in structured:
        out += render_value(key, value, styles, width, depth)
        out.append(Spacer(1, theme.SPACE_2))
    return out


def build_cover(project_name: str, project_id: str, sections: list[tuple[str, str, str, int]], styles: dict, width: float) -> list[Any]:
    """Title block plus a contents list. The contents list is the honest
    inventory: it names every tool that IS in the project, so a reader can
    see at a glance what the project covered and -- by absence -- what it
    did not."""
    story: list[Any] = [
        _para(project_name, styles["title"]),
        Spacer(1, theme.SPACE_2),
        _para("Full project record — every saved tool, in DMAIC order", styles["subtitle"]),
        Spacer(1, theme.SPACE_4),
        kv_table(
            [
                ("Project id", project_id),
                ("Tools saved", str(len(sections))),
                ("Phases covered", ", ".join(dict.fromkeys(phase for phase, _, _, _ in sections))),
            ],
            styles,
            width,
        ),
        Spacer(1, theme.SPACE_5),
        _para("Contents", styles["heading"]),
    ]
    rows = [(f"{tool_id}  {title}", phase) for phase, tool_id, title, _ in sections]
    story.append(kv_table(rows, styles, width, label_frac=0.62))
    return story


def build_tool_section(tool_id: str, title: str, phase: str, data: dict, version: int, styles: dict, width: float) -> list[Any]:
    heading = f"{tool_id}  ·  {title}"
    meta = f"{phase}  ·  v{version}"
    # KeepTogether on the header alone (not the whole section): a long
    # artifact must be free to flow across pages, but a heading stranded at
    # the foot of a page with its content overleaf reads as a missing
    # section.
    story: list[Any] = [
        KeepTogether([_para(heading, styles["heading"]), _para(meta, styles["meta"])]),
        Spacer(1, theme.SPACE_2),
    ]
    story += render_mapping(data, styles, width)
    return story


def build_project_story(
    project_name: str,
    project_id: str,
    artifacts: list[tuple[str, dict, int]],
    content_width: float,
) -> list[Any]:
    """The ordered body content -- everything except the per-page footer. A
    plain function of its inputs (no I/O, no wall clock), so tests can walk
    the flowables and assert on their text without generating a PDF."""
    styles = theme.build_styles()
    known = [(tool_id, data, version) for tool_id, data, version in artifacts if tool_id in TOOL_TITLES]
    known.sort(key=lambda row: (PHASE_ORDER.index(TOOL_TITLES[row[0]][0]), row[0]))

    sections = [(TOOL_TITLES[t][0], t, TOOL_TITLES[t][1], v) for t, _, v in known]
    story = build_cover(project_name, project_id, sections, styles, content_width)

    seen_phase: str | None = None
    for tool_id, data, version in known:
        phase, title = TOOL_TITLES[tool_id]
        story.append(PageBreak())
        if phase != seen_phase:
            story.append(_para(phase.upper(), styles["callout"]))
            story.append(Spacer(1, theme.SPACE_2))
            seen_phase = phase
        story += build_tool_section(tool_id, title, phase, data, version, styles, content_width)
    return story


def _draw_footer(canvas_obj: Any, doc: SimpleDocTemplate, *, project_id: str, engine_version: str) -> None:
    styles = theme.build_styles()
    meta_line = f"{project_id}  ·  engine v{engine_version}  ·  page {canvas_obj.getPageNumber()}"

    canvas_obj.saveState()
    canvas_obj.setStrokeColor(theme.BORDER)
    canvas_obj.setLineWidth(0.75)
    rule_y = theme.MARGIN_BOTTOM - 4
    canvas_obj.line(theme.MARGIN_LEFT, rule_y, theme.MARGIN_LEFT + doc.width, rule_y)

    meta_para = Paragraph(esc(meta_line), styles["footer_meta"])
    _, meta_h = meta_para.wrap(doc.width, rule_y)
    y = rule_y - meta_h - 2
    meta_para.drawOn(canvas_obj, theme.MARGIN_LEFT, y)

    policy_para = Paragraph(theme.FOOTER_POLICY_SENTENCE, styles["footer_policy"])
    _, policy_h = policy_para.wrap(doc.width, y)
    y -= policy_h
    policy_para.drawOn(canvas_obj, theme.MARGIN_LEFT, y)
    canvas_obj.restoreState()


def render_project_pdf(
    *,
    project_name: str,
    project_id: str,
    artifacts: list[tuple[str, dict, int]],
    engine_version: str,
) -> bytes:
    """Build the whole-project PDF and return its bytes.

    `artifacts` is (tool_id, artifact dict, version). Dicts rather than
    validated models on purpose: an export must still produce the other 22
    tools when one artifact fails to validate against a schema that has
    moved on -- refusing to export a whole project because one field drifted
    would be the same "you can't get your work out" failure in a new costume.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=theme.PAGE_SIZE,
        topMargin=theme.MARGIN_TOP,
        bottomMargin=theme.MARGIN_BOTTOM,
        leftMargin=theme.MARGIN_LEFT,
        rightMargin=theme.MARGIN_RIGHT,
        title=f"{project_name} — full project record",
        author="Sigma AI",
        # Compressed here, unlike the charter: a full project runs to dozens
        # of pages and this is emailed, not grepped.
        pageCompression=1,
    )
    story = build_project_story(project_name, project_id, artifacts, doc.width)

    def _footer(canvas_obj: Any, doc_: SimpleDocTemplate) -> None:
        _draw_footer(canvas_obj, doc_, project_id=project_id, engine_version=engine_version)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


__all__ = ["TOOL_TITLES", "build_project_story", "render_project_pdf"]
