"""Tests for gates.py: the phase-gate matrix (soft blocks + override,
hard blocks refuse override, every sequence gate Intake through Wrap a
real soft gate since the M6 eval fix)."""

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


# --- the four M6 soft sequence gates (formerly NOT_YET_BUILT stubs) --------


def test_measure_to_analyze_soft_blocks_listing_plan_check_and_dataset():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids=set(), has_dataset=False)
    result = gates.check("measure_to_analyze", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == ["T-11", "T-12", "a saved dataset"]
    # The message restates the missing list in plain language.
    assert "data collection plan" in result.reason.lower()
    assert "measurement check" in result.reason.lower()
    assert "a saved dataset" in result.reason
    assert "logged override reason" in result.reason


def test_measure_to_analyze_missing_only_the_dataset():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-11", "T-12"}, has_dataset=False)
    result = gates.check("measure_to_analyze", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == ["a saved dataset"]


def test_measure_to_analyze_clears_with_plan_check_and_dataset():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-11", "T-12"}, has_dataset=True)
    assert gates.check("measure_to_analyze", snapshot).status == "CLEAR"


def test_analyze_to_improve_soft_blocks_when_neither_evidence_source_exists():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids=set(), fishbone_verified_cause_count=None)
    result = gates.check("analyze_to_improve", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == [
        "either a fishbone (T-15) with at least one verified cause",
        "or a hypothesis run (T-17)",
    ]
    assert "either satisfies" in result.reason


def test_analyze_to_improve_soft_blocks_on_a_fishbone_with_zero_verified_causes():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-15"}, fishbone_verified_cause_count=0)
    result = gates.check("analyze_to_improve", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == [
        "either at least one verified cause on the fishbone (T-15 exists, none verified yet)",
        "or a hypothesis run (T-17)",
    ]


def test_analyze_to_improve_clears_on_a_fishbone_with_a_verified_cause():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-15"}, fishbone_verified_cause_count=1)
    assert gates.check("analyze_to_improve", snapshot).status == "CLEAR"


def test_analyze_to_improve_clears_on_a_hypothesis_run_alone():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-17"}, fishbone_verified_cause_count=None)
    assert gates.check("analyze_to_improve", snapshot).status == "CLEAR"


def test_improve_to_control_soft_blocks_listing_pilot_and_proof():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-19"})
    result = gates.check("improve_to_control", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == ["T-20"]
    assert "before/after proof" in result.reason


def test_improve_to_control_clears_with_pilot_and_proof():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-19", "T-20"})
    assert gates.check("improve_to_control", snapshot).status == "CLEAR"


def test_control_to_wrap_soft_blocks_listing_chart_and_plan():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids=set())
    result = gates.check("control_to_wrap", snapshot)
    assert result.status == "SOFT_BLOCK"
    assert result.missing == ["T-21", "T-22"]
    assert "control chart" in result.reason
    assert "control plan" in result.reason


def test_control_to_wrap_clears_with_chart_and_plan():
    snapshot = gates.ProjectSnapshot(artifact_tool_ids={"T-21", "T-22"})
    assert gates.check("control_to_wrap", snapshot).status == "CLEAR"


@pytest.mark.parametrize("gate_id", ["measure_to_analyze", "analyze_to_improve", "improve_to_control", "control_to_wrap"])
def test_m6_soft_gates_override_loop_clears_then_goes_stale(gate_id, tmp_path):
    """The full soft-gate override loop, per gate: blocked -> override with
    a logged reason -> re-check CLEARs with the override note -> project
    state changes -> the recorded missing set no longer matches -> the
    stale override no longer clears."""
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    blocked = gates.ProjectSnapshot()  # nothing saved at all -- every gate blocked
    first = gates.check(gate_id, blocked)
    assert first.status == "SOFT_BLOCK" and first.missing

    entry = gates.override(gate_id, "proj-1", "phase work reviewed offline; proceeding", "2026-08-07T01:00:00", store, blocked)
    assert set(entry.missing) == set(first.missing)

    cleared = gates.check(gate_id, blocked, store.list_overrides("proj-1"))
    assert cleared.status == "CLEAR"
    assert cleared.overridden is True
    assert cleared.override_reason == "phase work reviewed offline; proceeding"

    # One requirement appears -> different missing set -> override is stale.
    progressed = gates.ProjectSnapshot(artifact_tool_ids={"T-11", "T-19", "T-21"}, fishbone_verified_cause_count=0)
    stale = gates.check(gate_id, progressed, store.list_overrides("proj-1"))
    assert stale.status == "SOFT_BLOCK"
    assert stale.overridden is False
    assert set(stale.missing) != set(first.missing)


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


# --- measure_capability_language_requires_msa_pass (T-12 hard gate) --------

def test_msa_gate_clears_when_no_msa_has_ever_run_but_never_claims_a_checked_measurement():
    """M6 eval fix (persona FL-07): the no-T-12 CLEAR used to be
    byte-identical to a genuinely-passed check's CLEAR. The status stays
    CLEAR (matrix §4a EXIT-02 hard-blocks a FAILED check only; T-12
    presence is measure_to_analyze's soft-gate job) but the reason now
    says outright that nothing was checked."""
    snapshot = gates.ProjectSnapshot(msa_verdict=None, msa_on_file=False)
    result = gates.check("measure_capability_language_requires_msa_pass", snapshot)
    assert result.status == "CLEAR"
    assert "No measurement check (T-12) is on file" in result.reason
    assert "does not attest a checked measurement" in result.reason


def test_msa_gate_names_the_no_verdict_case_when_a_t12_exists_without_one():
    snapshot = gates.ProjectSnapshot(msa_verdict=None, msa_on_file=True)
    result = gates.check("measure_capability_language_requires_msa_pass", snapshot)
    assert result.status == "CLEAR"
    assert "records no verdict" in result.reason
    assert "does not attest a checked measurement" in result.reason


@pytest.mark.parametrize("verdict", ["acceptable", "marginal"])
def test_msa_gate_clears_on_a_non_failing_verdict_naming_it(verdict):
    snapshot = gates.ProjectSnapshot(msa_verdict=verdict, msa_on_file=True)
    result = gates.check("measure_capability_language_requires_msa_pass", snapshot)
    assert result.status == "CLEAR"
    assert repr(verdict) in result.reason  # a genuine pass is distinguishable: the verdict is named


def test_msa_gate_hard_blocks_on_a_failed_verdict_and_names_exit02():
    snapshot = gates.ProjectSnapshot(msa_verdict="fail")
    result = gates.check("measure_capability_language_requires_msa_pass", snapshot)
    assert result.status == "HARD_BLOCK"
    assert "EXIT-02" in result.reason


def test_msa_gate_cannot_be_overridden(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    snapshot = gates.ProjectSnapshot(msa_verdict="fail")
    with pytest.raises(PermissionError):
        gates.override(
            "measure_capability_language_requires_msa_pass", "proj-1", "let me past anyway",
            "2026-08-07T05:00:00", store, snapshot,
        )


def test_msa_gate_clears_once_a_re_run_reads_acceptable():
    """The fail -> re-run -> clear loop at the gates.py layer: the same
    check_id, re-evaluated against an updated snapshot (a fresh T-12
    version with a passing verdict), flips HARD_BLOCK -> CLEAR."""
    failing = gates.ProjectSnapshot(msa_verdict="fail")
    assert gates.check("measure_capability_language_requires_msa_pass", failing).status == "HARD_BLOCK"

    passing = gates.ProjectSnapshot(msa_verdict="acceptable")
    assert gates.check("measure_capability_language_requires_msa_pass", passing).status == "CLEAR"


# --- build_project_snapshot's M6 fields (msa_on_file / has_dataset /
# --- fishbone_verified_cause_count), off a real on-disk project ----------


def test_build_project_snapshot_populates_the_m6_fields(tmp_path):
    from factories import make_fishbone, make_fishbone_causes
    from sigma_engine.artifacts.fishbone import FishboneArtifact
    from sigma_engine.datasets import DatasetStore

    store = ProjectStore(tmp_path / "projects")
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")

    empty = gates.build_project_snapshot(store, "proj-1")
    assert empty.msa_on_file is False
    assert empty.has_dataset is False
    assert empty.fishbone_verified_cause_count is None

    # A saved fishbone (validated the same way the save route validates it,
    # so verified_causes is the server-computed field) with 1 verified cause.
    fishbone = FishboneArtifact.model_validate(make_fishbone()).model_dump(mode="json")
    store.save_artifact("proj-1", "fishbone-001", "T-15", fishbone, "2026-08-07T01:00:00")
    # One saved dataset.
    DatasetStore(store).save_dataset("proj-1", "waits.csv", b"wait_seconds\n1\n2\n", None, "2026-08-07T01:30:00")

    snapshot = gates.build_project_snapshot(store, "proj-1")
    assert snapshot.msa_on_file is False  # still no T-12
    assert snapshot.has_dataset is True
    assert snapshot.fishbone_verified_cause_count == 1

    # A fishbone re-save with nothing verified reads 0, not None.
    causes = make_fishbone_causes()
    for cause in causes:
        if cause["status"] == "verified":
            cause["status"] = "investigating"
    downgraded = FishboneArtifact.model_validate(make_fishbone(causes=causes)).model_dump(mode="json")
    store.save_artifact("proj-1", "fishbone-001", "T-15", downgraded, "2026-08-07T02:00:00")
    assert gates.build_project_snapshot(store, "proj-1").fishbone_verified_cause_count == 0
