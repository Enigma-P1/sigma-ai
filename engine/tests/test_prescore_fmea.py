"""Prescore tests for T-16: each of the 5 checks, driven to both pass and
flag/hard_flag at least once. The clean default fixture (make_fmea())
passes all 5."""

from factories import make_fmea, make_fmea_rows
from sigma_engine.artifacts.fmea import FmeaArtifact
from sigma_engine.prescore.fmea import run_fmea_prescore

EXPECTED_CHECK_IDS = {
    "mode_specificity", "ratings_in_range", "anchors_consulted_confirmed",
    "high_severity_without_action", "action_owners_present",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_fmea_passes_every_check():
    # The default fixture leaves row-a deliberately unaddressed (it's the
    # blocking_flags/high_severity_without_action positive fixture
    # elsewhere) -- give it an action here so this is the genuinely clean
    # all-pass case.
    rows = make_fmea_rows()
    rows[0]["action"] = "Add pressure sensor with auto-stop"
    rows[0]["action_owner"] = "Maria Ortiz"
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id, r in results.items():
        assert r.status == "pass", f"{check_id}: expected pass, got {r.status} ({r.detail})"


def test_mode_specificity_flags_a_single_word_mode():
    rows = make_fmea_rows()
    rows[0]["failure_mode"] = "Defect"
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert results["mode_specificity"].status == "flag"
    assert "row-a" in results["mode_specificity"].detail


def test_ratings_in_range_always_passes_by_schema_construction():
    artifact = FmeaArtifact.model_validate(make_fmea())
    results = _by_id(run_fmea_prescore(artifact))
    assert results["ratings_in_range"].status == "pass"
    assert "3" in results["ratings_in_range"].detail


def test_anchors_consulted_flags_an_unconfirmed_row():
    rows = make_fmea_rows()
    rows[1]["anchors_consulted"] = False
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert results["anchors_consulted_confirmed"].status == "flag"
    assert "row-b" in results["anchors_consulted_confirmed"].detail


def test_high_severity_without_action_is_hard_flag_even_without_safety_wording():
    # Broader than blocking_flags on purpose: it fires on ANY unaddressed
    # severity-9/10 row, safety-worded or not. Strip row-a's safety wording
    # (keeping severity 9 + no action) -- blocking_flags goes quiet, but
    # this check still fires, and row-c (has an action) stays clear.
    rows = make_fmea_rows()
    rows[0]["effect"] = "Cosmetic blemish noticed by quality inspector"
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    assert artifact.blocking_flags.value == []  # not safety-worded -- blocking_flags stays clean
    results = _by_id(run_fmea_prescore(artifact))
    assert results["high_severity_without_action"].status == "hard_flag"
    assert "row-a" in results["high_severity_without_action"].detail
    assert "row-c" not in results["high_severity_without_action"].detail


def test_high_severity_without_action_passes_once_addressed():
    rows = make_fmea_rows()
    rows[0]["action"] = "Add pressure sensor with auto-stop"
    rows[0]["action_owner"] = "Maria Ortiz"
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert results["high_severity_without_action"].status == "pass"


def test_action_owners_present_flags_an_action_with_no_owner():
    rows = make_fmea_rows()
    rows[1]["action_owner"] = ""
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert results["action_owners_present"].status == "flag"
    assert "row-b" in results["action_owners_present"].detail


def test_action_owners_present_passes_when_action_itself_is_blank():
    # No action recorded at all isn't an "action with no owner" -- that's
    # high_severity_without_action's concern, not this check's.
    rows = make_fmea_rows()
    rows[1]["action"] = ""
    rows[1]["action_owner"] = ""
    artifact = FmeaArtifact.model_validate(make_fmea(rows=rows))
    results = _by_id(run_fmea_prescore(artifact))
    assert results["action_owners_present"].status == "pass"
