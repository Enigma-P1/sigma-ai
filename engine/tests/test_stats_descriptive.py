"""Reference tests for stats/descriptive.py.

Mean and sample sd are checked against three NIST StRD Univariate Summary
Statistics certified values (Lew, embedded pre-M2; Lottery and Mavro,
fetched live 2026-08-07 -- see nist_lottery.py / nist_mavro.py), to
1e-9 relative tolerance, StRD's own certification precision. StRD does
not certify median/IQR/min/max, so those are checked against a small
hand-computed fixture with the arithmetic shown below.
"""

import pytest

from sigma_engine.nist_lew import CERTIFIED_MEAN as LEW_MEAN, CERTIFIED_STDEV as LEW_SD, DATA as LEW_DATA
from sigma_engine.nist_lottery import CERTIFIED_MEAN as LOTTERY_MEAN, CERTIFIED_STDEV as LOTTERY_SD, DATA as LOTTERY_DATA
from sigma_engine.nist_mavro import CERTIFIED_MEAN as MAVRO_MEAN, CERTIFIED_STDEV as MAVRO_SD, DATA as MAVRO_DATA
from sigma_engine.stats.descriptive import compute_descriptive_stats, iqr, mean, median, quartiles, sample_sd

RELATIVE_TOLERANCE = 1e-9  # StRD's own certification precision

STRD_CASES = [
    pytest.param(LEW_DATA, LEW_MEAN, LEW_SD, 200, id="Lew"),
    pytest.param(LOTTERY_DATA, LOTTERY_MEAN, LOTTERY_SD, 218, id="Lottery"),
    pytest.param(MAVRO_DATA, MAVRO_MEAN, MAVRO_SD, 50, id="Mavro"),
]


@pytest.mark.parametrize("data,certified_mean,certified_sd,expected_n", STRD_CASES)
def test_mean_matches_nist_strd_certified_value(data, certified_mean, certified_sd, expected_n):
    assert len(data) == expected_n
    got = mean(data)
    assert abs(got - certified_mean) <= RELATIVE_TOLERANCE * abs(certified_mean)


@pytest.mark.parametrize("data,certified_mean,certified_sd,expected_n", STRD_CASES)
def test_sample_sd_matches_nist_strd_certified_value(data, certified_mean, certified_sd, expected_n):
    got = sample_sd(data)
    assert abs(got - certified_sd) <= RELATIVE_TOLERANCE * abs(certified_sd)


@pytest.mark.parametrize("data,certified_mean,certified_sd,expected_n", STRD_CASES)
def test_compute_descriptive_stats_matches_certified_values_and_is_provenance_stamped(
    data, certified_mean, certified_sd, expected_n
):
    result = compute_descriptive_stats(data)
    assert result.value.n == expected_n
    assert abs(result.value.mean - certified_mean) <= RELATIVE_TOLERANCE * abs(certified_mean)
    assert abs(result.value.sd - certified_sd) <= RELATIVE_TOLERANCE * abs(certified_sd)
    assert result.provenance.method
    assert result.provenance.input_hash


# Hand-computed fixture (StRD certifies no median/IQR/min/max):
# sorted = [1, 2, 3, 4, 5, 6, 7, 8], n=8 (even)
# median (NIST §1.3.5.1, n even): (Y_(n/2) + Y_(n/2+1))/2 = (Y4+Y5)/2 = (4+5)/2 = 4.5
# Q1 (linear-interp percentile, 25th): position = 0.25*(8-1) = 1.75 (0-indexed)
#   -> between sorted[1]=2 and sorted[2]=3: 2 + 0.75*(3-2) = 2.75
# Q3 (75th): position = 0.75*7 = 5.25 -> between sorted[5]=6 and sorted[6]=7: 6 + 0.25*(7-6) = 6.25
# IQR = 6.25 - 2.75 = 3.5
HAND_FIXTURE = [8, 3, 1, 6, 4, 7, 2, 5]  # deliberately unsorted


def test_median_matches_hand_computed_fixture():
    assert median(HAND_FIXTURE) == pytest.approx(4.5)


def test_quartiles_and_iqr_match_hand_computed_fixture():
    q1, q3 = quartiles(HAND_FIXTURE)
    assert q1 == pytest.approx(2.75)
    assert q3 == pytest.approx(6.25)
    assert iqr(HAND_FIXTURE) == pytest.approx(3.5)


def test_compute_descriptive_stats_min_max_n_on_hand_fixture():
    result = compute_descriptive_stats(HAND_FIXTURE).value
    assert result.n == 8
    assert result.min == 1
    assert result.max == 8
    assert result.median == pytest.approx(4.5)
    assert result.iqr == pytest.approx(3.5)


def test_sample_sd_requires_at_least_two_observations():
    with pytest.raises(ValueError):
        sample_sd([1.0])


def test_compute_descriptive_stats_round_trips_through_json():
    from sigma_engine.provenance import Computed
    from sigma_engine.stats.descriptive import DescriptiveStats

    result = compute_descriptive_stats(HAND_FIXTURE)
    dumped = result.model_dump(mode="json")
    reloaded = Computed[DescriptiveStats].model_validate(dumped)
    assert reloaded == result
