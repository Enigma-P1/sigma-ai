"""Content assertions for sigma_engine/export/charter_pdf.py's built story:
walk the Platypus Paragraph/Table objects and extract their text (the
"render-to-string of the story elements" check named in the M1 export
brief) instead of parsing rendered PDF bytes. PDF-bytes-level checks
(magic bytes, page count, footer text) live in test_export_charter_pdf.py.
"""

from __future__ import annotations

from typing import Any

from reportlab.platypus import Paragraph, Table

from factories import load_demo_charter, make_charter
from sigma_engine.artifacts.charter import CharterArtifact
from sigma_engine.export.charter_pdf import build_charter_story


def _flowable_text(flowable: Any) -> str:
    """Plain text out of a Paragraph or Table. Spacer/HRFlowable/
    ListFlowable contribute "": none of the assertions below need
    bullet-list text (the one place this module builds one)."""
    if isinstance(flowable, Paragraph):
        return flowable.getPlainText()
    if isinstance(flowable, Table):
        parts: list[str] = []
        for row in flowable._cellvalues:
            for cell in row:
                cells = cell if isinstance(cell, (list, tuple)) else [cell]
                parts.extend(_flowable_text(c) for c in cells)
        return " ".join(p for p in parts if p)
    return ""


def story_text(story: list[Any]) -> str:
    return "\n".join(_flowable_text(f) for f in story)


def test_story_contains_problem_statement_and_owner_name():
    artifact = CharterArtifact.model_validate(load_demo_charter())
    story = build_charter_story(artifact, project_name="Coffee Bar", version=2, content_width=450.0)
    text = story_text(story)

    assert "Espresso-drink orders take too long" in text  # problem_statement.what
    assert "Priya Shah" in text  # process_owner.name


def test_story_contains_artifact_id_and_version():
    artifact = CharterArtifact.model_validate(load_demo_charter())
    story = build_charter_story(artifact, project_name="Coffee Bar", version=3, content_width=450.0)
    text = story_text(story)

    assert "Version 3" in text
    assert artifact.artifact_id in text  # "coffee-charter"


def test_story_shows_a_message_instead_of_a_broken_empty_risks_table():
    artifact = CharterArtifact.model_validate(make_charter(risks=[]))
    story = build_charter_story(artifact, project_name="Line 2 Molding", version=1, content_width=450.0)
    assert "No risks logged yet." in story_text(story)


def test_render_escapes_ampersand_instead_of_corrupting_it():
    """xml.sax.saxutils.escape() in charter_pdf_common.esc() is
    load-bearing: an unescaped '&' doesn't raise, it silently mangles the
    text (observed while building this: "R&D" -> "R&D;"). This proves the
    escaping path is actually wired into the section builders, not just
    defined and unused."""
    data = make_charter()
    data["problem_statement"]["what"] = "R&D scrap rate on Line 2"
    artifact = CharterArtifact.model_validate(data)

    story = build_charter_story(artifact, project_name="R&D Pilot", version=1, content_width=450.0)
    text = story_text(story)
    assert "R&D scrap rate on Line 2" in text
    assert "R&D;" not in text
