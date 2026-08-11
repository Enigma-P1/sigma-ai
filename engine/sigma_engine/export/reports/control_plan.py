"""T-22 Control Plan Report — the page that outlives the project.

Every other report in this suite documents something that already
happened. This one is an instruction to people who are not in the room:
here is what to watch, how often, who watches it, and what to do when it
moves. It is the only artifact here with a job after the Belt goes away,
and it is the one most likely to be printed and pinned up.

Which is exactly why it is the easiest one to fake. A control plan with
eleven tidy rows, every column filled, and no named owner who has agreed
to anything is indistinguishable on paper from a real one -- and it will
be followed by nobody. The engine already computes that judgement
(`plan_health.is_theater`), so this page leads with it rather than
printing the tidy table and letting the reader assume.

THE VERDICT IS ABOUT PEOPLE, NOT COMPLETENESS. Ownerless items and owners
who never accepted are the two failure modes that matter, and they are
what the banner reports. A plan can have every cell filled and still fail
here, which is the point.

REACTIONS TRAVEL WITH THE ITEM THEY BELONG TO. An OCAP printed in a
separate section at the back is a section nobody reads at 2am. Each
monitored item carries its own trigger and first action in the same row,
so the page works as the thing it will actually be used as: a lookup
table under time pressure.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.control_plan import ControlPlanArtifact, MonitoredItem, OcapEntry
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-22"
TOOL_TITLE = "Control Plan + Reaction Plan"

# Per-column budgets. This table is a lookup under time pressure, and the
# fields behind it are unbounded free text -- the worked example's "how
# often" carried a 400-character sampling rationale, which on its own turned
# one row into a full page of eight-character-wide columns.
#
# The rationale is not thrown away: frequency reasons print in their own
# block below the table, where a paragraph is the right shape. What the grid
# keeps is the instruction.
MAX_CHARACTERISTIC_CHARS = 70
MAX_HOW_CHARS = 60
MAX_WHERE_CHARS = 32
MAX_FREQUENCY_CHARS = 45
MAX_OWNER_CHARS = 40
MAX_REACTION_CHARS = 150


def ocap_for(artifact: ControlPlanArtifact, item_id: str) -> OcapEntry | None:
    for entry in artifact.ocap_entries:
        if entry.monitored_item_id == item_id:
            return entry
    return None


def owner_text(item: MonitoredItem) -> str:
    """Owner, and whether they know. An unaccepted owner is a name someone
    typed, which is not the same as a person who agreed."""
    name = item.owner_name.strip()
    if not name:
        return "— nobody"
    if not item.owner_accepted:
        return f"{name} (not accepted)"
    if item.per_shift_owners:
        accepted = sum(1 for s in item.per_shift_owners if s.owner_accepted)
        return f"{name} · {accepted}/{len(item.per_shift_owners)} shifts accepted"
    return name


def reaction_text(entry: OcapEntry | None) -> str:
    if entry is None:
        return "— no reaction plan"
    parts = []
    if entry.trigger_signal.strip():
        parts.append(f"If: {entry.trigger_signal.strip()}")
    if entry.action_steps:
        parts.append(f"Then: {entry.action_steps[0].strip()}")
        if len(entry.action_steps) > 1:
            parts.append(f"(+{len(entry.action_steps) - 1} more step(s))")
    if entry.escalation_contact.strip():
        parts.append(f"Escalate to {entry.escalation_contact.strip()}")
    text = " · ".join(parts) if parts else "— reaction plan is empty"
    return rt.clip(text, MAX_REACTION_CHARS)


def build_verdict(artifact: ControlPlanArtifact) -> tuple[str, rt.Tone]:
    health = artifact.plan_health.value if artifact.plan_health else None
    count = len(artifact.monitored_items)
    if health is None:  # pragma: no cover -- the validator always computes it
        return (f"{count} item(s) monitored.", "neutral")

    problems = []
    if health.ownerless_item_ids:
        problems.append(f"{len(health.ownerless_item_ids)} item(s) with no owner")
    if health.unaccepted_owner_item_ids:
        problems.append(f"{len(health.unaccepted_owner_item_ids)} owner(s) who have not accepted")
    if health.check_in_overdue:
        problems.append("an overdue check-in")

    if health.is_theater:
        return (
            f"This plan will not hold: {', '.join(problems)}. "
            f"{count} item(s) are listed, and listing is not controlling.",
            "fail",
        )
    if problems:
        return (f"{count} item(s) monitored, with gaps: {', '.join(problems)}.", "flag")
    return (
        f"{count} item(s) monitored, every one owned by a named person who has accepted it.",
        "pass",
    )


def build_meaning(artifact: ControlPlanArtifact) -> str:
    health = artifact.plan_health.value if artifact.plan_health else None
    if health is not None and health.is_theater:
        return (
            "A control plan is a promise that somebody will notice when this process drifts back. Right now "
            "there is no such person for at least one of these items, so for that item the honest reading is "
            "that the gain will be lost and nobody will be watching when it happens. Assigning a name is not "
            "the fix — the fix is a named person who has said yes, on a frequency they can actually keep."
        )
    return (
        "This is what keeps the improvement from quietly reverting. Every row names a thing to watch, how "
        "often, who watches it, and what to do when it moves — so the response to a bad signal is a lookup "
        "rather than a debate. Its usefulness decays: owners move roles and frequencies get skipped, which "
        "is what the scheduled check-in exists to catch."
    )


def build_report_card(artifact: ControlPlanArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    health = artifact.plan_health.value if artifact.plan_health else None
    by_id = {i.item_id: i for i in artifact.monitored_items}

    def names(ids: list[str]) -> str:
        return ", ".join(by_id[i].characteristic if i in by_id else i for i in ids[:4]) + (
            f" (+{len(ids) - 4} more)" if len(ids) > 4 else ""
        )

    if health is not None:
        if health.ownerless_item_ids:
            items.append(("fail", f"No owner named for: {names(health.ownerless_item_ids)}."))
        else:
            items.append(("pass", "Every monitored item has a named owner."))

        if health.unaccepted_owner_item_ids:
            items.append(
                (
                    "fail",
                    f"An owner is named but has not accepted for: {names(health.unaccepted_owner_item_ids)}. "
                    "A name entered on someone's behalf is not a commitment.",
                )
            )
        else:
            items.append(("pass", "Every named owner has accepted."))

        items.append(
            (
                "fail" if health.check_in_overdue else "pass",
                health.check_in_overdue_detail,
            )
        )

    primary = [i for i in artifact.monitored_items if i.is_primary_ctq]
    if primary:
        items.append(("pass", f"The primary CTQ is monitored: {primary[0].characteristic}."))
    else:
        items.append(
            (
                "fail",
                "No item is marked as the primary CTQ. A control plan that does not watch the thing the "
                "project was about is watching the wrong things carefully.",
            )
        )

    changed = [i for i in artifact.monitored_items if i.is_improve_change]
    if changed:
        items.append(("pass", f"{len(changed)} item(s) cover what Improve actually changed."))
    else:
        items.append(
            (
                "flag",
                "No item is marked as covering an Improve change. What was changed is the most likely thing "
                "to drift back.",
            )
        )

    missing_reaction = [i for i in artifact.monitored_items if ocap_for(artifact, i.item_id) is None]
    if missing_reaction:
        items.append(
            (
                "fail",
                f"{len(missing_reaction)} item(s) have no reaction plan: {names([i.item_id for i in missing_reaction])}. "
                "A signal nobody has a response to is a signal that gets ignored.",
            )
        )
    else:
        items.append(("pass", "Every monitored item has a reaction plan."))

    no_reason = [i for i in artifact.monitored_items if not i.frequency_reason.strip()]
    if no_reason:
        items.append(
            (
                "flag",
                f"{len(no_reason)} item(s) give no reason for their frequency. A default left standing is the "
                "commonest way a plan becomes unkeepable: nobody chose hourly, it was just there.",
            )
        )
    else:
        items.append(("pass", "Every frequency has a stated reason."))

    unverified = [r for r in artifact.training_rows if not r.verified_how.strip()]
    if artifact.training_rows and unverified:
        items.append(
            (
                "flag",
                f"{len(unverified)} of {len(artifact.training_rows)} training row(s) list training with no way "
                "to verify it happened.",
            )
        )
    elif artifact.training_rows:
        items.append(("pass", f"All {len(artifact.training_rows)} training row(s) name a verification method."))

    return items


def build_items_table(artifact: ControlPlanArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("What is watched", "How", "Where", "How often", "Owner", "If it moves")
    ]
    body = []
    # Primary CTQ first, then Improve changes, then the rest: under time
    # pressure the eye should land on the item the project was about.
    def sort_key(item: MonitoredItem) -> tuple[int, str]:
        return (0 if item.is_primary_ctq else 1 if item.is_improve_change else 2, item.characteristic.lower())

    for item in sorted(artifact.monitored_items, key=sort_key):
        label = rt.clip(item.characteristic, MAX_CHARACTERISTIC_CHARS)
        # Only badge it if the characteristic does not already say so --
        # the worked example's own text ends "the primary CTQ", and
        # appending the marker gave "... the primary CTQ) (primary CTQ)".
        if item.is_primary_ctq and "primary ctq" not in label.lower():
            label += " (primary CTQ)"
        body.append(
            [
                Paragraph(esc(label), styles["table_cell"]),
                Paragraph(esc(rt.clip(item.how_measured, MAX_HOW_CHARS)), styles["table_cell"]),
                Paragraph(esc(rt.clip(item.where, MAX_WHERE_CHARS)), styles["table_cell"]),
                Paragraph(esc(rt.clip(item.frequency, MAX_FREQUENCY_CHARS)), styles["table_cell"]),
                Paragraph(esc(rt.clip(owner_text(item), MAX_OWNER_CHARS)), styles["table_cell"]),
                Paragraph(esc(reaction_text(ocap_for(artifact, item.item_id))), styles["table_cell"]),
            ]
        )
    # The reaction column stays widest -- it is the one read under pressure
    # and the only cell holding a full sentence. The rest were rebalanced
    # after rendering: at 0.11 the "where" column was narrower than the word
    # "Espresso", so ReportLab broke words mid-way ("Espress / o station").
    # A column has to be wider than its longest word or wrapping stops
    # helping.
    fracs = [0.18, 0.15, 0.13, 0.13, 0.12, 0.29]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: ControlPlanArtifact,
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

    schedule = artifact.check_in_schedule
    summary: list[tuple[str, str]] = [("Items monitored", str(len(artifact.monitored_items)))]
    if schedule is not None:
        cadence = getattr(schedule, "cadence", None)
        if cadence is not None:
            summary.append(("Check-in cadence", f"every {cadence.interval} {cadence.unit}"))
        next_due = getattr(schedule, "next_due", None)
        if next_due is not None:
            summary.append(("Next check-in", str(next_due.value)))
    summary.append(("Plan as of", artifact.as_of))
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("WHAT IS WATCHED, AND BY WHOM", styles))
    story.append(build_items_table(artifact, styles, content_width))

    # Rationale, out of the grid. A frequency reason is a paragraph and the
    # table is a lookup; the two want different shapes on the page, and
    # forcing the paragraph into the cell was what broke the layout.
    reasons = [
        (item.characteristic.strip(), item.frequency_reason.strip())
        for item in artifact.monitored_items
        if item.frequency_reason.strip()
    ]
    if reasons:
        story.append(_label("WHY THESE FREQUENCIES", styles))
        for characteristic, reason in reasons:
            story.append(
                Paragraph(
                    esc(f"{rt.clip(characteristic, MAX_CHARACTERISTIC_CHARS)} — {rt.clip(reason, 320)}"),
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
