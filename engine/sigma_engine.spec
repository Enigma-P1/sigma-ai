# PyInstaller spec, onefile mode. Built per-OS by .github/workflows/build.yml
# (Windows and Mac jobs); a Linux build here is dev-only, never shipped.
#
# Output layout (PyInstaller >=6, onefile via EXE without COLLECT): a single
# self-contained executable dist/sigma-engine[.exe] and NO dist/sigma-engine/
# directory and NO _internal/ support folder. The interpreter, scipy's native
# libs, and everything else are packed inside the one file and unpacked to a
# temp dir at launch by the bootloader. Onefile is used precisely so there is
# no sibling support directory that can go missing in an installed layout --
# the earlier onedir build shipped a dist/sigma-engine/_internal/ that the
# exe resolved relative to its own path, and that path broke inside the
# installed MSI/.app, so the sidecar never started.
#
# Tauri's externalBin sidecar mechanism (see desktop/src-tauri/tauri.conf.json)
# expects exactly one file named "sigma-engine-<target-triple>[.exe]". With
# onefile that is the whole artifact: scripts/build-sidecar.sh renames the
# single dist/sigma-engine[.exe] to that pattern and copies just that one file
# into desktop/src-tauri/binaries/ -- there is nothing else to copy.

from PyInstaller.building.api import EXE, PYZ
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

# Onefile: the binaries and datas are bundled straight into the EXE (there is
# no exclude_binaries=True and no COLLECT step). The result is one file.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="sigma-engine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
