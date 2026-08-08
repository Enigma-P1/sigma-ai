"""Schema + metrics-arithmetic tests for T-07 SpaghettiArtifact -- distance,
walk time, daily burden, crossings, and the current/proposed delta table,
all against hand-computable fixtures (M2 build brief)."""

import pytest
from pydantic import ValidationError

from factories import make_calibration, make_operators, make_spaghetti, make_spaghetti_routes
from sigma_engine.artifacts.spaghetti import (
    DEFAULT_WALK_SPEED_METERS_PER_MINUTE,
    SpaghettiArtifact,
    compute_spaghetti_metrics,
)
from sigma_engine.provenance import compute


def test_accepts_a_complete_artifact_and_computes_metrics():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    assert artifact.metrics is not None
    m = artifact.metrics.value
    assert m.pixels_per_unit == pytest.approx(10.0)  # 100px = 10m
    assert len(m.routes) == 1
    rm = m.routes[0]
    assert rm.distance_per_trip == pytest.approx(70.0)  # 300px + 400px legs / 10px-per-m
    assert rm.daily_distance == pytest.approx(420.0)  # 70m x 6/day
    assert artifact.metrics.provenance.method
    assert artifact.metrics.provenance.input_hash


def test_walk_time_uses_the_cited_default_speed():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    rm = artifact.metrics.value.routes[0]
    assert rm.walk_time_minutes_per_trip == pytest.approx(70.0 / DEFAULT_WALK_SPEED_METERS_PER_MINUTE)
    assert rm.daily_walk_time_minutes == pytest.approx(5.0)  # 420m / 84 m/min


def test_walk_speed_override_changes_walk_time_only():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(walk_speed_override_per_minute=100.0))
    rm = artifact.metrics.value.routes[0]
    assert rm.walk_time_minutes_per_trip == pytest.approx(0.7)  # 70m / 100 m/min
    assert rm.distance_per_trip == pytest.approx(70.0)  # override never touches distance
    assert artifact.metrics.value.walk_speed_units_per_minute == pytest.approx(100.0)


def test_metrics_none_without_calibration():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=None))
    assert artifact.metrics is None


def test_metrics_none_with_degenerate_calibration_line():
    cal = make_calibration(point_b={"x": 0.0, "y": 0.0})  # point_a == point_b -> 0px span
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=cal))
    assert artifact.metrics is None


def test_operator_totals_group_by_operator_and_layout_mode():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    totals = artifact.metrics.value.operator_totals
    assert len(totals) == 1
    assert totals[0].operator_id == "op-1"
    assert totals[0].layout_mode == "current"
    assert totals[0].daily_trip_count == pytest.approx(6.0)
    assert totals[0].total_daily_distance == pytest.approx(420.0)


def test_posted_metrics_are_discarded_and_recomputed():
    tampered = compute(
        {
            "unit": "meters", "pixels_per_unit": 1.0, "walk_speed_units_per_minute": 1.0, "routes": [],
            "operator_totals": [], "total_daily_distance_all": 999.0, "total_daily_walk_time_minutes_all": 999.0,
            "crossings": [], "total_crossing_count": 0, "delta": None,
        },
        method="tampered", input_data=[],
    )
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(metrics=tampered.model_dump(mode="json")))
    assert artifact.metrics.value.total_daily_distance_all == pytest.approx(420.0)


def test_round_trip_via_model_dump():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    round_tripped = SpaghettiArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


def test_compute_spaghetti_metrics_matches_artifact_field():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    recomputed = compute_spaghetti_metrics(artifact.calibration, artifact.operators, artifact.routes, None)
    assert recomputed.value == artifact.metrics.value


def test_rejects_duplicate_operator_ids():
    operators = make_operators()
    operators.append({"operator_id": "op-1", "name": "Duplicate", "color_index": 2})
    with pytest.raises(ValidationError, match="operator_id"):
        SpaghettiArtifact.model_validate(make_spaghetti(operators=operators))


def test_rejects_duplicate_route_ids():
    routes = make_spaghetti_routes()
    routes.append({**routes[0], "route_id": "route-1"})
    with pytest.raises(ValidationError, match="route_id"):
        SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))


def test_rejects_route_referencing_unknown_operator():
    routes = make_spaghetti_routes()
    routes[0]["operator_id"] = "no-such-operator"
    with pytest.raises(ValidationError, match="unknown operator_id"):
        SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))


def test_rejects_route_with_fewer_than_two_points():
    routes = make_spaghetti_routes()
    routes[0]["points"] = [{"x": 0.0, "y": 0.0}]
    with pytest.raises(ValidationError):
        SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))


def test_rejects_non_positive_frequency():
    routes = make_spaghetti_routes()
    routes[0]["frequency_per_day"] = 0
    with pytest.raises(ValidationError):
        SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))


def test_rejects_non_positive_real_length():
    cal = make_calibration(real_length=0)
    with pytest.raises(ValidationError):
        SpaghettiArtifact.model_validate(make_spaghetti(calibration=cal))


def test_calibration_may_be_absent_at_schema_level():
    """PLAN §4.2's soft/hard split, mirroring ProcessMapArtifact.demand: a
    save right after upload, before the line is drawn, isn't blocked."""
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=None))
    assert artifact.calibration is None
    assert artifact.metrics is None


def test_observation_window_may_be_blank_at_schema_level():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(observation_window={"when": "", "duration": "", "shift": ""}))
    assert artifact.observation_window.when == ""


# --- Path crossings: hand-computable segment-intersection fixtures ---------


def _op(operator_id: str, name: str = "Op") -> dict:
    return {"operator_id": operator_id, "name": name, "color_index": 0}


def _route(route_id, operator_id, points, layout_mode="current", frequency=6.0, trip_label="Trip") -> dict:
    return {
        "route_id": route_id, "operator_id": operator_id, "trip_label": trip_label,
        "frequency_per_day": frequency, "layout_mode": layout_mode, "points": points,
    }


def test_crossings_hand_checked_two_crossing_segments():
    # A horizontal segment through y=50 and a vertical segment through
    # x=50 cross at exactly (50, 50) -- one proper interior crossing.
    routes = [
        _route("horiz", "op-1", [{"x": 0.0, "y": 50.0}, {"x": 100.0, "y": 50.0}]),
        _route("vert", "op-2", [{"x": 50.0, "y": 0.0}, {"x": 50.0, "y": 100.0}]),
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=[_op("op-1"), _op("op-2")], routes=routes))
    m = artifact.metrics.value
    assert m.total_crossing_count == 1
    assert m.crossings[0].crossing_count == 1
    assert {m.crossings[0].route_id_a, m.crossings[0].route_id_b} == {"horiz", "vert"}


def test_crossings_zero_for_parallel_non_crossing_routes():
    routes = [
        _route("a", "op-1", [{"x": 0.0, "y": 0.0}, {"x": 100.0, "y": 0.0}]),
        _route("b", "op-2", [{"x": 0.0, "y": 50.0}, {"x": 100.0, "y": 50.0}]),
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=[_op("op-1"), _op("op-2")], routes=routes))
    assert artifact.metrics.value.total_crossing_count == 0


def test_crossings_ignore_pairs_in_different_layout_modes():
    # Same geometry as the crossing test above, but split across current
    # vs proposed -- the algorithm-choice rule (documented in spaghetti.py)
    # is that only same-mode routes are compared.
    routes = [
        _route("horiz", "op-1", [{"x": 0.0, "y": 50.0}, {"x": 100.0, "y": 50.0}], layout_mode="current"),
        _route("vert", "op-2", [{"x": 50.0, "y": 0.0}, {"x": 50.0, "y": 100.0}], layout_mode="proposed"),
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=[_op("op-1"), _op("op-2")], routes=routes))
    assert artifact.metrics.value.total_crossing_count == 0


def test_crossings_shared_endpoint_is_not_a_crossing():
    routes = [
        _route("a", "op-1", [{"x": 0.0, "y": 0.0}, {"x": 100.0, "y": 0.0}]),
        _route("b", "op-2", [{"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 100.0}]),  # shares (0, 0) with "a"
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=[_op("op-1"), _op("op-2")], routes=routes))
    assert artifact.metrics.value.total_crossing_count == 0


# --- Current/proposed delta table: hand-computable 2x-shorter fixture ------


def test_delta_none_unless_both_layout_modes_have_a_route():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())  # only a "current" route
    assert artifact.metrics.value.delta is None


def test_delta_50_percent_reduction_hand_checked():
    # current: 700px / 10px-per-m = 70m x 6/day = 420 m/day.
    # proposed: 350px / 10px-per-m = 35m x 6/day = 210 m/day -- exactly
    # half, both per-trip and daily (same frequency on both sides).
    routes = make_spaghetti_routes() + [
        _route("route-2", "op-1", [{"x": 0.0, "y": 0.0}, {"x": 350.0, "y": 0.0}], layout_mode="proposed", trip_label="Register to grinder (proposed)"),
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))
    delta = artifact.metrics.value.delta
    assert delta is not None
    by_scope = {d.scope: d for d in delta}

    overall = by_scope["overall"]
    assert overall.current_daily_distance == pytest.approx(420.0)
    assert overall.proposed_daily_distance == pytest.approx(210.0)
    assert overall.distance_delta == pytest.approx(-210.0)
    assert overall.distance_delta_pct == pytest.approx(-50.0)
    assert overall.walk_time_delta_pct == pytest.approx(-50.0)

    assert by_scope["op-1"].distance_delta_pct == pytest.approx(-50.0)


def test_delta_handles_an_operator_present_in_only_one_mode():
    routes = make_spaghetti_routes() + [
        _route("route-2", "op-2", [{"x": 0.0, "y": 0.0}, {"x": 100.0, "y": 0.0}], layout_mode="proposed"),
    ]
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))
    by_scope = {d.scope: d for d in artifact.metrics.value.delta}
    assert by_scope["op-1"].proposed_daily_distance is None
    assert by_scope["op-1"].distance_delta is None
    assert by_scope["op-2"].current_daily_distance is None
