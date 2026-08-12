"""Tests for datasets.py: CSV/XLSX round-trip, type inference, the import
quality scan on a dirty fixture, and DatasetStore save/list/load. Route-
level behavior (including the dataset -> BaselineResult provenance chain)
is tests/test_routes_datasets.py's job.
"""

import io

import openpyxl
import pytest

from sigma_engine.datasets import (
    AddRowDerivation,
    CellEdit,
    DatasetStore,
    DeleteRowsDerivation,
    DeriveColumnDerivation,
    EditCellsDerivation,
    RecodeDerivation,
    apply_derivation,
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

# The docs/uat vital-few bug this whole feature exists to fix: "JM" and
# "J Morales" are the same picker under two spellings. A separate fixture
# from CLEAN_CSV/DIRTY_CSV so a derivation test's row/column names are
# unambiguous in failure output.
PICKER_CSV = (
    b"picker,item_ordered,item_shipped\n"
    b"JM,Ketchup 4 oz,Ketchup 4 oz\n"
    b"J Morales,Ketchup 4 oz,Ketchup 6 oz\n"
    b"AB,Mozzarella sticks,Onion rings\n"
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


# --- Derivations: apply_derivation (the pure per-kind transform) ---


def test_apply_derivation_edit_cells_sets_specific_positions_and_leaves_the_input_alone():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    derivation = EditCellsDerivation(edits=[CellEdit(row_index=0, column="picker", value="J. Morales")])
    new_header, new_rows = apply_derivation(header, rows, derivation)
    assert new_header == header
    assert new_rows[0]["picker"] == "J. Morales"
    assert rows[0]["picker"] == "JM"  # the caller's own rows list is never mutated in place


def test_apply_derivation_add_row_pads_missing_columns_with_blank():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    new_header, new_rows = apply_derivation(header, rows, AddRowDerivation(values={"picker": "TK"}))
    assert new_header == header
    assert len(new_rows) == len(rows) + 1
    assert new_rows[-1] == {"picker": "TK", "item_ordered": "", "item_shipped": ""}


def test_apply_derivation_add_row_rejects_an_unknown_column():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    with pytest.raises(ValueError, match="not found"):
        apply_derivation(header, rows, AddRowDerivation(values={"picler": "TK"}))  # typo'd column name


def test_apply_derivation_delete_rows_drops_by_index():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    new_header, new_rows = apply_derivation(header, rows, DeleteRowsDerivation(row_indices=[1]))
    assert new_header == header
    assert [r["picker"] for r in new_rows] == ["JM", "AB"]


def test_apply_derivation_recode_merges_multiple_spellings_into_one_target():
    # The exact vital-few bug (docs/uat/PLAN.md 1.3): "JM" and "J Morales"
    # are one person under two spellings; both keys point at one target.
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    derivation = RecodeDerivation(column="picker", mapping={"JM": "J. Morales", "J Morales": "J. Morales"})
    _, new_rows = apply_derivation(header, rows, derivation)
    assert [r["picker"] for r in new_rows] == ["J. Morales", "J. Morales", "AB"]


def test_apply_derivation_recode_leaves_values_outside_the_mapping_untouched():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    _, new_rows = apply_derivation(header, rows, RecodeDerivation(column="picker", mapping={"JM": "J. Morales"}))
    assert [r["picker"] for r in new_rows] == ["J. Morales", "J Morales", "AB"]  # "J Morales"/"AB" not in the mapping


def test_apply_derivation_recode_rejects_a_blank_target():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    with pytest.raises(ValueError, match="would be empty"):
        apply_derivation(header, rows, RecodeDerivation(column="picker", mapping={"JM": "   "}))


def test_apply_derivation_derive_column_joins_with_the_default_separator():
    # "group by Item ordered AND Item shipped" (docs/uat/PLAN.md 1.4).
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    derivation = DeriveColumnDerivation(new_column_name="item_pair", left_column="item_ordered", right_column="item_shipped")
    new_header, new_rows = apply_derivation(header, rows, derivation)
    assert new_header == [*header, "item_pair"]
    assert new_rows[1]["item_pair"] == "Ketchup 4 oz → Ketchup 6 oz"
    assert new_rows[0]["item_pair"] == "Ketchup 4 oz → Ketchup 4 oz"


def test_apply_derivation_derive_column_respects_a_custom_separator():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    derivation = DeriveColumnDerivation(
        new_column_name="item_pair", left_column="item_ordered", right_column="item_shipped", separator=" / "
    )
    _, new_rows = apply_derivation(header, rows, derivation)
    assert new_rows[1]["item_pair"] == "Ketchup 4 oz / Ketchup 6 oz"


def test_apply_derivation_derive_column_rejects_a_name_that_already_exists():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    derivation = DeriveColumnDerivation(new_column_name="picker", left_column="item_ordered", right_column="item_shipped")
    with pytest.raises(ValueError, match="already exists"):
        apply_derivation(header, rows, derivation)


def test_apply_derivation_rejects_an_out_of_range_row_index():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    with pytest.raises(ValueError, match="out of range"):
        apply_derivation(header, rows, EditCellsDerivation(edits=[CellEdit(row_index=99, column="picker", value="x")]))


def test_apply_derivation_rejects_a_negative_row_index():
    header, rows = parse_upload(PICKER_CSV, "picking.csv")
    with pytest.raises(ValueError, match="out of range"):
        apply_derivation(header, rows, DeleteRowsDerivation(row_indices=[-1]))


# --- Derivations: DatasetStore.derive_dataset (new dataset, parent untouched) ---


def test_derive_dataset_recode_produces_a_new_dataset_and_leaves_the_parent_byte_identical(tmp_path):
    import hashlib

    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "picking.csv", PICKER_CSV, None, "2026-08-07T01:00:00")

    derivation = RecodeDerivation(column="picker", mapping={"JM": "J. Morales", "J Morales": "J. Morales"})
    child = ds.derive_dataset("proj-1", parent.dataset_id, derivation, "2026-08-07T02:00:00")

    assert child.dataset_id != parent.dataset_id
    assert child.derived_from_dataset_id == parent.dataset_id
    assert child.derivation == derivation
    assert child.row_count == parent.row_count
    assert [r["picker"] for r in ds.load_rows("proj-1", child.dataset_id)] == ["J. Morales", "J. Morales", "AB"]

    # The parent's v1.csv was never opened for writing -- re-hash the file
    # on disk independently rather than trusting the in-memory object.
    parent_csv_on_disk = (tmp_path / "proj-1" / "datasets" / parent.dataset_id / "v1.csv").read_bytes()
    assert hashlib.sha256(parent_csv_on_disk).hexdigest() == parent.sha256

    # ...but re-loading its meta.json now shows the supersede pointer.
    reloaded_parent = ds.load_meta("proj-1", parent.dataset_id)
    assert reloaded_parent.superseded_by_dataset_id == child.dataset_id
    assert reloaded_parent.sha256 == parent.sha256
    assert reloaded_parent.derivation is None  # the PARENT itself was never derived from anything


def test_derive_dataset_child_sha256_matches_a_rehash_of_its_own_v1_csv(tmp_path):
    import hashlib

    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "picking.csv", PICKER_CSV, None, "2026-08-07T01:00:00")
    child = ds.derive_dataset("proj-1", parent.dataset_id, DeleteRowsDerivation(row_indices=[0]), "2026-08-07T02:00:00")

    child_csv_on_disk = (tmp_path / "proj-1" / "datasets" / child.dataset_id / "v1.csv").read_bytes()
    assert hashlib.sha256(child_csv_on_disk).hexdigest() == child.sha256
    assert child.row_count == 2


def test_derive_dataset_carries_forward_an_earlier_type_override(tmp_path):
    # "007"/"010" parse fine as float() -- infer_column_type alone would
    # call this column numeric -- but a caller earlier confirmed it's
    # really text (a SKU, not a quantity). A derivation must not silently
    # re-guess that decision away.
    sku_csv = b"sku,qty\n007,3\n010,5\n"
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "skus.csv", sku_csv, {"sku": "text"}, "2026-08-07T01:00:00")
    assert {c.name: c.type for c in parent.columns}["sku"] == "text"  # sanity: the override took on save

    child = ds.derive_dataset(
        "proj-1", parent.dataset_id, AddRowDerivation(values={"sku": "099", "qty": "1"}), "2026-08-07T02:00:00"
    )
    by_name = {c.name: c for c in child.columns}
    assert by_name["sku"].inferred_type == "numeric"  # what the sniffer alone would say on the new rows
    assert by_name["sku"].type == "text"  # the parent's confirmed override, carried forward


def test_derive_dataset_derive_column_is_always_text_even_when_it_looks_numeric(tmp_path):
    # separator="" joining two numeric-looking columns could otherwise
    # infer as numeric by accident -- a newly derived column is always
    # text regardless (module docstring / brief), so this must be forced,
    # not left to infer_column_type.
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "nums.csv", b"a,b\n1,2\n3,4\n", None, "2026-08-07T01:00:00")

    child = ds.derive_dataset(
        "proj-1", parent.dataset_id,
        DeriveColumnDerivation(new_column_name="ab", left_column="a", right_column="b", separator=""),
        "2026-08-07T02:00:00",
    )
    rows = ds.load_rows("proj-1", child.dataset_id)
    assert rows[0]["ab"] == "12"  # would infer numeric on its own -- confirms the trap is real
    by_name = {c.name: c for c in child.columns}
    assert by_name["ab"].inferred_type == "numeric"
    assert by_name["ab"].type == "text"  # forced


def test_derive_dataset_rescans_quality_on_the_new_rows(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    assert parent.quality.duplicate_row_count == 0

    # Appended row exactly duplicates row 1 -- the re-run scan should catch
    # it even though the parent's own scan (over the parent's rows) never saw it.
    child = ds.derive_dataset(
        "proj-1", parent.dataset_id,
        AddRowDerivation(values={"name": "register", "wait_seconds": "92"}),
        "2026-08-07T02:00:00",
    )
    assert child.quality.duplicate_row_count == 1


def test_derive_dataset_422_out_of_range_row_index(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    with pytest.raises(ValueError, match="out of range"):
        ds.derive_dataset("proj-1", parent.dataset_id, DeleteRowsDerivation(row_indices=[99]), "2026-08-07T02:00:00")


def test_derive_dataset_422_unknown_column(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    with pytest.raises(ValueError, match="not found"):
        ds.derive_dataset(
            "proj-1", parent.dataset_id, RecodeDerivation(column="no_such_column", mapping={"a": "b"}), "2026-08-07T02:00:00"
        )


def test_derive_dataset_422_recode_target_would_be_empty(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    with pytest.raises(ValueError, match="would be empty"):
        ds.derive_dataset(
            "proj-1", parent.dataset_id, RecodeDerivation(column="name", mapping={"register": ""}), "2026-08-07T02:00:00"
        )


def test_derive_dataset_422_derived_column_name_already_exists(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    ds = DatasetStore(store)
    parent = ds.save_dataset("proj-1", "wait_times.csv", CLEAN_CSV, None, "2026-08-07T01:00:00")
    with pytest.raises(ValueError, match="already exists"):
        ds.derive_dataset(
            "proj-1", parent.dataset_id,
            DeriveColumnDerivation(new_column_name="name", left_column="name", right_column="wait_seconds"),
            "2026-08-07T02:00:00",
        )


def test_derive_dataset_requires_an_existing_project(tmp_path):
    store = ProjectStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        DatasetStore(store).derive_dataset(
            "no-such-project", "no-such-dataset", DeleteRowsDerivation(row_indices=[0]), "2026-08-07T01:00:00"
        )


def test_derive_dataset_requires_an_existing_dataset(tmp_path):
    store = ProjectStore(tmp_path)
    store.create_project("proj-1", "Coffee Bar", "2026-08-07T00:00:00")
    with pytest.raises(FileNotFoundError):
        DatasetStore(store).derive_dataset(
            "proj-1", "no-such-dataset", DeleteRowsDerivation(row_indices=[0]), "2026-08-07T01:00:00"
        )
