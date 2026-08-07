"""Schema tests for T-03 CharterArtifact."""

import pytest
from pydantic import ValidationError

from factories import make_charter
from sigma_engine.artifacts.charter import CharterArtifact


def test_accepts_a_complete_charter():
    artifact = CharterArtifact.model_validate(make_charter())
    assert artifact.process_owner.name == "Maria Ortiz"
    assert artifact.problem_statement.magnitude.number == 6.2


def test_rejects_missing_process_owner():
    data = make_charter()
    del data["process_owner"]
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_accepts_magnitude_without_unit_schema_level():
    """Schema allows it (prescore flags it -- see test_prescore_charter.py);
    only structural presence is a schema concern."""
    data = make_charter()
    data["problem_statement"]["magnitude"]["unit"] = ""
    artifact = CharterArtifact.model_validate(data)
    assert artifact.problem_statement.magnitude.unit == ""


def test_rejects_empty_scope_out():
    data = make_charter()
    data["scope"]["out_scope"] = ""
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_rejects_empty_team():
    data = make_charter()
    data["team"] = []
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_accepts_empty_risk_block_schema_level():
    """Empty A-4 risk block is schema-legal (a charter-in-progress);
    prescore flags it as thin, doesn't reject it."""
    data = make_charter(risks=[])
    artifact = CharterArtifact.model_validate(data)
    assert artifact.risks == []


def test_rejects_incomplete_risk_row():
    data = make_charter()
    data["risks"][0].pop("owner")
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_rejects_bad_target_date():
    data = make_charter()
    data["goal"]["target_date"] = "not-a-date"
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_rejects_extra_unknown_field():
    data = make_charter()
    data["not_a_real_field"] = "oops"
    with pytest.raises(ValidationError):
        CharterArtifact.model_validate(data)


def test_round_trip_via_model_dump():
    artifact = CharterArtifact.model_validate(make_charter())
    round_tripped = CharterArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
