"""The engine must not take orders from other websites.

allow_origins=["*"] + allow_private_network=True is what the packaged app
needs, and it is also what would let any page a user visits while the app is
open script requests to 127.0.0.1:PORT -- reading the project list (which
carries local folder paths) and hitting DELETE /project/{id}. Binding
loopback does not help: the attacking JS runs in the user's own browser,
which is on loopback. reject_foreign_origins closes that; these pin it.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from sigma_engine.main import app
from sigma_engine.project_store import ProjectStore
from sigma_engine.routes.deps import get_store


@pytest.fixture()
def client(tmp_path):
    store = ProjectStore(tmp_path / "projects")
    app.dependency_overrides[get_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_store, None)


# What a real webview / probe / diagnostics browser sends.
ALLOWED = [
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://tauri.localhost:4609",   # a browser probe's random port
    "tauri://localhost",
    "http://localhost:1420",         # tauri dev
    "http://127.0.0.1:8756",
]

# What a hostile page sends.
FOREIGN = [
    "https://evil.com",
    "http://evil.com",
    "https://tauri.localhost.evil.com",   # suffix trick
    "http://localhost.evil.com",
    "null",
]


@pytest.mark.parametrize("origin", ALLOWED)
def test_the_apps_own_origins_are_allowed(client, origin):
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 200, f"{origin} should be allowed"


@pytest.mark.parametrize("origin", FOREIGN)
def test_a_foreign_origin_is_refused(client, origin):
    r = client.get("/health", headers={"Origin": origin})
    assert r.status_code == 403, f"{origin} should be refused"


@pytest.mark.parametrize("origin", FOREIGN)
def test_a_foreign_origin_cannot_reach_a_destructive_route(client, origin):
    # The one that actually matters: a project delete driven from evil.com.
    r = client.delete("/project/anything", headers={"Origin": origin})
    assert r.status_code == 403


def test_no_origin_header_passes(client):
    """curl, the boot-retry health check, every non-browser caller -- none
    of which a hostile page can forge, since browsers always attach Origin
    on a cross-origin fetch. Blocking these would break the sidecar's own
    startup probe."""
    assert client.get("/health").status_code == 200


def test_a_foreign_origin_is_refused_even_on_a_route_that_would_404(client):
    """The guard runs before routing, so an attacker cannot distinguish a
    blocked-but-real route from a nonexistent one -- and cannot use the
    engine to probe which project ids exist."""
    r = client.get("/project/some-secret-name", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403
