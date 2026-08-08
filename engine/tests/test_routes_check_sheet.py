"""Route tests for T-08: generic CRUD (registry-driven, T-12's contract)
plus the check-sheet-specific to_dataset action and its round trip into
/stats/pareto (rubric R-MEA-06 #3: the collection artifact IS the dataset
Pareto runs on -- no re-typed intermediate copy)."""

import pytest
from fastapi.testclient import TestClient

from factories import make_check_sheet
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_validate_and_save_check_sheet(client):
    _create_project(client)
    ok = client.post("/artifacts/T-08/validate", json=make_check_sheet())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True

    save = client.post("/project/proj-1/artifacts/T-08", json=make_check_sheet())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "checksheet-001", "tool_id": "T-08", "version": 1}


def test_prescore_route(client):
    _create_project(client)
    prescore = client.post("/prescore/T-08", json=make_check_sheet())
    assert prescore.status_code == 200, prescore.text
    check_ids = {c["check_id"] for c in prescore.json()}
    assert "strata_declared" in check_ids
    assert "entries_present" in check_ids


def test_to_dataset_404_when_artifact_never_saved(client):
    _create_project(client)
    resp = client.post("/project/proj-1/check-sheet/no-such-artifact/to-dataset", json={"created_at": "2026-08-07T01:00:00"})
    assert resp.status_code == 404


def test_to_dataset_422_when_no_entries(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-08", json=make_check_sheet(entries=[]))
    resp = client.post("/project/proj-1/check-sheet/checksheet-001/to-dataset", json={"created_at": "2026-08-07T01:00:00"})
    assert resp.status_code == 422
    assert "no entries" in resp.json()["detail"]


# --- The zero-re-entry round trip: check sheet -> dataset -> Pareto -------


def test_to_dataset_then_pareto_names_the_right_top_category(client):
    _create_project(client)
    # 3 categories, 5 taps across 2 strata values (task brief's smoke shape,
    # exercised here at the engine level): Scratch x3, Crack x1, Short pour x1.
    entries = [
        {"entry_id": "e1", "category_id": "cat-scratch", "timestamp": "2026-08-07T08:00:00", "strata": {"shift": "morning"}, "note": ""},
        {"entry_id": "e2", "category_id": "cat-scratch", "timestamp": "2026-08-07T08:05:00", "strata": {"shift": "morning"}, "note": ""},
        {"entry_id": "e3", "category_id": "cat-scratch", "timestamp": "2026-08-07T08:10:00", "strata": {"shift": "morning"}, "note": ""},
        {"entry_id": "e4", "category_id": "cat-crack", "timestamp": "2026-08-07T13:00:00", "strata": {"shift": "afternoon"}, "note": ""},
        {"entry_id": "e5", "category_id": "cat-short-pour", "timestamp": "2026-08-07T13:05:00", "strata": {"shift": "afternoon"}, "note": ""},
    ]
    save = client.post("/project/proj-1/artifacts/T-08", json=make_check_sheet(entries=entries))
    assert save.status_code == 200, save.text

    to_dataset = client.post("/project/proj-1/check-sheet/checksheet-001/to-dataset", json={"created_at": "2026-08-07T14:00:00"})
    assert to_dataset.status_code == 200, to_dataset.text
    dataset = to_dataset.json()
    assert dataset["row_count"] == 5
    # Provenance chain: check-sheet artifact id -> dataset id, recorded on
    # the dataset's own persisted meta.json (datasets.py's DatasetMeta).
    assert dataset["source_artifact_id"] == "checksheet-001"
    assert dataset["source_tool_id"] == "T-08"
    assert len(dataset["sha256"]) == 64

    # Confirm it round-trips through GET like any other dataset -- the
    # desktop pulls rows the same way T-14 already does for an uploaded CSV.
    detail = client.get(f"/project/proj-1/datasets/{dataset['dataset_id']}")
    assert detail.status_code == 200, detail.text
    rows = detail.json()["rows"]
    assert len(rows) == 5
    categories = [r["category"] for r in rows]
    assert categories.count("Scratch") == 3

    pareto = client.post("/stats/pareto", json={"categories": categories})
    assert pareto.status_code == 200, pareto.text
    top = pareto.json()["value"]["categories"][0]
    assert top["category"] == "Scratch"
    assert top["count"] == 3


def test_to_dataset_provenance_absent_on_an_ordinary_upload(client):
    """source_artifact_id/source_tool_id are None for a plain CSV/XLSX
    upload -- only a tool's own to_dataset action sets them."""
    _create_project(client)
    import base64

    csv_b64 = base64.b64encode(b"name,wait_seconds\nregister,92\n").decode("ascii")
    save = client.post(
        "/project/proj-1/datasets", json={"source_filename": "a.csv", "content_base64": csv_b64, "created_at": "2026-08-07T01:00:00"}
    )
    assert save.status_code == 200, save.text
    assert save.json()["source_artifact_id"] is None
    assert save.json()["source_tool_id"] is None
