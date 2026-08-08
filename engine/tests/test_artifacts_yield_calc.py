"""Schema tests for T-10 YieldCalcArtifact, including the G-yield-01
golden (matrix golden-coverage rule: T-10 carries a NIST-reference unit
test -- the DPMO/sigma-level half below reproduces one of the exact
published-table rows test_stats_sigma_level.py already reference-checks
against Wikipedia's "Six Sigma" article and MoreSteam.com's conversion
table, both fetched live 2026-08-07 per that module's own docstring)."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from factories import make_dpmo_block, make_yield_calc, make_yield_calc_steps
from sigma_engine.artifacts.yield_calc import (
    DpmoBlock,
    YieldCalcArtifact,
    YieldStep,
    compute_dpmo_result,
    compute_rty_result,
)
from sigma_engine.provenance import compute
from sigma_engine.stats.sigma_level import dpu, fpy_from_dpu, rty, sigma_level_from_dpmo


def test_accepts_a_complete_yield_calc():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    assert artifact.rty_result is not None
    assert artifact.dpmo_result is not None


# ---------------------------------------------------------------------------
# G-yield-01 golden: a 3-step line, hand-verified by hand-computing DPU
# (plain division, exact) and then feeding it through the SAME formula this
# module reuses (e^-DPU) rather than re-deriving an independent number --
# the same "hand-verify the formula and inputs, lean on math.exp/calculator
# for the transcendental step" idiom test_stats_sigma_level.py's own
# test_dpu_fpy_rty_hand_computed already uses in this codebase.
#
# Step 1: 100 units in, 95 first-pass-correct -> 5 defects -> DPU = 5/100
#         = 0.05 exactly (hand-checkable long division).
# Step 2: 95 units in, 90 first-pass-correct -> 5 defects -> DPU = 5/95
#         = 0.0526315789... (hand-checkable: 5/95 = 1/19).
# Step 3: 90 units in, 88 first-pass-correct -> 2 defects -> DPU = 2/90
#         = 0.0222222... (hand-checkable: 2/90 = 1/45).
# FPY_i = e^-DPU_i (this module's fpy_at_step, = stats/sigma_level.py's
# fpy_from_dpu, reused verbatim). RTY = product(FPY_i) = e^-(sum of DPUs)
# = e^-0.124853801... ~= 0.882626 (both forms asserted equal below, which
# is itself the DPU<->RTY log identity a hand-check can verify: DPU_total
# ~= -ln(RTY)).
# ---------------------------------------------------------------------------


def test_golden_g_yield_01_three_step_line_rty():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    steps = artifact.steps

    expected_dpu = [5 / 100, 5 / 95, 2 / 90]
    for step, dpu_expected in zip(steps, expected_dpu):
        assert step.dpu_at_step == pytest.approx(dpu_expected)
        assert step.fpy_at_step == pytest.approx(math.exp(-dpu_expected))

    expected_rty = math.exp(-sum(expected_dpu))
    assert expected_rty == pytest.approx(0.8826259320313404)
    assert artifact.rty_result.value == pytest.approx(expected_rty)
    # Equivalent form via the reused rty() function directly, over the
    # per-step fpy_at_step values -- proves compute_rty_result isn't doing
    # its own separate arithmetic from what the per-row computed fields show.
    assert artifact.rty_result.value == pytest.approx(rty([s.fpy_at_step for s in steps]))


def test_golden_g_yield_01_dpmo_and_sigma_level_matches_published_4_sigma_row():
    """1242 defects / 100000 units / 2 opportunities-per-unit -> DPMO =
    1e6*1242/(100000*2) = 6210 exactly -- the published Wikipedia "Six
    Sigma" / MoreSteam.com 4-sigma-with-shift table row (both independently
    reference-tested in test_stats_sigma_level.py's
    PUBLISHED_DPMO_BY_SIGMA_LEVEL). Cross-checking against that same
    published table here, not just against this module's own math, is the
    NIST/published-reference half of T-10's golden coverage."""
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    result = artifact.dpmo_result

    assert result.value.dpmo == pytest.approx(6210.0)
    assert result.value.sigma_level == pytest.approx(4.0, abs=0.01)
    assert result.value.convention == "with 1.5σ shift"

    # Cross-checked against the stats module's own tested convention
    # (task brief) -- sigma_level_from_dpmo is the exact function
    # compute_sigma_level (and thus compute_dpmo_result) calls beneath it.
    expected_level, expected_convention = sigma_level_from_dpmo(6210.0, apply_shift=True)
    assert result.value.sigma_level == pytest.approx(expected_level)
    assert result.value.convention == expected_convention


def test_shift_convention_always_labeled_both_ways():
    with_shift = YieldCalcArtifact.model_validate(make_yield_calc())
    without_shift = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(apply_sigma_shift=False))
    )
    assert with_shift.dpmo_result.value.convention == "with 1.5σ shift"
    assert without_shift.dpmo_result.value.convention == "without shift"
    # Same frozen 1.5 delta as stats/sigma_level.py's own convention test.
    assert with_shift.dpmo_result.value.sigma_level - without_shift.dpmo_result.value.sigma_level == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# compute_rty_result / compute_dpmo_result unit tests (direct, off YieldStep/
# DpmoBlock rather than the whole artifact) -- both computed both ways.
# ---------------------------------------------------------------------------


def test_compute_rty_result_matches_hand_sum():
    steps = [YieldStep.model_validate(s) for s in make_yield_calc_steps()]
    result = compute_rty_result(steps)
    expected = rty([fpy_from_dpu(dpu(s.units_in - s.first_pass_correct, s.units_in)) for s in steps])
    assert result.value == pytest.approx(expected)
    assert result.provenance.method
    assert result.provenance.input_hash


def test_compute_dpmo_result_matches_hand_computed():
    block = DpmoBlock.model_validate(make_dpmo_block())
    result = compute_dpmo_result(block)
    assert result.value.dpmo == pytest.approx(1_000_000.0 * 1242 / (100_000 * 2))
    assert result.provenance.method
    assert result.provenance.input_hash


# ---------------------------------------------------------------------------
# Tamper tests (copq.py's test idiom): posting a wrong computed value is
# discarded and recomputed, both for rty_result and dpmo_result.
# ---------------------------------------------------------------------------


def test_posted_rty_result_is_discarded_and_recomputed():
    art = YieldCalcArtifact.model_validate(
        make_yield_calc(rty_result=compute(0.01, method="tampered", input_data=[]).model_dump(mode="json"))
    )
    assert art.rty_result.value == pytest.approx(0.8826259320313404)
    assert art.rty_result.value != pytest.approx(0.01)
    assert "RTY" in art.rty_result.provenance.method


def test_posted_dpmo_result_is_discarded_and_recomputed():
    from sigma_engine.stats.sigma_level import SigmaLevelResult

    fake = SigmaLevelResult(dpmo=1.0, sigma_level=9.0, convention="with 1.5σ shift")
    art = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_result=compute(fake, method="tampered", input_data=[]).model_dump(mode="json"))
    )
    assert art.dpmo_result.value.dpmo == pytest.approx(6210.0)
    assert art.dpmo_result.value.sigma_level != pytest.approx(9.0)


def test_round_trip_via_model_dump():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc())
    round_tripped = YieldCalcArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


# ---------------------------------------------------------------------------
# Serial assumption: RTY only computed/claimed under steps_in_series=true.
# ---------------------------------------------------------------------------


def test_rty_is_none_when_steps_not_declared_in_series():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps_in_series=False))
    assert artifact.rty_result is None


def test_steps_in_series_is_required():
    body = make_yield_calc()
    del body["steps_in_series"]
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(body)


# ---------------------------------------------------------------------------
# DPMO block is optional and independent of the steps table.
# ---------------------------------------------------------------------------


def test_dpmo_block_is_optional():
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(dpmo_block=None))
    assert artifact.dpmo_block is None
    assert artifact.dpmo_result is None
    # The steps table half is untouched by the DPMO block's absence.
    assert artifact.rty_result is not None


def test_dpmo_block_independent_of_steps_in_series():
    """A DPMO calculation stands alone even when the steps aren't serial."""
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps_in_series=False))
    assert artifact.rty_result is None
    assert artifact.dpmo_result is not None
    assert artifact.dpmo_result.value.dpmo == pytest.approx(6210.0)


# ---------------------------------------------------------------------------
# Per-step sanity constraints: what IS enforced.
# ---------------------------------------------------------------------------


def test_rejects_units_in_not_positive():
    steps = make_yield_calc_steps()
    steps[0]["units_in"] = 0
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(make_yield_calc(steps=steps))


def test_rejects_first_pass_correct_above_units_in():
    steps = make_yield_calc_steps()
    steps[0]["first_pass_correct"] = 101  # units_in is 100
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(make_yield_calc(steps=steps))


def test_rejects_negative_first_pass_correct():
    steps = make_yield_calc_steps()
    steps[0]["first_pass_correct"] = -1
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(make_yield_calc(steps=steps))


def test_rejects_empty_steps():
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(make_yield_calc(steps=[]))


def test_zero_defect_step_is_fpy_one():
    steps = [{"name": "Perfect step", "units_in": 50, "first_pass_correct": 50}]
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps=steps, dpmo_block=None))
    assert artifact.steps[0].defects_at_step == 0
    assert artifact.steps[0].dpu_at_step == 0
    assert artifact.steps[0].fpy_at_step == pytest.approx(1.0)
    assert artifact.rty_result.value == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# What is deliberately NOT enforced: a later step's units_in is never
# checked against the prior step's first_pass_correct/defects_at_step --
# real lines rework and scrap units between steps.
# ---------------------------------------------------------------------------


def test_later_step_may_receive_more_units_than_prior_step_passed():
    """Step 2 receives 120 units even though step 1 only passed 95 --
    reworked/returned units re-entering the line. This must validate
    cleanly: the matrix's standard definition computes each step's FPY on
    its own entering units, independent of neighboring steps."""
    steps = [
        {"name": "Step 1", "units_in": 100, "first_pass_correct": 95},
        {"name": "Step 2 (rework rejoins the line)", "units_in": 120, "first_pass_correct": 118},
    ]
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps=steps, dpmo_block=None))
    assert artifact.steps[1].units_in == 120
    assert artifact.rty_result is not None  # no cross-step constraint blocked it


def test_later_step_may_receive_fewer_units_than_prior_step_passed():
    """Step 2 receives fewer units than step 1 passed -- some good units
    were scrapped/diverted before reaching step 2. Also must validate."""
    steps = [
        {"name": "Step 1", "units_in": 100, "first_pass_correct": 95},
        {"name": "Step 2 (some good units diverted elsewhere)", "units_in": 80, "first_pass_correct": 78},
    ]
    artifact = YieldCalcArtifact.model_validate(make_yield_calc(steps=steps, dpmo_block=None))
    assert artifact.steps[1].units_in == 80
    assert artifact.rty_result is not None


# ---------------------------------------------------------------------------
# Opportunity-inflation honesty guard (schema-level floor).
# ---------------------------------------------------------------------------


def test_opportunities_above_one_without_justification_is_rejected():
    with pytest.raises(ValidationError, match="opportunity_justification"):
        YieldCalcArtifact.model_validate(
            make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=3, opportunity_justification=""))
        )


def test_opportunities_above_one_with_whitespace_only_justification_is_rejected():
    with pytest.raises(ValidationError, match="opportunity_justification"):
        YieldCalcArtifact.model_validate(
            make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=3, opportunity_justification="   "))
        )


def test_opportunities_above_one_with_real_justification_is_accepted():
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(
            opportunities_per_unit=3,
            opportunity_justification="Three inspected weld points per bracket, per the weld QC spec.",
        ))
    )
    assert artifact.dpmo_block.opportunities_per_unit == 3


def test_opportunities_of_exactly_one_needs_no_justification():
    artifact = YieldCalcArtifact.model_validate(
        make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=1, opportunity_justification=""))
    )
    assert artifact.dpmo_block.opportunities_per_unit == 1


def test_opportunities_below_one_is_rejected():
    with pytest.raises(ValidationError):
        YieldCalcArtifact.model_validate(
            make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=0.5, opportunity_justification="half?"))
        )
