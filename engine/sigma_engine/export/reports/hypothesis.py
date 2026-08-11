"""T-17 Hypothesis Test Report — Summary, Diagnostic, Report Card.

Structured after Minitab's Assistant output because that structure is
genuinely good and genuinely hard to improve on: the answer in plain
language first, the assumption checks second, the warnings third. A reader
who only ever looks at the top of the page still gets a true statement.

Everything printed here already exists in the artifact. The engine's
hypothesis runner produces a `plain_language` block precisely so no layer
above it has to paraphrase a p-value -- and paraphrasing is where honest
statistics usually goes wrong. This module renders that block; it does not
compose new claims from the numbers.

The one thing this report will never say is "no difference". A
non-significant result means no difference was DETECTED at this sample
size, which is a statement about the study, not the world. That wording
discipline is enforced in the engine (hypothesis_common's plain-language
builders) and inherited here.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.hypothesis import HypothesisRunArtifact
from .. import report_theme as rt
from ..charter_pdf_common import fmt_number, kv_table

TOOL_ID = "T-17"
TOOL_TITLE = "Hypothesis Test"


def build_verdict(artifact: HypothesisRunArtifact) -> tuple[str, rt.Tone]:
    if artifact.refused:
        return (
            "The engine declined to run a test on this data — see the report card for why.",
            "neutral",
        )
    computed = artifact.result.value if artifact.result else None
    if computed is None:
        return ("No test run yet.", "neutral")
    return (computed.plain_language.comparison_summary, "pass" if computed.significant else "neutral")


def build_meaning(artifact: HypothesisRunArtifact) -> str:
    """Zone 3 is the engine's own p-value explanation plus its practical-
    significance prompt -- rendered, never rewritten."""
    computed = artifact.result.value if artifact.result else None
    if computed is None:
        return (
            "A hypothesis test asks whether a difference this large could plausibly have turned up "
            "by chance alone. It cannot tell you whether the difference is big enough to care about."
        )
    plain = computed.plain_language
    return f"{plain.p_value_meaning} {plain.effect_size_in_words} {plain.practical_significance_prompt}"


def build_diagnostic_rows(artifact: HypothesisRunArtifact) -> list[tuple[str, str]]:
    """The Diagnostic block: what was run, on what, and how it was chosen."""
    rows: list[tuple[str, str]] = []
    routing = artifact.routing
    if routing is not None:
        rows.append(("Test selected", routing.route.replace("_", " ")))
        rows.append(("Comparison type", routing.comparison_type.replace("_", " ")))
        if routing.switch_reason:
            rows.append(("Why switched", routing.switch_reason))
    computed = artifact.result.value if artifact.result else None
    if computed is not None:
        rows.append((computed.statistic_name, fmt_number(computed.statistic)))
        if computed.df is not None:
            rows.append(("Degrees of freedom", fmt_number(computed.df)))
        rows.append(("p-value", f"{computed.p_value:.4g}"))
        rows.append(("Alpha", fmt_number(computed.alpha)))
        rows.append((computed.effect_size_name, fmt_number(computed.effect_size_value)))
        if computed.effect_size_ci is not None:
            low, high = computed.effect_size_ci
            rows.append(("Effect size CI", f"{fmt_number(low)} to {fmt_number(high)}"))
        for group in computed.groups:
            label = getattr(group, "label", "group")
            n = getattr(group, "n", None)
            if n is not None:
                rows.append((f"n — {label}", str(n)))
    return rows


def build_report_card(artifact: HypothesisRunArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    computed = artifact.result.value if artifact.result else None

    if artifact.refused:
        items.append(("fail", "The engine refused to run a test rather than produce a misleading one."))

    if computed is not None:
        for assumption in computed.assumptions_checked:
            items.append(("pass", f"Assumption checked: {assumption}"))
        for warning in computed.warnings:
            items.append(("flag", warning))
        if computed.equal_shape_caveat:
            items.append(("flag", computed.equal_shape_caveat))
        if computed.exit13 is not None:
            items.append(("flag", "A named exit was raised on this test — see the tool screen."))
        if not computed.significant:
            items.append(
                (
                    "neutral",
                    "Not significant means no difference was DETECTED at this sample size — not that "
                    "there is no difference. A larger study could still find one.",
                )
            )

    if not artifact.declared_primary:
        items.append(
            (
                "flag",
                "This was not declared the primary test. Running several tests and reporting the one "
                "that came out significant inflates the false-positive rate.",
            )
        )

    routing = artifact.routing
    if routing is not None and routing.recommend_nonparametric:
        items.append(("flag", "The data shape suggested a non-parametric test."))
    return items


def build_story(
    *,
    artifact: HypothesisRunArtifact,
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
    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))

    diagnostic = build_diagnostic_rows(artifact)
    if diagnostic:
        story.append(
            rt.keep(
                [
                    _label("DIAGNOSTIC — what was run", styles),
                    kv_table(diagnostic, styles, content_width, label_frac=0.34),
                ]
            )
        )

    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
