"""T-35 Gage R&R Report.

The page a quality engineer expects to see, and the one that decides
whether anything else in the project is worth reading. If the measurement
system fails here, every capability index and every before/after claim
downstream is partly a measurement of the gauge.

Three things print that a bare %GRR does not say:

WHICH BASIS. %GRR of study variation and %GRR of tolerance answer different
questions -- "can this gauge see the process vary" versus "can this gauge
police the spec" -- and a gauge can pass one and fail the other. The basis
is named beside the number every time.

DISTINCT CATEGORIES. The number of non-overlapping groups the gauge can
actually sort parts into. Below five it is a sorting tool rather than a
measuring one, and that is invisible in a %GRR that looks merely marginal.

WHAT THE STUDY COULD NOT SEE. Parts that do not span real production
understate part-to-part variation, which inflates %GRR; a clamped variance
component means the estimator went negative and was floored. Both print, so
a study that barely resolved anything cannot read as clean.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.gage_rr import GageRRArtifact
from ...stats import gage_rr as gage_rr_mod
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, fmt_number, kv_table

TOOL_ID = "T-35"
TOOL_TITLE = "Gage R&R — full crossed study"

_TONE: dict[str, rt.Tone] = {"acceptable": "pass", "marginal": "flag", "unacceptable": "fail"}

# Rows printed in the components table, in the order a reader works down
# them: the two halves of measurement error, their total, then what the
# study was trying to see.
COMPONENT_ORDER = (
    ("repeatability", "Repeatability (equipment)"),
    ("reproducibility", "Reproducibility (operators)"),
    ("operator", "  — operator"),
    ("operator_x_part", "  — operator x part"),
    ("gage_rr", "Total Gage R&R"),
    ("part_to_part", "Part-to-part"),
    ("total_variation", "Total variation"),
)


def _basis_words(result: gage_rr_mod.GageRRResult) -> str:
    return "of tolerance" if result.basis == "tolerance" else "of study variation"


def build_verdict(artifact: GageRRArtifact) -> tuple[str, rt.Tone]:
    if artifact.design_error:
        return (f"This study cannot be computed: {artifact.design_error}", "neutral")
    result = artifact.result
    if result is None:  # pragma: no cover -- design_error covers this
        return ("No study computed yet.", "neutral")

    headline = result.grr_percent_tolerance if result.basis == "tolerance" else result.grr_percent_study_variation
    return (
        f"Gage R&R is {fmt_number(headline)}% {_basis_words(result)} — {result.verdict}. "
        f"{result.number_of_distinct_categories} distinct categories.",
        _TONE.get(result.verdict, "neutral"),
    )


def build_meaning(artifact: GageRRArtifact) -> str:
    result = artifact.result
    if result is None:
        return (
            "A Gage R&R asks how much of the variation you are looking at is the parts and how much is the "
            "measuring. Until it is answered, every number measured with this gauge is partly unknown."
        )
    if result.verdict == "unacceptable":
        return (
            "Most of what this gauge reports is the gauge, not the parts. Any capability index, control "
            "chart or before/after comparison built on these measurements is measuring the measurement "
            "system as much as the process — fix the gauge, the method, or the operator definitions "
            "before spending effort on the process itself."
        )
    if result.number_of_distinct_categories < gage_rr_mod.NDC_MINIMUM:
        return (
            "The percentage looks tolerable, but the gauge can only separate these parts into "
            f"{result.number_of_distinct_categories} distinct group(s). That is enough to sort pass from "
            "fail and not enough to measure improvement — a change smaller than one category is invisible."
        )
    return (
        "The measurement system can see the differences this project cares about. That is a "
        "precondition for everything downstream, not an achievement in itself: it means the numbers "
        "you collect next are about the process."
    )


def build_report_card(artifact: GageRRArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    result = artifact.result
    if result is None:
        return [("fail", artifact.design_error or "No study computed.")]

    items.append(
        (
            "pass" if result.parts >= 10 else "flag",
            f"{result.parts} parts, {result.operators} operators, {result.replicates} repeats per cell.",
        )
    )
    # The single most common way a Gage R&R flatters a gauge, and it is
    # invisible in the arithmetic: the study can only compare the gauge
    # against the parts it was given.
    items.append(
        (
            "neutral",
            "These percentages are ratios against the part-to-part variation IN THIS STUDY. If the parts "
            "did not span the real range of production, part-to-part is understated and %GRR is "
            "correspondingly overstated — no arithmetic here can detect that.",
        )
    )

    if result.number_of_distinct_categories < gage_rr_mod.NDC_MINIMUM:
        items.append(
            (
                "fail",
                f"{result.number_of_distinct_categories} distinct categories — below {gage_rr_mod.NDC_MINIMUM} "
                "this gauge sorts rather than measures.",
            )
        )
    else:
        items.append(("pass", f"{result.number_of_distinct_categories} distinct categories."))

    if result.basis == "study_variation":
        items.append(
            (
                "flag",
                "No tolerance was given, so this is %GRR of study variation only. It says whether the gauge "
                "can see the process vary, not whether it can police a specification.",
            )
        )
    else:
        items.append(("pass", "Judged against tolerance, which is what a spec'd characteristic asks."))

    if result.interaction_pooled:
        items.append(("pass", "Operator-by-part interaction was not significant and was pooled into repeatability."))
    else:
        items.append(
            (
                "flag",
                "Operator-by-part interaction was kept in the model — some operators measure some parts "
                "differently than others do. Worth understanding before training is blamed.",
            )
        )

    for component in result.components:
        if component.clamped_from_negative:
            items.append(
                (
                    "flag",
                    f"The {component.name.replace('_', ' ')} estimate came out negative and was floored at zero — "
                    "that component is smaller than this study can resolve, not absent.",
                )
            )

    for warning in result.warnings:
        items.append(("flag", warning))

    items.append(
        (
            "neutral",
            "Percentages are computed on standard deviations, not variances, which is why the component "
            "column does not add up to 100.",
        )
    )
    return items


def build_components_table(result: gage_rr_mod.GageRRResult, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    by_name = {c.name: c for c in result.components}
    has_tolerance = result.basis == "tolerance"
    header_labels = ["Source", "Variance", "Std dev", "% study var"]
    if has_tolerance:
        header_labels.append("% tolerance")
    header = [Paragraph(esc(h), styles["table_header"]) for h in header_labels]

    body = []
    for key, label in COMPONENT_ORDER:
        component = by_name.get(key)
        if component is None:
            continue
        row = [
            Paragraph(esc(label), styles["table_cell"]),
            Paragraph(fmt_number(component.variance), styles["table_cell"]),
            Paragraph(fmt_number(component.std_dev), styles["table_cell"]),
            Paragraph(f"{fmt_number(component.percent_study_variation)}%", styles["table_cell"]),
        ]
        if has_tolerance:
            pct = component.percent_tolerance
            row.append(Paragraph(f"{fmt_number(pct)}%" if pct is not None else "—", styles["table_cell"]))
        body.append(row)

    fracs = [0.30, 0.18, 0.18, 0.17, 0.17] if has_tolerance else [0.37, 0.21, 0.21, 0.21]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_anova_table(result: gage_rr_mod.GageRRResult, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [Paragraph(esc(h), styles["table_header"]) for h in ("Source", "DF", "SS", "MS", "F", "p")]
    body = []
    for row in result.anova:
        body.append(
            [
                Paragraph(esc(row.source.replace("_", " ")), styles["table_cell"]),
                Paragraph(str(row.df), styles["table_cell"]),
                Paragraph(fmt_number(row.ss), styles["table_cell"]),
                Paragraph(fmt_number(row.ms), styles["table_cell"]),
                Paragraph(fmt_number(row.f_statistic) if row.f_statistic is not None else "—", styles["table_cell"]),
                Paragraph(f"{row.p_value:.4g}" if row.p_value is not None else "—", styles["table_cell"]),
            ]
        )
    fracs = [0.28, 0.10, 0.18, 0.18, 0.13, 0.13]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: GageRRArtifact,
    project_name: str,
    version: int,
    chart_png: bytes | None = None,
    chart_unavailable_reason: str | None = None,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    verdict_text, tone = build_verdict(artifact)

    story: list[Any] = []
    title = TOOL_TITLE if not artifact.gauge_name else f"{TOOL_TITLE} — {artifact.gauge_name}"
    story += rt.header(
        project_name=project_name,
        tool_id=TOOL_ID,
        tool_title=title,
        version=version,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)
    if chart_png or chart_unavailable_reason:
        story += rt.chart(
            chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
        )

    result = artifact.result
    if result is not None:
        summary: list[tuple[str, str]] = [
            ("Study", f"{result.parts} parts x {result.operators} operators x {result.replicates} repeats"),
            ("%GRR", f"{fmt_number(result.grr_percent_study_variation)}% of study variation"),
        ]
        if result.grr_percent_tolerance is not None:
            summary.append(("%GRR of tolerance", f"{fmt_number(result.grr_percent_tolerance)}%"))
        summary.append(("Distinct categories", str(result.number_of_distinct_categories)))
        summary.append(("Model", "interaction pooled" if result.interaction_pooled else "interaction retained"))
        story.append(kv_table(summary, styles, content_width, label_frac=0.32))

        story.append(_label("VARIANCE COMPONENTS", styles))
        story.append(build_components_table(result, styles, content_width))
        story.append(_label("ANOVA", styles))
        story.append(build_anova_table(result, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
