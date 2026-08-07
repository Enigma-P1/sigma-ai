"""Phase gate state machine (PLAN §4.2): math/logic guards are hard,
sequence gates are soft-with-a-logged-override. Requirements live in one
data table (GATE_TABLE) so check() has no per-gate if-chain -- adding a
gate means adding a row, not a branch. The one exception is the picker's
EXIT-01 rule, which inspects a field *value* (the route), not mere
artifact presence, so it can't be expressed as a required-tool-ids row;
see the comment on that branch in check().

Measure-phase-and-later gates are stubbed as NOT_YET_BUILT rows: the table
names every transition so PHASE_ORDER is complete end-to-end, but no math
guard is invented for phases this milestone doesn't build (M1 brief: "do
NOT invent math guards yet").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from .project_store import OverrideLogEntry, ProjectStore

Phase = Literal["Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap"]
PHASE_ORDER: tuple[Phase, ...] = ("Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap")

GateStatus = Literal["CLEAR", "SOFT_BLOCK", "HARD_BLOCK", "NOT_YET_BUILT"]


class GateResult(BaseModel):
    status: GateStatus
    missing: list[str] = Field(default_factory=list)
    reason: str | None = None


class ProjectSnapshot(BaseModel):
    """The slice of project state a gate check needs, assembled by the
    caller from project_store data. Keeps gates.py free of file I/O and
    trivial to unit test with hand-built snapshots."""

    artifact_tool_ids: set[str] = Field(default_factory=set)  # tool_ids with >=1 saved version
    picker_route: str | None = None  # latest T-01 artifact's route, if any


@dataclass(frozen=True)
class GateRequirement:
    gate_id: str
    from_phase: Phase
    to_phase: Phase
    kind: Literal["hard", "soft", "stub"]
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
        gate_id="measure_to_analyze", from_phase="Measure", to_phase="Analyze", kind="stub",
        description="not-yet-built: Measure math guards (stability/capability/MSA) ship in M2.",
    ),
    GateRequirement(
        gate_id="analyze_to_improve", from_phase="Analyze", to_phase="Improve", kind="stub",
        description="not-yet-built: Analyze gates (verified-cause ranking) ship in M3.",
    ),
    GateRequirement(
        gate_id="improve_to_control", from_phase="Improve", to_phase="Control", kind="stub",
        description="not-yet-built: Improve gates (proof/remaining-gap) ship in M4.",
    ),
    GateRequirement(
        gate_id="control_to_wrap", from_phase="Control", to_phase="Wrap", kind="stub",
        description="not-yet-built: Control gates (control plan/OCAP) ship in M4.",
    ),
)

_BY_ID = {g.gate_id: g for g in GATE_TABLE}


def check(gate_id: str, snapshot: ProjectSnapshot) -> GateResult:
    req = _BY_ID.get(gate_id)
    if req is None:
        raise KeyError(f"unknown gate_id {gate_id!r}")

    if req.kind == "stub":
        return GateResult(status="NOT_YET_BUILT", reason=req.description)

    if gate_id == "intake_picker_not_exit01":
        # The only gate that can't be a generic required-tool-ids presence
        # check: it inspects the picker's *route value*, not whether a
        # picker artifact merely exists. Frozen rule source:
        # docs/traceability-matrix.md §4a, EXIT-01 trigger.
        if snapshot.picker_route == "EXIT-01":
            return GateResult(
                status="HARD_BLOCK",
                reason="Picker route is EXIT-01: not a viable first project as scoped (matrix §4a).",
            )
        return GateResult(status="CLEAR")

    missing = [t for t in req.required_tool_ids if t not in snapshot.artifact_tool_ids]
    if missing:
        return GateResult(status="SOFT_BLOCK", missing=missing)
    return GateResult(status="CLEAR")


def override(gate_id: str, project_id: str, reason: str, timestamp: str, store: ProjectStore) -> OverrideLogEntry:
    """Clear a soft block with a logged, non-empty reason. Hard gates
    refuse outright -- PLAN §4.2 draws the hard/soft line at "the math (or
    the frozen routing rule) would be wrong," not at inconvenience, and
    that line doesn't move for a determined override attempt."""
    req = _BY_ID.get(gate_id)
    if req is None:
        raise KeyError(f"unknown gate_id {gate_id!r}")
    if req.kind == "hard":
        raise PermissionError(f"gate {gate_id!r} is hard and cannot be overridden")
    if req.kind == "stub":
        raise PermissionError(f"gate {gate_id!r} is not yet built")
    return store.append_override(project_id, gate_id, reason, timestamp)  # raises on empty reason
