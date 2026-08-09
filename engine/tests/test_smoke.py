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


# The packaged desktop webview is a different origin from the 127.0.0.1
# engine, so every real call is preceded by a CORS preflight OPTIONS. These
# pin the CORSMiddleware that answers it -- without it the preflight got 405
# and the installed app read the engine as "not started" (main.py's comment
# has the full story). A cross-origin header is required to trigger the
# middleware's preflight handling.
_WEBVIEW_ORIGIN = "http://tauri.localhost"


def test_cors_preflight_on_health_is_allowed_not_405():
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": _WEBVIEW_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] in ("*", _WEBVIEW_ORIGIN)


def test_cors_preflight_on_a_post_route_is_allowed():
    # POST /project/create is the call that failed first on v0.1.0; its
    # preflight must clear too, not just the health poll's.
    client = TestClient(app)
    response = client.options(
        "/project/create",
        headers={
            "Origin": _WEBVIEW_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] in ("*", _WEBVIEW_ORIGIN)


def test_actual_cross_origin_get_carries_allow_origin_header():
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": _WEBVIEW_ORIGIN})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] in ("*", _WEBVIEW_ORIGIN)
