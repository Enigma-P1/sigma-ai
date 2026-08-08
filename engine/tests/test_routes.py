"""Route smoke tests for every new endpoint, plus /health and /smoke stay green."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from factories import (
    make_charter,
    make_fishbone,
    make_fmea,
    make_picker,
    make_pilot_plan,
    make_process_map,
    make_sipoc,
    make_solution_matrix,
    make_voc_ctq,
)
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def test_health_and_smoke_still_green(client):
    assert client.get("/health").status_code == 200
    assert client.get("/smoke").json()["match"] is True


def test_project_create_and_open(client):
    resp = client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["project_id"] == "proj-1"

    resp2 = client.get("/project/proj-1")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == "Coffee Bar"

    assert client.get("/project/no-such-project").status_code == 404


def test_validate_artifact_endpoint(client):
    ok = client.post("/artifacts/T-01/validate", json=make_picker())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True

    bad_tool = client.post("/artifacts/T-99/validate", json=make_picker())
    assert bad_tool.status_code == 404

    bad_data = client.post("/artifacts/T-01/validate", json={"nope": True})
    assert bad_data.status_code == 422


def test_save_load_and_list_versions(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    save1 = client.post("/project/proj-1/artifacts/T-03", json=make_charter())
    assert save1.status_code == 200, save1.text
    assert save1.json() == {"artifact_id": "charter-001", "tool_id": "T-03", "version": 1}

    save2 = client.post("/project/proj-1/artifacts/T-03", json=make_charter(notes="revised after gemba walk"))
    assert save2.json()["version"] == 2

    loaded = client.get("/project/proj-1/artifacts/charter-001")
    assert loaded.status_code == 200
    assert loaded.json()["notes"] == "revised after gemba walk"  # latest by default

    loaded_v1 = client.get("/project/proj-1/artifacts/charter-001", params={"version": 1})
    assert loaded_v1.json()["notes"] is None

    versions = client.get("/project/proj-1/artifacts/charter-001/versions")
    assert versions.json() == {"artifact_id": "charter-001", "versions": [1, 2]}


def test_save_rejects_invalid_artifact(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    bad = make_charter()
    del bad["process_owner"]
    resp = client.post("/project/proj-1/artifacts/T-03", json=bad)
    assert resp.status_code == 422


def test_prescore_endpoint(client):
    resp = client.post("/prescore/T-04", json=make_sipoc(step_count=3))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body[0]["check_id"] == "step_count_range"
    assert body[0]["status"] == "hard_flag"

    resp2 = client.post("/prescore/T-05", json=make_voc_ctq())
    assert resp2.json()[0]["status"] == "pass"

    assert client.post("/prescore/T-99", json={}).status_code == 404


def test_gates_check_and_override_flow(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    check = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert check.status_code == 200
    assert check.json()["status"] == "SOFT_BLOCK"
    assert set(check.json()["missing"]) == {"T-04", "T-05"}
    assert check.json()["overridden"] is False

    empty_reason = client.post(
        "/gates/override",
        json={"gate_id": "define_to_measure", "project_id": "proj-1", "reason": "", "timestamp": "2026-08-07T04:00:00"},
    )
    assert empty_reason.status_code == 422

    override = client.post(
        "/gates/override",
        json={
            "gate_id": "define_to_measure", "project_id": "proj-1",
            "reason": "SIPOC and CTQ pending; unblocking to start Measure prep", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 200, override.text
    assert override.json()["gate_id"] == "define_to_measure"
    assert set(override.json()["missing"]) == {"T-04", "T-05"}

    # Re-checking the same gate now reads CLEAR-with-override-note -- the
    # override loop feeds back into check() instead of the caller having to
    # remember client-side that it already logged a reason.
    recheck = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert recheck.status_code == 200
    assert recheck.json()["status"] == "CLEAR"
    assert recheck.json()["overridden"] is True
    assert recheck.json()["override_reason"] == "SIPOC and CTQ pending; unblocking to start Measure prep"
    assert recheck.json()["missing"] == []


def test_stale_override_does_not_clear_the_gate(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())
    client.post("/project/proj-1/artifacts/T-03", json=make_charter())

    # Override while both T-04 and T-05 are missing.
    override = client.post(
        "/gates/override",
        json={
            "gate_id": "define_to_measure", "project_id": "proj-1",
            "reason": "SIPOC pending, unblocking to prep Measure templates", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 200, override.text

    # Artifacts change: SIPOC gets saved for real, so the missing set is now
    # just T-05 -- different from what the override covered.
    client.post("/project/proj-1/artifacts/T-04", json=make_sipoc())

    recheck = client.post("/gates/check", json={"gate_id": "define_to_measure", "project_id": "proj-1"})
    assert recheck.status_code == 200
    assert recheck.json()["status"] == "SOFT_BLOCK"
    assert recheck.json()["overridden"] is False
    assert recheck.json()["missing"] == ["T-05"]


def test_project_info_returns_absolute_path_and_artifact_summary(client, tmp_path):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    client.post("/project/proj-1/artifacts/T-01", json=make_picker())

    resp = client.get("/project/proj-1/info")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["project_id"] == "proj-1"
    assert body["name"] == "Coffee Bar"
    assert body["artifact_count"] == 1
    assert body["artifact_index"]["picker-001"] == {"tool_id": "T-01", "latest_version": 1}
    assert Path(body["folder_path"]).is_absolute()
    assert Path(body["folder_path"]) == (tmp_path / "projects" / "proj-1").resolve()

    assert client.get("/project/no-such-project/info").status_code == 404


def test_process_map_crud_and_prescore_via_registry(client):
    """T-06 end-to-end through the generic registry-driven routes: validate,
    save (longest_step/constraint_step computed server-side), load, and
    prescore."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_process_map(demand={"available_time_minutes": 480, "demand_units": 96})
    validated = client.post("/artifacts/T-06/validate", json=body)
    assert validated.status_code == 200, validated.text
    # step-2 ("Wait for register", non_value_add, 4.0 min) is the longest
    # step of any type; step-3 ("Make drink", value_add, 3.0 min) is the
    # longest PROCESSING step, so it's named the constraint.
    assert validated.json()["artifact"]["longest_step"]["value"]["step_id"] == "step-2"
    assert validated.json()["artifact"]["constraint_step"]["value"]["step_id"] == "step-3"

    saved = client.post("/project/proj-1/artifacts/T-06", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "process-map-001", "tool_id": "T-06", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/process-map-001")
    assert loaded.status_code == 200
    assert loaded.json()["constraint_step"]["value"]["meets_pace"] is True

    prescore = client.post("/prescore/T-06", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["lane_owner_present"] == "pass"
    assert statuses["bottleneck_fields_consistency"] == "pass"


def test_fishbone_crud_and_prescore_via_registry(client):
    """T-15 end-to-end through the generic registry-driven routes: verified-
    without-evidence rejected at validate, a valid save computes
    verified_causes server-side, and prescore runs on the saved shape."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_fishbone()
    bad = make_fishbone(causes=[{
        "cause_id": "c-x", "branch": "method", "text": "Fixture never checked", "parent_cause_id": None,
        "status": "verified", "evidence": None, "why_chain_position": None,
    }])
    rejected = client.post("/artifacts/T-15/validate", json=bad)
    assert rejected.status_code == 422

    validated = client.post("/artifacts/T-15/validate", json=body)
    assert validated.status_code == 200, validated.text
    assert validated.json()["artifact"]["verified_causes"]["value"]["count"] == 1

    saved = client.post("/project/proj-1/artifacts/T-15", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "fishbone-001", "tool_id": "T-15", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/fishbone-001")
    assert loaded.json()["verified_causes"]["value"]["causes"][0]["cause_id"] == "c-1"

    prescore = client.post("/prescore/T-15", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["verified_causes_have_evidence"] == "pass"
    assert statuses["cause_count_minimum"] == "flag"  # default fixture has 4 causes, floor is 6


def test_fmea_crud_and_prescore_via_registry(client):
    """T-16 end-to-end through the generic registry-driven routes: RPN and
    the severity-first sorted_view are computed server-side on save, and
    the safety-worded/no-action row surfaces as a blocking flag."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_fmea()
    validated = client.post("/artifacts/T-16/validate", json=body)
    assert validated.status_code == 200, validated.text
    artifact = validated.json()["artifact"]
    assert artifact["sorted_view"]["value"] == ["row-a", "row-c", "row-b"]
    assert [f["row_id"] for f in artifact["blocking_flags"]["value"]] == ["row-a"]
    rows_by_id = {r["row_id"]: r for r in artifact["rows"]}
    assert rows_by_id["row-b"]["rpn"] == 448

    saved = client.post("/project/proj-1/artifacts/T-16", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "fmea-001", "tool_id": "T-16", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/fmea-001")
    assert loaded.json()["anchors"]["severity"]["10"]  # JSON keys are always strings on the wire

    prescore = client.post("/prescore/T-16", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["high_severity_without_action"] == "hard_flag"
    assert statuses["ratings_in_range"] == "pass"


def test_solution_matrix_crud_and_prescore_via_registry(client):
    """T-18 end-to-end through the generic registry-driven routes: the
    ranked fix list and per-solution scores are computed server-side on
    save, and the unlinked solution surfaces as a prescore flag."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_solution_matrix()
    validated = client.post("/artifacts/T-18/validate", json=body)
    assert validated.status_code == 200, validated.text
    artifact = validated.json()["artifact"]
    assert [r["solution_id"] for r in artifact["ranked_fix_list"]["value"]["ranked"]] == ["s-1", "s-2"]
    assert artifact["ranked_fix_list"]["value"]["unlinked"][0]["solution_id"] == "s-3"

    saved = client.post("/project/proj-1/artifacts/T-18", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "solmatrix-001", "tool_id": "T-18", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/solmatrix-001")
    assert loaded.json()["scores"]["value"][0]["weighted_total"] == 23.0

    prescore = client.post("/prescore/T-18", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["unlinked_solution_flags"] == "flag"
    assert statuses["ranked_list_exists"] == "pass"


def test_pilot_plan_crud_and_prescore_via_registry(client):
    """T-19 end-to-end through the generic registry-driven routes, plus the
    EXIT-10 refusal surfacing as a 422 at the /validate boundary -- the
    same "engine refusal rendered" the desktop smoke asserts on."""
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})

    body = make_pilot_plan()
    validated = client.post("/artifacts/T-19/validate", json=body)
    assert validated.status_code == 200, validated.text

    two_changes = make_pilot_plan(changes=[
        {"change_id": "ch-1", "text": "Add a fixture alignment checklist before each shift"},
        {"change_id": "ch-2", "text": "Also replace the injector at the same time"},
    ])
    refused = client.post("/artifacts/T-19/validate", json=two_changes)
    assert refused.status_code == 422
    assert "EXIT-10" in str(refused.json()["detail"])

    saved = client.post("/project/proj-1/artifacts/T-19", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "pilot-001", "tool_id": "T-19", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/pilot-001")
    assert loaded.json()["the_one_change"]["statement"] == body["the_one_change"]["statement"]

    prescore = client.post("/prescore/T-19", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["checklist_completeness"] == "pass"
    assert statuses["falsification_substance_heuristic"] == "pass"


def test_gates_hard_block_and_override_refused(client):
    client.post("/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    exit01_picker = make_picker(route="EXIT-01")
    exit01_picker["data_obtainable"] = {"answer": False, "detail": "No data source exists yet."}
    client.post("/project/proj-1/artifacts/T-01", json=exit01_picker)

    check = client.post("/gates/check", json={"gate_id": "intake_picker_not_exit01", "project_id": "proj-1"})
    assert check.json()["status"] == "HARD_BLOCK"

    override = client.post(
        "/gates/override",
        json={
            "gate_id": "intake_picker_not_exit01", "project_id": "proj-1",
            "reason": "skip anyway", "timestamp": "2026-08-07T04:00:00",
        },
    )
    assert override.status_code == 403
