from factories import make_time_study, make_time_study_cycles
from sigma_engine.artifacts.time_study import TimeStudyArtifact
from sigma_engine.prescore.time_study import run_time_study_prescore


def test_default_fixture_prescore_shape():
    """5 cycles is below the 10-cycle guidance floor (flag, not fail), and
    the fixture's outlier cycle already carries an explanatory note."""
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    results = run_time_study_prescore(artifact)
    by_id = {r.check_id: r for r in results}

    assert by_id["elements_defined_before_timing"].status == "pass"
    assert by_id["cycle_count_floor"].status == "flag"
    assert "Steam milk" in by_id["cycle_count_floor"].detail
    assert "Pull shot" in by_id["cycle_count_floor"].detail
    assert by_id["spread_present"].status == "pass"
    assert by_id["outliers_have_notes"].status == "pass"
    assert by_id["stats_match_recomputation"].status == "pass"


def test_untimed_element_flags_cycle_count_floor_separately():
    cycles = [{**c, "element_times": [et for et in c["element_times"] if et["element_id"] != "pull-shot"]} for c in make_time_study_cycles()]
    artifact = TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))
    results = run_time_study_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["cycle_count_floor"].status == "flag"
    assert "not yet timed at all" in by_id["cycle_count_floor"].detail
    assert "Pull shot" in by_id["cycle_count_floor"].detail


def test_meeting_the_cycle_floor_passes():
    # 10 identical cycles per element -- meets the floor, no outliers.
    cycles = [
        {"cycle_number": i + 1, "element_times": [
            {"element_id": "steam-milk", "seconds": 10.0}, {"element_id": "pull-shot", "seconds": 12.0},
        ], "observer_note": ""}
        for i in range(10)
    ]
    artifact = TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))
    results = run_time_study_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["cycle_count_floor"].status == "pass"
    assert "10-cycle guidance" in by_id["cycle_count_floor"].detail


def test_outlier_without_a_note_flags():
    cycles = make_time_study_cycles()
    cycles[2]["observer_note"] = ""  # strip the outlier cycle's explanation
    artifact = TimeStudyArtifact.model_validate(make_time_study(cycles=cycles))
    results = run_time_study_prescore(artifact)
    by_id = {r.check_id: r for r in results}
    assert by_id["outliers_have_notes"].status == "flag"
    assert "Steam milk cycle 3" in by_id["outliers_have_notes"].detail


def test_stats_match_recomputation_flags_a_hand_edited_file():
    """Same tampering idiom as test_prescore_msa.py's
    test_tampered_result_flags_result_matches_inputs: model_copy(update=...)
    at each nesting level, simulating a hand-edited on-disk JSON file."""
    artifact = TimeStudyArtifact.model_validate(make_time_study())
    tampered_stats0 = artifact.element_stats.value[0].model_copy(update={"n": 999})
    tampered_value = [tampered_stats0, *artifact.element_stats.value[1:]]
    tampered_computed = artifact.element_stats.model_copy(update={"value": tampered_value})
    tampered = artifact.model_copy(update={"element_stats": tampered_computed})

    results = run_time_study_prescore(tampered)
    by_id = {r.check_id: r for r in results}
    assert by_id["stats_match_recomputation"].status == "flag"
    assert "hand-edited" in by_id["stats_match_recomputation"].detail
