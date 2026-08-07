"""FastAPI sidecar app: /health and /smoke, served over 127.0.0.1 only.

Run directly with `python -m sigma_engine.main --port 8756`, or via the
PyInstaller-built binary (see run_engine.py / sigma_engine.spec), which the
desktop shell spawns as a Tauri sidecar.
"""

from __future__ import annotations

import argparse

from fastapi import FastAPI
from pydantic import BaseModel

from . import __version__
from .smoke import compute_smoke_result

app = FastAPI(title="Sigma AI Engine", version=__version__)

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
