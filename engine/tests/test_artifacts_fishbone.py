"""Schema accept/reject + verified_causes computation tests for T-15
FishboneArtifact -- the evidence-discipline invalidator (rubric R-ANA-02)
enforced as a hard schema rejection, not a prescore flag."""

import pytest
from pydantic import ValidationError

from factories import make_fishbone, make_fishbone_causes
from sigma_engine.artifacts.fishbone import FishboneArtifact, compute_verified_causes


def test_accepts_a_complete_fishbone():
    artifact = FishboneArtifact.model_validate(make_fishbone())
    assert artifact.effect.text.startswith("Line 2 scrap")
    assert artifact.effect.charter_ref == "charter-001"
    assert len(artifact.causes) == 4


def test_verified_causes_lists_only_verified_with_evidence_intact():
    artifact = FishboneArtifact.model_validate(make_fishbone())
    summary = artifact.verified_causes.value
    assert summary.count == 1
    assert summary.causes[0].cause_id == "c-1"
    assert summary.causes[0].evidence.kind == "check_sheet"
    assert summary.causes[0].evidence.ref == "checksheet-001"
    assert artifact.verified_causes.provenance.method
    assert artifact.verified_causes.provenance.input_hash


def test_verified_causes_is_an_honest_empty_list_not_none_when_nothing_verified():
    causes = make_fishbone_causes()
    causes[0] = {**causes[0], "status": "investigating"}  # was verified; c-1-why2's parent ref must stay valid
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    assert artifact.verified_causes is not None
    assert artifact.verified_causes.value.count == 0
    assert artifact.verified_causes.value.causes == []


def test_rejects_verified_cause_with_no_evidence():
    causes = make_fishbone_causes()
    causes[1] = {**causes[1], "status": "verified", "evidence": None}
    with pytest.raises(ValidationError, match="evidence is required"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_candidate_and_investigating_and_ruled_out_may_have_no_evidence():
    causes = make_fishbone_causes()
    for c in causes:
        assert c["status"] != "verified" or c["evidence"] is not None
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    assert artifact.causes[2].status == "candidate"
    assert artifact.causes[2].evidence is None


def test_rejects_evidence_with_blank_ref():
    causes = make_fishbone_causes()
    causes[0]["evidence"] = {"kind": "check_sheet", "ref": "   "}
    with pytest.raises(ValidationError, match="blank"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_rejects_duplicate_cause_ids():
    causes = make_fishbone_causes()
    causes.append({**causes[0], "cause_id": "c-1", "status": "candidate", "evidence": None})
    with pytest.raises(ValidationError, match="cause_id"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_rejects_self_parent():
    causes = make_fishbone_causes()
    causes[0]["parent_cause_id"] = causes[0]["cause_id"]
    with pytest.raises(ValidationError, match="own parent"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_rejects_unknown_parent_cause_id():
    causes = make_fishbone_causes()
    causes[0]["parent_cause_id"] = "no-such-cause"
    with pytest.raises(ValidationError, match="unknown parent_cause_id"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_rejects_a_parent_cycle():
    causes = [
        {"cause_id": "a", "branch": "method", "text": "a", "parent_cause_id": "b", "status": "candidate", "evidence": None, "why_chain_position": None},
        {"cause_id": "b", "branch": "method", "text": "b", "parent_cause_id": "a", "status": "candidate", "evidence": None, "why_chain_position": None},
    ]
    with pytest.raises(ValidationError, match="cycle"):
        FishboneArtifact.model_validate(make_fishbone(causes=causes))


def test_causes_may_start_empty():
    artifact = FishboneArtifact.model_validate(make_fishbone(causes=[]))
    assert artifact.causes == []
    assert artifact.verified_causes.value.count == 0


def test_posted_verified_causes_is_discarded_and_recomputed():
    from sigma_engine.provenance import compute
    tampered = compute({"count": 999, "causes": []}, method="tampered", input_data=[])
    artifact = FishboneArtifact.model_validate(make_fishbone(verified_causes=tampered.model_dump(mode="json")))
    assert artifact.verified_causes.value.count == 1  # the real count (c-1), not the tampered 999


def test_compute_verified_causes_matches_artifact_field():
    artifact = FishboneArtifact.model_validate(make_fishbone())
    assert compute_verified_causes(artifact.causes).value == artifact.verified_causes.value


def test_round_trip_via_model_dump():
    artifact = FishboneArtifact.model_validate(make_fishbone())
    round_tripped = FishboneArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


def test_rejects_blank_effect_text():
    with pytest.raises(ValidationError):
        FishboneArtifact.model_validate(make_fishbone(effect={"text": "", "charter_ref": None}))


def test_charter_ref_is_optional():
    artifact = FishboneArtifact.model_validate(make_fishbone(effect={"text": "Some effect", "charter_ref": None}))
    assert artifact.effect.charter_ref is None
