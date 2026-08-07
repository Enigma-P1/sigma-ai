"""Schema tests for T-04 SipocArtifact. Step-count *range enforcement*
lives in prescore (test_prescore_sipoc.py) -- the schema only requires the
list be non-empty, matching the soft/hard split used across every artifact.
"""

import pytest
from pydantic import ValidationError

from factories import make_sipoc
from sigma_engine.artifacts.sipoc import SipocArtifact


def test_accepts_a_complete_sipoc():
    artifact = SipocArtifact.model_validate(make_sipoc())
    assert len(artifact.process_steps) == 5


def test_accepts_three_steps_schema_level():
    """3 steps is schema-legal; prescore hard-flags it (see prescore test)."""
    artifact = SipocArtifact.model_validate(make_sipoc(step_count=3))
    assert len(artifact.process_steps) == 3


def test_accepts_ten_steps_schema_level():
    artifact = SipocArtifact.model_validate(make_sipoc(step_count=10))
    assert len(artifact.process_steps) == 10


def test_rejects_empty_process_steps():
    with pytest.raises(ValidationError):
        SipocArtifact.model_validate(make_sipoc(step_count=0))


def test_rejects_supplier_without_input():
    data = make_sipoc()
    data["supplier_input_pairs"] = [{"supplier": "Resin vendor"}]  # missing "input"
    with pytest.raises(ValidationError):
        SipocArtifact.model_validate(data)


def test_rejects_output_without_customer():
    data = make_sipoc()
    data["output_customer_pairs"] = [{"output": "Molded part"}]  # missing "customer"
    with pytest.raises(ValidationError):
        SipocArtifact.model_validate(data)


def test_round_trip_via_model_dump():
    artifact = SipocArtifact.model_validate(make_sipoc())
    round_tripped = SipocArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
