"""Tests for prescore/cross_checks.py's three reconciliation checks, each
driven both ways (pass and flag/advisory), plus the "a side doesn't exist
yet" omission contract."""

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from factories import make_charter, make_check_sheet, make_copq
from sigma_engine.main import app
from sigma_engine.project_store import ProjectStore
from sigma_engine.prescore.cross_checks import run_cross_checks


@pytest.fixture
def store(tmp_path):
    return ProjectStore(tmp_path / "projects")


def _make_project(store, project_id="proj-1"):
    store.create_project(project_id, "Coffee Bar", "2026-08-07T00:00:00")


def _save(store, project_id, tool_id, artifact_id, data):
    store.save_artifact(project_id, artifact_id, tool_id, data, "2026-08-07T00:00:00")


def _by_id(results):
    return {r.check_id: r for r in results}


# --- (a) charter business impact vs COPQ total -------------------------------

def test_charter_vs_copq_passes_within_tolerance(store):
    _make_project(store)
    # copq total = 9600 for Q2 2026 -> annualized 38400; charter states the
    # same money per year. Periods differ on purpose: the check must compare
    # annualized values, not raw ones.
    _save(store, "proj-1", "T-02", "copq", make_copq())
    _save(store, "proj-1", "T-03", "charter", make_charter(business_impact={"amount": 38400.0, "unit": "dollars per year", "basis": "COPQ Q2 total x 4"}))
    results = _by_id(run_cross_checks(store, "proj-1"))
    r = results["charter_business_impact_vs_copq_total"]
    assert r.status == "pass"
    assert "38400" in r.detail and "9600" in r.detail


def test_charter_vs_copq_flags_beyond_25_percent(store):
    _make_project(store)
    _save(store, "proj-1", "T-02", "copq", make_copq())  # total 9600/quarter -> 38400 annualized
    _save(store, "proj-1", "T-03", "charter", make_charter(business_impact={"amount": 150000.0, "unit": "dollars per year", "basis": "leadership estimate"}))
    results = _by_id(run_cross_checks(store, "proj-1"))
    r = results["charter_business_impact_vs_copq_total"]
    assert r.status == "flag"
    assert "150000" in r.detail and "9600" in r.detail


def test_charter_vs_copq_advisory_when_period_unknown(store):
    _make_project(store)
    _save(store, "proj-1", "T-02", "copq", make_copq())
    # "dollars" carries no period -- the check must refuse to guess, not flag.
    _save(store, "proj-1", "T-03", "charter", make_charter(business_impact={"amount": 40000.0, "unit": "dollars", "basis": "estimate"}))
    results = _by_id(run_cross_checks(store, "proj-1"))
    r = results["charter_business_impact_vs_copq_total"]
    assert r.status == "advisory"
    assert "same basis" in r.detail


def test_charter_vs_copq_omitted_when_copq_missing(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())
    results = _by_id(run_cross_checks(store, "proj-1"))
    assert "charter_business_impact_vs_copq_total" not in results


# --- (b) charter goal direction vs measured baseline -------------------------

def test_charter_vs_baseline_omitted_when_no_dataset_given(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())  # target 3.0, baseline_value 6.2, lower_is_better
    results = _by_id(run_cross_checks(store, "proj-1", dataset_id=None, column=None))
    assert "charter_goal_vs_measured_baseline" not in results  # no dataset given -- nothing to check yet


def test_charter_vs_baseline_both_directions(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())  # target 3.0 (%), lower_is_better

    # Measured mean 2.0 -- the goal (3.0) is WORSE than (higher than) what's
    # already measured for a lower-is-better metric: flag.
    from sigma_engine.prescore.cross_checks import _charter_vs_baseline
    flagged = _charter_vs_baseline(make_charter(), 2.0)
    assert flagged is not None
    assert flagged.status == "flag"

    # Measured mean 8.0 -- the goal (3.0) is a genuine improvement over
    # what's currently measured: pass.
    passed = _charter_vs_baseline(make_charter(), 8.0)
    assert passed is not None
    assert passed.status == "pass"


def test_charter_vs_baseline_end_to_end_via_saved_dataset(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())  # target 3.0, baseline_value 6.2, lower_is_better
    from sigma_engine.datasets import DatasetStore
    csv_bytes = b"value\n2.0\n2.1\n1.9\n2.0\n"
    meta = DatasetStore(store).save_dataset("proj-1", "measured.csv", csv_bytes, None, "2026-08-07T00:00:00")
    results = _by_id(run_cross_checks(store, "proj-1", dataset_id=meta.dataset_id, column="value"))
    r = results["charter_goal_vs_measured_baseline"]
    assert r.status == "flag"  # measured mean ~2.0 -- target 3.0 is no better


def test_charter_vs_baseline_end_to_end_via_saved_dataset_pass_case(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())  # target 3.0, baseline_value 6.2, lower_is_better
    from sigma_engine.datasets import DatasetStore
    csv_bytes = b"value\n8.0\n8.1\n7.9\n8.0\n"
    meta = DatasetStore(store).save_dataset("proj-1", "measured.csv", csv_bytes, None, "2026-08-07T00:00:00")
    results = _by_id(run_cross_checks(store, "proj-1", dataset_id=meta.dataset_id, column="value"))
    r = results["charter_goal_vs_measured_baseline"]
    assert r.status == "pass"  # measured mean ~8.0 -- target 3.0 is a real improvement


def test_charter_vs_baseline_omitted_when_baseline_value_absent(store):
    _make_project(store)
    charter = make_charter()
    charter["goal"]["baseline_value"] = None
    _save(store, "proj-1", "T-03", "charter", charter)
    from sigma_engine.datasets import DatasetStore
    meta = DatasetStore(store).save_dataset("proj-1", "measured.csv", b"value\n2.0\n2.1\n", None, "2026-08-07T00:00:00")
    results = _by_id(run_cross_checks(store, "proj-1", dataset_id=meta.dataset_id, column="value"))
    assert "charter_goal_vs_measured_baseline" not in results


# --- (c) check-sheet burst entry ---------------------------------------------

def _tap_entries_within_seconds(n, start="2026-08-07T08:00:00", step_seconds=1):
    start_dt = dt.datetime.fromisoformat(start)
    return [
        {
            "entry_id": f"burst-{i}", "category_id": "cat-scratch",
            "timestamp": (start_dt + dt.timedelta(seconds=i * step_seconds)).isoformat(),
            "strata": {}, "note": "", "entry_mode": "tap",
        }
        for i in range(n)
    ]


def test_check_sheet_burst_flags_advisory_when_over_10_in_60_seconds(store):
    _make_project(store)
    entries = _tap_entries_within_seconds(11, step_seconds=1)  # 11 taps across 10 seconds
    _save(store, "proj-1", "T-08", "checksheet", make_check_sheet(entries=entries))
    results = _by_id(run_cross_checks(store, "proj-1"))
    r = results["check_sheet_burst_entry"]
    assert r.status == "advisory"
    assert "burst" in r.detail
    assert "tally-transcription" in r.detail


def test_check_sheet_burst_passes_when_spread_out(store):
    _make_project(store)
    entries = _tap_entries_within_seconds(11, step_seconds=30)  # spread over 5 minutes -- no 60s window has >10
    _save(store, "proj-1", "T-08", "checksheet", make_check_sheet(entries=entries))
    results = _by_id(run_cross_checks(store, "proj-1"))
    assert results["check_sheet_burst_entry"].status == "pass"


def test_check_sheet_burst_ignores_transcribed_entries():
    """A legitimate transcription session drops many entries at the same
    as-of timestamp -- entry_mode="transcribed" must never trip the burst
    advisory (check_sheet.py's whole reason for the field). 5 real taps
    plus 15 transcribed entries land in the same tight window: if the
    transcribed ones were wrongly counted this would read as a 20-entry
    burst; correctly excluded, only the 5 taps count, well under the
    >10 threshold."""
    from sigma_engine.prescore.cross_checks import _check_sheet_burst
    taps = _tap_entries_within_seconds(5, step_seconds=1)
    transcribed = _tap_entries_within_seconds(15, step_seconds=1)
    for e in transcribed:
        e["entry_id"] = f"t-{e['entry_id']}"
        e["entry_mode"] = "transcribed"
        e["count"] = 4
    data = make_check_sheet(entries=taps + transcribed)
    result = _check_sheet_burst(data)
    assert result is not None
    assert result.status == "pass"


def test_check_sheet_burst_omitted_when_only_transcribed_entries_exist(store):
    _make_project(store)
    entries = _tap_entries_within_seconds(15, step_seconds=1)
    for e in entries:
        e["entry_mode"] = "transcribed"
        e["count"] = 4
    _save(store, "proj-1", "T-08", "checksheet", make_check_sheet(entries=entries))
    results = _by_id(run_cross_checks(store, "proj-1"))
    assert "check_sheet_burst_entry" not in results  # nothing tap-mode to judge a burst on


def test_check_sheet_burst_omitted_when_check_sheet_missing(store):
    _make_project(store)
    _save(store, "proj-1", "T-03", "charter", make_charter())
    results = _by_id(run_cross_checks(store, "proj-1"))
    assert "check_sheet_burst_entry" not in results


# --- omission / not-found contract -------------------------------------------

def test_no_checks_when_nothing_is_saved(store):
    _make_project(store)
    assert run_cross_checks(store, "proj-1") == []


def test_run_cross_checks_raises_file_not_found_for_missing_project(store):
    with pytest.raises(FileNotFoundError):
        run_cross_checks(store, "no-such-project")


# --- route-level -------------------------------------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def test_route_runs_all_three_checks_end_to_end(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-03", json=make_charter(business_impact={"amount": 150000.0, "unit": "dollars per year", "basis": "leadership estimate"}))
    client.post("/project/proj-1/artifacts/T-02", json=make_copq())
    client.post("/project/proj-1/artifacts/T-08", json=make_check_sheet(entries=_tap_entries_within_seconds(12, step_seconds=1)))

    resp = client.post("/prescore/cross/proj-1", json={})
    assert resp.status_code == 200, resp.text
    results = {r["check_id"]: r for r in resp.json()}
    assert results["charter_business_impact_vs_copq_total"]["status"] == "flag"  # 150000/yr vs 9600/quarter (38400 annualized)
    assert results["check_sheet_burst_entry"]["status"] == "advisory"
    assert "charter_goal_vs_measured_baseline" not in results  # no dataset given


def test_route_404s_for_missing_project(client):
    resp = client.post("/prescore/cross/no-such-project", json={})
    assert resp.status_code == 404


def test_route_422s_when_column_given_without_dataset_id(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    resp = client.post("/prescore/cross/proj-1", json={"column": "value"})
    assert resp.status_code == 422
