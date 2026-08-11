"""T-21 Control Chart Report.

Two things make a control chart report worth printing rather than
screenshotting, and both are about what happens AFTER the chart is drawn.

FROZEN LIMITS. Limits recomputed as new points arrive will absorb any drift
and go on declaring the process in control while it walks away from target
-- the chart's most common and most invisible failure. So the freeze date,
the reason for any recalculation, and the source hash all print. A reader
can see whether the limits they are being shown were earned or moved.

ACKNOWLEDGED SIGNALS. A signal nobody responded to is not a monitored
process. The report prints every out-of-control point, which rule it broke,
and whether anyone wrote down what they did about it -- so an unacknowledged
signal is visible on paper instead of scrolled past on screen.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.control_chart import ControlChartArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, fmt_number, kv_table

TOOL_ID = "T-21"
TOOL_TITLE = "Control Chart"


def _tracked(artifact: ControlChartArtifact) -> list[Any]:
    return list(artifact.signals.value) if artifact.signals else []


def build_verdict(artifact: ControlChartArtifact) -> tuple[str, rt.Tone]:
    if artifact.frozen_at is None:
        return ("Limits are not frozen yet — this chart is not monitoring anything.", "flag")

    tracked = _tracked(artifact)
    unacknowledged = [t for t in tracked if not t.acknowledgment.acknowledged]
    kind = "I-MR" if artifact.chart_type == "imr" else "p"

    if not tracked:
        return (f"{kind} chart in control — no out-of-control signals since limits were frozen.", "pass")
    if unacknowledged:
        return (
            f"{len(tracked)} out-of-control signal(s), {len(unacknowledged)} with no recorded response.",
            "fail",
        )
    return (f"{len(tracked)} out-of-control signal(s), all acknowledged with a response.", "flag")


def build_meaning(artifact: ControlChartArtifact) -> str:
    if artifact.frozen_at is None:
        return (
            "A control chart only controls anything once its limits are frozen. Until then the limits "
            "move with the data, so the process is compared against itself and always looks fine."
        )
    if not artifact.armed.monitoring_started:
        return (
            "Limits are frozen but monitoring has not been declared started. The chart will show "
            "signals; nobody has committed to looking at them on a schedule."
        )
    return (
        "Limits are frozen, so new points are judged against the process as it was when it was "
        "proven stable — not against a moving average that would quietly absorb any drift. A point "
        "outside the limits is a signal to act on, not a number to average away."
    )


def build_report_card(artifact: ControlChartArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []

    if artifact.frozen_at:
        items.append(("pass", f"Limits frozen at {artifact.frozen_at} — they do not move as points arrive."))
    else:
        items.append(("fail", "Limits are not frozen."))

    if artifact.recalculation_log:
        items.append(
            ("flag", f"Limits have been recalculated {len(artifact.recalculation_log)} time(s) — each with a logged reason.")
        )
        for entry in artifact.recalculation_log[-3:]:
            items.append(("neutral", f"Recalculated {entry.at}: {entry.reason}"))

    if artifact.armed.monitoring_started:
        items.append(("pass", f"Monitoring started. {artifact.armed.cadence_note}".strip()))
    else:
        items.append(("flag", "Monitoring has not been declared started — nobody is committed to checking this."))

    unacknowledged = [t for t in _tracked(artifact) if not t.acknowledgment.acknowledged]
    if unacknowledged:
        items.append(
            ("fail", f"{len(unacknowledged)} signal(s) with no recorded response — an unanswered signal is not monitoring.")
        )

    if artifact.rule2_enabled or artifact.rule3_enabled:
        enabled = [name for name, on in (("2", artifact.rule2_enabled), ("3", artifact.rule3_enabled)) if on]
        items.append(("neutral", f"Western Electric zone rule(s) {', '.join(enabled)} enabled in addition to rules 1 and 4."))
    else:
        items.append(("neutral", "Rules 1 and 4 only (beyond 3 sigma; run of 8). Zone rules 2 and 3 are opt-in."))

    return items


def build_signal_table(artifact: ControlChartArtifact, styles: dict, content_width: float) -> Any | None:
    from reportlab.platypus import Paragraph, Table

    tracked = _tracked(artifact)
    if not tracked:
        return None
    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Point", "Rule broken", "Acknowledged", "Response")]
    body = []
    for item in tracked:
        signal = item.signal
        index = getattr(signal, "index", None)
        rule = getattr(signal, "rule", None) or getattr(signal, "rule_name", "")
        ack = item.acknowledgment
        body.append(
            [
                Paragraph(esc(str(index if index is not None else "—")), styles["table_cell"]),
                Paragraph(esc(str(rule)), styles["table_cell"]),
                Paragraph("yes" if ack.acknowledged else "NO", styles["table_cell"]),
                Paragraph(esc(ack.response_note or "—"), styles["table_cell"]),
            ]
        )
    widths = [content_width * f for f in (0.10, 0.26, 0.16, 0.48)]
    table = Table([header, *body], colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: ControlChartArtifact,
    project_name: str,
    version: int,
    chart_png: bytes | None,
    chart_unavailable_reason: str | None,
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
        tool_title=f"{TOOL_TITLE} — {artifact.metric_ref}",
        version=version,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)
    story += rt.chart(
        chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
    )

    rows: list[tuple[str, str]] = [("Chart type", "I-MR (individuals)" if artifact.chart_type == "imr" else "p (proportion)")]
    baseline = artifact.imr_baseline or artifact.p_baseline
    if baseline is not None:
        value = baseline.value
        centre = getattr(value, "center_line", None) or getattr(value, "xbar", None) or getattr(value, "pbar", None)
        ucl = getattr(value, "ucl", None)
        lcl = getattr(value, "lcl", None)
        if centre is not None:
            rows.append(("Centre line", fmt_number(centre)))
        if ucl is not None and lcl is not None:
            rows.append(("Control limits", f"{fmt_number(lcl)} to {fmt_number(ucl)}"))
    if artifact.frozen_at:
        rows.append(("Frozen at", artifact.frozen_at))
    story.append(kv_table(rows, styles, content_width, label_frac=0.3))

    signals = build_signal_table(artifact, styles, content_width)
    if signals is not None:
        story.append(_label("SIGNALS — every out-of-control point and what was done", styles))
        story.append(signals)

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
