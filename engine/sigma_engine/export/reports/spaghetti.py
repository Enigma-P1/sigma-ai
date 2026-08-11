"""T-07 Spaghetti Diagram Report — the walking, priced in hours.

The drawing is what people remember and the arithmetic is what gets the
layout changed. A tangle of lines makes a room say "that looks bad"; a
line saying eleven kilometres a year makes them move the printer.

SO DISTANCE IS CONVERTED TO TIME, AND TIME TO A WORKING YEAR. Metres per
trip is abstract. Minutes per day is concrete. Days per year is a
staffing decision, and it is the same number.

CROSSINGS ARE COUNTED SEPARATELY FROM DISTANCE. Two operators walking the
same aisle in opposite directions is not extra distance — it is a
collision, a wait, and a near-miss, and layouts that reduce distance
sometimes increase it.

THE WALK SPEED IS PRINTED AS AN ASSUMPTION, because every time figure on
this page is distance divided by it. A reader who disagrees with the speed
can scale the conclusion themselves, which is not possible if the
assumption is buried.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.spaghetti import SpaghettiArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-07"
TOOL_TITLE = "Spaghetti Diagram"

# A working year, for turning minutes a day into something a manager can
# act on. Stated on the page rather than applied silently.
WORKING_DAYS_PER_YEAR = 250


def metrics(artifact: SpaghettiArtifact) -> Any:
    return artifact.metrics.value if artifact.metrics else None


def build_verdict(artifact: SpaghettiArtifact) -> tuple[str, rt.Tone]:
    m = metrics(artifact)
    if m is None or not m.routes:
        return (f"{len(artifact.routes)} route(s) drawn, not yet measured.", "neutral")
    daily_minutes = m.total_daily_walk_time_minutes_all
    yearly_hours = daily_minutes * WORKING_DAYS_PER_YEAR / 60
    return (
        f"{m.total_daily_distance_all:,.0f} {m.unit} walked a day — {daily_minutes:,.0f} minutes, "
        f"about {yearly_hours:,.0f} hours a year across {len(m.operator_totals)} operator(s).",
        "flag" if yearly_hours >= 100 else "neutral",
    )


def build_meaning(artifact: SpaghettiArtifact) -> str:
    m = metrics(artifact)
    if m is None or not m.routes:
        return (
            "A spaghetti diagram turns a layout into a number. Until the routes are measured it is a picture "
            "of what people already suspect."
        )
    yearly_hours = m.total_daily_walk_time_minutes_all * WORKING_DAYS_PER_YEAR / 60
    base = (
        f"That is roughly {yearly_hours:,.0f} hours a year of someone walking, which nobody has ever asked "
        f"for and nobody is paid to do. It is spent in seconds, which is why it is invisible: no single trip "
        "is worth complaining about."
    )
    if m.total_crossing_count:
        base += (
            f" On top of it, {m.total_crossing_count} path crossing(s) — points where two people are in the "
            "same place at once. Those cost waiting and near-misses rather than distance, and a layout change "
            "that shortens walks can easily make them worse."
        )
    base += (
        f" Every time figure here is distance divided by an assumed walking speed of "
        f"{m.walk_speed_units_per_minute:g} {m.unit}/minute; disagree with that and the hours scale directly."
    )
    return base


def build_report_card(artifact: SpaghettiArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    m = metrics(artifact)

    items.append(("neutral", f"{len(artifact.routes)} route(s), {len(artifact.operators)} operator(s)."))

    if artifact.calibration is None:
        items.append(
            (
                "fail",
                "The floor plan is not calibrated, so pixel distances cannot become real ones. Every distance "
                "below is unusable until a known length is marked on the plan.",
            )
        )
    else:
        items.append(("pass", "The floor plan is calibrated against a known length."))

    if m is None or not m.routes:
        items.append(("flag", "No route metrics computed yet."))
        return items

    items.append(
        (
            "neutral",
            f"Assumed walking speed {m.walk_speed_units_per_minute:g} {m.unit}/minute"
            + (" (overridden from the default)" if artifact.walk_speed_override_per_minute else "")
            + ". Every time figure on this page is distance divided by it.",
        )
    )
    items.append(
        (
            "neutral",
            f"A year here means {WORKING_DAYS_PER_YEAR} working days; the daily figures are the measured ones.",
        )
    )

    if m.total_crossing_count:
        items.append(
            (
                "flag",
                f"{m.total_crossing_count} path crossing(s) — congestion and near-miss points, which distance "
                "alone does not capture.",
            )
        )
    else:
        items.append(("pass", "No path crossings detected between the drawn routes."))

    worst = max(m.operator_totals, key=lambda o: o.total_daily_distance, default=None)
    if worst is not None and len(m.operator_totals) > 1:
        items.append(
            (
                "neutral",
                f"{worst.operator_name} walks the most: {worst.total_daily_distance:,.0f} {m.unit} a day over "
                f"{worst.daily_trip_count:g} trip(s).",
            )
        )

    window = artifact.observation_window
    described = getattr(window, "description", "") or getattr(window, "note", "")
    if not str(described).strip():
        items.append(
            (
                "flag",
                "The observation window is not described. Routes drawn on a quiet afternoon and scaled to a "
                "year overstate or understate by however much that afternoon differed.",
            )
        )

    return items


def build_routes_table(artifact: SpaghettiArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    m = metrics(artifact)
    operator_names = {o.operator_id: o.operator_name for o in m.operator_totals}
    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("Trip", "Who", "Per trip", "Times a day", "Distance a day", "Minutes a day")
    ]
    body = []
    for route in sorted(m.routes, key=lambda r: r.daily_distance, reverse=True):
        body.append(
            [
                Paragraph(esc(rt.clip(route.trip_label, 60)), styles["table_cell"]),
                Paragraph(esc(rt.clip(operator_names.get(route.operator_id, route.operator_id), 30)), styles["table_cell"]),
                Paragraph(f"{route.distance_per_trip:,.1f} {m.unit}", styles["table_cell"]),
                Paragraph(f"{route.frequency_per_day:g}", styles["table_cell"]),
                Paragraph(f"{route.daily_distance:,.0f} {m.unit}", styles["table_cell"]),
                Paragraph(f"{route.daily_walk_time_minutes:,.1f}", styles["table_cell"]),
            ]
        )
    fracs = [0.28, 0.16, 0.14, 0.13, 0.16, 0.13]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: SpaghettiArtifact,
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
    m = metrics(artifact)

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
    if chart_png or chart_unavailable_reason:
        story += rt.chart(
            chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
        )

    if m is not None and m.routes:
        yearly_hours = m.total_daily_walk_time_minutes_all * WORKING_DAYS_PER_YEAR / 60
        story.append(
            kv_table(
                [
                    ("Walked per day", f"{m.total_daily_distance_all:,.0f} {m.unit}"),
                    ("Time per day", f"{m.total_daily_walk_time_minutes_all:,.0f} minutes"),
                    ("Over a working year", f"about {yearly_hours:,.0f} hours ({WORKING_DAYS_PER_YEAR} days)"),
                    ("Path crossings", str(m.total_crossing_count)),
                ],
                styles,
                content_width,
                label_frac=0.32,
            )
        )
        story.append(_label("EVERY TRIP, WORST FIRST", styles))
        story.append(build_routes_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
