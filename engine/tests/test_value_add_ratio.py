"""T-06's value-add ratio — the one number a VSM produces that the process
map was missing.

T-06 already tagged every step value_add / non_value_add / enabling and
already timed them; nothing summed them. The ratio is the VSM punchline:
2.6 minutes of work inside an 8.4-minute lead time reads very differently
from either number alone.
"""

from __future__ import annotations

import pytest

from sigma_engine.artifacts.process_map import compute_value_add_ratio, ProcessStepModel


def _step(step_id: str, step_type: str, minutes: float | None) -> ProcessStepModel:
    return ProcessStepModel.model_validate(
        {
            "step_id": step_id,
            "lane_id": "l1",
            "order": 1,
            "name": step_id,
            "step_type": step_type,
            "time_minutes": minutes,
            "reason": "test",
        }
    )


def test_ratio_is_value_add_over_total_lead_time():
    steps = [_step("a", "value_add", 3.0), _step("b", "non_value_add", 7.0)]
    result = compute_value_add_ratio(steps).value
    assert result.total_lead_time_minutes == 10.0
    assert result.value_add_ratio == pytest.approx(0.3)


def test_enabling_time_counts_in_the_denominator_but_not_the_numerator():
    """Enabling work -- a required inspection, a regulated sign-off -- is
    neither waste nor value-add. Counting it as value-add flatters the
    ratio; counting it as waste tells someone to delete a step they legally
    cannot."""
    steps = [_step("a", "value_add", 2.0), _step("b", "enabling", 2.0), _step("c", "non_value_add", 6.0)]
    result = compute_value_add_ratio(steps).value
    assert result.enabling_minutes == 2.0
    assert result.value_add_minutes == 2.0
    assert result.total_lead_time_minutes == 10.0
    assert result.value_add_ratio == pytest.approx(0.2)


def test_untimed_steps_are_counted_and_reported_not_silently_skipped():
    """A ratio computed over half the steps, presented without saying so, is
    a lie by omission -- the reader has no way to know the denominator is
    partial."""
    steps = [_step("a", "value_add", 3.0), _step("b", "non_value_add", 7.0), _step("c", "non_value_add", None)]
    result = compute_value_add_ratio(steps).value
    assert result.steps_timed == 2
    assert result.steps_untimed == 1
    assert result.total_lead_time_minutes == 10.0


def test_no_timed_steps_returns_none_rather_than_a_zero_ratio():
    """Nothing to divide is not the same as 0% value-add, and a 0% readout
    on an untimed map would be read as a finding."""
    assert compute_value_add_ratio([_step("a", "value_add", None)]) is None


def test_all_zero_times_do_not_divide_by_zero():
    result = compute_value_add_ratio([_step("a", "value_add", 0.0)]).value
    assert result.value_add_ratio == 0.0


def test_result_carries_its_method_for_provenance():
    computed = compute_value_add_ratio([_step("a", "value_add", 1.0)])
    assert "value_add_ratio =" in computed.provenance.method
    assert "Enabling time counts toward the denominator only" in computed.provenance.method


def test_recomputed_on_the_artifact_not_hand_typeable(tmp_path):
    """Same contract as constraint_step and CopqArtifact.total: server
    computed, unconditionally replaced on validate, so a client cannot post
    a flattering ratio."""
    from sigma_engine.artifacts.process_map import ProcessMapArtifact

    artifact = ProcessMapArtifact.model_validate(
        {
            "artifact_id": "pm",
            "tool_id": "T-06",
            "schema_version": 1,
            "created_at": "2026-08-01T00:00:00",
            "updated_at": "2026-08-01T00:00:00",
            "lanes": [{"lane_id": "l1", "name": "Lane"}],
            "steps": [
                {"step_id": "a", "lane_id": "l1", "order": 1, "name": "A", "step_type": "value_add",
                 "time_minutes": 1.0, "reason": "r"},
                {"step_id": "b", "lane_id": "l1", "order": 2, "name": "B", "step_type": "non_value_add",
                 "time_minutes": 9.0, "reason": "r"},
            ],
            # A client-supplied ratio must not survive validation.
            "value_add_ratio": {"value": {"value_add_minutes": 99.0, "enabling_minutes": 0.0,
                                          "non_value_add_minutes": 0.0, "total_lead_time_minutes": 99.0,
                                          "value_add_ratio": 1.0, "steps_timed": 1, "steps_untimed": 0},
                                "provenance": {"method": "hand-typed", "engine_version": "0", "input_hash": "x",
                                               "assumptions_checked": [], "warnings": []}},
        }
    )
    assert artifact.value_add_ratio.value.value_add_ratio == pytest.approx(0.1)
