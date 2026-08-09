"""FastAPI sidecar app: /health and /smoke, served over 127.0.0.1 only.

Run directly with `python -m sigma_engine.main --port 8756`, or via the
PyInstaller-built binary (see run_engine.py / sigma_engine.spec), which the
desktop shell spawns as a Tauri sidecar.

M1 adds the Define/Intake engine core (artifacts, prescore, project
storage, gates) as routers included below; /health and /smoke are
untouched per the M1 brief.

M5 unit 1 adds the Layer 2 advisor router (routes/advisor.py): strictly
optional, degrades to a clean typed response with no API key configured,
and otherwise unrelated to every router above it.
"""

from __future__ import annotations

import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__
from .routes import advisor as advisor_routes
from .routes import artifacts as artifacts_routes
from .routes import check_sheet as check_sheet_routes
from .routes import datasets as datasets_routes
from .routes import export as export_routes
from .routes import floorplans as floorplans_routes
from .routes import gates as gates_routes
from .routes import hypothesis as hypothesis_routes
from .routes import prescore as prescore_routes
from .routes import projects as projects_routes
from .routes import stats as stats_routes
from .routes import time_study as time_study_routes
from .smoke import compute_smoke_result

app = FastAPI(title="Sigma AI Engine", version=__version__)

# The packaged desktop app's webview makes cross-origin requests to this
# engine (its origin is http://tauri.localhost on Windows / tauri://localhost
# elsewhere; the engine's is 127.0.0.1:PORT), so the browser sends a CORS
# preflight OPTIONS before every real call. Without this middleware FastAPI
# answers OPTIONS with 405 and the preflight fails -- the exact "engine
# didn't start" symptom the sidecar log surfaced on the first installed
# build (the dev browser never hit this because Vite proxies same-origin, so
# no test exercised it). The engine binds 127.0.0.1 only and uses no
# cookies/credentials, so a permissive origin policy is safe here: nothing
# off the local loopback can reach it regardless.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_routes.router)
app.include_router(advisor_routes.router)
app.include_router(artifacts_routes.router)
app.include_router(prescore_routes.router)
app.include_router(gates_routes.router)
app.include_router(export_routes.router)
app.include_router(stats_routes.router)
app.include_router(hypothesis_routes.router)
app.include_router(datasets_routes.router)
app.include_router(floorplans_routes.router)
app.include_router(check_sheet_routes.router)
app.include_router(time_study_routes.router)

# Must match the port the Tauri sidecar passes via --port (desktop/src-tauri/src/lib.rs).
DEFAULT_PORT = 8756


class HealthResponse(BaseModel):
    status: str
    engine_version: str


class SmokeResponse(BaseModel):
    dataset: str
    n: int
    mean: float
    stdev: float
    certified_mean: float
    certified_stdev: float
    match: bool


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", engine_version=__version__)


@app.get("/smoke", response_model=SmokeResponse)
def smoke() -> SmokeResponse:
    return SmokeResponse(**compute_smoke_result())


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(prog="sigma-engine")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port to bind on 127.0.0.1"
    )
    args = parser.parse_args()
    # 127.0.0.1 only, never 0.0.0.0 -- this sidecar is never meant to be
    # reachable off the local machine.
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
