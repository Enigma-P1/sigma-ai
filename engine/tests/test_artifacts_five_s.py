"""Schema/behavior tests for T-23 FiveSArtifact: category coverage,
per-round total/lowest_category computed fields, and the trend series
across rounds (task brief: "trend computation")."""

import pytest
from pydantic import ValidationError

from factories import make_five_s, make_five_s_round
from sigma_engine.artifacts.five_s import FiveSArtifact


def test_accepts_a_complete_round_and_computes_total():
    a = FiveSArtifact.model_validate(make_five_s())
    assert a.rounds[0].total == 4 + 3 + 4 + 3 + 2  # 16
    assert a.rounds[0].lowest_category == "sustain"  # the score-2 category


def test_round_must_cover_every_category_exactly_once():
    body = make_five_s()
    body["rounds"][0]["scores"] = body["rounds"][0]["scores"][:-1]  # drop "sustain"
    with pytest.raises(ValidationError, match="must cover exactly"):
        FiveSArtifact.model_validate(body)


def test_score_out_of_range_rejected():
    body = make_five_s()
    body["rounds"][0]["scores"][0]["score"] = 6
    with pytest.raises(ValidationError):
        FiveSArtifact.model_validate(body)


def test_duplicate_round_ids_rejected():
    rounds = [make_five_s_round(), make_five_s_round()]
    with pytest.raises(ValidationError, match="unique"):
        FiveSArtifact.model_validate(make_five_s(rounds=rounds))


def test_trend_computation_orders_by_date_and_carries_every_point():
    rounds = [
        make_five_s_round(round_id="round-2", date="2026-09-01", scores={"sort": 5, "set_in_order": 5, "shine": 5, "standardize": 5, "sustain": 4}),
        make_five_s_round(round_id="round-1", date="2026-08-01", scores={"sort": 4, "set_in_order": 3, "shine": 4, "standardize": 3, "sustain": 2}),
    ]
    a = FiveSArtifact.model_validate(make_five_s(rounds=rounds))
    trend = a.trend.value
    assert [p.round_id for p in trend] == ["round-1", "round-2"]  # date order, despite input order
    assert [p.total for p in trend] == [16, 24]
    assert trend[0].lowest_category == "sustain"
    assert trend[1].per_category == {"sort": 5, "set_in_order": 5, "shine": 5, "standardize": 5, "sustain": 4}


def test_uniform_scores_are_a_legal_round_the_fixture_for_prescores_honesty_flag():
    uniform = make_five_s_round(scores={"sort": 5, "set_in_order": 5, "shine": 5, "standardize": 5, "sustain": 5})
    a = FiveSArtifact.model_validate(make_five_s(rounds=[uniform]))
    assert a.rounds[0].total == 25
    assert len({s.score for s in a.rounds[0].scores}) == 1


def test_round_trip_via_model_dump():
    a = FiveSArtifact.model_validate(make_five_s())
    b = FiveSArtifact.model_validate(a.model_dump(mode="json"))
    assert b == a
