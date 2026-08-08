"""T-12 prescore: result-matches-inputs (mirrors prescore/copq.py's
total-matches-rows safety net for a hand-edited on-disk JSON file -- the
GET /project/{id}/artifacts/{id} path returns the stored dict verbatim,
without re-running MsaArtifact's validator, so a hand-edited `result` can
in principle drift from the stored readings) plus the matrix §4a sample-
guidance flags (>=10 items, >=2 valid repeats/item). Guidance, not a hard
rejection (PLAN §4.2's soft/hard split) -- these are prescore flags.
"""

from __future__ import annotations

from ..artifacts.msa import MsaArtifact
from ..stats import msa as msa_mod
from ..stats.constants import MSA_MIN_ITEMS_GUIDANCE, MSA_MIN_REPEATS_PER_ITEM
from .common import PrescoreResult


def _recompute(artifact: MsaArtifact) -> msa_mod.MsaResult:
    if artifact.data_type == "continuous":
        items = [msa_mod.ItemRepeats(item_id=r.item_id, readings=tuple(r.readings)) for r in artifact.continuous_items]
        return msa_mod.run_continuous_msa(items, gauge_increment=artifact.gauge_increment, usl=artifact.usl, lsl=artifact.lsl)
    ratings = [msa_mod.AttributeRating(item_id=r.item_id, rater_a=r.rater_a, rater_b=r.rater_b) for r in artifact.attribute_items]
    return msa_mod.run_attribute_msa(ratings)


def run_msa_prescore(artifact: MsaArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    if artifact.result is None:
        # _recompute_result always sets this on a valid artifact -- stay
        # honest about the unexpected state rather than crash the route.
        results.append(PrescoreResult(check_id="verdict_recorded", tool_id="T-12", status="flag", detail="no result on the artifact"))
        return results

    results.append(PrescoreResult(
        check_id="verdict_recorded", tool_id="T-12", status="pass", detail=f"verdict recorded: {artifact.result.verdict}",
    ))

    recomputed = _recompute(artifact)
    matches = recomputed.verdict == artifact.result.verdict
    results.append(PrescoreResult(
        check_id="result_matches_inputs", tool_id="T-12",
        status="pass" if matches else "flag",
        detail=(
            "stored verdict matches recomputed verdict from the stored readings" if matches
            else f"stored verdict {artifact.result.verdict!r} != recomputed {recomputed.verdict!r} -- the file may have been hand-edited"
        ),
    ))

    if artifact.data_type == "continuous":
        item_count = len(artifact.continuous_items)
        short_items = [
            r.item_id for r in artifact.continuous_items
            if len([x for x in r.readings if x is not None]) < MSA_MIN_REPEATS_PER_ITEM
        ]
        results.append(PrescoreResult(
            check_id="repeats_per_item", tool_id="T-12",
            status="pass" if not short_items else "flag",
            detail=(
                "every item has >= 2 valid repeat readings" if not short_items
                else f"items with < {MSA_MIN_REPEATS_PER_ITEM} valid repeats (excluded from s_repeat, matrix §4a): {short_items}"
            ),
        ))
    else:
        item_count = len(artifact.attribute_items)

    results.append(PrescoreResult(
        check_id="item_count_meets_guidance", tool_id="T-12",
        status="pass" if item_count >= MSA_MIN_ITEMS_GUIDANCE else "flag",
        detail=f"{item_count} items (guidance: >= {MSA_MIN_ITEMS_GUIDANCE} spanning the observed range, matrix §4a)",
    ))

    return results
