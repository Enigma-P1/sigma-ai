"""Thin HTTP client for the live Sigma AI engine.

Deliberately dumb: every call returns an EngineResponse (status_code +
parsed JSON body) rather than raising on a non-2xx status. A 422 with a
named EXIT (T-12's EXIT-02, T-19's EXIT-10, ...) is EXPECTED engine
behavior for several scripted steps in these scenarios, not a harness
bug -- the driver decides what's a legitimate response and what's a real
failure, this client just fetches.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class EngineResponse:
    status_code: int
    body: Any  # parsed JSON (dict/list) or, for a body-less response, None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class EngineError(RuntimeError):
    """Raised only when the driver explicitly demands a 2xx (via `expect_ok`)
    and didn't get one -- not raised by plain post()/get() calls."""

    def __init__(self, method: str, path: str, resp: EngineResponse) -> None:
        self.method = method
        self.path = path
        self.resp = resp
        super().__init__(f"{method} {path} -> {resp.status_code}: {resp.body!r}")


class EngineClient:
    def __init__(
        self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0, *, transport: httpx.BaseTransport | None = None,
    ) -> None:
        # `transport` lets tests swap in httpx.MockTransport (this
        # codebase's own convention -- see engine/tests/test_advisor_client.py's
        # module docstring: "mock the SDK transport ... no real network
        # call ever happens in this file") instead of hitting a live engine.
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "EngineClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def wait_healthy(self, tries: int = 40, delay: float = 0.5) -> None:
        last_exc: Exception | None = None
        for _ in range(tries):
            try:
                r = self._client.get("/health")
                if r.status_code == 200:
                    return
            except httpx.HTTPError as exc:  # pragma: no cover - transient startup
                last_exc = exc
            time.sleep(delay)
        raise RuntimeError(f"engine did not become healthy in time (last error: {last_exc})")

    def get(self, path: str, **kwargs: Any) -> EngineResponse:
        r = self._client.get(path, **kwargs)
        return EngineResponse(status_code=r.status_code, body=_safe_json(r))

    def post(self, path: str, json_body: Any = None, **kwargs: Any) -> EngineResponse:
        r = self._client.post(path, json=json_body, **kwargs)
        return EngineResponse(status_code=r.status_code, body=_safe_json(r))

    def post_ok(self, path: str, json_body: Any = None, **kwargs: Any) -> EngineResponse:
        """post() but raises EngineError on a non-2xx -- for steps where an
        error response would mean the harness itself is broken, not the
        scenario's story (e.g. creating the eval project)."""
        resp = self.post(path, json_body, **kwargs)
        if not resp.ok:
            raise EngineError("POST", path, resp)
        return resp


def _safe_json(r: httpx.Response) -> Any:
    if not r.content:
        return None
    try:
        return r.json()
    except ValueError:
        return {"_non_json_body": r.text}


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
