"""Assert the smoke calc matches NIST StRD certified values, and that the API wires it up."""

from fastapi.testclient import TestClient

from sigma_engine.main import app
from sigma_engine.nist_lew import CERTIFIED_MEAN, CERTIFIED_STDEV, DATA
from sigma_engine.smoke import RELATIVE_TOLERANCE, compute_smoke_result


def test_dataset_has_200_observations():
    assert len(DATA) == 200


def test_mean_matches_certified_value():
    result = compute_smoke_result()
    rel_diff = abs(result["mean"] - CERTIFIED_MEAN) / abs(CERTIFIED_MEAN)
    assert rel_diff <= RELATIVE_TOLERANCE


def test_stdev_matches_certified_value():
    result = compute_smoke_result()
    rel_diff = abs(result["stdev"] - CERTIFIED_STDEV) / abs(CERTIFIED_STDEV)
    assert rel_diff <= RELATIVE_TOLERANCE


def test_smoke_result_reports_match_true():
    result = compute_smoke_result()
    assert result["match"] is True
    assert result["dataset"] == "Lew"
    assert result["n"] == 200


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["engine_version"]


def test_smoke_endpoint_returns_match_true():
    client = TestClient(app)
    response = client.get("/smoke")
    assert response.status_code == 200
    body = response.json()
    assert body["match"] is True
    assert body["dataset"] == "Lew"
    assert body["n"] == 200
    assert body["mean"] == compute_smoke_result()["mean"]
