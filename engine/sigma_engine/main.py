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
import logging
import os
import sys
import threading
import time
import traceback
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import __version__
from .project_store import UnsafeIdError
from .routes import advisor as advisor_routes
from .routes import artifacts as artifacts_routes
from .routes import check_sheet as check_sheet_routes
from .routes import datasets as datasets_routes
from .routes import drafts as drafts_routes
from .routes import export as export_routes
from .routes import floorplans as floorplans_routes
from .routes import gates as gates_routes
from .routes import hypothesis as hypothesis_routes
from .routes import prescore as prescore_routes
from .routes import projects as projects_routes
from .routes import stats as stats_routes
from .routes import time_study as time_study_routes
from .smoke import compute_smoke_result

if TYPE_CHECKING:  # uvicorn is imported lazily in main() -- it is not needed
    import uvicorn  # to import this module, only to serve it.

app = FastAPI(title="Sigma AI Engine", version=__version__)

logger = logging.getLogger("sigma_engine")


# Registered BEFORE CORSMiddleware below, which matters: Starlette's
# add_middleware inserts at the front of the user stack, so the LAST one
# added is the outermost. Being inside CORSMiddleware is the whole point of
# this handler.
#
# Why it exists: an unhandled exception in a route is normally turned into a
# 500 by Starlette's ServerErrorMiddleware, which sits ABOVE the user
# middleware stack -- so that 500 skips CORSMiddleware entirely and reaches
# the packaged webview with no Access-Control-Allow-Origin. The browser then
# blocks it, fetch() rejects, and desktop/src/api/client.ts's request()
# reports "Could not reach the engine (...)" -- i.e. a real server bug is
# shown to the user as a transport failure, which is the same misdiagnosis
# class as the "engine didn't start" report that cost the first installed
# build. Through the Vite dev proxy the identical 500 renders correctly with
# its detail, which is precisely why no dev-mode test could catch this.
#
# Catching here (inside CORS) means the 500 carries CORS headers and the app
# renders it as the server error it is. The traceback is still logged, so
# the sidecar log keeps the full diagnostic it had before.
@app.middleware("http")
async def surface_server_errors_with_cors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:  # noqa: BLE001 -- deliberately broad; re-raising would
        # hand the response back to ServerErrorMiddleware, outside CORS.
        logger.error(
            "Unhandled error handling %s %s\n%s",
            request.method,
            request.url.path,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "The engine hit an internal error. See the sidecar log for the traceback."},
        )


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
#
# allow_private_network=True is not optional decoration. Chromium's Private
# Network Access rules make a page fetching a MORE-private address space
# (here: loopback) send `Access-Control-Request-Private-Network: true` on the
# preflight, and Starlette's CORSMiddleware DEFAULTS THAT TO FALSE -- it
# answers such a preflight with 400 "Disallowed CORS private-network", which
# the app reports as "Could not reach the engine". The packaged app is
# exactly this shape (webview page -> 127.0.0.1 sidecar) and, on Windows,
# its page is served by WebView2's custom scheme handler, which has no IP
# for Chromium to classify by. Nothing in dev sends that request header, so
# a 400 here is invisible until it is an installed app in a user's hands --
# the same shape as the two bugs that already cost a build each.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

@app.exception_handler(UnsafeIdError)
def _unsafe_id(_request: Request, exc: UnsafeIdError) -> JSONResponse:
    """A project or artifact id that cannot be a folder name is the caller's
    mistake, not the engine falling over. Most routes already map ValueError
    to 422 themselves and never reach here; this catches the rest so a
    crafted id is never a 500."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


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
app.include_router(drafts_routes.router)

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


def build_arg_parser() -> argparse.ArgumentParser:
    """The sidecar's CLI. Split out from main() so a test can assert the
    exact flags desktop/src-tauri/src/lib.rs passes -- a rename here is a
    sidecar that refuses to start in the installed app, with "unrecognized
    arguments" buried in a log the user never opens."""
    parser = argparse.ArgumentParser(prog="sigma-engine")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port to bind on 127.0.0.1"
    )
    parser.add_argument(
        "--shutdown-on-stdin-eof",
        action="store_true",
        help=(
            "Exit when stdin reaches EOF. The desktop app holds the write end of "
            "this pipe, so EOF means the app is gone and this engine must not "
            "outlive it. Off by default: a hand-run engine with stdin on "
            "/dev/null would otherwise exit instantly."
        ),
    )
    return parser


def _exit_when_stdin_closes(server: uvicorn.Server) -> None:
    """Block on stdin until EOF, then ask uvicorn to stop.

    WHY THIS EXISTS: the app spawns this engine through Tauri's sidecar
    plugin, and the PyInstaller ONEFILE bootloader is a *second* process --
    the bootloader forks the real Python interpreter as its own child. Tauri's
    CommandChild::kill() sends SIGKILL to the bootloader only, which cannot be
    forwarded, so the Python process is orphaned, keeps serving, and keeps
    holding 127.0.0.1:8756 forever. Verified in a real headless run of the
    built app: after the window closed, the app process was gone and
    `curl 127.0.0.1:8756/health` still answered.

    That orphan is not cosmetic. The next launch's fresh sidecar cannot bind
    the port and dies, while the stale one still answers /health -- so the
    readiness gate passes and the new UI silently runs against the PREVIOUS
    version's engine. On Windows it also pins sigma-engine.exe open against
    the installer during an upgrade.

    stdin is the fix because it needs no platform code and survives an
    ungraceful death: the app owns the write end, the OS closes it when the
    app process exits for ANY reason (clean quit, crash, kill -9), and the
    bootloader passes the same handle down to this process. EOF here is
    therefore an exact, portable "my app is gone" signal on Windows, macOS,
    and Linux alike.
    """
    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:  # no stdin at all (windowed build) -- nothing to watch
        return
    try:
        while stream.read(1):
            pass
    except Exception:  # noqa: BLE001 -- a broken pipe is EOF by another name
        pass
    logger.info("stdin closed: the desktop app is gone, shutting the engine down")
    server.should_exit = True
    # Backstop: uvicorn checks should_exit on a ~100ms tick, so a clean stop
    # lands well inside this window. If something is wedged (a hung request
    # holding the loop), exit anyway rather than become the orphan this whole
    # function exists to prevent. Every project write is atomic
    # (project_store._atomic_write_json), so a hard exit cannot corrupt state.
    time.sleep(10)
    os._exit(0)


def main() -> None:
    import uvicorn

    args = build_arg_parser().parse_args()
    # 127.0.0.1 only, never 0.0.0.0 -- this sidecar is never meant to be
    # reachable off the local machine.
    config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="info")
    server = uvicorn.Server(config)
    if args.shutdown_on_stdin_eof:
        threading.Thread(
            target=_exit_when_stdin_closes, args=(server,), daemon=True
        ).start()
    server.run()


if __name__ == "__main__":
    main()
