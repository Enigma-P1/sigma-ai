#!/usr/bin/env bash
# RUN THE REAL DESKTOP APP, HEADLESS, AND PROVE IT WORKS.
#
# WHY THIS EXISTS: three bugs reached a real user and each cost a paid
# Windows+Mac installer build, because every test we had stopped at the edge
# of the Tauri shell. tools/smoke-browser.mjs loads the UI from Vite;
# tools/packaged-sweep.mjs reproduces the packaged ORIGIN in Chromium; both
# are browser tests. Neither one compiles the Rust, spawns the sidecar the
# way the app does, creates a real window, or exercises the download handler.
# That layer -- sidecar launch, webview origin/CORS, window creation -- is
# exactly the layer that broke each time.
#
# This script builds nothing. It runs the ALREADY-BUILT Linux binary under
# Xvfb and asserts the things only a real run can show:
#
#   1. the app process starts and stays up;
#   2. a real window exists, with the configured title;
#   3. the sidecar was spawned BY THE APP (a child process, not by us);
#   4. the engine answers on the port the app chose;
#   5. the app's OWN WEBVIEW reached the engine cross-origin -- proven by
#      an OPTIONS preflight answered 200 in the app's sidecar log. A 405
#      there is the bug that shipped in the first installed build, and no
#      browser test can produce this evidence;
#   6. closing the window leaves NO engine process behind and frees the
#      port. An orphaned engine keeps answering /health, so the next
#      launch's readiness gate passes against a STALE engine while its own
#      sidecar dies on "address already in use".
#
# Prerequisites (build these first -- from the repo root):
#     scripts/build-sidecar.sh
#     cd desktop && npm run tauri build -- --bundles deb   # or --no-bundle
#
# Requires: Xvfb, curl. ImageMagick's `import` is optional -- with it, the
# script also writes screenshots for a human to look at, which is how the
# rail-clipping and empty-state defects were found.
#
# Usage:  desktop/tools/run-real-app.sh
# Env:    OUT_DIR (default /tmp/sigma-real-app), DISPLAY_NUM (default :99),
#         SETTLE_SECONDS (default 20 -- the onefile sidecar self-extracts on
#         first launch, so a cold run genuinely needs this).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

APP_BIN="$REPO_ROOT/desktop/src-tauri/target/release/desktop"
OUT_DIR="${OUT_DIR:-/tmp/sigma-real-app}"
DISPLAY_NUM="${DISPLAY_NUM:-:99}"
SETTLE_SECONDS="${SETTLE_SECONDS:-20}"
# Must match SIDECAR_PORT in desktop/src-tauri/src/lib.rs.
ENGINE_PORT=8756
# Tauri v2's app_log_dir on Linux, for identifier com.sigmaai.spike.
SIDECAR_LOG="${XDG_DATA_HOME:-$HOME/.local/share}/com.sigmaai.spike/logs/sidecar.log"
# The window title from desktop/src-tauri/tauri.conf.json.
WINDOW_TITLE="Sigma AI"

FAILURES=0
pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; FAILURES=$((FAILURES + 1)); }

cleanup() {
  [ -n "${APP_PID:-}" ] && kill -9 "$APP_PID" 2>/dev/null
  pkill -f 'release/sigma-engine' 2>/dev/null
  [ -n "${XVFB_PID:-}" ] && kill -9 "$XVFB_PID" 2>/dev/null
  return 0
}
trap cleanup EXIT

if [ ! -x "$APP_BIN" ]; then
  echo "ERROR: no built app at $APP_BIN" >&2
  echo "Build it first: cd desktop && npm run tauri build -- --bundles deb" >&2
  exit 2
fi
command -v Xvfb > /dev/null || { echo "ERROR: Xvfb not installed" >&2; exit 2; }

rm -rf "$OUT_DIR"; mkdir -p "$OUT_DIR"

# --- clean slate ------------------------------------------------------------
# A leftover engine from a previous run would make every check below pass for
# the wrong reason -- that is the whole point of check 6.
pkill -f 'release/desktop' 2>/dev/null
pkill -f 'release/sigma-engine' 2>/dev/null
sleep 1
if curl -fsS -m 2 "http://127.0.0.1:$ENGINE_PORT/health" > /dev/null 2>&1; then
  echo "ERROR: something is already serving 127.0.0.1:$ENGINE_PORT -- this run could not" >&2
  echo "       tell that engine apart from the app's own. Stop it and retry." >&2
  exit 2
fi
rm -f "$SIDECAR_LOG"

# --- X server ---------------------------------------------------------------
rm -f "/tmp/.X${DISPLAY_NUM#:}-lock"; rm -rf "/tmp/.X11-unix/X${DISPLAY_NUM#:}"
Xvfb "$DISPLAY_NUM" -screen 0 1400x900x24 -nolisten tcp > "$OUT_DIR/xvfb.log" 2>&1 &
XVFB_PID=$!
for _ in $(seq 1 50); do
  [ -e "/tmp/.X11-unix/X${DISPLAY_NUM#:}" ] && break
  sleep 0.2
done

# --- launch -----------------------------------------------------------------
echo "== launching $APP_BIN on $DISPLAY_NUM =="
cd "$REPO_ROOT"
env DISPLAY="$DISPLAY_NUM" \
    GDK_BACKEND=x11 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    WEBKIT_DISABLE_COMPOSITING_MODE=1 \
    WEBKIT_DISABLE_DMABUF_RENDERER=1 \
    "$APP_BIN" > "$OUT_DIR/app-run.log" 2>&1 &
APP_PID=$!
sleep "$SETTLE_SECONDS"

echo "== checks =="

# 1. still up
if kill -0 "$APP_PID" 2>/dev/null; then
  pass "app process $APP_PID alive after ${SETTLE_SECONDS}s"
else
  fail "app process exited within ${SETTLE_SECONDS}s -- see $OUT_DIR/app-run.log"
fi

# 2. a real window, with the configured title.
#    NOT `xdotool search --name`: the configured title contains an em dash,
#    so WM_NAME is a UTF8_STRING that xdotool's search path cannot decode
#    and the real window is invisible to it (it finds only GTK's 10x10
#    helper window, named "desktop"). Walking root's children and asking
#    getwindowname -- which reads _NET_WM_NAME -- sees it correctly.
WINDOW_ID=""
if command -v xdotool > /dev/null && command -v xwininfo > /dev/null; then
  for candidate in $(DISPLAY="$DISPLAY_NUM" xwininfo -root -children 2>/dev/null \
      | grep -oE '^\s+0x[0-9a-f]+' | tr -d ' '); do
    name=$(DISPLAY="$DISPLAY_NUM" xdotool getwindowname "$candidate" 2>/dev/null)
    case "$name" in "$WINDOW_TITLE"*) WINDOW_ID="$candidate"; WINDOW_NAME="$name";; esac
  done
  if [ -n "$WINDOW_ID" ]; then
    geom=$(DISPLAY="$DISPLAY_NUM" xdotool getwindowgeometry "$WINDOW_ID" 2>/dev/null | tr '\n' ' ')
    pass "window created: \"$WINDOW_NAME\" [$geom]"
  else
    fail "no window titled '$WINDOW_TITLE*' on $DISPLAY_NUM"
  fi
else
  echo "  SKIP  window check (needs xdotool and xwininfo)"
fi

# 3. the sidecar is the APP's child -- not something we started
SIDECAR_PID=$(pgrep -P "$APP_PID" -f 'sigma-engine' | head -1)
if [ -n "$SIDECAR_PID" ]; then
  pass "sidecar pid $SIDECAR_PID is a child of the app (ppid $APP_PID)"
else
  fail "no sigma-engine child of $APP_PID -- the app did not spawn its sidecar"
fi

# 4. the engine answers where the app put it
if HEALTH=$(curl -fsS -m 5 "http://127.0.0.1:$ENGINE_PORT/health" 2>/dev/null); then
  pass "engine answers 127.0.0.1:$ENGINE_PORT/health -> $HEALTH"
else
  fail "no engine on 127.0.0.1:$ENGINE_PORT"
fi

# 5. THE ONE NO BROWSER TEST CAN GIVE US: the app's own webview reached the
#    engine cross-origin. The webview's origin is tauri://localhost (Linux
#    and macOS) / http://tauri.localhost (Windows), the engine's is
#    127.0.0.1:PORT, so every call it makes with a JSON content-type
#    preflights first. A 200 here is the CORS middleware working in a REAL
#    webview; a 405 is the bug that shipped.
if [ -f "$SIDECAR_LOG" ]; then
  cp "$SIDECAR_LOG" "$OUT_DIR/sidecar.log"
  # `grep -c` exits 1 on no match while still printing 0, so the count is
  # taken with `|| true` -- `|| echo 0` would append a SECOND zero and turn
  # the comparison below into a syntax error.
  PREFLIGHTS=$(grep -c '"OPTIONS .*" 200 OK' "$SIDECAR_LOG" 2>/dev/null || true)
  PREFLIGHTS=${PREFLIGHTS:-0}
  BAD_PREFLIGHTS=$(grep -E '"OPTIONS [^"]*" (4[0-9][0-9]|5[0-9][0-9])' "$SIDECAR_LOG" 2>/dev/null)
  if [ "$PREFLIGHTS" -gt 0 ] && [ -z "$BAD_PREFLIGHTS" ]; then
    pass "webview reached the engine cross-origin: $PREFLIGHTS OPTIONS preflight(s), all 200"
    grep -m 2 '"OPTIONS ' "$SIDECAR_LOG" | sed 's/^/        /'
  elif [ -n "$BAD_PREFLIGHTS" ]; then
    fail "a CORS preflight was refused -- this is the shipped-bug signature:"
    echo "$BAD_PREFLIGHTS" | sed 's/^/        /'
  else
    fail "no OPTIONS preflight in $SIDECAR_LOG -- the webview never called the engine"
  fi
  # The readiness gate polls /health and only renders the app once it
  # answers. A 200 here means the user saw the home screen, not the
  # "engine didn't start" dead end.
  if grep -q '"GET /health HTTP/1.1" 200 OK' "$SIDECAR_LOG"; then
    pass "readiness gate cleared: the webview's own GET /health returned 200"
  else
    fail "no successful GET /health from the webview -- the app is on the failure screen"
  fi
else
  fail "no sidecar log at $SIDECAR_LOG"
fi

# optional: a picture, for a human to actually look at
if command -v import > /dev/null; then
  DISPLAY="$DISPLAY_NUM" import -window root "$OUT_DIR/screen.png" 2>/dev/null \
    && echo "  NOTE  screenshot: $OUT_DIR/screen.png"
fi

# 6. shutdown leaves nothing behind
echo "== shutdown =="
if [ -n "$WINDOW_ID" ]; then
  DISPLAY="$DISPLAY_NUM" xdotool windowclose "$WINDOW_ID"
else
  kill "$APP_PID" 2>/dev/null
fi
for _ in $(seq 1 20); do
  kill -0 "$APP_PID" 2>/dev/null || break
  sleep 0.5
done
sleep 3
STRAYS=$(pgrep -af 'release/sigma-engine' 2>/dev/null)
if [ -z "$STRAYS" ]; then
  pass "no engine process survived the app"
else
  fail "ORPHANED ENGINE after the app exited -- it will hold port $ENGINE_PORT and the"
  fail "      next launch will silently talk to it instead of its own sidecar:"
  echo "$STRAYS" | sed 's/^/        /'
fi
if curl -fsS -m 3 "http://127.0.0.1:$ENGINE_PORT/health" > /dev/null 2>&1; then
  fail "port $ENGINE_PORT still serving after the app exited"
else
  pass "port $ENGINE_PORT released"
fi

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "RESULT: PASS (real app, real window, real webview -> real engine)"
  exit 0
fi
echo "RESULT: FAIL ($FAILURES check(s)) -- logs in $OUT_DIR"
exit 1
