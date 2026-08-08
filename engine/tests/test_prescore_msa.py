"""Prescore tests for T-12: verdict_recorded, result_matches_inputs,
repeats_per_item, item_count_meets_guidance."""

from factories import make_attribute_msa, make_continuous_msa
from sigma_engine.artifacts.msa import MsaArtifact
from sigma_engine.prescore.msa import run_msa_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_healthy_continuous_msa_passes_every_check():
    artifact = MsaArtifact.model_validate(make_continuous_msa())
    results = _by_id(run_msa_prescore(artifact))
    assert results["verdict_recorded"].status == "pass"
    assert results["result_matches_inputs"].status == "pass"
    assert results["repeats_per_item"].status == "pass"
    assert results["item_count_meets_guidance"].status == "pass"  # fixture has 10 items


def test_healthy_attribute_msa_passes_and_has_no_repeats_check():
    artifact = MsaArtifact.model_validate(make_attribute_msa())
    results = _by_id(run_msa_prescore(artifact))
    assert results["verdict_recorded"].status == "pass"
    assert results["result_matches_inputs"].status == "pass"
    assert "repeats_per_item" not in results  # attribute path has no repeat-readings concept
    assert results["item_count_meets_guidance"].status == "pass"  # fixture has 12 items


def test_below_guidance_item_count_flags_not_hard_flags():
    body = make_continuous_msa()
    body["continuous_items"] = body["continuous_items"][:3]  # well under the 10-item guidance
    artifact = MsaArtifact.model_validate(body)
    results = _by_id(run_msa_prescore(artifact))
    assert results["item_count_meets_guidance"].status == "flag"  # soft guidance, not hard_flag (PLAN §4.2)


def test_short_repeats_flagged_by_item_id():
    body = make_continuous_msa()
    body["continuous_items"][0]["readings"] = [10.0, None]
    artifact = MsaArtifact.model_validate(body)
    results = _by_id(run_msa_prescore(artifact))
    assert results["repeats_per_item"].status == "flag"
    assert "item-0" in results["repeats_per_item"].detail


def test_tampered_result_flags_result_matches_inputs():
    artifact = MsaArtifact.model_validate(make_continuous_msa())
    tampered = artifact.model_copy(update={"result": artifact.result.model_copy(update={"verdict": "fail"})})
    results = _by_id(run_msa_prescore(tampered))
    assert results["result_matches_inputs"].status == "flag"
    assert "hand-edited" in results["result_matches_inputs"].detail
