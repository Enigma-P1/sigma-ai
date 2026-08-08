"""Schema + export tests for T-08 CheckSheetArtifact."""

import pytest
from pydantic import ValidationError

from factories import make_check_sheet, make_check_sheet_categories, make_check_sheet_entries
from sigma_engine.artifacts.check_sheet import CheckSheetArtifact, check_sheet_export_csv_bytes, check_sheet_export_rows


def test_accepts_a_complete_check_sheet():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet())
    assert len(artifact.categories) == 3
    assert len(artifact.strata_fields) == 1
    assert len(artifact.entries) == 3


def test_categories_required_but_entries_may_start_empty():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=[]))
    assert artifact.entries == []


def test_rejects_empty_categories():
    with pytest.raises(ValidationError):
        CheckSheetArtifact.model_validate(make_check_sheet(categories=[]))


def test_rejects_duplicate_category_ids():
    cats = make_check_sheet_categories()
    cats.append({"category_id": "cat-scratch", "label": "Duplicate"})
    with pytest.raises(ValidationError, match="category_id"):
        CheckSheetArtifact.model_validate(make_check_sheet(categories=cats))


def test_rejects_duplicate_category_labels():
    cats = make_check_sheet_categories()
    cats.append({"category_id": "cat-other", "label": "Scratch"})
    with pytest.raises(ValidationError, match="labels must be unique"):
        CheckSheetArtifact.model_validate(make_check_sheet(categories=cats))


def test_rejects_entry_referencing_unknown_category():
    entries = make_check_sheet_entries()
    entries[0]["category_id"] = "no-such-category"
    with pytest.raises(ValidationError, match="unknown category_id"):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))


def test_rejects_entry_with_undeclared_strata_key():
    entries = make_check_sheet_entries()
    entries[0]["strata"] = {"station": "line-2"}  # "station" was never declared
    with pytest.raises(ValidationError, match="undeclared strata key"):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))


def test_rejects_duplicate_entry_ids():
    entries = make_check_sheet_entries()
    entries.append({**entries[0], "entry_id": "e1"})
    with pytest.raises(ValidationError, match="entry_id"):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))


def test_rejects_invalid_timestamp():
    entries = make_check_sheet_entries()
    entries[0]["timestamp"] = "not-a-date"
    with pytest.raises(ValidationError, match="ISO8601"):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))


def test_round_trip_via_model_dump():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet())
    round_tripped = CheckSheetArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


# --- Export (to_dataset's pure half) ---


def test_export_rows_shape_and_label_mapping():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet())
    header, rows = check_sheet_export_rows(artifact)
    assert header == ["category", "timestamp", "shift", "note"]
    assert len(rows) == 3
    # Sorted by timestamp: e1 (08:00), e2 (08:05), e3 (13:00).
    assert rows[0] == {"category": "Scratch", "timestamp": "2026-08-07T08:00:00", "shift": "morning", "note": ""}
    assert rows[2] == {"category": "Crack", "timestamp": "2026-08-07T13:00:00", "shift": "afternoon", "note": "chipped on drop"}


def test_export_refuses_with_no_entries():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=[]))
    with pytest.raises(ValueError, match="no entries"):
        check_sheet_export_rows(artifact)


def test_export_csv_bytes_round_trip_through_the_stdlib_csv_reader():
    import csv
    import io

    artifact = CheckSheetArtifact.model_validate(make_check_sheet())
    csv_bytes = check_sheet_export_csv_bytes(artifact)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["category"] == "Scratch"
    assert rows[0]["shift"] == "morning"


# --- Soft delete (CheckSheetEntry.deleted, rubric R-MEA-04 generalized to T-08) ---


def test_deleted_entry_excluded_from_export_but_stays_on_the_artifact():
    entries = make_check_sheet_entries()
    entries[1] = {**entries[1], "deleted": {"reason": "double-tapped by accident", "at": "2026-08-07T08:06:00"}}
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))

    _, rows = check_sheet_export_rows(artifact)
    assert len(rows) == 2
    assert all(r["timestamp"] != "2026-08-07T08:05:00" for r in rows)

    assert len(artifact.entries) == 3  # soft delete: still on the artifact
    deleted_entry = next(e for e in artifact.entries if e.entry_id == "e2")
    assert deleted_entry.deleted is not None
    assert deleted_entry.deleted.reason == "double-tapped by accident"


def test_export_refuses_when_every_entry_is_deleted():
    entries = [{**e, "deleted": {"reason": "re-tallied by hand", "at": "2026-08-07T09:00:00"}} for e in make_check_sheet_entries()]
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
    with pytest.raises(ValueError, match="no entries"):
        check_sheet_export_rows(artifact)


def test_deletion_without_a_reason_is_rejected():
    entries = make_check_sheet_entries()
    entries[1] = {**entries[1], "deleted": {"reason": "", "at": "2026-08-07T08:06:00"}}
    with pytest.raises(ValidationError):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))


def test_deletion_with_an_invalid_timestamp_is_rejected():
    entries = make_check_sheet_entries()
    entries[1] = {**entries[1], "deleted": {"reason": "double-tapped", "at": "not-a-date"}}
    with pytest.raises(ValidationError, match="ISO8601"):
        CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
