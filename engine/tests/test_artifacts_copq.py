"""Schema tests for T-02 CopqArtifact."""

import pytest
from pydantic import ValidationError

from factories import make_copq, make_copq_rows
from sigma_engine.artifacts.copq import CopqArtifact, CopqRow, compute_copq_total


def test_accepts_a_complete_copq():
    artifact = CopqArtifact.model_validate(make_copq())
    assert artifact.total.value == pytest.approx(500 * 12.0 + 80 * 45.0)


def test_row_amount_is_derived_never_hand_typed():
    row = CopqRow.model_validate(make_copq_rows()[0])
    assert row.amount == row.quantity * row.rate
    # amount is a computed_field, not a settable input -- feeding it a
    # different number at construction is simply ignored by the schema,
    # not accepted as an override.
    row2 = CopqRow.model_validate({**make_copq_rows()[0], "amount": 999999})
    assert row2.amount == row2.quantity * row2.rate


def test_custom_category_requires_label():
    rows = make_copq_rows()
    rows.append({
        "category": "custom", "custom_label": None, "quantity": 1, "rate": 100.0,
        "period": "Q2 2026", "basis": "one-off event", "is_estimate": True,
    })
    with pytest.raises(ValidationError):
        CopqArtifact.model_validate(make_copq(rows=rows))


def test_rejects_empty_rows():
    with pytest.raises(ValidationError):
        CopqArtifact.model_validate(make_copq(rows=[]))


def test_rejects_negative_quantity():
    rows = make_copq_rows()
    rows[0]["quantity"] = -5
    with pytest.raises(ValidationError):
        CopqArtifact.model_validate(make_copq(rows=rows))


def test_compute_copq_total_matches_hand_sum():
    rows = [CopqRow.model_validate(r) for r in make_copq_rows()]
    total = compute_copq_total(rows)
    assert total.value == sum(r.quantity * r.rate for r in rows)
    assert total.provenance.method
    assert total.provenance.input_hash


def test_round_trip_via_model_dump():
    artifact = CopqArtifact.model_validate(make_copq())
    round_tripped = CopqArtifact.model_validate(artifact.model_dump(mode="json"))
    assert round_tripped == artifact
