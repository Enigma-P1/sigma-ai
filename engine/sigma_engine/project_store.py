"""Project folder storage (PLAN §4.5): one folder per project, one JSON file
per artifact version, an append-only override log. Every write is atomic
(temp file + rename) so a crash mid-write never leaves a half-written file
for a later load to trip over. This module is deliberately schema-agnostic
-- it stores and returns plain dicts; the caller (route layer) validates
against the right artifacts.* Pydantic model before/after.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ArtifactIndexEntry(BaseModel):
    tool_id: str
    latest_version: int


class ProjectMetadata(BaseModel):
    schema_version: int = 1
    project_id: str
    name: str
    created_at: str
    updated_at: str
    artifact_index: dict[str, ArtifactIndexEntry] = Field(default_factory=dict)


class OverrideLogEntry(BaseModel):
    gate_id: str
    reason: str = Field(min_length=1)
    timestamp: str
    # The gate's missing-tool-ids set *at override time*, so gates.check()
    # can tell a still-covering override from a stale one after artifacts
    # change (gates.py's _covering_override). Records written before this
    # field existed default to [], which can never match a real (non-empty)
    # missing set -- they load without error, they just never clear anything.
    missing: list[str] = Field(default_factory=list)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_name, path)  # atomic rename on POSIX and Windows
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _append_jsonl(path: Path, line_obj: dict[str, Any]) -> None:
    # An append-only log doesn't get the temp-file+rename treatment (that
    # would mean rewriting the whole log on every entry); a single-line
    # `open("a").write()` is what POSIX guarantees atomically for writes
    # under PIPE_BUF, which one JSON line always is here.
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line_obj, sort_keys=True))
        f.write("\n")


class ProjectStore:
    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def _project_dir(self, project_id: str) -> Path:
        return self.root / project_id

    def _metadata_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "project.json"

    def _artifact_version_path(self, project_id: str, artifact_id: str, version: int) -> Path:
        return self._project_dir(project_id) / "artifacts" / artifact_id / f"v{version}.json"

    def _overrides_path(self, project_id: str) -> Path:
        return self._project_dir(project_id) / "overrides.log.jsonl"

    def create_project(self, project_id: str, name: str, created_at: str) -> ProjectMetadata:
        if self._metadata_path(project_id).exists():
            raise FileExistsError(f"project {project_id!r} already exists")
        meta = ProjectMetadata(project_id=project_id, name=name, created_at=created_at, updated_at=created_at)
        _atomic_write_json(self._metadata_path(project_id), meta.model_dump(mode="json"))
        return meta

    def load_project(self, project_id: str) -> ProjectMetadata:
        path = self._metadata_path(project_id)
        if not path.exists():
            raise FileNotFoundError(f"project {project_id!r} not found")
        return ProjectMetadata.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save_artifact(
        self, project_id: str, artifact_id: str, tool_id: str, data: dict[str, Any], updated_at: str
    ) -> int:
        """Write a new immutable version of `artifact_id` and bump the
        project index. Version numbers start at 1 and only ever increase --
        there is no in-place edit of a saved version."""
        meta = self.load_project(project_id)
        current = meta.artifact_index.get(artifact_id)
        next_version = 1 if current is None else current.latest_version + 1
        _atomic_write_json(self._artifact_version_path(project_id, artifact_id, next_version), data)
        meta.artifact_index[artifact_id] = ArtifactIndexEntry(tool_id=tool_id, latest_version=next_version)
        meta.updated_at = updated_at
        _atomic_write_json(self._metadata_path(project_id), meta.model_dump(mode="json"))
        return next_version

    def load_artifact(self, project_id: str, artifact_id: str, version: int | None = None) -> dict[str, Any]:
        if version is None:
            meta = self.load_project(project_id)
            entry = meta.artifact_index.get(artifact_id)
            if entry is None:
                raise FileNotFoundError(f"artifact {artifact_id!r} not found in project {project_id!r}")
            version = entry.latest_version
        path = self._artifact_version_path(project_id, artifact_id, version)
        if not path.exists():
            raise FileNotFoundError(f"artifact {artifact_id!r} version {version} not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def latest_artifact_for_tool(
        self, project_id: str, meta: ProjectMetadata, tool_id: str, *, oldest: bool = False,
    ) -> dict[str, Any] | None:
        """Among this project's saved artifacts matching `tool_id`, the one
        picked by the ARTIFACT's own `updated_at` (a field inside the
        stored JSON, caller-supplied like every other timestamp in this
        schema layer -- not this store's project.json `updated_at`).
        Newest wins by default, tie-broken deterministically by
        artifact_id so two artifacts saved in the same instant never
        depend on dict iteration order.

        This is the one shared lookup for "a project's latest artifact of
        tool_id X" -- routes/gates.py's _build_snapshot, routes/stats.py's
        _latest_msa_verdict, and prescore/cross_checks.py's cross-tool
        checks all now call this instead of each iterating
        meta.artifact_index.items() on their own (critic-confirmed defect:
        the three had silently diverged -- meta.artifact_index iterates in
        the on-disk order, which is ALPHABETICAL BY ARTIFACT_ID because
        project.json is written sort_keys=True, not chronological.
        _latest_msa_verdict and the old _latest_artifact returned the
        FIRST match -- alphabetically-first, not latest. _build_snapshot's
        plain for-loop with no break kept overwriting on every match --
        alphabetically-LAST, also not actually "latest" by any timestamp,
        just a different accident. stats.py's own docstring claimed this
        was "the identical lookup" to gates.py's; it never was).

        Pass oldest=True to invert the comparison -- e.g.
        prescore/cross_checks.py's charter-vs-COPQ check wants the
        Define-phase COPQ the charter's business-impact figure actually
        quoted, not a later Wrap re-run (a project can legitimately have
        two T-02 artifacts, one per phase; "newest" would silently swap in
        the wrong one the moment a Wrap COPQ exists).

        None when no artifact of this tool_id has ever been saved."""
        candidates = [
            (artifact_id, self.load_artifact(project_id, artifact_id, entry.latest_version))
            for artifact_id, entry in meta.artifact_index.items()
            if entry.tool_id == tool_id
        ]
        if not candidates:
            return None
        pick = min if oldest else max
        # Tie-break key intentionally reuses the same (updated_at, artifact_id)
        # pair for both min and max -- deterministic either way, and never
        # dependent on the dict's own iteration order.
        return pick(candidates, key=lambda pair: (pair[1].get("updated_at") or "", pair[0]))[1]

    def list_versions(self, project_id: str, artifact_id: str) -> list[int]:
        directory = self._project_dir(project_id) / "artifacts" / artifact_id
        if not directory.exists():
            return []
        versions: list[int] = []
        for p in directory.glob("v*.json"):
            try:
                versions.append(int(p.stem[1:]))
            except ValueError:
                continue  # not one of ours; ignore rather than fail a whole listing
        return sorted(versions)

    def append_override(
        self, project_id: str, gate_id: str, reason: str, timestamp: str, missing: list[str] | None = None
    ) -> OverrideLogEntry:
        entry = OverrideLogEntry(
            gate_id=gate_id, reason=reason, timestamp=timestamp, missing=missing or []
        )  # raises on empty reason
        _append_jsonl(self._overrides_path(project_id), entry.model_dump(mode="json"))
        return entry

    def list_overrides(self, project_id: str) -> list[OverrideLogEntry]:
        path = self._overrides_path(project_id)
        if not path.exists():
            return []
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(OverrideLogEntry.model_validate(json.loads(line)))
        return entries

    def resolved_project_path(self, project_id: str) -> Path:
        """The real, absolute on-disk folder for `project_id` -- what
        routes/projects.py's /info endpoint reports to the desktop shell,
        replacing the documented-default guess project/path.ts previously
        had to fall back on (no endpoint reported a project's real path)."""
        return self._project_dir(project_id).resolve()
