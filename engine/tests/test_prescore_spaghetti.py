"""Prescore tests for T-07: each of the 8 checks, driven to both pass and
flag at least once (the clean default fixture passes all 8)."""

from factories import make_operators, make_spaghetti, make_spaghetti_routes
from sigma_engine.artifacts.spaghetti import SpaghettiArtifact
from sigma_engine.prescore.spaghetti import run_spaghetti_prescore

EXPECTED_CHECK_IDS = {
    "calibration_present", "calibration_span_plausible", "route_count_minimum", "route_with_three_plus_points",
    "frequencies_present", "operator_labels_non_placeholder", "observation_window_stated", "metrics_consistency",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_artifact_passes_every_check():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    results = _by_id(run_spaghetti_prescore(artifact))
    assert set(results) == EXPECTED_CHECK_IDS
    for check_id, r in results.items():
        assert r.status == "pass", f"{check_id}: expected pass, got {r.status} ({r.detail})"


def test_calibration_present_flags_when_missing():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=None))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["calibration_present"].status == "flag"
    assert results["calibration_span_plausible"].status == "flag"


def test_calibration_span_plausible_flags_a_tiny_line():
    cal = {"point_a": {"x": 0.0, "y": 0.0}, "point_b": {"x": 2.0, "y": 0.0}, "real_length": 1.0, "unit": "meters"}
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=cal))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["calibration_span_plausible"].status == "flag"
    assert "2.0px" in results["calibration_span_plausible"].detail


def test_route_count_minimum_flags_zero_routes():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(routes=[]))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["route_count_minimum"].status == "flag"
    assert results["frequencies_present"].detail == "no routes yet to check"


def test_route_with_three_plus_points_flags_all_straight_hops():
    routes = make_spaghetti_routes()
    routes[0]["points"] = [{"x": 0.0, "y": 0.0}, {"x": 300.0, "y": 0.0}]  # 2 points only
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(routes=routes))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["route_with_three_plus_points"].status == "flag"


def test_frequencies_present_always_passes():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["frequencies_present"].status == "pass"
    assert "1" in results["frequencies_present"].detail


def test_operator_labels_non_placeholder_flags_a_blocklisted_name():
    operators = make_operators()
    operators[0]["name"] = "TBD"
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=operators))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["operator_labels_non_placeholder"].status == "flag"
    assert "op-1" in results["operator_labels_non_placeholder"].detail


def test_operator_labels_non_placeholder_passes_with_no_operators():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(operators=[], routes=[]))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["operator_labels_non_placeholder"].status == "pass"
    assert results["operator_labels_non_placeholder"].detail == "no operators defined yet"


def test_observation_window_stated_flags_partial_fill():
    artifact = SpaghettiArtifact.model_validate(
        make_spaghetti(observation_window={"when": "Tuesday", "duration": "", "shift": ""})
    )
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["observation_window_stated"].status == "flag"
    assert "duration" in results["observation_window_stated"].detail
    assert "shift" in results["observation_window_stated"].detail


def test_metrics_consistency_flags_a_tampered_stored_value():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti())
    tampered = artifact.model_copy(
        update={"metrics": artifact.metrics.model_copy(
            update={"value": artifact.metrics.value.model_copy(update={"total_daily_distance_all": 999.0})}
        )}
    )
    results = _by_id(run_spaghetti_prescore(tampered))
    assert results["metrics_consistency"].status == "flag"
    assert "hand-edited" in results["metrics_consistency"].detail


def test_metrics_consistency_passes_without_calibration():
    artifact = SpaghettiArtifact.model_validate(make_spaghetti(calibration=None))
    results = _by_id(run_spaghetti_prescore(artifact))
    assert results["metrics_consistency"].status == "pass"
