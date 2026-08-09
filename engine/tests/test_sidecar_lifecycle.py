"""The sidecar's process lifecycle -- the half no HTTP test can see.

WHY THIS EXISTS: the desktop app spawns this engine as a Tauri sidecar and
is the only thing that ever stops it. Running the BUILT Linux app headless
showed that it doesn't: after the window closed and the app process was
gone, `curl 127.0.0.1:8756/health` still answered. Two causes, both
invisible to every test that imports `app` and calls it over TestClient:

  1. PyInstaller ONEFILE runs a bootloader process that forks the real
     Python interpreter as its own child. Tauri's CommandChild::kill()
     SIGKILLs the bootloader, and SIGKILL cannot be forwarded, so the
     Python process is orphaned and keeps holding the port.
  2. An orphan that keeps answering /health is worse than a dead one: the
     next launch's readiness gate passes against the STALE engine while its
     own fresh sidecar dies on "address already in use".

The fix is the --shutdown-on-stdin-eof lifeline (sigma_engine.main), and
these tests pin the two things that can silently break it: the flag's
existence/spelling (renaming it means the installed app's sidecar refuses
to start) and the fact that EOF on stdin actually stops a real, running
server process.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from sigma_engine.main import build_arg_parser

ENGINE_ROOT = Path(__file__).resolve().parents[1]

# The exact argv desktop/src-tauri/src/lib.rs builds. Any drift here is a
# sidecar that exits immediately with "unrecognized arguments" in a log the
# user never opens -- the same failure shape as the two bugs that already
# cost an installer build each.
DESKTOP_SIDECAR_ARGS = ["--port", "8756", "--shutdown-on-stdin-eof"]


def test_cli_accepts_exactly_what_the_desktop_app_passes():
    args = build_arg_parser().parse_args(DESKTOP_SIDECAR_ARGS)
    assert args.port == 8756
    assert args.shutdown_on_stdin_eof is True


def test_lifeline_is_off_by_default():
    """A hand-run engine (docs, packaged-sweep, `python -m sigma_engine.main`)
    must not inherit the flag: its stdin may be /dev/null, which is EOF at
    once, which would look like an engine that refuses to start."""
    args = build_arg_parser().parse_args(["--port", "8000"])
    assert args.shutdown_on_stdin_eof is False


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_serving(port: int, proc: subprocess.Popen, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"engine exited early with code {proc.returncode}")
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    pytest.fail(f"engine never bound 127.0.0.1:{port}")


def test_closing_stdin_stops_a_running_engine():
    """The end-to-end behaviour the app depends on: close the write end of
    the pipe (what the OS does for us when the app process dies, for any
    reason including a crash) and the engine goes away on its own."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "sigma_engine.main", "--port", str(port), "--shutdown-on-stdin-eof"],
        cwd=ENGINE_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_serving(port, proc)
        assert proc.stdin is not None
        proc.stdin.close()  # <- the only signal; nothing else is sent
        # Generous vs. the ~100ms uvicorn should_exit tick, tight vs. the
        # 10s hard backstop, so a pass here means the GRACEFUL path ran.
        proc.wait(timeout=8)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def test_engine_without_the_flag_ignores_a_closed_stdin():
    """The complement: a hand-run engine must survive stdin closing, or
    every doc'd `sigma-engine --port 8000 &` invocation would die."""
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "sigma_engine.main", "--port", str(port)],
        cwd=ENGINE_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_until_serving(port, proc)
        assert proc.stdin is not None
        proc.stdin.close()
        time.sleep(2)
        assert proc.poll() is None, "engine exited on stdin EOF without being asked to"
    finally:
        proc.kill()
        proc.wait(timeout=10)
