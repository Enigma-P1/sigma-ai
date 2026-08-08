"""Prescore tests for T-10: the RTY-only-in-series structural check, the
two matches-recomputed tamper nets (rty_result, dpmo_result), and the
opportunity-inflation guard's "teeth" -- both ways, per the build brief:
the check reports pass/hard_flag whichever way opportunities_per_unit
falls, and it activates on both an empty AND a placeholder justification.
"""

from __future__ import annotations

from factories import make_dpmo_block, make_yield_calc
from sigma_engine.artifacts.yield_calc import YieldCalcArtifact
from sigma_engine.prescore.yield_calc import run_yield_calc_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_consistent_yield_calc_passes_every_check():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    results = _by_id(run_yield_calc_prescore(artifact))
    assert results["rty_only_claimed_in_series"].status == "pass"
    assert results["rty_matches_recomputed"].status == "pass"
    assert results["dpmo_result_matches_recomputed"].status == "pass"
    assert results["opportunity_inflation_justified"].status == "pass"


# ---------------------------------------------------------------------------
# Tamper nets: a hand-edited-on-disk value no longer matches a fresh
# recompute (copq.py's test_tampered_total_flags idiom -- model_copy bypasses
# the validator, simulating a stored value the load path returns verbatim).
# ---------------------------------------------------------------------------


def test_tampered_rty_flags():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    tampered = artifact.model_copy(update={"rty_result": artifact.rty_result.model_copy(update={"value": 0.01})})
    results = _by_id(run_yield_calc_prescore(tampered))
    assert results["rty_matches_recomputed"].status == "flag"


def test_tampered_dpmo_flags():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    tampered_value = artifact.dpmo_result.value.model_copy(update={"dpmo": 1.0})
    tampered = artifact.model_copy(update={"dpmo_result": artifact.dpmo_result.model_copy(update={"value": tampered_value})})
    results = _by_id(run_yield_calc_prescore(tampered))
    assert results["dpmo_result_matches_recomputed"].status == "flag"


# ---------------------------------------------------------------------------
# Structural check: RTY only claimed under the explicit serial assumption --
# both directions of the mismatch are caught (each simulated via model_copy,
# since the schema's own _recompute makes either mismatch unreachable via
# ordinary validation).
# ---------------------------------------------------------------------------


def test_rty_present_without_series_hard_flags():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps_in_series=False))
    assert artifact.rty_result is None
    smuggled_rty = YieldCalcArtifact.model_validate(make_yield_calc()).rty_result
    tampered = artifact.model_copy(update={"rty_result": smuggled_rty})
    results = _by_id(run_yield_calc_prescore(tampered))
    assert results["rty_only_claimed_in_series"].status == "hard_flag"


def test_rty_missing_while_in_series_hard_flags():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    assert artifact.rty_result is not None
    tampered = artifact.model_copy(update={"rty_result": None})
    results = _by_id(run_yield_calc_prescore(tampered))
    assert results["rty_only_claimed_in_series"].status == "hard_flag"
    # No rty_result on the artifact -> nothing to run the matches-recomputed
    # check against, so it is skipped entirely, not fabricated as a pass.
    assert "rty_matches_recomputed" not in results


# ---------------------------------------------------------------------------
# DPMO block optional: its checks are skipped entirely (not fabricated as
# passes) when the block is absent.
# ---------------------------------------------------------------------------


def test_no_dpmo_block_skips_dpmo_checks_entirely():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(dpmo_block=None))
    results = _by_id(run_yield_calc_prescore(artifact))
    assert "dpmo_result_matches_recomputed" not in results
    assert "opportunity_inflation_justified" not in results
    # The steps-table checks still run.
    assert "rty_only_claimed_in_series" in results
    assert "rty_matches_recomputed" in results


# ---------------------------------------------------------------------------
# Opportunity-inflation guard, "both ways."
# ---------------------------------------------------------------------------


def test_opportunities_not_inflated_passes_and_says_so():
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=1, opportunity_justification=""))
    )
    results = _by_id(run_yield_calc_prescore(artifact))
    check = results["opportunity_inflation_justified"]
    assert check.status == "pass"
    assert "no inflation risk" in check.detail


def test_opportunities_inflated_with_real_justification_passes():
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(
            opportunities_per_unit=3,
            opportunity_justification="Three inspected weld points per bracket, per the weld QC spec.",
        ))
    )
    results = _by_id(run_yield_calc_prescore(artifact))
    assert results["opportunity_inflation_justified"].status == "pass"


def test_opportunities_inflated_with_placeholder_justification_hard_flags():
    """'various' clears the schema's bare non-empty gate but is exactly the
    classic DPMO game the prescore's teeth exist to catch."""
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=3, opportunity_justification="various"))
    )
    results = _by_id(run_yield_calc_prescore(artifact))
    check = results["opportunity_inflation_justified"]
    assert check.status == "hard_flag"
    assert "various" in check.detail


def test_opportunities_inflated_with_other_placeholder_words_hard_flag():
    for placeholder in ["many", "N/A", "  TBD  ", "Multiple", "misc"]:
        artifact = YieldCalcArtifact.model_validate(
            make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=2, opportunity_justification=placeholder))
        )
        results = _by_id(run_yield_calc_prescore(artifact))
        assert results["opportunity_inflation_justified"].status == "hard_flag", f"expected {placeholder!r} to be caught"


def test_placeholder_blocklist_is_exact_match_not_substring():
    """The blocklist is deliberately narrow (R-DEF-04's owner-name
    blocklist precedent): a real justification that happens to CONTAIN a
    blocked word isn't caught by accident -- only a justification that IS
    one of those words, alone, is."""
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(
            opportunities_per_unit=3,
            opportunity_justification=(
                "Various failure types are tracked separately: weld strength, seal integrity, "
                "and fill weight -- three named opportunities per unit."
            ),
        ))
    )
    results = _by_id(run_yield_calc_prescore(artifact))
    assert results["opportunity_inflation_justified"].status == "pass"
