"""FastAPI dependency: the ProjectStore root. Read lazily from the
environment on every call (not cached at import time) so tests can point
it at a temp directory with monkeypatch.setenv before making a request,
without needing dependency_overrides plumbing.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..project_store import ProjectStore

DEFAULT_PROJECTS_ROOT = Path.home() / ".sigma-ai" / "projects"
PROJECTS_ROOT_ENV_VAR = "SIGMA_PROJECTS_ROOT"


def get_store() -> ProjectStore:
    root = os.environ.get(PROJECTS_ROOT_ENV_VAR, str(DEFAULT_PROJECTS_ROOT))
    return ProjectStore(Path(root))
