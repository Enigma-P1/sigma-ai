"""T-25 A3 Report — one sheet, eight panels, budgets that are enforced.

An A3 is named after a paper size, and that is the whole discipline. The
constraint is the method: if the story does not fit on one sheet at a size
a person can read across a table, the thinking is not finished. A tool
that lets the panels grow until they fit whatever was typed has removed
the only thing an A3 does that a document does not.

So the budgets here are real. Each panel gets a character allowance sized
to the space it actually has on a landscape sheet; text past it is cut on
the page, and every over-budget panel is named in the report card with how
far over it runs. The full narrative is never lost — it is in the project
record, which is what that export is for — but the sheet stays a sheet.

THE LAYOUT IS THE ARGUMENT. Left column is the problem side, top to
bottom: background, current condition, goal, analysis. Right column is the
answer side in the same order: countermeasures, results, follow-up,
lessons. A reader who knows A3s can find any panel without reading a
heading, because it is where it always is.

EMPTY PANELS PRINT AS EMPTY. A panel with no narrative is the most
informative thing on the sheet — usually "results" on a project that
declared success — and quietly collapsing the grid to hide it would be
the one thing this page must not do.
"""

from __future__ import annotations

from typing import Any

from reportlab.lib.pagesizes import landscape
from reportlab.platypus import PageBreak

from ...artifacts.a3 import PANEL_ORDER, A3Artifact
from .. import pdf_theme as theme
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc

TOOL_ID = "T-25"
TOOL_TITLE = "A3"

PAGE_SIZE = landscape(theme.PAGE_SIZE)

PANEL_LABELS = {
    "background": "1. Background",
    "current_condition": "2. Current condition",
    "goal": "3. Goal",
    "analysis": "4. Analysis",
    "countermeasures": "5. Countermeasures",
    "results": "6. Results",
    "follow_up_control": "7. Follow-up and control",
    "lessons": "8. Lessons",
}

# Per-panel character budgets, and they are the point of this report.
#
# Derived by rendering and then measuring, not chosen by feel. The first
# pass used 620/780 and put row four on a second page, which defeats the
# entire exercise: an A3 that runs to two sheets is a document.
#
# The arithmetic that survives: a landscape sheet leaves about 440pt of
# height under the header, four rows deep, so ~110pt a row. At this body
# size with cell padding that is about seven lines of ~80 characters.
#
# Analysis and countermeasures get the extra because they carry the
# reasoning the sheet exists to show. Goal gets least, deliberately: a goal
# needing 400 characters is not a goal yet.
PANEL_BUDGETS: dict[str, int] = {
    "background": 500,
    "current_condition": 500,
    "goal": 320,
    "analysis": 600,
    "countermeasures": 600,
    "results": 500,
    "follow_up_control": 500,
    "lessons": 500,
}
DEFAULT_BUDGET = 500

# The two-column order: problem side down the left, answer side down the
# right. Fixed, so a reader can find a panel without reading its heading.
LEFT_COLUMN = ("background", "current_condition", "goal", "analysis")
RIGHT_COLUMN = ("countermeasures", "results", "follow_up_control", "lessons")


def panel_map(artifact: A3Artifact) -> dict[str, Any]:
    return {p.panel: p for p in artifact.panels}


def narrative_for(artifact: A3Artifact, kind: str) -> str:
    panel = panel_map(artifact).get(kind)
    return (panel.narrative if panel is not None else "").strip()


def budget_for(kind: str) -> int:
    return PANEL_BUDGETS.get(kind, DEFAULT_BUDGET)


def over_budget(artifact: A3Artifact) -> list[tuple[str, int, int]]:
    """(panel kind, actual length, budget) for panels that do not fit."""
    out = []
    for kind in PANEL_ORDER:
        text = narrative_for(artifact, kind)
        budget = budget_for(kind)
        if len(text) > budget:
            out.append((kind, len(text), budget))
    return out


def empty_panels(artifact: A3Artifact) -> list[str]:
    return [kind for kind in PANEL_ORDER if not narrative_for(artifact, kind)]


def build_verdict(artifact: A3Artifact) -> tuple[str, rt.Tone]:
    empties = empty_panels(artifact)
    overs = over_budget(artifact)
    status = artifact.closure.project_status

    if empties:
        return (
            f"{len(empties)} of {len(PANEL_ORDER)} panels are empty: "
            f"{', '.join(PANEL_LABELS[k].split('. ', 1)[1].lower() for k in empties[:4])}.",
            "fail" if status == "closed" else "flag",
        )
    if overs:
        worst = max(overs, key=lambda row: row[1] - row[2])
        return (
            f"All eight panels written, {len(overs)} over budget — "
            f"{PANEL_LABELS[worst[0]].split('. ', 1)[1].lower()} runs {worst[1] - worst[2]} characters long.",
            "flag",
        )
    return (f"All eight panels written and each fits its space. Project is {status}.", "pass")


def build_meaning(artifact: A3Artifact) -> str:
    overs = over_budget(artifact)
    empties = empty_panels(artifact)
    base = (
        "An A3 is a size before it is a document. The constraint is the method: a story that does not fit on "
        "one readable sheet is a story whose thinking is not finished, and the panels are where that shows."
    )
    if empties:
        return (
            base
            + f" {len(empties)} panel(s) here are empty. An empty panel is the most informative thing on the "
            "sheet — it is the part of the argument nobody has made yet."
        )
    if overs:
        total_over = sum(actual - budget for _, actual, budget in overs)
        return (
            base
            + f" {len(overs)} panel(s) run past their space by {total_over} characters in total, and are cut "
            "on this sheet. That is not a formatting problem to fix by shrinking the type — it usually means "
            "the panel is doing two jobs, or is narrating what the attached artifacts already show. The full "
            "text is in the project record."
        )
    return base + " This one fits, which is worth as much as anything written on it."


def build_report_card(artifact: A3Artifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    overs = over_budget(artifact)
    empties = empty_panels(artifact)

    total_chars = sum(len(narrative_for(artifact, kind)) for kind in PANEL_ORDER)
    items.append(("neutral", f"{len(PANEL_ORDER) - len(empties)} of {len(PANEL_ORDER)} panels written, {total_chars:,} characters in total."))

    if empties:
        items.append(
            ("fail", "Empty panel(s): " + ", ".join(PANEL_LABELS[k] for k in empties) + ".")
        )
    else:
        items.append(("pass", "Every panel has a narrative."))

    for kind, actual, budget in overs:
        items.append(
            (
                "flag",
                f"{PANEL_LABELS[kind]} is {actual} characters against a budget of {budget} — cut on the sheet, "
                "full text in the project record.",
            )
        )
    if not overs and not empties:
        items.append(("pass", "Every panel fits its space at a readable size."))

    seeded = [p for p in artifact.panels if p.seeded_from is not None]
    if seeded:
        items.append(("pass", f"{len(seeded)} panel(s) seeded from their source artifact rather than retyped."))
    else:
        items.append(
            (
                "flag",
                "No panel is seeded from a source artifact. A retyped A3 drifts from the tools underneath it, "
                "and the drift is invisible.",
            )
        )

    close_check = artifact.closure.close_check.value if artifact.closure.close_check else None
    if close_check is not None:
        flags = getattr(close_check, "standing_hard_flags", None) or artifact.closure.standing_hard_flags
        if flags:
            items.append(
                (
                    "fail",
                    f"{len(flags)} standing hard flag(s) are unresolved. A project does not close over the top "
                    "of those.",
                )
            )
        else:
            items.append(("pass", "No standing hard flags outstanding."))

    open_items = artifact.closure.open_items
    if open_items:
        items.append(
            (
                "flag" if artifact.closure.project_status == "closed" else "neutral",
                f"{len(open_items)} open item(s) carried at closure.",
            )
        )

    rb = artifact.realized_benefits
    if rb is not None:
        # The money lives on the server-computed `result`, not on the input
        # block -- the inputs are before/after/fix_cost and the arithmetic
        # is done once, in the engine.
        computed = rb.result.value if rb.result else None
        if computed is not None:
            items.append(
                (
                    "neutral",
                    f"Realized over {rb.window}: {computed.realized_to_date:,.0f}, "
                    f"{computed.net_of_fix_cost:,.0f} net of the {rb.fix_cost:,.0f} fix cost — measured from "
                    "the COPQ re-run, not projected from the original estimate.",
                )
            )
        if rb.annualized_projection is not None:
            items.append(
                (
                    "flag",
                    f"An annualized projection of {rb.annualized_projection:,.0f} is also stated"
                    + (f", on the basis: {rt.clip(rb.annualized_projection_basis or '', 160)}" if rb.annualized_projection_basis else " with no stated basis")
                    + ". A projection is not a realized benefit and should never be the headline number.",
                )
            )

    return items


def build_panel_grid(artifact: A3Artifact, styles: dict, content_width: float) -> Any:
    """The sheet itself: two columns, four rows, fixed positions."""
    from reportlab.platypus import Paragraph, Table

    column_width = content_width / 2

    def cell(kind: str) -> Any:
        text = narrative_for(artifact, kind)
        budget = budget_for(kind)
        if not text:
            body = "<i>— empty</i>"
        else:
            clipped = rt.clip(text, budget)
            body = esc(clipped)
            if len(text) > budget:
                body += f" <i>[{len(text) - budget} more characters in the project record]</i>"
        return Paragraph(f"<b>{esc(PANEL_LABELS[kind])}</b><br/>{body}", styles["a3_panel"])

    rows = [[cell(left), cell(right)] for left, right in zip(LEFT_COLUMN, RIGHT_COLUMN)]
    table = Table(rows, colWidths=[column_width, column_width], hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: A3Artifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    # The panel body is smaller than the standard report body on purpose:
    # eight panels on one sheet is the constraint, and this is the size at
    # which they fit while staying readable across a table.
    styles["a3_panel"] = theme.ParagraphStyle(
        "a3_panel",
        parent=styles["table_cell"],
        fontSize=theme.TEXT_XS,
        leading=theme.TEXT_XS * 1.35,
    )

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
    story.append(build_panel_grid(artifact, styles, content_width))

    # PAGE ONE IS THE SHEET AND NOTHING ELSE. The verdict banner moved here,
    # behind a page break, for the same reason the budgets exist: it is not
    # part of an A3, and the ~45pt it occupied was enough to push row four
    # onto a second page. What a reader hands across a table is the eight
    # panels; the judgement about them is for whoever is checking the work.
    story.append(PageBreak())
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)
    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story
