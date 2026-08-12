"""Draft storage (docs/uat/PLAN.md Phase 4.1, off the 2026-08-12 supervisor
UAT): a project's in-progress, per-tool typing, persisted so navigating away
never loses it. Sibling of DatasetStore / FloorPlanImageStore -- the same
project-folder-plus-JSON shape, under a different subdirectory (drafts/
instead of datasets/ or floorplans/) -- and the same temp-file+rename write
as project_store.py's _atomic_write_json, duplicated rather than imported
since that one is module-private (the same call floorplan_images.py already
made for its own _atomic_write).

A DRAFT IS NOT AN ARTIFACT. That is not a detail of this module, it is the
whole reason it exists as a separate module instead of one more field on
ProjectStore. An artifact is validated, versioned, and complete -- gates.py,
the tollgate checks, the phase packs, and every report all trust
artifact_index to mean exactly that, and none of them re-check it. The
moment a half-typed charter could ride into artifact_index as an artifact,
"saved" stops meaning anything and every one of those consumers would have
to start defending itself against partial data. So a draft never touches
artifact_index, never validates, and is invisible to all of them by
construction: nothing in this module imports gates.py, registry.py, or
export/, and nothing should ever be added here that does.

`payload` is opaque JSON the engine never inspects and never validates.
That is deliberate, not a gap to close later: the entire reason a draft
exists is that it is allowed to be incomplete (an owner-less charter, a
half-written problem statement), so validating its shape against the
eventual artifact schema would defeat the one thing it is for. The desktop
shell owns the shape of what it puts in `payload`; this store's job is only
to make sure typing a supervisor already did is never silently gone.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .project_store import ProjectStore

# tool_id becomes a filesystem path component (drafts/<tool_id>.json), and
# unlike artifact_id or project_id it arrives straight from the URL path
# rather than a validated request body -- nothing upstream has confirmed it
# isn't `../../meta` before it reaches this store. Real tool ids are T-01
# .. T-25 and T-35 today; this allowlist is a strict superset of that shape
# (letters, digits, hyphen, underscore) rather than a regex tailored to
# "T-\d\d", so a future tool id doesn't need this file touched to work. It
# rejects the one thing a traversal needs -- "/" -- along with "." runs, so
# a value never reaches Path.__truediv__ without first proving it is a
# single, ordinary path segment.
_SAFE_TOOL_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def is_safe_tool_id(tool_id: str) -> bool:
    return bool(_SAFE_TOOL_ID.fullmatch(tool_id))


class DraftRecord(BaseModel):
    """The persisted record (drafts/<tool_id>.json). `payload` is `Any`,
    not `dict[str, Any]`, on purpose: Pydantic still confirms the record
    envelope round-trips as JSON, but imposes no shape at all on the one
    field this store promises never to look inside."""

    schema_version: int = 1
    tool_id: str
    # Caller-supplied, like ProjectCreateRequest.created_at -- never
    # datetime.now() on the server, so callers (and tests) control it.
    updated_at: str
    payload: Any = None


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    # Same temp-file+rename technique as project_store.py's
    # _atomic_write_json: a crash between the write and the rename leaves
    # only a stray .tmp file next to a still-intact (or still-absent)
    # drafts/<tool_id>.json, never a half-written one.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_name, path)  # atomic rename on POSIX and Windows
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class DraftStore:
    """Sibling of DatasetStore/FloorPlanImageStore, taking a ProjectStore
    the same way they take one. One file per tool_id
    (drafts/<tool_id>.json), overwritten wholesale on every save -- a draft
    has no version history because it is not the thing being kept; the
    eventual artifact is."""

    def __init__(self, project_store: ProjectStore) -> None:
        self.projects = project_store

    def _drafts_dir(self, project_id: str) -> Path:
        return self.projects.resolved_project_path(project_id) / "drafts"

    def _draft_path(self, project_id: str, tool_id: str) -> Path:
        if not is_safe_tool_id(tool_id):
            raise ValueError(f"tool_id {tool_id!r} is not a safe path segment")
        return self._drafts_dir(project_id) / f"{tool_id}.json"

    def save_draft(self, project_id: str, tool_id: str, payload: Any, updated_at: str) -> DraftRecord:
        """Upsert: whatever was there for this tool_id, if anything, is
        replaced -- there is exactly one draft per (project, tool)."""
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        record = DraftRecord(tool_id=tool_id, updated_at=updated_at, payload=payload)
        _atomic_write_json(self._draft_path(project_id, tool_id), record.model_dump(mode="json"))
        return record

    def find_draft(self, project_id: str, tool_id: str) -> DraftRecord | None:
        """The draft, or None when this tool has none.

        Most tools have no draft most of the time, and that is the ordinary
        answer rather than an exceptional one -- so the route can answer
        "no" with a 200 instead of a 404 nobody can distinguish from a
        broken call. An unknown PROJECT still raises: that one really is a
        caller mistake.
        """
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        path = self._draft_path(project_id, tool_id)
        if not path.exists():
            return None
        return DraftRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def load_draft(self, project_id: str, tool_id: str) -> DraftRecord:
        """find_draft, but absent is an error -- kept for callers that treat
        a missing draft as exceptional."""
        record = self.find_draft(project_id, tool_id)
        if record is None:
            raise FileNotFoundError(f"no draft for tool_id {tool_id!r} in project {project_id!r}")
        return record

    def delete_draft(self, project_id: str, tool_id: str) -> None:
        """Idempotent by design: the client's real save flow deletes a
        draft the instant the matching artifact save succeeds, and must
        not first have to check whether one existed. missing_ok=True makes
        deleting an already-absent draft a no-op instead of an error."""
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        self._draft_path(project_id, tool_id).unlink(missing_ok=True)

    def list_drafts(self, project_id: str) -> list[DraftRecord]:
        """Every draft currently saved in this project. Cheap on purpose --
        no payload parsing beyond the envelope itself -- so a project
        screen can call it to show "you have unsaved typing in T-03"
        without paying for every draft's full content."""
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        directory = self._drafts_dir(project_id)
        if not directory.exists():
            return []
        drafts: list[DraftRecord] = []
        for path in sorted(directory.glob("*.json")):
            try:
                drafts.append(DraftRecord.model_validate(json.loads(path.read_text(encoding="utf-8"))))
            except (ValueError, json.JSONDecodeError):
                continue  # not one of ours, or corrupt -- skip rather than fail the whole listing (ProjectStore.list_projects precedent)
        return drafts
