"""Charter PDF sections that read as tables: scope in/out, team + process
owner, timeline milestones, and the key-risks-&-mitigations block (matrix
§5a / A-4). The narrative sections (title, problem statement, goal,
business impact) live in charter_pdf_sections.py.
"""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Spacer, Table

from ..artifacts.charter import RiskRow, ScopeBlock, TeamMember, TimelineMilestone
from . import pdf_theme as theme
from .charter_pdf_common import base_table_style, esc, fmt_date


def build_scope(scope: ScopeBlock, styles: dict, content_width: float) -> list[Any]:
    col = content_width / 2
    table = Table(
        [
            [Paragraph("IN SCOPE", styles["table_header"]), Paragraph("OUT OF SCOPE", styles["table_header"])],
            [Paragraph(esc(scope.in_scope), styles["table_cell"]), Paragraph(esc(scope.out_scope), styles["table_cell"])],
        ],
        colWidths=[col, col],
    )
    table.setStyle(base_table_style())
    return [Paragraph("Scope", styles["heading"]), table]


def build_team(team: list[TeamMember], owner: TeamMember, styles: dict, content_width: float) -> list[Any]:
    flows: list[Any] = [Paragraph("Team and Process Owner", styles["heading"])]

    owner_table = Table(
        [[Paragraph("PROCESS OWNER", styles["table_header"]), Paragraph(esc(f"{owner.name} — {owner.role}"), styles["body"])]],
        colWidths=[content_width * 0.28, content_width * 0.72],
    )
    owner_table.setStyle(
        base_table_style(
            extra=[
                ("BACKGROUND", (0, 0), (-1, -1), theme.ACCENT_SOFT),
                ("BOX", (0, 0), (-1, -1), 0.75, theme.ACCENT_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    flows.append(owner_table)
    flows.append(Spacer(1, theme.SPACE_2))

    rows = [[Paragraph("NAME", styles["table_header"]), Paragraph("ROLE", styles["table_header"])]]
    for member in team:
        rows.append([Paragraph(esc(member.name), styles["table_cell"]), Paragraph(esc(member.role), styles["table_cell"])])
    team_table = Table(rows, colWidths=[content_width * 0.35, content_width * 0.65])
    team_table.setStyle(base_table_style())
    flows.append(team_table)
    return flows


def build_timeline(timeline: list[TimelineMilestone], styles: dict, content_width: float) -> list[Any]:
    rows = [[Paragraph("MILESTONE", styles["table_header"]), Paragraph("DATE", styles["table_header"])]]
    for m in timeline:
        rows.append([Paragraph(esc(m.name), styles["table_cell"]), Paragraph(fmt_date(m.date), styles["table_cell"])])
    table = Table(rows, colWidths=[content_width * 0.72, content_width * 0.28])
    table.setStyle(base_table_style())
    return [Paragraph("Timeline Milestones", styles["heading"]), table]


def build_risks(risks: list[RiskRow], styles: dict, content_width: float) -> list[Any]:
    flows: list[Any] = [Paragraph("Key Risks and Mitigations", styles["heading"])]
    if not risks:
        flows.append(Paragraph("No risks logged yet.", styles["body_muted"]))
        return flows

    widths = [w * content_width for w in (0.22, 0.11, 0.11, 0.38, 0.18)]
    header = [Paragraph(h, styles["table_header"]) for h in ("RISK", "LIKELIHOOD", "IMPACT", "MITIGATION", "OWNER")]
    rows: list[list[Any]] = [header]
    extra: list[tuple] = []
    for i, r in enumerate(risks, start=1):
        rows.append(
            [
                Paragraph(esc(r.risk), styles["table_cell"]),
                Paragraph(r.likelihood.upper(), styles["table_cell"]),
                Paragraph(r.impact.upper(), styles["table_cell"]),
                Paragraph(esc(r.mitigation), styles["table_cell"]),
                Paragraph(esc(r.owner), styles["table_cell"]),
            ]
        )
        # research §F: color the signal (the level), not the row -- same
        # pass/flag/fail scale as every status pill in the app.
        extra.append(("TEXTCOLOR", (1, i), (1, i), theme.RISK_LEVEL_COLOR[r.likelihood]))
        extra.append(("TEXTCOLOR", (2, i), (2, i), theme.RISK_LEVEL_COLOR[r.impact]))

    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(base_table_style(extra=extra))
    flows.append(table)
    return flows
