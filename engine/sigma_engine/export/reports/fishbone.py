"""T-15 Fishbone Report — sorted by what is actually known.

A fishbone drawn on a whiteboard and photographed has one fatal property:
every cause on it looks equally true. The verified one and the one
somebody suggested in the third minute of the session are the same size,
in the same handwriting, on the same bone. Two weeks later nobody
remembers which was which, and the project fixes whichever is easiest.

So this page reorders the diagram's content by status. Verified causes
first, with their evidence; then the ones under investigation; then the
candidates; then the ruled-out, which are kept because knowing what was
eliminated is what stops a team relitigating it.

EVIDENCE IS RESOLVED TO WORDS, NOT LEFT AS IDS. "ds-4a2f" beside a
verified cause is not evidence to a reader, it is a promise that evidence
exists somewhere. The kind and the reference both print.

TEAM CONSENSUS IS NOT EVIDENCE — and the schema already enforces that,
refusing to save a cause marked verified with nothing attached. So this
page does not lecture about it. It reports the split that is actually in
question: how much of the diagram is known versus still suspected.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.fishbone import Cause, FishboneArtifact
from .. import report_theme as rt
from ..charter_pdf_common import esc, kv_table

TOOL_ID = "T-15"
TOOL_TITLE = "Fishbone + 5 Whys"

BRANCH_LABELS = {
    "people": "People",
    "method": "Method",
    "machine": "Machine",
    "material": "Material",
    "measurement": "Measurement",
    "environment": "Environment",
}
STATUS_ORDER = ("verified", "investigating", "candidate", "ruled_out")
STATUS_LABELS = {
    "verified": "VERIFIED — evidence attached",
    "investigating": "UNDER INVESTIGATION",
    "candidate": "CANDIDATE — suggested, not tested",
    "ruled_out": "RULED OUT",
}
STATUS_TONES: dict[str, rt.Tone] = {
    "verified": "pass",
    "investigating": "flag",
    "candidate": "neutral",
    "ruled_out": "neutral",
}


def by_status(artifact: FishboneArtifact, status: str) -> list[Cause]:
    return [c for c in artifact.causes if c.status == status]


def evidence_text(cause: Cause) -> str:
    """The evidence, in words. An id on its own is a promise that evidence
    exists, not evidence."""
    evidence = cause.evidence
    if evidence is None:
        return "no evidence attached"
    kind = str(evidence.kind).replace("_", " ")
    return f"{kind}: {rt.clip(evidence.ref, 120)}"


def verified_without_evidence(artifact: FishboneArtifact) -> list[Cause]:
    return [c for c in artifact.causes if c.status == "verified" and c.evidence is None]


def build_verdict(artifact: FishboneArtifact) -> tuple[str, rt.Tone]:
    verified = by_status(artifact, "verified")
    ruled_out = by_status(artifact, "ruled_out")
    total = len(artifact.causes)
    if not verified:
        return (f"{total} cause(s) on the diagram, none verified yet — all still suspects.", "flag")
    settled = len(verified) + len(ruled_out)
    return (
        f"{len(verified)} of {total} cause(s) verified with evidence"
        + (f", {len(ruled_out)} ruled out — {settled} of {total} settled." if ruled_out else "."),
        "pass",
    )


def build_meaning(artifact: FishboneArtifact) -> str:
    verified = by_status(artifact, "verified")
    candidates = by_status(artifact, "candidate")
    base = (
        "A fishbone is a list of suspects, not a list of causes. Its value comes entirely from what happened "
        "after the session: which suspects were tested, which survived, and which were eliminated — which is "
        "why this page is sorted by status rather than by branch."
    )
    if not verified:
        return (
            base
            + f" Nothing here is verified yet, so all {len(artifact.causes)} entries are still suspects. "
            "Fixing one now is a guess with a diagram behind it."
        )
    if candidates:
        base += (
            f" {len(candidates)} cause(s) are still untested. They are not wrong — they are unexamined, and "
            "the difference matters when someone proposes fixing one."
        )
    return base


def build_report_card(artifact: FishboneArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    items.append(("neutral", f"{len(artifact.causes)} cause(s) across {len(BRANCH_LABELS)} branches."))

    # The schema refuses to save a verified cause with no evidence, so this
    # can only fire on a hand-edited file. Kept as a safety net, worded as
    # one, and never as a lecture about something the tool prevents.
    unsupported = verified_without_evidence(artifact)
    if unsupported:  # pragma: no cover -- schema-enforced upstream
        items.append(
            (
                "fail",
                f"{len(unsupported)} cause(s) are marked verified with no evidence attached. The app does not "
                "allow that, so this file has been edited outside it.",
            )
        )
    else:
        items.append(
            (
                "pass",
                "Every verified cause carries evidence — enforced when the diagram is saved, not checked here "
                "after the fact.",
            )
        )

    for status in STATUS_ORDER:
        causes = by_status(artifact, status)
        if causes:
            items.append((STATUS_TONES[status], f"{len(causes)} {STATUS_LABELS[status].split(' —')[0].lower()}."))

    branches_used = {c.branch for c in artifact.causes}
    unused = [BRANCH_LABELS[b] for b in BRANCH_LABELS if b not in branches_used]
    if unused:
        items.append(
            (
                "neutral",
                f"{len(unused)} branch(es) empty: {', '.join(unused)}. Sometimes correct, and sometimes the "
                "branch nobody thought about.",
            )
        )

    why_chains = [c for c in artifact.causes if c.why_chain_position is not None]
    if why_chains:
        depth = max(c.why_chain_position or 0 for c in why_chains)
        items.append(
            (
                "pass" if depth >= 3 else "flag",
                f"A why-chain reaches depth {depth}."
                + ("" if depth >= 3 else " Stopping at the second why usually lands on a symptom."),
            )
        )
    else:
        items.append(("flag", "No why-chain recorded. The first cause named is rarely the one worth fixing."))

    return items


def build_story(
    *,
    artifact: FishboneArtifact,
    project_name: str,
    version: int,
    chart_png: bytes | None = None,
    chart_unavailable_reason: str | None = None,
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
    if chart_png or chart_unavailable_reason:
        story += rt.chart(
            chart_png, content_width=content_width, styles=styles, unavailable_reason=chart_unavailable_reason
        )

    effect = artifact.effect
    story.append(
        kv_table(
            [("The effect", rt.clip(getattr(effect, "text", str(effect)), 300))],
            styles,
            content_width,
            label_frac=0.24,
        )
    )

    # By status, not by branch: the diagram above already groups by branch,
    # and what a reader needs from the text is what is known.
    for status in STATUS_ORDER:
        causes = by_status(artifact, status)
        if not causes:
            continue
        story.append(_label(STATUS_LABELS[status], styles))
        for cause in causes:
            line = f"<b>{esc(BRANCH_LABELS.get(cause.branch, cause.branch))}</b> — {esc(rt.clip(cause.text, 260))}"
            if cause.status == "verified":
                line += f"<br/><i>{esc(evidence_text(cause))}</i>"
            elif cause.status == "ruled_out" and cause.evidence is not None:
                line += f"<br/><i>ruled out by {esc(evidence_text(cause))}</i>"
            if cause.why_chain_position is not None:
                line += f"<br/><i>why #{cause.why_chain_position} in a chain</i>"
            story.append(Paragraph(line, styles["card_item"]))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _label(text: str, styles: dict) -> Any:
    from reportlab.platypus import Paragraph

    return Paragraph(text, styles["zone_label"])
