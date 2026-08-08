"""Schema/behavior tests for T-22 ControlPlanArtifact: monitored items,
OCAP referential integrity, check-in pass/fail against the coffee-bar
IMR chart's own FROZEN limits (the task's hand fixture), next_due
cadence arithmetic, and plan_health's theater/overdue flags."""

import pytest
from pydantic import ValidationError

from factories import (
    TS,
    make_check_in,
    make_check_in_schedule,
    make_control_plan,
    make_monitored_item,
)
from sigma_engine.artifacts.control_plan import ControlPlanArtifact


def test_accepts_a_complete_plan_with_an_accepted_owner():
    a = ControlPlanArtifact.model_validate(make_control_plan())
    assert a.plan_health is not None
    assert a.plan_health.value.ownerless_item_ids == []
    assert a.plan_health.value.is_theater is False


def test_ownerless_item_saves_clean_but_renders_the_theater_flag():
    # Schema-loose on purpose (module docstring) -- an ownerless item must
    # be SAVEABLE so plan_health has something real to flag.
    items = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="", owner_accepted=False)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))
    assert a.plan_health.value.ownerless_item_ids == ["item-2"]
    assert a.plan_health.value.is_theater is True


def test_owner_named_but_not_accepted_flags_unaccepted_not_ownerless():
    items = [make_monitored_item(owner_name="Sam Lee", owner_accepted=False)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))
    assert a.plan_health.value.ownerless_item_ids == []
    assert a.plan_health.value.unaccepted_owner_item_ids == ["item-wait-time"]
    assert a.plan_health.value.is_theater is False


def test_ocap_entry_must_reference_a_real_monitored_item():
    body = make_control_plan()
    body["ocap_entries"][0]["monitored_item_id"] = "no-such-item"
    with pytest.raises(ValidationError, match="unknown monitored_item_id"):
        ControlPlanArtifact.model_validate(body)


def test_duplicate_item_ids_rejected():
    items = [make_monitored_item(), make_monitored_item()]
    with pytest.raises(ValidationError, match="unique"):
        ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))


# ---- Check-in pass/fail against the coffee-bar IMR chart's FROZEN limits
# (hand fixture, task brief: "one check-in entered passing against the
# frozen coffee-bar limits") -- frozen band is [81.276..., 107.640...]. ----

def test_check_in_inside_the_frozen_band_passes():
    schedule = make_check_in_schedule(completed=[make_check_in(value=95.0)])
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    result = a.check_in_schedule.completed[0].result
    assert result is not None
    assert result.value.verdict == "pass"
    assert "inside the frozen band" in result.value.detail


def test_check_in_beyond_the_frozen_ucl_fails():
    schedule = make_check_in_schedule(completed=[make_check_in(value=150.0)])
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    result = a.check_in_schedule.completed[0].result
    assert result.value.verdict == "fail"
    assert "outside the frozen band" in result.value.detail


def test_check_in_below_the_frozen_lcl_fails():
    schedule = make_check_in_schedule(completed=[make_check_in(value=40.0)])
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    assert a.check_in_schedule.completed[0].result.value.verdict == "fail"


def test_p_chart_check_in_uses_p_chart_limits_for_its_own_subgroup_n():
    schedule = make_check_in_schedule(
        frozen_limits={
            "control_chart_artifact_id": "cc-p-001", "chart_type": "p",
            "center": None, "ucl": None, "lcl": None, "p_bar": 0.20, "frozen_at": TS,
        },
        completed=[make_check_in(entered={"kind": "manual", "dataset_id": None, "values": None, "subgroup": {"label": "day-21", "n": 100, "defective_count": 20}})],
    )
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    # p=0.20 exactly at pbar -- clearly inside any symmetric band.
    assert a.check_in_schedule.completed[0].result.value.verdict == "pass"

    schedule2 = make_check_in_schedule(
        frozen_limits={
            "control_chart_artifact_id": "cc-p-001", "chart_type": "p",
            "center": None, "ucl": None, "lcl": None, "p_bar": 0.20, "frozen_at": TS,
        },
        completed=[make_check_in(entered={"kind": "manual", "dataset_id": None, "values": None, "subgroup": {"label": "day-22", "n": 100, "defective_count": 90}})],
    )
    a2 = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule2))
    assert a2.check_in_schedule.completed[0].result.value.verdict == "fail"


def test_frozen_limits_ref_requires_matching_fields_for_its_chart_type():
    schedule = make_check_in_schedule(frozen_limits={
        "control_chart_artifact_id": "cc-imr-001", "chart_type": "imr",
        "center": None, "ucl": None, "lcl": None, "p_bar": None, "frozen_at": TS,
    })
    with pytest.raises(ValidationError, match="requires center/ucl/lcl"):
        ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))


# ---- next_due cadence arithmetic + plan_health overdue ----

def test_next_due_advances_by_completed_count_times_cadence():
    schedule = make_check_in_schedule(completed=[])
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    assert a.check_in_schedule.next_due.value == "2026-08-10"  # 0 completed -- due at start_date

    schedule2 = make_check_in_schedule(completed=[make_check_in(check_in_id="chk-1"), make_check_in(check_in_id="chk-2")])
    a2 = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule2))
    assert a2.check_in_schedule.next_due.value == "2026-08-24"  # start + 2 weeks


def test_next_due_months_cadence_handles_year_rollover():
    schedule = make_check_in_schedule(
        cadence={"unit": "months", "interval": 1}, start_date="2026-12-15",
        completed=[make_check_in(check_in_id="chk-1")],
    )
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule))
    assert a.check_in_schedule.next_due.value == "2027-01-15"


def test_plan_health_overdue_flag_compares_next_due_to_as_of():
    schedule = make_check_in_schedule(completed=[])  # next_due = 2026-08-10
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule, as_of="2026-08-20"))
    assert a.plan_health.value.check_in_overdue is True

    a2 = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule, as_of="2026-08-01"))
    assert a2.plan_health.value.check_in_overdue is False


def test_no_schedule_is_not_overdue():
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=None))
    assert a.plan_health.value.check_in_overdue is False


def test_round_trip_via_model_dump():
    a = ControlPlanArtifact.model_validate(make_control_plan())
    b = ControlPlanArtifact.model_validate(a.model_dump(mode="json"))
    assert b == a
