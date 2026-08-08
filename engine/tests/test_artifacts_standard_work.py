"""Schema/behavior tests for T-24 StandardWorkArtifact: step schema,
metadata presence, supersedes naming, and referential step_id uniqueness."""

import pytest
from pydantic import ValidationError

from factories import make_standard_work, make_standard_work_steps
from sigma_engine.artifacts.standard_work import StandardWorkArtifact


def test_accepts_a_complete_sop():
    a = StandardWorkArtifact.model_validate(make_standard_work())
    assert a.version == 1
    assert a.owner == "Maria Ortiz"
    assert a.steps[0].changed_from_prior is True
    assert a.steps[1].changed_from_prior is False


def test_step_requires_action_and_standard():
    body = make_standard_work()
    body["steps"][0]["standard"] = ""
    with pytest.raises(ValidationError):
        StandardWorkArtifact.model_validate(body)


def test_duplicate_step_ids_rejected():
    steps = make_standard_work_steps()
    steps[1]["step_id"] = steps[0]["step_id"]
    with pytest.raises(ValidationError, match="unique"):
        StandardWorkArtifact.model_validate(make_standard_work(steps=steps))


def test_blank_supersedes_string_rejected_omit_the_field_instead():
    with pytest.raises(ValidationError, match="non-empty"):
        StandardWorkArtifact.model_validate(make_standard_work(supersedes="   "))


def test_supersedes_names_the_prior_instruction():
    a = StandardWorkArtifact.model_validate(make_standard_work(supersedes="Coffee Bar SOP v0 (paper, undated)"))
    assert a.supersedes == "Coffee Bar SOP v0 (paper, undated)"


def test_effective_date_must_be_iso8601():
    with pytest.raises(ValidationError):
        StandardWorkArtifact.model_validate(make_standard_work(effective_date="not-a-date"))


def test_round_trip_via_model_dump():
    a = StandardWorkArtifact.model_validate(make_standard_work())
    b = StandardWorkArtifact.model_validate(a.model_dump(mode="json"))
    assert b == a
