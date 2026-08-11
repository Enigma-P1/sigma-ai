"""T-02 COPQ Report — the number that gets quoted in the meeting.

This page has a specific hazard the others do not. Its output is a single
dollar figure, and a dollar figure is the most portable thing this app
produces: it gets lifted out of context, put in a slide, and repeated by
someone who never saw how it was built. By the third repetition nobody
remembers that half of it came from one operator's recollection.

So the page is built to travel with its own caveats attached:

THE ESTIMATE LABEL IS ON THE HEADLINE, not in a footnote. If any row is
marked as an estimate, the total is an estimate, and the banner says so
beside the number rather than below the fold.

THE MEASURED/ESTIMATED SPLIT IS PRINTED AS MONEY, not as a row count.
"3 of 5 rows are estimates" understates a case where the two measured rows
are $400 and the three estimated ones are $180,000 -- what a reader needs
is how many dollars of the total rest on somebody's memory.

EVERY ROW SHOWS ITS BASIS. The basis field is schema-required and this is
where it earns that: a reader can see "Q2 scrap log export" beside one row
and "estimate from operator interview" beside the next, and weigh them
differently without being told to.

WHAT IT DOES NOT DO is convert to an annual figure or extrapolate. Rows
carry free-text periods ("Q2 2026", "per month") that this engine
deliberately does not parse, so summing them is the caller's judgement.
The report says the periods are mixed when they are, and refuses to
invent an annualisation nobody asked for.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.copq import CopqArtifact, CopqRow
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-02"
TOOL_TITLE = "Cost of Poor Quality"

CATEGORY_LABELS = {
    "scrap": "Scrap",
    "rework": "Rework",
    "overtime": "Overtime",
    "expediting": "Expediting",
    "lost_business": "Lost business",
    "custom": "Custom",
}


def money(value: float) -> str:
    """Whole dollars. Cents on a COPQ total imply a precision the inputs
    never had -- a rate of "about $45/hr" does not produce a figure good to
    the penny, and printing one invites the number to be trusted further
    than it deserves."""
    return f"${value:,.0f}"


def row_label(row: CopqRow) -> str:
    if row.category == "custom":
        return (row.custom_label or "Custom").strip()
    return CATEGORY_LABELS.get(row.category, row.category)


def split_by_confidence(artifact: CopqArtifact) -> tuple[float, float]:
    """(measured dollars, estimated dollars). The split that matters, and
    the one a row count hides."""
    estimated = sum(r.amount for r in artifact.rows if r.is_estimate)
    measured = sum(r.amount for r in artifact.rows if not r.is_estimate)
    return measured, estimated


def periods(artifact: CopqArtifact) -> list[str]:
    """Distinct period strings, in first-appearance order. Free text by
    design -- this engine does not parse them, so it cannot reconcile them
    either, and saying which ones are present is the honest substitute."""
    seen: list[str] = []
    for row in artifact.rows:
        period = row.period.strip()
        if period and period not in seen:
            seen.append(period)
    return seen


def build_verdict(artifact: CopqArtifact) -> tuple[str, rt.Tone]:
    total = artifact.total.value if artifact.total else 0.0
    _, estimated = split_by_confidence(artifact)
    if estimated > 0:
        share = (estimated / total * 100) if total else 0.0
        return (
            f"{money(total)} — {rt.LABELS['estimate']}. {share:.0f}% of it ({money(estimated)}) is estimated.",
            "flag",
        )
    return (f"{money(total)}, every row from measured data.", "neutral")


def build_meaning(artifact: CopqArtifact) -> str:
    total = artifact.total.value if artifact.total else 0.0
    measured, estimated = split_by_confidence(artifact)
    period_list = periods(artifact)
    period_words = (
        f"over {period_list[0]}" if len(period_list) == 1 else f"across {len(period_list)} different periods"
    )

    base = (
        f"This is what the problem costs {period_words} — not a budget line, and not money already sitting "
        "in an account waiting to be released. It is the cost of the process behaving the way it currently "
        "behaves, and it becomes real savings only to the extent the process actually changes and somebody "
        "takes the resource out."
    )
    if estimated <= 0:
        return base + " Every row here traces to measured data, which is the strongest form this number takes."
    if measured <= 0:
        return (
            base
            + " Every row here is an estimate. That is a legitimate starting point for deciding whether a "
            "project is worth scoping, and it is not a figure to defend in a savings review — before this "
            "number is quoted anywhere it matters, at least the largest row needs a measured basis."
        )
    return (
        base
        + f" {money(measured)} of it traces to measured data and {money(estimated)} to estimates. Quote the "
        "whole figure only where an estimate is acceptable; where it is not, quote the measured part and say "
        "what the rest rests on."
    )


def build_report_card(artifact: CopqArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    total = artifact.total.value if artifact.total else 0.0
    measured, estimated = split_by_confidence(artifact)
    estimate_rows = [r for r in artifact.rows if r.is_estimate]

    items.append(("neutral", f"{len(artifact.rows)} cost row(s), totalling {money(total)}."))

    if estimate_rows:
        biggest = max(estimate_rows, key=lambda r: r.amount)
        items.append(
            (
                "flag" if estimated <= measured else "fail",
                f"{money(estimated)} of {money(total)} is estimated across {len(estimate_rows)} row(s). "
                f"The largest is {row_label(biggest)} at {money(biggest.amount)}, on the basis "
                f"\"{biggest.basis.strip()}\" — that is the row to measure first.",
            )
        )
    else:
        items.append(("pass", "No row is marked as an estimate."))

    period_list = periods(artifact)
    if len(period_list) > 1:
        items.append(
            (
                "flag",
                f"Rows cover {len(period_list)} different periods ({', '.join(period_list)}). They are summed "
                "as entered — this tool does not parse periods and so cannot put them on a common basis. "
                "Check that adding them answers the question you meant to ask.",
            )
        )
    elif period_list:
        items.append(("pass", f"All rows cover the same period: {period_list[0]}."))

    # The basis field is schema-required non-empty, so it cannot be missing.
    # What it CAN be is uselessly short, which passes validation and defeats
    # the purpose -- a reader cannot weigh "yes" as a basis.
    thin = [r for r in artifact.rows if len(r.basis.strip()) < 12]
    if thin:
        items.append(
            (
                "flag",
                f"{len(thin)} row(s) name a basis too short to check: "
                + "; ".join(f"{row_label(r)} — \"{r.basis.strip()}\"" for r in thin[:3])
                + ". A basis a later reader cannot follow is the same as none.",
            )
        )
    else:
        items.append(("pass", "Every row names a basis a reader can go and check."))

    zero_rows = [r for r in artifact.rows if r.amount == 0]
    if zero_rows:
        items.append(
            (
                "neutral",
                f"{len(zero_rows)} row(s) compute to zero — a quantity or rate of zero. Intentional placeholders "
                "are fine; unintentional ones quietly shrink the total.",
            )
        )

    items.append(
        (
            "neutral",
            "Row amounts are quantity x rate computed here, never typed. The total is the sum of those, "
            "recomputed on every save.",
        )
    )
    return items


def build_rows_table(artifact: CopqArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("Cost", "Quantity", "Rate", "Amount", "Period", "Basis")
    ]
    body = []
    # Largest first: the row that drives the total is the row a reader
    # should argue with, and it should not be buried in entry order.
    for row in sorted(artifact.rows, key=lambda r: r.amount, reverse=True):
        label = row_label(row)
        if row.is_estimate:
            label += "  (est.)"
        body.append(
            [
                Paragraph(esc(rt.clip(label, 45)), styles["table_cell"]),
                Paragraph(f"{row.quantity:,.4g}", styles["table_cell"]),
                Paragraph(money(row.rate) if row.rate >= 1 else f"${row.rate:,.2f}", styles["table_cell"]),
                Paragraph(money(row.amount), styles["table_cell"]),
                Paragraph(esc(rt.clip(row.period, 40)), styles["table_cell"]),
                Paragraph(esc(rt.clip(row.basis, 110)), styles["table_cell"]),
            ]
        )
    # Basis is the widest column on purpose: it is the free text a reader
    # has to actually read, and the numeric columns need no room to breathe.
    fracs = [0.17, 0.11, 0.11, 0.13, 0.14, 0.34]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: CopqArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    verdict_text, tone = build_verdict(artifact)
    total = artifact.total.value if artifact.total else 0.0
    measured, estimated = split_by_confidence(artifact)

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

    summary: list[tuple[str, str]] = [("Total", money(total))]
    if estimated > 0:
        summary.append(("From measured data", money(measured)))
        summary.append(("From estimates", money(estimated)))
    period_list = periods(artifact)
    summary.append(("Period", period_list[0] if len(period_list) == 1 else ", ".join(period_list) or "not stated"))
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("COST ROWS", styles))
    story.append(build_rows_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
