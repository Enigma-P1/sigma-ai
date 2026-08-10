"""T-13 Process Capability Report — the flagship one-pager.

This is the page Minitab's equivalent sells: the histogram with the spec
limits drawn on it, the capability indices, and the verdict. What makes
this version different is that it refuses to print a capability index the
process has not earned.

THE NUMBERS ARE RECOMPUTED HERE, NOT ACCEPTED FROM THE CLIENT. The browser
sends only the chart image; every value on the page comes from
`run_baseline` on this request. That keeps the document's arithmetic and
the app's arithmetic the same object rather than two things that agree
until they don't, and it means a tampered or stale client payload cannot
put a wrong number on a page that looks official.

The Coffee Bar worked example prints "stable, Cpk not claimable, Ppk
-1.14" -- a process that is perfectly predictable and predictably terrible.
That combination is the best teaching artifact in the product, and it only
reads correctly because stability and capability are answered as two
separate questions.
"""

from __future__ import annotations

from typing import Any

from ...stats.baseline import BaselineResult
from .. import report_theme as rt
from ..charter_pdf_common import fmt_number

TOOL_ID = "T-13"
TOOL_TITLE = "Process Capability"


def _idx(value: float | None) -> str:
    return fmt_number(value) if value is not None else "not claimable"


def _index_pair(within: float | None, overall: float | None, *, stable: bool | None) -> str:
    """Cp/Cpk and Pp/Ppk, with the RIGHT reason when one is missing.

    Two very different absences were printing the same words. Cp and Pp need
    BOTH spec limits and are simply undefined against a one-sided spec --
    that is arithmetic, not a judgement. Cp/Cpk are separately WITHHELD when
    the process is unstable, which is a judgement and the product's whole
    point. Printing "not claimable" for both told a reader with a one-sided
    spec that their process had failed a test it never took.
    """
    if within is None and overall is not None:
        left = "n/a (needs both spec limits)"
    elif within is None and stable is False:
        left = "not claimable (process not stable)"
    else:
        left = _idx(within)
    return f"{left}  /  {_idx(overall)}"


def build_verdict(result: BaselineResult) -> tuple[str, rt.Tone]:
    """One sentence, and the tone the engine's own gates imply.

    Stability and capability are answered separately and in that order,
    because "in control" and "meeting the customer's requirement" are
    different questions and conflating them is the single most common
    misreading of a capability study.
    """
    if not result.gate_ok:
        return (result.gate_message or "Not enough information to assess capability.", "neutral")

    cap = result.capability.value if result.capability else None
    stable = result.stable
    ppk = cap.ppk_index if cap else None
    cpk = cap.cpk_index if cap else None

    if cap is None or (ppk is None and cpk is None):
        state = "stable" if stable else "not stable"
        return (f"Process is {state}. No specification limits given, so capability is not computed.", "neutral")

    if not stable:
        return (
            f"Process is NOT stable, so Cp/Cpk are not claimable. Performance only: Ppk {_idx(ppk)}.",
            "fail",
        )

    headline = f"Process is stable. Cpk {_idx(cpk)}, Ppk {_idx(ppk)}."
    best = cpk if cpk is not None else ppk
    if best is None:
        return (headline, "neutral")
    if best < 1.0:
        return (headline + " The process cannot meet the specification as it runs today.", "fail")
    if best < 1.33:
        return (headline + " Marginal — meets specification with little margin.", "flag")
    return (headline + " Capable against the specification.", "pass")


def build_meaning(result: BaselineResult) -> str:
    """Zone 3. Deliberately not a restatement of the indices above it."""
    if not result.gate_ok:
        return (
            "Capability answers 'can this process meet the customer's requirement.' It cannot be "
            "answered yet — see the report card for what is missing."
        )
    cap = result.capability.value if result.capability else None
    ppk = cap.ppk_index if cap else None

    if result.stable and ppk is not None and ppk < 1.0:
        return (
            "Two separate findings. The process is predictable — it is not lurching around, and "
            "the same result will keep arriving. And what it predictably delivers does not meet "
            "the specification. Fixing this needs a change to how the process works, not tighter "
            "policing of it: chasing individual bad results will not move a stable process."
        )
    if not result.stable:
        return (
            "The process is not in statistical control, which means it is not one process — "
            "something is changing while it runs. Capability indices assume a single stable "
            "process, so Cp/Cpk are withheld until the instability is found and removed. "
            "Ppk is shown as historical performance, not as a capability claim."
        )
    return (
        "The process is predictable and meets the specification as it currently runs. Hold it "
        "there with a control plan rather than re-tuning it."
    )


def build_report_card(result: BaselineResult) -> list[tuple[rt.Tone, str]]:
    """Zone 4, assembled from the engine's own gates and exits rather than
    from a hand-written checklist, so it cannot drift from what the app
    actually enforced."""
    items: list[tuple[rt.Tone, str]] = []

    if result.n is not None:
        tone: rt.Tone = "pass" if result.n >= 30 else "flag"
        note = "" if result.n >= 30 else " — fewer than 30 points; treat the indices as provisional."
        items.append((tone, f"Sample size: {result.n} observations{note}"))

    if result.measurement_check == "failed":
        items.append(("fail", rt.LABELS["msa_unqualified"]))

    if result.stable is False:
        items.append(("fail", rt.LABELS["unstable"]))
    elif result.stable is True:
        items.append(("pass", "Stability: no out-of-control signals in the individuals chart."))

    if result.normality is not None:
        # NormalityResult reports an `advisory` and a `p_band`, NOT a boolean
        # `normal`. The first cut of this read a `.normal` attribute through
        # getattr with a None default, so the whole normality line silently
        # vanished from every report and the page looked complete. That is the
        # exact failure mode this file exists to avoid, reached by writing the
        # report against a remembered schema instead of the real one.
        norm = result.normality.value
        if norm.advisory == "concern":
            items.append(
                (
                    "flag",
                    f"Distribution shape is a concern (normality {norm.p_band}) — normal-theory "
                    "Cp/Cpk misstate the tails when the data is skewed.",
                )
            )
        elif norm.advisory == "too_few_to_judge":
            items.append(("flag", f"Too few points to judge distribution shape (n={norm.n})."))
        else:
            items.append(("pass", f"Distribution shape: no concern (normality {norm.p_band})."))

    if result.percentile_capability is not None:
        items.append(
            ("neutral", "A percentile-method capability is also available for the non-normal case; it is not Ppk.")
        )

    for exit_id in result.exits or ():
        items.append(("flag", f"Named exit raised: {exit_id}"))

    return items


def build_story(
    *,
    result: BaselineResult,
    project_name: str,
    chart_png: bytes | None,
    chart_unavailable_reason: str | None,
    provenance_rows: list[tuple[str, str]],
    exported_at: str,
    content_width: float,
) -> list[Any]:
    styles = rt.report_styles()
    verdict_text, tone = build_verdict(result)

    story: list[Any] = []
    story += rt.header(
        project_name=project_name,
        tool_id=TOOL_ID,
        tool_title=TOOL_TITLE,
        version=None,
        styles=styles,
        content_width=content_width,
    )
    story += rt.verdict_banner(verdict_text, tone, styles, content_width)
    story += rt.chart(
        chart_png,
        content_width=content_width,
        styles=styles,
        unavailable_reason=chart_unavailable_reason,
    )
    story += _numbers_table(result, styles, content_width)
    story.append(rt.keep(rt.meaning(build_meaning(result), styles)))
    story.append(rt.keep(rt.report_card(build_report_card(result), styles, content_width)))
    story.append(rt.keep(rt.provenance(provenance_rows, styles, content_width, exported_at=exported_at)))
    return story


def _numbers_table(result: BaselineResult, styles: dict, content_width: float) -> list[Any]:
    from ..charter_pdf_common import kv_table

    rows: list[tuple[str, str]] = []
    desc = result.descriptive.value if result.descriptive else None
    if desc is not None:
        # `sd`, not `stdev` -- DescriptiveStats' real field name. Guessed
        # wrong once here and once for NormalityResult.advisory; both were
        # caught only by running against real data, which is why this
        # module's tests build from run_baseline rather than from fixtures
        # shaped the way the report wishes the schema looked.
        rows.append(("Mean", fmt_number(desc.mean)))
        rows.append(("Std deviation", fmt_number(desc.sd)))
    cap = result.capability.value if result.capability else None
    if cap is not None:
        rows.append(("Cp / Cpk", _index_pair(cap.cp_index, cap.cpk_index, stable=result.stable)))
        rows.append(("Pp / Ppk", _index_pair(cap.pp_index, cap.ppk_index, stable=result.stable)))
    sigma = result.sigma.value if result.sigma else None
    if sigma is not None:
        rows.append(("DPMO / sigma level", f"{_idx(sigma.dpmo)}  /  {_idx(sigma.sigma_level)}"))
    if not rows:
        return []
    return [kv_table(rows, styles, content_width, label_frac=0.3)]
