"""Route tests for /project/{id}/drafts* (docs/uat/PLAN.md Phase 4.1): the
PUT/GET/DELETE/list surface, 404s on an unknown project or draft, DELETE's
idempotency, and -- the one that guards the design itself -- that saving a
draft never shows up in artifact_index."""

import pytest
from fastapi.testclient import TestClient

from factories import make_picker
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-12T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_put_and_get_draft_round_trip(client):
    _create_project(client)
    payload = {"problem_statement": "487 mis-picks in June", "goal": ""}

    put = client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": payload})
    assert put.status_code == 200, put.text
    body = put.json()
    assert body["tool_id"] == "T-03"
    assert body["updated_at"] == "2026-08-12T00:01:00"
    assert body["payload"] == payload

    get = client.get("/project/proj-1/drafts/T-03")
    assert get.status_code == 200, get.text
    assert get.json() == {"draft": body}


def test_put_overwrites_the_previous_draft(client):
    _create_project(client)
    client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": {"a": 1}})
    second = client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:05:00", "payload": {"a": 2, "b": 3}})
    assert second.status_code == 200, second.text

    get = client.get("/project/proj-1/drafts/T-03")
    assert get.json()["draft"]["payload"] == {"a": 2, "b": 3}
    assert get.json()["draft"]["updated_at"] == "2026-08-12T00:05:00"


def test_get_answers_no_draft_with_a_200_not_a_404(client):
    """Every tool screen asks this on mount and for most tools the answer is
    no. A 404 made the browser log a console error on every ordinary form
    open, and buried a real 404 among expected ones -- the packaged probes
    failed on exactly that. "No draft" is a 200 with nothing in it."""
    _create_project(client)
    resp = client.get("/project/proj-1/drafts/T-03")
    assert resp.status_code == 200
    assert resp.json() == {"draft": None}


def test_delete_then_get_reports_no_draft(client):
    _create_project(client)
    client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": {"a": 1}})

    delete = client.delete("/project/proj-1/drafts/T-03")
    assert delete.status_code == 200, delete.text
    assert delete.json() == {"deleted": True}

    gone = client.get("/project/proj-1/drafts/T-03")
    assert gone.status_code == 200
    assert gone.json() == {"draft": None}


def test_delete_is_idempotent_when_no_draft_ever_existed(client):
    """The client deletes a draft right after a successful artifact save
    and must not have to care whether one existed -- never a 404."""
    _create_project(client)
    resp = client.delete("/project/proj-1/drafts/T-03")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"deleted": True}

    # And again, after it's already gone.
    resp2 = client.delete("/project/proj-1/drafts/T-03")
    assert resp2.status_code == 200
    assert resp2.json() == {"deleted": True}


def test_put_404_for_unknown_project(client):
    resp = client.put("/project/no-such-project/drafts/T-03", json={"updated_at": "2026-08-12T00:00:00", "payload": {}})
    assert resp.status_code == 404


def test_get_404_for_unknown_project(client):
    resp = client.get("/project/no-such-project/drafts/T-03")
    assert resp.status_code == 404


def test_delete_404_for_unknown_project(client):
    resp = client.delete("/project/no-such-project/drafts/T-03")
    assert resp.status_code == 404


def test_list_404_for_unknown_project(client):
    resp = client.get("/project/no-such-project/drafts")
    assert resp.status_code == 404


def test_list_is_empty_then_returns_summaries_not_payloads(client):
    _create_project(client)
    assert client.get("/project/proj-1/drafts").json() == []

    client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": {"big": "payload data"}})
    client.put("/project/proj-1/drafts/T-04", json={"updated_at": "2026-08-12T00:02:00", "payload": {"other": "stuff"}})

    listing = client.get("/project/proj-1/drafts")
    assert listing.status_code == 200, listing.text
    rows = {row["tool_id"]: row for row in listing.json()}
    assert set(rows) == {"T-03", "T-04"}
    assert rows["T-03"] == {"tool_id": "T-03", "updated_at": "2026-08-12T00:01:00"}
    assert "payload" not in rows["T-03"]


def test_unsafe_tool_id_is_rejected_not_500(client, tmp_path):
    _create_project(client)
    # A literal ".." path segment is dot-segment-normalized away before
    # routing (RFC 3986 -- the same reason "/a/b/.." becomes "/a/" in a
    # browser address bar), so it never reaches this router at all; it
    # lands on GET /project/{project_id} instead, which has no PUT, hence
    # 405 here rather than anything from this router's own code. That
    # normalization is a real layer of defense, just not this one's.
    normalized_away = client.put("/project/proj-1/drafts/..", json={"updated_at": "2026-08-12T00:00:00", "payload": {}})
    assert normalized_away.status_code == 405

    # A percent-encoded ".." (%2e%2e) is NOT dot-segment-normalized -- it
    # decodes to the literal two-character string ".." and DOES reach
    # save_draft's tool_id parameter, so this is the case that actually
    # exercises DraftStore's own is_safe_tool_id guard over HTTP.
    encoded_dotdot = client.put("/project/proj-1/drafts/%2e%2e", json={"updated_at": "2026-08-12T00:00:00", "payload": {}})
    assert encoded_dotdot.status_code == 422, encoded_dotdot.text
    assert "not a safe path segment" in encoded_dotdot.json()["detail"]

    # An encoded "/" (%2F) makes the segment span what routing treats as
    # two path parts, so it never matches this router's single-segment
    # {tool_id} pattern -- Starlette 404s from routing itself, before any
    # of this router's code runs.
    encoded_slash = client.put("/project/proj-1/drafts/..%2Fmeta", json={"updated_at": "2026-08-12T00:00:00", "payload": {}})
    assert encoded_slash.status_code == 404

    # Whichever layer caught each attempt, none of them wrote a file
    # anywhere outside this project's own drafts/ directory.
    assert list(tmp_path.rglob("meta.json")) == []


# ---------------------------------------------------------------------------
# The design guarantee: a draft is not an artifact.
# ---------------------------------------------------------------------------


def test_saving_a_draft_never_appears_in_artifact_index(client):
    _create_project(client)

    # A draft for a tool that has never been actually saved as an artifact.
    client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": {"problem_statement": "typing..."}})

    info = client.get("/project/proj-1")
    assert info.status_code == 200
    assert info.json()["artifact_index"] == {}

    listing = client.get("/projects")
    row = next(r for r in listing.json() if r["project_id"] == "proj-1")
    assert row["artifact_count"] == 0
    assert row["tools_done"] == []


def test_saving_a_draft_alongside_a_real_artifact_does_not_pollute_its_index(client):
    _create_project(client)

    saved = client.post("/project/proj-1/artifacts/T-01", json=make_picker())
    assert saved.status_code == 200, saved.text

    # A draft in flight for a different tool at the same time as a real,
    # saved artifact for T-01.
    client.put("/project/proj-1/drafts/T-03", json={"updated_at": "2026-08-12T00:01:00", "payload": {"problem_statement": "typing..."}})

    info = client.get("/project/proj-1")
    assert set(info.json()["artifact_index"].keys()) == {"picker-001"}
    assert info.json()["artifact_index"]["picker-001"]["tool_id"] == "T-01"

    project_info = client.get("/project/proj-1/info")
    assert project_info.json()["artifact_count"] == 1
