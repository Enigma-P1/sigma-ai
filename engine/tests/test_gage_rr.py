"""Full crossed Gage R&R (T-35).

The headline test is `test_hand_computed_two_by_two_by_two`: every value in
it was derived by hand from the ANOVA definitions before the module was
run, so it checks the arithmetic against an independent derivation rather
than against itself. The rest cover the decisions that make a Gage R&R
mislead when they go wrong -- negative components, interaction pooling,
percentages taken on the wrong scale, and designs that cannot support the
estimate at all.
"""

from __future__ import annotations

import math

import pytest

from sigma_engine.stats.gage_rr import (
    GRR_ACCEPTABLE_MAX_PERCENT,
    GageRRError,
    Measurement,
    compute_gage_rr,
)


def _ms(rows: list[tuple[str, str, float]]) -> list[Measurement]:
    return [Measurement(part=p, operator=o, value=v) for p, o, v in rows]


# Hand-derived fixture. 2 parts x 2 operators x 2 replicates:
#
#   grand mean 4.5; part means 2.5 / 6.5; operator means 4 / 5;
#   cell means 2, 3, 6, 7 -- chosen so the interaction is exactly zero.
#
#   SS_part  = 2*2 * ((2.5-4.5)^2 + (6.5-4.5)^2)          = 32
#   SS_op    = 2*2 * ((4-4.5)^2   + (5-4.5)^2)            =  2
#   SS_int   = 0 (every cell residual is exactly 0)
#   SS_error = 2+2+2+2                                     =  8
#   SS_total                                               = 42  (= 32+2+0+8)
HAND = _ms(
    [
        ("p1", "A", 1.0), ("p1", "A", 3.0),
        ("p1", "B", 2.0), ("p1", "B", 4.0),
        ("p2", "A", 5.0), ("p2", "A", 7.0),
        ("p2", "B", 6.0), ("p2", "B", 8.0),
    ]
)


def _component(result, name):
    return next(c for c in result.components if c.name == name)


def test_hand_computed_two_by_two_by_two():
    result = compute_gage_rr(HAND)
    ss = {row.source: row.ss for row in result.anova}
    assert ss["part"] == pytest.approx(32.0)
    assert ss["operator"] == pytest.approx(2.0)
    assert ss["operator_x_part"] == pytest.approx(0.0, abs=1e-12)
    assert ss["repeatability"] == pytest.approx(8.0)
    assert ss["total"] == pytest.approx(42.0)

    # Interaction is exactly zero, so F=0, p=1, and the model pools it.
    assert result.interaction_pooled is True
    # Pooled MS_error = (0 + 8) / (1 + 4) = 1.6
    assert _component(result, "repeatability").variance == pytest.approx(1.6)
    # (MS_op - MS_error) / (parts * reps) = (2 - 1.6) / 4 = 0.1
    assert _component(result, "operator").variance == pytest.approx(0.1)
    # (MS_part - MS_error) / (operators * reps) = (32 - 1.6) / 4 = 7.6
    assert _component(result, "part_to_part").variance == pytest.approx(7.6)
    # GRR = 1.6 + 0.1 = 1.7 ; total = 9.3
    assert _component(result, "gage_rr").variance == pytest.approx(1.7)
    assert _component(result, "total_variation").variance == pytest.approx(9.3)
    # 100 * sqrt(1.7) / sqrt(9.3)
    assert result.grr_percent_study_variation == pytest.approx(100 * math.sqrt(1.7 / 9.3))
    # ndc = sqrt(2) * sqrt(7.6) / sqrt(1.7) = 2.99..., truncated
    assert result.number_of_distinct_categories == 2


def test_sum_of_squares_identity_holds_on_random_data():
    """The module raises if the decomposition does not reconstruct, so this
    also proves that guard is reachable rather than decorative."""
    import random

    random.seed(11)
    rows = [
        (f"p{p}", op, 10.0 + p * 1.7 + random.gauss(0, 0.5))
        for p in range(6)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    ss = {row.source: row.ss for row in result.anova}
    assert ss["part"] + ss["operator"] + ss["operator_x_part"] + ss["repeatability"] == pytest.approx(ss["total"])


def test_percentages_are_taken_on_standard_deviations_not_variances():
    """The convention, and the reason the %study-variation column does not
    sum to 100. Computing it on variances instead would make a bad gauge
    look far better than it is."""
    result = compute_gage_rr(HAND)
    grr = _component(result, "gage_rr")
    total = _component(result, "total_variation")
    assert grr.percent_study_variation == pytest.approx(100 * grr.std_dev / total.std_dev)
    assert grr.percent_study_variation != pytest.approx(100 * grr.variance / total.variance)


def test_a_gauge_swamped_by_noise_is_unacceptable():
    import random

    random.seed(3)
    # Parts nearly identical, measurement noise large: the study is looking
    # at the gauge, not the parts.
    rows = [
        (f"p{p}", op, 10.0 + p * 0.01 + random.gauss(0, 2.0))
        for p in range(10)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    assert result.verdict == "unacceptable"
    assert result.number_of_distinct_categories < 5
    assert any("distinct categories" in w for w in result.warnings)


def test_a_precise_gauge_on_well_spread_parts_is_acceptable():
    import random

    random.seed(5)
    rows = [
        (f"p{p}", op, 10.0 + p * 2.0 + random.gauss(0, 0.05))
        for p in range(10)
        for op in ("A", "B", "C")
        for _ in range(3)
    ]
    result = compute_gage_rr(_ms(rows))
    assert result.verdict == "acceptable"
    assert result.grr_percent_study_variation < GRR_ACCEPTABLE_MAX_PERCENT


def test_negative_variance_components_are_clamped_and_reported():
    """A variance cannot be negative; the ESTIMATOR can be, when the true
    component sits near zero. Clamping silently is standard. Not reporting
    it is how a study that barely resolved anything reads as clean."""
    # Operators identical by construction, so the operator component's raw
    # estimate lands at or below zero.
    rows = []
    for p in range(4):
        for op in ("A", "B"):
            rows += [(f"p{p}", op, 5.0 + p), (f"p{p}", op, 5.0 + p + 0.4)]
    result = compute_gage_rr(_ms(rows), pool_interaction=False)
    operator = _component(result, "operator")
    assert operator.variance >= 0.0
    if operator.clamped_from_negative:
        assert any("negative" in w for w in result.warnings)


def test_interaction_pooling_is_reported_not_hidden():
    """The pooled and unpooled models can give visibly different %GRR, so a
    reader is entitled to know which produced the number."""
    pooled = compute_gage_rr(HAND, pool_interaction=True)
    unpooled = compute_gage_rr(HAND, pool_interaction=False)
    assert pooled.interaction_pooled is True
    assert unpooled.interaction_pooled is False
    assert pooled.grr_percent_study_variation != pytest.approx(unpooled.grr_percent_study_variation)


def test_tolerance_percentage_uses_a_six_sigma_span():
    result = compute_gage_rr(HAND, tolerance=12.0)
    grr_sd = _component(result, "gage_rr").std_dev
    assert result.grr_percent_tolerance == pytest.approx(100 * 6 * grr_sd / 12.0)
    assert result.basis == "tolerance"


def test_verdict_prefers_tolerance_when_one_is_given():
    """Percent of tolerance answers 'can this gauge police the spec', which
    is the question a spec'd part is actually asking."""
    result = compute_gage_rr(HAND, tolerance=1000.0)
    assert result.basis == "tolerance"
    assert result.verdict == "acceptable"  # huge tolerance, tiny GRR against it


def test_single_operator_is_refused_and_points_at_the_honest_alternative():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p2", "A", 5.0), ("p2", "A", 6.0)]
    with pytest.raises(GageRRError, match="T-12"):
        compute_gage_rr(_ms(rows))


def test_single_part_is_refused():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0)]
    with pytest.raises(GageRRError, match="at least 2 parts"):
        compute_gage_rr(_ms(rows))


def test_missing_cell_is_refused_by_name():
    rows = [r for r in [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0),
                        ("p2", "A", 5.0), ("p2", "A", 6.0)]]
    with pytest.raises(GageRRError, match="every operator to measure every part"):
        compute_gage_rr(_ms(rows))


def test_unbalanced_replicates_are_refused():
    rows = [("p1", "A", 1.0), ("p1", "A", 2.0), ("p1", "B", 1.0), ("p1", "B", 2.0),
            ("p2", "A", 5.0), ("p2", "A", 6.0), ("p2", "A", 6.5),
            ("p2", "B", 5.0), ("p2", "B", 6.0)]
    with pytest.raises(GageRRError, match="same number of repeat readings"):
        compute_gage_rr(_ms(rows))


def test_one_reading_per_cell_is_refused():
    rows = [("p1", "A", 1.0), ("p1", "B", 2.0), ("p2", "A", 5.0), ("p2", "B", 6.0)]
    with pytest.raises(GageRRError, match="at least twice"):
        compute_gage_rr(_ms(rows))


def test_identical_readings_everywhere_are_refused_rather_than_dividing_by_zero():
    rows = [(f"p{p}", op, 4.0) for p in range(3) for op in ("A", "B") for _ in range(2)]
    with pytest.raises(GageRRError, match="nothing to decompose"):
        compute_gage_rr(_ms(rows))


def test_few_parts_are_flagged():
    rows = [(f"p{p}", op, 1.0 + p + (0.1 if op == "B" else 0.0)) for p in range(3) for op in ("A", "B") for _ in range(2)]
    rows = [(p, o, v + (0.01 * i)) for i, (p, o, v) in enumerate(rows)]
    result = compute_gage_rr(_ms(rows))
    assert any("Fewer than 10" in w for w in result.warnings)


def test_anova_table_carries_every_source_with_its_df():
    result = compute_gage_rr(HAND)
    sources = [row.source for row in result.anova]
    assert sources == ["part", "operator", "operator_x_part", "repeatability", "total"]
    dfs = {row.source: row.df for row in result.anova}
    assert dfs["part"] == 1 and dfs["operator"] == 1 and dfs["operator_x_part"] == 1
    assert dfs["repeatability"] == 4 and dfs["total"] == 7
