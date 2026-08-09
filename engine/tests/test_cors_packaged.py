"""CORS behaviour the PACKAGED desktop app depends on, and nothing else does.

The packaged webview's origin is http://tauri.localhost (Windows) /
tauri://localhost (mac), while this engine answers on 127.0.0.1:8756 -- so
every call the installed app makes is cross-origin and the browser refuses
to hand the app any response that doesn't carry CORS headers. In dev the
Vite dev server proxies the engine same-origin, so none of this is
exercised: that gap is exactly how the first installed build shipped with
no CORS middleware at all and reported "the engine didn't start".

These tests pin the two halves that the desktop sweep
(desktop/tools/packaged-sweep.mjs) can only assert from the browser side:
the preflight contract, and the fact that EVERY response class -- success,
4xx refusal, 404, and an unhandled 500 -- carries the header. The 500 case
is the one a browser test cannot manufacture without shipping a crash route
in production code, so it lives here.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sigma_engine.main import app

# The real Windows packaged webview origin. Any origin works with the
# permissive policy; using the true one keeps the intent readable.
PACKAGED_ORIGIN = "http://tauri.localhost"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    # raise_server_exceptions=False so an unhandled route error produces the
    # real 500 response the browser would see, instead of re-raising into
    # the test.
    return TestClient(app, raise_server_exceptions=False)


def test_preflight_on_a_json_post_is_answered_not_405(client):
    """The exact call that failed for the first installed user: a JSON POST
    from the webview preflights, and with no CORS middleware FastAPI
    answered OPTIONS with 405."""
    resp = client.options(
        "/project/create",
        headers={
            "Origin": PACKAGED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert "content-type" in resp.headers["access-control-allow-headers"].lower()


def test_private_network_preflight_is_granted_when_asked(client):
    """The webview page fetching 127.0.0.1 is a Private Network Access
    request in Chromium's model. If the browser asks, the engine must grant
    it, or every call fails in the installed app and nowhere else."""
    resp = client.options(
        "/project/create",
        headers={
            "Origin": PACKAGED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
            "Access-Control-Request-Private-Network": "true",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers.get("access-control-allow-private-network") == "true"


def test_private_network_header_absent_when_not_requested(client):
    """Inert everywhere else: the header only appears when the browser asked
    for it, so nothing about ordinary requests changes."""
    resp = client.options(
        "/project/create",
        headers={
            "Origin": PACKAGED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-private-network" not in resp.headers
    resp_get = client.get("/health", headers={"Origin": PACKAGED_ORIGIN})
    assert "access-control-allow-private-network" not in resp_get.headers


def test_success_response_carries_cors_header(client):
    resp = client.get("/health", headers={"Origin": PACKAGED_ORIGIN})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_deliberate_refusal_body_is_readable_cross_origin(client):
    """A 422 the UI is supposed to RENDER (the EXIT refusals) must carry the
    header, or the browser blocks the body and the app shows a transport
    failure instead of the named refusal."""
    resp = client.post(
        "/artifacts/T-03/validate",
        json={"nonsense": True},
        headers={"Origin": PACKAGED_ORIGIN},
    )
    assert resp.status_code == 422
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_404_carries_cors_header(client):
    resp = client.get("/no-such-route", headers={"Origin": PACKAGED_ORIGIN})
    assert resp.status_code == 404
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_unhandled_500_carries_cors_header(client):
    """The regression guard for surface_server_errors_with_cors (main.py).

    Starlette's ServerErrorMiddleware sits ABOVE the user middleware stack,
    so without that handler a 500 skips CORSMiddleware, arrives header-less,
    and desktop/src/api/client.ts reports it as "Could not reach the engine"
    -- a real server bug disguised as the engine being down, which is the
    misdiagnosis that already cost one installer build. A temporary route is
    registered here (and removed again) so production code never ships a
    crash endpoint.
    """

    @app.get("/__test_unhandled_error__")
    def _boom() -> None:  # pragma: no cover - the raise is the point
        raise ValueError("deliberate unhandled error")

    try:
        resp = client.get("/__test_unhandled_error__", headers={"Origin": PACKAGED_ORIGIN})
        assert resp.status_code == 500
        assert resp.headers.get("access-control-allow-origin") == "*", (
            "a 500 with no Access-Control-Allow-Origin is invisible to the packaged webview"
        )
        # Still a JSON body the app can render, not an HTML traceback page.
        assert "detail" in resp.json()
    finally:
        app.router.routes = [
            r for r in app.router.routes if getattr(r, "path", None) != "/__test_unhandled_error__"
        ]
        app.openapi_schema = None


def test_every_registered_route_answers_a_preflight(client):
    """Blanket coverage so a NEW route cannot ship without CORS: whatever is
    in the app's route table must answer OPTIONS, not 405."""
    # Enumerated from the OpenAPI schema rather than app.router.routes:
    # FastAPI wraps included routers in an opaque _IncludedRouter whose own
    # `path`/`methods` are None, so walking the route list silently sees
    # only /health and /smoke. The schema is the honest full list.
    seen = 0
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            if method.upper() in {"HEAD", "OPTIONS"}:
                continue
            # Path params filled with a value that cannot exist -- the
            # preflight never reaches the handler anyway.
            concrete = path
            while "{" in concrete:
                start = concrete.index("{")
                end = concrete.index("}", start)
                concrete = concrete[:start] + "cors-preflight-probe" + concrete[end + 1 :]
            resp = client.options(
                concrete,
                headers={
                    "Origin": PACKAGED_ORIGIN,
                    "Access-Control-Request-Method": method.upper(),
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            assert resp.status_code == 200, f"{method.upper()} {path} preflight returned {resp.status_code}"
            assert resp.headers.get("access-control-allow-origin") == "*", (
                f"{method.upper()} {path} preflight has no CORS header"
            )
            seen += 1
    assert seen >= 25, f"expected the route table to yield a substantial preflight set, got {seen}"
