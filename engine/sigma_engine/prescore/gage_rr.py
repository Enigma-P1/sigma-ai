"""T-35 prescore: the flags a Gage R&R needs BEFORE anyone quotes its %GRR.

Guidance, not rejection (PLAN §4.2's soft/hard split). The study can be
saved half-entered; these say what is missing or fragile about it.

The safety net mirrors prescore/copq.py and prescore/msa.py: the stored
`result` is recomputed from the readings, because a hand-edited
project.json could otherwise carry a %GRR that no longer matches the data
underneath it.
"""

from __future__ import annotations

from ..artifacts.gage_rr import GageRRArtifact
from ..stats import gage_rr as gage_rr_mod
from .common import PrescoreResult

# Conventional study size. Fewer parts makes the part-to-part estimate --
# and therefore every percentage, since they are all ratios against it --
# unstable.
RECOMMENDED_PARTS = 10
RECOMMENDED_OPERATORS = 3
RECOMMENDED_REPLICATES = 2


def run_gage_rr_prescore(artifact: GageRRArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    def add(check_id: str, status: str, detail: str) -> None:
        results.append(PrescoreResult(check_id=check_id, tool_id="T-35", status=status, detail=detail))

    if artifact.design_error:
        add("grr_design", "hard_flag", artifact.design_error)
        return results

    result = artifact.result
    if result is None:  # pragma: no cover -- design_error covers this
        add("grr_design", "hard_flag", "No study computed.")
        return results

    # Safety net: does the stored result still match the stored readings?
    measurements = [
        gage_rr_mod.Measurement(part=r.part, operator=r.operator, value=r.value) for r in artifact.readings
    ]
    try:
        recomputed = gage_rr_mod.compute_gage_rr(
            measurements, tolerance=artifact.tolerance, pool_interaction=artifact.pool_interaction
        )
    except gage_rr_mod.GageRRError as exc:
        add("grr_result_matches_readings", "hard_flag", f"The readings no longer support a study: {exc}")
        return results

    if abs(recomputed.grr_percent_study_variation - result.grr_percent_study_variation) > 1e-6:
        add(
            "grr_result_matches_readings",
            "hard_flag",
            "The stored %GRR does not match the stored readings — the file has been edited outside the app.",
        )
    else:
        add("grr_result_matches_readings", "pass", "The stored result matches the stored readings.")

    if result.parts < RECOMMENDED_PARTS:
        add(
            "grr_parts",
            "flag",
            f"{result.parts} parts (convention is {RECOMMENDED_PARTS}). The parts must also span the real range "
            "of production — a study on parts that are all alike understates part-to-part variation and so "
            "overstates %GRR.",
        )
    else:
        add("grr_parts", "pass", f"{result.parts} parts.")

    if result.operators < RECOMMENDED_OPERATORS:
        add(
            "grr_operators",
            "flag",
            f"{result.operators} operators (convention is {RECOMMENDED_OPERATORS}). Two can show that operators "
            "differ but gives a thin estimate of how much.",
        )
    else:
        add("grr_operators", "pass", f"{result.operators} operators.")

    if result.replicates < RECOMMENDED_REPLICATES:  # pragma: no cover -- the design check rejects this first
        add("grr_replicates", "flag", f"{result.replicates} repeat readings per cell.")
    else:
        add("grr_replicates", "pass", f"{result.replicates} repeat readings per part/operator cell.")

    if result.number_of_distinct_categories < gage_rr_mod.NDC_MINIMUM:
        add(
            "grr_ndc",
            "hard_flag",
            f"{result.number_of_distinct_categories} distinct categories. Below {gage_rr_mod.NDC_MINIMUM} the "
            "gauge sorts parts into groups rather than measuring them, and any capability or before/after "
            "number built on it is mostly measurement noise.",
        )
    else:
        add("grr_ndc", "pass", f"{result.number_of_distinct_categories} distinct categories.")

    if result.verdict == "unacceptable":
        add(
            "grr_verdict",
            "hard_flag",
            f"%GRR is {result.grr_percent_study_variation:.1f}% of study variation — the measurement system is "
            "not fit for this characteristic. Fix the measurement before trusting anything measured with it.",
        )
    elif result.verdict == "marginal":
        add(
            "grr_verdict",
            "flag",
            f"%GRR is {result.grr_percent_study_variation:.1f}% — usable with caution, and only where the cost "
            "of improving the gauge genuinely outweighs the cost of the error it lets through.",
        )
    else:
        add("grr_verdict", "pass", f"%GRR is {result.grr_percent_study_variation:.1f}% — acceptable.")

    if result.interaction_pooled:
        add(
            "grr_interaction",
            "pass",
            "The operator-by-part interaction was not significant and was pooled into repeatability.",
        )
    else:
        add(
            "grr_interaction",
            "flag",
            "The operator-by-part interaction was kept in the model — some operators measure some parts "
            "differently than others do, which is worth understanding before training is blamed.",
        )

    # ONE entry, not one per warning. check_id is the identity of a check
    # everywhere downstream -- it keys the results strip's pills and their
    # test ids -- so emitting `grr_warning` N times produced N colliding
    # entries. The warnings are joined into a single caveat instead, which
    # is also how a reader wants them: one place that says what this study
    # could not resolve.
    if result.warnings:
        add("grr_warnings", "flag", " · ".join(result.warnings))

    return results
