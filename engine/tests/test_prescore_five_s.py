"""T-23 prescore tests: rubric R-CTL-05's rule-checkable lines."""

from factories import make_five_s, make_five_s_round
from sigma_engine.artifacts.five_s import FiveSArtifact
from sigma_engine.prescore.five_s import run_five_s_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_single_round_with_schedule_passes_every_check():
    a = FiveSArtifact.model_validate(make_five_s())  # has a schedule + a photo-free round + a real action
    results = _by_id(run_five_s_prescore(a))
    assert results["scores_in_range"].status == "pass"
    assert results["uniform_scores_honesty"].status == "pass"
    assert results["recurrence_present"].status == "pass"  # schedule present
    assert results["min_category_action_present"].status == "pass"


def test_no_photos_flags():
    a = FiveSArtifact.model_validate(make_five_s())
    results = _by_id(run_five_s_prescore(a))
    assert results["photos_present"].status == "flag"


def test_uniform_scores_across_a_round_is_an_advisory_flag():
    uniform = make_five_s_round(scores={"sort": 5, "set_in_order": 5, "shine": 5, "standardize": 5, "sustain": 5})
    a = FiveSArtifact.model_validate(make_five_s(rounds=[uniform]))
    results = _by_id(run_five_s_prescore(a))
    assert results["uniform_scores_honesty"].status == "flag"
    assert "advisory" in results["uniform_scores_honesty"].detail


def test_one_round_no_schedule_flags_recurrence():
    a = FiveSArtifact.model_validate(make_five_s(schedule=None))
    results = _by_id(run_five_s_prescore(a))
    assert results["recurrence_present"].status == "flag"


def test_two_rounds_no_schedule_still_passes_recurrence():
    rounds = [make_five_s_round(round_id="round-1", date="2026-08-01"), make_five_s_round(round_id="round-2", date="2026-09-01")]
    a = FiveSArtifact.model_validate(make_five_s(rounds=rounds, schedule=None))
    results = _by_id(run_five_s_prescore(a))
    assert results["recurrence_present"].status == "pass"


def test_missing_lowest_category_action_flags():
    round_no_action = make_five_s_round(improvement_action="")
    a = FiveSArtifact.model_validate(make_five_s(rounds=[round_no_action]))
    results = _by_id(run_five_s_prescore(a))
    assert results["min_category_action_present"].status == "flag"
