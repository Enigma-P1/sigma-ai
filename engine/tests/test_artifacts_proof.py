"""Schema/behavior tests for T-20 ProofArtifact: the composed stability +
capability + hypothesis-test + gap pipeline, the threshold-as-declared
verdict, confounder weakening, guardrail tradeoffs, and the not-met /
descriptive-form variants -- plus find_next_cause as a standalone pure
function."""

import pytest

from factories import PROOF_AFTER_VALUES_NOT_MET, make_proof, make_pilot_plan_confounder_checklist
from sigma_engine.artifacts.proof import NextCauseRef, ProofArtifact, RankedSolutionRef, find_next_cause


def test_clean_proof_shows_threshold_met_and_partial_gap_recovery():
    a = ProofArtifact.model_validate(make_proof())
    assert a.verdict.value.threshold_verdict == "met"
    assert a.verdict.value.proof_form == "inferential"
    assert a.verdict.value.weakened is False
    assert a.gap.value.goal_met is False  # threshold cleared, charter goal not yet fully closed
    assert a.gap.value.original_gap == pytest.approx(3.2)
    assert a.gap.value.recovered == pytest.approx(2.17, abs=1e-9)
    assert a.gap.value.remaining == pytest.approx(1.03, abs=1e-9)
    assert a.gap.value.recovered_pct == pytest.approx(67.8125)
    assert a.gap.value.next_cause_ref is not None
    assert a.gap.value.next_cause_ref.cause_id == "c-2"
    assert "next-ranked verified cause" in a.gap.value.loop_verdict


def test_not_met_variant_carries_no_improvement_language():
    a = ProofArtifact.model_validate(make_proof(after_values=PROOF_AFTER_VALUES_NOT_MET))
    assert a.verdict.value.threshold_verdict == "not_met"
    headline = a.verdict.value.headline.lower()
    assert "threshold not met" in headline
    assert "target hit" not in headline
    assert "proven" not in headline


def test_weakened_variant_prints_the_confounder_sentence():
    checklist = make_pilot_plan_confounder_checklist()
    checklist["staffing"] = {"changed": True, "note": "Two new hires started the same week as rollout."}
    a = ProofArtifact.model_validate(make_proof(confounders=checklist))
    assert a.verdict.value.weakened is True
    assert "staffing" in a.verdict.value.confounder_notes[0]
    assert "weakens this proof" in a.verdict.value.headline


def test_goal_fully_met_when_after_mean_reaches_the_charter_goal():
    # Near-constant (not exactly constant) so sigma_overall stays nonzero
    # -- real data is never perfectly flat, and compute_capability's Cpk
    # divides by sigma. Mean is still exactly 3.0, the charter goal.
    at_goal = [3.0, 3.01, 2.99, 3.0, 3.02, 2.98, 3.0, 3.01, 2.99, 3.0]
    a = ProofArtifact.model_validate(make_proof(after_values=at_goal))
    assert a.gap.value.goal_met is True
    assert a.gap.value.remaining <= 0
    assert a.gap.value.loop_verdict == "Goal met -- route to Control."


def test_causes_exhausted_variant_routes_to_analyze_or_human_expert():
    a = ProofArtifact.model_validate(make_proof(next_cause_ref=None))
    assert a.gap.value.goal_met is False
    assert "no further verified" in a.gap.value.loop_verdict
    assert "Analyze" in a.gap.value.loop_verdict


def test_descriptive_proof_form_when_the_design_cant_carry_an_inferential_test():
    # Below the Welch/Mann-Whitney EXIT-06 floors (n<4/8 per sample) --
    # the design honestly can't support a formal test; the tool still
    # computes the threshold check (arithmetic, not inference).
    tiny = make_proof(
        before={"values": [6.0, 6.4, 6.2]}, after={"values": [4.0, 3.9, 4.1]},
    )
    a = ProofArtifact.model_validate(tiny)
    assert a.test_result.refused is True
    assert a.verdict.value.proof_form == "descriptive"
    assert "not statistically tested" in a.verdict.value.headline
    assert a.verdict.value.threshold_verdict == "met"  # arithmetic still runs


def test_material_guardrail_loss_produces_a_tradeoff_sentence_on_a_win():
    a = ProofArtifact.model_validate(make_proof(guardrails=[
        {"metric_ref": "line-2 throughput", "direction": "higher_is_better", "before_value": 100.0, "after_value": 80.0},
    ]))
    assert a.guardrail_report.value[0].material_worsening is True
    assert a.verdict.value.guardrail_tradeoff is not None
    assert "tradeoff" in a.verdict.value.headline.lower()
    assert "never plain 'proven'" in a.verdict.value.headline  # states the rule, never asserts "proven" as a claim
    assert "improvement proven" not in a.verdict.value.headline.lower()


def test_immaterial_guardrail_dip_does_not_trigger_the_tradeoff_sentence():
    a = ProofArtifact.model_validate(make_proof())  # default guardrail: 100 -> 99, a 1% dip
    assert a.guardrail_report.value[0].material_worsening is False
    assert a.verdict.value.guardrail_tradeoff is None


def test_metric_definition_measurement_system_are_single_fields_by_construction():
    # No before/after pair exists to diverge -- the schema shape itself
    # is the enforcement (module docstring).
    fields = set(ProofArtifact.model_fields)
    assert "metric_ref" in fields and "before_metric_ref" not in fields and "after_metric_ref" not in fields


def test_round_trip_via_model_dump():
    a = ProofArtifact.model_validate(make_proof())
    b = ProofArtifact.model_validate(a.model_dump(mode="json"))
    assert b == a


# --- find_next_cause: standalone pure function ------------------------------

RANKED = [
    RankedSolutionRef(rank=1, solution_id="s-1", name="Add checklist", linked_cause_ids=["c-1"]),
    RankedSolutionRef(rank=2, solution_id="s-2", name="Replace injector", linked_cause_ids=["c-2"]),
    RankedSolutionRef(rank=3, solution_id="s-3", name="Retrain operators", linked_cause_ids=["c-3"]),
]
VERIFIED_TEXT = {"c-1": "Fixture alignment not checked", "c-2": "Injector pressure drifts low", "c-3": "Operators skip calibration"}


def test_find_next_cause_returns_the_top_ranked_not_yet_piloted_verified_cause():
    result = find_next_cause(RANKED, verified_cause_ids=["c-1", "c-2", "c-3"], verified_cause_text_by_id=VERIFIED_TEXT, piloted_cause_ids=["c-1"])
    assert result == NextCauseRef(cause_id="c-2", cause_text="Injector pressure drifts low", via_solution_id="s-2", via_solution_name="Replace injector", rank=2)


def test_find_next_cause_skips_unverified_causes():
    result = find_next_cause(RANKED, verified_cause_ids=["c-1"], verified_cause_text_by_id=VERIFIED_TEXT, piloted_cause_ids=["c-1"])
    assert result is None  # c-2/c-3 are linked but never verified


def test_find_next_cause_returns_none_when_every_verified_cause_is_piloted():
    result = find_next_cause(RANKED, verified_cause_ids=["c-1", "c-2", "c-3"], verified_cause_text_by_id=VERIFIED_TEXT, piloted_cause_ids=["c-1", "c-2", "c-3"])
    assert result is None


def test_find_next_cause_respects_rank_order_not_list_order():
    scrambled = [RANKED[2], RANKED[0], RANKED[1]]  # rank 3, 1, 2 given out of order
    result = find_next_cause(scrambled, verified_cause_ids=["c-1", "c-2", "c-3"], verified_cause_text_by_id=VERIFIED_TEXT, piloted_cause_ids=[])
    assert result is not None and result.rank == 1  # lowest rank number wins, regardless of input order
