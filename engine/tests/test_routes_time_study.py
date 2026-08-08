"""Route tests for T-09: generic CRUD plus the per-element to_dataset
action and its round trip into /stats/baseline (feeds baseline with no
re-typed copy of the timed cycles)."""

import pytest
from fastapi.testclient import TestClient

from factories import make_time_study
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_validate_and_save_time_study(client):
    _create_project(client)
    ok = client.post("/artifacts/T-09/validate", json=make_time_study())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True
    stats = {s["element_id"]: s for s in ok.json()["artifact"]["element_stats"]["value"]}
    assert stats["steam-milk"]["n"] == 5
    assert len(stats["steam-milk"]["outliers"]) == 1

    save = client.post("/project/proj-1/artifacts/T-09", json=make_time_study())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "timestudy-001", "tool_id": "T-09", "version": 1}


def test_prescore_route(client):
    _create_project(client)
    prescore = client.post("/prescore/T-09", json=make_time_study())
    assert prescore.status_code == 200, prescore.text
    check_ids = {c["check_id"] for c in prescore.json()}
    assert "cycle_count_floor" in check_ids
    assert "outliers_have_notes" in check_ids


def test_to_dataset_404_when_artifact_never_saved(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/time-study/no-such-artifact/to-dataset",
        json={"element_id": "steam-milk", "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 404


def test_to_dataset_422_for_an_unknown_element(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-09", json=make_time_study())
    resp = client.post(
        "/project/proj-1/time-study/timestudy-001/to-dataset",
        json={"element_id": "no-such-element", "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 422


# --- The zero-re-entry round trip: time study element -> dataset -> baseline ---


def test_to_dataset_then_baseline_runs_on_the_flagged_element(client):
    _create_project(client)
    save = client.post("/project/proj-1/artifacts/T-09", json=make_time_study())
    assert save.status_code == 200, save.text

    to_dataset = client.post(
        "/project/proj-1/time-study/timestudy-001/to-dataset",
        json={"element_id": "steam-milk", "created_at": "2026-08-07T14:00:00"},
    )
    assert to_dataset.status_code == 200, to_dataset.text
    dataset = to_dataset.json()
    assert dataset["row_count"] == 5
    assert dataset["source_artifact_id"] == "timestudy-001"
    assert dataset["source_tool_id"] == "T-09"

    baseline = client.post(
        "/stats/baseline",
        json={
            "project_id": "proj-1", "dataset_id": dataset["dataset_id"], "column": "seconds",
            "usl": 30, "lsl": 0, "operational_definition_ok": True,
        },
    )
    assert baseline.status_code == 200, baseline.text
    body = baseline.json()
    # The hash chain: what /stats/baseline echoes back matches what the
    # to_dataset save actually recorded -- independently re-verifiable
    # (same contract test_routes_datasets.py proves for a plain CSV import).
    assert body["dataset_provenance"] == {
        "dataset_id": dataset["dataset_id"], "dataset_sha256": dataset["sha256"],
        "column": "seconds", "row_count_used": 5,
    }
    assert body["descriptive"]["value"]["n"] == 5
    assert body["descriptive"]["value"]["mean"] == pytest.approx(15.2)


def test_to_dataset_per_element_produces_independent_datasets(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-09", json=make_time_study())
    steam = client.post(
        "/project/proj-1/time-study/timestudy-001/to-dataset",
        json={"element_id": "steam-milk", "created_at": "2026-08-07T14:00:00"},
    ).json()
    shot = client.post(
        "/project/proj-1/time-study/timestudy-001/to-dataset",
        json={"element_id": "pull-shot", "created_at": "2026-08-07T14:01:00"},
    ).json()
    assert steam["dataset_id"] != shot["dataset_id"]
    assert "steam-milk" in steam["source_filename"]
    assert "pull-shot" in shot["source_filename"]
