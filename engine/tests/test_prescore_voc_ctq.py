"""Prescore tests for T-05: tree completeness (dangling reference
detection schema typing alone can't do)."""

from factories import make_voc_ctq
from sigma_engine.artifacts.voc_ctq import VocCtqArtifact
from sigma_engine.prescore.voc_ctq import run_voc_ctq_prescore


def test_complete_tree_passes():
    artifact = VocCtqArtifact.model_validate(make_voc_ctq())
    results = run_voc_ctq_prescore(artifact)
    assert results[0].status == "pass"


def test_ctq_with_dangling_need_flags():
    data = make_voc_ctq()
    data["ctqs"][0]["need_id"] = "N-does-not-exist"
    artifact = VocCtqArtifact.model_validate(data)
    results = run_voc_ctq_prescore(artifact)
    assert results[0].status == "flag"
    assert "C1" in results[0].detail


def test_need_with_dangling_statement_flags():
    data = make_voc_ctq()
    data["needs"][0]["statement_ids"] = ["S-does-not-exist"]
    artifact = VocCtqArtifact.model_validate(data)
    results = run_voc_ctq_prescore(artifact)
    assert results[0].status == "flag"
    assert "N1" in results[0].detail
