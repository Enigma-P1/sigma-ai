"""Charter PDF sections that read as narrative prose: the title block,
problem statement, SMART goal + metrics, and business impact. The
table-shaped sections (scope, team, timeline, risks) live in
charter_pdf_tables.py -- split so neither file runs long (M1 export brief).
"""

from __future__ import annotations

from typing import Any

from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, Spacer

from ..artifacts.charter import BusinessImpact, ProblemStatement, SmartGoal
from . import pdf_theme as theme
from .charter_pdf_common import esc, fmt_date, fmt_number, kv_table


def build_title_block(artifact: Any, project_name: str, version: int, styles: dict) -> list[Any]:
    updated = fmt_date(artifact.updated_at)
    meta = f"Version {version}  ·  Updated {updated}  ·  Artifact {artifact.artifact_id}"
    return [
        Paragraph("Project Charter", styles["title"]),
        Paragraph(esc(project_name), styles["subtitle"]),
        Spacer(1, theme.SPACE_1),
        Paragraph(esc(meta), styles["meta"]),
        Spacer(1, theme.SPACE_3),
        HRFlowable(width="100%", thickness=1, color=theme.BORDER, spaceAfter=theme.SPACE_3),
    ]


def _format_magnitude(mag: Any) -> str:
    text = fmt_number(mag.number)
    if mag.unit:
        text += f" {mag.unit}"
    if mag.period:
        text += f" ({mag.period})"
    return text


def build_problem_statement(ps: ProblemStatement, styles: dict, content_width: float) -> list[Any]:
    rows = [
        ("What", esc(ps.what)),
        ("Where", esc(ps.where)),
        ("When", esc(ps.when)),
        ("Magnitude", esc(_format_magnitude(ps.magnitude))),
    ]
    return [Paragraph("Problem Statement", styles["heading"]), kv_table(rows, styles, content_width)]


def build_goal(goal: SmartGoal, styles: dict, content_width: float) -> list[Any]:
    flows: list[Any] = [Paragraph("SMART Goal and Metrics", styles["heading"])]

    callout_style = styles["callout"]
    flows.append(Paragraph(esc(goal.statement), callout_style))
    flows.append(Spacer(1, theme.SPACE_2))

    baseline = fmt_number(goal.baseline_value) if goal.baseline_value is not None else "not yet measured"
    rows = [
        ("Metric", esc(goal.metric_name)),
        ("Baseline → Target", esc(f"{baseline} → {fmt_number(goal.target_value)} {goal.unit}")),
        ("Target date", fmt_date(goal.target_date)),
    ]
    flows.append(kv_table(rows, styles, content_width))

    if goal.consequential_metrics:
        flows.append(Spacer(1, theme.SPACE_2))
        flows.append(Paragraph("GUARDRAIL METRICS (watch these don't get worse)", styles["label"]))
        items = [ListItem(Paragraph(esc(m), styles["table_cell"]), leftIndent=theme.SPACE_4) for m in goal.consequential_metrics]
        flows.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=theme.SPACE_2))
    return flows


def build_business_impact(bi: BusinessImpact, styles: dict, content_width: float) -> list[Any]:
    rows = [
        ("Amount", esc(f"{fmt_number(bi.amount)} {bi.unit}")),
        ("Basis", esc(bi.basis)),
    ]
    return [Paragraph("Business Impact", styles["heading"]), kv_table(rows, styles, content_width)]
