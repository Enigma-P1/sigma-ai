"""Prescore tests for T-04: process step-count range (rubric R-DEF-06 /
matrix A-2 -- 4-7 pass, 8-9 flag, outside 4-9 hard_flag). Includes the
frozen-boundary golden values the matrix requires (round-3 panel rule)."""

import pytest

from factories import make_sipoc
from sigma_engine.artifacts.sipoc import SipocArtifact
from sigma_engine.prescore.sipoc import run_sipoc_prescore


@pytest.mark.parametrize("n,expected_status", [
    (3, "hard_flag"),
    (4, "pass"),
    (7, "pass"),
    (8, "flag"),
    (9, "flag"),
    (10, "hard_flag"),
])
def test_step_count_boundaries(n, expected_status):
    artifact = SipocArtifact.model_validate(make_sipoc(step_count=n))
    results = run_sipoc_prescore(artifact)
    assert len(results) == 1
    assert results[0].check_id == "step_count_range"
    assert results[0].status == expected_status
