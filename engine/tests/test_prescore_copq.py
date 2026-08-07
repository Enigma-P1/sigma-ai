"""Prescore tests for T-02: total-matches-rows + period consistency."""

from factories import make_copq, make_copq_rows
from sigma_engine.artifacts.copq import CopqArtifact
from sigma_engine.prescore.copq import run_copq_prescore


def _by_id(results):
    return {r.check_id: r for r in results}


def test_consistent_copq_passes_both_checks():
    artifact = CopqArtifact.model_validate(make_copq())
    results = _by_id(run_copq_prescore(artifact))
    assert results["total_matches_rows"].status == "pass"
    assert results["period_consistency"].status == "pass"


def test_tampered_total_flags():
    artifact = CopqArtifact.model_validate(make_copq())
    tampered = artifact.model_copy(update={"total": artifact.total.model_copy(update={"value": 1.0})})
    results = _by_id(run_copq_prescore(tampered))
    assert results["total_matches_rows"].status == "flag"


def test_mixed_periods_flag():
    rows = make_copq_rows()
    rows[1]["period"] = "Q3 2026"
    artifact = CopqArtifact.model_validate(make_copq(rows=rows))
    results = _by_id(run_copq_prescore(artifact))
    assert results["period_consistency"].status == "flag"
    assert "Q2 2026" in results["period_consistency"].detail
