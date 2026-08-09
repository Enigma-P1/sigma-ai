"""T-22 prescore: rubric R-CTL-03/R-CTL-04's rule-checkable lines.

`owner_named` renders `plan_health.ownerless_item_ids` as the FAIL-level
(hard_flag) theater check the task brief and R-CTL-03's own Fail line both
name explicitly. `owner_not_placeholder` closes the gap the M6 fidelity
panel named: a placeholder name ("TBD", "the team") is not an owner
whatever the accepted flag says, and a placeholder marked accepted=true is
the worst case -- the record claims a handoff that cannot have happened.
`ocap_coverage` escalates to hard_flag only for the primary-CTQ item --
R-CTL-04's Fail line is specifically "the primary CTQ has no response path
at all," not every item.
"""

from __future__ import annotations

from ..artifacts.control_plan import ControlPlanArtifact, MonitoredItem
from .charter import PLACEHOLDER_OWNER_NAMES
from .common import PrescoreResult

# R-DEF-04's owner-name blocklist, shared from prescore/charter.py rather
# than mirrored (the same exact-match-on-trimmed-lowercase approach --
# deliberately narrow, so a real person named e.g. "Teamsy" is never
# caught), plus "the team" -- the group-noun form a control plan's owner
# column attracts (the M6 fidelity panel's own exhibit): an article in
# front doesn't make a team a person.
PLACEHOLDER_CONTROL_PLAN_OWNER_NAMES = PLACEHOLDER_OWNER_NAMES | frozenset({"the team"})


def run_control_plan_prescore(artifact: ControlPlanArtifact) -> list[PrescoreResult]:
    return [
        _owner_named(artifact),
        _owner_accepted(artifact),
        _owner_not_placeholder(artifact),
        _frequency_reason_present(artifact),
        _ctq_and_fix_coverage(artifact),
        _ocap_coverage(artifact),
        _ocap_elements_complete(artifact),
        _training_verification_present(artifact),
        _check_in_overdue(artifact),
    ]


def _owner_named(artifact: ControlPlanArtifact) -> PrescoreResult:
    assert artifact.plan_health is not None
    bad = artifact.plan_health.value.ownerless_item_ids
    ok = not bad
    return PrescoreResult(
        check_id="owner_named", tool_id="T-22", status="pass" if ok else "hard_flag",
        detail=(
            "every monitored item names an owner" if ok
            else f"ownerless monitored item(s) -- an unowned control plan is theater, and this rubric agrees (R-CTL-03 Fail line): {bad}"
        ),
    )


def _owner_accepted(artifact: ControlPlanArtifact) -> PrescoreResult:
    assert artifact.plan_health is not None
    bad = artifact.plan_health.value.unaccepted_owner_item_ids
    ok = not bad
    return PrescoreResult(
        check_id="owner_accepted", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "every named owner has accepted the role" if ok
            else f"item(s) with a named owner and no evidence of handoff (R-CTL-03 Needs-work line): {bad}"
        ),
    )


def _placeholder_owner_entries(item: MonitoredItem) -> list[tuple[str, str, bool]]:
    """(label, name, accepted) for every owner field on this item whose
    name is on the blocklist -- the top-level owner plus any per-shift
    owners, since both carry the same name+accepted pair the two checks
    above read."""
    entries: list[tuple[str, str, bool]] = []
    if item.owner_name.strip().lower() in PLACEHOLDER_CONTROL_PLAN_OWNER_NAMES:
        entries.append((item.item_id, item.owner_name, item.owner_accepted))
    for shift in item.per_shift_owners:
        if shift.owner_name.strip().lower() in PLACEHOLDER_CONTROL_PLAN_OWNER_NAMES:
            entries.append((f"{item.item_id} (shift {shift.shift!r})", shift.owner_name, shift.owner_accepted))
    return entries


def _owner_not_placeholder(artifact: ControlPlanArtifact) -> PrescoreResult:
    """M6 fidelity-panel fix: the blocklist applies to owner fields
    REGARDLESS of the accepted flag -- `owner_named` only tests blankness
    and `owner_accepted` only tests the boolean, so "TBD" + accepted=true
    used to pass both. Placeholder+accepted is the worst case (hard_flag):
    an accepted placeholder is not an owner, it is a record claiming a
    handoff to nobody. A placeholder not yet marked accepted flags (and
    also shows in owner_accepted's own needs-work line)."""
    placeholders = [e for i in artifact.monitored_items for e in _placeholder_owner_entries(i)]
    if not placeholders:
        return PrescoreResult(
            check_id="owner_not_placeholder", tool_id="T-22", status="pass",
            detail="no owner field carries a placeholder name",
        )
    accepted = [(label, name) for label, name, acc in placeholders if acc]
    unaccepted = [(label, name) for label, name, acc in placeholders if not acc]
    parts = []
    if accepted:
        parts.append(
            "an accepted placeholder is not an owner -- item(s) with a placeholder owner name marked "
            f"accepted, as if a real person had taken the handoff (R-CTL-03 Fail line): {accepted}"
        )
    if unaccepted:
        parts.append(f"item(s) with a placeholder owner name (R-CTL-03 / R-DEF-04's blocklist): {unaccepted}")
    return PrescoreResult(
        check_id="owner_not_placeholder", tool_id="T-22",
        status="hard_flag" if accepted else "flag",
        detail="; ".join(parts),
    )


def _frequency_reason_present(artifact: ControlPlanArtifact) -> PrescoreResult:
    missing = [i.item_id for i in artifact.monitored_items if not i.frequency_reason.strip()]
    ok = not missing
    return PrescoreResult(
        check_id="frequency_reason_present", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "every item's monitoring frequency carries a stated reason" if ok
            else f"item(s) with a frequency but no stated reason -- a default left standing (R-CTL-03 #2): {missing}"
        ),
    )


def _ctq_and_fix_coverage(artifact: ControlPlanArtifact) -> PrescoreResult:
    has_ctq = any(i.is_primary_ctq for i in artifact.monitored_items)
    has_fix = any(i.is_improve_change for i in artifact.monitored_items)
    missing = (["primary CTQ"] if not has_ctq else []) + (["the Improve change"] if not has_fix else [])
    ok = not missing
    return PrescoreResult(
        check_id="ctq_and_fix_coverage", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "the plan covers both the primary CTQ and what Improve changed" if ok
            else f"the plan is missing coverage of: {', '.join(missing)} (R-CTL-03 #3)"
        ),
    )


def _ocap_coverage(artifact: ControlPlanArtifact) -> PrescoreResult:
    covered = {o.monitored_item_id for o in artifact.ocap_entries}
    primary_uncovered = [i.item_id for i in artifact.monitored_items if i.is_primary_ctq and i.item_id not in covered]
    other_uncovered = [i.item_id for i in artifact.monitored_items if not i.is_primary_ctq and i.item_id not in covered]
    if primary_uncovered:
        return PrescoreResult(
            check_id="ocap_coverage", tool_id="T-22", status="hard_flag",
            detail=(
                f"the primary-CTQ monitored item(s) have no OCAP response path at all -- a signal would fire into "
                f"silence (R-CTL-04 Fail line): {primary_uncovered}"
            ),
        )
    ok = not other_uncovered
    return PrescoreResult(
        check_id="ocap_coverage", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "every monitored item has at least one OCAP entry" if ok
            else f"monitored item(s) with no OCAP entry yet: {other_uncovered}"
        ),
    )


def _ocap_elements_complete(artifact: ControlPlanArtifact) -> PrescoreResult:
    incomplete = [
        o.ocap_id for o in artifact.ocap_entries
        if len(o.action_steps) < 2 or not o.escalation_contact.strip() or not o.acting_owner.strip()
    ]
    ok = not incomplete
    return PrescoreResult(
        check_id="ocap_elements_complete", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "every OCAP entry carries a first response, a containment step, an escalation contact, and an acting "
            "owner" if ok else f"OCAP entr(y/ies) missing a concrete element (R-CTL-04 #1): {incomplete}"
        ),
    )


def _training_verification_present(artifact: ControlPlanArtifact) -> PrescoreResult:
    missing = [r.row_id for r in artifact.training_rows if not r.verified_how.strip()]
    ok = not missing
    return PrescoreResult(
        check_id="training_verification_present", tool_id="T-22", status="pass" if ok else "flag",
        detail=(
            "every training row names how it was verified" if ok
            else f"training row(s) listed with no verification method (R-CTL-04 Needs-work line): {missing}"
        ),
    )


def _check_in_overdue(artifact: ControlPlanArtifact) -> PrescoreResult:
    assert artifact.plan_health is not None
    overdue = artifact.plan_health.value.check_in_overdue
    return PrescoreResult(
        check_id="check_in_overdue", tool_id="T-22", status="pass" if not overdue else "flag",
        detail=artifact.plan_health.value.check_in_overdue_detail,
    )
