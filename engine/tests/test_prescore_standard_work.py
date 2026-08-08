"""T-24 prescore tests: rubric R-CTL-06's rule-checkable lines."""

from factories import make_standard_work, make_standard_work_steps
from sigma_engine.artifacts.standard_work import StandardWorkArtifact
from sigma_engine.prescore.standard_work import run_standard_work_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_sop_passes_every_check():
    a = StandardWorkArtifact.model_validate(make_standard_work())  # supersedes=None by default, one changed step
    results = _by_id(run_standard_work_prescore(a))
    assert results["step_schema_present"].status == "pass"
    assert results["metadata_present"].status == "pass"
    assert results["changed_steps_marked"].status == "pass"
    assert results["steps_read_as_actions"].status == "pass"


def test_supersedes_named_but_no_step_marked_changed_flags():
    steps = make_standard_work_steps()
    for s in steps:
        s["changed_from_prior"] = False
    a = StandardWorkArtifact.model_validate(make_standard_work(steps=steps, supersedes="Coffee Bar SOP v0"))
    results = _by_id(run_standard_work_prescore(a))
    assert results["changed_steps_marked"].status == "flag"


def test_no_supersedes_never_flags_change_marking():
    steps = make_standard_work_steps()
    for s in steps:
        s["changed_from_prior"] = False
    a = StandardWorkArtifact.model_validate(make_standard_work(steps=steps, supersedes=None))
    results = _by_id(run_standard_work_prescore(a))
    assert results["changed_steps_marked"].status == "pass"


def test_policy_worded_step_flags():
    steps = make_standard_work_steps()
    steps[0]["action"] = "Ensure the fixture is properly aligned before starting"
    a = StandardWorkArtifact.model_validate(make_standard_work(steps=steps))
    results = _by_id(run_standard_work_prescore(a))
    assert results["steps_read_as_actions"].status == "flag"
    assert steps[0]["step_id"] in results["steps_read_as_actions"].detail
