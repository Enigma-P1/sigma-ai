"""Prescore tests for T-01 routing-consistency."""

from factories import make_picker
from sigma_engine.artifacts.picker import PickerArtifact
from sigma_engine.prescore.picker import run_picker_prescore


def test_consistent_route_passes():
    artifact = PickerArtifact.model_validate(make_picker())
    results = run_picker_prescore(artifact)
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].check_id == "routing_consistency"


def test_inconsistent_route_flags_when_schema_is_bypassed():
    """The schema validator normally rejects this combination at
    construction; model_copy(update=...) bypasses validators (Pydantic v2
    semantics) so the prescore check itself can be exercised directly."""
    artifact = PickerArtifact.model_validate(make_picker(route="full-DMAIC"))
    tampered = artifact.model_copy(update={"route": "EXIT-01"})
    results = run_picker_prescore(tampered)
    assert results[0].status == "flag"
    assert "inconsistent" in results[0].detail
