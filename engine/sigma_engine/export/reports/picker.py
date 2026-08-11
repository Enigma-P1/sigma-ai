"""T-01 Project Picker Report — the page that says no.

This is the cheapest document in the suite and potentially the most
valuable, because the most expensive mistake in Six Sigma is not a bad
analysis — it is three months spent on a project that could never have
worked. Five questions, asked before anyone commits, and one of them
failing is a reason to stop rather than a box to argue past.

THE FAILED CRITERION IS NAMED, WITH THE ANSWER GIVEN. "Not viable as
scoped" on its own invites a rescope that changes nothing. "The outcome is
not measurable — you said: <their words>" tells the sponsor exactly what
has to change before this is worth starting.

THE ROUTE IS A CONSEQUENCE, NOT A CHOICE. Full DMAIC, PDCA quick path or
EXIT-01 follow from the five answers, and the page prints the route beside
the answers so a reader can check the reasoning rather than take it.

A PASS IS STATED PLAINLY AND WITHOUT CEREMONY. Four of five criteria
passing is not a pass, and a page that congratulates a marginal intake is
how a doomed project gets its budget.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.picker import PickerArtifact
from .. import report_theme as rt
from ..charter_pdf_common import esc, kv_table

TOOL_ID = "T-01"
TOOL_TITLE = "Project Picker"

# The five intake criteria, in the order they are asked, with the question
# each one really means.
CRITERIA = (
    ("scope_narrow", "Is the scope narrow enough?", "A process with a start and an end, not a department."),
    ("measurable_outcome", "Is the outcome measurable?", "A number that exists or can be collected, not a feeling."),
    ("data_obtainable", "Can the data be obtained?", "By this team, in this timeframe, without a new system."),
    ("process_owner_engaged", "Does a process owner care?", "Someone who owns the process asked for this or backs it."),
    ("business_impact_plausible", "Is the impact worth it?", "Plausible benefit, stated before the work starts."),
)

ROUTE_MEANING = {
    "full-DMAIC": "Full DMAIC — the problem is worth the whole method.",
    "PDCA": "PDCA quick path — real, but small enough that full DMAIC would cost more than the problem.",
    "EXIT-01": "EXIT-01 — not a viable first Green Belt project as scoped.",
}


def criterion_results(artifact: PickerArtifact) -> list[tuple[str, str, bool, str]]:
    """(label, question-meaning, answer, the user's own detail)."""
    out = []
    for field, label, meaning in CRITERIA:
        criterion = getattr(artifact, field)
        out.append((label, meaning, criterion.answer, criterion.detail.strip()))
    return out


def failed_criteria(artifact: PickerArtifact) -> list[tuple[str, str, bool, str]]:
    return [row for row in criterion_results(artifact) if not row[2]]


def build_verdict(artifact: PickerArtifact) -> tuple[str, rt.Tone]:
    failed = failed_criteria(artifact)
    route = str(artifact.route)
    if route == "EXIT-01":
        names = "; ".join(label.rstrip("?") for label, _, _, _ in failed) or "one or more criteria"
        return (f"Not a viable first project as scoped — {names.lower()}.", "fail")
    if failed:
        return (
            f"Routed to {route} with {len(failed)} criterion/criteria unmet — see below before committing.",
            "flag",
        )
    return (f"All five intake criteria met. Routed to {route}.", "pass")


def build_meaning(artifact: PickerArtifact) -> str:
    failed = failed_criteria(artifact)
    route = str(artifact.route)
    if route == "EXIT-01":
        label, _, _, detail = failed[0] if failed else ("", "", False, "")
        return (
            "Stopping here is the tool working, not the tool refusing. The most expensive mistake available "
            "is three months on a project that could not have succeeded, and the criterion below is the one "
            f"that would have caused it: {label.rstrip('?').lower()} — \"{rt.clip(detail, 160)}\". Change that, "
            "or pick a different problem; do not proceed and hope."
        )
    if route == "PDCA":
        return (
            "This is a real problem and a small one. PDCA gets it fixed in days rather than spending the "
            "measurement and analysis phases proving something everyone already agrees on. Choosing the "
            "smaller method for a smaller problem is a judgement, not a shortcut."
        )
    if failed:
        return (
            "The route is full DMAIC, but not every criterion is met. That is workable and it is a risk worth "
            "naming to the sponsor now — an unmet criterion at intake is the thing that stalls the project in "
            "month two, and it is much cheaper to fix here."
        )
    return (
        "All five hold, which means the usual reasons a project fails before it starts have been checked: it "
        "is scoped to a process, the outcome is a number, the data is reachable, somebody owns it, and the "
        "benefit is worth the effort. That is the point of asking before committing."
    )


def build_report_card(artifact: PickerArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    for label, meaning, answer, detail in criterion_results(artifact):
        items.append(
            (
                "pass" if answer else "fail",
                f"{label.rstrip('?')}: {'yes' if answer else 'NO'} — {rt.clip(detail, 200)}",
            )
        )
    route = str(artifact.route)
    items.append(("neutral", ROUTE_MEANING.get(route, f"Routed to {route}.")))
    return items


def build_story(
    *,
    artifact: PickerArtifact,
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

    story.append(kv_table([("Route", ROUTE_MEANING.get(str(artifact.route), str(artifact.route)))], styles, content_width, label_frac=0.24))

    story.append(_label("THE FIVE QUESTIONS, AND WHAT WAS ANSWERED", styles))
    for label, meaning, answer, detail in criterion_results(artifact):
        story.append(
            Paragraph(
                f"<b>{esc(label)}</b>  {esc('yes' if answer else 'NO')}<br/>"
                f"{esc(rt.clip(detail, 400))}<br/>"
                f"<i>{esc(meaning)}</i>",
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
