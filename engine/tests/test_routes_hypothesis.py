"""Route tests for T-17: /stats/hypothesis/route, /stats/hypothesis/run
(raw-array and dataset-column paths), generic artifact CRUD via
ARTIFACT_REGISTRY (same contract as T-01..T-12), and /prescore/T-17."""

import base64

import pytest
from fastapi.testclient import TestClient

from factories import make_hypothesis
from sigma_engine.main import app

NIST_PROCESS_1_OLD = [32, 37, 35, 28, 41, 44, 35, 31, 34, 38, 42]
NIST_PROCESS_2_NEW = [36, 31, 30, 31, 34, 36, 29, 32, 31]

WELCH_QUESTION = {
    "question_text": "Is process 2 faster than process 1?",
    "comparison_type": "two_independent",
    "groups": [{"label": "Process 1", "values": NIST_PROCESS_1_OLD}, {"label": "Process 2", "values": NIST_PROCESS_2_NEW}],
}

TINY_EXIT06_QUESTION = {
    "question_text": "tiny groups",
    "comparison_type": "two_independent",
    "groups": [{"label": "A", "values": [1, 2, 3]}, {"label": "B", "values": [4, 5, 6]}],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id: str = "proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Test", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


# --- /stats/hypothesis/route -------------------------------------------------


def test_route_endpoint_returns_the_printed_decision_tree(client):
    resp = client.post("/stats/hypothesis/route", json={"question": WELCH_QUESTION})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["route"] == "welch_two_sample_t"
    assert body["exit"] is None
    assert len(body["decision_path"]) > 0
    assert all({"question", "answer", "branch"} <= set(node.keys()) for node in body["decision_path"])


def test_route_endpoint_never_computes_a_statistic():
    """Routing-only means no `statistic`/`p_value` keys anywhere in the
    response -- it's a decision object, not a result."""
    c = TestClient(app)
    resp = c.post("/stats/hypothesis/route", json={"question": WELCH_QUESTION})
    body = resp.json()
    assert "statistic" not in body and "p_value" not in body


def test_route_endpoint_exit06(client):
    resp = client.post("/stats/hypothesis/route", json={"question": TINY_EXIT06_QUESTION})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["route"] is None
    assert body["exit"]["exit_id"] == "EXIT-06"


def test_route_endpoint_malformed_question_is_422(client):
    bad = dict(WELCH_QUESTION, groups=[{"label": "only one", "values": [1, 2, 3, 4, 5, 6, 7, 8]}])
    resp = client.post("/stats/hypothesis/route", json={"question": bad})
    assert resp.status_code == 422


# --- /stats/hypothesis/run ---------------------------------------------------


def test_run_endpoint_happy_welch(client):
    resp = client.post("/stats/hypothesis/run", json={"question": WELCH_QUESTION})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["refused"] is False
    assert body["routing"]["route"] == "welch_two_sample_t"
    assert body["result"]["value"]["statistic"] == pytest.approx(2.2694, abs=1e-4)
    assert body["result"]["value"]["p_value"] < 0.05
    assert body["result"]["provenance"]["method"]  # provenance-stamped


def test_run_endpoint_exit06_refusal(client):
    resp = client.post("/stats/hypothesis/run", json={"question": TINY_EXIT06_QUESTION})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["refused"] is True
    assert body["result"] is None
    assert body["routing"]["exit"]["exit_id"] == "EXIT-06"


def test_run_endpoint_anova_carries_exit13(client):
    q = {
        "question_text": "do the 3 temperatures differ?", "comparison_type": "multi_group",
        "groups": [
            {"label": "Level 1", "values": [6.9, 5.4, 5.8, 4.6, 4.0]},
            {"label": "Level 2", "values": [8.3, 6.8, 7.8, 9.2, 6.5]},
            {"label": "Level 3", "values": [8.0, 10.5, 8.1, 6.9, 9.3]},
        ],
    }
    resp = client.post("/stats/hypothesis/run", json={"question": q})
    body = resp.json()
    assert body["result"]["value"]["exit13"]["exit_id"] == "EXIT-13"


# --- Dataset-column path (mirrors /stats/baseline's dataset provenance contract) ---


def _upload_csv(client, project_id: str, filename: str, values) -> dict:
    csv_text = "value\n" + "\n".join(str(v) for v in values)
    resp = client.post(
        f"/project/{project_id}/datasets",
        json={"source_filename": filename, "content_base64": base64.b64encode(csv_text.encode()).decode(), "created_at": "2026-08-07T00:00:00"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_run_endpoint_dataset_sourced_groups(client):
    _create_project(client)
    da = _upload_csv(client, "proj-1", "a.csv", NIST_PROCESS_1_OLD)
    db = _upload_csv(client, "proj-1", "b.csv", NIST_PROCESS_2_NEW)

    body = {
        "question": {"question_text": "Is A faster than B?", "comparison_type": "two_independent", "groups": [{"label": "A"}, {"label": "B"}]},
        "project_id": "proj-1",
        "group_columns": {"0": {"dataset_id": da["dataset_id"], "column": "value"}, "1": {"dataset_id": db["dataset_id"], "column": "value"}},
    }
    resp = client.post("/stats/hypothesis/run", json=body)
    assert resp.status_code == 200, resp.text
    out = resp.json()
    assert out["routing"]["route"] == "welch_two_sample_t"
    assert out["result"]["value"]["statistic"] == pytest.approx(2.2694, abs=1e-4)
    assert len(out["dataset_provenance"]) == 2
    assert out["dataset_provenance"][0]["dataset_sha256"]
    assert out["dataset_provenance"][0]["row_count_used"] == 11


def test_run_endpoint_missing_project_id_with_dataset_ref_is_422(client):
    body = {"question": {"question_text": "q", "comparison_type": "two_independent", "groups": [{"label": "A"}, {"label": "B"}]},
            "group_columns": {"0": {"dataset_id": "does-not-matter", "column": "value"}}}
    resp = client.post("/stats/hypothesis/run", json=body)
    assert resp.status_code == 422


def test_run_endpoint_unknown_dataset_is_404(client):
    _create_project(client)
    body = {
        "question": {"question_text": "q", "comparison_type": "one_sample_vs_target", "sample": [], "target": 0.0},
        "project_id": "proj-1", "sample_column": {"dataset_id": "nonexistent", "column": "value"},
    }
    resp = client.post("/stats/hypothesis/run", json=body)
    assert resp.status_code == 404


# --- Generic artifact CRUD (registry-driven, same contract as T-01..T-12) --


def test_validate_and_save_hypothesis_artifact(client):
    _create_project(client)
    ok = client.post("/artifacts/T-17/validate", json=make_hypothesis())
    assert ok.status_code == 200, ok.text
    assert ok.json()["valid"] is True
    assert ok.json()["artifact"]["routing"]["route"] == "welch_two_sample_t"

    save = client.post("/project/proj-1/artifacts/T-17", json=make_hypothesis())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "hyp-001", "tool_id": "T-17", "version": 1}


def test_save_rejects_a_malformed_question(client):
    _create_project(client)
    bad = make_hypothesis(question={"question_text": "q", "comparison_type": "association_categorical"})  # missing contingency_table
    resp = client.post("/project/proj-1/artifacts/T-17", json=bad)
    assert resp.status_code == 422


def test_load_saved_hypothesis_artifact_round_trips(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-17", json=make_hypothesis())
    loaded = client.get("/project/proj-1/artifacts/hyp-001")
    assert loaded.status_code == 200, loaded.text
    assert loaded.json()["routing"]["route"] == "welch_two_sample_t"


def test_prescore_hypothesis_via_route(client):
    _create_project(client)
    client.post("/project/proj-1/artifacts/T-17", json=make_hypothesis())
    prescore = client.post("/prescore/T-17", json=make_hypothesis())
    assert prescore.status_code == 200, prescore.text
    check_ids = {c["check_id"] for c in prescore.json()}
    assert check_ids == {"routing_recorded", "route_tamper_check", "declared_primary_present", "exit_honored", "tests_run_vs_declared_primary"}
    assert all(c["status"] == "pass" for c in prescore.json())
