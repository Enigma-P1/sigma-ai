"""T-10 Yield Report — the arithmetic that surprises people.

Every step in this process looks fine. Five steps at 95% each feel like a
95% process, and they are a 77% one. That gap is the whole reason this
tool exists, and it is the thing the page is built to make unavoidable:
the rolled figure sits in the banner, the step yields sit under it, and
the reader can see for themselves that no single step is the problem.

THE HIDDEN FACTORY IS NAMED IN UNITS. "RTY 77%" is a statistic; "23 of
every 100 units need rework somewhere" is a staffing problem. The second
is what gets a project funded, so it is printed beside the first.

DPMO AND SIGMA TRAVEL WITH THEIR CONVENTION. A sigma level means nothing
without saying whether the 1.5-sigma shift was applied — the same process
is 4.5 sigma under one convention and 3.0 under the other, and quoting the
flattering one without the label is the single most common abuse of this
number. The engine carries the convention on the result and this page
prints it beside the figure every time.

OPPORTUNITY COUNTS ARE THE SOFT SPOT. DPMO scales directly with
opportunities per unit, so a generous opportunity count buys a better
sigma level for free. The justification is printed next to it, so the
reader can judge whether the denominator was chosen or discovered.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.yield_calc import YieldCalcArtifact, YieldStep
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-10"
TOOL_TITLE = "Yield: FPY, RTY and DPMO"

# Below this, a step is worth naming in the verdict as the one to fix.
WEAK_STEP_YIELD = 0.95


def pct(value: float | None, digits: int = 1) -> str:
    return "—" if value is None else f"{value * 100:.{digits}f}%"


def weakest_step(artifact: YieldCalcArtifact) -> YieldStep | None:
    if not artifact.steps:
        return None
    return min(artifact.steps, key=lambda s: s.fpy_at_step)


def build_verdict(artifact: YieldCalcArtifact) -> tuple[str, rt.Tone]:
    rty = artifact.rty_result.value if artifact.rty_result else None
    if rty is None:
        return ("No rolled yield computed yet.", "neutral")

    per_hundred = round((1 - rty) * 100)
    tone: rt.Tone = "pass" if rty >= 0.95 else "flag" if rty >= 0.80 else "fail"
    basis = "rolled through all steps" if artifact.steps_in_series else "steps are not in series — see below"
    return (
        f"Rolled throughput yield {pct(rty)} — about {per_hundred} in every 100 units "
        f"need rework or scrap somewhere ({basis}).",
        tone,
    )


def build_meaning(artifact: YieldCalcArtifact) -> str:
    rty = artifact.rty_result.value if artifact.rty_result else None
    weak = weakest_step(artifact)
    if rty is None:
        return (
            "Rolled throughput yield is the share of units that get through every step right the first "
            "time, with no rework anywhere. It is the number that describes what customers and staffing "
            "actually feel."
        )

    best_step = max(artifact.steps, key=lambda s: s.fpy_at_step) if artifact.steps else None
    base = (
        "First-pass yield is per step. Rolled throughput yield multiplies them together, which is why it is "
        "always lower than the worst step and usually lower than people expect: a unit has to survive every "
        "step, not the average step. The gap between them is the hidden factory — rework that is being done, "
        "staffed and paid for, and that appears in nobody's defect rate."
    )
    if weak is not None and best_step is not None and len(artifact.steps) > 1:
        base += (
            f" Here the weakest step is {weak.name.strip()} at {pct(weak.fpy_at_step)} and the strongest is "
            f"{best_step.name.strip()} at {pct(best_step.fpy_at_step)}. Fixing the weakest step raises the "
            "rolled figure by the most, and fixing a strong one barely moves it."
        )
    return base


def build_report_card(artifact: YieldCalcArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    items.append(("neutral", f"{len(artifact.steps)} step(s) measured."))

    if not artifact.steps_in_series:
        items.append(
            (
                "flag",
                "These steps are marked as NOT in series. Rolled throughput yield multiplies step yields, "
                "which only describes a unit that must pass through every step in turn — read the rolled "
                "figure with that in mind.",
            )
        )
    else:
        items.append(("pass", "Steps are in series, which is what the rolled multiplication assumes."))

    weak = weakest_step(artifact)
    if weak is not None and weak.fpy_at_step < WEAK_STEP_YIELD:
        items.append(
            (
                "flag",
                f"{weak.name.strip()} is the weakest step at {pct(weak.fpy_at_step)} "
                f"({weak.first_pass_correct:,.0f} of {weak.units_in:,.0f} right first time). It is where the "
                "rolled figure is being lost.",
            )
        )
    elif weak is not None:
        items.append(("pass", f"Every step is at or above {pct(WEAK_STEP_YIELD, 0)} first-pass yield."))

    thin = [s for s in artifact.steps if s.units_in < 30]
    if thin:
        items.append(
            (
                "flag",
                f"{len(thin)} step(s) are based on fewer than 30 units "
                f"({', '.join(s.name.strip() for s in thin[:3])}). A yield from a handful of units moves a lot "
                "with one more defect.",
            )
        )

    dpmo = artifact.dpmo_result.value if artifact.dpmo_result else None
    block = artifact.dpmo_block
    if dpmo is not None and block is not None:
        items.append(
            (
                "neutral",
                f"Sigma level {dpmo.sigma_level:.2f} is quoted on the {dpmo.convention.replace('_', ' ')} "
                "convention. The same process reads roughly 1.5 sigma different on the other one, so the "
                "convention travels with the number, always.",
            )
        )
        justification = (block.opportunity_justification or "").strip()
        if block.opportunities_per_unit > 1 and not justification:
            items.append(
                (
                    "fail",
                    f"{block.opportunities_per_unit:g} opportunities per unit are claimed with no justification. "
                    "DPMO divides by this number — an unjustified opportunity count buys a better sigma level "
                    "for nothing, and it is the first thing a sceptical reviewer will challenge.",
                )
            )
        elif block.opportunities_per_unit > 1:
            items.append(("pass", f"{block.opportunities_per_unit:g} opportunities per unit, justified: {justification}"))
        else:
            items.append(("pass", "One opportunity per unit — the conservative choice, and unarguable."))

    items.append(
        (
            "neutral",
            "Step yields are the counted ratio (right first time / units in), not a model fitted on top of a "
            "defect count. The rolled figure is their product.",
        )
    )
    return items


def build_steps_table(artifact: YieldCalcArtifact, styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [
        Paragraph(esc(h), styles["table_header"])
        for h in ("Step", "Units in", "Right first time", "Needed rework", "First-pass yield")
    ]
    body = []
    # Process order, not sorted: a yield table is read as a walk through the
    # process, and re-ordering it by yield would break the one thing the
    # reader is using it to follow.
    for step in artifact.steps:
        body.append(
            [
                Paragraph(esc(step.name.strip()), styles["table_cell"]),
                Paragraph(f"{step.units_in:,.0f}", styles["table_cell"]),
                Paragraph(f"{step.first_pass_correct:,.0f}", styles["table_cell"]),
                Paragraph(f"{step.defective_units_at_step:,.0f}", styles["table_cell"]),
                Paragraph(pct(step.fpy_at_step), styles["table_cell"]),
            ]
        )
    fracs = [0.34, 0.15, 0.19, 0.16, 0.16]
    table = Table([header, *body], colWidths=[content_width * f for f in fracs], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: YieldCalcArtifact,
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

    rty = artifact.rty_result.value if artifact.rty_result else None
    summary: list[tuple[str, str]] = [("Rolled throughput yield", pct(rty))]
    if artifact.steps:
        worst = weakest_step(artifact)
        if worst is not None:
            summary.append(("Weakest step", f"{worst.name.strip()} — {pct(worst.fpy_at_step)}"))
    dpmo = artifact.dpmo_result.value if artifact.dpmo_result else None
    if dpmo is not None:
        summary.append(("DPMO", f"{dpmo.dpmo:,.0f}"))
        summary.append(("Sigma level", f"{dpmo.sigma_level:.2f} ({dpmo.convention.replace('_', ' ')})"))
    story.append(kv_table(summary, styles, content_width, label_frac=0.32))

    story.append(_label("YIELD BY STEP", styles))
    story.append(build_steps_table(artifact, styles, content_width))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
