"""Schema accept/reject + RPN/sorted_view/blocking_flags computation tests
for T-16 FmeaArtifact -- includes the hand-checkable RPN + severity-first
ordering fixture (rubric R-ANA-03's stated RPN limitation)."""

import pytest
from pydantic import ValidationError

from factories import make_fmea, make_fmea_rows
from sigma_engine.artifacts.fmea import FmeaArtifact, compute_blocking_flags, compute_sorted_view


def test_accepts_a_complete_fmea():
    artifact = FmeaArtifact.model_validate(make_fmea())
    assert len(artifact.rows) == 3


def test_rpn_is_severity_times_occurrence_times_detection_per_row():
    artifact = FmeaArtifact.model_validate(make_fmea())
    by_id = {r.row_id: r for r in artifact.rows}
    assert by_id["row-a"].rpn == 9 * 3 * 2 == 54
    assert by_id["row-b"].rpn == 7 * 8 * 8 == 448
    assert by_id["row-c"].rpn == 9 * 2 * 2 == 36


def test_hand_checkable_severity_first_then_rpn_ordering():
    # row-b's RPN (448) is the largest of the three, but its severity (7)
    # is lower than row-a's and row-c's (9) -- severity-first means row-b
    # must sort LAST despite the biggest RPN. Between row-a (rpn 54) and
    # row-c (rpn 36), both severity 9, row-a's larger RPN wins the tie.
    artifact = FmeaArtifact.model_validate(make_fmea())
    assert artifact.sorted_view.value == ["row-a", "row-c", "row-b"]


def test_rpn_field_cannot_be_hand_typed():
    # rpn is a computed_field (CopqRow.amount's pattern) -- a posted value
    # under that key is simply not a settable input, same as CopqRow.amount.
    body = make_fmea()
    body["rows"][0]["rpn"] = 999999
    artifact = FmeaArtifact.model_validate(body)
    assert artifact.rows[0].rpn == 54  # the real computed value, tampering had no effect


def test_blocking_flags_fires_on_high_severity_safety_worded_no_action():
    artifact = FmeaArtifact.model_validate(make_fmea())
    flags = artifact.blocking_flags.value
    assert [f.row_id for f in flags] == ["row-a"]
    assert flags[0].severity == 9
    assert "safety" in flags[0].reason or "regulatory" in flags[0].reason


def test_blocking_flags_empty_once_the_row_gets_an_action():
    rows = make_fmea_rows()
    rows[0]["action"] = "Add pressure sensor with auto-stop"
    rows[0]["action_owner"] = "Maria Ortiz"
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    assert artifact.blocking_flags.value == []


def test_blocking_flags_does_not_fire_on_high_severity_non_safety_effect():
    rows = make_fmea_rows()
    rows[0]["effect"] = "Cosmetic blemish noticed by quality inspector"  # sev 9, no action, but not safety-worded
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    assert artifact.blocking_flags.value == []


def test_blocking_flags_does_not_fire_on_low_severity_even_if_safety_worded():
    rows = make_fmea_rows()
    rows[0]["severity"] = 4
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    assert artifact.blocking_flags.value == []


def test_anchors_are_embedded_with_original_wording_for_all_ten_points():
    artifact = FmeaArtifact.model_validate(make_fmea())
    assert set(artifact.anchors.severity) == set(range(1, 11))
    assert set(artifact.anchors.occurrence) == set(range(1, 11))
    assert set(artifact.anchors.detection) == set(range(1, 11))
    assert artifact.anchors.severity[10]
    assert artifact.anchors.severity[1]


def test_posted_anchors_blocking_flags_and_sorted_view_are_discarded_and_recomputed():
    body = make_fmea()
    body["anchors"] = {"severity": {1: "TAMPERED"}, "occurrence": {}, "detection": {}}
    body["blocking_flags"] = {"value": [], "provenance": {"input_hash": "x", "method": "tampered", "engine_version": "0", "assumptions_checked": [], "warnings": []}}
    body["sorted_view"] = {"value": ["nope"], "provenance": {"input_hash": "x", "method": "tampered", "engine_version": "0", "assumptions_checked": [], "warnings": []}}
    artifact = FmeaArtifact.model_validate(body)
    assert artifact.anchors.severity[1] != "TAMPERED"
    assert [f.row_id for f in artifact.blocking_flags.value] == ["row-a"]
    assert artifact.sorted_view.value == ["row-a", "row-c", "row-b"]


def test_compute_functions_match_artifact_fields():
    artifact = FmeaArtifact.model_validate(make_fmea())
    assert compute_blocking_flags(artifact.rows).value == artifact.blocking_flags.value
    assert compute_sorted_view(artifact.rows).value == artifact.sorted_view.value


def test_rejects_severity_out_of_range():
    rows = make_fmea_rows()
    rows[0]["severity"] = 11
    with pytest.raises(ValidationError):
        FmeaArtifact.model_validate(make_fmea(rows=rows))

    rows2 = make_fmea_rows()
    rows2[0]["occurrence"] = 0
    with pytest.raises(ValidationError):
        FmeaArtifact.model_validate(make_fmea(rows=rows2))


def test_rejects_empty_rows():
    with pytest.raises(ValidationError):
        FmeaArtifact.model_validate(make_fmea(rows=[]))


def test_rejects_duplicate_row_ids():
    rows = make_fmea_rows()
    rows.append({**rows[0], "row_id": rows[0]["row_id"]})
    with pytest.raises(ValidationError, match="row_id"):
        FmeaArtifact.model_validate(make_fmea(rows=rows))


def test_rejects_blank_failure_mode():
    rows = make_fmea_rows()
    rows[0]["failure_mode"] = ""
    with pytest.raises(ValidationError):
        FmeaArtifact.model_validate(make_fmea(rows=rows))


def test_action_due_must_be_iso8601_when_present():
    rows = make_fmea_rows()
    rows[0]["action_due"] = "not-a-date"
    with pytest.raises(ValidationError):
        FmeaArtifact.model_validate(make_fmea(rows=rows))


def test_action_owner_and_action_may_be_blank_at_schema_level():
    """PLAN §4.2's soft/hard split: content-completeness (action owner
    presence, high-severity-without-action) lives in prescore, not here."""
    rows = make_fmea_rows()
    rows[0]["action"] = ""
    rows[0]["action_owner"] = ""
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    assert artifact.rows[0].action == ""
    assert artifact.rows[0].action_owner == ""


def test_process_step_ref_is_optional_free_link():
    artifact = FmeaArtifact.model_validate(make_fmea())
    assert artifact.rows[0].process_step_ref is None
    assert artifact.rows[2].process_step_ref == "step-3"


def test_round_trip_via_model_dump():
    artifact = FmeaArtifact.model_validate(make_fmea())
    round_tripped = FmeaArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
