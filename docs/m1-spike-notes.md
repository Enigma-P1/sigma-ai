---
type: knowledge
status: spike-complete-pending-ci
tags: [m1, packaging, tauri, pyinstaller]
date: 2026-08-07
---

# M1 packaging spike — notes

Minimum scaffold proving the Tauri + PyInstaller-sidecar pipeline (PLAN.md
§7, §8). Not the product: one tool-free window, one NIST computation.

## How it works

- **`engine/`** — FastAPI app (`sigma_engine/main.py`) with `GET /health` and
  `GET /smoke`. `/smoke` runs `stats.describe()` over the NIST StRD "Lew"
  beam-deflection dataset (200 points, embedded in `sigma_engine/nist_lew.py`)
  and compares to the certified mean/stdev to 1e-9 relative tolerance. Binds
  127.0.0.1 only; port is a CLI arg (`--port`, default 8756).
- **`engine/sigma_engine.spec`** — PyInstaller **onedir** build. Output is
  `dist/sigma-engine/sigma-engine[.exe]` plus a `_internal/` support
  directory (interpreter, scipy's native libs, ~275 files). See "onedir's
  `_internal` problem" below — this is the spike's main finding.
- **`scripts/build-sidecar.sh`** — runs PyInstaller, then renames the exe to
  `sigma-engine-<target-triple>[.exe]` (via `rustc --print host-tuple`) and
  copies the whole onedir output into `desktop/src-tauri/binaries/`. One
  script, used by both local dev and CI, so there's one place that knows the
  naming/placement rule.
- **`desktop/`** — Tauri v2 + React/TS/Vite. `src-tauri/src/lib.rs` spawns
  the sidecar in `.setup()` via `tauri-plugin-shell`'s `Command::sidecar`,
  stores the child in managed state, kills it on `WindowEvent::CloseRequested`.
  The frontend (`src/App.tsx`) never talks to Rust for this — it polls
  `http://127.0.0.1:8756/health` directly with `fetch`, then calls `/smoke`
  once and renders computed-vs-certified values plus a pass/fail line.
  No shell capability grant is needed in `capabilities/default.json`: Tauri's
  permission/ACL system gates calls *from the webview*, and the sidecar is
  spawned from Rust, not JS (confirmed against tauri.app's sidecar guide,
  "Running it from Rust" vs "...from JavaScript").
- **`.github/workflows/build.yml`** — `test` (ubuntu-latest, pytest) always
  runs; `build-windows` / `build-mac` (`needs: test`) build the sidecar,
  place it, then `tauri build`. Triggers: push to `main`, manual dispatch.

## Running dev mode

`tauri dev` looks for `binaries/sigma-engine-<host-triple>` on disk the same
way a bundled build does — it has to exist *before* you run dev mode:

```
cd engine && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
../scripts/build-sidecar.sh          # from repo root
cd desktop && npm install && npm run tauri dev
```

## What CI produces

- `test`: pytest results (gate for the other two jobs).
- `build-windows`: `sigma-ai-windows-installers` artifact — `.msi` and
  `.exe` (nsis) from `src-tauri/target/release/bundle/`.
- `build-mac`: `sigma-ai-mac-installer` artifact — one `.dmg`, hand-built
  with `hdiutil` from a fixed-up `.app` (see below), because Tauri's own dmg
  step would seal in the bug.

## onedir's `_internal` problem (the spike's main finding)

PyInstaller's onedir bootloader looks for `_internal` **as a literal
filesystem sibling of the running executable** — this is fixed C bootloader
behavior, not something Tauri config can redirect. Tauri's `externalBin`
sidecar and its `bundle.resources` are documented to land in *different*
directories on macOS (`Contents/MacOS` vs `Contents/Resources`, per
tauri.app's `resourceDir()` reference) and, it turns out, on Linux too
(`/usr/bin` vs `/usr/lib/<app>`, FHS-style) — so a naive
`"resources": {"binaries/_internal": "_internal"}` mapping produces an
installer that looks fine in CI but is silently broken on launch.

This was not left as a theoretical risk — it was reproduced and fixed
in-container:

1. Ran the onedir exe alone, without `_internal` beside it →
   `[PYI-2471:ERROR] Failed to load Python shared library
   '.../_internal/libpython3.11.so.1.0': ... No such file or directory`
   (exit 255).
2. Built a real Tauri `.deb` locally (Linux prerequisites installed for this
   spike; not a shipped target) and inspected it: sidecar landed at
   `usr/bin/sigma-engine`, `_internal` landed at `usr/lib/Sigma AI/_internal`
   — confirmed broken, same error as (1), on the actual bundled artifact.
3. Fix: move `_internal` to sit beside the sidecar exe. Retested — `/health`
   and `/smoke` both return `match: true` from the relocated bundle.

**Windows is expected to be unaffected**: tauri.app documents
`resourceDir()` on Windows as "the directory that contains the main
executable" — i.e. the same directory `externalBin` already uses — so no
fixup step was added to `build-windows`. This is inference from Tauri's
docs, not a Windows reproduction (no Windows box available here); the
Windows smoke-test step in the workflow (below) is what actually checks it.

**macOS fix, applied in `build-mac`:** build `--bundles app` only, merge
`Contents/Resources/_internal` into `Contents/Frameworks/` (ditto, symlinks
preserved), smoke-test the relocated sidecar for real
(`curl 127.0.0.1:8756/health` and `/smoke`, asserting `match: true`),
*then* `hdiutil create` the dmg from the fixed `.app`.

**Corrected by CI run 31202027106 (first real macOS run):** the sibling
rule above is NOT what the bootloader does inside an .app. When the exe
path ends in `Contents/MacOS/`, PyInstaller's bootloader resolves support
files to **`Contents/Frameworks/`** — the run failed with
`[PYI-9202] Failed to load Python shared library
'.../Contents/Frameworks/Python'` while a sibling `_internal` sat unused
in `Contents/MacOS/`. So: sibling `_internal` outside an .app
(Linux/Windows), `Contents/Frameworks/` inside one. The workflow was
fixed accordingly (same run also proved the Windows path green end-to-end
— msi/nsis built, staged sidecar smoke passed, no fixup needed there,
confirming the inference above). If these assumptions ever stop holding,
the fallback is switching `sigma_engine.spec` from onedir to onefile mode
— a single self-contained executable sidesteps the support-directory
requirement
entirely, at the cost of a slower (self-extracting) cold start.

## Verified in-container vs. CI must prove

| Claim | Status |
|---|---|
| `pytest` (6 tests: dataset size, mean/stdev match, `/health`, `/smoke`) | **Verified** — all pass |
| `uvicorn` serving `/health` and `/smoke` with real JSON, `match: true` | **Verified** — curled directly |
| Engine binds 127.0.0.1 only (not 0.0.0.0) | **Verified** — checked `/proc/net/tcp` |
| PyInstaller onedir build succeeds, frozen binary serves correctly | **Verified** — built and curled the frozen exe |
| `scripts/build-sidecar.sh` naming/placement logic | **Verified** — ran it, placed binary responds correctly |
| `_internal` must sit beside the sidecar exe (onedir requirement) | **Verified** — reproduced the failure and the fix |
| `npm install`, `tsc --noEmit`, `npm run build` (frontend) | **Verified** — all clean |
| `cargo check` / `cargo build` (Rust backend) | **Verified** — after installing Linux webkit2gtk/gtk3 dev packages in-container (not present by default; not needed on Windows/Mac runners, which ship native webviews). Caught and fixed one real borrow-checker error (`state` MutexGuard temporary lifetime in the window-close handler) — see `src-tauri/src/lib.rs`. |
| Real Tauri bundling (`externalBin` + `resources` resolution, icon processing) | **Verified** — built an actual `.deb` locally and inspected its contents (Linux is not a shipped target; this was to validate the bundling mechanism itself) |
| `actionlint` + `shellcheck` against `build.yml` and `build-sidecar.sh` | **Verified** — clean, zero warnings |
| Windows msi/nsis build actually succeeds | **Not verified here — CI must prove.** No Windows box in this container. |
| Windows `resources`/`externalBin` co-location (the `_internal` question) | **Not verified here — CI must prove.** Inferred from Tauri's docs (see above); the workflow's Windows smoke-test step checks it directly. |
| macOS `.app`/dmg build, code signing/Gatekeeper behavior | **Not verified here — CI must prove.** No Mac in this container. The fixup mechanism was proven on an analogous Linux artifact, not on macOS itself. |
| The §7 clean-machine test (fresh account, no Python, 15-minute install-to-Project-Picker) | **Not attempted — later M1 gate**, requires real Windows/Mac hardware and a non-developer tester. This spike only proves the build pipeline. |
| Installed-app GUI actually renders correctly (webview, window title, live polling) | **Not verified here.** No display server in this container; `tsc`/`cargo build` succeeding is necessary but not sufficient. |

## Deviations from the brief, and why

- Added `scripts/build-sidecar.sh` (not in the original deliverable list) so
  the exact placement logic used by CI is also runnable and testable
  locally — this is what let the `_internal` finding above get caught and
  fixed pre-CI instead of discovered as a silent CI failure.
- Added a sidecar smoke-test step inside both `build-windows` and
  `build-mac` (curl `/health` + `/smoke`, assert `match: true`) before
  trusting the packaged installer. Not asked for explicitly, but it's the
  direct analogue of the §7 clean-machine test's "a stats smoke check
  passes on that same machine" requirement, run one layer earlier where a
  CI failure is cheaper to diagnose than a failed installer artifact.
- `build-mac` builds the dmg with `hdiutil` directly instead of letting
  Tauri's own dmg bundler do it, because Tauri's dmg step would wrap the
  *unfixed* `.app` (see the onedir finding). The resulting dmg is a plain
  drag-to-Applications image; it lacks Tauri's optional background-image/
  drop-arrow cosmetics. Acceptable for a pipeline spike; revisit if that
  polish matters once real tools ship on this pipeline.
- CSP left `null` (permissive), matching the create-tauri-app default.
  Given "no network calls other than localhost sidecar" is currently true
  by construction (the frontend only calls one hardcoded 127.0.0.1 URL),
  restricting `connect-src` would be a real hardening step but is an
  untested change layered on an already-untested build; left for a
  follow-up once the packaging pipeline itself is proven in CI.
