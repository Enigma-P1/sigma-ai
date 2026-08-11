"""T-06 Process Map (swimlane) + Waste Walk: lanes, steps tagged value-add /
non-value-add / enabling with the 8-wastes checklist, connectors, and an
optional demand block. The engine reports two distinct, separately
provenance-stamped readouts (fidelity fix, M2 close-out): `longest_step` is
the longest-timed step of ANY type (a pure wait included) whenever at least
one step carries a time; `constraint_step` is the longest-timed step among
PROCESSING steps only (step_type value_add or enabling), computed once both
demand fields are present -- a pure-wait non_value_add step can queue up
behind the real constraint, but it cannot *be* the constraint (matrix §5a
A-7 read together with the Theory-of-Constraints sense of the word: a queue
is the constraint's consequence, not the constraint itself). `meets_pace` is
judged on `constraint_step` alone. Both follow CopqArtifact.total's pattern
(artifacts/copq.py): the computation lives next to the schema, stamped
through provenance.compute(), and the model_validator unconditionally
overwrites whatever a client posts, so neither field can ever be anything
but the engine's own arithmetic.

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


class LongestStepResult(BaseModel):
    """The longest-timed step of ANY step_type, waits included -- an honest
    "what takes the longest, period" readout that needs no demand block.
    Engine-computed only -- see ProcessMapArtifact.longest_step below."""

    step_id: str
    step_name: str
    step_type: StepType
    time_minutes: float


class ConstraintStepResult(BaseModel):
    """A-7's constraint readout, restricted to PROCESSING steps (step_type
    value_add or enabling) -- see the module docstring for why a pure wait
    is excluded. Engine-computed only -- see ProcessMapArtifact.constraint_step
    below."""

    step_id: str
    step_name: str
    time_minutes: float
    pace_minutes_per_unit: float
    meets_pace: bool


class ValueAddRatioResult(BaseModel):
    """The number a value-stream map exists to produce, and the one thing
    T-06 was missing.

    A VSM's punchline is its timeline ladder: three minutes of work inside a
    four-day lead time. The shock is the RATIO, not either number alone --
    it is what stops an argument about who is working hard enough and starts
    one about the waiting. T-06 already tags every step value_add /
    non_value_add / enabling and already times them; it simply never summed
    them.

    `enabling` time counts in the total but NOT in the numerator. Enabling
    work (a required inspection, a regulated sign-off) is not waste, and
    calling it value-add would flatter the ratio while calling it waste
    would tell someone to delete a step they legally cannot. It gets its own
    line so the reader sees the three-way split rather than a binary that
    hides it."""

    value_add_minutes: float
    enabling_minutes: float
    non_value_add_minutes: float
    total_lead_time_minutes: float
    value_add_ratio: float
    steps_timed: int
    steps_untimed: int


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
    # same contract as CopqArtifact.total / MsaArtifact.result. Each is None
    # whenever there isn't enough on the artifact to compute it from yet (an
    # honest "nothing to name", not a zero) -- see compute_longest_step /
    # compute_constraint_step below for the exact preconditions.
    longest_step: Computed[LongestStepResult] | None = None
    constraint_step: Computed[ConstraintStepResult] | None = None
    value_add_ratio: Computed[ValueAddRatioResult] | None = None

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
    def _recompute_longest_and_constraint(self) -> "ProcessMapArtifact":
        self.longest_step = compute_longest_step(self.steps)
        self.constraint_step = compute_constraint_step(self.steps, self.demand)
        self.value_add_ratio = compute_value_add_ratio(self.steps)
        return self


# Processing steps only -- the set a step's time can compete to be named
# `constraint_step` from (module docstring: a pure wait can queue up behind
# the constraint, but it cannot be the constraint).
PROCESSING_STEP_TYPES: frozenset[StepType] = frozenset({"value_add", "enabling"})


def _pick_longest(candidates: list[ProcessStepModel]) -> ProcessStepModel:
    """Deterministic argmax by time_minutes, tie-broken on (lane_id, order,
    step_id) -- there's no business meaning to breaking a tie one way or
    another, only a requirement that the same inputs always name the same
    step."""
    max_time = max(s.time_minutes for s in candidates)
    return sorted(
        (s for s in candidates if s.time_minutes == max_time),
        key=lambda s: (s.lane_id, s.order, s.step_id),
    )[0]


def compute_longest_step(steps: list[ProcessStepModel]) -> Computed[LongestStepResult] | None:
    """The longest-timed step of any step_type, waits included. None
    whenever no step carries a time yet -- an honest "nothing to name,"
    not a zero. Needs no demand block: this is a plain "what takes the
    longest" fact, not a pace judgment."""
    timed = [s for s in steps if s.time_minutes is not None]
    if not timed:
        return None
    step = _pick_longest(timed)
    result = LongestStepResult(
        step_id=step.step_id, step_name=step.name, step_type=step.step_type, time_minutes=step.time_minutes,
    )
    return compute(
        result,
        method="longest_step = argmax(step.time_minutes) over ALL timed steps, any step_type (waits included)",
        input_data={
            "steps": [
                {"step_id": s.step_id, "lane_id": s.lane_id, "order": s.order, "step_type": s.step_type, "time_minutes": s.time_minutes}
                for s in steps
            ],
        },
        assumptions_checked=["no step_type filter -- a pure wait is eligible here even though it can't be the constraint_step"],
    )


def compute_constraint_step(
    steps: list[ProcessStepModel], demand: DemandBlock | None
) -> Computed[ConstraintStepResult] | None:
    """A-7 (matrix §5a): longest effective step time vs the pace demand
    requires (available time / demand -- two fields), restricted to
    PROCESSING steps only (module docstring) -- meets_pace is judged on
    this step. None whenever the inputs to compute from aren't there yet --
    an absent/partial demand block, or no PROCESSING step carrying a time
    -- which is an honest "nothing to name," not a zero."""
    if demand is None or demand.available_time_minutes is None or demand.demand_units is None:
        return None
    processing = [s for s in steps if s.time_minutes is not None and s.step_type in PROCESSING_STEP_TYPES]
    if not processing:
        return None

    step = _pick_longest(processing)
    pace = demand.available_time_minutes / demand.demand_units
    result = ConstraintStepResult(
        step_id=step.step_id,
        step_name=step.name,
        time_minutes=step.time_minutes,
        pace_minutes_per_unit=pace,
        meets_pace=step.time_minutes <= pace,
    )
    return compute(
        result,
        method=(
            "constraint_step = argmax(step.time_minutes) over PROCESSING steps only (step_type value_add or "
            "enabling) -- a pure-wait non_value_add step cannot be the constraint (matrix §5a A-7, fidelity fix); "
            "pace_minutes_per_unit = available_time_minutes / demand_units; meets_pace judged on this step"
        ),
        input_data={
            "steps": [
                {"step_id": s.step_id, "lane_id": s.lane_id, "order": s.order, "step_type": s.step_type, "time_minutes": s.time_minutes}
                for s in steps
            ],
            "demand": demand.model_dump(mode="json"),
        },
        assumptions_checked=[
            "pace is arithmetic on two fields (available time / demand), not full takt/line-balancing (T-32, v1.1)",
            "only value_add/enabling steps are eligible -- a non_value_add (wait) step is excluded by construction",
        ],
    )


def compute_value_add_ratio(steps: list[ProcessStepModel]) -> Computed[ValueAddRatioResult] | None:
    """Value-add time over total lead time -- the VSM readout (matrix I.B.2).

    None when no step carries a time: an honest "nothing to divide" rather
    than a zero ratio, matching compute_longest_step's contract.

    UNTIMED STEPS ARE COUNTED AND REPORTED, never silently skipped. A map
    where half the steps have no time yields a ratio computed over the other
    half, and a reader told "12% value-add" without being told it came from
    six of twelve steps has been misled by an omission. The count rides on
    the result so the report card can flag it.
    """
    timed = [s for s in steps if s.time_minutes is not None]
    if not timed:
        return None

    def total(step_type: StepType) -> float:
        return sum(s.time_minutes for s in timed if s.step_type == step_type)

    value_add = total("value_add")
    enabling = total("enabling")
    non_value_add = total("non_value_add")
    lead_time = value_add + enabling + non_value_add

    result = ValueAddRatioResult(
        value_add_minutes=value_add,
        enabling_minutes=enabling,
        non_value_add_minutes=non_value_add,
        total_lead_time_minutes=lead_time,
        # Lead time can only be zero if every timed step is timed at zero;
        # report 0.0 rather than dividing by it.
        value_add_ratio=(value_add / lead_time) if lead_time > 0 else 0.0,
        steps_timed=len(timed),
        steps_untimed=len(steps) - len(timed),
    )
    return compute(
        result,
        method=(
            "value_add_ratio = sum(time_minutes where step_type=value_add) / sum(time_minutes over all "
            "timed steps). Enabling time counts toward the denominator only -- it is neither waste nor "
            "value-add. Untimed steps are excluded from both and reported as steps_untimed."
        ),
        input_data={
            "steps": [
                {"step_id": s.step_id, "step_type": s.step_type, "time_minutes": s.time_minutes}
                for s in steps
            ]
        },
        assumptions_checked=[
            "every timed step carries exactly one step_type (schema-enforced)",
            "untimed steps excluded from numerator and denominator alike, and reported as steps_untimed",
        ],
    )
