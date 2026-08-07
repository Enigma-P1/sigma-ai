#!/usr/bin/env bash
# Build the engine sidecar with PyInstaller and place it where Tauri's
# externalBin expects. Shared by local dev and .github/workflows/build.yml so
# there is exactly one place that knows the naming/placement rule.
#
# Requires: pyinstaller importable (this script prefers engine/.venv if
# present, else falls back to `pyinstaller` on PATH) and rustc on PATH (used
# only to name the binary -- no Rust code is built here).
#
# Usage: scripts/build-sidecar.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE_DIR="$REPO_ROOT/engine"
BIN_DIR="$REPO_ROOT/desktop/src-tauri/binaries"

if [ -x "$ENGINE_DIR/.venv/bin/pyinstaller" ]; then
  PYINSTALLER="$ENGINE_DIR/.venv/bin/pyinstaller"
else
  PYINSTALLER="pyinstaller"
fi

echo "== Building sidecar with $PYINSTALLER =="
( cd "$ENGINE_DIR" && "$PYINSTALLER" sigma_engine.spec --noconfirm )

# Tauri requires the target-triple suffix (not just an OS name) because the
# same "windows" or "darwin" OS can mean different triples (e.g. Apple
# Silicon vs Intel Mac); rustc knows the exact one for the machine we're on.
TARGET_TRIPLE="$(rustc --print host-tuple)"
echo "== Host target triple: $TARGET_TRIPLE =="

SRC_DIR="$ENGINE_DIR/dist/sigma-engine"
if [ -f "$SRC_DIR/sigma-engine.exe" ]; then
  EXT=".exe"
elif [ -f "$SRC_DIR/sigma-engine" ]; then
  EXT=""
else
  echo "ERROR: PyInstaller output not found at $SRC_DIR/sigma-engine[.exe]" >&2
  exit 1
fi

mkdir -p "$BIN_DIR"

DEST_EXE="$BIN_DIR/sigma-engine-${TARGET_TRIPLE}${EXT}"
cp "$SRC_DIR/sigma-engine${EXT}" "$DEST_EXE"
chmod +x "$DEST_EXE" 2>/dev/null || true

# onedir mode ships a support directory alongside the executable (PyInstaller
# >=6 default name: _internal). It MUST stay a sibling of the renamed exe --
# PyInstaller's bootloader looks it up relative to the running executable's
# own path, not via any Tauri-configurable setting. Confirmed in-container:
# running the exe with _internal missing fails with "Failed to load Python
# shared library ... No such file or directory" (see docs/m1-spike-notes.md).
rm -rf "$BIN_DIR/_internal"
cp -r "$SRC_DIR/_internal" "$BIN_DIR/_internal"

echo "== Placed sidecar =="
echo "  $DEST_EXE"
echo "  $BIN_DIR/_internal/ ($(find "$BIN_DIR/_internal" -type f | wc -l) files)"
