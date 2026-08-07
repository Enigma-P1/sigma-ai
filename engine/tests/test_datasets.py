"""Tests for datasets.py: CSV/XLSX round-trip, type inference, the import
quality scan on a dirty fixture, and DatasetStore save/list/load. Route-
level behavior (including the dataset -> BaselineResult provenance chain)
is tests/test_routes_datasets.py's job.
"""

import io

import openpyxl
import pytest

from sigma_engine.datasets import (
    DatasetStore,
    build_columns,
    build_preview,
    infer_column_type,
    parse_upload,
    scan_quality,
)
from sigma_engine.project_store import ProjectStore

CLEAN_CSV = b"name,wait_seconds\nregister,92\ngrinder,97\nregister,94\n"

# Deliberately dirty: a blank cell (wait_seconds row 2), a non-numeric
# value in the numeric column (row 3, "n/a"), and an exact duplicate of
# row 1 (row 4).
DIRTY_CSV = (
    b"name,wait_seconds\n"
    b"register,92\n"
    b"grinder,\n"
    b"restock,n/a\n"
    b"register,92\n"
)


def test_infer_column_type_numeric_vs_text():
    assert infer_column_type(["1", "2.5", "3"]) == "numeric"
    assert infer_column_type(["a", "b", "c"]) == "text"
    assert infer_column_type(["1", "abc", "3"]) == "text"  # one bad value taints the whole column
    assert infer_column_type(["", "", ""]) == "text"  # nothing to judge


def test_csv_round_trip_via_preview():
    preview = build_preview(CLEAN_CSV, "wait_times.csv", None)
    assert preview.row_count == 3
    by_name = {c.name: c for c in preview.columns}
    assert by_name["name"].inferred_type == "text"
    assert by_name["wait_seconds"].inferred_type == "numeric"
    assert preview.sample_rows[0] == {"name": "register", "wait_seconds": "92"}
    assert preview.quality.row_count == 3
    assert preview.quality.duplicate_row_count == 0


def _write_xlsx_bytes(rows: list[list[object]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_xlsx_round_trip_via_preview():
    content = _write_xlsx_bytes([
        ["name", "wait_seconds"],
        ["register", 92],
        ["grinder", 97.5],
        ["register", 94],
    ])
    preview = build_preview(content, "wait_times.xlsx", None)
    assert preview.row_count == 3
    by_name = {c.name: c for c in preview.columns}
    assert by_name["wait_seconds"].inferred_type == "numeric"
    # openpyxl hands back native ints/floats -- confirm they normalize to
    # plain strings a numeric-column float() parse still accepts.
    assert by_name["wait_seconds"].sample_values[0] == "92"
    assert by_name["wait_seconds"].sample_values[1] == "97.5"


def test_xlsx_skips_trailing_blank_rows():
    content = _write_xlsx_bytes([
        ["name", "wait_seconds"],
        ["register", 92],
        [None, None],
    ])
    preview = build_preview(content, "wait_times.xlsx", None)
    assert preview.row_count == 1


def test_unsupported_file_type_rejected():
    with pytest.raises(ValueError, match="unsupported file type"):
        parse_upload(b"whatever", "notes.txt")


def test_column_type_override_changes_the_effective_type_and_the_scan():
    # wait_seconds column has a "n/a" value -- inferred as text. Force it
    # numeric via override and the quality scan should now flag "n/a" as
    # the non-numeric-in-numeric-column finding it actually is.
    header, rows = parse_upload(DIRTY_CSV, "dirty.csv")
    columns = build_columns(header, rows, {"wait_seconds": "numeric"})
    by_name = {c.name: c for c in columns}
    assert by_name["wait_seconds"].inferred_type == "text"  # what the sniffer alone would say
    assert by_name["wait_seconds"].type == "numeric"  # the confirmed override
    scan = scan_quality(columns, rows)
    assert scan.non_numeric_in_numeric_columns["wait_seconds"] == 1


def test_quality_scan_finds_missing_non_numeric_and_duplicates_on_dirty_fixture():
    preview = build_preview(DIRTY_CSV, "dirty.csv", {"wait_seconds": "numeric"})
    q = preview.quality
    assert q.row_count == 4
    assert q.missing_values["wait_seconds"] == 1  # the blank grinder cell
    assert q.non_numeric_in_numeric_columns["wait_seconds"] == 1  # "n/a"
    assert q.duplicate_row_count == 1  # the second "register,92" row


def test_quality_scan_is_clean_on_the_clean_fixture():
    preview = build_preview(CLEAN_CSV, "wait_times.csv", None)
    q = preview.quality
    assert sum(q.missing_values.values()) == 0
    assert sum(q.non_numeric_in_numeric_columns.values()) == 0
    assert q.duplicate_row_count == 0


def test_preview_never_persists_anything(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    build_preview(CLEAN_CSV, "wait_times.csv", None)
    assert not (tmp_path / "proj-1" / "datasets").exists()


def test_save_dataset_writes_v1_csv_and_meta_json(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    meta = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")

    dataset_dir = tmp_path / "proj-1" / "datasets" / meta.dataset_id
    assert (dataset_dir / "v1.csv").exists()
    assert (dataset_dir / "meta.json").exists()
    assert meta.row_count == 3
    assert meta.source_filename == "wait_times.csv"
    assert len(meta.sha256) == 64  # hex sha256


def test_save_dataset_sha256_matches_the_actual_written_file(tmp_path):
    import hashlib

    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    meta = DatasetStore(store).save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    written = (tmp_path / "proj-1" / "datasets" / meta.dataset_id / "v1.csv").read_bytes()
    assert hashlib.sha256(written).hexdigest() == meta.sha256


def test_save_dataset_requires_an_existing_project(tmp_path):
    store = ProjectStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        DatasetStore(store).save_dataset("no-such-project", "x.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")


def test_list_and_load_round_trip(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    meta1 = ds.save_dataset("proj-1", "a.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    meta2 = ds.save_dataset("proj-1", "a.csv", CLEAN_CSV, None, "2026-08-07T02:00:00")

    listed = ds.list_datasets("proj-1")
    assert {m.dataset_id for m in listed} == {meta1.dataset_id, meta2.dataset_id}

    loaded = ds.load_meta("proj-1", meta1.dataset_id)
    assert loaded == meta1

    rows = ds.load_rows("proj-1", meta1.dataset_id)
    assert rows == [
        {"name": "register", "wait_seconds": "92"},
        {"name": "grinder", "wait_seconds": "97"},
        {"name": "register", "wait_seconds": "94"},
    ]


def test_load_numeric_column_happy_path(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    meta = DatasetStore(store).save_dataset("proj-1", "a.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    values, loaded_meta = DatasetStore(store).load_numeric_column("proj-1", meta.dataset_id, "wait_seconds")
    assert values == [92.0, 97.0, 94.0]
    assert loaded_meta.dataset_id == meta.dataset_id


def test_load_numeric_column_rejects_a_text_column(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    meta = DatasetStore(store).save_dataset("proj-1", "a.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    with pytest.raises(ValueError, match="not numeric"):
        DatasetStore(store).load_numeric_column("proj-1", meta.dataset_id, "name")


def test_load_numeric_column_refuses_to_silently_drop_bad_values(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    meta = DatasetStore(store).save_dataset(
        "proj-1", "dirty.csv", DIRTY_CSV, {"wait_seconds": "numeric"}, "2026-08-07T01:00:00"
    )
    with pytest.raises(ValueError, match="missing/non-numeric"):
        DatasetStore(store).load_numeric_column("proj-1", meta.dataset_id, "wait_seconds")
