"""Advisor settings (PLAN §5.1): where the Layer 2 advisor's API key, base
URL override, and enabled flag live. Stored once per project-store root as
`settings.json`, a SIBLING of every project folder -- never inside a
project (M5 brief) -- because advisor configuration is a machine/install
preference, not project data: it has nothing to do with any one DMAIC
project and must never round-trip through a project export/copy.

Every other module reaches settings.json through AdvisorSettingsStore only
(routes/advisor.py, client.py's callers) -- masking and the atomic-write
technique both stay in this one place.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel

SETTINGS_FILENAME = "settings.json"

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
    UI could mistake for a real value."""
    if not api_key:
        return None
    tail = api_key[-_UNMASKED_SUFFIX_LEN:] if len(api_key) > _UNMASKED_SUFFIX_LEN else api_key
    return (_MASK_CHAR * _MASK_WIDTH) + tail


def _atomic_write_json(path: Path, data: dict) -> None:
    # Same temp-file + os.replace technique as project_store.py's
    # _atomic_write_json / datasets.py's _atomic_write -- duplicated here
    # rather than imported (both are module-private, and every storage
    # module in this engine already owns its own atomic-write helper
    # rather than sharing one across modules).
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_name, path)  # atomic rename on POSIX and Windows
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
        return AdvisorSettings.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save(self, settings: AdvisorSettings) -> AdvisorSettings:
        _atomic_write_json(self._path(), settings.model_dump(mode="json"))
        return settings
