"""T-11 Data Collection Plan Report — the two-people test, on paper.

The operational definition is the most under-rated artifact in a project
and the cheapest to get wrong. Its test is simple and this page applies it
literally: could two people, working separately from this sheet alone,
produce the same number? Every field below exists because one of them
routinely differs between two well-meaning observers — where the clock
starts, where it stops, what counts as one unit, what precision to record.

SO THE DEFINITION IS PRINTED AS ITS PARTS, not as a paragraph. A prose
definition reads as complete and hides which part is missing; a labelled
list makes an empty "stops when" impossible to miss.

STRATIFICATION IS A DECISION, NOT A DEFAULT. Collecting without strata is
legitimate and permanent: you cannot split the data afterwards by a factor
you never recorded. So either the factors are listed, or the reason for
not collecting them is — and this page will not let both be blank.

THE PLANNED SAMPLE SIZE PRINTS WITH ITS RATIONALE. A number with no
reasoning behind it is a number somebody guessed, and it is usually the
reason a study lands just short of being able to conclude anything.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.data_collection_plan import DataCollectionPlanArtifact
from .. import report_theme as rt
from ..charter_pdf_common import esc, kv_table

TOOL_ID = "T-11"
TOOL_TITLE = "Data Collection Plan"

# The operational-definition fields, in the order a reader checks them, with
# the question each one answers. Labels rather than field names: the page is
# read by whoever collects the data, not by whoever wrote the schema.
DEFINITION_FIELDS = (
    ("what_measured", "What is measured"),
    ("how_instrument", "Measured with"),
    ("precision_unit", "Recorded to"),
    ("starts_when", "The clock starts when"),
    ("stops_when", "The clock stops when"),
)


def missing_definition_fields(artifact: DataCollectionPlanArtifact) -> list[str]:
    definition = artifact.operational_definition
    return [label for field, label in DEFINITION_FIELDS if not (getattr(definition, field, "") or "").strip()]


def build_verdict(artifact: DataCollectionPlanArtifact) -> tuple[str, rt.Tone]:
    missing = missing_definition_fields(artifact)
    metric = (artifact.metric_name or "").strip() or "an unnamed metric"
    if missing:
        return (
            f"The operational definition for {metric} is incomplete — missing: {', '.join(missing).lower()}. "
            "Two people following this sheet would not produce the same number.",
            "fail",
        )
    if not artifact.operational_definition.two_people_confirmed:
        return (
            f"{metric} is fully defined on paper, but the two-people test has not been run.",
            "flag",
        )
    return (f"{metric} is defined, and two people confirmed they measure it the same way.", "pass")


def build_meaning(artifact: DataCollectionPlanArtifact) -> str:
    missing = missing_definition_fields(artifact)
    base = (
        "Everything downstream inherits this. A baseline, a capability index and a before/after claim are all "
        "just this definition applied repeatedly — so an ambiguity here does not stay here, it becomes "
        "variation in the data that looks exactly like process variation and cannot be told apart from it "
        "later."
    )
    if missing:
        return (
            base
            + f" With {len(missing)} part(s) of the definition still open, different collectors will resolve "
            "them differently and nobody will know it happened."
        )
    if not artifact.stratification_factors and not (artifact.no_stratification_reason or "").strip():
        return (
            base
            + " No stratification factors are recorded and no reason is given for that. This is the one "
            "decision that cannot be revisited: data collected without a factor can never be split by it."
        )
    return base + " With the definition settled, the numbers that follow are about the process."


def build_report_card(artifact: DataCollectionPlanArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    definition = artifact.operational_definition
    missing = missing_definition_fields(artifact)

    if missing:
        items.append(("fail", f"Operational definition incomplete: {', '.join(missing).lower()} not stated."))
    else:
        items.append(("pass", "Every part of the operational definition is filled in."))

    items.append(
        (
            "pass" if definition.two_people_confirmed else "flag",
            "Two people measured the same thing and agreed on the definition."
            if definition.two_people_confirmed
            else "The two-people test has not been confirmed. It costs ten minutes and is the only real check "
            "that this definition is unambiguous.",
        )
    )

    if artifact.data_type:
        items.append(("pass", f"Data type declared: {str(artifact.data_type).replace('_', ' ')} — it decides which tools downstream are valid."))
    else:
        items.append(("flag", "No data type declared. Continuous and attribute data need different charts and different tests."))

    if artifact.stratification_factors:
        items.append(
            (
                "pass",
                f"{len(artifact.stratification_factors)} stratification factor(s) will be captured: "
                + ", ".join(f.name for f in artifact.stratification_factors[:5])
                + ".",
            )
        )
    elif (artifact.no_stratification_reason or "").strip():
        items.append(
            (
                "neutral",
                f"No stratification, with a stated reason: {rt.clip(artifact.no_stratification_reason, 200)}",
            )
        )
    else:
        items.append(
            (
                "fail",
                "No stratification factors and no reason given. This is not recoverable later — data collected "
                "without a factor cannot be split by it afterwards.",
            )
        )

    logistics = artifact.logistics
    gaps = [
        label
        for field, label in (
            ("who_collects", "who collects"),
            ("where_collected", "where"),
            ("when_how_often", "when and how often"),
        )
        if not (getattr(logistics, field, "") or "").strip()
    ]
    if gaps:
        items.append(("flag", f"Collection logistics incomplete: {', '.join(gaps)} not stated. A plan nobody is assigned to does not run."))
    else:
        items.append(("pass", f"{logistics.who_collects.strip()} collects, {logistics.where_collected.strip()}, {logistics.when_how_often.strip()}."))

    if logistics.planned_n:
        rationale = (logistics.sample_size_rationale or "").strip()
        items.append(
            (
                "pass" if rationale else "flag",
                f"Planned sample size {logistics.planned_n}"
                + (f", because: {rt.clip(rationale, 180)}" if rationale else " with no stated rationale — usually a guess, and usually short."),
            )
        )
    else:
        items.append(("flag", "No planned sample size. Collection stops when someone gets tired rather than when the question is answerable."))

    bias = (artifact.bias_note or "").strip()
    if bias:
        items.append(("pass", f"Bias considered up front: {rt.clip(bias, 200)}"))
    else:
        items.append(
            (
                "neutral",
                "No bias note. Worth one sentence on who is being observed and whether being observed changes "
                "what they do.",
            )
        )
    return items


def build_story(
    *,
    artifact: DataCollectionPlanArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    verdict_text, tone = build_verdict(artifact)
    definition = artifact.operational_definition

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

    # As labelled parts, not prose: a paragraph reads as complete and hides
    # which piece is missing.
    story.append(_label("THE OPERATIONAL DEFINITION", styles))
    definition_rows = [
        (label, (getattr(definition, field, "") or "").strip() or "— not stated")
        for field, label in DEFINITION_FIELDS
    ]
    story.append(kv_table(definition_rows, styles, content_width, label_frac=0.32))

    logistics = artifact.logistics
    story.append(_label("HOW IT GETS COLLECTED", styles))
    logistics_rows: list[tuple[str, str]] = [
        ("Who collects", (logistics.who_collects or "").strip() or "— not stated"),
        ("Where", (logistics.where_collected or "").strip() or "— not stated"),
        ("When, how often", (logistics.when_how_often or "").strip() or "— not stated"),
        ("Planned sample", str(logistics.planned_n) if logistics.planned_n else "— not stated"),
    ]
    if artifact.stratification_factors:
        logistics_rows.append(("Split by", ", ".join(f.name for f in artifact.stratification_factors)))
    story.append(kv_table(logistics_rows, styles, content_width, label_frac=0.32))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
