"""Tests for stats/normality.py: the Anderson-Darling wrapper itself is
scipy's own certified implementation (not re-derived here -- see module
docstring), so these tests verify OUR contract: n-aware advisory
bucketing, the frozen p<0.05 concern threshold and n<15 too-few-to-judge
floor (both named constants), the p-band never claims false precision,
and normality is never a silent gate (a value is always returned).
"""

import numpy as np
import pytest

from sigma_engine.stats.normality import assess_normality, p_band

# Fixed-seed synthetic data: deterministic and reproducible (same seed ->
# same floats on any machine, numpy's Generator/PCG64 is a documented,
# stable algorithm) -- these assert a *behavioral* property (concern
# fires on skewed data), not a certified numeric value.
RNG = np.random.default_rng(2026)
CLEARLY_NORMAL = list(RNG.normal(loc=50, scale=2, size=100))
CLEARLY_SKEWED = list(RNG.exponential(scale=3.0, size=100))


def test_too_few_to_judge_below_n15_regardless_of_shape():
    for data in (CLEARLY_NORMAL[:14], CLEARLY_SKEWED[:14]):
        result = assess_normality(data).value
        assert result.advisory == "too_few_to_judge"


def test_at_n15_advisory_is_no_longer_automatically_too_few():
    result = assess_normality(CLEARLY_NORMAL[:15]).value
    assert result.n == 15
    assert result.advisory in ("no_concern", "concern")  # never too_few_to_judge at n=15


def test_no_concern_on_clearly_normal_data():
    result = assess_normality(CLEARLY_NORMAL).value
    assert result.advisory == "no_concern"
    assert result.approx_pvalue >= 0.05


def test_concern_on_clearly_skewed_data():
    result = assess_normality(CLEARLY_SKEWED).value
    assert result.advisory == "concern"
    assert result.approx_pvalue < 0.05


def test_concern_threshold_is_exactly_the_frozen_alpha():
    """matrix §4a EXIT-05: concern iff Anderson-Darling p < 0.05."""
    from sigma_engine.stats.constants import NORMALITY_CONCERN_ALPHA

    assert NORMALITY_CONCERN_ALPHA == 0.05
    result = assess_normality(CLEARLY_SKEWED).value
    assert (result.approx_pvalue < NORMALITY_CONCERN_ALPHA) == (result.advisory == "concern" if result.n >= 15 else False)


def test_p_band_never_claims_false_precision():
    assert p_band(0.20) == "p >= 0.15"
    assert p_band(0.15) == "p >= 0.15"
    assert p_band(0.005) == "p <= 0.01"  # clipped table floor
    assert p_band(0.01) == "p <= 0.01"
    assert p_band(0.03) == "p ~= 0.030"
    assert p_band(None) == "not computed"


def test_statistic_is_none_only_below_the_numerical_floor_not_the_judgment_floor():
    """Never a silent gate: even n=5 (< 15, too_few_to_judge) still gets a
    real statistic if scipy can compute one -- only n<3 withholds it."""
    tiny_but_computable = assess_normality(CLEARLY_NORMAL[:5]).value
    assert tiny_but_computable.advisory == "too_few_to_judge"
    assert tiny_but_computable.statistic is not None

    too_tiny = assess_normality(CLEARLY_NORMAL[:2]).value
    assert too_tiny.statistic is None
    assert too_tiny.advisory == "too_few_to_judge"


def test_result_is_provenance_stamped():
    result = assess_normality(CLEARLY_NORMAL)
    assert result.provenance.method
    assert result.provenance.input_hash
