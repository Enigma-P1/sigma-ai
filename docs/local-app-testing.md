# Running the real desktop app locally

Every automated test in this repo except one stops at the edge of the Tauri
shell. `desktop/tools/smoke-browser.mjs` loads the UI from Vite;
`desktop/tools/packaged-sweep.mjs` and `desktop/tools/xorigin-probe.mjs`
reproduce the packaged *origin* in Chromium. All three are browser tests.
None of them compiles the Rust, spawns the sidecar the way the app does,
creates a real window, or exercises the download handler.

That layer — sidecar launch, webview origin/CORS, window creation, downloads
— is where all three shipped bugs lived, and each one cost a paid
Windows+Mac installer build to find:

1. the onedir sidecar's `_internal/` folder didn't survive installation, so
   the engine never started;
2. the engine had no CORS middleware, so the packaged webview's preflight
   got 405 and the app reported "the engine didn't start";
3. the config-created window had no download handler, so the charter PDF
   export was silently dropped on macOS.

`desktop/tools/run-real-app.sh` closes that gap on Linux, for free. It runs
the **actual built binary** under Xvfb and asserts the things only a real run
can show. It is the last gate to run before paying for an installer build.

## Prerequisites

```bash
# system (Debian/Ubuntu)
apt-get install -y libwebkit2gtk-4.1-dev build-essential curl \
                   xvfb xdotool imagemagick x11-utils

# repo
cd engine && pip install -e ".[dev]"     # or use engine/.venv
cd desktop && npm ci
```

`xdotool`, `imagemagick` (`import`) and `x11-utils` (`xwininfo`) are optional
— without them the script skips the window-title check and the screenshot —
but you want them, because *looking at a screenshot of the real app* is how
two of the layout defects below were found.

## Build, then run

```bash
# 1. the sidecar: one self-contained file, no _internal/ next to it
scripts/build-sidecar.sh

# 2. the app itself (a .deb is a bonus; the runnable binary is the point)
cd desktop && npm run tauri build -- --bundles deb
#   ...or, if bundling fights you:
cd desktop && npm run tauri build -- --no-bundle

# 3. drive it headless and assert
desktop/tools/run-real-app.sh
```

Expected output:

```
== launching .../target/release/desktop on :99 ==
== checks ==
  PASS  app process 19433 alive after 20s
  PASS  window created: "Sigma AI — Packaging Spike" [... Geometry: 900x650 ]
  PASS  sidecar pid 19453 is a child of the app (ppid 19433)
  PASS  engine answers 127.0.0.1:8756/health -> {"status":"ok","engine_version":"0.1.0"}
  PASS  webview reached the engine cross-origin: 1 OPTIONS preflight(s), all 200
        [sigma-engine] INFO:  127.0.0.1:44876 - "OPTIONS /health HTTP/1.1" 200 OK
  PASS  readiness gate cleared: the webview's own GET /health returned 200
== shutdown ==
  PASS  no engine process survived the app
  PASS  port 8756 released

RESULT: PASS (real app, real window, real webview -> real engine)
```

The fifth check is the one no browser test can produce. That `OPTIONS
/health ... 200 OK` line is written by the engine because **the app's own
WebKitGTK webview** sent a CORS preflight from `tauri://localhost` to
`127.0.0.1:8756`. A `405` there is bug #2 above, reproduced before it ships
rather than after.

Artifacts land in `/tmp/sigma-real-app/` (override with `OUT_DIR`):
`app-run.log`, `sidecar.log`, `screen.png`.

## Driving it by hand

The script is a smoke check. For anything richer — clicking through a real
DMAIC flow, exercising the PDF export — drive the same window with
`xdotool`, which works fine against a WebKitGTK webview:

```bash
Xvfb :99 -screen 0 1400x900x24 &
DISPLAY=:99 openbox &                  # optional; gives real decorations
DISPLAY=:99 ./desktop/src-tauri/target/release/desktop &

export DISPLAY=:99
xdotool mousemove --sync 232 269 click 1        # click a field
xdotool type --delay 40 "Coffee Bar wait time"  # React state updates
import -window root /tmp/shot.png               # then LOOK at it
```

Two notes learned the hard way:

- **`xdotool search --name` cannot find this window.** The configured title
  contains an em dash, so `WM_NAME` is a `UTF8_STRING` that xdotool's search
  path fails to decode; it finds only GTK's 10x10 helper window, named
  `desktop`. Walk `xwininfo -root -children` and ask `xdotool getwindowname`
  per candidate instead (what `run-real-app.sh` does).
- **Confirm the click landed** before assuming a step worked. A click issued
  while React is mid-render is silently dropped. `mousemove --sync`, a short
  sleep, then `click` is reliable; `mousemove --sync ... click 1` as one
  invocation occasionally is not.

## What a green Linux run does NOT prove

The webview is the whole point of this run, and it is a *different webview*
on every platform. Linux is WebKitGTK; macOS is WKWebView; Windows is
WebView2 (Chromium). A green run here proves the app's own code is right —
the sidecar is spawned and reachable, the origin is cross-origin and the
CORS policy answers it, the window is built, the download handler is
registered. It does not prove:

- **Download behaviour on Windows/macOS.** `on_download` is registered
  through the same Tauri API everywhere, but each platform implements it
  differently. On WebKitGTK the destination defaults to
  `dirs::download_dir()`; on macOS the handler is what stops WKWebView's
  navigation delegate from cancelling the download outright (bug #3); on
  Windows WebView2 has its own default download UI. Only the Linux path is
  exercised here.
- **Installer packaging.** The `.deb` this produces shares nothing with the
  NSIS/MSI and `.app`/`.dmg` paths. Install layout, code signing,
  Gatekeeper/SmartScreen, and whether the sidecar survives being installed
  into `Program Files` are all still CI-and-installer-only questions — bug
  #1 was exactly that class.
- **Blob/`objectURL` lifetime differences.** The charter export creates a
  blob URL, clicks an `<a download>`, and revokes the URL synchronously.
  WebKitGTK tolerates it; WebView2 and WKWebView are not guaranteed to.
- **Fonts, DPI, and native form controls.** Every `<select>` here is a GTK
  popup rendered by a container's font set, at 1x scaling, on a 1400x900
  virtual screen.

## Why this isn't wired into CI

It could be — `ubuntu-latest` has `webkit2gtk-4.1` via apt and Xvfb
preinstalled. It is deliberately left as a local/pre-release gate:

- the job is dominated by an uncached `cargo build --release` of the full
  Tauri dependency tree (~10 min cold on a runner, on top of PyInstaller and
  `npm ci`), which is a lot to add to every push; and
- headless WebKitGTK on a hosted runner is a *third* WebKit build, unrelated
  to any user's machine. A job that goes red for environmental reasons is a
  job people learn to ignore, which is worse than no job.

The two findings this run produced that CI would have had to catch are both
now covered by deterministic tests that do run in CI:
`engine/tests/test_cors_packaged.py` (the preflight contract) and
`engine/tests/test_sidecar_lifecycle.py` (the sidecar must not outlive the
app). Run `run-real-app.sh` before each installer build; that is what it is
for.
