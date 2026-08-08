"""Tests for stats/msa.py: resolution pre-check, pooled within-item SD,
repeatability% denominator selection + banded verdict (boundary goldens
at exactly 10.0/30.0), Cohen's kappa + banded verdict (boundary golden at
exactly 0.75), EXIT-02/EXIT-03 payloads (matrix §4a EXIT-02 rows).
"""

import pytest

from sigma_engine.stats.msa import (
    AttributeRating,
    ItemRepeats,
    check_resolution,
    cohens_kappa,
    compute_repeatability,
    kappa_verdict,
    pooled_within_item_sd,
    repeatability_verdict,
    run_attribute_msa,
    run_continuous_msa,
)

# --- Resolution pre-check ----------------------------------------------------

def test_resolution_passes_fine_increment_and_enough_distinct_values():
    data = [10.1, 10.2, 10.3, 10.4, 10.5, 10.6]
    result = check_resolution(data, gauge_increment=0.1, usl=20.0, lsl=0.0)  # span=20, ratio=0.005
    assert result.passed is True
    assert result.reasons == ()
    assert result.span_basis == "tolerance"


def test_resolution_fails_on_coarse_increment_relative_to_span():
    data = [10.0, 11.0, 12.0, 13.0, 14.0]  # observed spread = 4
    result = check_resolution(data, gauge_increment=1.0, usl=None, lsl=None)  # ratio = 0.25 > 0.10
    assert result.passed is False
    assert result.span_basis == "observed_spread"
    assert any("gauge increment" in r for r in result.reasons)


def test_resolution_fails_on_too_few_distinct_values():
    data = [10.0, 10.0, 10.0, 10.0, 11.0]  # only 2 distinct values
    result = check_resolution(data, gauge_increment=0.01, usl=20.0, lsl=0.0)
    assert result.passed is False
    assert any("distinct" in r for r in result.reasons)


def test_resolution_fails_on_both_criteria_at_once_and_names_both_reasons():
    data = [10.0, 10.0, 10.0]
    result = check_resolution(data, gauge_increment=5.0, usl=20.0, lsl=0.0)  # ratio=0.25 AND only 1 distinct
    assert result.passed is False
    assert len(result.reasons) == 2


def test_resolution_pre_check_short_circuits_continuous_msa_to_automatic_fail():
    # Whole-minute stopwatch on a ~3-minute process: coarse increment.
    items = [ItemRepeats(item_id=f"i{i}", readings=(3.0, 3.0)) for i in range(10)]
    result = run_continuous_msa(items, gauge_increment=1.0, usl=6.0, lsl=0.0)  # span=6, ratio=1/6=0.167>0.10
    assert result.verdict == "fail"
    assert result.resolution_check is not None and result.resolution_check.passed is False
    assert result.repeatability is None  # never computed -- automatic fail path
    assert result.exit02 is not None
    assert result.exit02.exit_id == "EXIT-02"


# --- Pooled within-item SD: formula + exclusion logging ---------------------

def test_pooled_within_item_sd_matches_hand_computation():
    # Two items, exactly 2 repeats each: s_i^2 = ((a-b)/2)^2 * 2 / 1 for n=2
    # (sample variance, ddof=1): item1 readings 10,12 -> mean 11, var=((10-11)^2+(12-11)^2)/1=2
    # item2 readings 20,22 -> mean 21, var=2. Pooled = (1*2 + 1*2)/(1+1) = 2 -> s_repeat=sqrt(2).
    items = [
        ItemRepeats(item_id="i1", readings=(10.0, 12.0)),
        ItemRepeats(item_id="i2", readings=(20.0, 22.0)),
    ]
    pooled = pooled_within_item_sd(items)
    assert pooled.s_repeat == pytest.approx(2 ** 0.5)
    assert pooled.items_used == 2
    assert pooled.items_excluded == ()


def test_pooled_within_item_sd_excludes_items_with_missing_or_invalid_repeats_and_logs_them():
    items = [
        ItemRepeats(item_id="good-1", readings=(10.0, 12.0)),
        ItemRepeats(item_id="good-2", readings=(20.0, 22.0)),
        ItemRepeats(item_id="short-on-repeats", readings=(15.0, None)),  # only 1 valid -> excluded
    ]
    pooled = pooled_within_item_sd(items)
    assert pooled.items_used == 2
    assert pooled.items_excluded == ("short-on-repeats",)
    assert "short-on-repeats" in pooled.exclusion_reasons[0]
    assert pooled.total_valid_readings == 4  # the excluded item's single valid reading isn't counted either


def test_pooled_within_item_sd_raises_when_no_item_has_enough_valid_repeats():
    items = [ItemRepeats(item_id="i1", readings=(10.0, None))]
    with pytest.raises(ValueError, match="requires >=1 item"):
        pooled_within_item_sd(items)


# --- Repeatability%: denominator selection + banded verdict -----------------

def test_denominator_is_tolerance_when_both_specs_exist():
    items = [ItemRepeats(item_id=f"i{i}", readings=(100.0 + i, 100.0 + i)) for i in range(10)]  # s_repeat = 0
    result = compute_repeatability(items, usl=110.0, lsl=90.0)
    assert result.value.denominator == "tolerance"
    assert result.value.denominator_value == pytest.approx(20.0)
    assert result.value.ev_percent == pytest.approx(0.0)
    assert result.value.verdict == "acceptable"


def test_denominator_is_study_variation_when_no_full_spec_pair_exists():
    items = [ItemRepeats(item_id=f"i{i}", readings=(100.0 + i, 100.0 + i)) for i in range(10)]
    result = compute_repeatability(items, usl=None, lsl=None)
    assert result.value.denominator == "study_variation"


@pytest.mark.parametrize("ev_percent,expected", [(0.0, "acceptable"), (10.0, "acceptable"), (10.0001, "marginal"), (30.0, "marginal"), (30.0001, "fail"), (99.0, "fail")])
def test_repeatability_verdict_boundaries_exclusive_exhaustive(ev_percent, expected):
    assert repeatability_verdict(ev_percent) == expected


def test_repeatability_golden_exactly_10_percent_is_acceptable():
    """Boundary golden (matrix §4a, round-3 lock fix): denominator solved
    so %EV lands at exactly 10.0. A single two-reading item with spread
    +/-s has s_repeat = s*sqrt(2) (sample SD, ddof=1, of {-s,+s} about 0)."""
    s = 1.0
    s_repeat = s * (2 ** 0.5)
    denom = 6 * s_repeat / 0.10  # solve so 6*s_repeat/denom*100 == 10.0 exactly
    result = compute_repeatability([ItemRepeats(item_id="only", readings=(100.0 - s, 100.0 + s))], usl=denom, lsl=0.0)
    assert result.value.ev_percent == pytest.approx(10.0, abs=1e-9)
    assert result.value.verdict == "acceptable"


def test_repeatability_golden_exactly_30_percent_is_marginal():
    """Boundary golden at exactly 30.0: same construction, target 30.0."""
    s = 1.0
    s_repeat = s * (2 ** 0.5)
    denom = 6 * s_repeat / 0.30  # solve so 6*s_repeat/denom*100 == 30.0 exactly
    result = compute_repeatability([ItemRepeats(item_id="only", readings=(100.0 - s, 100.0 + s))], usl=denom, lsl=0.0)
    assert result.value.ev_percent == pytest.approx(30.0, abs=1e-9)
    assert result.value.verdict == "marginal"


def test_repeatability_denominator_must_be_positive():
    items = [ItemRepeats(item_id="i1", readings=(1.0, 1.0))]
    with pytest.raises(ValueError, match="denominator"):
        compute_repeatability(items, usl=5.0, lsl=5.0)  # zero-width tolerance


# --- Cohen's kappa: hand-computable fixture + banded verdict ---------------

def test_cohens_kappa_matches_hand_computed_classic_example():
    # 4 categories aren't needed here (binary pass/fail); classic textbook
    # 2x2 by hand: 10 items, agree pass 6, agree fail 2, disagree 2 (1 each way).
    ratings = (
        [AttributeRating(item_id=f"pp{i}", rater_a=True, rater_b=True) for i in range(6)]
        + [AttributeRating(item_id=f"ff{i}", rater_a=False, rater_b=False) for i in range(2)]
        + [AttributeRating(item_id="pf", rater_a=True, rater_b=False)]
        + [AttributeRating(item_id="fp", rater_a=False, rater_b=True)]
    )
    result = cohens_kappa(ratings)
    # p_o = 8/10 = 0.8; a_pass=7/10=0.7, b_pass=7/10=0.7
    # p_e = 0.7*0.7 + 0.3*0.3 = 0.49+0.09=0.58; kappa=(0.8-0.58)/(1-0.58)=0.22/0.42
    assert result.value.percent_agreement == pytest.approx(80.0)
    assert result.value.p_expected == pytest.approx(0.58)
    assert result.value.kappa == pytest.approx(0.22 / 0.42, rel=1e-9)


def test_cohens_kappa_perfect_trivial_agreement_is_one_not_undefined():
    ratings = [AttributeRating(item_id=f"i{i}", rater_a=True, rater_b=True) for i in range(5)]
    result = cohens_kappa(ratings)
    assert result.value.kappa == 1.0
    assert result.value.verdict == "acceptable"


@pytest.mark.parametrize("kappa,expected", [(1.0, "acceptable"), (0.75, "acceptable"), (0.7499, "marginal"), (0.40, "marginal"), (0.3999, "fail"), (0.0, "fail")])
def test_kappa_verdict_boundaries_exclusive_exhaustive(kappa, expected):
    assert kappa_verdict(kappa) == expected


def test_kappa_golden_exactly_0_75_is_acceptable():
    """Boundary golden (matrix §4a, round-3 lock fix): construct ratings so
    kappa lands at exactly 0.75. With a_pass=b_pass=0.5 (each rater says
    "pass" exactly half the time), p_e = 0.5*0.5+0.5*0.5 = 0.5; solving
    (p_o-0.5)/(1-0.5)=0.75 needs p_o=0.875. n=16, TT=FF=7, TF=FT=1 hits
    both exactly: a_pass=(TT+TF)/16=8/16=0.5, b_pass=(TT+FT)/16=8/16=0.5,
    p_o=(TT+FF)/16=14/16=0.875 -- all integers, hand-verifiable."""
    ratings = (
        [AttributeRating(item_id=f"tt{i}", rater_a=True, rater_b=True) for i in range(7)]
        + [AttributeRating(item_id=f"ff{i}", rater_a=False, rater_b=False) for i in range(7)]
        + [AttributeRating(item_id="tf", rater_a=True, rater_b=False)]
        + [AttributeRating(item_id="ft", rater_a=False, rater_b=True)]
    )
    assert len(ratings) == 16
    result = cohens_kappa(ratings)
    assert result.value.p_expected == pytest.approx(0.5)
    assert result.value.kappa == pytest.approx(0.75, abs=1e-9)
    assert result.value.verdict == "acceptable"


def test_run_attribute_msa_fail_verdict_carries_exit02_no_caveat():
    ratings = [AttributeRating(item_id=f"i{i}", rater_a=(i % 2 == 0), rater_b=(i % 3 == 0)) for i in range(20)]
    result = run_attribute_msa(ratings)
    if result.verdict == "fail":
        assert result.exit02 is not None
    assert result.caveat is None  # attribute path never carries the repeatability-only caveat
    assert result.resolution_check is None


def test_run_continuous_msa_caveat_present_on_every_continuous_verdict():
    for readings in [(100.0, 100.0), (100.0, 130.0)]:
        items = [ItemRepeats(item_id=f"i{i}", readings=readings) for i in range(10)]
        result = run_continuous_msa(items, gauge_increment=0.1, usl=200.0, lsl=0.0)
        assert result.caveat is not None and "Repeatability-only" in result.caveat
