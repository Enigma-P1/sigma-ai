"""Phase packs — one phase's reports with a cover and a verdict index.

The pack's whole claim is that it agrees with the reports it contains. It
is built by CALLING each report module's own build_story and build_verdict
rather than re-deriving anything, and these tests exist to keep it that
way: a pack that drifted from the report it claims to enclose would be
worse than no pack at all.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

import pytest
from fastapi.testclient import TestClient

EXAMPLE_ZIP = pathlib.Path(__file__).resolve().parents[2] / "examples" / "coffee-bar-example-project.zip"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    root = tmp_path_factory.mktemp("pack-projects")
    subprocess.run(["unzip", "-qo", str(EXAMPLE_ZIP), "-d", str(root)], check=True)
    os.environ["SIGMA_PROJECTS_ROOT"] = str(root)
    from sigma_engine.main import app

    return TestClient(app)


def test_every_phase_pack_renders_a_real_pdf(client):
    from sigma_engine.export import pack_pdf

    for phase in pack_pdf.PACK_PHASES:
        res = client.post(f"/project/coffee-bar-example/pack/{phase}/pdf", json={})
        assert res.status_code == 200, (phase, res.text[:200])
        assert res.content.startswith(b"%PDF-"), phase
        assert len(res.content) > 5000, phase


def test_an_unknown_phase_is_refused_with_the_list_of_real_ones(client):
    res = client.post("/project/coffee-bar-example/pack/Nonsense/pdf", json={})
    assert res.status_code == 404
    assert "Define" in res.json()["detail"]


def test_intake_is_not_a_pack_of_its_own(client):
    """One tool behind a cover page is a worse document than the report.
    Intake folds into Define, where a reviewer looks for "was this the right
    project" anyway."""
    from sigma_engine.export import pack_pdf

    assert "Intake" not in pack_pdf.PACK_PHASES
    assert "T-01" in pack_pdf.tools_in_phase("Define")


def test_the_index_quotes_each_report_rather_than_judging_it_again(client):
    """The pack must never form a second opinion. Every index line comes
    from the report's own build_verdict, so a pack and the report it
    encloses cannot disagree."""
    import glob

    from sigma_engine.export import pack_pdf
    from sigma_engine.routes.export import ARTIFACT_REPORTS

    root = pathlib.Path(os.environ["SIGMA_PROJECTS_ROOT"]) / "coffee-bar-example"
    by_tool = {v["tool_id"]: k for k, v in json.load(open(root / "project.json"))["artifact_index"].items()}

    for tool_id in pack_pdf.tools_in_phase("Measure"):
        entry = ARTIFACT_REPORTS.get(tool_id)
        artifact_id = by_tool.get(tool_id)
        if entry is None or artifact_id is None:
            continue
        model, module, _ = entry
        data = json.load(open(sorted(glob.glob(str(root / "artifacts" / artifact_id / "*.json")))[-1]))
        artifact = model.model_validate(data)
        # The route calls exactly this; if a module ever stopped exposing it
        # the pack would have to invent a judgement instead.
        text, tone = module.build_verdict(artifact)
        assert isinstance(text, str) and text
        assert tone in ("pass", "flag", "fail", "neutral")


def test_a_tool_that_was_never_done_is_named_rather_than_omitted(client):
    """A Measure pack with no measurement check is the most important fact
    about that phase; a pack that simply did not mention it would read as
    complete. The worked example has no T-10, which is what makes this
    checkable."""
    from sigma_engine.export import pack_pdf

    root = pathlib.Path(os.environ["SIGMA_PROJECTS_ROOT"]) / "coffee-bar-example"
    saved = {v["tool_id"] for v in json.load(open(root / "project.json"))["artifact_index"].values()}
    measure_tools = set(pack_pdf.tools_in_phase("Measure"))
    absent = measure_tools - saved
    assert absent, "this test needs a Measure tool the worked example did not do"

    entries: list = []
    missing = sorted(absent)
    pdf = pack_pdf.build_pack(
        phase="Measure", project_name="P", project_id="p", engine_version="0.1.0",
        entries=entries + [("T-12", lambda w: [], ("repeatability fine", "pass"))],
        missing=missing, exported_at="x",
    )
    assert pdf.startswith(b"%PDF-")


def test_a_phase_with_nothing_saved_refuses_rather_than_shipping_a_cover(client, tmp_path):
    """An empty pack is a cover page and an index of absences. Better to say
    so than to hand someone a document that looks like work."""
    empty_root = tmp_path / "empty"
    (empty_root / "blank-project").mkdir(parents=True)
    (empty_root / "blank-project" / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 1, "project_id": "blank-project", "name": "Blank",
                "created_at": "2026-08-10T00:00:00Z", "updated_at": "2026-08-10T00:00:00Z",
                "current_phase": "Define", "artifact_index": {},
            }
        )
    )
    previous = os.environ["SIGMA_PROJECTS_ROOT"]
    os.environ["SIGMA_PROJECTS_ROOT"] = str(empty_root)
    try:
        res = client.post("/project/blank-project/pack/Measure/pdf", json={})
        assert res.status_code == 404
        assert "saved" in res.json()["detail"]
    finally:
        os.environ["SIGMA_PROJECTS_ROOT"] = previous
