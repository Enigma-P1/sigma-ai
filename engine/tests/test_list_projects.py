"""GET /projects — what is actually on disk.

The Open-a-project screen was backed only by a localStorage recently-opened
history, so a project placed in the projects folder by hand was invisible in
the app by construction, with no error to explain it. Someone unzipping the
worked example hit exactly that (docs/field-notes.md). These tests pin the
endpoint that fixes it.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from sigma_engine.main import app
from sigma_engine.project_store import ProjectStore


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path))
    return TestClient(app)


def test_lists_a_project_that_was_never_opened_in_this_app(tmp_path, monkeypatch):
    """The exact bug: a complete project dropped into the folder, never
    opened on this machine, therefore absent from every list the app had."""
    store = ProjectStore(tmp_path)
    store.create_project("dropped-in", "Dropped in by hand", "2026-08-01T00:00:00")

    rows = _client(tmp_path, monkeypatch).get("/projects").json()
    assert [r["project_id"] for r in rows] == ["dropped-in"]
    assert rows[0]["name"] == "Dropped in by hand"


def test_empty_root_returns_an_empty_list_not_an_error(tmp_path, monkeypatch):
    assert _client(tmp_path, monkeypatch).get("/projects").json() == []


def test_a_corrupt_project_does_not_hide_the_healthy_ones(tmp_path, monkeypatch):
    """One unreadable folder must not make every other project unlistable.
    Raising here would turn a single bad file into total data loss from the
    user's side, which is the failure mode this whole area keeps having."""
    store = ProjectStore(tmp_path)
    store.create_project("good", "Good project", "2026-08-01T00:00:00")
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "project.json").write_text("{ not json", encoding="utf-8")

    rows = _client(tmp_path, monkeypatch).get("/projects").json()
    assert [r["project_id"] for r in rows] == ["good"]


def test_a_stray_directory_without_project_json_is_skipped(tmp_path, monkeypatch):
    (tmp_path / "not-a-project").mkdir()
    assert _client(tmp_path, monkeypatch).get("/projects").json() == []


def test_stray_files_at_the_root_are_ignored(tmp_path, monkeypatch):
    (tmp_path / ".DS_Store").write_text("junk", encoding="utf-8")
    assert _client(tmp_path, monkeypatch).get("/projects").json() == []


def test_ordered_newest_updated_first(tmp_path, monkeypatch):
    store = ProjectStore(tmp_path)
    store.create_project("older", "Older", "2026-01-01T00:00:00")
    store.create_project("newer", "Newer", "2026-07-01T00:00:00")
    rows = _client(tmp_path, monkeypatch).get("/projects").json()
    assert [r["project_id"] for r in rows] == ["newer", "older"]


def test_summary_says_where_the_project_got_to(tmp_path, monkeypatch):
    """A list that only names projects makes you open each one to remember
    where you were, which is the thing it exists to save you."""
    store = ProjectStore(tmp_path)
    store.create_project("p", "P", "2026-08-01T00:00:00")
    store.save_artifact(
        "p",
        "charter",
        "T-03",
        {"artifact_id": "charter", "tool_id": "T-03", "schema_version": 1},
        "2026-08-02T00:00:00",
    )
    store.save_artifact(
        "p",
        "fmea",
        "T-16",
        {"artifact_id": "fmea", "tool_id": "T-16", "schema_version": 1},
        "2026-08-03T00:00:00",
    )
    row = _client(tmp_path, monkeypatch).get("/projects").json()[0]
    assert row["artifact_count"] == 2
    assert row["tools_done"] == ["T-03", "T-16"]
    # T-16 is Analyze, T-03 is Define -- the furthest phase reached wins.
    assert row["latest_phase"] == "Analyze"


def test_store_list_projects_is_usable_without_the_route(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("a", "A", "2026-08-01T00:00:00")
    assert [m.project_id for m in store.list_projects()] == ["a"]


def test_missing_root_directory_is_not_an_error(tmp_path):
    assert ProjectStore(tmp_path / "does-not-exist").list_projects() == []
