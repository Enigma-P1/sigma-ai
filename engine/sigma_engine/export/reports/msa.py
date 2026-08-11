"""T-12 Measurement Check Report.

NOT a Gage R&R, and the report says so on the page. This tool runs a
single-operator test/retest repeatability study plus, on the attribute path,
two-rater agreement with Cohen's kappa. Reproducibility across operators,
bias, linearity and stability over time are named and routed out, not
computed (stats/msa.py). Full multi-operator Gage R&R is T-35.

Printing that limitation is not modesty, it is the point. A page headed
"measurement study" that stays silent about what it did not measure is
exactly how a marginal gauge gets waved through -- and everything
downstream, every capability index and every before/after claim, inherits
that error silently.

The verdict leads because nothing computed after this is trustworthy if it
fails: a failed measurement check means the numbers are measuring the
measurement system, not the process.
"""

from __future__ import annotations

from typing import Any

from ...artifacts.msa import MsaArtifact
from .. import report_theme as rt
from ..charter_pdf_common import fmt_number, kv_table

TOOL_ID = "T-12"
TOOL_TITLE = "Measurement Check"

_TONE: dict[str, rt.Tone] = {"acceptable": "pass", "marginal": "flag", "fail": "fail"}


def build_verdict(artifact: MsaArtifact) -> tuple[str, rt.Tone]:
    result = artifact.result
    if result is None:
        return ("No measurement study computed yet.", "neutral")

    tone = _TONE.get(result.verdict, "neutral")
    if result.data_type == "continuous":
        rep = result.repeatability.value if result.repeatability else None
        if rep is None:
            return (
                "Gauge resolution check failed — the gauge cannot see the variation being studied, "
                "so repeatability was not computed.",
                "fail",
            )
        return (
            f"Repeatability {fmt_number(rep.repeatability_percent)}% of "
            f"{rep.denominator.replace('_', ' ')} — {result.verdict}.",
            tone,
        )

    agree = result.attribute_agreement.value if result.attribute_agreement else None
    if agree is None:
        return ("No attribute agreement computed.", "neutral")
    return (
        f"Two-rater agreement {fmt_number(agree.percent_agreement)}%, "
        f"kappa {fmt_number(agree.kappa)} — {result.verdict}.",
        tone,
    )


def build_meaning(artifact: MsaArtifact) -> str:
    result = artifact.result
    if result is None:
        return "A measurement check asks whether your numbers are measuring the process or the measuring."

    if result.data_type == "attribute":
        return (
            "Percent agreement alone flatters a rare-defect process: two raters who both say 'fine' "
            "to everything agree 95% of the time on a 5%-defect line while judging nothing. Kappa "
            "corrects for that by removing the agreement you would get by chance, which is why both "
            "are printed and neither is printed alone."
        )
    if result.verdict == "fail":
        return (
            "The measurement system cannot reliably tell apart the differences this project is about. "
            "Every number downstream — the baseline, the capability index, the before/after "
            "comparison — is partly measuring the gauge rather than the process. Fix the measurement "
            "before trusting any of it."
        )
    return (
        "Repeat readings of the same item land close enough together that the differences this "
        "project cares about are real rather than measurement noise. This is a single-operator "
        "check, so it says nothing about whether two people would agree."
    )


def build_report_card(artifact: MsaArtifact) -> list[tuple[rt.Tone, str]]:
    items: list[tuple[rt.Tone, str]] = []
    result = artifact.result
    if result is None:
        return [("neutral", "No study computed.")]

    # The scope limit goes on EVERY page, pass or fail. A reader who only
    # ever sees the passing version must still learn what was not tested.
    items.append(
        (
            "neutral",
            "Scope: single-operator test/retest only. Operator-to-operator reproducibility, bias, "
            "linearity and drift over time were NOT assessed — those need a full Gage R&R.",
        )
    )

    if result.verdict == "fail":
        items.append(("fail", rt.LABELS["msa_unqualified"]))

    if result.data_type == "continuous":
        rep = result.repeatability.value if result.repeatability else None
        if rep is not None:
            items.append(("pass" if rep.items_used >= 5 else "flag", f"Items measured: {rep.items_used}"))
            if rep.items_excluded:
                items.append(
                    ("flag", f"{len(rep.items_excluded)} item(s) excluded: {'; '.join(rep.exclusion_reasons)}")
                )
            items.append(
                (
                    "neutral",
                    f"Percentage is against {rep.denominator.replace('_', ' ')} "
                    f"({fmt_number(rep.denominator_value)}) — the basis changes the number, so it is named here.",
                )
            )
        if result.resolution_check is not None:
            passed = getattr(result.resolution_check, "passed", None)
            if passed is False:
                items.append(("fail", "Gauge resolution too coarse for the span being measured."))
            elif passed is True:
                items.append(("pass", "Gauge resolution is fine enough for the span being measured."))
    else:
        agree = result.attribute_agreement.value if result.attribute_agreement else None
        if agree is not None:
            items.append(("pass" if agree.n >= 20 else "flag", f"Items judged: {agree.n}"))
            items.append(
                (
                    "neutral",
                    f"Chance agreement alone would have been {fmt_number(agree.p_expected * 100)}% — "
                    "kappa is what is left after removing it.",
                )
            )

    if result.caveat:
        items.append(("flag", result.caveat))
    return items


def build_story(
    *,
    artifact: MsaArtifact,
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

    rows: list[tuple[str, str]] = [("Data type", artifact.data_type)]
    if artifact.gauge_name:
        rows.append(("Gauge", artifact.gauge_name))
    if artifact.gauge_increment is not None:
        rows.append(("Smallest increment", fmt_number(artifact.gauge_increment)))
    rows.append(("Operator", artifact.operator))
    result = artifact.result
    if result is not None and result.data_type == "continuous" and result.repeatability:
        rep = result.repeatability.value
        rows.append(("Repeat-measure SD", fmt_number(rep.s_repeat)))
        rows.append(("Repeatability", f"{fmt_number(rep.repeatability_percent)}%"))
    if result is not None and result.attribute_agreement:
        agree = result.attribute_agreement.value
        rows.append(("Percent agreement", f"{fmt_number(agree.percent_agreement)}%"))
        rows.append(("Cohen's kappa", fmt_number(agree.kappa)))
    story.append(kv_table(rows, styles, content_width, label_frac=0.3))

    story.append(rt.keep(rt.meaning(build_meaning(artifact), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(artifact), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story
