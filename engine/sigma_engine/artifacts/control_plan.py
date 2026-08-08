"""T-22 Control Plan + Response Plan (OCAP) + Scheduled Check-ins.

Monitored items name characteristic/how/where/frequency+reason and a named
owner (rubric R-CTL-03): `owner_name` is schema-LOOSE (blank allowed) on
purpose, matching this engine's hard/soft split everywhere else (PLAN
§4.2) -- an ownerless item must be SAVEABLE so the theater flag has
something to render against (R-CTL-03's Fail line: "the tool flags an
ownerless plan as theater"). `plan_health` below is the computed,
always-fresh theater/coverage readout; prescore/control_plan.py renders it.

OCAP entries carry the four concrete elements rubric R-CTL-04 #1 names --
trigger signal, ordered action_steps (first response + containment),
escalation trigger/contact, and the acting owner -- against a
`monitored_item_id` that must resolve (referential integrity, schema-hard:
a dangling OCAP entry is a broken reference, not a content-quality call).

Check-ins reuse `stats/p_chart.p_chart_limits` and the FROZEN i_ucl/i_lcl
band a T-21 ControlChartArtifact already computed and froze
(control_chart.py's "frozen means frozen" contract) -- `FrozenLimitsRef` is
the caller-resolved snapshot of that frozen baseline (same
echoed-by-ref/no-project-store-I/O-at-the-schema-layer contract as
control_chart.py's own `DataSource` and proof.py's `DataRef`: the caller
loads the linked T-21 artifact and copies its frozen numbers in before this
artifact ever validates). `next_due` is pure calendar arithmetic
(start_date + cadence * count-of-completed-check-ins) -- deterministic, no
wall clock. Whether a check-in is now overdue needs a "now" to compare
against; per this engine's own discipline (never `datetime.now()` at the
schema layer -- routes/datasets.py, routes/floorplans.py, routes/
check_sheet.py's shared comment), `as_of` is caller-supplied, like
control_chart.py's `action_at`.
"""

from __future__ import annotations

import datetime as _dt
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..provenance import Computed, compute
from ..stats.p_chart import Subgroup, p_chart_limits
from .base import ArtifactBase, validate_iso8601

CadenceUnit = Literal["days", "weeks", "months"]
CheckInVerdict = Literal["pass", "fail"]
ControlChartType = Literal["imr", "p"]


class ShiftOwner(BaseModel):
    """R-CTL-03's multi-shift guidance: "a multi-shift or multi-site process
    names one global owner with no per-shift/site handoff... the passing
    form names a primary owner per operating unit." Optional per item --
    a single-shift process never needs this list populated."""

    shift: str = Field(min_length=1)
    owner_name: str = ""
    owner_accepted: bool = False


class MonitoredItem(BaseModel):
    item_id: str = Field(min_length=1)
    characteristic: str = Field(min_length=1)
    how_measured: str = Field(min_length=1)
    operational_definition_ref: str = ""  # unchecked cross-ref into T-11, fmea.py's process_step_ref idiom
    where: str = Field(min_length=1)
    frequency: str = Field(min_length=1)
    frequency_reason: str = ""  # blank -> prescore flag (R-CTL-03 #2: "a default left standing")
    is_primary_ctq: bool = False
    is_improve_change: bool = False  # R-CTL-03 #3: the plan covers what Improve changed, plus the primary CTQ
    # Schema-loose on purpose -- see module docstring. R-CTL-03's Fail line
    # (ownerless = theater) is rendered by plan_health/prescore, not a
    # ValidationError, so an ownerless item can be saved and then flagged.
    owner_name: str = ""
    owner_accepted: bool = False
    per_shift_owners: list[ShiftOwner] = Field(default_factory=list)


class OcapEntry(BaseModel):
    ocap_id: str = Field(min_length=1)
    monitored_item_id: str = Field(min_length=1)
    trigger_signal: str = Field(min_length=1)  # what "out of control" looks like for this item
    # Ordered, concrete steps -- "the exact out-of-control action path"
    # (task brief); rubric R-CTL-04 #1's first-response + containment are
    # steps[0]/steps[1] by convention, checked for presence in prescore.
    action_steps: list[str] = Field(default_factory=list)
    escalation_trigger: str = ""
    escalation_contact: str = ""  # named recipient
    acting_owner: str = ""


class TrainingRow(BaseModel):
    """A-5 / rubric R-CTL-04 #2: who, on what (the T-24 SOP), by whom, by
    when, verified how, done. `who` is the one schema-hard field -- a
    training row must at least name a trainee to exist at all; the rest is
    content-quality (prescore's job, matching R-CTL-04's own Needs-work
    line: "training is listed without a verification method")."""

    row_id: str = Field(min_length=1)
    who: str = Field(min_length=1)
    sop_ref: str | None = None  # unchecked cross-ref -> T-24 StandardWorkArtifact.artifact_id
    by_whom: str = ""
    by_when: str | None = None
    verified_how: str = ""
    verified_at: str | None = None
    done: bool = False

    @field_validator("by_when", "verified_at")
    @classmethod
    def _dates_iso8601_if_present(cls, v: str | None) -> str | None:
        return v if v is None else validate_iso8601(v)


class CheckInCadence(BaseModel):
    unit: CadenceUnit
    interval: int = Field(ge=1)


class FrozenLimitsRef(BaseModel):
    """The caller-resolved snapshot of a T-21 ControlChartArtifact's FROZEN
    baseline (module docstring) -- reused, not recomputed: this module
    trusts the linked chart's own frozen i_ucl/i_lcl (imr) or p_bar (p),
    copied in by the caller exactly once per freeze/recalculate, the same
    "echoed by ref" contract proof.py's `charter_baseline_value` uses for
    T-03's numbers."""

    control_chart_artifact_id: str = Field(min_length=1)
    chart_type: ControlChartType
    center: float | None = None
    ucl: float | None = None
    lcl: float | None = None
    p_bar: float | None = None
    frozen_at: str = Field(min_length=1)

    @model_validator(mode="after")
    def _fields_match_chart_type(self) -> "FrozenLimitsRef":
        if self.chart_type == "imr":
            if self.center is None or self.ucl is None or self.lcl is None:
                raise ValueError("chart_type='imr' requires center/ucl/lcl (the frozen individuals-chart band)")
        elif self.p_bar is None:
            raise ValueError("chart_type='p' requires p_bar (the frozen pooled proportion)")
        return self


class EnteredValues(BaseModel):
    """This week's numbers, entered by hand or pulled from a dataset --
    `subgroup` reuses control_chart.py's own p-chart Subgroup shape
    verbatim (`don't duplicate`)."""

    kind: Literal["dataset", "manual"]
    dataset_id: str | None = None
    values: list[float] | None = None  # imr: one or more individual readings
    subgroup: Subgroup | None = None  # p: this check-in's own {label, n, defective_count}


class CheckInResult(BaseModel):
    verdict: CheckInVerdict
    detail: str


def compute_check_in_result(entered: EnteredValues, limits: FrozenLimitsRef) -> Computed[CheckInResult]:
    """"week 3: is the fix holding?" -- engine pass/fail against the linked
    chart's FROZEN limits (PLAN §4.1's Control-plan row), never a fresh
    signal search over the check-in's own few points. p-chart limits are
    recomputed per this check-in's own subgroup size via
    stats.p_chart.p_chart_limits (reused verbatim) since a p-chart's band
    breathes with n; imr's frozen band is fixed and applies as-is."""
    if limits.chart_type == "imr":
        if not entered.values:
            raise ValueError("entered.values is required for a check-in against an imr control chart")
        assert limits.ucl is not None and limits.lcl is not None
        out = [v for v in entered.values if v > limits.ucl or v < limits.lcl]
        verdict: CheckInVerdict = "fail" if out else "pass"
        band = f"[{limits.lcl:.4g}, {limits.ucl:.4g}]"
        detail = (
            f"{len(out)} of {len(entered.values)} entered value(s) fall outside the frozen band {band}"
            if out else f"all {len(entered.values)} entered value(s) hold inside the frozen band {band}"
        )
        input_data = {"values": entered.values, "ucl": limits.ucl, "lcl": limits.lcl}
    else:
        if entered.subgroup is None:
            raise ValueError("entered.subgroup is required for a check-in against a p control chart")
        assert limits.p_bar is not None
        ucl, lcl = p_chart_limits(limits.p_bar, entered.subgroup.n)
        p = entered.subgroup.defective_count / entered.subgroup.n
        verdict = "fail" if (p > ucl or p < lcl) else "pass"
        detail = f"{entered.subgroup.label}: p={p:.4g} vs the frozen p_bar={limits.p_bar:.4g} band [{lcl:.4g}, {ucl:.4g}] (n={entered.subgroup.n})"
        input_data = {"subgroup": entered.subgroup.model_dump(mode="json"), "p_bar": limits.p_bar}

    result = CheckInResult(verdict=verdict, detail=detail)
    return compute(
        result,
        method=(
            "check-in pass/fail = entered value(s) tested against the LINKED CONTROL CHART'S FROZEN limits "
            "(p-chart limits re-derived per this check-in's own subgroup n via p_chart_limits, since a p-chart's "
            "band breathes with n) -- the check-in's own few points are never treated as a fresh signal search"
        ),
        input_data=input_data,
        assumptions_checked=["limits are the FROZEN baseline carried on this plan, never recomputed from the check-in's own values"],
    )


class CompletedCheckIn(BaseModel):
    check_in_id: str = Field(min_length=1)
    label: str = Field(min_length=1)  # e.g. "week 3: is the fix holding?"
    due_date: str
    completed_at: str
    entered: EnteredValues
    note: str = ""
    result: Computed[CheckInResult] | None = None  # server-computed, never hand-typed -- see CheckInSchedule._recompute

    @model_validator(mode="after")
    def _iso_dates(self) -> "CompletedCheckIn":
        validate_iso8601(self.due_date)
        validate_iso8601(self.completed_at)
        return self


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (_dt.date(year, month + 1, 1) - _dt.timedelta(days=1)).day


def _add_cadence(start_date: str, cadence: CheckInCadence, steps: int) -> str:
    """start_date advanced by `steps` whole cadence periods -- pure
    calendar arithmetic, no wall clock (module docstring)."""
    d = _dt.date.fromisoformat(start_date[:10])
    n = cadence.interval * steps
    if cadence.unit == "days":
        return (d + _dt.timedelta(days=n)).isoformat()
    if cadence.unit == "weeks":
        return (d + _dt.timedelta(weeks=n)).isoformat()
    total_months = d.month - 1 + n
    year = d.year + total_months // 12
    month = total_months % 12 + 1
    return _dt.date(year, month, min(d.day, _days_in_month(year, month))).isoformat()


class CheckInSchedule(BaseModel):
    """One recurring schedule per plan (PLAN §4.1: "the app SCHEDULES
    recurring check-ins"), covering the fix as a whole. `next_due` is
    unconditionally recomputed (ControlChartArtifact.signals' contract) as
    start_date advanced by exactly len(completed) cadence steps --
    sequential and deterministic, never a hand-typed date."""

    cadence: CheckInCadence
    start_date: str
    control_chart_ref: str = Field(min_length=1)  # the T-21 artifact this schedule is judged against
    frozen_limits: FrozenLimitsRef
    completed: list[CompletedCheckIn] = Field(default_factory=list)
    next_due: Computed[str] | None = None

    @model_validator(mode="after")
    def _recompute(self) -> "CheckInSchedule":
        validate_iso8601(self.start_date)
        ids = [c.check_in_id for c in self.completed]
        if len(ids) != len(set(ids)):
            raise ValueError("check_in_id values must be unique")
        for c in self.completed:
            c.result = compute_check_in_result(c.entered, self.frozen_limits)
        due = _add_cadence(self.start_date, self.cadence, len(self.completed))
        self.next_due = compute(
            due,
            method="next_due = start_date advanced by (count of completed check-ins) whole cadence steps -- a sequential schedule, never a hand-typed date",
            input_data={"start_date": self.start_date, "cadence": self.cadence.model_dump(mode="json"), "completed_count": len(self.completed)},
        )
        return self


class PlanHealthResult(BaseModel):
    """The theater flags (task brief): ownerless items, unaccepted owners,
    an overdue check-in. `is_theater` is R-CTL-03's Fail line made
    machine-checkable, mirroring fmea.py's blocking_flags-as-the-Fail-line
    move."""

    ownerless_item_ids: list[str]
    unaccepted_owner_item_ids: list[str]
    check_in_overdue: bool
    check_in_overdue_detail: str
    is_theater: bool


def compute_plan_health(
    items: list[MonitoredItem], schedule: CheckInSchedule | None, as_of: str
) -> Computed[PlanHealthResult]:
    ownerless = [i.item_id for i in items if not i.owner_name.strip()]
    unaccepted = [i.item_id for i in items if i.owner_name.strip() and not i.owner_accepted]
    overdue = False
    overdue_detail = "no check-in schedule on this plan yet"
    if schedule is not None and schedule.next_due is not None:
        overdue = schedule.next_due.value < as_of
        overdue_detail = (
            f"next check-in was due {schedule.next_due.value}, before as_of {as_of}" if overdue
            else f"next check-in due {schedule.next_due.value}, not yet due as of {as_of}"
        )
    result = PlanHealthResult(
        ownerless_item_ids=ownerless, unaccepted_owner_item_ids=unaccepted,
        check_in_overdue=overdue, check_in_overdue_detail=overdue_detail, is_theater=bool(ownerless),
    )
    return compute(
        result,
        method=(
            "plan_health = ownerless monitored items (is_theater -- R-CTL-03's Fail line) + items whose named "
            "owner hasn't accepted + whether the schedule's next_due has passed as_of (PLAN §4.1)"
        ),
        input_data={
            "items": [{"item_id": i.item_id, "owner_name": i.owner_name, "owner_accepted": i.owner_accepted} for i in items],
            "as_of": as_of, "next_due": schedule.next_due.value if schedule and schedule.next_due else None,
        },
    )


class ControlPlanArtifact(ArtifactBase):
    tool_id: Literal["T-22"] = "T-22"

    monitored_items: list[MonitoredItem] = Field(min_length=1)
    ocap_entries: list[OcapEntry] = Field(default_factory=list)
    training_rows: list[TrainingRow] = Field(default_factory=list)
    check_in_schedule: CheckInSchedule | None = None
    as_of: str = Field(min_length=1)  # caller-supplied "now" for plan_health's overdue read -- see module docstring

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # CopqArtifact.total's contract.
    plan_health: Computed[PlanHealthResult] | None = None

    @model_validator(mode="after")
    def _referential_integrity(self) -> "ControlPlanArtifact":
        validate_iso8601(self.as_of)
        item_ids = [i.item_id for i in self.monitored_items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("item_id values must be unique")
        id_set = set(item_ids)
        for o in self.ocap_entries:
            if o.monitored_item_id not in id_set:
                raise ValueError(f"OCAP entry {o.ocap_id!r} references unknown monitored_item_id {o.monitored_item_id!r}")
        return self

    @model_validator(mode="after")
    def _recompute_plan_health(self) -> "ControlPlanArtifact":
        self.plan_health = compute_plan_health(self.monitored_items, self.check_in_schedule, self.as_of)
        return self
