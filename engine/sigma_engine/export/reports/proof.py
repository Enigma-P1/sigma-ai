"""T-20 Before/After Proof Report.

The page a sponsor actually wants, and the one most likely to overstate.

Three disciplines are printed rather than assumed:

GAP ARITHMETIC, not a percentage. "40% improvement" hides whether the goal
was met. The engine computes the original gap, how much was recovered, and
what remains against the charter's own target, and all three print.

THE THRESHOLD AS DECLARED. The pilot named its success line before the data
arrived. Restating it here, in the words it was declared in, is what stops
a near-miss being rounded into a win after the fact.

CONFOUNDERS ALONGSIDE THE RESULT, never below the fold. A busier period, a
seasonal shift, a co-occurring change -- these weaken a claim, and a report
that prints the improvement while omitting them is the standard way
improvement projects mislead. On the Coffee Bar data the app's own
confounder note argues AGAINST its result ("a busier peak lengthens queues,
so this confound biases against the pilot"), which is exactly the tone this
page should carry.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.proof import ProofArtifact
from .. import report_theme as rt
from ..charter_pdf_common import fmt_number, kv_table

TOOL_ID = "T-20"
TOOL_TITLE = "Before / After Proof"


def build_verdict(artifact: ProofArtifact) -> tuple[str, rt.Tone]:
    verdict = artifact.verdict.value if artifact.verdict else None
    gap = artifact.gap.value if artifact.gap else None

    if verdict is None or gap is None:
        return ("No before/after comparison computed yet.", "neutral")

    headline = getattr(verdict, "headline", "") or ""
    if gap.goal_met:
        return (headline or "Threshold met as declared.", "pass")
    return (headline or "Threshold not met.", "flag")


def build_meaning(artifact: ProofArtifact) -> str:
    gap = artifact.gap.value if artifact.gap else None
    if gap is None:
        return (
            "A before/after proof asks whether the change moved the metric the charter promised to "
            "move, by enough, and whether anything else could explain it."
        )
    if gap.goal_met:
        return (
            "The charter's target was reached. Reaching a target is not the same as proving the "
            "change caused it — read the confounders below before treating this as settled, and "
            "hold the gain with a control plan rather than declaring the project over."
        )
    return (
        "The change moved the metric but not far enough to meet the charter's target. That is a "
        "result, not a failure: the honest next step is another pass at the next verified cause, "
        "not restating the goal to match what was achieved."
    )


def build_numbers(artifact: ProofArtifact) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    gap = artifact.gap.value if artifact.gap else None
    if gap is None:
        return rows
    rows.append(("Charter baseline", fmt_number(gap.charter_baseline_value)))
    rows.append(("Charter target", fmt_number(gap.charter_goal_value)))
    rows.append(("After", fmt_number(gap.after_value)))
    rows.append(("Original gap", fmt_number(gap.original_gap)))
    rows.append(("Recovered", f"{fmt_number(gap.recovered)}  ({fmt_number(gap.recovered_pct)}% of the gap)"))
    rows.append(("Remaining", fmt_number(gap.remaining)))
    rows.append(("Direction", gap.direction.replace("_", " ")))
    if gap.loop_verdict:
        rows.append(("Loop verdict", gap.loop_verdict))

    before = artifact.before_baseline
    after = artifact.after_baseline
    if before is not None and after is not None:
        rows.append(("n before / after", f"{before.n} / {after.n}"))
    return rows


def build_report_card(artifact: ProofArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    verdict = artifact.verdict.value if artifact.verdict else None
    gap = artifact.gap.value if artifact.gap else None

    # Confounders first: they are the reason to distrust everything above.
    for note in getattr(verdict, "confounder_notes", None) or []:
        items.append(("flag", note))

    tradeoff = getattr(verdict, "guardrail_tradeoff", None)
    if tradeoff:
        items.append(("fail", f"Guardrail moved the wrong way: {tradeoff}"))

    for side, baseline in (("before", artifact.before_baseline), ("after", artifact.after_baseline)):
        if baseline is None:
            continue
        if baseline.stable is False:
            items.append(("flag", f"The {side} period was not stable — its mean is a summary of a moving process."))
        elif baseline.stable is True:
            items.append(("pass", f"The {side} period was stable."))
        if baseline.n is not None and baseline.n < 30:
            items.append(("flag", f"Only {baseline.n} observations in the {side} period."))

    if gap is not None and gap.goal_met and gap.remaining is not None and abs(gap.remaining) < 0.1 * max(abs(gap.original_gap), 1e-9):
        # Name WHICH target. A pilot is judged against the threshold it
        # declared up front, while the gap arithmetic is against the
        # charter's goal, and those are often different numbers -- on the
        # Coffee Bar data, 5.5 declared versus 5.0 in the charter. An
        # unqualified "narrow margin" next to a verdict quoting the other
        # threshold reads as a contradiction rather than a caution.
        items.append(
            (
                "flag",
                f"The CHARTER goal ({fmt_number(gap.charter_goal_value)}) was cleared by only "
                f"{fmt_number(abs(gap.remaining))} of a {fmt_number(abs(gap.original_gap))} gap — a small "
                "shift either way would change that answer. (The pilot's own declared threshold, quoted "
                "in the verdict above, may be a different number.)",
            )
        )

    if getattr(artifact, "declared_package", None):
        items.append(
            (
                "neutral",
                "This pilot changed several things at once as a declared package, so the result belongs "
                "to the package — not to any single component within it.",
            )
        )

    items.append(
        ("neutral", "A before/after comparison shows association over time. It is not, by itself, proof of cause.")
    )
    return items


def build_story(
    *,
    artifact: ProofArtifact,
    project_name: str,
    version: int,
    chart_png: bytes | None,
    chart_unavailable_reason: str | None,
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
    if chart_png or chart_unavailable_reason:
        story += rt.chart(
            chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
        )
    numbers = build_numbers(artifact)
    if numbers:
        story.append(kv_table(numbers, styles, content_width, label_frac=0.32))
    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story
