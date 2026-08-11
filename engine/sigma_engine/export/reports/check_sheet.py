"""T-08 Check Sheet Report — the tally, and what the tally cannot see.

A check sheet is the humblest tool in the suite and the one most often
over-read. It produces counts of what somebody wrote down, and the gap
between that and "what happens" is where projects go wrong. So this page
prints the tally plainly and spends its report card on the gap.

DELETED ENTRIES ARE COUNTED AND SUMMARISED, NOT ERASED. Every deletion in
this engine carries a logged reason, and a tally that quietly excludes
them is a tally a reader cannot audit. The count of exclusions prints
whether or not there were any, so a reader learns the number is zero
rather than assuming it.

THE TOP CATEGORY IS NOT THE BIGGEST PROBLEM. It is the most-recorded
category, which is a different claim: what gets tallied depends on what
the sheet made easy to tally, who was holding it, and when. The page says
so beside the ranking rather than leaving the reader to make the leap.

STRATA ARE SHOWN WHEN THEY WERE COLLECTED. A tally split by shift or line
answers a question the total never can, and collecting strata and then
never looking at them is the commonest waste in a check sheet.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ...artifacts.check_sheet import CheckSheetArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-08"
TOOL_TITLE = "Check Sheet Tally"

# A tally this thin cannot support a Pareto reading; below it the page
# says so rather than ranking noise.
THIN_TOTAL = 20


def live_entries(artifact: CheckSheetArtifact) -> list[Any]:
    return [e for e in artifact.entries if e.deleted is None]


def deleted_entries(artifact: CheckSheetArtifact) -> list[Any]:
    return [e for e in artifact.entries if e.deleted is not None]


def tally(artifact: CheckSheetArtifact) -> list[tuple[str, int]]:
    """(label, count) descending. Counts respect each entry's `count`
    field — a tap is 1, a batch entry may be more — and exclude deletions."""
    labels = {c.category_id: c.label for c in artifact.categories}
    counts: Counter[str] = Counter()
    for entry in live_entries(artifact):
        counts[entry.category_id] += entry.count
    # Categories with no entries still print: a zero is a finding, and
    # dropping it makes the sheet look like it only ever had four options.
    for category in artifact.categories:
        counts.setdefault(category.category_id, 0)
    return sorted(
        ((labels.get(cid, cid), n) for cid, n in counts.items()),
        key=lambda pair: (-pair[1], pair[0].lower()),
    )


def total_count(artifact: CheckSheetArtifact) -> int:
    return sum(e.count for e in live_entries(artifact))


def build_verdict(artifact: CheckSheetArtifact) -> tuple[str, rt.Tone]:
    total = total_count(artifact)
    rows = tally(artifact)
    if total == 0:
        return ("Nothing tallied yet.", "neutral")
    top_label, top_count = rows[0]
    share = top_count / total * 100
    return (
        f"{total:,} observation(s) across {len(artifact.categories)} category/categories. "
        f"Most recorded: {top_label} — {top_count:,} ({share:.0f}%).",
        "neutral",
    )


def build_meaning(artifact: CheckSheetArtifact) -> str:
    total = total_count(artifact)
    rows = tally(artifact)
    base = (
        "This counts what was written down, which is not the same as what happened. A check sheet records "
        "the events somebody was present for, willing to log, and able to categorise — so the ranking below "
        "is the most-recorded category, not necessarily the biggest problem."
    )
    if total < THIN_TOTAL:
        return (
            base
            + f" With {total} observation(s) this is too thin to rank at all: one more tally could reorder it. "
            "Treat it as a sense of what is out there, and collect more before deciding anything."
        )
    if len(rows) >= 2 and rows[0][1] > 0:
        share = rows[0][1] / total * 100
        if share >= 50:
            base += (
                f" One category carries {share:.0f}% of the tally, which is a strong enough concentration to "
                "be worth attacking on its own."
            )
        elif share <= 100 / max(len(rows), 1) * 1.3:
            base += (
                " No category dominates — the counts are close to even, which usually means the categories "
                "are cutting the problem the wrong way rather than that everything is equally broken."
            )
    return base


def build_report_card(artifact: CheckSheetArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    total = total_count(artifact)
    removed = deleted_entries(artifact)

    items.append(
        (
            "neutral" if total >= THIN_TOTAL else "flag",
            f"{total:,} observation(s) counted."
            + ("" if total >= THIN_TOTAL else f" Below {THIN_TOTAL} the ranking is not stable."),
        )
    )

    if removed:
        reasons = Counter((e.deleted.reason or "").strip() for e in removed)
        top_reason, top_n = reasons.most_common(1)[0]
        items.append(
            (
                "flag",
                f"{len(removed)} entry/entries excluded from this tally, each with a logged reason "
                f"(most common: \"{top_reason}\" x{top_n}). They remain in the record and can be reviewed.",
            )
        )
    else:
        items.append(("pass", "No entries were excluded from this tally."))

    empty = [label for label, n in tally(artifact) if n == 0]
    if empty:
        items.append(
            (
                "neutral",
                f"{len(empty)} category/categories were never tallied: {', '.join(empty[:4])}. Either they do "
                "not occur, or the sheet made them hard to record.",
            )
        )

    if artifact.strata_fields:
        used = sum(1 for e in live_entries(artifact) if e.strata)
        if used == 0:
            items.append(
                (
                    "flag",
                    f"{len(artifact.strata_fields)} strata field(s) were defined and never filled in. Strata "
                    "collected but not recorded cannot answer the question they were added for.",
                )
            )
        else:
            items.append(
                (
                    "pass",
                    f"{used:,} of {len(live_entries(artifact)):,} entries carry strata — the tally can be split "
                    f"by {', '.join(f.label for f in artifact.strata_fields)}.",
                )
            )
    else:
        items.append(
            (
                "neutral",
                "No strata were collected. A total that cannot be split by shift, line or person answers "
                "fewer questions than it looks like it does.",
            )
        )

    items.append(
        (
            "neutral",
            "Counts are the sum of each entry's own count, so a batch entry of 5 counts as 5, not as 1.",
        )
    )
    return items


def build_tally_table(artifact: CheckSheetArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    total = total_count(artifact)
    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Category", "Count", "Share", "Cumulative")]
    body = []
    running = 0
    for label, count in tally(artifact):
        running += count
        body.append(
            [
                Paragraph(esc(rt.clip(label, 70)), styles["table_cell"]),
                Paragraph(f"{count:,}", styles["table_cell"]),
                Paragraph(f"{(count / total * 100):.1f}%" if total else "—", styles["table_cell"]),
                Paragraph(f"{(running / total * 100):.1f}%" if total else "—", styles["table_cell"]),
            ]
        )
    fracs = [0.46, 0.16, 0.19, 0.19]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: CheckSheetArtifact,
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
        tool_title=TOOL_TITLE,
        version=version,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)

    summary: list[tuple[str, str]] = [
        ("Observations", f"{total_count(artifact):,}"),
        ("Categories", str(len(artifact.categories))),
        ("Excluded", f"{len(deleted_entries(artifact))} (with logged reasons)"),
    ]
    if artifact.strata_fields:
        summary.append(("Strata collected", ", ".join(f.label for f in artifact.strata_fields)))
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("TALLY", styles))
    story.append(build_tally_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
