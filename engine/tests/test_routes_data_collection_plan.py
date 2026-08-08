"""T-11 Data Collection Plan route wiring: proves the registry/route
wiring (routes/artifacts.py + routes/prescore.py, both generic and
tool_id-parameterized) actually reaches DataCollectionPlanArtifact -- no
bespoke route file needed for this tool, unlike T-08/T-09's to_dataset."""

from fastapi.testclient import TestClient
import pytest

from factories import make_data_collection_plan
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_validate_and_save_data_collection_plan(client):
    _create_project(client)
    ok = client.post("/artifacts/T-11/validate", json=make_data_collection_plan())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True

    save = client.post("/project/proj-1/artifacts/T-11", json=make_data_collection_plan())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "dcp-001", "tool_id": "T-11", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/dcp-001")
    assert loaded.status_code == 200
    assert loaded.json()["data_type"] == "continuous"


def test_save_rejects_invalid_data_type(client):
    _create_project(client)
    bad = make_data_collection_plan(data_type="attribute")
    resp = client.post("/project/proj-1/artifacts/T-11", json=bad)
    assert resp.status_code == 422


def test_prescore_route_all_pass_for_the_complete_fixture(client):
    _create_project(client)
    resp = client.post("/prescore/T-11", json=make_data_collection_plan())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body) == 6
    assert all(c["status"] == "pass" for c in body), body


def test_prescore_route_flags_an_incomplete_plan(client):
    _create_project(client)
    plan = make_data_collection_plan()
    plan["data_type"] = None
    resp = client.post("/prescore/T-11", json=plan)
    assert resp.status_code == 200, resp.text
    by_id = {c["check_id"]: c["status"] for c in resp.json()}
    assert by_id["data_type_declared"] == "flag"
