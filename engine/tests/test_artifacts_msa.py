"""Schema tests for T-12 MsaArtifact: continuous + attribute paths, and the
"result is always server-recomputed, never hand-typed" contract (mirrors
test_artifacts_copq.py's total contract for MsaArtifact.result/verdict).
"""

import pytest
from pydantic import ValidationError

from factories import make_attribute_msa, make_continuous_msa
from sigma_engine.artifacts.msa import MsaArtifact


def test_accepts_a_complete_continuous_msa():
    artifact = MsaArtifact.model_validate(make_continuous_msa())
    assert artifact.result is not None
    assert artifact.result.data_type == "continuous"
    assert artifact.result.verdict in ("acceptable", "marginal", "fail")


def test_accepts_a_complete_attribute_msa():
    artifact = MsaArtifact.model_validate(make_attribute_msa())
    assert artifact.result is not None
    assert artifact.result.data_type == "attribute"
    assert artifact.result.attribute_agreement is not None
    assert artifact.result.attribute_agreement.value.kappa == 1.0  # all raters agree in the fixture


def test_continuous_requires_gauge_increment():
    with pytest.raises(ValidationError):
        MsaArtifact.model_validate(make_continuous_msa(gauge_increment=None))


def test_continuous_requires_at_least_one_item():
    with pytest.raises(ValidationError):
        MsaArtifact.model_validate(make_continuous_msa(continuous_items=[]))


def test_continuous_item_requires_at_least_two_reading_slots():
    bad = make_continuous_msa()
    bad["continuous_items"][0]["readings"] = [10.0]
    with pytest.raises(ValidationError):
        MsaArtifact.model_validate(bad)


def test_attribute_requires_at_least_one_item():
    with pytest.raises(ValidationError):
        MsaArtifact.model_validate(make_attribute_msa(attribute_items=[]))


def test_missing_repeat_reading_is_excluded_and_logged_not_rejected():
    """A None reading slot is a valid (if thin) input -- msa.py excludes
    the item from s_repeat and logs it; the schema itself doesn't reject it."""
    body = make_continuous_msa()
    body["continuous_items"][0]["readings"] = [10.0, None]
    artifact = MsaArtifact.model_validate(body)
    assert artifact.result.repeatability is not None
    assert "item-0" in artifact.result.repeatability.value.items_excluded


def test_posted_result_is_discarded_and_recomputed():
    """Rubric R-MEA-07 'verdict recorded' pre-score line: a hand-typed/
    tampered result can never survive validation, exactly like CopqArtifact's
    total (test_artifacts_copq.py::test_posted_total_is_discarded_and_recomputed)."""
    tampered = make_continuous_msa()
    tampered["result"] = {
        "data_type": "continuous", "verdict": "acceptable", "resolution_check": None,
        "repeatability": None, "attribute_agreement": None, "caveat": None, "exit02": None,
    }
    artifact = MsaArtifact.model_validate(tampered)
    # The tampered stub had resolution_check=None and repeatability=None --
    # if either survived, the tampered dict wasn't actually discarded.
    assert artifact.result.resolution_check is not None
    assert artifact.result.repeatability is not None


def test_round_trip_via_model_dump():
    artifact = MsaArtifact.model_validate(make_continuous_msa())
    round_tripped = MsaArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact


def test_attribute_round_trip_via_model_dump():
    artifact = MsaArtifact.model_validate(make_attribute_msa())
    round_tripped = MsaArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
