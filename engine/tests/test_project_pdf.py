"""Whole-project PDF export (export/project_pdf.py + routes/export.py).

Asserts against the built flowable story rather than parsed PDF bytes,
matching test_charter_pdf.py's approach: no pypdf dependency, and a failure
points at the content that is wrong instead of at a binary diff.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from sigma_engine.export import project_pdf
from sigma_engine.export.project_pdf import (
    MAX_CELL_CHARS,
    TOOL_TITLES,
    build_project_story,
    can_tabulate,
    render_project_pdf,
)
from sigma_engine.main import app
from sigma_engine.registry import ARTIFACT_REGISTRY


def _flatten(flowables) -> str:
    """Every string anywhere in the story -- paragraphs, table cells, and
    the contents of KeepTogether wrappers."""
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


CHARTER = {
    "artifact_id": "charter",
    "tool_id": "T-03",
    "schema_version": 1,
    "problem_statement": {"what": "Orders take too long at the counter.", "where": "Front counter"},
    "business_impact": {"amount": 16084.0, "unit": "dollars per year"},
}
FMEA = {
    "artifact_id": "fmea",
    "tool_id": "T-16",
    "schema_version": 1,
    "rows": [
        {"step": "Prepare drink", "failure_mode": "Shot pulls slow", "severity": 5},
        {"step": "Call name", "failure_mode": "Name called once", "severity": 4},
    ],
}


def test_every_registry_tool_has_a_title():
    """A tool added to the registry without a title here would export under
    a bare id, or -- worse -- be dropped by build_project_story's filter and
    silently vanish from the record."""
    assert sorted(TOOL_TITLES) == sorted(ARTIFACT_REGISTRY)


def test_story_carries_content_from_every_supplied_artifact():
    story = build_project_story("Coffee Bar", "coffee-bar", [("T-03", CHARTER, 1), ("T-16", FMEA, 2)], 480.0)
    text = _flatten(story)
    assert "Orders take too long at the counter." in text
    assert "Shot pulls slow" in text
    assert "Project Charter" in text
    assert "FMEA" in text


def test_sections_are_ordered_by_dmaic_phase_not_input_order():
    # Supplied Analyze-then-Define; the record must read Define-then-Analyze.
    # Compare the SECTION HEADERS ("T-03 · Project Charter"), not bare tool
    # names: kv_table uppercases its labels, so the contents list contains
    # "PROJECT CHARTER" and "FMEA", and a bare-name search matches one entry
    # in the contents and the other in the body -- comparing two different
    # kinds of position and proving nothing.
    story = build_project_story("P", "p", [("T-16", FMEA, 1), ("T-03", CHARTER, 1)], 480.0)
    text = _flatten(story)
    assert text.index("T-03 · Project Charter") < text.index("T-16 · FMEA")
    assert text.index("DEFINE") < text.index("ANALYZE")


def test_computed_values_are_marked_as_computed_not_flattened():
    """The typed-vs-derived distinction is the product's whole claim; an
    export that drops it turns a traceable record into an assertion."""
    artifact = {
        "artifact_id": "copq",
        "tool_id": "T-02",
        "schema_version": 1,
        "total": {"value": 4021.0, "provenance": {"method": "sum of row amounts", "engine_version": "0.1.0"}},
    }
    text = _flatten(build_project_story("P", "p", [("T-02", artifact, 1)], 480.0))
    assert "4,021" in text
    assert "Engine-computed" in text
    assert "sum of row amounts" in text


def test_bulk_sample_vectors_are_summarised_not_printed():
    artifact = {"artifact_id": "a", "tool_id": "T-13", "schema_version": 1, "values": list(range(120))}
    # T-13 has no artifact model, so use a real tool id that does.
    artifact["tool_id"] = "T-21"
    text = _flatten(build_project_story("P", "p", [("T-21", artifact, 1)], 480.0))
    assert "120 values" in text
    assert "119" not in text  # the vector itself never reaches the page


def test_unknown_tool_ids_are_skipped_rather_than_crashing():
    story = build_project_story("P", "p", [("T-99", {"artifact_id": "x"}, 1), ("T-03", CHARTER, 1)], 480.0)
    assert "Orders take too long at the counter." in _flatten(story)


def test_long_prose_is_never_put_in_a_table():
    """Regression: the A3's narrative panels produced a table cell ~2000pt
    tall against a ~710pt frame, and ReportLab raised LayoutError on page
    127 -- a row splits between rows but never within one, so the whole
    export died. Long text must route to labelled blocks instead."""
    items = [{"panel": "Background", "narrative": "x" * (MAX_CELL_CHARS + 50)}]
    assert can_tabulate(items) is False
    assert can_tabulate([{"panel": "Background", "narrative": "short"}]) is True


def test_renders_a_real_pdf_with_the_long_prose_that_used_to_crash():
    artifact = {
        "artifact_id": "a3",
        "tool_id": "T-25",
        "schema_version": 1,
        "panels": [{"panel": "Background", "narrative": "Espresso orders ran long. " * 200}],
    }
    pdf = render_project_pdf(project_name="P", project_id="p", artifacts=[("T-25", artifact, 1)], engine_version="0.1.0")
    assert pdf.startswith(b"%PDF-")
    assert len(re.findall(rb"/Type\s*/Page[^s]", pdf)) >= 2


def test_route_404s_for_a_project_with_no_saved_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path))
    client = TestClient(app)
    created = client.post(
        "/project/create",
        json={"project_id": "empty-proj", "name": "Empty", "created_at": "2026-08-09T00:00:00"},
    )
    assert created.status_code == 200, created.text
    response = client.get("/project/empty-proj/export/pdf")
    assert response.status_code == 404
    assert "no saved tools" in response.json()["detail"]


def test_route_404s_for_a_missing_project(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path))
    response = TestClient(app).get("/project/does-not-exist/export/pdf")
    assert response.status_code == 404


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Coffee Bar — worked example", "Coffee-Bar---worked-example"),
        ("../../etc/passwd", "etc-passwd"),
        ('quote"and\nnewline', "quote-and-newline"),
        ("", "sigma-project"),
        ("???", "sigma-project"),
    ],
)
def test_download_filename_is_safe(name, expected):
    """Project names are free text and end up in a Content-Disposition
    header, so path separators, quotes and newlines must not survive."""
    from sigma_engine.routes.export import _safe_filename

    assert _safe_filename(name) == expected


def test_module_exposes_a_stable_surface():
    assert set(project_pdf.__all__) <= set(dir(project_pdf))
