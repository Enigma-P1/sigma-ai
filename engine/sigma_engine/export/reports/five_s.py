"""T-23 5S Report — the score, and whether it means anything yet.

A 5S audit produces a number out of 25 and the number is almost always
read as a grade. It is more useful as a direction: one round is a
snapshot with no trend, and a rising total that is rising entirely on the
first four S's while Sustain stays flat is the classic pattern of an area
that gets tidied before audits.

So this page leads with the latest total, prints the per-category
breakdown that shows where it comes from, and gives the trend the
prominence a single total does not deserve.

SUSTAIN IS CALLED OUT SEPARATELY. It is the only one of the five that
measures whether the other four survive without supervision, and an area
scoring well on Sort/Set/Shine with a weak Sustain is not a 5S success
with one gap — it is a cleanup with a countdown on it.

AN AUDIT WITH NO ACTION IS A SCORE, NOT AN IMPROVEMENT. The lowest
category with no improvement action attached is flagged, because the
point of scoring an area is deciding what to do about it.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.five_s import FiveSArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-23"
TOOL_TITLE = "5S Audit"

CATEGORY_ORDER = ("sort", "set_in_order", "shine", "standardize", "sustain")
CATEGORY_LABELS = {
    "sort": "Sort",
    "set_in_order": "Set in order",
    "shine": "Shine",
    "standardize": "Standardize",
    "sustain": "Sustain",
}
MAX_PER_CATEGORY = 5
MAX_TOTAL = MAX_PER_CATEGORY * len(CATEGORY_ORDER)
# Below this a category is weak enough to be the thing to fix next.
WEAK_SCORE = 3


def latest_round(artifact: FiveSArtifact) -> Any:
    """Most recent by date, falling back to entry order when dates tie —
    an audit list is usually appended to, so the last entry is the newest."""
    return max(artifact.rounds, key=lambda r: (r.date, artifact.rounds.index(r)))


def scores_by_category(round_: Any) -> dict[str, int]:
    return {s.category: s.score for s in round_.scores}


def total_for(round_: Any) -> int:
    return sum(s.score for s in round_.scores)


def build_verdict(artifact: FiveSArtifact) -> tuple[str, rt.Tone]:
    current = latest_round(artifact)
    total = total_for(current)
    tone: rt.Tone = "pass" if total >= 20 else "flag" if total >= 13 else "fail"

    if len(artifact.rounds) < 2:
        return (
            f"{total}/{MAX_TOTAL} in {current.area.strip()} ({current.date}) — one round, so no trend yet.",
            tone,
        )
    previous = sorted(artifact.rounds, key=lambda r: r.date)[-2]
    change = total - total_for(previous)
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    return (
        f"{total}/{MAX_TOTAL} in {current.area.strip()} ({current.date}) — {direction}"
        + (f" {abs(change)} since {previous.date}." if change else f" since {previous.date}."),
        tone,
    )


def build_meaning(artifact: FiveSArtifact) -> str:
    current = latest_round(artifact)
    scores = scores_by_category(current)
    sustain = scores.get("sustain")

    base = (
        "5S scores an area on five habits, not on how it looks today. The first four can be achieved by a "
        "good clean-up; only the fifth says whether any of it survives a month without someone watching."
    )
    if sustain is not None and sustain <= WEAK_SCORE:
        others = [v for k, v in scores.items() if k != "sustain"]
        if others and sum(others) / len(others) > sustain + 1:
            return (
                base
                + f" That is the pattern here: the other categories average {sum(others) / len(others):.1f} "
                f"and Sustain is {sustain}. This area is being tidied, not standardised, and the score will "
                "fall back between audits unless the sustaining mechanism gets the attention."
            )
        return base + f" Sustain is {sustain}/{MAX_PER_CATEGORY} here, which is the one to fix first."
    if len(artifact.rounds) < 2:
        return base + " With a single round there is no trend, and a 5S total means much more as a direction than as a grade."
    return base + " With Sustain holding up, the gains from the other four have somewhere to live."


def build_report_card(artifact: FiveSArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    current = latest_round(artifact)
    scores = scores_by_category(current)

    items.append(
        (
            "neutral" if len(artifact.rounds) > 1 else "flag",
            f"{len(artifact.rounds)} audit round(s) recorded."
            + ("" if len(artifact.rounds) > 1 else " A single round is a snapshot; 5S is judged on trend."),
        )
    )

    missing = [c for c in CATEGORY_ORDER if c not in scores]
    if missing:
        items.append(
            (
                "flag",
                f"{len(missing)} category/categories unscored in the latest round: "
                f"{', '.join(CATEGORY_LABELS[c] for c in missing)}. The total is out of "
                f"{len(scores) * MAX_PER_CATEGORY}, not {MAX_TOTAL}.",
            )
        )

    weak = [(c, s) for c, s in scores.items() if s <= WEAK_SCORE]
    if weak:
        worst = min(weak, key=lambda pair: pair[1])
        items.append(
            (
                "flag",
                f"Weakest: {CATEGORY_LABELS.get(worst[0], worst[0])} at {worst[1]}/{MAX_PER_CATEGORY}"
                + (f", with {len(weak) - 1} other category/categories also at or below {WEAK_SCORE}." if len(weak) > 1 else "."),
            )
        )
    else:
        items.append(("pass", f"Every category scores above {WEAK_SCORE}/{MAX_PER_CATEGORY}."))

    sustain = scores.get("sustain")
    if sustain is not None:
        # Three-way, and trend-aware. A flat pass/fail split at "above 3"
        # called a mid-scale 3 a FAILURE on an area that had just climbed
        # 10 -> 15 -> 18 with Sustain itself rising 2 -> 3. A verdict that
        # harsh on visible progress is how a tool teaches people to ignore
        # its verdicts.
        history = sorted(artifact.rounds, key=lambda r: r.date)
        previous_sustain = (
            scores_by_category(history[-2]).get("sustain") if len(history) >= 2 else None
        )
        movement = ""
        if previous_sustain is not None and previous_sustain != sustain:
            movement = f" It has moved from {previous_sustain} to {sustain} since {history[-2].date}."

        if sustain >= MAX_PER_CATEGORY - 1:
            tone: rt.Tone = "pass"
        elif sustain <= WEAK_SCORE - 1:
            tone = "fail"
        else:
            tone = "flag"
        items.append(
            (
                tone,
                f"Sustain is {sustain}/{MAX_PER_CATEGORY} — the only category that measures whether the other "
                f"four hold without supervision.{movement}",
            )
        )

    action = (current.improvement_action or "").strip()
    if not action:
        items.append(
            (
                "fail",
                "The latest round records no improvement action. An audit that scores an area and changes "
                "nothing is measurement for its own sake.",
            )
        )
    elif not (current.improvement_action_owner or "").strip():
        items.append(("flag", f"An improvement action is recorded with no owner: \"{action}\""))
    else:
        items.append(("pass", f"Improvement action owned by {current.improvement_action_owner.strip()}: \"{action}\""))

    if artifact.schedule is None:
        items.append(
            (
                "flag",
                "No recurrence schedule. 5S without a next date is a one-off tidy — the score decays and "
                "nobody is booked to notice.",
            )
        )
    else:
        due = getattr(artifact.schedule, "next_round_due", None)
        items.append(
            (
                "pass",
                f"Recurring: {artifact.schedule.cadence_note.strip()}"
                + (f", next round due {due}." if due else "."),
            )
        )

    if current.photos:
        items.append(("pass", f"{len(current.photos)} photo(s) attached to the latest round."))

    return items


def build_scores_table(artifact: FiveSArtifact, styles: dict, content_width: float) -> Any:
    """Latest round's per-category scores, with every earlier round's total
    alongside so the direction is visible without a separate chart."""
    from reportlab.platypus import Paragraph, Table

    rounds = sorted(artifact.rounds, key=lambda r: r.date)
    # Keep the table readable: the most recent handful is what a reader
    # uses, and the full history is in the project record.
    shown = rounds[-4:]
    header = [Paragraph(esc("Category"), styles["table_header"])] + [
        Paragraph(esc(f"{r.date}"), styles["table_header"]) for r in shown
    ]
    body = []
    for category in CATEGORY_ORDER:
        row = [Paragraph(esc(CATEGORY_LABELS[category]), styles["table_cell"])]
        for round_ in shown:
            score = scores_by_category(round_).get(category)
            row.append(Paragraph("—" if score is None else f"{score}/{MAX_PER_CATEGORY}", styles["table_cell"]))
        body.append(row)
    total_row = [Paragraph(esc("Total"), styles["table_cell"])] + [
        Paragraph(f"{total_for(r)}/{MAX_TOTAL}", styles["table_cell"]) for r in shown
    ]
    body.append(total_row)

    label_frac = 0.28
    rest = (1 - label_frac) / max(len(shown), 1)
    fracs = [label_frac] + [rest] * len(shown)
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: FiveSArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    from reportlab.platypus import Paragraph

    styles = rt.report_styles()
    verdict_text, tone = build_verdict(artifact)
    current = latest_round(artifact)

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

    summary: list[tuple[str, str]] = [
        ("Area", current.area.strip()),
        ("Latest round", current.date),
        ("Score", f"{total_for(current)}/{MAX_TOTAL}"),
        ("Rounds recorded", str(len(artifact.rounds))),
    ]
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("SCORES BY CATEGORY", styles))
    story.append(build_scores_table(artifact, styles, content_width))

    notes = [(s.category, s.note.strip()) for s in current.scores if s.note.strip()]
    if notes:
        story.append(_label("AUDITOR NOTES, LATEST ROUND", styles))
        for category, note in notes:
            story.append(
                Paragraph(esc(f"{CATEGORY_LABELS.get(category, category)}: {note}"), styles["card_item"])
            )

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
