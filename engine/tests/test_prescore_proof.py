"""Prescore tests for T-20: threshold-as-declared, confounder echo,
guardrail-section presence, gap arithmetic tamper-check, and the single-
copy metric-identity guarantee."""

from factories import PROOF_AFTER_VALUES_NOT_MET, make_proof, make_pilot_plan_confounder_checklist
from sigma_engine.artifacts.proof import ProofArtifact
from sigma_engine.prescore.proof import run_proof_prescore

EXPECTED_CHECK_IDS = {
    "threshold_as_declared", "confounder_echo_present", "guardrail_section_present_or_explicitly_none",
    "gap_arithmetic_consistency", "metric_identity_single_copy",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_proof_passes_every_check():
    a = ProofArtifact.model_validate(make_proof())
    results = _by_id(run_proof_prescore(a))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id, r in results.items():
        assert r.status == "pass", f"{check_id}: expected pass, got {r.status} ({r.detail})"


def test_threshold_as_declared_reads_not_met_for_the_not_met_variant():
    a = ProofArtifact.model_validate(make_proof(after_values=PROOF_AFTER_VALUES_NOT_MET))
    results = _by_id(run_proof_prescore(a))
    assert results["threshold_as_declared"].status == "pass"
    assert "not_met" in results["threshold_as_declared"].detail


# ---------------------------------------------------------------------------
# Also-fix (critic finding 6): threshold_as_declared used to be vacuous --
# `v in ("met", "not_met")` is always true, since threshold_verdict's own
# type (Literal["met", "not_met"]) already guarantees it, so the check
# could never fail no matter what the stored verdict said. Now it recomputes
# the after value (weight-aware, Fix 3) and compares against a fresh
# met/not_met read -- both ways: untampered passes (covered above), a
# hand-edited verdict either direction hard_flags.
# ---------------------------------------------------------------------------


def test_threshold_as_declared_hard_flags_a_met_verdict_stored_over_not_met_data():
    a = ProofArtifact.model_validate(make_proof())  # data says "met"
    assert a.verdict.value.threshold_verdict == "met"
    tampered_value = a.verdict.value.model_copy(update={"threshold_verdict": "not_met"})
    tampered = a.model_copy(update={"verdict": a.verdict.model_copy(update={"value": tampered_value})})
    results = _by_id(run_proof_prescore(tampered))
    assert results["threshold_as_declared"].status == "hard_flag"
    assert "hand-edited" in results["threshold_as_declared"].detail


def test_threshold_as_declared_hard_flags_a_not_met_verdict_stored_over_met_data():
    a = ProofArtifact.model_validate(make_proof(after_values=PROOF_AFTER_VALUES_NOT_MET))  # data says "not_met"
    assert a.verdict.value.threshold_verdict == "not_met"
    tampered_value = a.verdict.value.model_copy(update={"threshold_verdict": "met"})
    tampered = a.model_copy(update={"verdict": a.verdict.model_copy(update={"value": tampered_value})})
    results = _by_id(run_proof_prescore(tampered))
    assert results["threshold_as_declared"].status == "hard_flag"
    assert "hand-edited" in results["threshold_as_declared"].detail


def test_confounder_echo_present_passes_on_the_weakened_variant_too():
    checklist = make_pilot_plan_confounder_checklist()
    checklist["staffing"] = {"changed": True, "note": "Two new hires started the same week as rollout."}
    a = ProofArtifact.model_validate(make_proof(confounders=checklist))
    results = _by_id(run_proof_prescore(a))
    assert results["confounder_echo_present"].status == "pass"
    assert "1 confounder(s) changed" in results["confounder_echo_present"].detail


def test_guardrail_section_flags_an_explicitly_empty_guardrail_list():
    a = ProofArtifact.model_validate(make_proof(guardrails=[]))
    results = _by_id(run_proof_prescore(a))
    assert results["guardrail_section_present_or_explicitly_none"].status == "flag"


def test_gap_arithmetic_consistency_passes_on_a_clean_recompute():
    a = ProofArtifact.model_validate(make_proof())
    results = _by_id(run_proof_prescore(a))
    assert results["gap_arithmetic_consistency"].status == "pass"
    assert "recomputed and matches" in results["gap_arithmetic_consistency"].detail


def test_gap_arithmetic_consistency_flags_a_hand_edited_remainder():
    # model_copy (not model_validate) never re-runs _recompute -- the
    # right tool to simulate a hand-edited on-disk file whose stored
    # numbers no longer match what the inputs actually compute to
    # (prescore/hypothesis.py's route_tamper_check precedent).
    a = ProofArtifact.model_validate(make_proof())
    tampered_value = a.gap.value.model_copy(update={"remaining": 0.0, "goal_met": True})
    tampered_gap = a.gap.model_copy(update={"value": tampered_value})
    tampered = a.model_copy(update={"gap": tampered_gap})
    results = _by_id(run_proof_prescore(tampered))
    assert results["gap_arithmetic_consistency"].status == "hard_flag"
    assert "hand-edited" in results["gap_arithmetic_consistency"].detail


def test_metric_identity_single_copy_passes_when_all_three_refs_are_filled():
    a = ProofArtifact.model_validate(make_proof())
    results = _by_id(run_proof_prescore(a))
    assert results["metric_identity_single_copy"].status == "pass"
    assert "one copy each" in results["metric_identity_single_copy"].detail
