"""Route smoke tests for every new endpoint, plus /health and /smoke stay green."""

import pytest
from fastapi.testclient import TestClient

from factories import make_charter, make_picker, make_sipoc, make_voc_ctq
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def test_health_and_smoke_still_green(client):
    assert client.get("/health").status_code == 200
    assert client.get("/smoke").json()["match"] is True


def test_project_create_and_open(client):
    resp = client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["project_id"] == "proj-1"

    resp2 = client.get("/project/proj-1")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "Coffee Bar"

    assert client.get("/project/no-such-project").status_code == 404


def test_validate_artifact_endpoint(client):
    ok = client.post("/artifacts/T-01/validate", json=make_picker())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True

    bad_tool = client.post("/artifacts/T-99/validate", json=make_picker())
    assert bad_tool.status_code == 404

    bad_data = client.post("/artifacts/T-01/validate", json={"nope": True})
    assert bad_data.status_code == 422


def test_save_load_and_list_versions(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    save1 = client.post("/project/proj-1/artifacts/T-03", json=make_charter())
    assert save1.status_code == 200, save1.text
    assert save1.json() == {"artifact_id": "charter-001", "tool_id": "T-03", "version": 1}

    save2 = client.post("/project/proj-1/artifacts/T-03", json=make_charter(notes="revised after gemba walk"))
    assert save2.json()["version"] == 2

    loaded = client.get("/project/proj-1/artifacts/charter-001")
    assert loaded.status_code == 200
    assert loaded.json()["notes"] == "revised after gemba walk"  # latest by default

    loaded_v1 = client.get("/project/proj-1/artifacts/charter-001", params={"version": 1})
    assert loaded_v1.json()["notes"] is None

    versions = client.get("/project/proj-1/artifacts/charter-001/versions")
    assert versions.json() == {"artifact_id": "charter-001", "versions": [1, 2]}


def test_save_rejects_invalid_artifact(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    bad = make_charter()
    del bad["process_owner"]
    resp = client.post("/project/proj-1/artifacts/T-03", json=bad)
    assert resp.status_code == 422


def test_prescore_endpoint(client):
    resp = client.post("/prescore/T-04", json=make_sipoc(step_count=3))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body[0]["check_id"] == "step_count_range"
    assert body[0]["status"] == "hard_flag"

    resp2 = client.post("/prescore/T-05", json=make_voc_ctq())
    assert resp2.json()[0]["status"] == "pass"

    assert client.post("/prescore/T-99", json={}).status_code == 404


def test_gates_check_and_override_flow(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    check = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert check.status_code == 200
    assert check.json()["status"] == "SOFT_BLOCK"
    assert set(check.json()["missing"]) == {"T-04", "T-05"}

    empty_reason = client.post(
        "/gates/override",
        json={"gate_id": "define_to_measure", "project_id": "proj-1", "reason": "", "timestamp": "2026-08-07T04:00:00"},
    )
    assert empty_reason.status_code == 422

    override = client.post(
        "/gates/override",
        json={
            "gate_id": "define_to_measure", "project_id": "proj-1",
            "reason": "SIPOC and CTQ pending; unblocking to start Measure prep", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 200, override.text
    assert override.json()["gate_id"] == "define_to_measure"


def test_gates_hard_block_and_override_refused(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    exit01_picker = make_picker(route="EXIT-01")
    exit01_picker["data_obtainable"] = {"answer": False, "detail": "No data source exists yet."}
    client.post("/project/proj-1/artifacts/T-01", json=exit01_picker)

    check = client.post("/gates/check", json={"gate_id": "intake_picker_not_exit01", "project_id": "proj-1"})
    assert check.json()["status"] == "HARD_BLOCK"

    override = client.post(
        "/gates/override",
        json={
            "gate_id": "intake_picker_not_exit01", "project_id": "proj-1",
            "reason": "skip anyway", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 403
