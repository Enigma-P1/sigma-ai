"""Route tests for T-12 (generic artifact CRUD via ARTIFACT_REGISTRY) and
the cross-tool capability-language loop the task brief calls for: a failed
T-12 flags BaselineResult.measurement_check, the gates.py hard block names
EXIT-02, and a passing T-12 re-run clears both."""

import pytest
from fastapi.testclient import TestClient

from factories import make_attribute_msa, make_continuous_msa
from sigma_engine.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id: str = "proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


# --- T-12 generic CRUD (registry-driven, same contract as T-01..T-05) ------

def test_validate_and_save_continuous_msa(client):
    _create_project(client)
    ok = client.post("/artifacts/T-12/validate", json=make_continuous_msa())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True
    assert ok.json()["artifact"]["result"]["verdict"] in ("acceptable", "marginal", "fail")

    save = client.post("/project/proj-1/artifacts/T-12", json=make_continuous_msa())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "msa-001", "tool_id": "T-12", "version": 1}


def test_save_attribute_msa_and_prescore(client):
    _create_project(client)
    save = client.post("/project/proj-1/artifacts/T-12", json=make_attribute_msa())
    assert save.status_code == 200, save.text

    prescore = client.post("/prescore/T-12", json=make_attribute_msa())
    assert prescore.status_code == 200, prescore.text
    check_ids = {c["check_id"] for c in prescore.json()}
    assert "verdict_recorded" in check_ids
    assert "result_matches_inputs" in check_ids


def test_save_rejects_invalid_msa(client):
    _create_project(client)
    bad = make_continuous_msa()
    bad["continuous_items"] = []
    resp = client.post("/project/proj-1/artifacts/T-12", json=bad)
    assert resp.status_code == 422


# --- The capability-language loop: fail -> flag -> re-run -> clear --------

# Coarse-increment, low-distinct-value fixture: resolution pre-check fails
# outright, so the verdict is "fail" without needing to fight the %EV bands.
FAILING_MSA = make_continuous_msa(
    artifact_id="msa-loop",
    gauge_increment=5.0,  # 5/20 = 25% of the tolerance span -- fails the 1/10 ceiling
    usl=20.0, lsl=0.0,
    continuous_items=[{"item_id": "only-item", "readings": [10.0, 10.0]}],  # also < 5 distinct values
)

# Fine-increment, well-behaved fixture: passes resolution and reads a tight
# repeatability% comfortably inside the acceptable band.
PASSING_MSA = make_continuous_msa(artifact_id="msa-loop")

BASELINE_DATA = [50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 51]


def test_fail_then_baseline_flagged_then_rerun_pass_then_flag_clears(client):
    _create_project(client, "proj-loop")
    failing_save = client.post("/project/proj-loop/artifacts/T-12", json=FAILING_MSA)
    assert failing_save.status_code == 200, failing_save.text

    # 1. Failed check -> baseline flagged.
    baseline_after_fail = client.post(
        "/stats/baseline",
        json={"data": BASELINE_DATA, "project_id": "proj-loop", "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    assert baseline_after_fail.status_code == 200, baseline_after_fail.text
    body = baseline_after_fail.json()
    assert body["measurement_check"] == "failed"
    assert body["capability"] is None
    assert body["sigma"] is None
    assert "EXIT-02" in body["exits"]

    # 2. gates.py hard-blocks capability language, reason names EXIT-02.
    gate = client.post(
        "/gates/check", json={"gate_id": "measure_capability_language_requires_msa_pass", "project_id": "proj-loop"}
    )
    assert gate.status_code == 200, gate.text
    assert gate.json()["status"] == "HARD_BLOCK"
    assert "EXIT-02" in gate.json()["reason"]

    # 3. Re-run T-12 with a passing study (a new version of the same artifact_id).
    passing_save = client.post("/project/proj-loop/artifacts/T-12", json=PASSING_MSA)
    assert passing_save.status_code == 200, passing_save.text
    assert passing_save.json()["version"] == 2  # same artifact_id, new version -- a genuine re-run, not a fresh one

    # 4. Flag clears on both the baseline result and the gate.
    baseline_after_pass = client.post(
        "/stats/baseline",
        json={"data": BASELINE_DATA, "project_id": "proj-loop", "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    assert baseline_after_pass.status_code == 200, baseline_after_pass.text
    body2 = baseline_after_pass.json()
    assert body2["measurement_check"] is None
    assert body2["capability"] is not None
    assert "EXIT-02" not in body2["exits"]

    gate_after_pass = client.post(
        "/gates/check", json={"gate_id": "measure_capability_language_requires_msa_pass", "project_id": "proj-loop"}
    )
    assert gate_after_pass.json()["status"] == "CLEAR"


def test_baseline_without_project_id_never_consults_msa(client):
    """The raw-array path with no project_id is unaffected -- there is
    nothing to consult, and that's honest, not a silent failure."""
    resp = client.post(
        "/stats/baseline",
        json={"data": BASELINE_DATA, "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["measurement_check"] is None
