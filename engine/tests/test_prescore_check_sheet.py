from factories import make_check_sheet, make_check_sheet_entries
from sigma_engine.artifacts.check_sheet import CheckSheetArtifact
from sigma_engine.prescore.check_sheet import run_check_sheet_prescore


def test_clean_check_sheet_passes_every_check():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet())
    results = run_check_sheet_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["strata_declared"].status == "pass"
    assert by_id["entries_present"].status == "pass"
    assert by_id["entries_carry_full_strata"].status == "pass"
    # cat-short-pour was declared but never tallied in the default fixture.
    assert by_id["category_coverage"].status == "flag"
    assert "Short pour" in by_id["category_coverage"].detail


def test_no_strata_declared_flags():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(strata_fields=[], entries=[
        {**e, "strata": {}} for e in make_check_sheet_entries()
    ]))
    results = run_check_sheet_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["strata_declared"].status == "flag"
    assert "entries_carry_full_strata" not in by_id  # nothing declared, nothing to check


def test_no_entries_flags_entries_present_and_skips_coverage():
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=[]))
    results = run_check_sheet_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["entries_present"].status == "flag"
    assert "category_coverage" not in by_id  # nothing tallied yet -- no coverage claim to make


def test_incomplete_strata_on_a_row_flags():
    entries = make_check_sheet_entries()
    entries[0]["strata"] = {}  # missing the declared "shift" value
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
    results = run_check_sheet_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["entries_carry_full_strata"].status == "flag"
    assert "e1" in by_id["entries_carry_full_strata"].detail


def test_full_category_coverage_passes():
    entries = make_check_sheet_entries()
    entries.append({"entry_id": "e4", "category_id": "cat-short-pour", "timestamp": "2026-08-07T09:00:00", "strata": {"shift": "morning"}, "note": ""})
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
    results = run_check_sheet_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["category_coverage"].status == "pass"


def test_a_deleted_entry_does_not_count_toward_category_coverage():
    # cat-crack's only tally (e3) gets soft-deleted -- coverage must go
    # back to flagging cat-crack as untouched, the same as if it had never
    # been tapped (rubric R-MEA-04 generalized to T-08: a deleted row
    # shouldn't be able to satisfy a "this category was tallied" check).
    entries = make_check_sheet_entries()
    entries[2] = {**entries[2], "deleted": {"reason": "wrong category tapped", "at": "2026-08-07T13:01:00"}}
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
    by_id = {r.check_id: r for r in run_check_sheet_prescore(artifact)}
    assert by_id["category_coverage"].status == "flag"
    assert "Crack" in by_id["category_coverage"].detail


def test_all_entries_deleted_reads_as_no_entries_present():
    entries = [{**e, "deleted": {"reason": "re-collected", "at": "2026-08-07T13:01:00"}} for e in make_check_sheet_entries()]
    artifact = CheckSheetArtifact.model_validate(make_check_sheet(entries=entries))
    by_id = {r.check_id: r for r in run_check_sheet_prescore(artifact)}
    assert by_id["entries_present"].status == "flag"
    assert "category_coverage" not in by_id
