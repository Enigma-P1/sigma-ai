"""Phase gate state machine (PLAN §4.2): math/logic guards are hard,
sequence gates are soft-with-a-logged-override. Requirements live in one
data table (GATE_TABLE) so check() has no per-gate if-chain -- adding a
gate means adding a row, not a branch. The exceptions are gates that
inspect a field *value* or non-artifact state, not mere artifact
presence, so they can't be expressed as a required-tool-ids row alone:
the picker's EXIT-01 route, the T-12 capability-language verdict, the
measure exit's saved-dataset requirement, and the analyze exit's
verified-cause-or-hypothesis-run either/or -- see _missing_for and the
two value-gate branches in check().

Every sequence gate Intake through Wrap is now a real soft gate (M6 eval
fix: the four Measure-and-later transitions shipped across M2-M4 but sat
as not-yet-built stubs until the eval campaign caught it). Soft means
exactly what PLAN §4.2 promises: "a gate warning lists what's missing,
and the user can proceed with a required, logged override reason."
Artifact requirements per transition come from the matrix §1 phase
column, kept honest about what is checkable: T-13 (baseline) writes no
artifact -- the saved dataset is its evidence, so the Measure exit checks
dataset presence instead of a T-13 row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from pydantic import BaseModel, Field

from .project_store import OverrideLogEntry, ProjectStore

Phase = Literal["Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap"]
PHASE_ORDER: tuple[Phase, ...] = ("Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap")

# NOT_YET_BUILT is gone from this Literal on purpose (M6): no stub rows
# remain in GATE_TABLE, so no code path can produce it anymore. The
# desktop's GateStatus mirror still tolerates the string, harmlessly.
GateStatus = Literal["CLEAR", "SOFT_BLOCK", "HARD_BLOCK"]


class GateResult(BaseModel):
    status: GateStatus
    missing: list[str] = Field(default_factory=list)
    reason: str | None = None
    # Set when a SOFT_BLOCK cleared because the project's override log
    # (project_store.py's overrides.log.jsonl) already carries a reason
    # logged against exactly this missing-tool-ids set -- see check()'s
    # _covering_override. Never set for HARD_BLOCK: hard gates can't be
    # overridden (PLAN §4.2).
    overridden: bool = False
    override_reason: str | None = None


class ProjectSnapshot(BaseModel):
    """The slice of project state a gate check needs, assembled by the
    caller from project_store data. Keeps gates.py free of file I/O and
    trivial to unit test with hand-built snapshots."""

    artifact_tool_ids: set[str] = Field(default_factory=set)  # tool_ids with >=1 saved version
    picker_route: str | None = None  # latest T-01 artifact's route, if any
    # Latest T-12 (Measurement Check) artifact's verdict, if any T-12
    # artifact has ever been saved for this project -- like picker_route,
    # this inspects a field *value*, not mere tool presence, because the
    # frozen rule (matrix §4a EXIT-02) cares which verdict, not whether a
    # check ever ran. routes/gates.py's _build_snapshot populates this the
    # same way it populates picker_route.
    msa_verdict: str | None = None
    # Whether ANY T-12 artifact exists at all (M6 eval fix, persona
    # finding FL-07): msa_verdict=None used to conflate "no T-12 ever ran"
    # with "T-12 on file, no verdict recorded", and the capability-language
    # gate answered both with the same bare CLEAR a genuinely-passed check
    # earns -- indistinguishable downstream. This flag keeps the honest
    # difference; prescore/control_chart.py's measurement_check_on_file
    # consumes the same pair (routes/prescore.py threads it through).
    msa_on_file: bool = False
    # Measure-exit requirements that live outside the artifact index
    # (matrix §1: T-13 writes no artifact -- a saved dataset is its
    # evidence) and the Analyze exit's verified-cause count (None = no
    # T-15 saved; 0 = a fishbone exists but nothing on it is verified).
    has_dataset: bool = False
    fishbone_verified_cause_count: int | None = None


@dataclass(frozen=True)
class GateRequirement:
    gate_id: str
    from_phase: Phase
    to_phase: Phase
    kind: Literal["hard", "soft"]
    description: str
    required_tool_ids: tuple[str, ...] = ()


GATE_TABLE: tuple[GateRequirement, ...] = (
    GateRequirement(
        gate_id="intake_picker_present", from_phase="Intake", to_phase="Define", kind="soft",
        description="Project Picker (T-01) must exist before Define work begins.",
        required_tool_ids=("T-01",),
    ),
    GateRequirement(
        gate_id="intake_picker_not_exit01", from_phase="Intake", to_phase="Define", kind="hard",
        description="Picker route must not be EXIT-01 (matrix §4a) to proceed to Define.",
    ),
    GateRequirement(
        gate_id="define_to_measure", from_phase="Define", to_phase="Measure", kind="soft",
        description="Define exit soft-requires Charter + SIPOC + VoC/CTQ complete (PLAN §4.2).",
        required_tool_ids=("T-03", "T-04", "T-05"),
    ),
    GateRequirement(
        gate_id="measure_to_analyze", from_phase="Measure", to_phase="Analyze", kind="soft",
        description=(
            "Measure exit soft-requires a data collection plan (T-11), a measurement check (T-12), and at least "
            "one saved dataset (matrix §1 Measure rows; T-13 writes no artifact -- the saved dataset is its "
            "evidence)."
        ),
        required_tool_ids=("T-11", "T-12"),
    ),
    GateRequirement(
        gate_id="measure_capability_language_requires_msa_pass", from_phase="Measure", to_phase="Analyze", kind="hard",
        description=(
            "Capability-claim language is hard-blocked while the project's latest T-12 measurement check reads "
            "fail (matrix §4a EXIT-02) -- fix the measurement system and get a passing T-12 re-run first."
        ),
    ),
    GateRequirement(
        gate_id="analyze_to_improve", from_phase="Analyze", to_phase="Improve", kind="soft",
        description=(
            "Analyze exit soft-requires verified-cause evidence: a fishbone (T-15) with at least one verified "
            "cause, or a hypothesis run (T-17) -- either satisfies (matrix §1 Analyze rows; the T-15 schema "
            "guarantees every verified cause carries evidence)."
        ),
    ),
    GateRequirement(
        gate_id="improve_to_control", from_phase="Improve", to_phase="Control", kind="soft",
        description=(
            "Improve exit soft-requires a pilot plan (T-19) and a before/after proof (T-20) (matrix §1 Improve rows)."
        ),
        required_tool_ids=("T-19", "T-20"),
    ),
    GateRequirement(
        gate_id="control_to_wrap", from_phase="Control", to_phase="Wrap", kind="soft",
        description=(
            "Control exit soft-requires a control chart (T-21) and a control plan (T-22) (matrix §1 Control rows)."
        ),
        required_tool_ids=("T-21", "T-22"),
    ),
)

# Plain-language missing-list entries for requirements that are not a bare
# tool id. The desktop's GateBanner maps tool-id entries to tool names and
# renders anything else verbatim, so these read as sentences in the
# "Missing: ..." line; the override log's exact-set matching
# (_covering_override) works on them like any other string.
_MISSING_DATASET = "a saved dataset"
_MISSING_FISHBONE_WITH_VERIFIED_CAUSE = "either a fishbone (T-15) with at least one verified cause"
_MISSING_VERIFIED_CAUSE_ON_FISHBONE = "either at least one verified cause on the fishbone (T-15 exists, none verified yet)"
_MISSING_HYPOTHESIS_RUN = "or a hypothesis run (T-17)"

# The four M6 soft gates carry their missing list restated in
# GateResult.reason as one plain-English sentence (the eval brief's "lists
# exactly what's missing in plain language"); the two pre-existing soft
# gates keep their original bare-missing shape untouched.
_SOFT_GATES_WITH_REASON = frozenset(
    {"measure_to_analyze", "analyze_to_improve", "improve_to_control", "control_to_wrap"}
)


def _missing_for(req: GateRequirement, snapshot: ProjectSnapshot) -> list[str]:
    """The one shared missing-list computation check() and override() both
    use, so an override always records exactly the set a later check()
    compares against (_covering_override's contract). Generic
    required-tool-ids presence first, then the two soft gates whose
    requirements aren't expressible as artifact presence alone."""
    missing = [t for t in req.required_tool_ids if t not in snapshot.artifact_tool_ids]
    if req.gate_id == "measure_to_analyze" and not snapshot.has_dataset:
        # T-13 (baseline) writes no artifact -- the saved dataset is its
        # evidence (matrix §1), so dataset presence stands in for it.
        missing.append(_MISSING_DATASET)
    if req.gate_id == "analyze_to_improve":
        has_verified_cause = (snapshot.fishbone_verified_cause_count or 0) >= 1
        has_hypothesis_run = "T-17" in snapshot.artifact_tool_ids
        if not has_verified_cause and not has_hypothesis_run:
            fishbone_entry = (
                _MISSING_FISHBONE_WITH_VERIFIED_CAUSE
                if snapshot.fishbone_verified_cause_count is None
                else _MISSING_VERIFIED_CAUSE_ON_FISHBONE
            )
            missing.extend([fishbone_entry, _MISSING_HYPOTHESIS_RUN])
    return missing


_BY_ID = {g.gate_id: g for g in GATE_TABLE}


def _covering_override(
    gate_id: str, missing: list[str], overrides: Sequence[OverrideLogEntry]
) -> OverrideLogEntry | None:
    """The logged override for `gate_id` whose recorded missing set exactly
    matches the CURRENT missing set, if any (last/most-recent match wins).
    An override logged against a different missing set doesn't match --
    artifacts changed since, so the reason on file no longer describes what
    is being skipped now, and the gate must not silently clear. Records
    written before `missing` existed default it to `[]` (project_store.py),
    which can never equal a real (non-empty) missing set, so old records
    load fine and are correctly treated as not covering anything."""
    current = set(missing)
    match: OverrideLogEntry | None = None
    for entry in overrides:
        if entry.gate_id == gate_id and set(entry.missing) == current:
            match = entry  # keep scanning -- last entry in log order wins
    return match


def build_project_snapshot(store: ProjectStore, project_id: str) -> ProjectSnapshot:
    """The one shared way to build a ProjectSnapshot from a live project
    (promoted from routes/gates.py's formerly-private `_build_snapshot`,
    M5 unit 2: advisor/modes.py's tollgate context selector needed the
    identical snapshot gates.check() consumes, and duplicating this logic
    a second time risked exactly the kind of silent divergence
    ProjectStore.latest_artifact_for_tool's own docstring warns about --
    see that docstring for the concrete history of that failure mode).
    Raises FileNotFoundError for an unknown project, same contract as
    every other store-backed lookup in this engine."""
    from .datasets import DatasetStore  # local import, cross_checks.py's same cycle-avoidance move

    meta = store.load_project(project_id)  # FileNotFoundError propagates
    tool_ids = {entry.tool_id for entry in meta.artifact_index.values()}

    picker_data = store.latest_artifact_for_tool(project_id, meta, "T-01")
    msa_data = store.latest_artifact_for_tool(project_id, meta, "T-12")
    fishbone_data = store.latest_artifact_for_tool(project_id, meta, "T-15")
    picker_route = picker_data.get("route") if picker_data is not None else None
    msa_verdict = (msa_data.get("result") or {}).get("verdict") if msa_data is not None else None

    fishbone_verified_cause_count: int | None = None
    if fishbone_data is not None:
        # verified_causes is server-computed on every validate
        # (fishbone.py), so it's present on any saved T-15; the causes-list
        # recount is a defensive fallback for a hand-edited/legacy file,
        # counting by the same status the computation itself keys on.
        computed_count = ((fishbone_data.get("verified_causes") or {}).get("value") or {}).get("count")
        if isinstance(computed_count, int):
            fishbone_verified_cause_count = computed_count
        else:
            causes = fishbone_data.get("causes") or []
            fishbone_verified_cause_count = sum(
                1 for c in causes if isinstance(c, dict) and c.get("status") == "verified"
            )

    return ProjectSnapshot(
        artifact_tool_ids=tool_ids,
        picker_route=picker_route,
        msa_verdict=msa_verdict,
        msa_on_file=msa_data is not None,
        has_dataset=bool(DatasetStore(store).list_datasets(project_id)),
        fishbone_verified_cause_count=fishbone_verified_cause_count,
    )


def check(gate_id: str, snapshot: ProjectSnapshot, overrides: Sequence[OverrideLogEntry] = ()) -> GateResult:
    req = _BY_ID.get(gate_id)
    if req is None:
        raise KeyError(f"unknown gate_id {gate_id!r}")

    if gate_id == "intake_picker_not_exit01":
        # The only gate that can't be a generic required-tool-ids presence
        # check: it inspects the picker's *route value*, not whether a
        # picker artifact merely exists. Frozen rule source:
        # docs/traceability-matrix.md §4a, EXIT-01 trigger. Hard blocks
        # can't be overridden (PLAN §4.2), so `overrides` plays no part here.
        if snapshot.picker_route == "EXIT-01":
            return GateResult(
                status="HARD_BLOCK",
                reason="Picker route is EXIT-01: not a viable first project as scoped (matrix §4a).",
            )
        return GateResult(status="CLEAR")

    if gate_id == "measure_capability_language_requires_msa_pass":
        # Second field-value-inspecting special case (see the picker
        # branch above): a hard gate on the latest T-12 *verdict*, not on
        # T-12's mere presence. Hard blocks can't be overridden (PLAN
        # §4.2): this matches rubric R-MEA-07's "the suite blocks the
        # capability-language automatically," not a request the user can
        # talk their way past.
        #
        # The no-verdict case stays CLEAR by status -- the frozen rule
        # (matrix §4a EXIT-02) hard-blocks a FAILED check only, T-12
        # presence is the soft measure_to_analyze gate's job (overridable
        # there, per PLAN §4.2's soft-sequence promise), and a T-21
        # freeze without a T-12 is flagged by prescore/control_chart.py's
        # measurement_check_on_file -- but it now carries a reason that
        # says outright no checked measurement backs it (M6 eval fix,
        # persona finding FL-07: this CLEAR used to be byte-identical to
        # a genuinely-passed check's, so a project that never ran T-12
        # read as if its measurement were checked).
        if snapshot.msa_verdict == "fail":
            return GateResult(
                status="HARD_BLOCK",
                reason=(
                    "Measurement check failed (EXIT-02): fix the measurement system and get a passing T-12 "
                    "re-run before capability language is trusted."
                ),
            )
        if snapshot.msa_verdict is None:
            on_file = (
                "A T-12 exists but its latest version records no verdict"
                if snapshot.msa_on_file
                else "No measurement check (T-12) is on file for this project"
            )
            return GateResult(
                status="CLEAR",
                reason=(
                    f"{on_file}. This CLEAR only means no failed check is blocking capability language -- it "
                    "does not attest a checked measurement. Run T-12 and get a recorded verdict before "
                    "trusting capability claims."
                ),
            )
        return GateResult(
            status="CLEAR",
            reason=(
                f"Latest T-12 measurement check reads {snapshot.msa_verdict!r} -- capability language is "
                "not blocked."
            ),
        )

    missing = _missing_for(req, snapshot)
    if not missing:
        return GateResult(status="CLEAR")

    covering = _covering_override(gate_id, missing, overrides)
    if covering is not None:
        return GateResult(status="CLEAR", overridden=True, override_reason=covering.reason)

    reason = None
    if gate_id in _SOFT_GATES_WITH_REASON:
        reason = (
            f"{req.description} Missing now: {', '.join(missing)}. You can proceed anyway with a logged "
            "override reason (PLAN §4.2)."
        )
    return GateResult(status="SOFT_BLOCK", missing=missing, reason=reason)


def override(
    gate_id: str, project_id: str, reason: str, timestamp: str, store: ProjectStore, snapshot: ProjectSnapshot
) -> OverrideLogEntry:
    """Clear a soft block with a logged, non-empty reason. Hard gates
    refuse outright -- PLAN §4.2 draws the hard/soft line at "the math (or
    the frozen routing rule) would be wrong," not at inconvenience, and
    that line doesn't move for a determined override attempt. `snapshot` is
    the project state *at override time*: the log entry records which
    tool_ids were missing right now, so a later check() can tell a
    still-covering override from a stale one (see _covering_override)."""
    req = _BY_ID.get(gate_id)
    if req is None:
        raise KeyError(f"unknown gate_id {gate_id!r}")
    if req.kind == "hard":
        raise PermissionError(f"gate {gate_id!r} is hard and cannot be overridden")
    missing = _missing_for(req, snapshot)
    return store.append_override(project_id, gate_id, reason, timestamp, missing=missing)  # raises on empty reason
