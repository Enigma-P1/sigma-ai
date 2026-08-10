"""T-16 FMEA Report — the dense-table case.

This is in Phase 1 alongside Capability on purpose. Capability proves the
report frame can carry an image; it proves nothing about the class of
report where the content IS a wide table, which is where layout actually
breaks. Landscape, column priority, wrapping, pagination and repeated
headers all get exercised here or nowhere.

It also fixes a real defect rather than only exporting one. The on-screen
FMEA lays its row out as a fixed grid sized around the narrow
severity/occurrence/detection selects, so every free-text column clips
mid-word -- `Steam wa`, `Barista sca`, `Grind setti` (docs/field-notes.md).
Nine complete rows, none of them readable. On paper the same mistake is
available and worse, because there is no hover and no scroll to recover
the tail. So the text columns here get the width and the rating columns
get what is left, which is the inverse of the screen and the correct way
round: a reader needs to know what the failure IS before the number means
anything.

Rows print in the artifact's own `sorted_view` order -- severity first,
then RPN -- because equal RPNs are not equal risks, and a severity-10
failure buried below a higher-RPN nuisance is exactly the misread the
sort exists to prevent.
"""

from __future__ import annotations

from typing import Any

from reportlab.lib.pagesizes import landscape
from reportlab.platypus import Paragraph, Table

from ...artifacts.fmea import FmeaArtifact, FmeaRow
from .. import pdf_theme as theme
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc

TOOL_ID = "T-16"
TOOL_TITLE = "FMEA — failure modes, ranked"
PAGE_SIZE = landscape(theme.PAGE_SIZE)

# Fractions of the content width. Text gets 74% between three columns and
# the six numeric/short columns share the rest -- the reverse of the screen
# layout, and the whole point of this module's existence.
COLUMNS: list[tuple[str, str, float]] = [
    ("step_name", "Step", 0.13),
    ("failure_mode", "Failure mode", 0.20),
    ("effect", "Effect", 0.19),
    ("cause", "Cause", 0.19),
    ("severity", "S", 0.03),
    ("occurrence", "O", 0.03),
    ("detection", "D", 0.03),
    ("rpn", "RPN", 0.045),
    ("action", "Action", 0.135),
]


def _ordered_rows(artifact: FmeaArtifact) -> list[FmeaRow]:
    """Severity-first order as the engine computed it. Falls back to the
    stored order if the computed view is absent rather than inventing a
    second sort -- two orderings of the same table is how a report starts
    disagreeing with the screen."""
    by_id = {row.row_id: row for row in artifact.rows}
    view = artifact.sorted_view.value if artifact.sorted_view else None
    if not view:
        return list(artifact.rows)
    ordered = [by_id[row_id] for row_id in view if row_id in by_id]
    ordered += [row for row in artifact.rows if row.row_id not in set(view)]
    return ordered


def build_verdict(artifact: FmeaArtifact) -> tuple[str, rt.Tone]:
    rows = artifact.rows
    if not rows:
        return ("No failure modes recorded yet.", "neutral")
    flags = artifact.blocking_flags.value if artifact.blocking_flags else []
    top = max(rows, key=lambda r: (r.severity, r.rpn))
    if flags:
        return (
            f"{len(flags)} safety/regulatory failure mode(s) blocking closure. "
            f"Highest severity: {top.severity} on '{top.failure_mode}'.",
            "fail",
        )
    high = [r for r in rows if r.severity >= 9]
    if high:
        return (
            f"{len(rows)} failure modes. {len(high)} at severity 9-10 — these cannot be "
            f"ignored on RPN grounds alone. Highest RPN: {top.rpn}.",
            "flag",
        )
    return (f"{len(rows)} failure modes assessed. Highest RPN {top.rpn} on '{top.failure_mode}'.", "pass")


def build_meaning(artifact: FmeaArtifact) -> str:
    return (
        "Rows are ordered by severity first, then RPN. That order is deliberate: RPN multiplies "
        "three 1-10 judgements, so a rare, easily-caught annoyance can score the same as a "
        "hazard that maims someone. Work the top of this list, and treat any high-severity row "
        "as actionable regardless of where its RPN lands."
    )


def build_report_card(artifact: FmeaArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    rows = artifact.rows

    flags = artifact.blocking_flags.value if artifact.blocking_flags else []
    if flags:
        items.append(("fail", f"{len(flags)} row(s) flagged safety/regulatory — these block project closure."))

    unconsulted = [r for r in rows if not r.anchors_consulted]
    if unconsulted:
        items.append(
            (
                "flag",
                f"{len(unconsulted)} of {len(rows)} rows were rated without the anchor scale shown — "
                "those ratings are gut feel, not calibrated.",
            )
        )
    elif rows:
        items.append(("pass", "Every rating was made with its anchor scale on screen."))

    unowned = [r for r in rows if r.action and not r.action_owner]
    if unowned:
        items.append(("flag", f"{len(unowned)} action(s) have no owner."))

    open_high = [r for r in rows if r.severity >= 9 and r.action_status == "open"]
    if open_high:
        items.append(("fail", f"{len(open_high)} severity 9-10 failure mode(s) still have an open action."))

    no_action = [r for r in rows if r.severity >= 9 and not r.action]
    if no_action:
        items.append(("fail", f"{len(no_action)} severity 9-10 row(s) have no action at all."))

    items.append(
        ("neutral", "RPN is an ordering aid, not a risk threshold — there is no RPN below which a hazard is safe.")
    )
    return items


def _cell(text: str, styles: dict) -> Paragraph:
    return Paragraph(esc(text or "—"), styles["table_cell"])


def build_table(artifact: FmeaArtifact, styles: dict, content_width: float) -> Table:
    header = [Paragraph(esc(label), styles["table_header"]) for _, label, _ in COLUMNS]
    body: list[list[Any]] = []
    for row in _ordered_rows(artifact):
        cells: list[Any] = []
        for key, _, _ in COLUMNS:
            value = row.rpn if key == "rpn" else getattr(row, key, "")
            cells.append(_cell(str(value), styles))
        body.append(cells)

    widths = [content_width * frac for _, _, frac in COLUMNS]
    # repeatRows=1 reprints the header on every page. Without it a table
    # that breaks leaves the continuation with nine unlabelled columns of
    # numbers, which is unreadable in a way that is easy to miss in review
    # because page one looks perfect.
    table = Table([header, *body], colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: FmeaArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    verdict_text, tone = build_verdict(artifact)

    story: list[Any] = []
    story += rt.header(
        project_name=project_name,
        tool_id=TOOL_ID,
        tool_title=TOOL_TITLE,
        version=version,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)
    story.append(build_table(artifact, styles, content_width))
    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story
