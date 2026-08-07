"""Tests for gates.py: the phase-gate matrix (soft blocks + override,
hard blocks refuse override, stub gates for Measure+)."""

import json

import pytest

from sigma_engine import gates
from sigma_engine.project_store import ProjectStore


def test_intake_gate_soft_blocks_when_no_picker():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids=set(), picker_route=None)
    result = gates.check("intake_picker_present", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert "T-01" in result.missing


def test_intake_gate_clears_once_picker_exists():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-01"}, picker_route="full-DMAIC")
    assert gates.check("intake_picker_present", snapshot).status == "CLEAR"


def test_intake_hard_blocks_on_exit01_route():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-01"}, picker_route="EXIT-01")
    result = gates.check("intake_picker_not_exit01", snapshot)
    assert result.status == "HARD_BLOCK"
    assert "EXIT-01" in result.reason


def test_intake_clears_when_route_is_not_exit01():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-01"}, picker_route="PDCA")
    assert gates.check("intake_picker_not_exit01", snapshot).status == "CLEAR"


def test_define_exit_soft_blocks_lists_missing_tools():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})
    result = gates.check("define_to_measure", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert set(result.missing) == {"T-04", "T-05"}


def test_define_exit_clears_when_all_three_present():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03", "T-04", "T-05"})
    assert gates.check("define_to_measure", snapshot).status == "CLEAR"


@pytest.mark.parametrize("gate_id", ["measure_to_analyze", "analyze_to_improve", "improve_to_control", "control_to_wrap"])
def test_measure_plus_gates_are_stubbed_not_yet_built(gate_id):
    snapshot = gates.ProjectSnapshot(artifact_tool_ids=set())
    result = gates.check(gate_id, snapshot)
    assert result.status == "NOT_YET_BUILT"
    assert result.reason


def test_check_unknown_gate_raises():
    with pytest.raises(KeyError):
        gates.check("not-a-real-gate", gates.ProjectSnapshot())


def test_phase_order_is_complete_and_ordered():
    assert gates.PHASE_ORDER == ("Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap")


def test_override_clears_soft_block_with_reason(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})  # T-04/T-05 missing
    entry = gates.override(
        "define_to_measure", "proj-1", "SIPOC pending, unblocking to prep Measure templates", "2026-08-07T03:00:00",
        store, snapshot,
    )
    assert entry.gate_id == "define_to_measure"
    assert set(entry.missing) == {"T-04", "T-05"}
    assert store.list_overrides("proj-1")[0].reason


def test_override_rejects_empty_reason(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})
    with pytest.raises(Exception):
        gates.override("define_to_measure", "proj-1", "", "2026-08-07T03:00:00", store, snapshot)


def test_override_refuses_hard_gate(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-01"}, picker_route="EXIT-01")
    with pytest.raises(PermissionError):
        gates.override(
            "intake_picker_not_exit01", "proj-1", "I really want to skip this", "2026-08-07T03:00:00", store, snapshot
        )


def test_override_refuses_stub_gate(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot()
    with pytest.raises(PermissionError):
        gates.override("measure_to_analyze", "proj-1", "not built yet anyway", "2026-08-07T03:00:00", store, snapshot)


def test_check_clears_with_override_note_when_override_covers_current_missing_set(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})  # T-04/T-05 missing
    gates.override(
        "define_to_measure", "proj-1", "SIPOC and CTQ pending; unblocking to start Measure prep",
        "2026-08-07T03:00:00", store, snapshot,
    )

    result = gates.check("define_to_measure", snapshot, store.list_overrides("proj-1"))
    assert result.status == "CLEAR"
    assert result.overridden is True
    assert result.override_reason == "SIPOC and CTQ pending; unblocking to start Measure prep"
    assert result.missing == []


def test_check_ignores_override_when_missing_set_is_unchanged_but_reason_absent(tmp_path):
    """No override logged at all -> still a plain SOFT_BLOCK, not cleared."""
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})
    result = gates.check("define_to_measure", snapshot, store.list_overrides("proj-1"))
    assert result.status == "SOFT_BLOCK"
    assert result.overridden is False
    assert set(result.missing) == {"T-04", "T-05"}


def test_check_does_not_clear_a_stale_override(tmp_path):
    """Override logged while T-04/T-05 were missing; then T-04 gets added.
    The current missing set (just T-05) no longer matches what the override
    covered, so the old reason no longer applies -- the gate stays blocked."""
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    stale_snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})  # T-04/T-05 missing
    gates.override(
        "define_to_measure", "proj-1", "SIPOC pending, unblocking to prep Measure templates",
        "2026-08-07T03:00:00", store, stale_snapshot,
    )

    current_snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03", "T-04"})  # only T-05 missing now
    result = gates.check("define_to_measure", current_snapshot, store.list_overrides("proj-1"))
    assert result.status == "SOFT_BLOCK"
    assert result.overridden is False
    assert result.missing == ["T-05"]


def test_check_tolerates_pre_existing_override_records_with_no_missing_field(tmp_path):
    """An override.log.jsonl line written before `missing` existed loads
    fine (defaults to []) and is correctly treated as not covering a real
    (non-empty) missing set -- never a crash, never a false clear."""
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    old_style_line = json.dumps(
        {"gate_id": "define_to_measure", "reason": "pre-upgrade override", "timestamp": "2026-08-01T00:00:00"}
    )
    (store.root / "proj-1" / "overrides.log.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (store.root / "proj-1" / "overrides.log.jsonl").write_text(old_style_line + "\n", encoding="utf-8")

    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-03"})
    result = gates.check("define_to_measure", snapshot, store.list_overrides("proj-1"))
    assert result.status == "SOFT_BLOCK"
    assert result.overridden is False


def test_hard_block_never_carries_an_override_note(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-01"}, picker_route="EXIT-01")
    result = gates.check("intake_picker_not_exit01", snapshot, [])
    assert result.status == "HARD_BLOCK"
    assert result.overridden is False
