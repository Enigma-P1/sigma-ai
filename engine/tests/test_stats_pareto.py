"""Tests for stats/pareto.py: sorting, cumulative share, the 80% vital-few
line, and the honest "flat" case (docs/research §F "flat-bars honest
headline") -- PLAN §4.1 T-14 row.
"""

import pytest

from sigma_engine.stats.pareto import compute_pareto


def test_sorted_descending_by_count_with_cumulative_share():
    # register=16, grinder=4, restock=2, training=2 -- hand-verified in
    # the M2 build notes: register alone is 66.7% (not yet 80%); +grinder
    # crosses to 83.3%.
    categories = ["register"] * 16 + ["grinder"] * 4 + ["restock"] * 2 + ["training"] * 2
    result = compute_pareto(categories)
    cats = result.value.categories
    assert [c.category for c in cats] == ["register", "grinder", "restock", "training"]
    assert cats[0].count == 16
    assert cats[0].share == pytest.approx(16 / 24)
    assert cats[0].cumulative_share == pytest.approx(16 / 24)
    assert cats[1].cumulative_share == pytest.approx(20 / 24)
    assert result.value.total == 24


def test_vital_few_is_the_smallest_prefix_crossing_80_percent():
    categories = ["register"] * 16 + ["grinder"] * 4 + ["restock"] * 2 + ["training"] * 2
    result = compute_pareto(categories)
    cats = result.value.categories
    assert cats[0].vital_few is True   # 66.7% -- not yet crossed, but included
    assert cats[1].vital_few is True   # crosses to 83.3% right here
    assert cats[2].vital_few is False
    assert cats[3].vital_few is False
    assert result.value.vital_few_count == 2


def test_flat_distribution_is_named_honestly_not_forced_into_a_vital_few():
    # Four categories, perfectly even -- no small subset dominates.
    categories = ["a", "b", "c", "d"] * 10
    result = compute_pareto(categories)
    assert result.value.flat is True
    # Still sorted/computed correctly even though flat -- the tiebreak is
    # alphabetical on equal counts.
    assert [c.category for c in result.value.categories] == ["a", "b", "c", "d"]


def test_non_flat_distribution_is_not_marked_flat():
    categories = ["register"] * 16 + ["grinder"] * 4 + ["restock"] * 2 + ["training"] * 2
    result = compute_pareto(categories)
    assert result.value.flat is False


def test_single_category_reads_as_flat_not_a_triumphant_vital_few():
    result = compute_pareto(["only"] * 5)
    assert result.value.vital_few_count == 1
    assert result.value.flat is True


def test_rejects_empty_input():
    with pytest.raises(ValueError, match="at least one category"):
        compute_pareto([])


def test_result_is_provenance_stamped():
    result = compute_pareto(["a", "a", "b"])
    assert result.provenance.method
    assert result.provenance.input_hash


def test_pareto_result_round_trips_through_json():
    from sigma_engine.stats.pareto import ParetoResult

    result = compute_pareto(["a", "a", "b", "c"])
    dumped = result.model_dump(mode="json")
    reloaded = ParetoResult.model_validate(dumped["value"])
    assert reloaded == result.value
