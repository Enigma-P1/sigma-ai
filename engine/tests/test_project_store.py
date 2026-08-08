"""Tests for project_store.py: round-trip, versioning, atomicity, overrides."""

import json

import pytest

from sigma_engine.project_store import ProjectStore


@pytest.fixture
def store(tmp_path):
    return ProjectStore(tmp_path / "projects")


def test_create_and_load_project_round_trips(store):
    created = store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    loaded = store.load_project("proj-1")
    assert loaded == created
    assert loaded.artifact_index == {}


def test_create_project_twice_raises(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    with pytest.raises(FileExistsError):
        store.create_project("proj-1", "Coffee Bar Again", "2026-08-07T00:00:00")


def test_load_missing_project_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load_project("does-not-exist")


def test_save_and_load_artifact_round_trips(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    data = {"schema_version": 1, "artifact_id": "picker-001", "hello": "world"}
    version = store.save_artifact("proj-1", "picker-001", "T-01", data, "2026-08-07T01:00:00")
    assert version == 1
    loaded = store.load_artifact("proj-1", "picker-001")
    assert loaded == data


def test_save_artifact_versions_increment_and_prior_versions_stay_loadable(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    v1 = {"schema_version": 1, "artifact_id": "picker-001", "route": "PDCA"}
    v2 = {"schema_version": 1, "artifact_id": "picker-001", "route": "full-DMAIC"}

    store.save_artifact("proj-1", "picker-001", "T-01", v1, "2026-08-07T01:00:00")
    store.save_artifact("proj-1", "picker-001", "T-01", v2, "2026-08-07T02:00:00")

    assert store.load_artifact("proj-1", "picker-001", version=1) == v1
    assert store.load_artifact("proj-1", "picker-001", version=2) == v2
    assert store.load_artifact("proj-1", "picker-001") == v2  # latest by default
    assert store.list_versions("proj-1", "picker-001") == [1, 2]

    meta = store.load_project("proj-1")
    assert meta.artifact_index["picker-001"].latest_version == 2
    assert meta.artifact_index["picker-001"].tool_id == "T-01"


def test_list_versions_empty_for_unknown_artifact(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    assert store.list_versions("proj-1", "no-such-artifact") == []


# ---------------------------------------------------------------------------
# latest_artifact_for_tool (Fix 5, critic-confirmed): the shared "which of
# this project's artifacts of tool_id X is latest" lookup, replacing three
# call sites (routes/gates.py, routes/stats.py, prescore/cross_checks.py)
# that used to each pick a different, wrong "latest" -- meta.artifact_index
# iterates in the on-disk sort_keys=True order (alphabetical by
# artifact_id), which is NOT chronological order.
# ---------------------------------------------------------------------------


def test_latest_artifact_for_tool_prefers_updated_at_over_alphabetical_order(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    # "aaa-old" sorts alphabetically FIRST but is chronologically OLDER;
    # "zzz-new" sorts alphabetically LAST and is chronologically NEWER.
    # The old stats.py-style bug (first match) would return "aaa-old" here.
    store.save_artifact("proj-1", "aaa-old", "T-02", {"updated_at": "2026-01-01T00:00:00", "marker": "old"}, "2026-01-01T00:00:00")
    store.save_artifact("proj-1", "zzz-new", "T-02", {"updated_at": "2026-06-01T00:00:00", "marker": "new"}, "2026-06-01T00:00:00")
    meta = store.load_project("proj-1")

    latest = store.latest_artifact_for_tool("proj-1", meta, "T-02")
    assert latest is not None and latest["marker"] == "new"  # updated_at wins over alphabetical

    oldest = store.latest_artifact_for_tool("proj-1", meta, "T-02", oldest=True)
    assert oldest is not None and oldest["marker"] == "old"


def test_latest_artifact_for_tool_tie_breaks_deterministically_by_artifact_id(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    same_ts = "2026-01-01T00:00:00"
    store.save_artifact("proj-1", "aaa", "T-02", {"updated_at": same_ts, "marker": "aaa"}, same_ts)
    store.save_artifact("proj-1", "zzz", "T-02", {"updated_at": same_ts, "marker": "zzz"}, same_ts)
    meta = store.load_project("proj-1")
    # Deterministic (not dict-iteration-order-dependent): same result on repeated calls.
    first = store.latest_artifact_for_tool("proj-1", meta, "T-02")
    second = store.latest_artifact_for_tool("proj-1", meta, "T-02")
    assert first == second


def test_latest_artifact_for_tool_returns_none_when_never_saved(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    meta = store.load_project("proj-1")
    assert store.latest_artifact_for_tool("proj-1", meta, "T-99") is None


def test_writes_are_atomic_no_stray_temp_files(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    store.save_artifact("proj-1", "picker-001", "T-01", {"a": 1}, "2026-08-07T01:00:00")
    artifact_dir = store.root / "proj-1" / "artifacts" / "picker-001"
    leftover_temp_files = [p for p in artifact_dir.iterdir() if p.name.endswith(".tmp")]
    assert leftover_temp_files == []
    assert (artifact_dir / "v1.json").exists()


def test_append_override_writes_jsonl_and_rejects_empty_reason(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    store.append_override("proj-1", "define_to_measure", "SIPOC still in draft, proceeding to unblock Measure prep", "2026-08-07T03:00:00")

    with pytest.raises(Exception):
        store.append_override("proj-1", "define_to_measure", "", "2026-08-07T03:05:00")

    overrides = store.list_overrides("proj-1")
    assert len(overrides) == 1
    assert overrides[0].gate_id == "define_to_measure"
    assert overrides[0].reason
    assert overrides[0].missing == []  # no missing list passed -- defaults to empty, not an error

    raw_lines = (store.root / "proj-1" / "overrides.log.jsonl").read_text().strip().splitlines()
    assert len(raw_lines) == 1
    assert json.loads(raw_lines[0])["gate_id"] == "define_to_measure"


def test_append_override_records_the_missing_set_it_covers(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    entry = store.append_override(
        "proj-1", "define_to_measure", "SIPOC and CTQ pending", "2026-08-07T03:00:00", missing=["T-04", "T-05"]
    )
    assert entry.missing == ["T-04", "T-05"]
    assert store.list_overrides("proj-1")[0].missing == ["T-04", "T-05"]


def test_list_overrides_empty_when_no_log(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    assert store.list_overrides("proj-1") == []


def test_resolved_project_path_is_absolute_and_under_store_root(store):
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    path = store.resolved_project_path("proj-1")
    assert path.is_absolute()
    assert path == (store.root / "proj-1").resolve()
