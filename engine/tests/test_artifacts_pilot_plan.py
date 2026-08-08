"""Schema accept/reject tests for T-19 PilotPlanArtifact -- includes the
EXIT-10 trigger test (task brief): a second entry in `changes` must raise,
by name, teaching the one-change-at-a-time rule in the error."""

import pytest
from pydantic import ValidationError

from factories import make_declared_package, make_pilot_plan, make_pilot_plan_confounder_checklist, make_pilot_plan_with_package
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


def test_undeclared_second_change_still_raises_exit_10_exactly_as_before():
    """Regression, stated explicitly (task brief: "frozen... regression-
    prove it"): a second changes[] entry with NO declared_package is still
    EXIT-10's failure, byte-identical to the pre-M4 behavior -- the carve-
    out only ever applies when declared_package is actually present."""
    body = make_pilot_plan(changes=[
        {"change_id": "ch-1", "text": "Add a fixture alignment checklist before each shift"},
        {"change_id": "ch-2", "text": "Also replace the injector at the same time"},
    ])
    assert "declared_package" not in body
    with pytest.raises(ValidationError, match="EXIT-10"):
        PilotPlanArtifact.model_validate(body)


# ---------------------------------------------------------------------------
# M4 addition: declared_package (rubric R-IMP-02's "one honest carve-out").
# ---------------------------------------------------------------------------


def test_declared_package_with_matching_changes_count_saves_clean_and_suppresses_exit_10():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan_with_package())
    assert len(artifact.changes) == 2
    assert artifact.declared_package is not None
    assert artifact.declared_package.components == ["fixture head", "drive motor"]


def test_declared_package_stamps_the_package_attribution_note():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan_with_package())
    assert artifact.package_attribution_note is not None
    text = artifact.package_attribution_note.value
    assert "package-level only" in text
    assert "fixture head" in text and "drive motor" in text
    assert artifact.package_attribution_note.provenance.method


def test_no_declared_package_leaves_attribution_note_none():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan())
    assert artifact.declared_package is None
    assert artifact.package_attribution_note is None


def test_declared_package_component_count_must_match_changes_count():
    body = make_pilot_plan_with_package()
    body["changes"] = body["changes"][:1]  # 1 changes entry, but 2 components declared
    with pytest.raises(ValidationError, match="1:1"):
        PilotPlanArtifact.model_validate(body)


def test_declared_package_count_mismatch_is_not_reported_as_exit_10():
    """The count-mismatch failure is a distinct data-entry error, not
    EXIT-10 (module docstring) -- the desktop keys its EXIT-10 refusal
    panel off the literal substring "EXIT-10" in the validation message,
    so this message must NOT contain it, or the wrong banner would render."""
    body = make_pilot_plan_with_package()
    body["changes"] = body["changes"][:1]
    with pytest.raises(ValidationError) as exc_info:
        PilotPlanArtifact.model_validate(body)
    assert "EXIT-10" not in str(exc_info.value)


def test_declared_package_with_three_components_needs_three_changes():
    package = make_declared_package(components=["fixture head", "drive motor", "control board"])
    body = make_pilot_plan_with_package(declared_package=package, changes=[
        {"change_id": "ch-1", "text": "Replace the fixture head"},
        {"change_id": "ch-2", "text": "Replace the drive motor"},
        {"change_id": "ch-3", "text": "Replace the control board"},
    ])
    artifact = PilotPlanArtifact.model_validate(body)
    assert len(artifact.changes) == 3


def test_declared_package_rejects_blank_component():
    package = make_declared_package(components=["fixture head", "   "])
    with pytest.raises(ValidationError, match="non-empty"):
        PilotPlanArtifact.model_validate(make_pilot_plan_with_package(declared_package=package))


def test_declared_package_rejects_empty_component_list():
    package = make_declared_package(components=[])
    body = make_pilot_plan_with_package(declared_package=package, changes=[])
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(body)


def test_declared_package_rejects_blank_rationale():
    package = make_declared_package(rationale="")
    with pytest.raises(ValidationError):
        PilotPlanArtifact.model_validate(make_pilot_plan_with_package(declared_package=package))


def test_declared_package_with_one_component_is_schema_legal_but_reads_as_just_a_change():
    """Schema-legal (artifacts/pilot_plan.py's DeclaredPackage docstring:
    "structurally it changes nothing") -- a 1-component package caps
    `changes` at 1 entry, same as no package at all. The "that's just a
    change, not a package" bar is prescore's job (test_prescore_pilot_
    plan.py), not a schema rejection."""
    package = make_declared_package(components=["fixture head"])
    body = make_pilot_plan_with_package(declared_package=package, changes=[
        {"change_id": "ch-1", "text": "Replace the fixture head"},
    ])
    artifact = PilotPlanArtifact.model_validate(body)
    assert len(artifact.declared_package.components) == 1


def test_declared_package_round_trip_via_model_dump():
    artifact = PilotPlanArtifact.model_validate(make_pilot_plan_with_package())
    round_tripped = PilotPlanArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
