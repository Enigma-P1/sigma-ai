"""T-04 SIPOC Report — the scope agreement, on one page.

A SIPOC is not really a diagram of a process. It is a negotiation with a
sponsor about where the project starts and stops, written down so that in
month two nobody can say "well obviously that part was included". Its most
valuable two fields are the ones people skip: scope start and scope end.

SO THE BOUNDARIES LEAD. They print at the top, before the five columns,
because they are the sentence the sponsor is actually agreeing to. The
columns describe what falls inside them.

THE FIVE COLUMNS PRINT AS THREE PAIRED TABLES, not as five parallel lists.
Suppliers and inputs belong together — "the roaster" is meaningless
without "green beans" beside it — and the same for outputs and customers.
Five columns of unequal length side by side is the version that fits a
whiteboard and misleads on paper, because row 3 of one column has nothing
to do with row 3 of the next.

STEP COUNT IS A JUDGEMENT THIS PAGE MAKES. A SIPOC with twenty process
steps is a process map wearing a SIPOC's clothes, and one with two is a
boundary statement rather than a scope. Five to seven is what the level of
detail is for, and the report card says so.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.sipoc import SipocArtifact
from .. import report_theme as rt
from ..charter_pdf_common import base_table_style, esc, kv_table

TOOL_ID = "T-04"
TOOL_TITLE = "SIPOC"

# The band a SIPOC's step list is useful in. Below it the map says nothing
# about how the work flows; above it, it has become the process map.
MIN_USEFUL_STEPS = 4
MAX_USEFUL_STEPS = 8
MAX_CELL = 110


def build_verdict(artifact: SipocArtifact) -> tuple[str, rt.Tone]:
    steps = len(artifact.process_steps)
    tone: rt.Tone = "pass" if MIN_USEFUL_STEPS <= steps <= MAX_USEFUL_STEPS else "flag"
    return (
        f"Scope: {rt.clip(artifact.scope_start, 90)} → {rt.clip(artifact.scope_end, 90)} "
        f"({steps} step(s)).",
        tone,
    )


def build_meaning(artifact: SipocArtifact) -> str:
    steps = len(artifact.process_steps)
    base = (
        "The two ends of that arrow are what the project is agreeing to. Everything before the start and "
        "after the end is somebody else's problem for the duration — which is the point, and the only "
        "protection against a project that quietly grows until it cannot finish."
    )
    if steps > MAX_USEFUL_STEPS:
        return (
            base
            + f" At {steps} steps this has stopped being a SIPOC and become a process map. That is not wrong, "
            "but the detail belongs in T-06, where it can carry times and waste; here it makes the boundary "
            "harder to see, which is the one thing this tool is for."
        )
    if steps < MIN_USEFUL_STEPS:
        return (
            base
            + f" With {steps} step(s) the middle is thin enough that a reader cannot tell what the process "
            "actually does between those two boundaries."
        )
    return base + " The step list is at the level this tool wants: enough to see the shape, not enough to argue about."


def build_report_card(artifact: SipocArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    steps = len(artifact.process_steps)

    items.append(
        (
            "pass" if MIN_USEFUL_STEPS <= steps <= MAX_USEFUL_STEPS else "flag",
            f"{steps} process step(s)."
            + (
                ""
                if MIN_USEFUL_STEPS <= steps <= MAX_USEFUL_STEPS
                else f" {MIN_USEFUL_STEPS}–{MAX_USEFUL_STEPS} is the level of detail a SIPOC is for."
            ),
        )
    )
    items.append(
        ("pass", f"{len(artifact.supplier_input_pairs)} supplier/input pair(s) and {len(artifact.output_customer_pairs)} output/customer pair(s).")
    )

    # A SIPOC whose customers are all internal usually means the external
    # customer was never asked, which is where CTQs come from.
    customers = {pair.customer.strip().lower() for pair in artifact.output_customer_pairs}
    items.append(("neutral", f"Customers named: {', '.join(sorted(c for c in customers if c))[:200]}."))

    numbers = [step.step_number for step in artifact.process_steps]
    if len(set(numbers)) != len(numbers):
        items.append(("fail", "Two process steps share a step number — the order is ambiguous."))
    elif numbers and sorted(numbers) != list(range(min(numbers), min(numbers) + len(numbers))):
        items.append(("flag", "Step numbers have gaps."))
    else:
        items.append(("pass", "Steps are numbered in an unbroken sequence."))

    items.append(
        (
            "neutral",
            "Suppliers pair with inputs and outputs pair with customers, so each row means something on its "
            "own. Five independent columns of unequal length is a whiteboard shape, not a page one.",
        )
    )
    return items


def _pair_table(rows: list[tuple[str, str]], headings: tuple[str, str], styles: dict, content_width: float) -> Any:
    from reportlab.platypus import Paragraph, Table

    header = [Paragraph(esc(h), styles["table_header"]) for h in headings]
    body = [
        [
            Paragraph(esc(rt.clip(left, MAX_CELL)), styles["table_cell"]),
            Paragraph(esc(rt.clip(right, MAX_CELL)), styles["table_cell"]),
        ]
        for left, right in rows
    ]
    table = Table([header, *body], colWidths=[content_width * 0.5, content_width * 0.5], repeatRows=1, hAlign="LEFT")
    table.setStyle(base_table_style())
    return table


def build_story(
    *,
    artifact: SipocArtifact,
    project_name: str,
    version: int,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    from reportlab.platypus import Paragraph, Table

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

    # The boundaries first: this is the sentence the sponsor agreed to.
    story.append(
        kv_table(
            [("Starts when", artifact.scope_start.strip()), ("Ends when", artifact.scope_end.strip())],
            styles,
            content_width,
            label_frac=0.28,
        )
    )

    story.append(_label("SUPPLIERS AND WHAT THEY PROVIDE", styles))
    story.append(
        _pair_table(
            [(p.supplier, p.input) for p in artifact.supplier_input_pairs],
            ("Supplier", "Input"),
            styles,
            content_width,
        )
    )

    story.append(_label("THE PROCESS, AT SIPOC LEVEL", styles))
    step_header = [Paragraph(esc(h), styles["table_header"]) for h in ("#", "Step")]
    step_body = [
        [
            Paragraph(str(step.step_number), styles["table_cell"]),
            Paragraph(esc(rt.clip(step.description, 200)), styles["table_cell"]),
        ]
        for step in sorted(artifact.process_steps, key=lambda s: s.step_number)
    ]
    step_table = Table(
        [step_header, *step_body], colWidths=[content_width * 0.08, content_width * 0.92], repeatRows=1, hAlign="LEFT"
    )
    step_table.setStyle(base_table_style())
    story.append(step_table)

    story.append(_label("OUTPUTS AND WHO RECEIVES THEM", styles))
    story.append(
        _pair_table(
            [(p.output, p.customer) for p in artifact.output_customer_pairs],
            ("Output", "Customer"),
            styles,
            content_width,
        )
    )

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
