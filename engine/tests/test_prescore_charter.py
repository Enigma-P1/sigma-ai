"""Prescore tests for T-03: solution-language, magnitude pattern, and the
buildable-now subset of R-DEF-03/04 (owner placeholder, consequential
metric, risk block).
"""

from factories import make_charter
from sigma_engine.artifacts.charter import CharterArtifact
from sigma_engine.prescore.charter import run_charter_prescore

CHECK_IDS = {
    "problem_statement_solution_language",
    "goal_solution_language",
    "magnitude_pattern",
    "owner_not_placeholder",
    "consequential_metric_present",
    "risk_block_present",
}


def _by_id(results):
    return {r.check_id: r for r in results}


def test_clean_charter_passes_every_check():
    artifact = CharterArtifact.model_validate(make_charter())
    results = _by_id(run_charter_prescore(artifact))
    assert set(results) == CHECK_IDS
    assert all(r.status == "pass" for r in results.values())


def test_solution_shaped_problem_statement_flags():
    data = make_charter()
    data["problem_statement"]["what"] = "We need to train operators because they keep scrapping parts"
    artifact = CharterArtifact.model_validate(data)
    results = _by_id(run_charter_prescore(artifact))
    assert results["problem_statement_solution_language"].status == "flag"
    assert "train" in results["problem_statement_solution_language"].detail


def test_solution_shaped_goal_flags():
    data = make_charter()
    data["goal"]["statement"] = "Install the new labeler by Q3"
    artifact = CharterArtifact.model_validate(data)
    results = _by_id(run_charter_prescore(artifact))
    assert results["goal_solution_language"].status == "flag"


def test_magnitude_without_unit_flags_not_rejects():
    data = make_charter()
    data["problem_statement"]["magnitude"]["unit"] = ""
    artifact = CharterArtifact.model_validate(data)  # schema accepts it
    results = _by_id(run_charter_prescore(artifact))
    assert results["magnitude_pattern"].status == "flag"
    assert "unit" in results["magnitude_pattern"].detail


def test_placeholder_owner_name_flags():
    data = make_charter()
    data["process_owner"] = {"name": "TBD", "role": "Line-2 supervisor"}
    artifact = CharterArtifact.model_validate(data)
    results = _by_id(run_charter_prescore(artifact))
    assert results["owner_not_placeholder"].status == "flag"


def test_no_consequential_metric_flags():
    data = make_charter()
    data["goal"]["consequential_metrics"] = []
    artifact = CharterArtifact.model_validate(data)
    results = _by_id(run_charter_prescore(artifact))
    assert results["consequential_metric_present"].status == "flag"


def test_empty_risk_block_flags():
    artifact = CharterArtifact.model_validate(make_charter(risks=[]))
    results = _by_id(run_charter_prescore(artifact))
    assert results["risk_block_present"].status == "flag"
