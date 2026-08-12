"""Deleting a project -- the one thing a tester swept the whole app for.

He checked the project list, diagnostics, advisor settings, hover and
right-click on the card, and found no undo and no delete anywhere. His own
framing was not outrage but arithmetic: "if I keep using it I will
eventually create junk."

These tests pin the two things that make a destructive route safe to have:
it removes exactly the project asked for and nothing beside it, and it
refuses rather than reassures when the project is not there.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sigma_engine.main import app
from sigma_engine.project_store import ProjectStore, UnsafeIdError
from sigma_engine.routes.deps import get_store


@pytest.fixture()
def store(tmp_path):
    return ProjectStore(tmp_path / "projects")


@pytest.fixture()
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_store, None)


def _make(store, project_id: str) -> None:
    store.create_project(project_id, project_id.title(), "2026-08-12T00:00:00Z")
    store.save_artifact(project_id, "art-1", "T-01", {"x": 1}, "2026-08-12T00:00:00Z")


def test_delete_removes_the_project_and_its_artifacts(store):
    _make(store, "doomed")
    assert store.resolved_project_path("doomed").exists()
    store.delete_project("doomed")
    assert not (store.root / "doomed").exists()
    with pytest.raises(FileNotFoundError):
        store.load_project("doomed")


def test_delete_leaves_every_other_project_alone(store):
    """The assertion that actually matters on a destructive operation."""
    _make(store, "keep-one")
    _make(store, "doomed")
    _make(store, "keep-two")
    store.delete_project("doomed")
    assert sorted(m.project_id for m in store.list_projects()) == ["keep-one", "keep-two"]
    assert store.load_artifact("keep-one", "art-1") == {"x": 1}
    assert store.load_artifact("keep-two", "art-1") == {"x": 1}


def test_delete_of_a_project_that_never_existed_is_a_404_not_a_shrug(client):
    """Unlike a draft delete, this is deliberately not idempotent: a
    cheerful "done" for a project that isn't there most likely means the
    user is looking at the wrong name, or something else already removed
    their work. Either way they should hear about it."""
    resp = client.delete("/project/no-such-project")
    assert resp.status_code == 404


def test_delete_over_http_round_trip(client, store):
    _make(store, "doomed")
    resp = client.delete("/project/doomed")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"deleted": True}
    assert client.get("/project/doomed").status_code == 404


@pytest.mark.parametrize("bad", ["../../etc", "a/b", ".."])
def test_delete_cannot_be_aimed_outside_the_projects_folder(store, tmp_path, bad):
    """The nightmare case for a recursive delete. resolved_project_path is
    what stops it, and this is here so nobody later 'simplifies' this method
    into joining its own path."""
    _make(store, "keep-me")
    outside = tmp_path / "bystander"
    outside.mkdir()
    (outside / "important.txt").write_text("do not delete me", encoding="utf-8")

    with pytest.raises((UnsafeIdError, FileNotFoundError)):
        store.delete_project(bad)

    assert (outside / "important.txt").exists()
    assert store.load_project("keep-me").project_id == "keep-me"


def test_delete_refuses_a_directory_that_is_not_a_project(store):
    """A folder under the projects root with no project.json is somebody
    else's data sitting in the wrong place. Do not recursively delete it on
    the strength of a matching name."""
    store.root.mkdir(parents=True, exist_ok=True)
    stray = store.root / "not-a-project"
    stray.mkdir()
    (stray / "holiday-photos.txt").write_text("mine", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        store.delete_project("not-a-project")
    assert (stray / "holiday-photos.txt").exists()
