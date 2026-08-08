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


# ---------------------------------------------------------------------------
# Fix 5 (critic-confirmed): gates.py and stats.py used to pick a DIFFERENT
# "latest" T-12 when a project carries two -- stats.py's _latest_msa_verdict
# returned the first match (alphabetical, since project.json is written
# sort_keys=True), gates.py's _build_snapshot kept overwriting with no
# break (alphabetically-last). Two T-12 artifact_ids, deliberately ordered
# so alphabetically-first is chronologically OLDER: both call paths must
# now agree, and both must land on the NEWER one (ProjectStore.
# latest_artifact_for_tool's shared "updated_at wins" contract), not
# whichever their own old bug happened to prefer.
# ---------------------------------------------------------------------------


def test_gates_and_stats_agree_on_the_latest_of_two_msa_artifacts(client):
    _create_project(client, "proj-two-msa")

    # "msa-a" sorts alphabetically FIRST but is chronologically OLDER and
    # fails (same shape as this file's own FAILING_MSA). "msa-b" sorts
    # alphabetically LAST and is chronologically NEWER and passes (same
    # shape as PASSING_MSA). The old stats.py bug (first match) would have
    # read msa-a's "fail"; the old gates.py bug (last match, no break)
    # would have read whichever artifact_id happened to sort last -- here
    # that's also msa-b, but only by the same alphabetical accident the
    # critic named, not because either old implementation ever compared
    # updated_at. Both routes must now agree, deliberately, on msa-b (the
    # actually-newer one).
    older_failing = make_continuous_msa(
        artifact_id="msa-a", updated_at="2026-08-01T00:00:00",
        gauge_increment=5.0, usl=20.0, lsl=0.0,
        continuous_items=[{"item_id": "only-item", "readings": [10.0, 10.0]}],
    )
    newer_passing = make_continuous_msa(artifact_id="msa-b", updated_at="2026-08-05T00:00:00")

    save_a = client.post("/project/proj-two-msa/artifacts/T-12", json=older_failing)
    assert save_a.status_code == 200, save_a.text
    save_b = client.post("/project/proj-two-msa/artifacts/T-12", json=newer_passing)
    assert save_b.status_code == 200, save_b.text

    older_verdict = client.get("/project/proj-two-msa/artifacts/msa-a").json()["result"]["verdict"]
    newer_verdict = client.get("/project/proj-two-msa/artifacts/msa-b").json()["result"]["verdict"]
    assert older_verdict == "fail"
    assert newer_verdict != "fail"  # the fixture only proves anything if the two genuinely disagree

    # stats.py's path: /stats/baseline only reports measurement_check=="failed"
    # (and refuses capability language) when the CONSULTED verdict is "fail".
    baseline_resp = client.post(
        "/stats/baseline",
        json={"data": BASELINE_DATA, "project_id": "proj-two-msa", "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    assert baseline_resp.status_code == 200, baseline_resp.text
    assert baseline_resp.json()["measurement_check"] is None  # NOT "failed" -- picked msa-b, not msa-a
    assert baseline_resp.json()["capability"] is not None

    # gates.py's path: the same hard gate, same project.
    gate_resp = client.post(
        "/gates/check", json={"gate_id": "measure_capability_language_requires_msa_pass", "project_id": "proj-two-msa"}
    )
    assert gate_resp.status_code == 200, gate_resp.text
    assert gate_resp.json()["status"] == "CLEAR"  # NOT HARD_BLOCK -- picked msa-b too, agreeing with stats.py
