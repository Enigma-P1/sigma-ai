"""The T-20/T-21 full-loop test (build brief): pilot -> before/after
datasets -> proof, exercised through the real HTTP routes (generic
artifact CRUD + prescore, registered for T-20/T-21 in registry.py -- no
bespoke route file needed for either, task brief's own design finding).
Three proof variants (met+partial-recovery+next-cause, weakened,
not-met), plus a T-21 freeze-preview and EXIT-11 refusal, both via the
existing generic /artifacts/{tool_id}/validate endpoint."""

import base64

import pytest
from fastapi.testclient import TestClient

from factories import TS, make_control_chart_imr, make_pilot_plan, make_pilot_plan_confounder_checklist, make_proof
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client):
    resp = client.post("/project/create", json={"project_id": "loop-1", "name": "Loop Test", "created_at": TS})
    assert resp.status_code == 200, resp.text


def _save_dataset(client, filename: str, header: str, rows: list[str]) -> str:
    csv_text = header + "\n" + "\n".join(rows) + "\n"
    content_b64 = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
    resp = client.post("/project/loop-1/datasets", json={"source_filename": filename, "content_base64": content_b64, "created_at": TS})
    assert resp.status_code == 200, resp.text
    return resp.json()["sha256"]


def _save_pilot(client) -> str:
    resp = client.post("/project/loop-1/artifacts/T-19", json=make_pilot_plan())
    assert resp.status_code == 200, resp.text
    return resp.json()["artifact_id"]


def test_full_loop_threshold_met_gap_partially_recovered_next_cause_named(client):
    _create_project(client)
    before_sha = _save_dataset(client, "before.csv", "scrap_pct", ["6.0", "6.4", "6.1", "6.3", "5.9", "6.5", "6.2", "6.0", "6.3", "6.1"])
    after_sha = _save_dataset(client, "after.csv", "scrap_pct", ["4.2", "3.9", "4.1", "4.0", "3.8", "4.3", "4.0", "3.9", "4.1", "4.0"])
    pilot_id = _save_pilot(client)

    body = make_proof(pilot_ref=pilot_id)
    body["before"]["dataset_sha256"] = before_sha
    body["after"]["dataset_sha256"] = after_sha

    save = client.post("/project/loop-1/artifacts/T-20", json=body)
    assert save.status_code == 200, save.text
    proof_id = save.json()["artifact_id"]

    loaded = client.get(f"/project/loop-1/artifacts/{proof_id}").json()
    assert loaded["verdict"]["value"]["threshold_verdict"] == "met"
    gap = loaded["gap"]["value"]
    assert 0 < gap["recovered_pct"] < 100  # partial recovery, hand-checkable at 67.8125% (test_artifacts_proof.py)
    assert gap["goal_met"] is False
    assert gap["next_cause_ref"]["cause_id"] == "c-2"
    assert "next-ranked verified cause" in gap["loop_verdict"]

    prescore = client.post("/prescore/T-20", json=body).json()
    assert all(r["status"] == "pass" for r in prescore), prescore


def test_full_loop_weakened_variant_prints_confounder_sentence(client):
    _create_project(client)
    pilot_id = _save_pilot(client)
    checklist = make_pilot_plan_confounder_checklist()
    checklist["demand"] = {"changed": True, "note": "A local event doubled foot traffic during the after window."}
    body = make_proof(pilot_ref=pilot_id, confounders=checklist)

    save = client.post("/project/loop-1/artifacts/T-20", json=body)
    assert save.status_code == 200, save.text
    loaded = client.get(f"/project/loop-1/artifacts/{save.json()['artifact_id']}").json()
    assert loaded["verdict"]["value"]["weakened"] is True
    assert "weakens this proof" in loaded["verdict"]["value"]["headline"]
    assert "demand" in loaded["verdict"]["value"]["confounder_notes"][0]


def test_full_loop_not_met_variant_carries_no_improvement_language(client):
    _create_project(client)
    pilot_id = _save_pilot(client)
    body = make_proof(pilot_ref=pilot_id, after_values=[5.0, 4.9, 5.1, 5.0, 4.8, 5.2, 5.0, 4.9, 5.1, 5.0])

    save = client.post("/project/loop-1/artifacts/T-20", json=body)
    assert save.status_code == 200, save.text
    loaded = client.get(f"/project/loop-1/artifacts/{save.json()['artifact_id']}").json()
    headline = loaded["verdict"]["value"]["headline"].lower()
    assert loaded["verdict"]["value"]["threshold_verdict"] == "not_met"
    assert "threshold not met" in headline
    assert "target hit" not in headline and "proven" not in headline


def test_control_chart_freeze_preview_via_validate_endpoint(client):
    # No save needed -- POST /artifacts/T-21/validate runs the same
    # freeze validator and hands back the computed baseline for preview.
    preview = client.post("/artifacts/T-21/validate", json=make_control_chart_imr())
    assert preview.status_code == 200, preview.text
    artifact = preview.json()["artifact"]
    assert artifact["imr_baseline"]["value"]["n"] == 24
    assert artifact["frozen_at"] is not None


def test_control_chart_saves_through_the_generic_registry_route(client):
    _create_project(client)
    save = client.post("/project/loop-1/artifacts/T-21", json=make_control_chart_imr())
    assert save.status_code == 200, save.text
    prescore = client.post("/prescore/T-21", json=make_control_chart_imr()).json()
    ids = {r["check_id"] for r in prescore}
    assert "family_matches_data" in ids
    assert any(r["check_id"] == "never_armed" and r["status"] == "hard_flag" for r in prescore)


def test_control_chart_exit11_refusal_via_validate_endpoint(client):
    body = make_control_chart_imr()
    body["chart_type"], body["selector"] = "p", {"data_shape": "attribute", "defectives_or_defects": "defects"}
    body["imr_values"] = None
    body["p_subgroups"] = [{"label": "d1", "n": 50, "defective_count": 5}]
    refused = client.post("/artifacts/T-21/validate", json=body)
    assert refused.status_code == 422
    assert "EXIT-11" in str(refused.json())
