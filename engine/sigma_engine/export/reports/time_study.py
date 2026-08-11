"""T-09 Time Study Report — where the time actually goes.

A time study's output is usually quoted as one number: the cycle time. That
number is the least interesting thing it produces. What decides where to
spend effort is the split across elements and the spread within them — an
element averaging 40 seconds with a range of 15 to 90 is a different problem
from one that takes 40 seconds every time, and the average hides which you
have.

SPREAD IS PRINTED BESIDE EVERY MEAN. Median and range travel with the
average for exactly that reason. An element whose median sits well below
its mean is being dragged by occasional long cycles, and that is a
different fix from a slow element.

OUTLIERS ARE SHOWN, NOT REMOVED. A long cycle is usually the most
informative observation in the study — it is the interruption, the missing
part, the question to the supervisor. The engine flags them by fence rule;
this page counts them and leaves them in the arithmetic, because silently
trimming them turns a study of the real process into a study of the good
days.

WORK SAMPLING ANSWERS A DIFFERENT QUESTION and prints separately. Cycle
timing says how long the work takes; sampling says how much of the day is
spent doing it. A process can have excellent cycle times and 40% waiting.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.time_study import TimeStudyArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-09"
TOOL_TITLE = "Time Study"

SAMPLING_LABELS = {
    "working": "Working",
    "waiting": "Waiting",
    "moving": "Moving",
    "other": "Other",
}
# A coefficient of variation above this means the element's average is a
# poor description of any single cycle.
HIGH_VARIATION_CV = 0.30


def element_stats(artifact: TimeStudyArtifact) -> list[Any]:
    return list(artifact.element_stats.value) if artifact.element_stats else []


def live_cycles(artifact: TimeStudyArtifact) -> list[Any]:
    return [c for c in artifact.cycles if c.deleted is None]


def total_cycle_seconds(artifact: TimeStudyArtifact) -> float:
    """Sum of element means — the average time for one pass through all
    elements. Not the mean of per-cycle totals, which would silently drop
    any cycle missing an element."""
    return sum(s.descriptive.mean for s in element_stats(artifact) if s.descriptive is not None)


def fmt_seconds(value: float) -> str:
    if value >= 90:
        return f"{value / 60:.1f} min"
    return f"{value:.1f} s"


def build_verdict(artifact: TimeStudyArtifact) -> tuple[str, rt.Tone]:
    stats = element_stats(artifact)
    cycles = live_cycles(artifact)
    if not stats or not cycles:
        sampling = artifact.work_sampling_summary.value if artifact.work_sampling_summary else None
        if sampling is not None and sampling.total_observations:
            return (f"Work sampling only — {sampling.total_observations} observation(s), no timed cycles.", "neutral")
        return ("No timed cycles recorded yet.", "neutral")

    total = total_cycle_seconds(artifact)
    slowest = max(
        (s for s in stats if s.descriptive is not None), key=lambda s: s.descriptive.mean, default=None
    )
    tail = ""
    if slowest is not None and total > 0:
        share = slowest.descriptive.mean / total * 100
        tail = f" Longest element: {slowest.element_name.strip()} at {fmt_seconds(slowest.descriptive.mean)} ({share:.0f}% of the cycle)."
    return (
        f"{fmt_seconds(total)} per cycle across {len(stats)} element(s), from {len(cycles)} timed cycle(s).{tail}",
        "neutral",
    )


def build_meaning(artifact: TimeStudyArtifact) -> str:
    stats = [s for s in element_stats(artifact) if s.descriptive is not None]
    if not stats:
        return (
            "A time study measures how long each element of the work takes, so effort goes to the element "
            "that actually costs time rather than the one that feels slowest."
        )

    variable = [
        s for s in stats if s.descriptive.mean > 0 and (s.descriptive.sd / s.descriptive.mean) > HIGH_VARIATION_CV
    ]
    base = (
        "The split matters more than the total. Effort spent on an element that is 8% of the cycle cannot "
        "produce more than an 8% improvement, however satisfying the fix feels."
    )
    if variable:
        worst = max(variable, key=lambda s: s.descriptive.sd / s.descriptive.mean)
        cv = worst.descriptive.sd / worst.descriptive.mean
        base += (
            f" {len(variable)} element(s) vary more than {HIGH_VARIATION_CV:.0%} around their own average — "
            f"the widest is {worst.element_name.strip()} at {cv:.0%}, ranging "
            f"{fmt_seconds(worst.descriptive.min)} to {fmt_seconds(worst.descriptive.max)}. Inconsistency that "
            "wide is usually a method or interruption problem, and standardising it often buys more than "
            "speeding anything up."
        )
    else:
        base += " Every element here is consistent enough that its average describes a typical cycle well."
    return base


def build_report_card(artifact: TimeStudyArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    stats = element_stats(artifact)
    cycles = live_cycles(artifact)
    removed = [c for c in artifact.cycles if c.deleted is not None]

    items.append(("neutral", f"{len(cycles)} timed cycle(s) across {len(stats)} element(s)."))

    thin = [s for s in stats if s.below_recommended_cycles]
    if thin:
        items.append(
            (
                "flag",
                f"{len(thin)} element(s) are below the recommended cycle count: "
                + "; ".join(f"{s.element_name.strip()} (n={s.n})" for s in thin[:3])
                + ". Their averages will move with the next few observations.",
            )
        )
    else:
        items.append(("pass", "Every element has enough cycles for its average to be worth quoting."))

    flagged = [(s, s.outliers) for s in stats if s.outliers]
    if flagged:
        total_outliers = sum(len(o) for _, o in flagged)
        example = flagged[0][1][0]
        items.append(
            (
                "flag",
                f"{total_outliers} outlying cycle(s) flagged across {len(flagged)} element(s) — e.g. cycle "
                f"{example.cycle_number} at {fmt_seconds(example.seconds)} ({example.reason}). They are left "
                "in the arithmetic: a long cycle is usually the most informative observation in the study.",
            )
        )
    else:
        items.append(("pass", "No cycles fall outside the outlier fences."))

    if removed:
        reasons = "; ".join(f"cycle {c.cycle_number}: {(c.deleted.reason or '').strip()}" for c in removed[:3])
        items.append(("flag", f"{len(removed)} cycle(s) excluded with a logged reason ({reasons})."))
    else:
        items.append(("pass", "No cycles were excluded."))

    no_sd = [s for s in stats if s.descriptive is None]
    if no_sd:
        items.append(
            (
                "neutral",
                f"{len(no_sd)} element(s) have fewer than 2 observations, so no spread is computed for them — "
                "not estimated, simply absent.",
            )
        )

    sampling = artifact.work_sampling_summary.value if artifact.work_sampling_summary else None
    if sampling is not None and sampling.total_observations:
        working = next((s for s in sampling.shares if s.category == "working"), None)
        if working is not None:
            items.append(
                (
                    "flag" if working.share < 0.6 else "pass",
                    f"Work sampling: {working.share:.0%} of {sampling.total_observations} observation(s) were "
                    "working. Cycle times describe the work; this describes how much of the day reaches it.",
                )
            )

    items.append(
        (
            "neutral",
            "Cycle total is the sum of element means, not the mean of cycle totals — so a cycle missing one "
            "element cannot quietly shorten it.",
        )
    )
    return items


def build_elements_table(artifact: TimeStudyArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    total = total_cycle_seconds(artifact)
    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("Element", "n", "Mean", "Median", "Range", "Share", "Outliers")
    ]
    body = []
    for stat in element_stats(artifact):
        d = stat.descriptive
        share = f"{d.mean / total * 100:.0f}%" if (d is not None and total > 0) else "—"
        body.append(
            [
                Paragraph(esc(rt.clip(stat.element_name, 45)), styles["table_cell"]),
                Paragraph(str(stat.n), styles["table_cell"]),
                Paragraph(fmt_seconds(d.mean) if d else "—", styles["table_cell"]),
                Paragraph(fmt_seconds(d.median) if d else "—", styles["table_cell"]),
                Paragraph(f"{fmt_seconds(d.min)}–{fmt_seconds(d.max)}" if d else "—", styles["table_cell"]),
                Paragraph(share, styles["table_cell"]),
                Paragraph(str(len(stat.outliers)) if stat.outliers else "—", styles["table_cell"]),
            ]
        )
    fracs = [0.28, 0.07, 0.13, 0.13, 0.20, 0.10, 0.09]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_sampling_table(artifact: TimeStudyArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    sampling = artifact.work_sampling_summary.value
    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Category", "Observations", "Share")]
    body = [
        [
            Paragraph(esc(SAMPLING_LABELS.get(s.category, s.category)), styles["table_cell"]),
            Paragraph(f"{s.count:,}", styles["table_cell"]),
            Paragraph(f"{s.share:.1%}", styles["table_cell"]),
        ]
        for s in sampling.shares
    ]
    fracs = [0.48, 0.26, 0.26]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: TimeStudyArtifact,
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

    stats = element_stats(artifact)
    summary: list[tuple[str, str]] = []
    if stats:
        summary.append(("Cycle time", fmt_seconds(total_cycle_seconds(artifact))))
        summary.append(("Elements", str(len(stats))))
        summary.append(("Cycles timed", str(len(live_cycles(artifact)))))
    sampling = artifact.work_sampling_summary.value if artifact.work_sampling_summary else None
    if sampling is not None and sampling.total_observations:
        summary.append(("Sampling observations", f"{sampling.total_observations:,}"))
    if summary:
        story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    if stats:
        story.append(_label("TIME BY ELEMENT", styles))
        story.append(build_elements_table(artifact, styles, content_width))

    if sampling is not None and sampling.total_observations:
        story.append(_label("WORK SAMPLING — HOW THE DAY IS SPENT", styles))
        story.append(build_sampling_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
