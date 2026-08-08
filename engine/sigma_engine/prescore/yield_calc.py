"""T-10 prescore: R-MEA-09 rule-checkable lines.

Two "matches recomputed" safety nets (copq.py's total_matches_rows /
msa.py's result_matches_inputs idiom -- the GET /project/{id}/artifacts/
{id} path returns the stored dict verbatim without re-running the
Pydantic validator, so a hand-edited on-disk JSON file could in principle
carry a value that no longer matches its own inputs) plus a structural
check on the serial claim and the opportunity-inflation guard's "teeth" --
the part a schema-level non-empty check can't do: screening the
justification text itself for a placeholder non-answer.

"Both ways" (the build brief's own phrase for what this guard must do, at
minimum): (1) the check reports a definite pass/hard_flag whichever way
opportunities_per_unit falls -- not-inflated (<=1) is reported pass, not
silently skipped, exactly like the inflated case is reported when it is
honestly justified; and (2) the guard fires on both an outright-empty AND
a low-effort placeholder justification (PLACEHOLDER_OPPORTUNITY_
JUSTIFICATIONS below) -- a single throwaway word is enough to clear the
schema's bare non-empty gate but not enough to clear this one.
"""

from __future__ import annotations

from ..artifacts.yield_calc import YieldCalcArtifact, compute_dpmo_result, compute_rty_result
from .common import PrescoreResult

_RELATIVE_TOLERANCE = 1e-9

# R-MEA-09 pre-score: the opportunity-inflation guard's "teeth" beyond the
# schema's bare non-empty check. Case-insensitive EXACT match against the
# trimmed justification -- the same deliberately-narrow, no-substring-match
# design as R-DEF-04's owner-name blocklist (prescore/charter.py's
# PLACEHOLDER_OWNER_NAMES) so a real justification that happens to use one
# of these words in passing isn't caught by accident; only a justification
# that IS one of these words, alone, is.
PLACEHOLDER_OPPORTUNITY_JUSTIFICATIONS = frozenset({
    "n/a", "na", "none", "tbd", "unknown", "several", "many", "various",
    "multiple", "misc", "miscellaneous", "some", "assorted", "etc", "other", "others",
})


def _close_enough(a: float, b: float) -> bool:
    return abs(a - b) <= _RELATIVE_TOLERANCE * max(1.0, abs(a), abs(b))


def run_yield_calc_prescore(artifact: YieldCalcArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    # -- RTY only claimed under the explicit serial assumption ------------
    rty_consistent = (artifact.steps_in_series and artifact.rty_result is not None) or (
        not artifact.steps_in_series and artifact.rty_result is None
    )
    results.append(PrescoreResult(
        check_id="rty_only_claimed_in_series",
        tool_id="T-10",
        status="pass" if rty_consistent else "hard_flag",
        detail=(
            f"steps_in_series={artifact.steps_in_series}, rty_result "
            f"{'present' if artifact.rty_result is not None else 'absent'} -- consistent"
            if rty_consistent else
            f"steps_in_series={artifact.steps_in_series} but rty_result is "
            f"{'present' if artifact.rty_result is not None else 'absent'} -- RTY must be computed if and only if "
            "the steps are declared in series (matrix II.E.1)"
        ),
    ))

    if artifact.rty_result is not None:
        recomputed_rty = compute_rty_result(artifact.steps)
        rty_matches = _close_enough(recomputed_rty.value, artifact.rty_result.value)
        results.append(PrescoreResult(
            check_id="rty_matches_recomputed",
            tool_id="T-10",
            status="pass" if rty_matches else "flag",
            detail=(
                "stored RTY matches recomputed product(step FPYs)" if rty_matches
                else f"stored RTY {artifact.rty_result.value} != recomputed {recomputed_rty.value} -- "
                "the file may have been hand-edited"
            ),
        ))

    # -- DPMO block (optional -- both checks skipped entirely when absent) -
    block = artifact.dpmo_block
    if block is not None:
        if artifact.dpmo_result is None:
            # _recompute always sets this alongside dpmo_block on a valid
            # artifact -- stay honest about the unexpected state rather
            # than crash the route (msa.py's run_msa_prescore precedent).
            results.append(PrescoreResult(
                check_id="dpmo_result_matches_recomputed", tool_id="T-10", status="flag",
                detail="dpmo_block is set but dpmo_result is missing",
            ))
        else:
            recomputed_dpmo = compute_dpmo_result(block)
            dpmo_matches = _close_enough(recomputed_dpmo.value.dpmo, artifact.dpmo_result.value.dpmo) and _close_enough(
                recomputed_dpmo.value.sigma_level, artifact.dpmo_result.value.sigma_level
            )
            results.append(PrescoreResult(
                check_id="dpmo_result_matches_recomputed",
                tool_id="T-10",
                status="pass" if dpmo_matches else "flag",
                detail=(
                    "stored DPMO/sigma level matches a fresh recompute from defects/units/opportunities_per_unit"
                    if dpmo_matches else
                    f"stored DPMO {artifact.dpmo_result.value.dpmo}/sigma {artifact.dpmo_result.value.sigma_level} "
                    f"!= recomputed {recomputed_dpmo.value.dpmo}/{recomputed_dpmo.value.sigma_level} -- the file "
                    "may have been hand-edited"
                ),
            ))

        justification = block.opportunity_justification.strip()
        if block.opportunities_per_unit <= 1:
            results.append(PrescoreResult(
                check_id="opportunity_inflation_justified",
                tool_id="T-10",
                status="pass",
                detail=f"opportunities_per_unit={block.opportunities_per_unit} -- no inflation risk, no justification needed",
            ))
        elif justification and justification.lower() not in PLACEHOLDER_OPPORTUNITY_JUSTIFICATIONS:
            results.append(PrescoreResult(
                check_id="opportunity_inflation_justified",
                tool_id="T-10",
                status="pass",
                detail=f"opportunities_per_unit={block.opportunities_per_unit} is justified: {justification}",
            ))
        else:
            results.append(PrescoreResult(
                check_id="opportunity_inflation_justified",
                tool_id="T-10",
                status="hard_flag",
                detail=(
                    f"opportunities_per_unit={block.opportunities_per_unit} > 1 with no real justification "
                    f"({'empty' if not justification else f'placeholder: {justification!r}'}) -- name what the "
                    "extra opportunities actually are, or sigma is being flattered by inflated opportunity "
                    "counting (rubric R-MEA-09)"
                ),
            ))

    return results
