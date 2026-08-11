"""T-05 VoC → CTQ Report — the traceable chain, printed as a chain.

The whole value of this tool is that it refuses to let a measurable target
appear from nowhere. Every CTQ traces to a need, every need to at least
one thing a customer actually said, and every statement to a named
customer role. That chain is either intact or it is not, and a report that
prints four tidy lists side by side hides which.

SO THE CHAIN IS PRINTED AS A CHAIN. Each CTQ appears with the need it
serves and the customer words underneath it, in one block. A reader
follows "we measure this → because they need that → because they said
this" without cross-referencing ids, which is the form the argument has to
survive in front of a sponsor.

VERBATIM IS KEPT VERBATIM. Customer statements are captured close to the
customer's own words on purpose, and paraphrasing them onto the page would
throw away the one thing that makes them persuasive. They are quoted, and
the source is named beside them.

THE PRIMARY CTQ IS MARKED, because a project with five equally important
CTQs has no primary metric, and the charter needs one.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.voc_ctq import Ctq, VocCtqArtifact
from .. import report_theme as rt
from ..charter_pdf_common import esc, kv_table

TOOL_ID = "T-05"
TOOL_TITLE = "Voice of the Customer → CTQ"

DIRECTION_WORDS = {
    "lower_is_better": "lower is better",
    "higher_is_better": "higher is better",
    "target_is_best": "on target is best",
}
MAX_QUOTE = 260


def primary_ctq(artifact: VocCtqArtifact) -> Ctq | None:
    for ctq in artifact.ctqs:
        if ctq.ctq_id == artifact.primary_ctq_id:
            return ctq
    return None


def chain_for(artifact: VocCtqArtifact, ctq: Ctq) -> tuple[Any, list[Any]]:
    """(need, statements) behind one CTQ. Traversed by id rather than
    printed as ids: a reader should never have to resolve "n-3" themselves."""
    need = next((n for n in artifact.needs if n.need_id == ctq.need_id), None)
    if need is None:
        return None, []
    statements = [s for s in artifact.statements if s.statement_id in set(need.statement_ids)]
    return need, statements


def orphan_ctqs(artifact: VocCtqArtifact) -> list[Ctq]:
    need_ids = {n.need_id for n in artifact.needs}
    return [c for c in artifact.ctqs if c.need_id not in need_ids]


def unheard_customers(artifact: VocCtqArtifact) -> list[str]:
    """Customer roles named in the customer list that no statement is
    attributed to — the ones nobody actually asked."""
    heard = {s.customer_role.strip().lower() for s in artifact.statements}
    return [c.role for c in artifact.customers if c.role.strip().lower() not in heard]


def build_verdict(artifact: VocCtqArtifact) -> tuple[str, rt.Tone]:
    primary = primary_ctq(artifact)
    if primary is None:
        return (
            f"{len(artifact.ctqs)} CTQ(s), but the declared primary ({artifact.primary_ctq_id}) is not among them.",
            "fail",
        )
    direction = DIRECTION_WORDS.get(str(primary.direction), str(primary.direction).replace("_", " "))
    target = f", target {primary.target}" if primary.target else ""
    return (
        f"Primary CTQ: {rt.clip(primary.measure, 110)} — {direction}{target}. "
        f"{len(artifact.ctqs)} CTQ(s) from {len(artifact.statements)} customer statement(s).",
        "pass",
    )


def build_meaning(artifact: VocCtqArtifact) -> str:
    orphans = orphan_ctqs(artifact)
    unheard = unheard_customers(artifact)
    base = (
        "This is where the project's metric comes from, and the chain matters more than the metric. A number "
        "traced back through a need to something a customer actually said can be defended; the same number "
        "chosen because it was easy to collect cannot, and looks identical on a slide."
    )
    if orphans:
        base += (
            f" {len(orphans)} CTQ(s) here point at a need that does not exist in this artifact — for those the "
            "chain is broken and the measure is unsupported."
        )
    if unheard:
        base += (
            f" {len(unheard)} named customer(s) have no statement attributed to them "
            f"({', '.join(unheard[:3])}), so their view is represented by inference rather than by anything "
            "they said."
        )
    return base


def build_report_card(artifact: VocCtqArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []

    items.append(
        (
            "neutral",
            f"{len(artifact.customers)} customer(s), {len(artifact.statements)} statement(s), "
            f"{len(artifact.needs)} need(s), {len(artifact.ctqs)} CTQ(s).",
        )
    )

    primary = primary_ctq(artifact)
    if primary is None:
        items.append(("fail", f"The declared primary CTQ id ({artifact.primary_ctq_id}) matches no CTQ."))
    else:
        items.append(("pass", f"A single primary CTQ is declared: {rt.clip(primary.measure, 120)}"))

    orphans = orphan_ctqs(artifact)
    if orphans:
        items.append(
            (
                "fail",
                f"{len(orphans)} CTQ(s) reference a need that is not here: "
                + ", ".join(rt.clip(c.measure, 60) for c in orphans[:3])
                + ".",
            )
        )
    else:
        items.append(("pass", "Every CTQ traces to a need in this document."))

    needs_without_statements = [n for n in artifact.needs if not n.statement_ids]
    if needs_without_statements:
        items.append(("fail", f"{len(needs_without_statements)} need(s) rest on no customer statement."))
    else:
        items.append(("pass", "Every need rests on at least one thing a customer said."))

    unheard = unheard_customers(artifact)
    if unheard:
        items.append(
            (
                "flag",
                f"{len(unheard)} named customer(s) were never quoted: {', '.join(unheard[:4])}. Either they "
                "were not asked, or what they said was not recorded.",
            )
        )
    else:
        items.append(("pass", "Every named customer is represented by something they actually said."))

    external = [c for c in artifact.customers if not c.is_internal]
    if not external:
        items.append(
            (
                "flag",
                "Every customer here is internal. Internal customers are legitimate, and a project with no "
                "external voice at all usually optimises what is convenient to produce.",
            )
        )
    else:
        items.append(("pass", f"{len(external)} external customer(s) represented."))

    no_target = [c for c in artifact.ctqs if not (c.target or "").strip()]
    if no_target:
        items.append(
            (
                "flag",
                f"{len(no_target)} CTQ(s) have a direction but no target value. A direction says which way to "
                "push; without a target nothing says when to stop.",
            )
        )

    if artifact.charter_metric_link:
        items.append(("pass", f"Linked to the charter metric: {rt.clip(artifact.charter_metric_link, 120)}"))

    return items


def build_story(
    *,
    artifact: VocCtqArtifact,
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

    story.append(
        kv_table(
            [
                ("Customers", ", ".join(rt.clip(c.role, 60) for c in artifact.customers)),
                ("Charter metric", rt.clip(artifact.charter_metric_link, 160) or "— not linked"),
            ],
            styles,
            content_width,
            label_frac=0.28,
        )
    )

    # As a chain, one CTQ at a time. Primary first: it is the one the
    # charter has to carry.
    story.append(_label("EACH MEASURE, AND WHERE IT CAME FROM", styles))
    ordered = sorted(artifact.ctqs, key=lambda c: (c.ctq_id != artifact.primary_ctq_id, c.measure.lower()))
    for ctq in ordered:
        need, statements = chain_for(artifact, ctq)
        direction = DIRECTION_WORDS.get(str(ctq.direction), str(ctq.direction).replace("_", " "))
        heading = rt.clip(ctq.measure, 140)
        if ctq.ctq_id == artifact.primary_ctq_id:
            heading += "  (primary)"
        lines = [f"<b>{esc(heading)}</b> — {esc(direction)}" + (f", target {esc(str(ctq.target))}" if ctq.target else "")]
        if need is not None:
            lines.append(f"because they need: {esc(rt.clip(need.text, 220))}")
        else:
            lines.append("<i>no need in this document matches this CTQ</i>")
        for statement in statements[:3]:
            source = f"{statement.customer_role.strip()}, {str(statement.source).replace('_', ' ')}"
            lines.append(f"&ldquo;{esc(rt.clip(statement.text, MAX_QUOTE))}&rdquo; — <i>{esc(source)}</i>")
        if len(statements) > 3:
            lines.append(f"<i>+{len(statements) - 3} more statement(s) in the project record</i>")
        story.append(Paragraph("<br/>".join(lines), styles["card_item"]))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
