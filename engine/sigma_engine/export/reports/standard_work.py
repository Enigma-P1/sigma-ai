"""T-24 Standard Work / SOP Report — the only report meant to be used, not read.

Every other page in this suite is written for someone deciding something.
This one is written for someone doing something, at the machine, probably
in a hurry, possibly on their second day. That changes what a good page
looks like: no verdict banner competing with the first step, no analysis
prose between the reader and the instruction, and a numbered list that
survives being printed and taped to a wall.

ACTION AND STANDARD ARE SEPARATE COLUMNS, ALWAYS. "What you do" and "what
right looks like" are different sentences, and SOPs fail most often by
merging them — "clean the filter properly" is an action with the standard
smuggled into an adverb, and nobody can tell whether they have done it.
The schema keeps them apart and so does the page.

CHANGED STEPS ARE MARKED. When an SOP supersedes a prior version, the
person who already knows the old way needs to see what moved, and reading
the whole thing again to find out is what guarantees they will not.

THE STALENESS QUESTION IS ASKED ON THE PAGE. An SOP with an effective date
and no change log entry for a year is either perfect or abandoned, and the
report card says which question to ask rather than pretending the document
is evergreen.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.standard_work import SopStep, StandardWorkArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-24"
TOOL_TITLE = "Standard Work"

# A step whose action runs past this is not one step. The number is a
# judgement rather than a limit: it is where "do X" turns into a paragraph
# that hides three decisions.
LONG_ACTION_CHARS = 220
MAX_ACTION_CHARS = 300
MAX_STANDARD_CHARS = 240
MAX_NOTE_CHARS = 160


def ordered_steps(artifact: StandardWorkArtifact) -> list[SopStep]:
    return sorted(artifact.steps, key=lambda s: s.order)


def changed_steps(artifact: StandardWorkArtifact) -> list[SopStep]:
    return [s for s in artifact.steps if s.changed_from_prior]


def build_verdict(artifact: StandardWorkArtifact) -> tuple[str, rt.Tone]:
    steps = artifact.steps
    changed = changed_steps(artifact)
    supersedes = (artifact.supersedes or "").strip()
    if supersedes and changed:
        return (
            f"{len(steps)} step(s), v{artifact.version}, effective {artifact.effective_date}. "
            f"{len(changed)} step(s) changed from the version this replaces.",
            "neutral",
        )
    return (
        f"{len(steps)} step(s), v{artifact.version}, effective {artifact.effective_date}. "
        f"Owned by {artifact.owner.strip()}.",
        "neutral",
    )


def build_meaning(artifact: StandardWorkArtifact) -> str:
    changed = changed_steps(artifact)
    base = (
        "Standard work is the current best-known way to do this, written down so it can be taught, followed "
        "and improved. It is not a rule to obey and forget: it is the baseline the next improvement is "
        "measured against, which is why it carries a version and an owner."
    )
    if changed:
        base += (
            f" {len(changed)} step(s) here changed from the previous version and are marked. Someone who "
            "already knows the old way should read those and can skim the rest."
        )
    if not artifact.linked_control_plan_id:
        base += (
            " Nothing in the control plan points at this document yet, so nobody is scheduled to notice if "
            "the process drifts away from it."
        )
    return base


def build_report_card(artifact: StandardWorkArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    steps = ordered_steps(artifact)

    items.append(("neutral", f"{len(steps)} step(s), owned by {artifact.owner.strip()}."))

    # action and standard are schema-required non-empty, so the failure that
    # actually happens is one restating the other.
    echoing = [s for s in steps if s.standard.strip().lower() == s.action.strip().lower()]
    if echoing:
        items.append(
            (
                "fail",
                f"{len(echoing)} step(s) give a standard identical to the action: "
                + "; ".join(f"step {s.order}" for s in echoing[:4])
                + ". \"What right looks like\" has to be checkable by someone who just did the action.",
            )
        )
    else:
        items.append(("pass", "Every step separates what you do from what right looks like."))

    long_steps = [s for s in steps if len(s.action.strip()) > LONG_ACTION_CHARS]
    if long_steps:
        items.append(
            (
                "flag",
                f"{len(long_steps)} step(s) run long enough to be several steps: "
                + ", ".join(f"step {s.order}" for s in long_steps[:4])
                + ". A step nobody can hold in their head gets skimmed.",
            )
        )
    else:
        items.append(("pass", "Every step is short enough to follow in one read."))

    orders = [s.order for s in steps]
    if len(set(orders)) != len(orders):
        items.append(("fail", "Two or more steps share an order number — the sequence is ambiguous."))
    elif orders and orders != list(range(min(orders), min(orders) + len(orders))):
        items.append(("flag", "Step numbers have gaps. Harmless on paper, confusing when someone refers to \"step 4\"."))
    else:
        items.append(("pass", "Steps are numbered in an unbroken sequence."))

    if artifact.supersedes:
        changed = changed_steps(artifact)
        if changed:
            items.append(("pass", f"{len(changed)} step(s) marked as changed from {artifact.supersedes}."))
        else:
            items.append(
                (
                    "flag",
                    f"This supersedes {artifact.supersedes} but no step is marked as changed. Either nothing "
                    "changed — in which case why the new version — or the marks were not applied.",
                )
            )

    if artifact.change_log:
        latest = max(artifact.change_log, key=lambda entry: entry.at)
        items.append(("pass", f"Change log present; latest entry {latest.at}: {rt.clip(latest.note, 120)}"))
    else:
        items.append(
            (
                "flag",
                "No change log. A document with no history cannot be told apart from one nobody has revisited.",
            )
        )

    if artifact.linked_control_plan_id:
        items.append(("pass", f"A control plan references this document ({artifact.linked_control_plan_id})."))
    else:
        items.append(
            (
                "flag",
                "No control plan points here. Standard work with nothing watching it is a document, not a "
                "control.",
            )
        )

    if artifact.seeded_from_process_map_id:
        items.append(("pass", f"Seeded from the process map ({artifact.seeded_from_process_map_id}) rather than written from memory."))

    return items


def build_steps_table(artifact: StandardWorkArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    has_changes = bool(changed_steps(artifact))
    labels = ["#", "Do this", "What right looks like"]
    if has_changes:
        labels.append("New?")
    header = [Paragraph(esc(h), styles["table_header"]) for h in labels]

    body = []
    for step in ordered_steps(artifact):
        # Escape FIRST, then add markup. Building the string the other way
        # round leaves the action unescaped, and an action containing "&" or
        # "<" — a spec like "<0.5 mm" is entirely plausible here — breaks
        # the Paragraph's XML parse rather than printing.
        action = esc(rt.clip(step.action, MAX_ACTION_CHARS))
        if step.note.strip():
            action += f"<br/><i>{esc(rt.clip(step.note, MAX_NOTE_CHARS))}</i>"
        row = [
            Paragraph(str(step.order), styles["table_cell"]),
            Paragraph(action, styles["table_cell"]),
            Paragraph(esc(rt.clip(step.standard, MAX_STANDARD_CHARS)), styles["table_cell"]),
        ]
        if has_changes:
            row.append(Paragraph("changed" if step.changed_from_prior else "", styles["table_cell"]))
        body.append(row)

    fracs = [0.05, 0.50, 0.34, 0.11] if has_changes else [0.06, 0.55, 0.39]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: StandardWorkArtifact,
    project_name: str,
    version: int,
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
        tool_title=f"{TOOL_TITLE} — {rt.clip(artifact.title, 80)}",
        version=version,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)

    summary: list[tuple[str, str]] = [
        ("Owner", artifact.owner.strip()),
        ("Version", f"v{artifact.version}"),
        ("Effective", artifact.effective_date),
    ]
    if artifact.supersedes:
        summary.append(("Supersedes", artifact.supersedes))
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    # The steps come before the analysis, unlike every other report here.
    # Someone printing this is printing it for the steps.
    story.append(_label("THE STEPS", styles))
    story.append(build_steps_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
