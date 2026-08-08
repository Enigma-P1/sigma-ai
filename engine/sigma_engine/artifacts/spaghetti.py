"""T-07 Spaghetti Diagram (interactive): a calibrated floor-plan image,
routes traced per operator/trip, and every metric the tool promises --
distance per trip, walk time, daily travel burden, path crossings, and the
current-vs-proposed delta table -- computed here in the model validator,
never client-side (CopqArtifact.total's pattern, reused at T-06 for
`bottleneck`: the computation lives next to the schema, stamped through
provenance.compute(), and the model_validator unconditionally overwrites
whatever a client posts).

Field-by-field:
  floor_plan   -- a pointer to the uploaded image (floorplan_images.py's
                  dataset-store pattern); required, since every other field
                  here is coordinates *on* that image.
  calibration  -- two canvas points + a real_length + unit; optional at
                  schema level (mirrors ProcessMapArtifact.demand) so a
                  save right after upload, before the calibration line is
                  drawn, isn't blocked. pixels-per-unit is *derived* from
                  this, not stored -- it lives on the computed metrics.
  operators    -- id/name/color-index; default-empty, like connectors.
  routes       -- operator_id/trip_label/frequency_per_day/points/
                  layout_mode; default-empty.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase

Unit = Literal["meters", "feet"]
LayoutMode = Literal["current", "proposed"]


class FloorPlanRef(BaseModel):
    """Pointer to an uploaded floor-plan image. Bytes live in the project
    folder (floorplan_images.py's FloorPlanImageStore); this is the
    metadata + SHA-256 provenance anchor the artifact actually carries --
    the same split as DatasetMeta vs. the v1.csv file it describes."""

    image_id: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)


class CalibrationPoint(BaseModel):
    x: float
    y: float


class Calibration(BaseModel):
    """Two canvas points + the real-world length they represent -- the
    single known-length line rubric R-MEA-03 requires ("the floor plan is
    calibrated by a drawn known-length line, and that real length is
    stated"). Pixels-per-unit is *derived* from these three fields, not
    stored here -- it lives on the computed SpaghettiMetrics below, next
    to every other number that scale feeds."""

    point_a: CalibrationPoint
    point_b: CalibrationPoint
    real_length: float = Field(gt=0)
    unit: Unit


class Operator(BaseModel):
    operator_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    color_index: int = Field(ge=0)


class RoutePoint(BaseModel):
    x: float
    y: float


class SpaghettiRoute(BaseModel):
    route_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    trip_label: str = Field(min_length=1)
    # This *is* the trip count (rubric: "trips counted, not imagined") --
    # how many times/day this trip happens, not a separate tally field.
    frequency_per_day: float = Field(gt=0)
    # >=2 is the structural floor (a route needs a start and an end to have
    # any distance at all); the rubric's ">=3 points" bar is a content
    # signal, not a schema one -- see prescore/spaghetti.py.
    points: list[RoutePoint] = Field(min_length=2)
    layout_mode: LayoutMode = "current"


class ObservationWindow(BaseModel):
    """Schema-loose (every field blank-allowed, same reasoning as
    ProcessMapArtifact's Lane.owner) -- rubric R-MEA-03 pass criterion #4
    *and* its own "Pre-scored in code" line ("observation-window fields
    non-empty") both name this; prescore/spaghetti.py's
    observation_window_stated is what actually enforces it as content."""

    when: str = ""
    duration: str = ""
    shift: str = ""


# ---- Computed metrics (this module's T-06-bottleneck-pattern half) --------


class RouteMetrics(BaseModel):
    route_id: str
    operator_id: str
    trip_label: str
    layout_mode: LayoutMode
    unit: Unit
    distance_per_trip: float
    walk_time_minutes_per_trip: float
    frequency_per_day: float
    daily_distance: float
    daily_walk_time_minutes: float


class OperatorTotal(BaseModel):
    operator_id: str
    operator_name: str
    layout_mode: LayoutMode
    daily_trip_count: float
    total_daily_distance: float
    total_daily_walk_time_minutes: float


class PathCrossing(BaseModel):
    route_id_a: str
    route_id_b: str
    crossing_count: int


class DeltaRow(BaseModel):
    """One row of the current-vs-proposed table -- either one operator
    (`scope` = that operator's operator_id) or the "overall" rollup.
    Any *_delta field is None only when one side has no data to compare
    (delta_table below only ever runs once both sides have >=1 row, so in
    practice this stays None solely when one operator has routes in only
    one of the two modes)."""

    scope: str
    scope_label: str
    current_daily_distance: float | None
    proposed_daily_distance: float | None
    distance_delta: float | None
    distance_delta_pct: float | None
    current_daily_walk_time_minutes: float | None
    proposed_daily_walk_time_minutes: float | None
    walk_time_delta_minutes: float | None
    walk_time_delta_pct: float | None


class SpaghettiMetrics(BaseModel):
    unit: Unit
    pixels_per_unit: float
    walk_speed_units_per_minute: float
    routes: list[RouteMetrics]
    operator_totals: list[OperatorTotal]
    total_daily_distance_all: float
    total_daily_walk_time_minutes_all: float
    crossings: list[PathCrossing]
    total_crossing_count: int
    # None until both layout modes have >=1 route -- an honest "nothing to
    # compare yet," not a table of zeros (rubric-driven: PLAN's "before/
    # after layout mode with delta metrics").
    delta: list[DeltaRow] | None


# Cited, overridable default (SpaghettiArtifact.walk_speed_override_per_minute):
# ~1.4 m/s is a commonly-cited self-selected level-ground adult walking
# speed in ergonomics/pedestrian-planning literature (e.g. Browning et al.
# 2006, J Appl Physiol, reports ~1.4 m/s preferred speed for normal-weight
# adults). MUTCD's 3.5 ft/s pedestrian-signal-timing figure (~1.07 m/s) is
# a conservative accessibility figure, not a typical-pace one, so it isn't
# used here. A Green Belt who's actually timed the walk (T-09) should
# override this, not trust it blindly.
DEFAULT_WALK_SPEED_METERS_PER_MINUTE = 84.0  # 1.4 m/s x 60
METERS_PER_FOOT = 0.3048
DEFAULT_WALK_SPEED_FEET_PER_MINUTE = DEFAULT_WALK_SPEED_METERS_PER_MINUTE / METERS_PER_FOOT

# prescore/spaghetti.py's plausibility floor for a calibration line's pixel
# span -- exported so the two modules can't drift on the threshold value.
MIN_CALIBRATION_PIXEL_SPAN = 10.0


def _default_walk_speed(unit: Unit) -> float:
    return DEFAULT_WALK_SPEED_METERS_PER_MINUTE if unit == "meters" else DEFAULT_WALK_SPEED_FEET_PER_MINUTE


def _dist(a: CalibrationPoint | RoutePoint, b: CalibrationPoint | RoutePoint) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def _polyline_pixel_length(points: list[RoutePoint]) -> float:
    return sum(_dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def _orientation(p: RoutePoint, q: RoutePoint, r: RoutePoint) -> int:
    """Sign of the cross product (q-p) x (r-q): 0 collinear, 1 clockwise, 2
    counterclockwise -- the standard building block for a segment-
    intersection test (Cormen/Leiserson/Rivest/Stein, "Introduction to
    Algorithms," the polygon/segment-intersection chapter)."""
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    if abs(val) < 1e-9:
        return 0
    return 1 if val > 0 else 2


def _segments_cross(p1: RoutePoint, q1: RoutePoint, p2: RoutePoint, q2: RoutePoint) -> bool:
    """True only for a proper interior crossing (each segment's endpoints
    fall on opposite sides of the other segment's line). Deliberately
    excludes shared endpoints and collinear touches/overlaps: those are
    common and legitimate in a spaghetti trace (two operators starting or
    ending at the same station) and would otherwise be over-counted as
    "crossings" in the congestion sense this metric exists to flag."""
    o1, o2 = _orientation(p1, q1, p2), _orientation(p1, q1, q2)
    o3, o4 = _orientation(p2, q2, p1), _orientation(p2, q2, q1)
    return o1 != o2 and o1 != 0 and o2 != 0 and o3 != o4 and o3 != 0 and o4 != 0


def _route_metrics(route: SpaghettiRoute, pixels_per_unit: float, walk_speed: float, unit: Unit) -> RouteMetrics:
    distance = _polyline_pixel_length(route.points) / pixels_per_unit
    walk_time = distance / walk_speed
    return RouteMetrics(
        route_id=route.route_id, operator_id=route.operator_id, trip_label=route.trip_label,
        layout_mode=route.layout_mode, unit=unit, distance_per_trip=distance,
        walk_time_minutes_per_trip=walk_time, frequency_per_day=route.frequency_per_day,
        daily_distance=distance * route.frequency_per_day,
        daily_walk_time_minutes=walk_time * route.frequency_per_day,
    )


def _operator_totals(route_metrics: list[RouteMetrics], operator_by_id: dict[str, Operator]) -> list[OperatorTotal]:
    groups: dict[tuple[str, str], list[RouteMetrics]] = {}
    for rm in route_metrics:
        groups.setdefault((rm.operator_id, rm.layout_mode), []).append(rm)
    totals = [
        OperatorTotal(
            operator_id=operator_id, layout_mode=layout_mode,
            operator_name=operator_by_id[operator_id].name if operator_id in operator_by_id else operator_id,
            daily_trip_count=sum(rm.frequency_per_day for rm in rms),
            total_daily_distance=sum(rm.daily_distance for rm in rms),
            total_daily_walk_time_minutes=sum(rm.daily_walk_time_minutes for rm in rms),
        )
        for (operator_id, layout_mode), rms in groups.items()
    ]
    return sorted(totals, key=lambda t: (t.operator_id, t.layout_mode))


def _crossings(routes: list[SpaghettiRoute]) -> tuple[list[PathCrossing], int]:
    # Only routes within the SAME layout_mode are compared: "current" and
    # "proposed" are two different hypothetical states of the floor, never
    # walked simultaneously, so a current-vs-proposed "crossing" wouldn't
    # correspond to any real event on the floor (algorithm choice, per the
    # M2 build brief's "document it in a comment").
    by_mode: dict[str, list[SpaghettiRoute]] = {}
    for r in routes:
        by_mode.setdefault(r.layout_mode, []).append(r)

    pair_counts: dict[tuple[str, str], int] = {}
    for mode_routes in by_mode.values():
        for i in range(len(mode_routes)):
            for j in range(i + 1, len(mode_routes)):
                r1, r2 = mode_routes[i], mode_routes[j]
                count = sum(
                    1
                    for a in range(len(r1.points) - 1)
                    for b in range(len(r2.points) - 1)
                    if _segments_cross(r1.points[a], r1.points[a + 1], r2.points[b], r2.points[b + 1])
                )
                if count:
                    key = tuple(sorted((r1.route_id, r2.route_id)))
                    pair_counts[key] = pair_counts.get(key, 0) + count
    crossings = [PathCrossing(route_id_a=a, route_id_b=b, crossing_count=c) for (a, b), c in sorted(pair_counts.items())]
    return crossings, sum(c.crossing_count for c in crossings)


def _delta_row(scope: str, scope_label: str, cur: OperatorTotal | None, prop: OperatorTotal | None) -> DeltaRow:
    cur_d = cur.total_daily_distance if cur else None
    prop_d = prop.total_daily_distance if prop else None
    cur_t = cur.total_daily_walk_time_minutes if cur else None
    prop_t = prop.total_daily_walk_time_minutes if prop else None
    d_delta = (prop_d - cur_d) if (cur_d is not None and prop_d is not None) else None
    t_delta = (prop_t - cur_t) if (cur_t is not None and prop_t is not None) else None
    return DeltaRow(
        scope=scope, scope_label=scope_label,
        current_daily_distance=cur_d, proposed_daily_distance=prop_d, distance_delta=d_delta,
        distance_delta_pct=(d_delta / cur_d * 100.0) if (d_delta is not None and cur_d) else None,
        current_daily_walk_time_minutes=cur_t, proposed_daily_walk_time_minutes=prop_t,
        walk_time_delta_minutes=t_delta,
        walk_time_delta_pct=(t_delta / cur_t * 100.0) if (t_delta is not None and cur_t) else None,
    )


def _delta_table(operator_totals: list[OperatorTotal], operator_by_id: dict[str, Operator]) -> list[DeltaRow] | None:
    current = {t.operator_id: t for t in operator_totals if t.layout_mode == "current"}
    proposed = {t.operator_id: t for t in operator_totals if t.layout_mode == "proposed"}
    if not current or not proposed:
        return None  # only compute a delta once both layout modes have >=1 route

    rows = [
        _delta_row(
            operator_id, operator_by_id[operator_id].name if operator_id in operator_by_id else operator_id,
            current.get(operator_id), proposed.get(operator_id),
        )
        for operator_id in sorted(set(current) | set(proposed))
    ]

    def _overall(by_operator: dict[str, OperatorTotal], layout_mode: LayoutMode) -> OperatorTotal:
        return OperatorTotal(
            operator_id="", operator_name="", layout_mode=layout_mode,
            daily_trip_count=sum(t.daily_trip_count for t in by_operator.values()),
            total_daily_distance=sum(t.total_daily_distance for t in by_operator.values()),
            total_daily_walk_time_minutes=sum(t.total_daily_walk_time_minutes for t in by_operator.values()),
        )

    rows.append(_delta_row("overall", "All operators", _overall(current, "current"), _overall(proposed, "proposed")))
    return rows


def compute_spaghetti_metrics(
    calibration: Calibration | None,
    operators: list[Operator],
    routes: list[SpaghettiRoute],
    walk_speed_override_per_minute: float | None,
) -> Computed[SpaghettiMetrics] | None:
    """T-07's whole metrics stack, computed once here and stamped through
    provenance.compute() -- ProcessMapArtifact.compute_bottleneck's pattern,
    reused. None whenever there's no calibration to scale by yet (an honest
    "nothing computable yet"), or the calibration line is degenerate (both
    points equal -- a 0-pixel span can't derive a scale; treated as "not
    computable yet" rather than raising, since the calibration object
    itself is still schema-valid)."""
    if calibration is None:
        return None
    pixel_span = _dist(calibration.point_a, calibration.point_b)
    if pixel_span <= 0:
        return None

    pixels_per_unit = pixel_span / calibration.real_length
    walk_speed = walk_speed_override_per_minute or _default_walk_speed(calibration.unit)

    operator_by_id = {o.operator_id: o for o in operators}
    route_metrics = [_route_metrics(r, pixels_per_unit, walk_speed, calibration.unit) for r in routes]
    operator_totals = _operator_totals(route_metrics, operator_by_id)
    crossings, total_crossings = _crossings(routes)
    delta = _delta_table(operator_totals, operator_by_id)

    metrics = SpaghettiMetrics(
        unit=calibration.unit, pixels_per_unit=pixels_per_unit, walk_speed_units_per_minute=walk_speed,
        routes=route_metrics, operator_totals=operator_totals,
        total_daily_distance_all=sum(rm.daily_distance for rm in route_metrics),
        total_daily_walk_time_minutes_all=sum(rm.daily_walk_time_minutes for rm in route_metrics),
        crossings=crossings, total_crossing_count=total_crossings, delta=delta,
    )
    return compute(
        metrics,
        method=(
            "pixels_per_unit = |point_b - point_a| / real_length; distance_per_trip = polyline pixel "
            "length / pixels_per_unit; walk_time = distance / walk_speed "
            f"(default {DEFAULT_WALK_SPEED_METERS_PER_MINUTE:.0f} m/min, override honored when set); "
            "daily = per-trip x frequency_per_day; crossings = proper segment-intersection count between "
            "different routes within the same layout_mode (orientation/cross-product test, collinear "
            "touches and shared endpoints excluded); delta = proposed - current per operator and overall, "
            "only once both layout modes have >=1 route"
        ),
        input_data={
            "calibration": calibration.model_dump(mode="json"),
            "operators": [o.model_dump(mode="json") for o in operators],
            "routes": [r.model_dump(mode="json") for r in routes],
            "walk_speed_override_per_minute": walk_speed_override_per_minute,
        },
        assumptions_checked=[
            f"default walk speed is {DEFAULT_WALK_SPEED_METERS_PER_MINUTE:.0f} m/min "
            f"({DEFAULT_WALK_SPEED_FEET_PER_MINUTE:.0f} ft/min) unless overridden -- a stated, cited, "
            "overridable constant, not a per-project measurement (T-09 timing a real walk is the honest upgrade)",
            "path crossings compare routes only within the same layout_mode -- current and proposed are "
            "two different hypothetical floor states, never walked simultaneously",
        ],
    )


class SpaghettiArtifact(ArtifactBase):
    tool_id: Literal["T-07"] = "T-07"

    floor_plan: FloorPlanRef
    calibration: Calibration | None = None
    operators: list[Operator] = Field(default_factory=list)
    routes: list[SpaghettiRoute] = Field(default_factory=list)
    # In `calibration.unit` per minute; None means "use the cited default
    # for this unit" (compute_spaghetti_metrics._default_walk_speed).
    walk_speed_override_per_minute: float | None = Field(default=None, gt=0)
    observation_window: ObservationWindow = Field(default_factory=ObservationWindow)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as CopqArtifact.total / ProcessMapArtifact.bottleneck.
    # None only when there's no calibration yet to scale by.
    metrics: Computed[SpaghettiMetrics] | None = None

    @model_validator(mode="after")
    def _referential_integrity(self) -> "SpaghettiArtifact":
        operator_ids = [o.operator_id for o in self.operators]
        if len(operator_ids) != len(set(operator_ids)):
            raise ValueError("operator_id values must be unique")
        operator_id_set = set(operator_ids)

        route_ids = [r.route_id for r in self.routes]
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("route_id values must be unique")

        for route in self.routes:
            if route.operator_id not in operator_id_set:
                raise ValueError(f"route {route.route_id!r} references unknown operator_id {route.operator_id!r}")
        return self

    @model_validator(mode="after")
    def _recompute_metrics(self) -> "SpaghettiArtifact":
        self.metrics = compute_spaghetti_metrics(
            self.calibration, self.operators, self.routes, self.walk_speed_override_per_minute
        )
        return self
