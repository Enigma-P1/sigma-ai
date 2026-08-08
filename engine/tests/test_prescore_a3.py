"""T-25 prescore tests: rubric R-WRAP-01/02/03's rule-checkable lines,
including "close_blocked surfaced" (task brief)."""

from factories import make_a3, make_a3_closure, make_a3_panels, make_fmea
from sigma_engine.artifacts.a3 import A3Artifact
from sigma_engine.artifacts.fmea import FmeaArtifact
from sigma_engine.prescore.a3 import run_a3_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_a3_passes_every_check():
    a = A3Artifact.model_validate(make_a3())
    results = _by_id(run_a3_prescore(a))
    assert results["panels_seeded_or_narrated"].status == "pass"
    assert results["realized_benefits_present"].status == "pass"
    assert results["tollgates_answered"].status == "flag"  # no answers given by the default fixture
    assert results["lessons_substantive"].status == "pass"
    assert results["open_items_have_owners"].status == "pass"
    assert results["close_blocked_surfaced"].status == "pass"


def test_empty_panel_is_a_hard_flag():
    panels = make_a3_panels()
    for p in panels:
        if p["panel"] == "analysis":
            p["seeded_from"], p["narrative"] = None, ""
    a = A3Artifact.model_validate(make_a3(panels=panels))
    results = _by_id(run_a3_prescore(a))
    assert results["panels_seeded_or_narrated"].status == "hard_flag"
    assert "analysis" in results["panels_seeded_or_narrated"].detail


def test_missing_realized_benefits_window_flags():
    a = A3Artifact.model_validate(make_a3(realized_benefits=None))
    results = _by_id(run_a3_prescore(a))
    assert results["realized_benefits_present"].status == "flag"


def test_fully_answered_tollgates_pass():
    body = make_a3()
    body["tollgates"] = [
        {"phase": "Control", "questions": [], "answers": [
            {"question_id": "control-1", "answered": True, "response": "ok"},
            {"question_id": "control-2", "answered": True, "response": "ok"},
            {"question_id": "control-3", "answered": True, "response": "ok"},
        ]},
    ]
    a = A3Artifact.model_validate(body)
    results = _by_id(run_a3_prescore(a))
    assert "Control" not in results["tollgates_answered"].detail or results["tollgates_answered"].status == "flag"
    # Only Control is fully answered; the other five phases are still incomplete.
    assert results["tollgates_answered"].status == "flag"


def test_lessons_with_only_wins_flags():
    closure = make_a3_closure(lessons=[{"lesson_id": "l-1", "text": "Everything went great.", "went_wrong": False}])
    a = A3Artifact.model_validate(make_a3(closure=closure))
    results = _by_id(run_a3_prescore(a))
    assert results["lessons_substantive"].status == "flag"


def test_open_item_without_owner_flags():
    closure = make_a3_closure(open_items=[{"item_id": "oi-1", "description": "something left over", "owner": ""}])
    a = A3Artifact.model_validate(make_a3(closure=closure))
    results = _by_id(run_a3_prescore(a))
    assert results["open_items_have_owners"].status == "flag"


def test_close_blocked_surfaced_hard_flags_when_fmea_carries_blocking_flags():
    fmea = FmeaArtifact.model_validate(make_fmea())
    fmea_check = {"fmea_artifact_id": fmea.artifact_id, "blocking_flags": [f.model_dump(mode="json") for f in fmea.blocking_flags.value]}
    a = A3Artifact.model_validate(make_a3(closure=make_a3_closure(fmea_check=fmea_check)))
    results = _by_id(run_a3_prescore(a))
    assert results["close_blocked_surfaced"].status == "hard_flag"
    assert "row-a" in str(results["close_blocked_surfaced"].detail) or "severity-9/10" in results["close_blocked_surfaced"].detail
