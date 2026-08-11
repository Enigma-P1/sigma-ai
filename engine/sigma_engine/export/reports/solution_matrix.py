"""T-18 Solution Selection Report — the page that has to survive an argument.

This is the one report whose readers arrive with a preferred answer. A
solution matrix exists because somebody wants to do the expensive thing
and somebody else wants to do the easy thing, and its output is a ranking
that will be disputed by whoever it ranks second. So the page is built to
be argued with rather than to look authoritative.

THE WEIGHTS ARE PRINTED. A weighted total is only as defensible as the
weights behind it, and a ranking presented without them invites the
suspicion that they were tuned until the favourite won. Weights are
declared with a timestamp in this artifact; the page shows them.

UNSCORED SOLUTIONS ARE LISTED, NOT DROPPED. A solution with no criterion
scores has no weighted total and cannot be ranked — and silently omitting
it from the page is how an inconvenient option disappears from a decision.
They print below the ranking, named, with the reason they are not in it.

SOLUTIONS NOT LINKED TO A VERIFIED CAUSE ARE FLAGGED. The commonest
failure in Improve is a solution everyone likes that addresses no cause
the project verified. The engine tracks the link; this page makes the
absence visible rather than leaving it to be noticed.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.solution_matrix import SolutionMatrixArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-18"
TOOL_TITLE = "Solution Selection Matrix"

QUADRANT_LABELS = {
    "just_do_it": "Just do it",
    "big_project": "Big project",
    "fill_in": "Fill-in",
    "thankless": "Thankless",
}


def ranked_entries(artifact: SolutionMatrixArtifact) -> list[Any]:
    fix_list = artifact.ranked_fix_list.value if artifact.ranked_fix_list else None
    return list(fix_list.ranked) if fix_list else []


def unlinked_entries(artifact: SolutionMatrixArtifact) -> list[Any]:
    fix_list = artifact.ranked_fix_list.value if artifact.ranked_fix_list else None
    return list(fix_list.unlinked) if fix_list else []


def unscored_solutions(artifact: SolutionMatrixArtifact) -> list[Any]:
    """Solutions with no criterion scores. They cannot carry a weighted
    total, so they cannot be ranked — which is exactly why they need
    printing rather than dropping."""
    ranked_ids = {e.solution_id for e in ranked_entries(artifact)}
    return [s for s in artifact.solutions if s.solution_id not in ranked_ids]


def build_verdict(artifact: SolutionMatrixArtifact) -> tuple[str, rt.Tone]:
    ranked = ranked_entries(artifact)
    if not ranked:
        return (
            f"{len(artifact.solutions)} solution(s) on the table, none scored yet — nothing is ranked.",
            "neutral",
        )
    top = ranked[0]
    quadrant = QUADRANT_LABELS.get(top.quadrant, top.quadrant)
    total = f"{top.weighted_total:g}" if top.weighted_total is not None else "—"
    return (
        f"Top-ranked: {top.name.strip()} — weighted {total}, impact {top.impact}/5, effort {top.effort}/5 "
        f"({quadrant}).",
        "pass",
    )


def build_meaning(artifact: SolutionMatrixArtifact) -> str:
    ranked = ranked_entries(artifact)
    unlinked = unlinked_entries(artifact)
    base = (
        "This is a ranking, not a decision. It says which solutions score best against criteria this team "
        "declared and weighted before scoring — which is what keeps the choice from being whoever argued "
        "hardest in the room. The weights are the argument; if you disagree with the order, disagree with "
        "the weights first."
    )
    if unlinked:
        base += (
            f" {len(unlinked)} solution(s) here are not linked to any verified cause. A solution that "
            "addresses no cause the project proved is a guess with a rank next to it, however well it scores."
        )
    if len(ranked) >= 2 and ranked[0].weighted_total is not None and ranked[1].weighted_total is not None:
        gap = ranked[0].weighted_total - ranked[1].weighted_total
        if gap <= 0.5:
            base += (
                f" The top two are separated by {gap:g}, which is inside the noise of a 1–5 scoring scale. "
                "Treat them as tied and pick on something this matrix does not measure — reversibility, or "
                "who has to do the work."
            )
    return base


def build_report_card(artifact: SolutionMatrixArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    ranked = ranked_entries(artifact)
    unlinked = unlinked_entries(artifact)
    unscored = unscored_solutions(artifact)

    items.append(("neutral", f"{len(artifact.solutions)} solution(s), {len(artifact.criteria)} weighted criterion/criteria."))

    if not artifact.criteria:
        items.append(
            (
                "fail",
                "No criteria declared. Impact and effort alone put solutions in quadrants but cannot rank "
                "them, and a quadrant is not a decision.",
            )
        )
    else:
        items.append(("pass", "Criteria were declared and weighted before scoring."))

    if unscored:
        items.append(
            (
                "flag",
                f"{len(unscored)} solution(s) are unscored and therefore unranked: "
                + ", ".join(s.name.strip() for s in unscored[:4])
                + ". They are listed below the ranking rather than dropped.",
            )
        )
    else:
        items.append(("pass", "Every solution on the table is scored."))

    if unlinked:
        items.append(
            (
                "fail",
                f"{len(unlinked)} solution(s) address no verified cause: "
                + ", ".join(getattr(u, "name", str(u)) for u in unlinked[:4])
                + ".",
            )
        )
    else:
        items.append(("pass", "Every solution links to at least one verified cause."))

    if ranked:
        thankless = [e for e in ranked if e.quadrant == "thankless"]
        if thankless:
            items.append(
                (
                    "flag",
                    f"{len(thankless)} solution(s) sit in the thankless quadrant (high effort, low impact): "
                    + ", ".join(e.name.strip() for e in thankless[:3])
                    + ". Ranking them at all is worth a second look.",
                )
            )

    items.append(
        (
            "neutral",
            "Weighted totals are score x weight summed per solution, computed here and never hand-entered. "
            "A 1–5 scale is ordinal — the totals order the options, they do not measure the distance between "
            "them.",
        )
    )
    return items


def build_ranking_table(artifact: SolutionMatrixArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("#", "Solution", "Weighted", "Impact", "Effort", "Quadrant")
    ]
    body = []
    for entry in ranked_entries(artifact):
        body.append(
            [
                Paragraph(str(entry.rank), styles["table_cell"]),
                Paragraph(esc(rt.clip(entry.name, 70)), styles["table_cell"]),
                Paragraph(f"{entry.weighted_total:g}" if entry.weighted_total is not None else "—", styles["table_cell"]),
                Paragraph(f"{entry.impact}/5", styles["table_cell"]),
                Paragraph(f"{entry.effort}/5", styles["table_cell"]),
                Paragraph(esc(QUADRANT_LABELS.get(entry.quadrant, entry.quadrant)), styles["table_cell"]),
            ]
        )
    fracs = [0.06, 0.40, 0.14, 0.12, 0.12, 0.16]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_criteria_table(artifact: SolutionMatrixArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Criterion", "Weight", "Declared")]
    body = [
        [
            Paragraph(esc(rt.clip(c.name, 60)), styles["table_cell"]),
            Paragraph(f"{c.weight:g}", styles["table_cell"]),
            Paragraph(esc(c.declared_at), styles["table_cell"]),
        ]
        for c in artifact.criteria
    ]
    fracs = [0.50, 0.18, 0.32]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: SolutionMatrixArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    from reportlab.platypus import Paragraph

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

    ranked = ranked_entries(artifact)
    summary: list[tuple[str, str]] = [
        ("Solutions", str(len(artifact.solutions))),
        ("Ranked", str(len(ranked))),
        ("Criteria", str(len(artifact.criteria))),
    ]
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    if ranked:
        story.append(_label("RANKING", styles))
        story.append(build_ranking_table(artifact, styles, content_width))

    if artifact.criteria:
        story.append(_label("THE WEIGHTS BEHIND THE RANKING", styles))
        story.append(build_criteria_table(artifact, styles, content_width))

    unscored = unscored_solutions(artifact)
    if unscored:
        story.append(_label("ON THE TABLE BUT NOT RANKED", styles))
        for solution in unscored:
            story.append(
                Paragraph(
                    esc(f"{solution.name.strip()} — no criterion scores, so no weighted total."),
                    styles["card_item"],
                )
            )

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
