"""Route tests for GET /project/{project_id}/artifacts/T-03/pdf (M1 export
brief): 200 + application/pdf on a saved charter (latest version by
default, an explicit ?version=N otherwise), 404 clean when the project or
the charter doesn't exist yet.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from factories import load_demo_charter, make_charter
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client: TestClient, project_id: str = "proj-1") -> None:
    resp = client.post(
        "/project/create",
        json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"},
    )
    assert resp.status_code == 200, resp.text


def test_charter_pdf_200_on_saved_charter(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    resp = client.get("/project/proj-1/artifacts/T-03/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"
    assert 'filename="charter-001-v1.pdf"' in resp.headers["content-disposition"]


def test_charter_pdf_defaults_to_latest_version_and_honors_explicit_version(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())
    client.post("/project/proj-1/artifacts/T-03", json=make_charter(notes="revised after gemba walk"))

    latest = client.get("/project/proj-1/artifacts/T-03/pdf")
    assert latest.status_code == 200
    assert 'filename="charter-001-v2.pdf"' in latest.headers["content-disposition"]

    v1 = client.get("/project/proj-1/artifacts/T-03/pdf", params={"version": 1})
    assert v1.status_code == 200
    assert 'filename="charter-001-v1.pdf"' in v1.headers["content-disposition"]


def test_charter_pdf_404_on_missing_project(client):
    resp = client.get("/project/no-such-project/artifacts/T-03/pdf")
    assert resp.status_code == 404


def test_charter_pdf_404_when_no_charter_saved_yet(client):
    _create_project(client)
    resp = client.get("/project/proj-1/artifacts/T-03/pdf")
    assert resp.status_code == 404


def test_charter_pdf_404_on_out_of_range_version(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    resp = client.get("/project/proj-1/artifacts/T-03/pdf", params={"version": 99})
    assert resp.status_code == 404


def test_charter_pdf_works_for_the_demo_fixtures_own_artifact_id(client):
    """demo/coffee-bar/define/charter.json uses artifact_id "coffee-charter",
    not the desktop app's fixed "charter" (CharterForm.tsx) -- the route
    looks up by tool_id (routes/export.py's _find_charter_artifact_id), so
    both work without the caller knowing the id in advance."""
    demo_charter = load_demo_charter()

    client.post(
        "/project/create",
        json={"project_id": "coffee-bar", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"},
    )
    save = client.post("/project/coffee-bar/artifacts/T-03", json=demo_charter)
    assert save.status_code == 200, save.text

    resp = client.get("/project/coffee-bar/artifacts/T-03/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"
    assert 'filename="coffee-charter-v1.pdf"' in resp.headers["content-disposition"]
