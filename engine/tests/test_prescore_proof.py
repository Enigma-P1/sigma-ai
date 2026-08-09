"""Prescore tests for T-20: threshold-as-declared, confounder echo,
guardrail-section presence, gap arithmetic tamper-check, the single-copy
metric-identity guarantee, and the capability-language-on-unstable
contradiction check (M6 fidelity-panel fix)."""

from factories import PROOF_BEFORE_VALUES, PROOF_AFTER_VALUES_MET, PROOF_AFTER_VALUES_NOT_MET, make_proof, make_pilot_plan_confounder_checklist
from sigma_engine.artifacts.proof import ProofArtifact
from sigma_engine.prescore.proof import run_proof_prescore

EXPECTED_CHECK_IDS = {
    "threshold_as_declared", "confounder_echo_present", "guardrail_section_present_or_explicitly_none",
    "gap_arithmetic_consistency", "metric_identity_single_copy", "capability_language_requires_stability",
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


# ---------------------------------------------------------------------------
# M6 fidelity-panel fix: capability-index vocabulary in free text on an
# artifact whose OWN computed stability read says a window is unstable is a
# schema-visible contradiction (rubric R-MEA-08/R-MEA-09 -- the engine
# gated Cpk on stability, so no free-text claim of it can be backed).
# Fires ONLY when a computed stable field is False; word-boundary matched.
# The stock make_proof fixture's 10-point windows read not-stable via the
# EXIT-04 point-count floor, which is exactly the "computed state says
# stability failed" precondition -- asserted, not assumed, below.
# ---------------------------------------------------------------------------

# 20-point windows built by doubling the stock 10-point ones -- verified
# engine-stable (n=20 clears the EXIT-04 floor, no rule-1/rule-4 signal).
STABLE_BEFORE_VALUES = list(PROOF_BEFORE_VALUES) * 2
STABLE_AFTER_VALUES = list(PROOF_AFTER_VALUES_MET) * 2


def _stable_proof(**overrides):
    body = make_proof(after_values=STABLE_AFTER_VALUES, **overrides)
    body["before"]["values"] = STABLE_BEFORE_VALUES
    return body


def test_capability_language_on_unstable_flags_naming_field_and_term():
    a = ProofArtifact.model_validate(make_proof(notes="Cpk was about 1.35, comfortably inside spec on the before window."))
    assert a.before_baseline.stable is False  # the fixture's premise: computed state says not stable
    results = _by_id(run_proof_prescore(a))
    r = results["capability_language_requires_stability"]
    assert r.status == "flag"
    assert "stability failed here" in r.detail
    assert "can't be backed by these numbers" in r.detail
    assert "R-MEA-08" in r.detail and "R-MEA-09" in r.detail
    assert "notes" in r.detail and "cpk" in r.detail


def test_capability_language_in_a_confounder_note_is_named_by_field():
    checklist = make_pilot_plan_confounder_checklist()
    checklist["measurement"] = {"changed": False, "note": "Process capability held up fine per the ops lead."}
    a = ProofArtifact.model_validate(make_proof(confounders=checklist))
    assert a.after_baseline.stable is False
    r = _by_id(run_proof_prescore(a))["capability_language_requires_stability"]
    assert r.status == "flag"
    assert "confounders.measurement.note" in r.detail
    assert "process capability" in r.detail


def test_capability_language_does_not_fire_when_stable():
    """Both windows engine-stable: capability vocabulary in notes is then
    backable (the engine really computed Cpk) -- the check must NOT fire."""
    a = ProofArtifact.model_validate(_stable_proof(notes="Cpk 1.2 on the after window, per the baseline run."))
    assert a.before_baseline.stable is True and a.after_baseline.stable is True
    r = _by_id(run_proof_prescore(a))["capability_language_requires_stability"]
    assert r.status == "pass"


def test_capability_language_unstable_but_clean_free_text_passes():
    a = ProofArtifact.model_validate(make_proof(notes="Round-1 window; the loop continues on the remaining gap."))
    assert a.before_baseline.stable is False
    r = _by_id(run_proof_prescore(a))["capability_language_requires_stability"]
    assert r.status == "pass"
    assert "not-stable" in r.detail


def test_capability_language_word_boundary_escapable_never_fires():
    """Boundary case the fix names outright: 'capable' inside 'escapable'
    must not match -- the vocabulary is word-boundary matched."""
    a = ProofArtifact.model_validate(make_proof(notes="An escapable bind: the crew worked around it either way."))
    assert a.before_baseline.stable is False
    r = _by_id(run_proof_prescore(a))["capability_language_requires_stability"]
    assert r.status == "pass"


def test_capability_language_bare_capable_does_fire_on_unstable():
    a = ProofArtifact.model_validate(make_proof(notes="The line is clearly capable now."))
    assert a.before_baseline.stable is False
    r = _by_id(run_proof_prescore(a))["capability_language_requires_stability"]
    assert r.status == "flag"
    assert "capable" in r.detail
