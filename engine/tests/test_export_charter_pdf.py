"""Tests for sigma_engine/export/charter_pdf.py's rendered PDF bytes and
footer text: render the demo Coffee Bar charter fixture and check the
result is a real, correctly-sized PDF -- without pypdf as a new dependency
(M1 export brief). Story-content assertions (problem statement, owner
name, artifact id/version) live in test_export_charter_pdf_story.py.
"""

from __future__ import annotations

import re

from factories import load_demo_charter, make_charter
from sigma_engine import __version__
from sigma_engine.artifacts.charter import CharterArtifact
from sigma_engine.export.charter_pdf import build_charter_story, footer_text, render_charter_pdf


def _pdf_page_count(pdf_bytes: bytes) -> int:
    """Count real page objects (/Type /Page). Excludes /Type /Pages (the
    page-tree root), which contains "/Type /Page" as a raw substring --
    verified against reportlab's own output before relying on it."""
    return len(re.findall(rb"/Type\s*/Page(?!s)\b", pdf_bytes))


def test_demo_charter_fixture_is_schema_valid():
    artifact = CharterArtifact.model_validate(load_demo_charter())
    assert artifact.artifact_id == "coffee-charter"


def test_render_demo_charter_is_a_real_one_to_two_page_pdf():
    artifact = CharterArtifact.model_validate(load_demo_charter())
    pdf_bytes = render_charter_pdf(artifact, project_name="Coffee Bar", version=2, engine_version=__version__)

    assert pdf_bytes[:5] == b"%PDF-"
    page_count = _pdf_page_count(pdf_bytes)
    assert 1 <= page_count <= 2, f"expected 1-2 pages, got {page_count}"


def test_render_from_factories_charter_with_empty_risks_is_also_valid():
    """Not just the demo fixture -- the generic factory charter (empty
    risks, no baseline_value) renders cleanly too."""
    artifact = CharterArtifact.model_validate(make_charter(risks=[]))
    pdf_bytes = render_charter_pdf(artifact, project_name="Line 2 Molding", version=1, engine_version=__version__)

    assert pdf_bytes[:5] == b"%PDF-"
    assert 1 <= _pdf_page_count(pdf_bytes) <= 2


def test_footer_text_carries_policy_sentence_and_ids():
    meta_line, policy_line = footer_text("coffee-charter", 2, 1, "0.1.0")

    assert "coffee-charter" in meta_line
    assert "v2" in meta_line
    assert "schema v1" in meta_line
    assert "engine v0.1.0" in meta_line
    assert "not certification evidence" in policy_line
    assert "not validation for regulated processes" in policy_line


def test_build_charter_story_is_a_pure_function_of_its_inputs():
    """Same inputs -> the same number of flowables every time -- no wall
    clock, no hidden state (charter_pdf.py's docstring claims this)."""
    artifact = CharterArtifact.model_validate(load_demo_charter())
    first = build_charter_story(artifact, project_name="Coffee Bar", version=2, content_width=450.0)
    second = build_charter_story(artifact, project_name="Coffee Bar", version=2, content_width=450.0)
    assert len(first) == len(second) > 0
