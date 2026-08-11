"""T-19 Pilot Plan Report — a pre-registration, and it only works before.

This page has one job the others do not: it exists to be printed BEFORE
the pilot runs, because everything valuable on it stops being valuable the
moment results are known. A success threshold chosen after seeing the data
is not a threshold, it is a description. A falsification line written
afterwards is a story.

So the page prints the declaration timestamps, and it prints the
falsification line as prominently as the success criterion. Most pilot
plans state only what success looks like, which quietly guarantees
success: with no line that would have counted as failure, any outcome can
be narrated as a win.

CONFOUNDERS ARE LISTED BEFORE THEY CAN BE EXPLAINED AWAY. A confounder
named in advance is a limitation; the same confounder raised afterwards
sounds like an excuse, and gets treated as one. The checklist prints
whether or not anything was ticked.

THE ONE CHANGE IS THE HEADLINE, because a pilot that changes four things
at once cannot attribute its result to any of them, and that is the
commonest way a pilot wastes a month.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.pilot_plan import PilotPlanArtifact
from .. import report_theme as rt
from ..charter_pdf_common import esc, kv_table

TOOL_ID = "T-19"
TOOL_TITLE = "Pilot Plan"

# The schema's Direction literal, in words a reader can act on. The values
# are "higher_is_better"/"lower_is_better" -- printing them raw gave
# "handoff_minutes must be lower_is_better 5.5", which is a field name
# leaking onto a page a sponsor reads.
DIRECTION_WORDS = {
    "lower_is_better": "must come down to",
    "higher_is_better": "must reach",
}


def direction_phrase(threshold: Any) -> str:
    direction = str(getattr(threshold, "direction", "")).lower()
    return DIRECTION_WORDS.get(direction, f"must reach ({direction.replace('_', ' ')})")


def confounder_items(artifact: PilotPlanArtifact) -> list[tuple[str, bool, str]]:
    """(name, changed, note) per confounder.

    Read off the model rather than a raw model_dump: each entry is a
    ConfounderAnswer with `changed` and `note`, not a bare boolean. An
    earlier version dumped to JSON and tested `value is True`, which is
    never true for a dict — so the "confounders acknowledged" line silently
    never printed, on a page whose whole argument is that naming them in
    advance is what separates a limitation from an excuse.
    """
    checklist = artifact.confounder_checklist
    if checklist is None:
        return []
    out: list[tuple[str, bool, str]] = []
    for name, answer in sorted(checklist.model_dump(mode="json").items()):
        if isinstance(answer, dict):
            out.append((name, bool(answer.get("changed")), str(answer.get("note") or "").strip()))
    return out


def build_verdict(artifact: PilotPlanArtifact) -> tuple[str, rt.Tone]:
    change_count = len(artifact.changes)
    threshold = artifact.success_threshold
    success = (
        f"{threshold.metric_ref} {direction_phrase(threshold)} {threshold.value:g}"
        if threshold is not None
        else "no success threshold declared"
    )
    if change_count > 1:
        # Necessarily a DECLARED package: the artifact refuses to validate
        # with more than one change unless one was declared (EXIT-10 in
        # artifacts/pilot_plan.py). So this is the honest path being used
        # correctly, and reporting it as a problem -- which an earlier
        # version did -- punishes the exact behaviour the schema forces.
        return (
            f"A declared package of {change_count} changes, tested together on purpose. Success: {success}.",
            "pass",
        )
    return (f"One change. Success: {success}.", "pass")


def build_meaning(artifact: PilotPlanArtifact) -> str:
    status = str(getattr(artifact, "status", "designed"))
    base = (
        "This is a prediction made in advance, which is the only kind worth making. The threshold and the "
        "falsification line were both written before the pilot ran, so when the data arrives there is "
        "nothing left to negotiate — the plan already says which result counts as which."
    )
    if len(artifact.changes) > 1:
        base += (
            f" With {len(artifact.changes)} changes in flight, a good result tells you the package worked and "
            "nothing about which part did. That was declared up front rather than discovered afterwards, "
            "which makes it a stated trade: speed now, and a separate pilot later if a component ever needs "
            "removing on its own."
        )
    if status != "designed":
        base += f" Status is \"{status}\" — this plan has already been acted on, so the declarations above are the record, not a draft."
    return base


def build_report_card(artifact: PilotPlanArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []

    count = len(artifact.changes)
    if count == 1:
        items.append(("pass", "One change, so the result is attributable to it."))
    else:
        items.append(
            (
                "pass",
                f"{count} changes declared as a deliberate package — the only way this artifact accepts more "
                "than one. The trade is explicit and stated: the result belongs to the package, never to a "
                "component of it.",
            )
        )

    threshold = artifact.success_threshold
    if threshold is not None:
        items.append(
            (
                "pass",
                f"Success declared in advance ({threshold.declared_at}): {threshold.metric_ref} "
                f"{direction_phrase(threshold)} {threshold.value:g}.",
            )
        )
    else:
        items.append(("fail", "No success threshold. Without one, any result can be read as a win."))

    line = (artifact.falsification_line or "").strip()
    if line:
        items.append(("pass", f"Falsification line declared: {rt.clip(line, 200)}"))
    else:
        items.append(
            (
                "fail",
                "No falsification line. A pilot with no result that would have counted as failure cannot fail.",
            )
        )

    design = artifact.comparison_design
    if design is not None:
        items.append(
            (
                "pass",
                f"Comparison defined before running — {str(design.kind).replace('_', ' ')}: "
                f"{rt.clip(design.description, 160)}",
            )
        )
    else:
        items.append(("fail", "No comparison design. Against what will the result be judged?"))

    checklist = confounder_items(artifact)
    flagged = [(name, note) for name, changed, note in checklist if changed]
    if flagged:
        detail = "; ".join(
            f"{name.replace('_', ' ')}" + (f" — {rt.clip(note, 90)}" if note else "") for name, note in flagged[:4]
        )
        items.append(
            (
                "flag",
                f"{len(flagged)} confounder(s) acknowledged up front: {detail}. "
                "Named in advance these are limitations; raised afterwards they read as excuses.",
            )
        )
    elif checklist:
        items.append(
            (
                "neutral",
                "No confounders ticked on the checklist. Worth a second look — a pilot with genuinely none is "
                "rarer than a checklist filled in quickly.",
            )
        )

    change = artifact.the_one_change
    if change is not None:
        if change.linked_cause_ids:
            items.append(("pass", f"The change is linked to {len(change.linked_cause_ids)} verified cause(s)."))
        else:
            items.append(
                (
                    "flag",
                    "The change is not linked to any verified cause — this pilot may be testing a guess.",
                )
            )

    if artifact.package_attribution_note is not None:
        note = artifact.package_attribution_note.value
        if note:
            items.append(("neutral", rt.clip(str(note), 240)))

    return items


def build_story(
    *,
    artifact: PilotPlanArtifact,
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

    change = artifact.the_one_change
    threshold = artifact.success_threshold
    design = artifact.comparison_design
    summary: list[tuple[str, str]] = []
    if change is not None:
        summary.append(("The one change", rt.clip(change.statement, 300)))
    if threshold is not None:
        summary.append(
            (
                "Success means",
                f"{threshold.metric_ref} {direction_phrase(threshold)} {threshold.value:g} "
                f"(declared {threshold.declared_at})",
            )
        )
    # The falsification line sits beside the success criterion rather than
    # below the fold. Printing only the success half is what makes a pilot
    # unfalsifiable in practice.
    if (artifact.falsification_line or "").strip():
        summary.append(("Failure means", rt.clip(artifact.falsification_line, 300)))
    if design is not None:
        summary.append(("Compared against", f"{str(design.kind).replace('_', ' ')} — {rt.clip(design.description, 200)}"))
    summary.append(("Status", str(getattr(artifact, "status", "designed"))))
    story.append(kv_table(summary, styles, content_width, label_frac=0.28))

    if len(artifact.changes) > 1:
        story.append(_label("WHAT IS BEING CHANGED", styles))
        for index, item in enumerate(artifact.changes, start=1):
            description = getattr(item, "text", None) or getattr(item, "description", None) or getattr(item, "statement", "")
            story.append(Paragraph(esc(f"{index}. {rt.clip(str(description), 260)}"), styles["card_item"]))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
