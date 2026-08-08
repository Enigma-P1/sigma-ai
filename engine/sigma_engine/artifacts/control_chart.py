"""T-21 Control Charts: I-MR (continuous) or p (attribute), selected by
data shape + the defectives-or-defects answer (matrix VI.A.3: pass/fail
units -> p; counts per unit/area -> EXIT-11 BY NAME, never a p-chart --
schema-hard here, the same EXIT-10-as-ValidationError move
artifacts/pilot_plan.py makes for its own one-change rule). Limits are
FROZEN once set (from a window that itself clears the freeze floor --
>=20 points/subgroups, no default-rule signal in it, matrix §4a's
companion clause) and change only on a deliberate, logged
`recalculate_reason` (rubric R-CTL-01 #2/#3). Once armed, engine-computed
signals against the FROZEN limits carry a per-signal acknowledgment +
response note (rubric R-CTL-02); a chart that is never armed reads a
Fail, not a thin Pass -- tracked via `armed.monitoring_started`.

Reuses stats/imr.py (compute_imr_chart, rule1_beyond_3sigma,
rule4_run_of_8) and stats/p_chart.py (compute_p_chart, p_chart_limits,
rule1_beyond_limits) for every number -- this module composes and
stores, it recomputes no chart math of its own.

FROZEN MEANS FROZEN -- the one deliberate departure from this engine's
usual "every Computed[] field is unconditionally recomputed on every
validate" contract (FishboneArtifact.verified_causes, SolutionMatrixArtifact.
scores, ...): `imr_baseline`/`p_baseline` recompute ONLY when the caller
sets `freeze_requested=True` (first freeze) or a non-empty
`recalculate_reason` (a later freeze) -- exactly what "frozen, recalculated
only on deliberate decision" requires (R-CTL-01's own "Needs work when:
limits are recalculated on every update" line). Outside those two
triggers, whatever was already on the artifact (i.e. what a load-modify-
save round trip carried in) is kept unchanged. This reopens the same
trust boundary provenance.py's own docstring already names as out of
scope ("cannot... stop a caller from fabricating a Computed by calling
its constructor directly" -- the load path stays open); the freeze
window's raw values are additionally retained (`frozen_window_*`) so
prescore CAN recompute-and-compare -- the same tamper-check shape
prescore/hypothesis.py already runs on T-17's stored route.

A no-save preview of "what would freezing do right now" needs no new
route: POST /artifacts/T-21/validate (routes/artifacts.py's generic,
already-shipped validate-only endpoint) with `freeze_requested=true` on a
draft body runs this exact validator without persisting anything --
either the computed baseline+signals come back, or a 422 names precisely
why the freeze floor isn't cleared yet.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..provenance import Computed, compute, hash_input
from ..stats import imr as imr_mod
from ..stats import p_chart as p_chart_mod
from ..stats.constants import EXIT04_MIN_POINTS_TO_FREEZE_LIMITS
from ..stats.imr import ImrChartResult, Signal, compute_imr_chart
from ..stats.p_chart import PChartResult, Subgroup, compute_p_chart
from .base import ArtifactBase, validate_iso8601

ChartType = Literal["imr", "p"]
DataShape = Literal["continuous", "attribute"]
DefectivesOrDefects = Literal["defectives", "defects"]

# matrix §4a: the same "any window used to set or freeze control limits"
# floor I-MR's baseline uses (stats/constants.py) -- not chart-specific.
FREEZE_FLOOR = EXIT04_MIN_POINTS_TO_FREEZE_LIMITS


class ControlChartExit(BaseModel):
    """EXIT-11 payload -- same shape as hypothesis_selector.HypothesisExitPayload
    (exit_id/message/routes_to), kept local rather than imported so this
    module carries no dependency on the T-17 selector; the exit ID and its
    underlying rule (matrix §4a EXIT-11) are cited independently here."""

    model_config = ConfigDict(frozen=True)

    exit_id: Literal["EXIT-11"] = "EXIT-11"
    message: str = (
        "This is counts-per-unit/area (defects), not pass/fail units (defectives) -- a p-chart is barred for it "
        "by name (defectives != defects, matrix VI.A.3 / §4a)."
    )
    routes_to: str = (
        "c/u chart family (T-29, v1.1) for monitoring; DPMO/yield (T-10) remains available as a descriptive summary."
    )


class ChartSelector(BaseModel):
    """The printed decision path (matrix VI.A.3): data shape first, then
    -- for attribute data only -- the defectives-or-defects question.
    EXIT-11 fires, schema-hard, the moment "defects" is answered."""

    data_shape: DataShape
    defectives_or_defects: DefectivesOrDefects | None = None

    @model_validator(mode="after")
    def _attribute_requires_the_question_answered(self) -> "ChartSelector":
        if self.data_shape == "attribute" and self.defectives_or_defects is None:
            raise ValueError(
                "selector.defectives_or_defects is required when data_shape='attribute' -- matrix VI.A.3's printed "
                "selector asks defectives-or-defects FIRST for any attribute chart"
            )
        return self

    @model_validator(mode="after")
    def _exit11_on_defects(self) -> "ChartSelector":
        if self.data_shape == "attribute" and self.defectives_or_defects == "defects":
            e = ControlChartExit()
            raise ValueError(f"{e.exit_id}: {e.message} Routes to: {e.routes_to}")
        return self


class DataSource(BaseModel):
    """Where the plotted data came from (task brief: "dataset or check-
    sheet-derived") -- provenance only; the values themselves live in
    `imr_values`/`p_subgroups` below (this module stays free of file I/O,
    same contract as every other stats/artifacts module -- the caller
    resolves a dataset/check-sheet ref into raw values before this
    artifact ever validates, exactly HypothesisQuestion's own contract)."""

    kind: Literal["dataset", "check_sheet", "manual"]
    dataset_id: str | None = None
    dataset_sha256: str | None = None
    column: str | None = None
    check_sheet_artifact_id: str | None = None


class ArmedState(BaseModel):
    monitoring_started: bool = False
    cadence_note: str = ""


class RecalculationLogEntry(BaseModel):
    reason: str = Field(min_length=1)
    at: str
    triggered_by: Literal["initial_freeze", "recalculate"]

    @model_validator(mode="after")
    def _at_iso8601(self) -> "RecalculationLogEntry":
        validate_iso8601(self.at)
        return self


class SignalAcknowledgment(BaseModel):
    acknowledged: bool = False
    response_note: str = ""
    at: str | None = None


class TrackedSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    signal: Signal
    acknowledgment: SignalAcknowledgment


def _signal_key(s: Signal) -> str:
    return f"{s.rule_id}:{s.start_index}:{s.end_index}:{s.side}"


class ControlChartArtifact(ArtifactBase):
    tool_id: Literal["T-21"] = "T-21"

    chart_type: ChartType
    metric_ref: str = Field(min_length=1)
    selector: ChartSelector
    source: DataSource

    # Exactly one of these is populated, matching chart_type (validator-enforced below).
    imr_values: list[float] | None = None
    p_subgroups: list[Subgroup] | None = None

    # Transient action triggers -- consumed and cleared by _freeze_or_recalculate below.
    freeze_requested: bool = False
    recalculate_reason: str | None = None
    action_at: str | None = None

    # Frozen state: server-computed on freeze/recalculate, else carried
    # forward unchanged (module docstring's "frozen means frozen").
    frozen_at: str | None = None
    source_dataset_hash: str | None = None
    frozen_window_values: list[float] | None = None
    frozen_window_subgroups: list[Subgroup] | None = None
    imr_baseline: Computed[ImrChartResult] | None = None
    p_baseline: Computed[PChartResult] | None = None
    recalculation_log: list[RecalculationLogEntry] = Field(default_factory=list)

    # Armed state + signal tracking (rubric R-CTL-02).
    armed: ArmedState = Field(default_factory=ArmedState)
    acknowledgments: dict[str, SignalAcknowledgment] = Field(default_factory=dict)
    signals: Computed[list[TrackedSignal]] | None = None

    @model_validator(mode="after")
    def _chart_type_matches_selector(self) -> "ControlChartArtifact":
        expected: ChartType = "imr" if self.selector.data_shape == "continuous" else "p"
        if self.chart_type != expected:
            raise ValueError(
                f"chart_type={self.chart_type!r} does not match the selector (data_shape={self.selector.data_shape!r} "
                f"-> expected {expected!r}) -- the chart family must match the data type through the printed "
                "selector (matrix VI.A.3, rubric R-CTL-01 #1)"
            )
        return self

    @model_validator(mode="after")
    def _data_matches_chart_type(self) -> "ControlChartArtifact":
        if self.chart_type == "imr":
            if not self.imr_values or len(self.imr_values) < 2:
                raise ValueError("chart_type='imr' requires imr_values with at least 2 points")
            if self.p_subgroups is not None:
                raise ValueError("chart_type='imr' must not carry p_subgroups")
        else:
            if not self.p_subgroups:
                raise ValueError("chart_type='p' requires at least 1 p_subgroups entry")
            if self.imr_values is not None:
                raise ValueError("chart_type='p' must not carry imr_values")
        return self

    @model_validator(mode="after")
    def _freeze_or_recalculate(self) -> "ControlChartArtifact":
        """The one place imr_baseline/p_baseline are (re)computed -- see
        module docstring's "frozen means frozen" note. Runs only when the
        caller is actually attempting to (re)freeze this save; otherwise a
        no-op that leaves the incoming baseline fields exactly as given."""
        reason = (self.recalculate_reason or "").strip()
        attempting = self.freeze_requested or bool(self.recalculate_reason is not None)
        if not attempting:
            return self
        if self.recalculate_reason is not None and not reason:
            raise ValueError(
                "recalculate_reason, if given, must be a non-empty logged reason (PLAN §4.1's deliberate-decision "
                "rule) -- whitespace-only is not a reason"
            )
        already_frozen = self.imr_baseline is not None or self.p_baseline is not None
        if reason and not already_frozen:
            raise ValueError("recalculate_reason was given but no limits are frozen yet -- use freeze_requested=true for the first freeze")
        if self.action_at is None:
            raise ValueError("action_at (ISO8601) is required whenever freeze_requested or recalculate_reason is set")
        validate_iso8601(self.action_at)

        if self.chart_type == "imr":
            window = self.imr_values or []
            n_points = len(window)
            has_signal = imr_mod.compute_imr_chart(window).value.has_default_rule_signal if n_points >= 2 else True
        else:
            window = self.p_subgroups or []
            n_points = len(window)
            has_signal = compute_p_chart(window).value.has_default_rule_signal if n_points >= 1 else True

        if n_points < FREEZE_FLOOR or has_signal:
            raise ValueError(
                f"EXIT-04 companion floor (matrix §4a): freezing/recalculating limits needs >={FREEZE_FLOOR} points and "
                f"no default-rule (rule 1 or 4) signal in that exact window -- got {n_points} point(s), default-rule "
                f"signal present={has_signal}. The chart runs diagnostically (no frozen limits, no stability claim) "
                "until this window clears."
            )

        if self.chart_type == "imr":
            self.imr_baseline = compute_imr_chart(window)
            self.p_baseline = None
            self.frozen_window_values, self.frozen_window_subgroups = list(window), None
            hash_payload: object = list(window)
        else:
            self.p_baseline = compute_p_chart(window)
            self.imr_baseline = None
            self.frozen_window_values, self.frozen_window_subgroups = None, list(window)
            hash_payload = [s.model_dump(mode="json") for s in window]

        self.frozen_at = self.action_at
        self.source_dataset_hash = hash_input(hash_payload)
        self.recalculation_log = [
            *self.recalculation_log,
            RecalculationLogEntry(
                reason=reason or "initial freeze", at=self.action_at,
                triggered_by="recalculate" if already_frozen else "initial_freeze",
            ),
        ]
        self.freeze_requested = False
        self.recalculate_reason = None
        self.action_at = None  # one-shot trigger, same as the two fields above -- consumed, not a lingering state
        return self

    @model_validator(mode="after")
    def _compute_signals(self) -> "ControlChartArtifact":
        """Signals against the FROZEN limits, over the CURRENT (possibly
        grown-since-freeze) data -- unconditionally recomputed every
        validate (unlike the baseline itself): the point count and any
        new monitoring reading always feed this, only the limits stay
        fixed. None while unfrozen -- a diagnostic chart has no armed
        signal log (rubric R-CTL-02: never-armed is a Fail, not a thin
        Pass)."""
        if self.imr_baseline is None and self.p_baseline is None:
            self.signals = None
            return self

        if self.chart_type == "imr":
            assert self.imr_baseline is not None
            b = self.imr_baseline.value
            current = self.imr_values or []
            raw = imr_mod.rule1_beyond_3sigma(current, b.xbar, b.sigma_within) + imr_mod.rule4_run_of_8(current, b.xbar)
        else:
            assert self.p_baseline is not None
            b = self.p_baseline.value
            current = self.p_subgroups or []
            points = []
            for s in current:
                ucl, lcl = p_chart_mod.p_chart_limits(b.p_bar, s.n)
                points.append(p_chart_mod.PChartPoint(label=s.label, n=s.n, defective_count=s.defective_count, p=s.defective_count / s.n, ucl=ucl, lcl=lcl))
            raw = p_chart_mod.rule1_beyond_limits(points) + imr_mod.rule4_run_of_8([pt.p for pt in points], b.p_bar)

        raw.sort(key=lambda s: (s.start_index, s.rule_id))
        tracked = [TrackedSignal(signal=s, acknowledgment=self.acknowledgments.get(_signal_key(s), SignalAcknowledgment())) for s in raw]

        self.signals = compute(
            tracked,
            method=(
                "signals = WECO rule1 (imr: beyond the frozen +/-3sigma band; p: beyond each point's own "
                "frozen-pbar-derived limits) + rule4 (8 consecutive points same side of the frozen center), "
                "evaluated against the FROZEN baseline over the current data (matrix §4a / VI.A.1)"
            ),
            input_data={"chart_type": self.chart_type, "n_current": len(current), "frozen_at": self.frozen_at},
            assumptions_checked=["baseline limits are frozen -- not recomputed from the current data"],
        )
        return self
