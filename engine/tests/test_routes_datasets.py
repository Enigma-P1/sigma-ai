"""Route tests for /project/{id}/datasets* and the dataset-sourced half of
POST /stats/baseline -- including the dataset -> BaselineResult provenance
chain (R-MEA-06: "provenance hash links dataset -> any BaselineResult").
"""

import base64

import pytest
from fastapi.testclient import TestClient

from sigma_engine.main import app

CLEAN_CSV = b"name,wait_seconds\nregister,92\ngrinder,97\nregister,94\n"
B64_CLEAN_CSV = base64.b64encode(CLEAN_CSV).decode("ascii")

# The docs/uat vital-few bug this feature exists to fix: "JM" and
# "J Morales" are the same picker under two spellings.
PICKER_CSV = (
    b"picker,item_ordered,item_shipped\n"
    b"JM,Ketchup 4 oz,Ketchup 4 oz\n"
    b"J Morales,Ketchup 4 oz,Ketchup 6 oz\n"
    b"AB,Mozzarella sticks,Onion rings\n"
)
B64_PICKER_CSV = base64.b64encode(PICKER_CSV).decode("ascii")

# n=20, alternating above/below its own mean, no run of 8, no point beyond
# 3 sigma -- a genuinely stable I-MR read (same construction discipline as
# test_stats_baseline.py's own fixtures).
STABLE_WAITS = [95, 91, 98, 93, 97, 92, 99, 94, 96, 90, 98, 93, 95, 91, 99, 94, 97, 92, 96, 90]
STABLE_CSV = ("wait_seconds\n" + "\n".join(str(v) for v in STABLE_WAITS) + "\n").encode("ascii")
B64_STABLE_CSV = base64.b64encode(STABLE_CSV).decode("ascii")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_preview_route_returns_columns_and_quality_without_saving(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/datasets/preview",
        json={"source_filename": "wait_times.csv", "content_base64": B64_CLEAN_CSV},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["row_count"] == 3
    by_name = {c["name"]: c for c in body["columns"]}
    assert by_name["wait_seconds"]["inferred_type"] == "numeric"
    assert body["quality"]["duplicate_row_count"] == 0

    listed = client.get("/project/proj-1/datasets").json()
    assert listed == []  # preview never persists


def test_preview_route_respects_column_type_override(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/datasets/preview",
        json={"source_filename": "wait_times.csv", "content_base64": B64_CLEAN_CSV, "column_types": {"name": "numeric"}},
    )
    assert resp.status_code == 200, resp.text
    by_name = {c["name"]: c for c in resp.json()["columns"]}
    assert by_name["name"]["inferred_type"] == "text"
    assert by_name["name"]["type"] == "numeric"
    # scan now reflects the confirmed override, not just the sniffer
    assert resp.json()["quality"]["non_numeric_in_numeric_columns"]["name"] == 3


def test_save_route_persists_and_get_route_returns_meta_and_rows(client):
    _create_project(client)
    save = client.post(
        "/project/proj-1/datasets",
        json={"source_filename": "wait_times.csv", "content_base64": B64_CLEAN_CSV, "created_at": "2026-08-07T01:00:00"},
    )
    assert save.status_code == 200, save.text
    meta = save.json()
    assert meta["row_count"] == 3
    assert len(meta["sha256"]) == 64

    detail = client.get(f"/project/proj-1/datasets/{meta['dataset_id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["meta"] == meta
    assert body["rows"] == [
        {"name": "register", "wait_seconds": "92"},
        {"name": "grinder", "wait_seconds": "97"},
        {"name": "register", "wait_seconds": "94"},
    ]

    listed = client.get("/project/proj-1/datasets").json()
    assert [d["dataset_id"] for d in listed] == [meta["dataset_id"]]


def test_save_route_404_on_missing_project(client):
    resp = client.post(
        "/project/no-such-project/datasets",
        json={"source_filename": "a.csv", "content_base64": B64_CLEAN_CSV, "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 404


def test_get_route_404_for_missing_dataset(client):
    _create_project(client)
    assert client.get("/project/proj-1/datasets/no-such-dataset").status_code == 404


def test_invalid_base64_returns_422(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/datasets/preview",
        json={"source_filename": "a.csv", "content_base64": "not-valid-base64!!"},
    )
    assert resp.status_code == 422


# --- POST .../datasets/{dataset_id}/derive -- the vital-few fix (docs/uat) ---


def _save_picker_dataset(client, project_id="proj-1"):
    save = client.post(
        f"/project/{project_id}/datasets",
        json={"source_filename": "picking.csv", "content_base64": B64_PICKER_CSV, "created_at": "2026-08-07T01:00:00"},
    )
    assert save.status_code == 200, save.text
    return save.json()


def test_derive_route_recode_merges_spellings_and_supersedes_the_parent(client):
    _create_project(client)
    parent = _save_picker_dataset(client)

    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={
            "derivation": {"kind": "recode", "column": "picker", "mapping": {"JM": "J. Morales", "J Morales": "J. Morales"}},
            "created_at": "2026-08-07T02:00:00",
        },
    )
    assert resp.status_code == 200, resp.text
    child = resp.json()
    assert child["dataset_id"] != parent["dataset_id"]
    assert child["derived_from_dataset_id"] == parent["dataset_id"]
    assert child["derivation"] == {
        "kind": "recode", "column": "picker", "mapping": {"JM": "J. Morales", "J Morales": "J. Morales"},
    }

    detail = client.get(f"/project/proj-1/datasets/{child['dataset_id']}").json()
    assert [r["picker"] for r in detail["rows"]] == ["J. Morales", "J. Morales", "AB"]

    reloaded_parent = client.get(f"/project/proj-1/datasets/{parent['dataset_id']}").json()["meta"]
    assert reloaded_parent["superseded_by_dataset_id"] == child["dataset_id"]
    assert reloaded_parent["sha256"] == parent["sha256"]  # the parent's bytes never changed

    listed = client.get("/project/proj-1/datasets").json()
    assert {d["dataset_id"] for d in listed} == {parent["dataset_id"], child["dataset_id"]}


def test_derive_route_edit_cells(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={
            "derivation": {"kind": "edit_cells", "edits": [{"row_index": 0, "column": "picker", "value": "J. Morales"}]},
            "created_at": "2026-08-07T02:00:00",
        },
    )
    assert resp.status_code == 200, resp.text
    rows = client.get(f"/project/proj-1/datasets/{resp.json()['dataset_id']}").json()["rows"]
    assert rows[0]["picker"] == "J. Morales"


def test_derive_route_add_row(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={"derivation": {"kind": "add_row", "values": {"picker": "TK"}}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 200, resp.text
    child = resp.json()
    assert child["row_count"] == 4
    rows = client.get(f"/project/proj-1/datasets/{child['dataset_id']}").json()["rows"]
    assert rows[-1] == {"picker": "TK", "item_ordered": "", "item_shipped": ""}


def test_derive_route_delete_rows(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={"derivation": {"kind": "delete_rows", "row_indices": [1]}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 200, resp.text
    child = resp.json()
    assert child["row_count"] == 2
    rows = client.get(f"/project/proj-1/datasets/{child['dataset_id']}").json()["rows"]
    assert [r["picker"] for r in rows] == ["JM", "AB"]


def test_derive_route_derive_column_default_separator(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={
            "derivation": {
                "kind": "derive_column", "new_column_name": "item_pair",
                "left_column": "item_ordered", "right_column": "item_shipped",
            },
            "created_at": "2026-08-07T02:00:00",
        },
    )
    assert resp.status_code == 200, resp.text
    child = resp.json()
    by_name = {c["name"]: c for c in child["columns"]}
    assert by_name["item_pair"]["type"] == "text"
    rows = client.get(f"/project/proj-1/datasets/{child['dataset_id']}").json()["rows"]
    assert rows[1]["item_pair"] == "Ketchup 4 oz → Ketchup 6 oz"


def test_derive_route_404_on_missing_project(client):
    resp = client.post(
        "/project/no-such-project/datasets/whatever/derive",
        json={"derivation": {"kind": "delete_rows", "row_indices": [0]}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 404


def test_derive_route_404_on_missing_dataset(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/datasets/no-such-dataset/derive",
        json={"derivation": {"kind": "delete_rows", "row_indices": [0]}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 404


def test_derive_route_422_out_of_range_row_index(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={"derivation": {"kind": "delete_rows", "row_indices": [99]}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 422


def test_derive_route_422_unknown_column(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={
            "derivation": {"kind": "recode", "column": "no_such_column", "mapping": {"a": "b"}},
            "created_at": "2026-08-07T02:00:00",
        },
    )
    assert resp.status_code == 422


def test_derive_route_422_recode_target_would_be_empty(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={"derivation": {"kind": "recode", "column": "picker", "mapping": {"JM": ""}}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 422


def test_derive_route_422_derived_column_name_already_exists(client):
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={
            "derivation": {
                "kind": "derive_column", "new_column_name": "picker",
                "left_column": "item_ordered", "right_column": "item_shipped",
            },
            "created_at": "2026-08-07T02:00:00",
        },
    )
    assert resp.status_code == 422


def test_derive_route_422_on_unrecognized_derivation_kind(client):
    # Pydantic's discriminated union rejects an unknown "kind" tag before
    # DatasetStore.derive_dataset is ever called -- FastAPI's own request-
    # validation 422, not the ValueError->422 path the other cases above go through.
    _create_project(client)
    parent = _save_picker_dataset(client)
    resp = client.post(
        f"/project/proj-1/datasets/{parent['dataset_id']}/derive",
        json={"derivation": {"kind": "not_a_real_kind"}, "created_at": "2026-08-07T02:00:00"},
    )
    assert resp.status_code == 422


# --- Dataset-sourced /stats/baseline, and the dataset -> BaselineResult provenance chain ---


def test_baseline_from_dataset_matches_the_equivalent_raw_array(client):
    _create_project(client)
    save = client.post(
        "/project/proj-1/datasets",
        json={"source_filename": "waits.csv", "content_base64": B64_STABLE_CSV, "created_at": "2026-08-07T01:00:00"},
    )
    dataset_id = save.json()["dataset_id"]
    dataset_sha256 = save.json()["sha256"]

    from_dataset = client.post(
        "/stats/baseline",
        json={
            "project_id": "proj-1", "dataset_id": dataset_id, "column": "wait_seconds",
            "usl": 130, "lsl": 60, "operational_definition_ok": True,
        },
    )
    assert from_dataset.status_code == 200, from_dataset.text
    from_raw = client.post(
        "/stats/baseline",
        json={"data": STABLE_WAITS, "usl": 130, "lsl": 60, "operational_definition_ok": True},
    )
    assert from_raw.status_code == 200, from_raw.text

    ds_body, raw_body = from_dataset.json(), from_raw.json()
    # Same input data -> identical computed results (same provenance
    # input_hash on every nested Computed[T], not just the top-level n).
    assert ds_body["stable"] == raw_body["stable"] is True
    assert ds_body["descriptive"] == raw_body["descriptive"]
    assert ds_body["capability"] == raw_body["capability"]

    # The hash chain itself: what the route echoes back matches what the
    # dataset save actually recorded -- independently re-verifiable.
    assert ds_body["dataset_provenance"] == {
        "dataset_id": dataset_id, "dataset_sha256": dataset_sha256, "column": "wait_seconds", "row_count_used": 20,
    }
    assert "dataset_provenance" not in raw_body


def test_baseline_rejects_both_data_and_dataset_id(client):
    resp = client.post(
        "/stats/baseline",
        json={"data": [1.0, 2.0], "project_id": "proj-1", "dataset_id": "x", "column": "y", "operational_definition_ok": True},
    )
    assert resp.status_code == 422


def test_baseline_rejects_neither_data_nor_dataset_id(client):
    resp = client.post("/stats/baseline", json={"operational_definition_ok": True})
    assert resp.status_code == 422


def test_baseline_from_dataset_404_when_dataset_missing(client):
    _create_project(client)
    resp = client.post(
        "/stats/baseline",
        json={"project_id": "proj-1", "dataset_id": "no-such-dataset", "column": "wait_seconds", "operational_definition_ok": True},
    )
    assert resp.status_code == 404


def test_baseline_from_dataset_422_on_non_numeric_column(client):
    _create_project(client)
    save = client.post(
        "/project/proj-1/datasets",
        json={"source_filename": "waits.csv", "content_base64": B64_CLEAN_CSV, "created_at": "2026-08-07T01:00:00"},
    )
    dataset_id = save.json()["dataset_id"]
    resp = client.post(
        "/stats/baseline",
        json={"project_id": "proj-1", "dataset_id": dataset_id, "column": "name", "operational_definition_ok": True},
    )
    assert resp.status_code == 422
    assert "not numeric" in resp.json()["detail"]
