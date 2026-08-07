"""Route smoke tests for POST /stats/descriptive and POST /stats/baseline."""

from fastapi.testclient import TestClient

from sigma_engine.main import app

client = TestClient(app)


def test_descriptive_route_returns_provenance_stamped_result():
    resp = client.post("/stats/descriptive", json={"data": [1, 2, 3, 4, 5]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["value"]["n"] == 5
    assert body["value"]["mean"] == 3.0
    assert body["provenance"]["method"]


def test_descriptive_route_rejects_fewer_than_two_points():
    resp = client.post("/stats/descriptive", json={"data": [1.0]})
    assert resp.status_code == 422


def test_baseline_route_happy_path():
    data = [50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 51]
    resp = client.post(
        "/stats/baseline",
        json={"data": data, "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gate_ok"] is True
    assert body["n"] == 20
    assert "descriptive" in body and body["descriptive"] is not None


def test_baseline_route_honest_exit_on_missing_specs_is_200_not_an_error():
    resp = client.post("/stats/baseline", json={"data": [1, 2, 3], "operational_definition_ok": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["gate_ok"] is False
    assert body["gate_message"]


def test_baseline_route_defaults_rule2_rule3_off():
    data = [50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 49, 51, 50, 49, 51, 48, 52, 51]
    resp = client.post(
        "/stats/baseline",
        json={"data": data, "usl": 100, "lsl": 0, "operational_definition_ok": True},
    )
    body = resp.json()
    assert body["stability"]["value"]["rule2_enabled"] is False
    assert body["stability"]["value"]["rule3_enabled"] is False
