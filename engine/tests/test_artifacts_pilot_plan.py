"""Schema accept/reject tests for T-19 PilotPlanArtifact -- includes the
EXIT-10 trigger test (task brief): a second entry in `changes` must raise,
by name, teaching the one-change-at-a-time rule in the error."""

import pytest
from pydantic import ValidationError

from factories import make_pilot_plan, make_pilot_plan_confounder_checklist
from sigma_engine.artifacts.pilot_plan import PilotPlanArtifact


def test_accepts_a_complete_pilot_plan():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    assert artifact.status == "designed"
    assert len(artifact.changes) == 1


def test_exit_10_fires_on_a_second_change():
    body = make_pilot_plan(changes=[
        {"change_id": "ch-1", "text": "Add a fixture alignment checklist before each shift"},
        {"change_id": "ch-2", "text": "Also replace the injector at the same time"},
    ])
    with pytest.raises(ValidationError, match="EXIT-10"):
        PilotPlanArtifact.model_validate(body)


def test_exit_10_error_teaches_the_one_change_rule():
    body = make_pilot_plan(changes=[
        {"change_id": "ch-1", "text": "Add a fixture alignment checklist before each shift"},
        {"change_id": "ch-2", "text": "Also replace the injector at the same time"},
    ])
    with pytest.raises(ValidationError) as exc_info:
        PilotPlanArtifact.model_validate(body)
    msg = str(exc_info.value)
    assert "one change" in msg.lower()
    assert "PACKAGE" in msg or "package" in msg  # names the declared-inseparable-package carve-out
    assert "changes" in msg  # points at the field to fix


def test_removing_the_extra_change_saves_clean():
    # The brief's own "remove it, save clean" flow -- start from the
    # two-change body, drop the extra entry, confirm it now validates.
    body = make_pilot_plan(changes=[
        {"change_id": "ch-1", "text": "Add a fixture alignment checklist before each shift"},
        {"change_id": "ch-2", "text": "Also replace the injector at the same time"},
    ])
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(body)
    body["changes"] = body["changes"][:1]
    artifact = PilotPlanArtifact.model_validate(body)
    assert len(artifact.changes) == 1


def test_rejects_zero_changes():
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(make_pilot_plan(changes=[]))


def test_rejects_the_one_change_statement_mismatching_changes_entry():
    body = make_pilot_plan()
    body["the_one_change"]["statement"] = "A completely different change than what's in `changes`"
    with pytest.raises(ValidationError, match="match"):
        PilotPlanArtifact.model_validate(body)


def test_rejects_blank_falsification_line():
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(make_pilot_plan(falsification_line=""))


def test_rejects_missing_confounder_entry():
    body = make_pilot_plan()
    del body["confounder_checklist"]["measurement"]
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(body)


def test_confounder_note_may_be_blank_at_schema_level():
    """PLAN §4.2's soft/hard split: whether a note was actually filled in
    is prescore's job (checklist_completeness), not a schema rejection --
    the five yes/no answers are the structural requirement."""
    checklist = make_pilot_plan_confounder_checklist()
    checklist["staffing"]["note"] = ""
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan(confounder_checklist=checklist))
    assert artifact.confounder_checklist.staffing.note == ""


def test_success_threshold_declared_at_must_be_iso8601():
    body = make_pilot_plan()
    body["success_threshold"]["declared_at"] = "not-a-date"
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(body)


def test_rejects_invalid_comparison_kind():
    body = make_pilot_plan()
    body["comparison_design"]["kind"] = "sideways_glance"
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(body)


def test_status_defaults_and_accepts_each_literal():
    for status in ("designed", "running", "complete"):
        artifact = PilotPlanArtifact.model_validate(make_pilot_plan(status=status))
        assert artifact.status == status


def test_round_trip_via_model_dump():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    round_tripped = PilotPlanArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
