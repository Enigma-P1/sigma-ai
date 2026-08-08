"""Shared plumbing for the three scenario drivers: project reset, dataset/
floorplan upload helpers, the save+prescore pair every artifact step runs,
and small CSV readers over the read-only fixture data."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

from ..lib.client import EngineClient, b64
from ..lib.recorder import Recorder

REPO_ROOT = Path(__file__).resolve().parents[3]
SCENARIOS_DATA_ROOT = REPO_ROOT / "evals" / "scenarios"
DEMO_ROOT = REPO_ROOT / "demo"

PROJECTS_ROOT_ENV_VAR = "SIGMA_PROJECTS_ROOT"
DEFAULT_PROJECTS_ROOT = Path.home() / ".sigma-ai" / "projects"


def projects_root() -> Path:
    return Path(os.environ.get(PROJECTS_ROOT_ENV_VAR, str(DEFAULT_PROJECTS_ROOT)))


def reset_project(engine: EngineClient, project_id: str, name: str, created_at: str) -> dict[str, Any]:
    """Delete any prior on-disk copy of `project_id` (so freeze and every
    replay both start a scenario from a byte-identical, empty project --
    the harness owns this project id, nothing else should be writing to
    it) then create it fresh. Not itself a recorded golden step -- pure
    setup, not a computed response."""
    import shutil

    shutil.rmtree(projects_root() / project_id, ignore_errors=True)
    resp = engine.post_ok("/project/create", {"project_id": project_id, "name": name, "created_at": created_at})
    return resp.body


# Every tool below carries >=1 field that this engine's artifact layer
# "unconditionally recomputes on every validate" (artifacts/*.py's own
# recurring docstring phrase -- proof.py, msa.py, hypothesis.py,
# solution_matrix.py, fishbone.py, fmea.py, process_map.py, spaghetti.py,
# time_study.py, yield_calc.py, copq.py, pilot_plan.py all use it
# verbatim). Since the field is thrown away and rebuilt from the artifact's
# OTHER (real-input) fields regardless of what's submitted, there is never
# a reason to submit a stale computed value -- and submitting one is
# actively risky: if the artifact schema has grown a new required
# sub-field since a fixture was authored (T-20's `verdict.package_attribution`,
# added at M4, is exactly this), Pydantic fails on the STALE shape before
# the recompute ever runs. Stripping to None sidesteps that entirely (every
# one of these fields is typed `X | None = None`), which is also simply
# correct: a fixture file only ever needs to carry REAL inputs.
TOP_LEVEL_COMPUTED_FIELDS: dict[str, tuple[str, ...]] = {
    "T-02": ("total",),
    "T-06": ("longest_step", "constraint_step"),
    "T-07": ("metrics",),
    "T-09": ("element_stats", "work_sampling_summary"),
    "T-10": ("rty_result", "dpmo_result"),
    "T-12": ("result",),
    "T-15": ("verified_causes",),
    "T-16": ("blocking_flags", "sorted_view"),
    "T-17": ("routing", "result", "refused"),
    "T-18": ("scores", "ranked_fix_list"),
    "T-19": ("package_attribution_note",),
    "T-20": ("before_baseline", "after_baseline", "test_result", "guardrail_report", "gap", "verdict"),
    # T-21 and T-22 need extra, structure-specific handling (freeze
    # mechanics; a nested check_in_schedule) -- see prepare_control_chart /
    # prepare_control_plan below, called explicitly by drivers instead.
}


def strip_computed(tool_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Delete (not null-out) each computed key so every field's OWN default
    applies -- most are `X | None = None`, but e.g. HypothesisRunArtifact.
    refused is a plain `bool = False`, which `None` would fail type
    validation on."""
    body = dict(body)
    for key in TOP_LEVEL_COMPUTED_FIELDS.get(tool_id, ()):
        body.pop(key, None)
    return body


def prepare_control_chart(body: dict[str, Any], *, action_at: str) -> dict[str, Any]:
    """T-21's `imr_baseline`/`p_baseline`/`signals` are the one deliberate
    exception to "unconditionally recomputed" (control_chart.py: "FROZEN
    MEANS FROZEN" -- they only recompute when `freeze_requested`/
    `recalculate_reason` triggers it). To get a fresh, verifiable freeze
    out of a re-posted fixture (rather than trusting whatever baseline
    numbers happened to be typed into the file), this clears every frozen/
    derived field and sets `freeze_requested=True` + `action_at` so the
    engine (re)computes the freeze from `imr_values`/`p_subgroups` itself."""
    body = dict(body)
    for key in ("imr_baseline", "p_baseline", "signals", "frozen_at", "source_dataset_hash",
                "frozen_window_values", "frozen_window_subgroups"):
        body[key] = None
    body["recalculation_log"] = []
    body["acknowledgments"] = {}
    body["freeze_requested"] = True
    body["recalculate_reason"] = None
    body["action_at"] = action_at
    return body


def prepare_control_plan(body: dict[str, Any]) -> dict[str, Any]:
    """T-22's computed fields live partly at the top level (`plan_health`)
    and partly nested one level down inside `check_in_schedule`
    (`next_due`, and each `completed[].result`) -- same "unconditionally
    recomputed" contract, just not a flat top-level key."""
    body = dict(body)
    body["plan_health"] = None
    cis = body.get("check_in_schedule")
    if cis:
        cis = dict(cis)
        cis["next_due"] = None
        cis["completed"] = [dict(c, result=None) for c in cis.get("completed", [])]
        body["check_in_schedule"] = cis
    return body


def save_and_prescore(
    recorder: Recorder, engine: EngineClient, project_id: str, tool_id: str, step_prefix: str, body: dict[str, Any],
    *, strip: bool = True,
) -> dict[str, Any]:
    """The triple almost every artifact step runs, in this order:

    1. POST /artifacts/{tool_id}/validate -- the FULL computed artifact
       echo (routes/artifacts.py's `validate_artifact` returns
       `{"valid": true, "artifact": <every field, freshly recomputed>}`).
       This -- not the save call below -- is where "capture every computed
       response" actually lives, and is recorded as `{prefix}.validate`.
    2. POST /project/{project_id}/artifacts/{tool_id} -- persists a new
       version. Its own HTTP response is deliberately tiny
       (`{"artifact_id", "tool_id", "version"}`, routes/artifacts.py's
       `save_artifact`) -- recorded anyway as `{prefix}.save`, since the
       version-number sequence (1, 2, 3, ...) is itself a real, worth-
       freezing piece of deterministic engine behavior (persistence +
       versioning), just a much smaller one than step 1's echo.
    3. POST /prescore/{tool_id} -- the rule-based rubric checks (PLAN
       §5.1's "deterministic pre-score first"), recorded as `{prefix}.prescore`.

    Returns the validate call's `artifact` (the rich computed object) so
    the driver can chain real computed values into later steps.
    `strip=False` opts out of the top-level computed-field stripping above
    (T-21/T-22 handle their own via prepare_control_chart/prepare_control_plan
    before calling this, since their computed fields aren't flat top-level
    ones this generic pass would find)."""
    if strip:
        body = strip_computed(tool_id, body)
    validated = recorder.call(
        f"{step_prefix}.validate", "POST", f"/artifacts/{tool_id}/validate", body, tool_ids=[tool_id],
    )
    recorder.call(
        f"{step_prefix}.save", "POST", f"/project/{project_id}/artifacts/{tool_id}", body, tool_ids=[tool_id],
    )
    recorder.call(
        f"{step_prefix}.prescore", "POST", f"/prescore/{tool_id}", body, tool_ids=[tool_id],
    )
    return validated["artifact"]


def validate_only(
    recorder: Recorder, engine: EngineClient, tool_id: str, step_name: str, body: dict[str, Any],
    *, expect_status: tuple[int, ...] = (200,),
) -> Any:
    return recorder.call(f"{step_name}", "POST", f"/artifacts/{tool_id}/validate", body,
                          tool_ids=[tool_id], expect_status=expect_status)


def prescore_only(recorder: Recorder, tool_id: str, step_name: str, body: dict[str, Any]) -> Any:
    return recorder.call(f"{step_name}", "POST", f"/prescore/{tool_id}", body, tool_ids=[tool_id])


def merge(body: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """Shallow merge -- used to build the next state of a control-chart
    artifact from the PREVIOUS validate response (S-2's control chart goes
    through freeze -> extend-without-refreezing -> logged-recalculate, all
    on one artifact_id; each step's body is the last one's full computed
    echo with a few fields overridden)."""
    return {**body, **overrides}


def gate_check(recorder: Recorder, project_id: str, gate_id: str, *, suffix: str = "") -> Any:
    name = f"gate.{gate_id}{suffix}"
    return recorder.call(name, "POST", "/gates/check", {"gate_id": gate_id, "project_id": project_id})


def upload_dataset(
    recorder: Recorder, engine: EngineClient, project_id: str, step_name: str, csv_path: Path, created_at: str,
    *, tool_ids: list[str], do_preview: bool = True,
) -> dict[str, Any]:
    content = csv_path.read_bytes()
    body = {"source_filename": csv_path.name, "content_base64": b64(content)}
    if do_preview:
        recorder.call(f"{step_name}.preview", "POST", f"/project/{project_id}/datasets/preview", body, tool_ids=tool_ids)
    saved = recorder.call(
        f"{step_name}.save", "POST", f"/project/{project_id}/datasets",
        {**body, "created_at": created_at}, tool_ids=tool_ids,
    )
    return saved


def upload_floorplan(
    recorder: Recorder, engine: EngineClient, project_id: str, step_name: str, png_path: Path, created_at: str,
    *, tool_ids: list[str],
) -> dict[str, Any]:
    content = png_path.read_bytes()
    return recorder.call(
        f"{step_name}.upload", "POST", f"/project/{project_id}/floorplans",
        {"source_filename": png_path.name, "content_base64": b64(content), "created_at": created_at},
        tool_ids=tool_ids,
    )


# --- CSV readers over the read-only fixture data ------------------------

def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_csv_column(path: Path, column: str) -> list[float]:
    return [float(row[column]) for row in read_csv_rows(path)]
