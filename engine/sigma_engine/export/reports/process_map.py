"""T-06 Process Map Report — the picture, and the two numbers under it.

The map is the deliverable here, so the drawing gets the top of the page.
But a process map that is only a drawing is a wall decoration: what makes
it worth an hour of a team's time is the arithmetic that falls out of it,
and this page prints the two numbers that change what people do.

THE VALUE-ADD RATIO IS THE PUNCHLINE. In almost every process anyone maps
for the first time, the share of total lead time that a customer would pay
for turns out to be under 10%, and seeing that number beside the picture
is what moves a room from "everyone is working hard" to "most of the
elapsed time is not work". It is printed as a share and in minutes,
because the minutes are what get recovered.

THE CONSTRAINT IS NAMED, NOT INFERRED. The longest step and the constraint
are different questions — the longest step is where the most time goes,
the constraint is what sets the pace of the whole line — and this page
keeps them apart, because improving a long step that is not the constraint
buys nothing at all.

WHAT THE PICTURE CANNOT SHOW is that untimed steps are excluded from both
numerator and denominator of the ratio. That is stated rather than
implied: a map with half its steps untimed produces a ratio about the
half that were.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.process_map import ProcessMapArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-06"
TOOL_TITLE = "Process Map"

# The eight wastes, in words. Reading a WasteEntry with a duck-typed
# getattr(w, "kind", w) fell through to str(w) on the model and printed a
# Python repr -- "waste id='waiting' note='Cups sit a median 4.5 min…'" --
# onto a page a supervisor reads. The field is `waste_id`, and it is a
# Literal, so there is no excuse for guessing at it.
WASTE_LABELS = {
    "defects": "Defects",
    "overproduction": "Overproduction",
    "waiting": "Waiting",
    "non_utilized_talent": "Talent unused",
    "transportation": "Transport",
    "inventory": "Inventory",
    "motion": "Motion",
    "extra_processing": "Over-processing",
}

STEP_TYPE_LABELS = {
    "value_add": "Value-add",
    "non_value_add": "Waste",
    "enabling": "Enabling",
}
# Value-add share below this is the normal, striking finding rather than a
# sign of a broken map.
TYPICAL_VA_SHARE = 0.15


def value_add(artifact: ProcessMapArtifact) -> Any:
    return artifact.value_add_ratio.value if artifact.value_add_ratio else None


def build_verdict(artifact: ProcessMapArtifact) -> tuple[str, rt.Tone]:
    va = value_add(artifact)
    if va is None:
        return (f"{len(artifact.steps)} step(s) across {len(artifact.lanes)} lane(s).", "neutral")
    share = va.value_add_ratio
    return (
        f"{share:.0%} of the {va.total_lead_time_minutes:g} minutes is value-add — "
        f"{va.non_value_add_minutes:g} minutes is waste and {va.enabling_minutes:g} is enabling.",
        "flag" if share < TYPICAL_VA_SHARE else "neutral",
    )


def build_meaning(artifact: ProcessMapArtifact) -> str:
    va = value_add(artifact)
    if va is None:
        return (
            "A process map is worth the hour it takes when it produces numbers, not just a picture. Time the "
            "steps and this page can say what share of the elapsed time a customer would pay for."
        )
    base = (
        f"Of every {va.total_lead_time_minutes:g} minutes this process takes, {va.value_add_minutes:g} change "
        "the thing the customer is buying. The rest is waiting, moving, checking and correcting — work that "
        "is really happening, done by people who are genuinely busy, and that the customer would not miss."
    )
    if va.value_add_ratio < TYPICAL_VA_SHARE:
        base += (
            " That ratio is normal and it is the point: the opportunity is almost never in making the "
            "value-add steps faster, it is in the gaps between them."
        )
    if va.steps_untimed:
        base += (
            f" {va.steps_untimed} step(s) carry no time and are excluded from both halves of the ratio, so "
            "this describes the timed part of the process only."
        )
    return base


def build_report_card(artifact: ProcessMapArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    va = value_add(artifact)

    items.append(("neutral", f"{len(artifact.steps)} step(s) across {len(artifact.lanes)} lane(s)."))

    if va is None:
        items.append(("flag", "No step carries a time, so no value-add ratio can be computed."))
    else:
        items.append(
            (
                "pass" if not va.steps_untimed else "flag",
                f"{va.steps_timed} step(s) timed"
                + (
                    f", {va.steps_untimed} untimed and excluded from the ratio entirely — not counted as zero."
                    if va.steps_untimed
                    else "."
                ),
            )
        )
        items.append(
            (
                "neutral",
                "Enabling time counts toward the denominator only: it is neither what the customer pays for "
                "nor pure waste.",
            )
        )

    longest = artifact.longest_step.value if artifact.longest_step else None
    constraint = artifact.constraint_step.value if artifact.constraint_step else None
    if longest is not None:
        items.append(
            (
                "neutral",
                f"Longest step: {longest.step_name} at {longest.time_minutes:g} min "
                f"({STEP_TYPE_LABELS.get(longest.step_type, longest.step_type)}).",
            )
        )
    if constraint is not None:
        items.append(
            (
                "pass" if constraint.meets_pace else "fail",
                f"Constraint: {constraint.step_name} at {constraint.time_minutes:g} min against a required "
                f"pace of {constraint.pace_minutes_per_unit:g} min/unit — "
                + ("keeps up with demand." if constraint.meets_pace else "cannot keep up with demand, so the whole process cannot."),
            )
        )
        if longest is not None and constraint.step_id != longest.step_id:
            items.append(
                (
                    "flag",
                    "The longest step is NOT the constraint. Speeding up the longest one buys nothing until "
                    f"{constraint.step_name} moves.",
                )
            )

    defect_points = [s for s in artifact.steps if s.defect_point]
    if defect_points:
        items.append(("neutral", f"{len(defect_points)} step(s) marked as defect points: " + ", ".join(rt.clip(s.name, 40) for s in defect_points[:4]) + "."))

    wasted = [s for s in artifact.steps if s.wastes]
    if wasted:
        items.append(("pass", f"{len(wasted)} step(s) carry a named waste from the waste walk."))
    else:
        items.append(("flag", "No step carries a named waste. The map shows what happens but not what is wrong with it."))

    return items


def build_steps_table(artifact: ProcessMapArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    lane_names = {lane.lane_id: lane.name for lane in artifact.lanes}
    header = [Paragraph(esc(h), styles["table_header"]) for h in ("#", "Step", "Who", "Type", "Minutes", "Waste")]
    body = []
    for step in sorted(artifact.steps, key=lambda s: s.order):
        wastes = ", ".join(WASTE_LABELS.get(w.waste_id, str(w.waste_id).replace("_", " ")) for w in step.wastes)
        body.append(
            [
                Paragraph(str(step.order), styles["table_cell"]),
                Paragraph(esc(rt.clip(step.name, 70)), styles["table_cell"]),
                Paragraph(esc(rt.clip(lane_names.get(step.lane_id, step.lane_id), 32)), styles["table_cell"]),
                Paragraph(esc(STEP_TYPE_LABELS.get(step.step_type, step.step_type)), styles["table_cell"]),
                Paragraph(f"{step.time_minutes:g}" if step.time_minutes is not None else "—", styles["table_cell"]),
                Paragraph(esc(rt.clip(wastes, 60)), styles["table_cell"]),
            ]
        )
    fracs = [0.05, 0.32, 0.17, 0.13, 0.12, 0.21]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: ProcessMapArtifact,
    project_name: str,
    version: int,
    chart_png: bytes | None = None,
    chart_unavailable_reason: str | None = None,
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
    # The map is the deliverable; it goes above the arithmetic.
    if chart_png or chart_unavailable_reason:
        story += rt.chart(
            chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
        )

    va = value_add(artifact)
    summary: list[tuple[str, str]] = []
    if va is not None:
        summary.append(("Value-add ratio", f"{va.value_add_ratio:.1%}"))
        summary.append(("Total lead time", f"{va.total_lead_time_minutes:g} min"))
        summary.append(("Of which waste", f"{va.non_value_add_minutes:g} min"))
    constraint = artifact.constraint_step.value if artifact.constraint_step else None
    if constraint is not None:
        summary.append(("Constraint", f"{constraint.step_name} ({constraint.time_minutes:g} min)"))
    if summary:
        story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("THE STEPS", styles))
    story.append(build_steps_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
