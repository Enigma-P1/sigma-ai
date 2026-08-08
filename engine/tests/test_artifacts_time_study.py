"""Schema + hand-computed stats tests for T-09 TimeStudyArtifact -- the
5-cycle fixture with one obvious outlier (factories.make_time_study_cycles'
own docstring shows the IQR fence arithmetic; repeated here at the point of
use so this test is self-contained)."""

import math

import pytest
from pydantic import ValidationError

from factories import make_time_study, make_time_study_cycles, make_time_study_elements
from sigma_engine.artifacts.time_study import TimeStudyArtifact, compute_element_stats


def test_accepts_a_complete_time_study():
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    assert len(artifact.elements) == 2
    assert len(artifact.cycles) == 5


def test_elements_required_but_cycles_may_start_empty():
    artifact = TimeStudyArtifact.model_validate(make_time_study(cycles=[]))
    assert artifact.cycles == []
    stats_by_id = {s.element_id: s for s in artifact.element_stats.value}
    assert stats_by_id["steam-milk"].n == 0
    assert stats_by_id["steam-milk"].descriptive is None
    assert stats_by_id["steam-milk"].below_recommended_cycles is True


def test_rejects_empty_elements():
    with pytest.raises(ValidationError):
        TimeStudyArtifact.model_validate(make_time_study(elements=[]))


def test_rejects_cycle_referencing_unknown_element():
    cycles = make_time_study_cycles()
    cycles[0]["element_times"][0]["element_id"] = "no-such-element"
    with pytest.raises(ValidationError, match="unknown element_id"):
        TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))


def test_rejects_duplicate_cycle_numbers():
    cycles = make_time_study_cycles()
    cycles.append({**cycles[0], "cycle_number": cycles[0]["cycle_number"]})
    with pytest.raises(ValidationError, match="cycle_number"):
        TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))


def test_rejects_duplicate_element_id_within_one_cycle():
    cycles = make_time_study_cycles()
    cycles[0]["element_times"].append({"element_id": "steam-milk", "seconds": 5.0})
    with pytest.raises(ValidationError, match="unique within one cycle"):
        TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))


def test_round_trip_via_model_dump():
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    round_tripped = TimeStudyArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


def test_posted_element_stats_is_discarded_and_recomputed():
    """MsaArtifact.result's guarantee, applied here: a hand-typed/tampered
    element_stats can never survive a save."""
    tampered = compute_element_stats(make_element_models(), [])  # a wrong-shaped but validly-typed Computed[...]
    artifact = TimeStudyArtifact.model_validate(
        make_time_study(element_stats=tampered.model_dump(mode="json"))
    )
    assert artifact.element_stats.value[0].n == 5  # real cycles win, not the tampered n=0


def make_element_models():
    from sigma_engine.artifacts.time_study import WorkElement

    return [WorkElement.model_validate(e) for e in make_time_study_elements()]


# --- Hand-computed stats: the 5-cycle fixture, arithmetic shown ------------


def test_hand_computed_stats_and_outlier_fence_for_the_flagged_element():
    """steam-milk's cycle times, in cycle order: [9, 8, 40, 10, 9].
    Sorted: [8, 9, 9, 10, 40] -- n=5 puts every quartile at an exact array
    index (linear-interpolation percentiles need no interpolation here):
      Q1 = sorted[1] = 9
      Q3 = sorted[3] = 10
      IQR = 10 - 9 = 1
      lower fence = Q1 - 1.5*IQR = 9 - 1.5 = 7.5
      upper fence = Q3 + 1.5*IQR = 10 + 1.5 = 11.5
    Cycle 3's 40s is the only value outside [7.5, 11.5] -- the one obvious
    outlier the task brief calls for. mean = (9+8+40+10+9)/5 = 76/5 = 15.2.
    sample SD (n-1 denom): deviations from 15.2 are -6.2, -7.2, 24.8, -5.2,
    -6.2; squared: 38.44, 51.84, 615.04, 27.04, 38.44; sum = 770.8;
    /(5-1) = 192.7; sqrt(192.7) ~= 13.8816 -- asserted below via the same
    formula (math.sqrt), not a hand-typed literal, so it can never drift
    from the engine's own arithmetic.
    """
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    stats_by_id = {s.element_id: s for s in artifact.element_stats.value}
    steam = stats_by_id["steam-milk"]

    assert steam.n == 5
    assert steam.descriptive is not None
    assert steam.descriptive.mean == pytest.approx(15.2)
    assert steam.descriptive.median == pytest.approx(9.0)
    assert steam.descriptive.q1 == pytest.approx(9.0)
    assert steam.descriptive.q3 == pytest.approx(10.0)
    assert steam.descriptive.iqr == pytest.approx(1.0)

    times = [9, 8, 40, 10, 9]
    expected_sd = math.sqrt(sum((t - 15.2) ** 2 for t in times) / (len(times) - 1))
    assert steam.descriptive.sd == pytest.approx(expected_sd)

    assert len(steam.outliers) == 1
    outlier = steam.outliers[0]
    assert outlier.cycle_number == 3
    assert outlier.seconds == pytest.approx(40.0)
    assert outlier.direction == "high"
    assert outlier.fence_value == pytest.approx(11.5)
    assert steam.below_recommended_cycles is True  # n=5 < the 10-cycle guidance floor
    assert "10" in steam.cycle_count_note


def test_clean_element_has_no_outliers():
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    stats_by_id = {s.element_id: s for s in artifact.element_stats.value}
    shot = stats_by_id["pull-shot"]
    assert shot.n == 5
    assert shot.outliers == []
    assert shot.descriptive.q1 == pytest.approx(12.0)
    assert shot.descriptive.q3 == pytest.approx(13.0)


def test_outlier_is_flagged_never_dropped_from_the_mean():
    """Rubric R-MEA-04: the flagged 40s cycle still counts in the mean --
    it is not silently excluded once flagged."""
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    steam = {s.element_id: s for s in artifact.element_stats.value}["steam-milk"]
    without_outlier_mean = (9 + 8 + 10 + 9) / 4
    assert steam.descriptive.mean != pytest.approx(without_outlier_mean)
    assert steam.descriptive.mean == pytest.approx(15.2)


def test_below_two_cycles_has_no_spread_but_still_reports_n():
    cycles = [make_time_study_cycles()[0]]  # only 1 cycle recorded
    artifact = TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))
    stats_by_id = {s.element_id: s for s in artifact.element_stats.value}
    assert stats_by_id["steam-milk"].n == 1
    assert stats_by_id["steam-milk"].descriptive is None  # sample SD needs n>=2
    assert stats_by_id["steam-milk"].outliers == []


# --- Work sampling (optional mode) -----------------------------------------


def test_work_sampling_summary_none_with_no_observations():
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    assert artifact.work_sampling_summary is None


def test_work_sampling_share_per_category_hand_computed():
    observations = [
        {"observation_id": f"o{i}", "timestamp": "2026-08-07T08:00:00", "category": cat, "note": ""}
        for i, cat in enumerate(["working", "working", "working", "waiting", "moving"])
    ]
    artifact = TimeStudyArtifact.model_validate(make_time_study(interval_observations=observations))
    summary = artifact.work_sampling_summary.value
    assert summary.total_observations == 5
    shares = {s.category: s for s in summary.shares}
    assert shares["working"].count == 3
    assert shares["working"].share == pytest.approx(0.6)
    assert shares["waiting"].count == 1
    assert shares["moving"].count == 1
    assert shares["other"].count == 0  # zero-filled, not omitted
    assert shares["other"].share == pytest.approx(0.0)
