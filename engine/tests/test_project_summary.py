"""Tests for the one-page Project Summary (export/reports/summary.py) and
its route (POST /project/{id}/summary/pdf, routes/export.py) --
docs/uat/PLAN.md 2.4: "the artifact both testers came for and neither
got." Two properties get checked everywhere here: every number traces to
a saved artifact or a Computed[...] it already carries (never
re-derived), and a missing artifact prints an honest gap in its own
section rather than the section silently disappearing.

Story-content assertions run against the built flowables directly
(_flatten, matching test_report_group_c.py's own convention) rather than
against PDF bytes: report_pdf.render() compresses its page streams
(pageCompression=1), so text search only works pre-render. Route tests
below stick to what compressed bytes CAN prove -- status, content-type,
page count, filename -- the same split test_routes_export.py and
test_export_charter_pdf.py already draw between route and story tests.
"""

from __future__ import annotations

import base64
import re

import pytest
from fastapi.testclient import TestClient

from factories import make_charter, make_check_sheet, make_fishbone, make_solution_matrix
from sigma_engine.artifacts.charter import CharterArtifact
from sigma_engine.artifacts.check_sheet import CheckSheetArtifact
from sigma_engine.artifacts.fishbone import FishboneArtifact
from sigma_engine.artifacts.solution_matrix import SolutionMatrixArtifact
from sigma_engine.datasets import ColumnInfo, DatasetMeta, QualityScanResult
from sigma_engine.export import pdf_theme, report_pdf
from sigma_engine.export.report_pdf import content_width_for
from sigma_engine.export.reports import check_sheet as check_sheet_report_mod
from sigma_engine.export.reports import summary
from sigma_engine.stats.pareto import compute_pareto

CONTENT_WIDTH = content_width_for(pdf_theme.PAGE_SIZE)


def _pdf_page_count(pdf_bytes: bytes) -> int:
    """Count real page objects (/Type /Page). Excludes /Type /Pages (the
    page-tree root) -- same technique as test_export_charter_pdf.py's
    _pdf_page_count, verified there against reportlab's own output."""
    return len(re.findall(rb"/Type\s*/Page(?!s)\b", pdf_bytes))


def _flatten(flowables) -> str:
    out: list[str] = []
    for flowable in flowables:
        if hasattr(flowable, "getPlainText"):
            out.append(flowable.getPlainText())
        elif hasattr(flowable, "_cellvalues"):
            for row in flowable._cellvalues:
                for cell in row:
                    out.append(cell if isinstance(cell, str) else _flatten([cell]))
        elif hasattr(flowable, "_content"):
            out.append(_flatten(flowable._content))
    return " ".join(str(o) for o in out)


def _story(**overrides) -> list:
    base = dict(
        project_name="P", charter=None, fishbone=None, solution_matrix=None, check_sheet=None,
        datasets=[], provenance_rows=[("Engine version", "0.1.0")], exported_at="2026-08-12 00:00 UTC",
        content_width=CONTENT_WIDTH,
    )
    base.update(overrides)
    return summary.build_story(**base)


def _text(**overrides) -> str:
    return _flatten(_story(**overrides))


def _dataset_meta(**overrides) -> DatasetMeta:
    base = dict(
        dataset_id="ds-1", project_id="proj-1", source_filename="errors.csv",
        created_at="2026-08-07T01:00:00", sha256="a" * 64, row_count=342,
        columns=[ColumnInfo(name="aisle", inferred_type="numeric", type="numeric", sample_values=["5", "12"])],
        quality=QualityScanResult(
            row_count=342, missing_values={"aisle": 0}, non_numeric_in_numeric_columns={"aisle": 0},
            duplicate_row_count=0,
        ),
    )
    base.update(overrides)
    return DatasetMeta(**base)


# ------------------------------------------------------- gaps, never dropped


def test_no_charter_names_the_gap_where_the_problem_and_baseline_go():
    text = _text()
    assert "PROBLEM, GOAL & BASELINE" in text
    assert "No charter saved yet." in text


def test_charter_with_no_baseline_value_names_that_specific_gap():
    body = make_charter()
    body["goal"] = {**body["goal"], "baseline_value": None}
    charter = CharterArtifact.model_validate(body)

    text = _text(charter=charter)
    assert "No charter saved yet." not in text
    assert "No baseline number recorded on the charter yet." in text


def test_no_dataset_names_the_gap():
    text = _text()
    assert "DATA IMPORTED" in text
    assert "No dataset imported yet." in text


def test_no_check_sheet_names_the_gap():
    text = _text()
    assert "TOP CATEGORIES" in text
    assert "No categorized tally saved yet." in text


def test_check_sheet_with_nothing_tallied_is_a_different_honest_gap():
    cs = CheckSheetArtifact.model_validate(make_check_sheet(entries=[]))
    text = _text(check_sheet=cs)
    assert "No categorized tally saved yet." not in text
    assert "nothing has been tallied yet" in text


def test_no_fishbone_names_the_gap():
    text = _text()
    assert "FISHBONE CAUSES" in text
    assert "No fishbone saved yet." in text


def test_fishbone_with_causes_but_none_verified_states_the_real_count():
    fb = FishboneArtifact.model_validate(
        make_fishbone(causes=[{"cause_id": "c1", "branch": "machine", "text": "drifts mid-peak", "status": "candidate"}])
    )
    text = _text(fishbone=fb)
    assert "No fishbone saved yet." not in text
    assert "1 cause on the fishbone; 0 verified." in text


def test_dataset_text_pure_function_returns_none_with_no_datasets():
    assert summary.dataset_text([]) is None


# ----------------------------------------------------------- quote, not derive


def test_problem_and_goal_quotes_the_charter_verbatim():
    charter = CharterArtifact.model_validate(make_charter())
    text = _text(charter=charter)
    assert "Line 2 scrap rate" in text
    assert "Plant A" in text
    assert "Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026." in text


def test_baseline_quotes_the_charters_own_numbers():
    charter = CharterArtifact.model_validate(make_charter())
    text = _text(charter=charter)
    assert "6.2% → 3%" in text


def test_dataset_section_quotes_row_count_and_filename():
    text = _text(datasets=[_dataset_meta(row_count=342, source_filename="errors.csv")])
    assert "342 rows imported from errors.csv" in text


def test_two_datasets_names_the_most_recent_and_the_total_count():
    older = _dataset_meta(dataset_id="ds-1", created_at="2026-08-01T00:00:00", row_count=100, source_filename="first.csv")
    newer = _dataset_meta(dataset_id="ds-2", created_at="2026-08-07T00:00:00", row_count=342, source_filename="errors.csv")
    text = _text(datasets=[older, newer])
    assert "342 rows imported from errors.csv" in text
    assert "most recent of 2 datasets" in text
    assert "first.csv" not in text  # the headline names the current one, not the whole history


def test_top_categories_matches_the_check_sheets_own_tally_exactly():
    """The 'quote, never re-derive' rule, checked structurally: whatever
    check_sheet.py's own tally() returns is what this page shows -- never
    a second, independently-sorted count."""
    cs = CheckSheetArtifact.model_validate(make_check_sheet())
    text = _text(check_sheet=cs)
    for label, count in check_sheet_report_mod.tally(cs):
        if count > 0:
            assert label in text
            assert str(count) in text


def test_more_than_four_categories_is_capped_and_points_at_the_full_report():
    categories = [{"category_id": f"c{i}", "label": f"Category {i}"} for i in range(8)]
    entries = [
        {"entry_id": f"e{i}-{j}", "category_id": f"c{i}", "timestamp": "2026-08-07T08:00:00", "note": ""}
        for i in range(8)
        for j in range(i + 1)  # distinct, ascending counts -> an unambiguous ranking
    ]
    cs = CheckSheetArtifact.model_validate(make_check_sheet(categories=categories, strata_fields=[], entries=entries))
    text = _text(check_sheet=cs)
    assert "Top 4 shown" in text
    assert "full ranking is in the Check Sheet report" in text


def test_verified_causes_are_quoted_by_text():
    fb = FishboneArtifact.model_validate(make_fishbone())  # the factory's one verified cause
    text = _text(fishbone=fb)
    assert "1 cause on the fishbone" in text or "4 causes on the fishbone" in text  # factory carries 4 causes total
    assert "1 verified" in text
    assert "Fixture alignment not checked before shift start" in text


def test_more_than_three_verified_causes_are_counted_not_all_quoted():
    causes = [
        {
            "cause_id": f"c{i}", "branch": "machine", "text": f"cause number {i}", "status": "verified",
            "evidence": {"kind": "observation_note", "ref": f"note {i}"},
        }
        for i in range(6)
    ]
    fb = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    text = _text(fishbone=fb)
    assert "6 causes on the fishbone; 6 verified." in text
    assert "+3 more verified causes" in text
    assert "cause number 3" not in text  # the 4th (index 3) is past the cap of 3


# --------------------------------------------------------------- next action


def test_next_action_is_marked_as_advice_not_a_computed_result():
    text = _text()
    assert "SUGGESTED NEXT STEP" in text
    assert "not a computed result" in text


def test_next_action_with_nothing_saved_points_at_the_charter():
    assert "No charter saved yet -- start there" in next_action_text_for()


def next_action_text_for(**overrides):
    return summary.next_action_text(
        overrides.get("charter"), overrides.get("fishbone"), overrides.get("solution_matrix")
    )


def test_next_action_with_only_a_charter_points_at_bringing_in_data():
    charter = CharterArtifact.model_validate(make_charter())
    assert "bring in data and find out where the gap actually concentrates" in next_action_text_for(charter=charter)


def test_next_action_with_an_open_fishbone_points_at_adding_causes():
    fb = FishboneArtifact.model_validate(make_fishbone(causes=[]))
    assert "add candidate causes on the branches that fit" in next_action_text_for(fishbone=fb)


def test_next_action_with_unverified_causes_points_at_evidence():
    fb = FishboneArtifact.model_validate(
        make_fishbone(causes=[{"cause_id": "c1", "branch": "machine", "text": "drifts mid-peak", "status": "candidate"}])
    )
    assert "attach evidence to a candidate cause" in next_action_text_for(fishbone=fb)


def test_next_action_with_verified_causes_points_at_the_solution_matrix():
    fb = FishboneArtifact.model_validate(make_fishbone())  # one verified cause
    assert "rank countermeasures for them in the Solution Matrix (T-18)" in next_action_text_for(fishbone=fb)


def test_next_action_with_a_ranked_solution_matrix_quotes_the_top_fix():
    sm = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    fb = FishboneArtifact.model_validate(make_fishbone())
    text = next_action_text_for(fishbone=fb, solution_matrix=sm)
    assert 'Top-ranked countermeasure on file: "Add fixture alignment checklist"' in text
    assert "quick win" in text  # quadrant "quick_win", underscore replaced with a space


def test_next_action_with_an_unranked_solution_matrix_falls_back_to_the_fishbone():
    """Every solution unlinked -- ranked_fix_list.ranked is empty -- so the
    cascade must not claim a top fix that does not exist."""
    unranked = {
        "schema_version": 1, "artifact_id": "solmatrix-002", "tool_id": "T-18",
        "created_at": "2026-08-07T00:00:00", "updated_at": "2026-08-07T00:00:00",
        "solutions": [
            {"solution_id": "s-1", "name": "Idea", "description": "", "linked_cause_ids": [], "impact": 3, "effort": 3, "criterion_scores": []},
        ],
        "criteria": [],
    }
    sm = SolutionMatrixArtifact.model_validate(unranked)
    fb = FishboneArtifact.model_validate(make_fishbone())
    text = next_action_text_for(fishbone=fb, solution_matrix=sm)
    assert "Top-ranked countermeasure" not in text
    assert "rank countermeasures for them in the Solution Matrix (T-18)" in text


# ------------------------------------------------------------- the one page


def test_the_summary_is_one_page_even_with_a_rich_project():
    """The whole discipline, restated for this report -- export/reports/
    a3.py's own capstone test does the identical thing for the A3 sheet.
    Every BUDGETED section here is pushed to its actual cap, not just to a
    generous-looking input: the problem and goal text are each long enough
    to hit PROBLEM_CHAR_BUDGET/GOAL_CHAR_BUDGET's own clips (a short
    factory-default charter understates this section, since clip() is a
    no-op on text already under budget), category labels and cause text
    are long enough to hit their own per-cell clips, plus ten causes (six
    verified), nine check-sheet categories, a ranked solution matrix, and
    two datasets. See test_the_summary_is_one_page_with_a_dataset_pareto_
    chart_and_a_rich_project below for the same discipline applied to the
    OTHER top-categories source -- a dataset Pareto with a chart image
    instead of a check sheet."""
    body = make_charter()
    body["problem_statement"]["what"] = (
        "Wrong items picked and shipped on restaurant orders across every one of the eighteen evening-shift picking routes"
    )
    body["problem_statement"]["where"] = (
        "The entire ninety-thousand-square-foot food-service distribution warehouse, all four dock doors and four aisles"
    )
    body["goal"]["statement"] = (
        "Reduce mis-picks from four hundred eighty-seven errors a month to under fifty by the end of Q4 2026, "
        "without adding headcount or slowing down the evening shift's throughput"
    )
    charter = CharterArtifact.model_validate(body)
    assert len(summary.problem_text(charter)) > summary.PROBLEM_CHAR_BUDGET, (
        "this fixture is supposed to exceed the problem clip budget -- if it stopped doing so, "
        "this test would silently stop exercising PROBLEM_CHAR_BUDGET's worst case"
    )
    assert len(summary.goal_text(charter)) > summary.GOAL_CHAR_BUDGET, (
        "this fixture is supposed to exceed the goal clip budget -- if it stopped doing so, "
        "this test would silently stop exercising GOAL_CHAR_BUDGET's worst case"
    )
    causes = [
        {
            "cause_id": f"c{i}", "branch": "machine",
            "text": ("this verified root cause has a genuinely long sentence behind it " * 2) + str(i), "status": "verified",
            "evidence": {"kind": "observation_note", "ref": f"logged on the floor, shift {i}"},
        }
        for i in range(6)
    ] + [
        {"cause_id": f"cand{i}", "branch": "method", "text": f"candidate suspect {i}", "status": "candidate"}
        for i in range(4)
    ]
    fishbone = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    solution_matrix = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    categories = [{"category_id": f"c{i}", "label": f"A fairly long category label for aisle {i}"} for i in range(9)]
    entries = [
        {"entry_id": f"e{i}-{j}", "category_id": f"c{i}", "timestamp": "2026-08-07T08:00:00", "note": ""}
        for i in range(9)
        for j in range(9 - i)
    ]
    check_sheet = CheckSheetArtifact.model_validate(
        make_check_sheet(categories=categories, strata_fields=[], entries=entries)
    )
    datasets = [_dataset_meta(dataset_id="ds-1", created_at="2026-08-01T00:00:00"), _dataset_meta(dataset_id="ds-2", row_count=612)]

    pdf_bytes = report_pdf.render(
        story_builder=lambda w: summary.build_story(
            project_name="A Fairly Long Project Name, For Good Measure",
            charter=charter, fishbone=fishbone, solution_matrix=solution_matrix, check_sheet=check_sheet,
            datasets=datasets,
            provenance_rows=[
                ("Artifacts used", "T-03 charter-001 v1, T-15 fishbone-001 v1, T-18 solmatrix-001 v1, T-08 checksheet-001 v1"),
                ("Dataset", "ds-2 · 612 row(s) · sha256 aaaaaaaaaaaa…"), ("Engine version", "0.1.0"),
            ],
            exported_at="2026-08-12 00:00 UTC", content_width=w,
        ),
        title="t", project_id="p", engine_version="0.1.0",
    )
    assert pdf_bytes.startswith(b"%PDF-")
    assert _pdf_page_count(pdf_bytes) == 1, f"expected exactly 1 page, got {_pdf_page_count(pdf_bytes)}"


def _png(width: int, height: int) -> bytes:
    """Minimal valid PNG bytes for a report's chart slot -- the same
    builder as test_report_pdf.py's test_chart_is_capped_so_the_report_
    stays_one_page, duplicated locally rather than imported across test
    files (no test-to-test imports elsewhere in this suite)."""
    import struct
    import zlib

    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_the_summary_is_one_page_with_a_dataset_pareto_chart_and_a_rich_project():
    """The same discipline as test_the_summary_is_one_page_even_with_a_rich_
    project, for the OTHER top-categories source: no check sheet, so a
    dataset-Pareto tally carries TOP CATEGORIES -- enough categories to hit
    TOP_CATEGORIES_SHOWN, long enough labels to hit the table's own
    per-cell clip, and its chart image, the one element this path adds
    over the check-sheet path. Charter, fishbone and solution matrix are
    pushed to the same worst-case sizes as the other test, so this
    measures the chart's own cost rather than a lighter project elsewhere
    absorbing it."""
    body = make_charter()
    body["problem_statement"]["what"] = (
        "Wrong items picked and shipped on restaurant orders across every one of the eighteen evening-shift picking routes"
    )
    body["problem_statement"]["where"] = (
        "The entire ninety-thousand-square-foot food-service distribution warehouse, all four dock doors and four aisles"
    )
    body["goal"]["statement"] = (
        "Reduce mis-picks from four hundred eighty-seven errors a month to under fifty by the end of Q4 2026, "
        "without adding headcount or slowing down the evening shift's throughput"
    )
    charter = CharterArtifact.model_validate(body)

    causes = [
        {
            "cause_id": f"c{i}", "branch": "machine",
            "text": ("this verified root cause has a genuinely long sentence behind it " * 2) + str(i), "status": "verified",
            "evidence": {"kind": "observation_note", "ref": f"logged on the floor, shift {i}"},
        }
        for i in range(6)
    ] + [
        {"cause_id": f"cand{i}", "branch": "method", "text": f"candidate suspect {i}", "status": "candidate"}
        for i in range(4)
    ]
    fishbone = FishboneArtifact.model_validate(make_fishbone(causes=causes))
    solution_matrix = SolutionMatrixArtifact.model_validate(make_solution_matrix())
    datasets = [_dataset_meta(dataset_id="ds-1", created_at="2026-08-01T00:00:00"), _dataset_meta(dataset_id="ds-2", row_count=612)]

    raw_categories: list[str] = []
    for i in range(12):
        label = f"A fairly long imported category label for part number {10000 + i}"
        raw_categories += [label] * (12 - i)  # strictly descending counts -- an unambiguous ranking
    pareto = compute_pareto(raw_categories).value
    dataset_pareto = summary.DatasetParetoSource(
        source_filename="a-fairly-long-imported-error-log-filename-for-testing.xlsx",
        column="Wrong Part Number",
        pareto=pareto,
    )

    pdf_bytes = report_pdf.render(
        story_builder=lambda w: summary.build_story(
            project_name="A Fairly Long Project Name, For Good Measure",
            charter=charter, fishbone=fishbone, solution_matrix=solution_matrix, check_sheet=None,
            datasets=datasets,
            dataset_pareto=dataset_pareto,
            chart_png=_png(1000, 560),
            provenance_rows=[
                ("Artifacts used", "T-03 charter-001 v1, T-15 fishbone-001 v1, T-18 solmatrix-001 v1"),
                ("Dataset", "ds-2 · 612 row(s) · sha256 aaaaaaaaaaaa…"),
                (
                    "Top categories from",
                    "dataset column 'Wrong Part Number' in a-fairly-long-imported-error-log-filename-for-testing.xlsx",
                ),
                ("Engine version", "0.1.0"),
            ],
            exported_at="2026-08-12 00:00 UTC", content_width=w,
        ),
        title="t", project_id="p", engine_version="0.1.0",
    )
    assert pdf_bytes.startswith(b"%PDF-")
    assert _pdf_page_count(pdf_bytes) == 1, f"expected exactly 1 page, got {_pdf_page_count(pdf_bytes)}"


# --------------------------------------------------------------- the route


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    from sigma_engine.main import app

    return TestClient(app)


def _create_project(client: TestClient, project_id: str = "proj-1", name: str = "Line 2 Molding") -> None:
    resp = client.post("/project/create", json={"project_id": project_id, "name": name, "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


CSV_BYTES = b"aisle,defect\n5,scratch\n5,scratch\n12,crack\n5,short pour\n"
CSV_B64 = base64.b64encode(CSV_BYTES).decode("ascii")


def test_route_404s_on_a_missing_project(client):
    resp = client.post("/project/no-such-project/summary/pdf")
    assert resp.status_code == 404


def test_route_200s_and_is_one_page_on_a_freshly_created_project(client):
    """Nothing saved at all is still a valid summary -- an index of gaps,
    not a 404. Unlike the phase pack (which refuses an empty phase), this
    report's whole purpose is to say what is missing, so an empty project
    is exactly the case it must handle, not refuse."""
    _create_project(client)
    resp = client.post("/project/proj-1/summary/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")
    assert _pdf_page_count(resp.content) == 1
    assert 'filename="Line-2-Molding-summary.pdf"' in resp.headers["content-disposition"]


def test_route_with_a_charter_and_a_fishbone_stays_one_page(client):
    """The task's own verification scenario: a project with a charter and
    a fishbone, nothing else."""
    _create_project(client)
    assert client.post("/project/proj-1/artifacts/T-03", json=make_charter()).status_code == 200
    assert client.post("/project/proj-1/artifacts/T-15", json=make_fishbone()).status_code == 200

    resp = client.post("/project/proj-1/summary/pdf")
    assert resp.status_code == 200, resp.text
    assert _pdf_page_count(resp.content) == 1


def test_route_with_a_saved_dataset_stays_one_page(client):
    _create_project(client)
    save = client.post(
        "/project/proj-1/datasets",
        json={"source_filename": "errors.csv", "content_base64": CSV_B64, "created_at": "2026-08-07T01:00:00"},
    )
    assert save.status_code == 200, save.text

    resp = client.post("/project/proj-1/summary/pdf")
    assert resp.status_code == 200
    assert _pdf_page_count(resp.content) == 1


def test_route_with_every_source_populated_stays_one_page(client):
    _create_project(client)
    assert client.post("/project/proj-1/artifacts/T-03", json=make_charter()).status_code == 200
    assert client.post("/project/proj-1/artifacts/T-15", json=make_fishbone()).status_code == 200
    assert client.post("/project/proj-1/artifacts/T-18", json=make_solution_matrix()).status_code == 200
    assert client.post("/project/proj-1/artifacts/T-08", json=make_check_sheet()).status_code == 200
    save = client.post(
        "/project/proj-1/datasets",
        json={"source_filename": "errors.csv", "content_base64": CSV_B64, "created_at": "2026-08-07T01:00:00"},
    )
    assert save.status_code == 200, save.text

    resp = client.post("/project/proj-1/summary/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.content.startswith(b"%PDF-")
    assert _pdf_page_count(resp.content) == 1


def test_route_does_not_change_when_a_stale_artifact_cannot_validate(client, tmp_path, monkeypatch):
    """One unreadable artifact must not break a summary that covers
    several -- project_pdf.py's own defensive stance, applied here too
    (routes/export.py's _load_optional)."""
    import json as jsonlib

    _create_project(client)
    assert client.post("/project/proj-1/artifacts/T-03", json=make_charter()).status_code == 200

    root = tmp_path / "projects" / "proj-1" / "artifacts" / "charter-001"
    bad = jsonlib.loads((root / "v1.json").read_text())
    del bad["problem_statement"]  # now fails CharterArtifact validation
    (root / "v1.json").write_text(jsonlib.dumps(bad))

    resp = client.post("/project/proj-1/summary/pdf")
    assert resp.status_code == 200, resp.text
    assert _pdf_page_count(resp.content) == 1


# --- Solution-matrix quadrant labels ------------------------------------
# Not strictly this feature's territory, but this is the file that noticed:
# the report's label map was keyed on names the artifact never produces, so
# three quadrants out of four printed their raw enum value to the user.

def test_quadrant_labels_cover_every_quadrant_the_artifact_can_produce():
    from typing import get_args

    from sigma_engine.artifacts.solution_matrix import Quadrant
    from sigma_engine.export.reports.solution_matrix import QUADRANT_LABELS

    assert set(get_args(Quadrant)) == set(QUADRANT_LABELS), (
        "every Quadrant the artifact can hold needs a human label, or the report "
        "falls back to printing the raw enum value"
    )


# --- number/unit spacing (found rendering the populated summary) ----------

def test_word_unit_gets_a_space_but_a_symbol_unit_does_not():
    from sigma_engine.export.reports.summary import _value_unit
    assert _value_unit("487", "picking errors") == "487 picking errors"
    assert _value_unit("1.26", "% of order lines") == "1.26% of order lines"
    assert _value_unit("6,800", "$/month") == "6,800$/month"
    assert _value_unit("5", "") == "5"


def test_populated_problem_line_does_not_run_the_number_into_its_unit():
    body = make_charter()
    body["problem_statement"] = {
        "what": "Wrong items picked", "where": "line 2", "when": "since April",
        "magnitude": {"number": 487, "unit": "picking errors", "period": "June 2026"},
    }
    charter = CharterArtifact.model_validate(body)
    text = _text(charter=charter)
    assert "487 picking errors" in text
    assert "487picking" not in text
