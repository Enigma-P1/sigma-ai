"""T-22 prescore tests: rubric R-CTL-03/04's rule-checkable lines."""

from factories import make_check_in_schedule, make_control_plan, make_monitored_item
from sigma_engine.artifacts.control_plan import ControlPlanArtifact
from sigma_engine.prescore.control_plan import run_control_plan_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_plan_passes_every_check():
    a = ControlPlanArtifact.model_validate(make_control_plan())
    results = _by_id(run_control_plan_prescore(a))
    assert results["owner_named"].status == "pass"
    assert results["owner_accepted"].status == "pass"
    assert results["owner_not_placeholder"].status == "pass"
    assert results["frequency_reason_present"].status == "pass"
    assert results["ctq_and_fix_coverage"].status == "pass"
    assert results["ocap_coverage"].status == "pass"
    assert results["ocap_elements_complete"].status == "pass"
    assert results["training_verification_present"].status == "pass"
    assert results["check_in_overdue"].status == "pass"


def test_ownerless_item_is_a_hard_flag_theater_line():
    items = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="")]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))
    results = _by_id(run_control_plan_prescore(a))
    assert results["owner_named"].status == "hard_flag"
    assert "item-2" in results["owner_named"].detail


def test_placeholder_owner_marked_accepted_is_a_hard_flag():
    """M6 fidelity-panel fix: 'TBD' + accepted=true used to pass BOTH owner
    checks (owner_named only tests blankness, owner_accepted only tests the
    boolean). The blocklist now applies regardless of accepted, and the
    accepted placeholder is the worst case -- hard_flag."""
    items = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="TBD", owner_accepted=True)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))
    results = _by_id(run_control_plan_prescore(a))
    # The two pre-existing checks still can't see it -- that's the gap...
    assert results["owner_named"].status == "pass"
    assert results["owner_accepted"].status == "pass"
    # ...and the new check is what closes it.
    assert results["owner_not_placeholder"].status == "hard_flag"
    assert "an accepted placeholder is not an owner" in results["owner_not_placeholder"].detail
    assert "item-2" in results["owner_not_placeholder"].detail
    assert "TBD" in results["owner_not_placeholder"].detail


def test_placeholder_owner_not_accepted_is_a_soft_flag():
    """'the team', unaccepted: the blocklist fires regardless of accepted,
    but only the accepted case escalates to hard_flag."""
    items = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="the team", owner_accepted=False)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))
    results = _by_id(run_control_plan_prescore(a))
    assert results["owner_not_placeholder"].status == "flag"
    assert "item-2" in results["owner_not_placeholder"].detail
    assert "an accepted placeholder" not in results["owner_not_placeholder"].detail


def test_placeholder_blocklist_is_exact_match_case_insensitive():
    """Deliberately narrow (prescore/charter.py's idiom): 'tbd' in any case
    is caught; a real name that merely contains a blocklisted word is not."""
    caught = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="  tBd ", owner_accepted=True)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=caught))
    assert _by_id(run_control_plan_prescore(a))["owner_not_placeholder"].status == "hard_flag"

    not_caught = [make_monitored_item(), make_monitored_item(item_id="item-2", owner_name="Teamsy Vargas", owner_accepted=True)]
    a2 = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=not_caught))
    assert _by_id(run_control_plan_prescore(a2))["owner_not_placeholder"].status == "pass"


def test_placeholder_per_shift_owner_is_caught_too():
    """ShiftOwner carries the same name+accepted pair as the top-level
    owner field, so the blocklist reads it the same way."""
    item = make_monitored_item(
        per_shift_owners=[{"shift": "nights", "owner_name": "TBD", "owner_accepted": True}],
    )
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=[item]))
    results = _by_id(run_control_plan_prescore(a))
    assert results["owner_not_placeholder"].status == "hard_flag"
    assert "nights" in results["owner_not_placeholder"].detail


def test_primary_ctq_with_no_ocap_is_hard_flagged():
    a = ControlPlanArtifact.model_validate(make_control_plan(ocap_entries=[]))
    results = _by_id(run_control_plan_prescore(a))
    assert results["ocap_coverage"].status == "hard_flag"
    assert "primary-CTQ" in results["ocap_coverage"].detail


def test_non_primary_item_with_no_ocap_is_only_a_soft_flag():
    items = [make_monitored_item(), make_monitored_item(item_id="item-2", is_primary_ctq=False)]
    a = ControlPlanArtifact.model_validate(make_control_plan(monitored_items=items))  # ocap_entries covers item-wait-time only
    results = _by_id(run_control_plan_prescore(a))
    assert results["ocap_coverage"].status == "flag"


def test_ocap_missing_escalation_contact_flags():
    body = make_control_plan()
    body["ocap_entries"][0]["escalation_contact"] = ""
    a = ControlPlanArtifact.model_validate(body)
    results = _by_id(run_control_plan_prescore(a))
    assert results["ocap_elements_complete"].status == "flag"


def test_frequency_without_reason_flags():
    body = make_control_plan()
    body["monitored_items"][0]["frequency_reason"] = ""
    a = ControlPlanArtifact.model_validate(body)
    results = _by_id(run_control_plan_prescore(a))
    assert results["frequency_reason_present"].status == "flag"


def test_missing_primary_ctq_or_improve_change_coverage_flags():
    items = [make_monitored_item(is_primary_ctq=False, is_improve_change=False)]
    body = make_control_plan(monitored_items=items)
    body["ocap_entries"][0]["monitored_item_id"] = items[0]["item_id"]
    a = ControlPlanArtifact.model_validate(body)
    results = _by_id(run_control_plan_prescore(a))
    assert results["ctq_and_fix_coverage"].status == "flag"
    assert "primary CTQ" in results["ctq_and_fix_coverage"].detail


def test_training_row_without_verification_method_flags():
    body = make_control_plan()
    body["training_rows"][0]["verified_how"] = ""
    a = ControlPlanArtifact.model_validate(body)
    results = _by_id(run_control_plan_prescore(a))
    assert results["training_verification_present"].status == "flag"


def test_overdue_check_in_flags():
    schedule = make_check_in_schedule(completed=[])
    a = ControlPlanArtifact.model_validate(make_control_plan(check_in_schedule=schedule, as_of="2026-09-01"))
    results = _by_id(run_control_plan_prescore(a))
    assert results["check_in_overdue"].status == "flag"
