"""Tests for drafts.py: DraftStore save/load/delete/list round trips, the
tool_id path-safety guard, and the "payload is never validated" guarantee
that is the entire reason this module exists (docs/uat/PLAN.md Phase 4.1)."""

import pytest

from sigma_engine.drafts import DraftStore, is_safe_tool_id
from sigma_engine.project_store import ProjectStore


def test_save_and_load_draft_round_trips(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)

    saved = store.save_draft("proj-1", "T-03", {"problem_statement": "487 mis-picks in June"}, "2026-08-12T00:01:00")
    assert saved.tool_id == "T-03"
    assert saved.updated_at == "2026-08-12T00:01:00"
    assert saved.payload == {"problem_statement": "487 mis-picks in June"}

    loaded = store.load_draft("proj-1", "T-03")
    assert loaded == saved


def test_save_draft_overwrites_the_previous_one(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)

    store.save_draft("proj-1", "T-03", {"problem_statement": "first draft"}, "2026-08-12T00:01:00")
    second = store.save_draft("proj-1", "T-03", {"problem_statement": "second draft", "goal": "cut errors 50%"}, "2026-08-12T00:05:00")

    loaded = store.load_draft("proj-1", "T-03")
    assert loaded == second
    assert loaded.payload == {"problem_statement": "second draft", "goal": "cut errors 50%"}
    # Upsert, not versioned -- no v1/v2 history for a draft, unlike an artifact.
    assert not (projects.resolved_project_path("proj-1") / "drafts" / "T-03").is_dir()


def test_load_missing_draft_raises_file_not_found(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    with pytest.raises(FileNotFoundError):
        store.load_draft("proj-1", "T-03")


def test_delete_is_idempotent_when_no_draft_exists(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    # Must not raise: the client deletes on a successful artifact save and
    # must not have to first check whether a draft was ever there.
    store.delete_draft("proj-1", "T-03")
    store.delete_draft("proj-1", "T-03")


def test_delete_removes_a_saved_draft(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    store.save_draft("proj-1", "T-03", {"a": 1}, "2026-08-12T00:01:00")

    store.delete_draft("proj-1", "T-03")

    with pytest.raises(FileNotFoundError):
        store.load_draft("proj-1", "T-03")
    # And deleting again is still a no-op, not a second error.
    store.delete_draft("proj-1", "T-03")


def test_save_404s_on_missing_project(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    store = DraftStore(projects)
    with pytest.raises(FileNotFoundError):
        store.save_draft("no-such-project", "T-03", {"a": 1}, "2026-08-12T00:00:00")


def test_load_404s_on_missing_project(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    store = DraftStore(projects)
    with pytest.raises(FileNotFoundError):
        store.load_draft("no-such-project", "T-03")


def test_delete_404s_on_missing_project(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    store = DraftStore(projects)
    with pytest.raises(FileNotFoundError):
        store.delete_draft("no-such-project", "T-03")


def test_list_404s_on_missing_project(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    store = DraftStore(projects)
    with pytest.raises(FileNotFoundError):
        store.list_drafts("no-such-project")


def test_list_is_empty_when_nothing_saved(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    assert store.list_drafts("proj-1") == []


def test_list_returns_every_saved_draft(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    store.save_draft("proj-1", "T-03", {"a": 1}, "2026-08-12T00:01:00")
    store.save_draft("proj-1", "T-04", {"b": 2}, "2026-08-12T00:02:00")

    drafts = {d.tool_id: d for d in store.list_drafts("proj-1")}
    assert set(drafts) == {"T-03", "T-04"}
    assert drafts["T-03"].updated_at == "2026-08-12T00:01:00"
    assert drafts["T-04"].updated_at == "2026-08-12T00:02:00"


def test_payload_is_never_validated(tmp_path):
    """The whole point of a draft: an incomplete, malformed-by-artifact-
    standards payload is saved and returned exactly as given, never
    checked against T-03's (or any tool's) schema."""
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)

    # No artifact_id, no schema_version, wrong types, an extra unknown
    # field -- everything a real ArtifactBase subclass would reject.
    garbage_payload = {"problem_statement": "typing in progress", "owner": None, "random_junk": [1, 2, {"x": "y"}]}
    saved = store.save_draft("proj-1", "T-03", garbage_payload, "2026-08-12T00:01:00")
    assert saved.payload == garbage_payload
    assert store.load_draft("proj-1", "T-03").payload == garbage_payload

    # Even a bare string or list payload (not an object at all) round-trips.
    store.save_draft("proj-1", "T-04", "just a string, not even an object", "2026-08-12T00:02:00")
    assert store.load_draft("proj-1", "T-04").payload == "just a string, not even an object"


# ---------------------------------------------------------------------------
# tool_id path safety
# ---------------------------------------------------------------------------


def test_is_safe_tool_id_accepts_real_tool_ids():
    for tool_id in ("T-01", "T-25", "T-35"):
        assert is_safe_tool_id(tool_id)


@pytest.mark.parametrize(
    "unsafe",
    [
        "../../meta",
        "../meta",
        "..",
        "T-01/../../meta",
        "T-01/etc",
        "a/b",
        "",
        ".",
    ],
)
def test_is_safe_tool_id_rejects_traversal_shapes(unsafe):
    assert not is_safe_tool_id(unsafe)


def test_unsafe_tool_id_raises_and_nothing_escapes_the_project_directory(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)

    with pytest.raises(ValueError):
        store.save_draft("proj-1", "../../meta", {"x": 1}, "2026-08-12T00:01:00")

    # Nothing named "meta.json" was written anywhere under tmp_path, and
    # the tool_id check runs before any directory gets created, so the
    # project's drafts/ folder itself never came into existence either.
    assert list(tmp_path.rglob("meta.json")) == []
    assert not (tmp_path / "projects" / "proj-1" / "drafts").exists()


def test_unsafe_tool_id_raises_on_load_delete_too(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)

    with pytest.raises(ValueError):
        store.load_draft("proj-1", "../../meta")
    with pytest.raises(ValueError):
        store.delete_draft("proj-1", "../../meta")


def test_writes_are_atomic_no_stray_temp_files(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-12T00:00:00")
    store = DraftStore(projects)
    store.save_draft("proj-1", "T-03", {"a": 1}, "2026-08-12T00:01:00")

    drafts_dir = projects.resolved_project_path("proj-1") / "drafts"
    leftover_temp_files = [p for p in drafts_dir.iterdir() if p.name.endswith(".tmp")]
    assert leftover_temp_files == []
    assert (drafts_dir / "T-03.json").exists()
