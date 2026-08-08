"""Route smoke tests for every new endpoint, plus /health and /smoke stay green."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from factories import make_charter, make_picker, make_process_map, make_sipoc, make_voc_ctq
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
    assert check.json()["overridden"] is False

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
    assert set(override.json()["missing"]) == {"T-04", "T-05"}

    # Re-checking the same gate now reads CLEAR-with-override-note -- the
    # override loop feeds back into check() instead of the caller having to
    # remember client-side that it already logged a reason.
    recheck = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert recheck.status_code == 200
    assert recheck.json()["status"] == "CLEAR"
    assert recheck.json()["overridden"] is True
    assert recheck.json()["override_reason"] == "SIPOC and CTQ pending; unblocking to start Measure prep"
    assert recheck.json()["missing"] == []


def test_stale_override_does_not_clear_the_gate(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    # Override while both T-04 and T-05 are missing.
    override = client.post(
        "/gates/override",
        json={
            "gate_id": "define_to_measure", "project_id": "proj-1",
            "reason": "SIPOC pending, unblocking to prep Measure templates", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 200, override.text

    # Artifacts change: SIPOC gets saved for real, so the missing set is now
    # just T-05 -- different from what the override covered.
    client.post("/project/proj-1/artifacts/T-04", json=make_sipoc())

    recheck = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert recheck.status_code == 200
    assert recheck.json()["status"] == "SOFT_BLOCK"
    assert recheck.json()["overridden"] is False
    assert recheck.json()["missing"] == ["T-05"]


def test_project_info_returns_absolute_path_and_artifact_summary(client, tmp_path):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())

    resp = client.get("/project/proj-1/info")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["project_id"] == "proj-1"
    assert body["name"] == "Coffee Bar"
    assert body["artifact_count"] == 1
    assert body["artifact_index"]["picker-001"] == {"tool_id": "T-01", "latest_version": 1}
    assert Path(body["folder_path"]).is_absolute()
    assert Path(body["folder_path"]) == (tmp_path / "projects" / "proj-1").resolve()

    assert client.get("/project/no-such-project/info").status_code == 404


def test_process_map_crud_and_prescore_via_registry(client):
    """T-06 end-to-end through the generic registry-driven routes: validate,
    save (longest_step/constraint_step computed server-side), load, and
    prescore."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_process_map(demand={"available_time_minutes": 480, "demand_units": 96})
    validated = client.post("/artifacts/T-06/validate", json=body)
    assert validated.status_code == 200, validated.text
    # step-2 ("Wait for register", non_value_add, 4.0 min) is the longest
    # step of any type; step-3 ("Make drink", value_add, 3.0 min) is the
    # longest PROCESSING step, so it's named the constraint.
    assert validated.json()["artifact"]["longest_step"]["value"]["step_id"] == "step-2"
    assert validated.json()["artifact"]["constraint_step"]["value"]["step_id"] == "step-3"

    saved = client.post("/project/proj-1/artifacts/T-06", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "process-map-001", "tool_id": "T-06", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/process-map-001")
    assert loaded.status_code == 200
    assert loaded.json()["constraint_step"]["value"]["meets_pace"] is True

    prescore = client.post("/prescore/T-06", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["lane_owner_present"] == "pass"
    assert statuses["bottleneck_fields_consistency"] == "pass"


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
