"""Route tests for T-10 (generic artifact CRUD + prescore via
ARTIFACT_REGISTRY/PRESCORE_REGISTRY, same contract as T-01..T-09/T-12) --
proves the build brief's "zero new route code" claim: T-10 rides
/artifacts/T-10/validate, /project/{id}/artifacts/T-10, and /prescore/T-10
purely off the registry, same as every other tool."""

import pytest
from fastapi.testclient import TestClient

from factories import make_dpmo_block, make_yield_calc
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id: str = "proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_validate_yield_calc(client):
    _create_project(client)
    ok = client.post("/artifacts/T-10/validate", json=make_yield_calc())
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["valid"] is True
    assert body["artifact"]["rty_result"]["value"] == pytest.approx(0.8826259320313404)
    assert body["artifact"]["dpmo_result"]["value"]["dpmo"] == pytest.approx(6210.0)
    assert body["artifact"]["dpmo_result"]["value"]["convention"] == "with 1.5σ shift"


def test_save_and_load_yield_calc(client):
    _create_project(client)
    save = client.post("/project/proj-1/artifacts/T-10", json=make_yield_calc())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "yieldcalc-001", "tool_id": "T-10", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/yieldcalc-001")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["rty_result"]["value"] == pytest.approx(0.8826259320313404)


def test_prescore_yield_calc_via_registry(client):
    _create_project(client)
    prescore = client.post("/prescore/T-10", json=make_yield_calc())
    assert prescore.status_code == 200, prescore.text
    check_ids = {c["check_id"] for c in prescore.json()}
    assert "rty_only_claimed_in_series" in check_ids
    assert "rty_matches_recomputed" in check_ids
    assert "dpmo_result_matches_recomputed" in check_ids
    assert "opportunity_inflation_justified" in check_ids


def test_save_rejects_invalid_yield_calc(client):
    _create_project(client)
    bad = make_yield_calc()
    bad["steps"] = []
    resp = client.post("/project/proj-1/artifacts/T-10", json=bad)
    assert resp.status_code == 422


def test_save_rejects_uninjustified_opportunity_inflation(client):
    _create_project(client)
    bad = make_yield_calc(dpmo_block=make_dpmo_block(opportunities_per_unit=5, opportunity_justification=""))
    resp = client.post("/project/proj-1/artifacts/T-10", json=bad)
    assert resp.status_code == 422
    assert "opportunity_justification" in str(resp.json()["detail"])
