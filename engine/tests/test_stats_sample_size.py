"""Tests for stats/sample_size.py: I-MR rule of thumb, the two margin-of-
error calculators against hand-computable (textbook) fixtures, and the
bias/convenience-sample warning strings (rubric R-MEA-05 Pass #5)."""

import math

import pytest

from sigma_engine.stats.sample_size import (
    imr_baseline_rule_of_thumb,
    sample_size_for_mean,
    sample_size_for_proportion,
    sampling_bias_warnings,
)


def test_imr_rule_of_thumb_is_25_to_30_and_states_convention_not_law():
    result = imr_baseline_rule_of_thumb()
    assert result.minimum_n == 25
    assert result.recommended_n == 30
    assert "convention" in result.rationale.lower()
    assert "not a derived law" in result.rationale or "not a derived formula" in result.rationale


def test_sample_size_for_mean_hand_computable_fixture():
    """Textbook z~=1.96 at 95%: n=(1.96*10/3)^2 ~= 42.68 -> ceil 43."""
    result = sample_size_for_mean(planning_sd=10.0, margin_of_error=3.0, confidence_level=0.95)
    assert result.value.z == pytest.approx(1.959963985, abs=1e-6)
    assert result.value.n_exact == pytest.approx((1.96 * 10 / 3) ** 2, abs=0.01)
    assert result.value.n == 43
    assert "43" in result.value.plain_english
    assert result.provenance.method


def test_sample_size_for_mean_rounds_up_never_down():
    """n is always math.ceil(n_exact) -- never a plain round(), which would
    under-shoot the stated margin of error about half the time."""
    result = sample_size_for_mean(planning_sd=4.5, margin_of_error=1.3, confidence_level=0.90)
    assert result.value.n_exact % 1 != 0  # a genuinely fractional case, not a lucky whole number
    assert result.value.n == math.ceil(result.value.n_exact)


def test_sample_size_for_mean_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        sample_size_for_mean(planning_sd=0.0, margin_of_error=1.0)
    with pytest.raises(ValueError):
        sample_size_for_mean(planning_sd=1.0, margin_of_error=0.0)


def test_sample_size_for_proportion_classic_385_fixture():
    """The textbook-famous case: p=0.5 (max variance, no prior estimate),
    E=5%, 95% confidence -> n=385 (appears in essentially every intro-stats
    sample-size table; hand check: 1.96^2*0.25/0.0025 = 3.8416*0.25/0.0025
    = 0.9604/0.0025 = 384.16 -> ceil 385)."""
    result = sample_size_for_proportion(planning_p=0.5, margin_of_error=0.05, confidence_level=0.95)
    assert result.value.n == 385
    assert "385" in result.value.plain_english


def test_sample_size_for_proportion_rejects_p_outside_open_unit_interval():
    with pytest.raises(ValueError):
        sample_size_for_proportion(planning_p=0.0, margin_of_error=0.05)
    with pytest.raises(ValueError):
        sample_size_for_proportion(planning_p=1.0, margin_of_error=0.05)


def test_higher_confidence_requires_more_n():
    lo = sample_size_for_mean(planning_sd=10.0, margin_of_error=3.0, confidence_level=0.90)
    hi = sample_size_for_mean(planning_sd=10.0, margin_of_error=3.0, confidence_level=0.99)
    assert hi.value.n > lo.value.n


def test_sampling_bias_warnings_fire_only_for_flagged_conditions():
    assert sampling_bias_warnings() == []
    warnings = sampling_bias_warnings(is_convenience_sample=True, short_collection_window=True)
    assert len(warnings) == 2
    assert any("convenience sample" in w for w in warnings)
    assert any("collection window" in w for w in warnings)


def test_sampling_bias_warnings_single_shift_and_operator():
    warnings = sampling_bias_warnings(single_shift_only=True, single_operator_only=True)
    assert len(warnings) == 2
    assert any("shift" in w for w in warnings)
    assert any("operator" in w for w in warnings)
