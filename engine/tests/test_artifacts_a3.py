"""Schema/behavior tests for T-25 A3Artifact: panel completeness, tollgate
question stamping, realized-benefits arithmetic, the objectives-vs-charter
verdict (reusing proof.compute_gap), and the close-block loop -- an
unaddressed severity-9/10 FMEA row blocks closure; an action added clears
it (task brief's star scenario)."""

import pytest
from pydantic import ValidationError

from factories import make_a3, make_a3_closure, make_fmea, make_fmea_rows
from sigma_engine.artifacts.a3 import PANEL_ORDER, TOLLGATE_PHASES, A3Artifact
from sigma_engine.artifacts.fmea import FmeaArtifact


def test_accepts_a_complete_a3_and_orders_panels_canonically():
    body = make_a3()
    body["panels"] = list(reversed(body["panels"]))  # scrambled input order
    a = A3Artifact.model_validate(body)
    assert tuple(p.panel for p in a.panels) == PANEL_ORDER


def test_missing_panel_kind_rejected():
    body = make_a3()
    body["panels"] = body["panels"][:-1]  # drop "lessons" -- fewer than 8 panels, schema-length-rejected
    with pytest.raises(ValidationError, match="at least 8 items"):
        A3Artifact.model_validate(body)


def test_duplicate_panel_kind_rejected():
    body = make_a3()
    body["panels"][-1] = dict(body["panels"][0])  # duplicate "background", still missing "lessons"
    with pytest.raises(ValidationError, match="must cover exactly"):
        A3Artifact.model_validate(body)


def test_tollgates_are_engine_stamped_with_original_wording_for_all_six_phases():
    a = A3Artifact.model_validate(make_a3())
    assert tuple(t.phase for t in a.tollgates) == TOLLGATE_PHASES
    for t in a.tollgates:
        assert len(t.questions) >= 3
        assert all(q.text.strip() for q in t.questions)


def test_tollgate_answers_survive_a_round_trip_but_questions_are_never_client_supplied():
    body = make_a3()
    body["tollgates"] = [{
        "phase": "Control",
        "questions": [{"question_id": "fake", "text": "a client cannot inject a question"}],  # discarded
        "answers": [{"question_id": "control-1", "answered": True, "response": "Maria Ortiz accepted the role.", "evidence_ref": "control-plan-001"}],
    }]
    a = A3Artifact.model_validate(body)
    control_tg = next(t for t in a.tollgates if t.phase == "Control")
    assert [q.question_id for q in control_tg.questions] == ["control-1", "control-2", "control-3"]
    assert control_tg.answers[0].response == "Maria Ortiz accepted the role."


def test_realized_benefits_arithmetic_is_engine_computed():
    a = A3Artifact.model_validate(make_a3())
    result = a.realized_benefits.result.value
    assert result.realized_to_date == pytest.approx(40000.0 - 15000.0)
    assert result.net_of_fix_cost == pytest.approx(40000.0 - 15000.0 - 2000.0)


def test_objectives_verdict_reuses_proof_compute_gap_verbatim():
    a = A3Artifact.model_validate(make_a3())
    gap = a.closure.objectives_verdict.value
    # charter_baseline=6.2, goal=3.0, achieved=4.03, lower_is_better -- same
    # numbers/direction as factories.make_proof's own partial-recovery fixture.
    assert gap.original_gap == pytest.approx(3.2)
    assert gap.recovered == pytest.approx(6.2 - 4.03)
    assert gap.goal_met is False
    assert 0 < gap.recovered_pct < 100


# ---- The close-block loop (task brief's star scenario) ----

def test_close_block_loop_unaddressed_sev9_blocks_then_clears_when_actioned():
    # Step 1: an FMEA with row-a left severity-9, safety-worded, unaddressed
    # (factories.make_fmea's own blocking_flags fixture).
    fmea = FmeaArtifact.model_validate(make_fmea())
    assert len(fmea.blocking_flags.value) == 1
    assert fmea.blocking_flags.value[0].row_id == "row-a"

    fmea_check = {
        "fmea_artifact_id": fmea.artifact_id,
        "blocking_flags": [f.model_dump(mode="json") for f in fmea.blocking_flags.value],
    }

    # Step 2: the A3 sees it -- close_blocked is True, and the row is named.
    open_a3 = A3Artifact.model_validate(make_a3(closure=make_a3_closure(fmea_check=fmea_check, project_status="open")))
    assert open_a3.closure.close_check.value.close_blocked is True
    assert open_a3.closure.close_check.value.blocking_rows[0].row_id == "row-a"

    # Step 3: trying to mark the project closed while blocked is a hard
    # refusal (R-WRAP-03/R-ANA-03), not a silent acceptance.
    with pytest.raises(ValidationError, match="R-WRAP-03/R-ANA-03"):
        A3Artifact.model_validate(make_a3(closure=make_a3_closure(fmea_check=fmea_check, project_status="closed")))

    # Step 4: an action + owner is added to the FMEA row -- blocking_flags clears.
    fixed_rows = make_fmea_rows()
    fixed_rows[0]["action"] = "Add a second injector-pressure check before mold"
    fixed_rows[0]["action_owner"] = "Sam Lee"
    fixed_fmea = FmeaArtifact.model_validate(make_fmea(rows=fixed_rows))
    assert fixed_fmea.blocking_flags.value == []

    cleared_check = {"fmea_artifact_id": fixed_fmea.artifact_id, "blocking_flags": []}

    # Step 5: the A3 now closes cleanly.
    closed_a3 = A3Artifact.model_validate(make_a3(closure=make_a3_closure(fmea_check=cleared_check, project_status="closed")))
    assert closed_a3.closure.close_check.value.close_blocked is False
    assert closed_a3.closure.project_status == "closed"


def test_no_fmea_linked_does_not_block_closure():
    a = A3Artifact.model_validate(make_a3(closure=make_a3_closure(fmea_check=None, project_status="closed")))
    assert a.closure.close_check.value.close_blocked is False


def test_round_trip_via_model_dump():
    a = A3Artifact.model_validate(make_a3())
    b = A3Artifact.model_validate(a.model_dump(mode="json"))
    assert b == a
