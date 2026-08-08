"""T-06 Process Map (swimlane) + Waste Walk: lanes, steps tagged value-add /
non-value-add / enabling with the 8-wastes checklist, connectors, and an
optional demand block. When both demand fields are present and at least one
step carries a time, the engine names the bottleneck server-side (matrix
§5a A-7: longest effective step time vs the pace demand requires) --
CopqArtifact.total's pattern (artifacts/copq.py): the computation lives
next to the schema, stamped through provenance.compute(), and the
model_validator unconditionally overwrites whatever a client posts, so
`bottleneck` can only ever be the engine's own arithmetic.

Content-quality checks (a VA/NVA step with no reason, a checked waste with
no note, a lane with no owner) are prescore *flags*, not schema rejections
-- PLAN §4.2's hard-guard line is "the math/logic would be wrong," and none
of those are (see prescore/process_map.py, mirroring charter.py's risks
list and copq.py's docstring on this same split).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase

StepType = Literal["value_add", "non_value_add", "enabling"]

# The 8 canonical lean wastes -- DOWNTIME -- the superset the waste walk
# uses (traceability matrix §3a, 1.4.4: "T-06 waste walk uses the 8-waste
# superset", covering ASQ I.B.2).
WasteId = Literal[
    "defects", "overproduction", "waiting", "non_utilized_talent",
    "transportation", "inventory", "motion", "extra_processing",
]
WASTE_IDS: tuple[WasteId, ...] = (
    "defects", "overproduction", "waiting", "non_utilized_talent",
    "transportation", "inventory", "motion", "extra_processing",
)


class StepPosition(BaseModel):
    """One step's canvas position -- opaque display data (M2 brief): the
    engine stores and round-trips x/y, never interprets them."""

    x: float
    y: float


class Lane(BaseModel):
    lane_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    # Schema-loose on purpose (prescore/process_map.py's lane_owner_present
    # flags a blank one) -- a lane can exist while its owner is still being
    # worked out, same reasoning as CharterArtifact.risks starting empty.
    owner: str = ""


class WasteEntry(BaseModel):
    """One checked waste on a step. `note` is schema-loose for the same
    reason as Lane.owner above -- prescore's waste_notes_present is what
    catches a checked-but-empty note (rubric R-MEA-02: "concrete
    observations ... not a recited list")."""

    waste_id: WasteId
    note: str = ""


class ProcessStepModel(BaseModel):
    step_id: str = Field(min_length=1)
    lane_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    order: int = Field(ge=0)
    step_type: StepType
    # Required content-wise only for value_add/non_value_add (prescore's
    # reason_required_for_tagged_steps) -- an enabling step may leave this
    # blank, so the schema can't hard-require it uniformly.
    reason: str = ""
    time_minutes: float | None = Field(default=None, ge=0)
    defect_point: bool = False
    strata: list[str] = Field(default_factory=list)
    wastes: list[WasteEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_duplicate_wastes(self) -> "ProcessStepModel":
        ids = [w.waste_id for w in self.wastes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"step {self.step_id!r}: the same waste_id is checked more than once")
        return self


class Connector(BaseModel):
    from_step: str = Field(min_length=1)
    to_step: str = Field(min_length=1)
    label: str | None = None


class DemandBlock(BaseModel):
    """Both fields optional (M2 brief) -- a demand block can exist with
    only one field filled in while the other is still being gathered.
    compute_bottleneck below only fires once both are present."""

    available_time_minutes: float | None = Field(default=None, gt=0)
    demand_units: float | None = Field(default=None, gt=0)


class BottleneckResult(BaseModel):
    """A-7's constraint readout. Engine-computed only -- see
    ProcessMapArtifact.bottleneck below."""

    bottleneck_step_id: str
    bottleneck_step_name: str
    bottleneck_time_minutes: float
    pace_minutes_per_unit: float
    meets_pace: bool


class ProcessMapArtifact(ArtifactBase):
    tool_id: Literal["T-06"] = "T-06"

    lanes: list[Lane] = Field(min_length=1)
    steps: list[ProcessStepModel] = Field(min_length=1)
    connectors: list[Connector] = Field(default_factory=list)
    demand: DemandBlock | None = None
    # Keyed by step_id; opaque to the engine (M2 brief) -- layout survives
    # save/load but is never read by compute_bottleneck or prescore.
    layout: dict[str, StepPosition] = Field(default_factory=dict)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as CopqArtifact.total / MsaArtifact.result. None
    # whenever there isn't enough on the artifact to name a bottleneck from
    # (an honest "nothing to compute yet", not a zero).
    bottleneck: Computed[BottleneckResult] | None = None

    @model_validator(mode="after")
    def _referential_integrity(self) -> "ProcessMapArtifact":
        lane_ids = [l.lane_id for l in self.lanes]
        if len(lane_ids) != len(set(lane_ids)):
            raise ValueError("lane_id values must be unique")
        lane_id_set = set(lane_ids)

        step_ids = [s.step_id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_id values must be unique")
        step_id_set = set(step_ids)

        for step in self.steps:
            if step.lane_id not in lane_id_set:
                raise ValueError(f"step {step.step_id!r} references unknown lane_id {step.lane_id!r}")
        for c in self.connectors:
            if c.from_step not in step_id_set:
                raise ValueError(f"connector references unknown from_step {c.from_step!r}")
            if c.to_step not in step_id_set:
                raise ValueError(f"connector references unknown to_step {c.to_step!r}")
        return self

    @model_validator(mode="after")
    def _recompute_bottleneck(self) -> "ProcessMapArtifact":
        self.bottleneck = compute_bottleneck(self.steps, self.demand)
        return self


def compute_bottleneck(
    steps: list[ProcessStepModel], demand: DemandBlock | None
) -> Computed[BottleneckResult] | None:
    """A-7 (matrix §5a): longest effective step time vs the pace demand
    requires (available time / demand -- two fields), the bottleneck step
    named. None whenever the inputs to compute from aren't there yet -- an
    absent/partial demand block, or no step carrying a time -- which is an
    honest "nothing to name," not a zero."""
    if demand is None or demand.available_time_minutes is None or demand.demand_units is None:
        return None
    timed = [s for s in steps if s.time_minutes is not None]
    if not timed:
        return None

    max_time = max(s.time_minutes for s in timed)
    # Tie-break deterministically (lane_id, order, step_id) -- there's no
    # business meaning to breaking a tie one way or another, only a
    # requirement that the same inputs always name the same step.
    bottleneck_step = sorted(
        (s for s in timed if s.time_minutes == max_time),
        key=lambda s: (s.lane_id, s.order, s.step_id),
    )[0]

    pace = demand.available_time_minutes / demand.demand_units
    result = BottleneckResult(
        bottleneck_step_id=bottleneck_step.step_id,
        bottleneck_step_name=bottleneck_step.name,
        bottleneck_time_minutes=bottleneck_step.time_minutes,
        pace_minutes_per_unit=pace,
        meets_pace=bottleneck_step.time_minutes <= pace,
    )
    return compute(
        result,
        method=(
            "bottleneck = argmax(step.time_minutes) over steps with a time; "
            "pace_minutes_per_unit = available_time_minutes / demand_units (matrix §5a A-7)"
        ),
        input_data={
            "steps": [
                {"step_id": s.step_id, "lane_id": s.lane_id, "order": s.order, "time_minutes": s.time_minutes}
                for s in steps
            ],
            "demand": demand.model_dump(mode="json"),
        },
        assumptions_checked=[
            "pace is arithmetic on two fields (available time / demand), not full takt/line-balancing (T-32, v1.1)",
        ],
    )
