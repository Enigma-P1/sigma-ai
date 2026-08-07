"""Tests for provenance.py: hashing, compute(), and frozen-field immutability."""

import pytest
from pydantic import ValidationError

from sigma_engine import __version__
from sigma_engine.provenance import Computed, ProvenanceRecord, compute, hash_input


def test_hash_input_is_deterministic():
    assert hash_input({"a": 1, "b": 2}) == hash_input({"b": 2, "a": 1})  # key order doesn't matter


def test_hash_input_differs_for_different_data():
    assert hash_input([1, 2, 3]) != hash_input([1, 2, 4])


def test_compute_stamps_engine_version_and_hash():
    result = compute(42.0, method="sum(x)", input_data=[1, 2, 3], assumptions_checked=["a"], warnings=["w"])
    assert result.value == 42.0
    assert result.provenance.engine_version == __version__
    assert result.provenance.method == "sum(x)"
    assert result.provenance.input_hash == hash_input([1, 2, 3])
    assert result.provenance.assumptions_checked == ("a",)
    assert result.provenance.warnings == ("w",)


def test_computed_value_assignment_raises():
    result = compute(1.0, method="m", input_data=1)
    with pytest.raises(ValidationError):
        result.value = 2.0


def test_provenance_record_assignment_raises():
    record = ProvenanceRecord(input_hash="abc", method="m", engine_version="0.1.0")
    with pytest.raises(ValidationError):
        record.method = "other"


def test_computed_provenance_assignment_raises():
    result = compute(1.0, method="m", input_data=1)
    with pytest.raises(ValidationError):
        result.provenance = ProvenanceRecord(input_hash="x", method="y", engine_version="z")


def test_computed_round_trips_through_json():
    result = compute(3.5, method="m", input_data={"x": 1}, assumptions_checked=["ok"])
    dumped = result.model_dump(mode="json")
    reloaded = Computed[float].model_validate(dumped)
    assert reloaded == result
