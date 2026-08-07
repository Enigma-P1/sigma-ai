# PyInstaller spec, onedir mode. Built per-OS by .github/workflows/build.yml
# (Windows and Mac jobs); a Linux build here is dev-only, never shipped.
#
# Output layout (PyInstaller >=6, onedir default): dist/sigma-engine/sigma-engine[.exe]
# plus a dist/sigma-engine/_internal/ directory holding the interpreter, scipy's
# native libs, and everything else. contents_directory is pinned explicitly
# below so that layout can't silently change out from under the CI rename step.
#
# Tauri's externalBin sidecar mechanism (see desktop/src-tauri/tauri.conf.json)
# expects exactly one file named "sigma-engine-<target-triple>[.exe]". The CI
# workflow renames dist/sigma-engine/sigma-engine[.exe] to that pattern and
# copies the whole onedir output (renamed exe + _internal/) into
# desktop/src-tauri/binaries/ -- see scripts/build-sidecar.sh, which both CI
# and local dev use, for the exact placement logic and its known macOS risk.

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis

block_cipher = None

a = Analysis(
    ["run_engine.py"],
    pathex=[],
    binaries=[],
    datas=[],
    # scipy ships its own PyInstaller hooks (hook-scipy.*, installed via
    # pyinstaller-hooks-contrib) that cover scipy.stats.describe's compiled
    # submodules; verified in-container that no extra hiddenimports are
    # needed for this spec (see docs/m1-spike-notes.md).
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="sigma-engine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)

COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="sigma-engine",
    contents_directory="_internal",
)
