"""Step recording, golden freeze/replay, and the per-scenario manifest.

A `Recorder` is handed to each scenario driver. The driver calls
`recorder.call(...)` for every engine request that should become (or be
checked against) a golden file; the recorder handles normalization,
writing (freeze mode), and diffing (replay mode). One `Recorder` covers
exactly one scenario -- `evals/goldens/<scenario_id>/`.
"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .client import EngineClient
from .normalize import canonical_json_bytes, canonicalize_for_golden, hash_value

Mode = Literal["freeze", "replay"]

MAX_DIFF_LINES = 60


@dataclass
class StepDiff:
    step: str
    kind: Literal["missing_golden", "mismatch", "unexpected_status", "orphaned_golden"]
    detail: str


@dataclass
class ManifestStep:
    name: str
    tool_ids: list[str]
    method: str
    path: str
    status_code: int
    input_hash: str


@dataclass
class ScenarioReport:
    scenario_id: str
    mode: Mode
    steps_run: int = 0
    diffs: list[StepDiff] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.diffs


class Recorder:
    def __init__(self, scenario_id: str, engine: EngineClient, goldens_root: Path, mode: Mode) -> None:
        self.scenario_id = scenario_id
        self.engine = engine
        self.dir = goldens_root / scenario_id
        self.mode = mode
        self.report = ScenarioReport(scenario_id=scenario_id, mode=mode)
        self._manifest_steps: list[ManifestStep] = []
        self._seen_names: set[str] = set()
        self._touched_files: set[str] = set()
        if mode == "freeze":
            # A fresh freeze reflects EXACTLY the current driver's step set
            # -- wipe any prior run's files first so a renamed/removed step
            # can never leave an orphaned golden behind (the orphaned-
            # golden check in finalize() then has nothing stale to trip on
            # for a normal freeze; it still fires for a REPLAY, which never
            # deletes anything, exactly where "a step vanished silently" is
            # the thing worth catching).
            import shutil

            shutil.rmtree(self.dir, ignore_errors=True)
            self.dir.mkdir(parents=True, exist_ok=True)

    # -- the one call every driver step goes through -------------------
    def call(
        self,
        name: str,
        method: str,
        path: str,
        json_body: Any = None,
        *,
        tool_ids: list[str] | None = None,
        expect_status: tuple[int, ...] = (200,),
    ) -> Any:
        """POST/GET `path`, record+diff the (normalized) response body under
        golden name `name`, and return the RAW (non-normalized) parsed body
        so the driver can chain values (dataset ids, computed numbers, ...)
        into later steps. Raises RuntimeError if the response status isn't
        one of `expect_status` -- a scenario driver declares which statuses
        are legitimate for a given step (a 422 IS the expected outcome for
        an EXIT-10 bundling probe, for instance)."""
        if name in self._seen_names:
            raise RuntimeError(f"duplicate step name {name!r} in scenario {self.scenario_id!r}")
        self._seen_names.add(name)

        if method == "GET":
            resp = self.engine.get(path)
        else:
            resp = self.engine.post(path, json_body)

        if resp.status_code not in expect_status:
            raise RuntimeError(
                f"[{self.scenario_id}] step {name!r}: {method} {path} -> {resp.status_code} "
                f"(expected one of {expect_status}); body={resp.body!r}"
            )

        input_hash = hash_value({"path": path, "method": method, "body": json_body})
        self._manifest_steps.append(
            ManifestStep(name=name, tool_ids=list(tool_ids or []), method=method, path=path,
                         status_code=resp.status_code, input_hash=input_hash)
        )
        self._record_golden(name, resp.body)
        self.report.steps_run += 1
        return resp.body

    # -- golden file plumbing -------------------------------------------
    def _golden_path(self, name: str) -> Path:
        return self.dir / f"{_slug(name)}.json"

    def _record_golden(self, name: str, body: Any) -> None:
        canon = canonicalize_for_golden(body)
        path = self._golden_path(name)
        self._touched_files.add(path.name)
        if self.mode == "freeze":
            path.write_bytes(canonical_json_bytes(canon))
            return
        # replay
        if not path.exists():
            self.report.diffs.append(StepDiff(name, "missing_golden", f"no golden file at {path}"))
            return
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        if on_disk != canon:
            self.report.diffs.append(StepDiff(name, "mismatch", _readable_diff(path.name, on_disk, canon)))

    def write_extra(self, filename: str, obj: Any) -> Path:
        """For scenario-level artifacts that aren't a single engine call's
        response (none currently needed beyond manifest.json, but kept
        generic for the coverage/golden-id-map writers to reuse the same
        canonical-write + diff path)."""
        canon = canonicalize_for_golden(obj)
        path = self.dir / filename
        self._touched_files.add(path.name)
        if self.mode == "freeze":
            self.dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_json_bytes(canon))
            return path
        if not path.exists():
            self.report.diffs.append(StepDiff(filename, "missing_golden", f"no golden file at {path}"))
            return path
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        if on_disk != canon:
            self.report.diffs.append(StepDiff(filename, "mismatch", _readable_diff(filename, on_disk, canon)))
        return path

    def finalize(self) -> ScenarioReport:
        """Write (freeze) or diff (replay) manifest.json, then check for
        orphaned goldens -- a file on disk this run never touched, which
        means a step was removed/renamed without a re-freeze (silent
        coverage loss the diff-per-step loop above can't otherwise catch)."""
        manifest = {
            "scenario_id": self.scenario_id,
            "step_count": len(self._manifest_steps),
            "steps": [
                {
                    "name": s.name, "tool_ids": s.tool_ids, "method": s.method,
                    "path": s.path, "status_code": s.status_code, "input_hash": s.input_hash,
                }
                for s in self._manifest_steps
            ],
        }
        self.write_extra("manifest.json", manifest)

        if self.dir.exists():
            for existing in sorted(self.dir.glob("*.json")):
                if existing.name not in self._touched_files:
                    self.report.diffs.append(
                        StepDiff(existing.stem, "orphaned_golden",
                                 f"{existing.name} exists on disk but no step produced it this run "
                                 "(a step was renamed/removed without re-freezing)")
                    )
        return self.report

    @property
    def manifest_steps(self) -> list[ManifestStep]:
        return list(self._manifest_steps)


def _slug(name: str) -> str:
    return name.replace("/", "_").replace(" ", "_")


def _readable_diff(label: str, old: Any, new: Any) -> str:
    old_lines = json.dumps(old, sort_keys=True, indent=2).splitlines()
    new_lines = json.dumps(new, sort_keys=True, indent=2).splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"{label} (frozen)", tofile=f"{label} (live)", lineterm=""))
    if len(diff) > MAX_DIFF_LINES:
        shown = diff[:MAX_DIFF_LINES]
        shown.append(f"... [{len(diff) - MAX_DIFF_LINES} more diff line(s) truncated]")
        diff = shown
    return "\n".join(diff)
