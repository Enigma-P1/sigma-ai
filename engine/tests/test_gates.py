"""Tests for gates.py: the phase-gate matrix (soft blocks + override,
hard blocks refuse override, stub gates for Measure+)."""

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
    entry = gates.override(
        "define_to_measure", "proj-1", "SIPOC pending, unblocking to prep Measure templates", "2026-08-07T03:00:00", store
    )
    assert entry.gate_id == "define_to_measure"
    assert store.list_overrides("proj-1")[0].reason


def test_override_rejects_empty_reason(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    with pytest.raises(Exception):
        gates.override("define_to_measure", "proj-1", "", "2026-08-07T03:00:00", store)


def test_override_refuses_hard_gate(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    with pytest.raises(PermissionError):
        gates.override("intake_picker_not_exit01", "proj-1", "I really want to skip this", "2026-08-07T03:00:00", store)


def test_override_refuses_stub_gate(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    with pytest.raises(PermissionError):
        gates.override("measure_to_analyze", "proj-1", "not built yet anyway", "2026-08-07T03:00:00", store)
