"""A project id becomes a folder name, and it arrives from outside.

The create screen has a box labelled "Project folder (ID)" that a user types
into, so this is not only an attack surface -- it is a footgun with a text
field in front of it. `root / "../../etc"` is a perfectly good Path, and
before the guard in project_store._safe_segment there was nothing between
that string and the filesystem.

Everything else inherits the fix: DatasetStore, DraftStore and the floorplan
store all build their paths from ProjectStore.resolved_project_path, so a
contained project id contains them too. These tests pin that, so a later
store added the same way cannot quietly reopen the hole.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sigma_engine.main import app
from sigma_engine.project_store import ProjectStore, UnsafeIdError
from sigma_engine.routes.deps import get_store

ESCAPES = ["../evil", "../../etc", "a/b", "a\\b", "..", ".", "", "with space", "dot.dot", "tilde~"]


@pytest.fixture()
def store(tmp_path):
    return ProjectStore(tmp_path / "projects")


@pytest.mark.parametrize("bad", ESCAPES)
def test_project_id_that_is_not_a_plain_name_is_refused(store, bad):
    with pytest.raises(UnsafeIdError):
        store.create_project(bad, "Escape", "2026-08-12T00:00:00Z")


def test_nothing_is_written_outside_the_projects_root(store, tmp_path):
    # The path this id would actually have reached: root is <tmp>/projects,
    # so "../../escaped" resolves to <tmp>/../escaped -- OUTSIDE tmp_path,
    # not inside it. Asserting on tmp_path would pass with the guard removed
    # and prove nothing, which is the whole trap in a test like this.
    escaped = (store.root / ".." / ".." / "escaped").resolve()
    assert not escaped.exists(), "precondition: the target must not already exist"

    with pytest.raises(UnsafeIdError):
        store.create_project("../../escaped", "Escape", "2026-08-12T00:00:00Z")

    # The interesting assertion is not the raise, it is the filesystem.
    assert not escaped.exists()
    assert list(tmp_path.glob("**/escaped*")) == []


@pytest.mark.parametrize("bad", ["../other", "a/b", ".."])
def test_artifact_id_is_contained_too(store, bad):
    store.create_project("real-project", "Real", "2026-08-12T00:00:00Z")
    with pytest.raises(UnsafeIdError):
        store.save_artifact("real-project", bad, "T-01", {"x": 1}, "2026-08-12T00:00:00Z")


def test_the_ids_this_app_actually_mints_still_work(store):
    """The guard must tighten nothing that already worked: a slug from the
    create screen, and the uuid hex the engine mints for artifacts."""
    meta = store.create_project("june-2026-warehouse-picking-errors", "June", "2026-08-12T00:00:00Z")
    assert meta.project_id == "june-2026-warehouse-picking-errors"
    version = store.save_artifact(
        "june-2026-warehouse-picking-errors", "9d2c5177e5afe041", "T-01", {"x": 1}, "2026-08-12T00:00:00Z"
    )
    assert version == 1
    assert store.load_artifact("june-2026-warehouse-picking-errors", "9d2c5177e5afe041") == {"x": 1}


def test_a_symlink_out_of_the_projects_folder_is_refused(store, tmp_path):
    """Belt as well as braces. The id is a plain name, so it passes
    _safe_segment -- but the folder it names points somewhere else."""
    store.root.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (store.root / "sneaky").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        store.resolved_project_path("sneaky")


def test_a_weirdly_named_folder_does_not_break_the_project_list(store):
    """list_projects walks whatever is on disk. A folder the guard would
    reject must be skipped, not raise -- one odd directory cannot be allowed
    to make every real project unlistable."""
    store.create_project("good-one", "Good", "2026-08-12T00:00:00Z")
    (store.root / "not a project").mkdir()
    assert [m.project_id for m in store.list_projects()] == ["good-one"]


def test_over_http_a_crafted_id_is_a_422_not_a_500(tmp_path):
    """Percent-encoded dot segments survive URL normalisation and reach the
    handler, so the store's guard is what actually stops them -- and the
    caller should see a 422, not the engine falling over."""
    store = ProjectStore(tmp_path / "projects")
    app.dependency_overrides[get_store] = lambda: store
    try:
        client = TestClient(app)
        created = client.post(
            "/project/create",
            json={"project_id": "../../escaped", "name": "Escape", "created_at": "2026-08-12T00:00:00Z"},
        )
        assert created.status_code == 422
        fetched = client.get("/project/%2e%2e%2f%2e%2e%2fescaped")
        assert fetched.status_code in (404, 422)
        assert not (tmp_path / "escaped").exists()
    finally:
        app.dependency_overrides.pop(get_store, None)
