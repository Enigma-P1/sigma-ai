"""Advisor settings (PLAN §5.1): where the Layer 2 advisor's API key, base
URL override, and enabled flag live. Stored once per project-store root as
`settings.json`, a SIBLING of every project folder -- never inside a
project (M5 brief) -- because advisor configuration is a machine/install
preference, not project data: it has nothing to do with any one DMAIC
project and must never round-trip through a project export/copy.

Every other module reaches settings.json through AdvisorSettingsStore only
(routes/advisor.py, client.py's callers) -- masking and the atomic-write
technique both stay in this one place.

M5 exit critic, severity 1: a truncated or hand-edited settings.json used
to 500 EVERY advisor route (load() had no try/except around json.loads +
model_validate). load() now treats a corrupt/unreadable file exactly like
a missing one -- an honest AdvisorSettings() default, logged, never a 500 --
because the ONLY way a user could previously clear a stored key was
hand-editing this file (routes/advisor.py's PUT kept the current key
whenever body.api_key was falsy), which is the exact road to a truncated
edit. PUT now accepts clear_api_key explicitly instead, so hand-editing is
no longer the only removal path, but a corrupt file must still never 500 --
disk corruption, a crash mid-write (see _atomic_write_json's fsync below),
or a manual edit from before this fix all still land here.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, ValidationError

SETTINGS_FILENAME = "settings.json"

_logger = logging.getLogger(__name__)

# Fixed-width mask for GET responses (M5 brief: "masked last-4 only") -- a
# constant number of placeholder characters regardless of the real key's
# length, so the response never even leaks how long the stored key is.
_MASK_CHAR = "*"
_MASK_WIDTH = 8
_UNMASKED_SUFFIX_LEN = 4


class AdvisorSettings(BaseModel):
    """The persisted record. `api_key` is the real secret at rest on disk
    -- masking happens only where it's read back out for display
    (mask_api_key below), never here, so the store itself stays a faithful
    round trip of whatever was saved."""

    schema_version: int = 1
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool = True


def mask_api_key(api_key: str | None) -> str | None:
    """Last-4-only mask (M5 brief: "the settings GET must mask it"). None
    stays None -- an honest "nothing stored," not a masked empty string a
    UI could mistake for a real value.

    M5 exit critic (bullet finding): a key no longer than
    _UNMASKED_SUFFIX_LEN used to fall through the `len() > 4` guard below
    and come back as `tail = api_key` unchanged -- the fixed-width star
    prefix made it LOOK masked while the response body actually carried
    the entire real key. A key this short can't have any of itself shown
    without showing all of it, so it's masked completely instead."""
    if not api_key:
        return None
    if len(api_key) <= _UNMASKED_SUFFIX_LEN:
        return _MASK_CHAR * _UNMASKED_SUFFIX_LEN
    tail = api_key[-_UNMASKED_SUFFIX_LEN:]
    return (_MASK_CHAR * _MASK_WIDTH) + tail


def _fsync_dir_best_effort(dir_path: Path) -> None:
    """Directory fsync is a POSIX concept -- Windows has no equivalent
    (os.open() on a directory raises there), and this engine ships a
    Windows desktop build (PLAN §7: "Tauri desktop shell", tested on "a
    stock Windows machine"). Best-effort only: if the platform or
    filesystem doesn't support it, this is a no-op, never a crash -- the
    file's own fsync (below) is what actually protects settings.json
    against a zero-length publish; the directory fsync is belt-and-braces
    for making the rename itself durable, which matters less than the
    file content being real."""
    try:
        dir_fd = os.open(dir_path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        pass  # e.g. Windows: directories aren't fsync-able there
    finally:
        os.close(dir_fd)


def _atomic_write_json(path: Path, data: dict) -> None:
    # Same temp-file + os.replace technique as project_store.py's
    # _atomic_write_json / datasets.py's _atomic_write -- duplicated here
    # rather than imported (both are module-private, and every storage
    # module in this engine already owns its own atomic-write helper
    # rather than sharing one across modules).
    #
    # M5 exit critic, severity 1: neither sibling ever called fsync, so a
    # crash between the temp file's write() and the os.replace() rename
    # could publish a zero-length or partially-flushed settings.json --
    # exactly the shape of corruption load() (above) now has to survive.
    # fsync-before-rename is the standard fix: it forces the temp file's
    # bytes out of the OS page cache and onto disk BEFORE the rename makes
    # them visible at the real path, so the rename can never expose a
    # write the crash caught mid-flight. Settings.json is small and
    # infrequently written (a user editing advisor settings, not a hot
    # path), so the extra syscall's cost is irrelevant here.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)  # atomic rename on POSIX and Windows
        _fsync_dir_best_effort(path.parent)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class AdvisorSettingsStore:
    """Sibling of ProjectStore, keyed off the same root. routes/advisor.py
    constructs this from the same `store.root` the project routes already
    resolve via routes/deps.py's get_store -- no new env var, no second
    root to keep in sync with SIGMA_PROJECTS_ROOT."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def _path(self) -> Path:
        return self.root / SETTINGS_FILENAME

    def load(self) -> AdvisorSettings:
        path = self._path()
        if not path.exists():
            return AdvisorSettings()  # honest default: nothing configured yet, advisor unavailable
        try:
            raw_text = path.read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            return AdvisorSettings.model_validate(parsed)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            # M5 exit critic, severity 1: a truncated write (crash mid-save,
            # a hand-edit gone wrong, a zero-length file from a pre-fsync
            # build) must never 500 every advisor route -- treat it exactly
            # like "nothing configured yet" (the same honest default as the
            # not-exists branch above), logged so it's visible to whoever
            # runs this install, never raised. Every advisor route already
            # goes through resolve_config() on top of this, which turns
            # "no key" into a clean 409 -- this is what makes that path
            # reachable instead of dying on the read.
            _logger.warning("advisor settings.json at %s is unreadable/invalid (%s) -- using defaults", path, exc)
            return AdvisorSettings()

    def save(self, settings: AdvisorSettings) -> AdvisorSettings:
        _atomic_write_json(self._path(), settings.model_dump(mode="json"))
        return settings
