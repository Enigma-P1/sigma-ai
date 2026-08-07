"""Schema tests for T-05 VocCtqArtifact. Referential (tree) integrity lives
in prescore (test_prescore_voc_ctq.py); the schema only enforces the fields
themselves, including the tool's namesake critical-vs-easy check question.
"""

import pytest
from pydantic import ValidationError

from factories import make_voc_ctq
from sigma_engine.artifacts.voc_ctq import VocCtqArtifact


def test_accepts_a_complete_tree():
    artifact = VocCtqArtifact.model_validate(make_voc_ctq())
    assert artifact.ctqs[0].critical_vs_easy_check


def test_rejects_missing_critical_vs_easy_check():
    data = make_voc_ctq()
    data["ctqs"][0].pop("critical_vs_easy_check")
    with pytest.raises(ValidationError):
        VocCtqArtifact.model_validate(data)


def test_rejects_empty_customers():
    with pytest.raises(ValidationError):
        VocCtqArtifact.model_validate(make_voc_ctq(customers=[]))


def test_rejects_need_with_no_statement_ids():
    data = make_voc_ctq()
    data["needs"][0]["statement_ids"] = []
    with pytest.raises(ValidationError):
        VocCtqArtifact.model_validate(data)


def test_accepts_dangling_need_reference_schema_level():
    """Schema doesn't chase foreign keys (prescore does -- tree_completeness);
    a CTQ pointing at a need_id that doesn't exist yet is schema-legal."""
    data = make_voc_ctq()
    data["ctqs"][0]["need_id"] = "N-does-not-exist"
    artifact = VocCtqArtifact.model_validate(data)
    assert artifact.ctqs[0].need_id == "N-does-not-exist"


def test_round_trip_via_model_dump():
    artifact = VocCtqArtifact.model_validate(make_voc_ctq())
    round_tripped = VocCtqArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
