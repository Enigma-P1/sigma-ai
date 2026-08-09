"""Tests for stats/hypothesis_selector.py -- every §4a exit detectable
from the inputs (task brief), the nonparametric switch, and the mandated
boundary goldens: every EXIT-06 floor at n and n-1 per route, EXIT-09 at
the compound boundary, EXIT-14 trigger combinations. (EXIT-13's both-
sides-of-alpha boundary lives in test_stats_hypothesis_parametric.py,
where the ANOVA math it annotates is tested, plus one end-to-end check in
test_stats_hypothesis_runner.py.)
"""

import pytest

from sigma_engine.stats.hypothesis_common import GroupInput, HypothesisQuestion
from sigma_engine.stats.hypothesis_selector import route_hypothesis


def make_question(**kwargs) -> HypothesisQuestion:
    defaults = dict(question_text="test question", comparison_type="two_independent")
    defaults.update(kwargs)
    return HypothesisQuestion(**defaults)


def groups_of(n: int, count: int = 2, offset: float = 0.0) -> list[GroupInput]:
    return [GroupInput(label=f"g{i}", values=[float(x) + offset * i for x in range(1, n + 1)]) for i in range(count)]


# --- Happy-path routing per comparison_type ---------------------------------


def test_routes_two_independent_to_welch_by_default():
    q = make_question(comparison_type="two_independent", groups=groups_of(11, 2))
    d = route_hypothesis(q)
    assert d.route == "welch_two_sample_t"
    assert d.exit is None
    assert d.decision_path  # non-empty, printable
    assert all(n.question and n.answer and n.branch for n in d.decision_path)


def test_routes_paired_to_paired_t_by_default():
    q = make_question(comparison_type="paired", paired_before=[float(x) for x in range(1, 9)], paired_after=[float(x) - 1 for x in range(1, 9)])
    d = route_hypothesis(q)
    assert d.route == "paired_t"


def test_routes_multi_group_to_anova():
    q = make_question(comparison_type="multi_group", groups=groups_of(5, 3))
    d = route_hypothesis(q)
    assert d.route == "one_way_anova"


def test_routes_one_sample_vs_target_to_one_sample_t():
    q = make_question(comparison_type="one_sample_vs_target", sample=[float(x) for x in range(1, 9)], target=3.0)
    d = route_hypothesis(q)
    assert d.route == "one_sample_t"


def test_routes_proportions_one_group_to_one_proportion():
    q = make_question(comparison_type="proportions", groups=[GroupInput(label="s", successes=10, n=20)], target=0.5)
    d = route_hypothesis(q)
    assert d.route == "one_proportion"


def test_routes_proportions_two_groups_to_two_proportion_z():
    q = make_question(comparison_type="proportions", groups=[GroupInput(label="a", successes=10, n=20), GroupInput(label="b", successes=15, n=20)])
    d = route_hypothesis(q)
    assert d.route == "two_proportion_z"


def test_routes_association_categorical_to_chi_square():
    q = make_question(comparison_type="association_categorical", contingency_table=[[10, 20], [30, 15]])
    d = route_hypothesis(q)
    assert d.route == "chi_square_independence"


def test_relationship_continuous_always_exits_15():
    q = make_question(comparison_type="relationship_continuous")
    d = route_hypothesis(q)
    assert d.route is None
    assert d.exit.exit_id == "EXIT-15"


# --- Nonparametric switch: actually routes, not just "recommends" ----------


def test_two_independent_switches_to_mann_whitney_when_ordinal_and_small_n():
    q = make_question(comparison_type="two_independent", declared_data_type="ordinal", groups=groups_of(6, 2))
    d = route_hypothesis(q)
    assert d.route == "mann_whitney_u"
    assert d.recommend_nonparametric is True
    assert d.switch_reason is not None and "declared ordinal" in d.switch_reason


def test_two_independent_stays_welch_when_n_at_or_above_switch_ceiling():
    q = make_question(comparison_type="two_independent", declared_data_type="ordinal", groups=groups_of(15, 2))
    d = route_hypothesis(q)
    assert d.route == "welch_two_sample_t"  # n=15 is NOT < HYP_SWITCH_MAX_GROUP_N=15
    assert d.recommend_nonparametric is False


def test_paired_switches_to_wilcoxon_on_user_shape_concern():
    q = make_question(
        comparison_type="paired", user_shape_concern=True,
        paired_before=[float(x) for x in range(1, 7)], paired_after=[float(x) - 1 for x in range(1, 7)],
    )
    d = route_hypothesis(q)
    assert d.route == "wilcoxon_signed_rank"
    assert "shape concern" in d.switch_reason


def test_one_sample_switches_to_wilcoxon_on_advisory_normality_concern():
    skewed = [2.0, 2.1, 2.0, 2.05, 1.95, 2.0, 50.0]  # n=7 < 15, extreme outlier; none equal target
    q = make_question(comparison_type="one_sample_vs_target", sample=skewed, target=1.0)
    d = route_hypothesis(q)
    assert d.route == "wilcoxon_signed_rank"
    assert "normality concern" in d.switch_reason


def test_multi_group_never_switches_raises_exit14_instead():
    """No shipped nonparametric alternate for 3+ groups in v1 (Kruskal-
    Wallis is v1.1, matrix A-3) -- the analogous condition is EXIT-14, not
    a switch."""
    q = make_question(comparison_type="multi_group", declared_data_type="ordinal", groups=groups_of(6, 3))
    d = route_hypothesis(q)
    assert d.route is None
    assert d.exit.exit_id == "EXIT-14"
    assert d.recommend_nonparametric is False  # the switch machinery never applies to multi_group


# --- EXIT-06 boundary goldens: n and n-1 per route --------------------------


def test_exit06_welch_t_boundary_n8_pass_n7_fail():
    pass_q = make_question(comparison_type="two_independent", groups=groups_of(8, 2))
    fail_q = make_question(comparison_type="two_independent", groups=groups_of(7, 2))
    assert route_hypothesis(pass_q).route == "welch_two_sample_t"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_one_sample_t_boundary_n8_pass_n7_fail():
    pass_q = make_question(comparison_type="one_sample_vs_target", sample=[float(x) for x in range(1, 9)], target=0.0)
    fail_q = make_question(comparison_type="one_sample_vs_target", sample=[float(x) for x in range(1, 8)], target=0.0)
    assert route_hypothesis(pass_q).route == "one_sample_t"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_paired_t_boundary_pairs8_pass_pairs7_fail():
    pass_q = make_question(comparison_type="paired", paired_before=[float(x) for x in range(1, 9)], paired_after=[float(x) - 1 for x in range(1, 9)])
    fail_q = make_question(comparison_type="paired", paired_before=[float(x) for x in range(1, 8)], paired_after=[float(x) - 1 for x in range(1, 8)])
    assert route_hypothesis(pass_q).route == "paired_t"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_anova_per_group_n_boundary_4_pass_3_fail():
    pass_q = make_question(comparison_type="multi_group", groups=groups_of(4, 3))
    fail_q = make_question(comparison_type="multi_group", groups=groups_of(3, 3))
    assert route_hypothesis(pass_q).route == "one_way_anova"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_anova_group_count_boundary_3_pass_2_fail_even_with_ample_n():
    pass_q = make_question(comparison_type="multi_group", groups=groups_of(10, 3))
    fail_q = make_question(comparison_type="multi_group", groups=groups_of(10, 2))  # ample n, but only 2 groups
    assert route_hypothesis(pass_q).route == "one_way_anova"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_mann_whitney_boundary_n4_pass_n3_fail():
    # Force the switch via declared ordinal so the floor under test is
    # Mann-Whitney's own (n>=4), not Welch's.
    pass_q = make_question(comparison_type="two_independent", declared_data_type="ordinal", groups=groups_of(4, 2))
    fail_q = make_question(comparison_type="two_independent", declared_data_type="ordinal", groups=groups_of(3, 2))
    pass_d = route_hypothesis(pass_q)
    assert pass_d.route == "mann_whitney_u"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_wilcoxon_paired_boundary_nonzero6_pass_nonzero5_fail():
    pass_q = make_question(
        comparison_type="paired", declared_data_type="ordinal",
        paired_before=[float(x) for x in range(1, 7)], paired_after=[float(x) - 1 for x in range(1, 7)],
    )
    fail_q = make_question(
        comparison_type="paired", declared_data_type="ordinal",
        paired_before=[float(x) for x in range(1, 6)], paired_after=[float(x) - 1 for x in range(1, 6)],
    )
    pass_d = route_hypothesis(pass_q)
    assert pass_d.route == "wilcoxon_signed_rank"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_wilcoxon_one_sample_boundary_nonzero6_pass_nonzero5_fail():
    pass_q = make_question(comparison_type="one_sample_vs_target", declared_data_type="ordinal", sample=[float(x) for x in range(1, 7)], target=0.0)
    fail_q = make_question(comparison_type="one_sample_vs_target", declared_data_type="ordinal", sample=[float(x) for x in range(1, 6)], target=0.0)
    pass_d = route_hypothesis(pass_q)
    assert pass_d.route == "wilcoxon_signed_rank"
    fail_d = route_hypothesis(fail_q)
    assert fail_d.route is None and fail_d.exit.exit_id == "EXIT-06"


def test_exit06_proportions_boundary_at_exactly_5_from_below_and_above():
    # n*phat: n=20, x=5 -> 5.0 (pass boundary); x=4 -> 4.0 (fail).
    pass_low = make_question(comparison_type="proportions", groups=[GroupInput(label="s", successes=5, n=20)], target=0.5)
    fail_low = make_question(comparison_type="proportions", groups=[GroupInput(label="s", successes=4, n=20)], target=0.5)
    assert route_hypothesis(pass_low).route == "one_proportion"
    assert route_hypothesis(fail_low).exit.exit_id == "EXIT-06"
    # n*(1-phat): n=20, x=15 -> n*(1-phat)=5.0 (pass); x=16 -> 4.0 (fail).
    pass_high = make_question(comparison_type="proportions", groups=[GroupInput(label="s", successes=15, n=20)], target=0.5)
    fail_high = make_question(comparison_type="proportions", groups=[GroupInput(label="s", successes=16, n=20)], target=0.5)
    assert route_hypothesis(pass_high).route == "one_proportion"
    assert route_hypothesis(fail_high).exit.exit_id == "EXIT-06"


# --- EXIT-09 at the compound boundary, through the full selector -----------


def test_exit09_fires_through_selector_when_time_ordered_and_both_conditions_hold():
    strongly_anticorrelated = [0.0, 10.0] * 10  # n=20, r1 ~= -1: significant AND material
    q = make_question(
        comparison_type="one_sample_vs_target", time_ordered=True, sample=strongly_anticorrelated, target=5.0,
    )
    d = route_hypothesis(q)
    assert d.route is None
    assert d.exit.exit_id == "EXIT-09"


def test_exit09_does_not_fire_when_time_ordered_is_false_even_on_the_same_data():
    strongly_anticorrelated = [0.0, 10.0] * 10
    q = make_question(comparison_type="one_sample_vs_target", time_ordered=False, sample=strongly_anticorrelated, target=5.0)
    d = route_hypothesis(q)
    assert d.exit is None or d.exit.exit_id != "EXIT-09"
    assert d.route == "one_sample_t"


def test_exit09_does_not_fire_on_iid_like_data_even_when_time_ordered():
    # np.random.default_rng(42).normal(5.0, 0.3, 16).round(3) -- r1~=0.023,
    # neither significant (threshold 2/sqrt(16)=0.5) nor material (<0.3).
    iid_ish = [5.091, 4.688, 5.225, 5.282, 4.415, 4.609, 5.038, 4.905, 4.995, 4.744, 5.264, 5.233, 5.02, 5.338, 5.14, 4.742]
    q = make_question(comparison_type="one_sample_vs_target", time_ordered=True, sample=iid_ish, target=5.0)
    d = route_hypothesis(q)
    assert d.exit is None or d.exit.exit_id != "EXIT-09"


# --- EXIT-14 trigger combinations -------------------------------------------


def test_exit14_fires_on_declared_ordinal_alone():
    q = make_question(comparison_type="multi_group", declared_data_type="ordinal", groups=groups_of(10, 3))
    d = route_hypothesis(q)
    assert d.exit.exit_id == "EXIT-14"


def test_exit14_fires_on_normality_concern_alone_when_group_n_below_20():
    skewed = [1.0, 1.1, 1.0, 1.05, 0.95, 1.0, 1.1, 1.0, 40.0]  # n=9 < 20, extreme outlier -> AD concern
    clean = [10.0, 10.1, 9.9, 10.05, 9.95, 10.02, 9.98, 10.03, 10.0]
    q = make_question(
        comparison_type="multi_group",
        groups=[GroupInput(label="skewed", values=skewed), GroupInput(label="clean1", values=clean), GroupInput(label="clean2", values=clean)],
    )
    d = route_hypothesis(q)
    assert d.exit.exit_id == "EXIT-14"


def test_exit14_normality_concern_does_not_fire_at_group_n_20_even_if_skewed():
    """The n<20 gate is on group size, not on how skewed the data looks --
    a group at n=20 clears EXIT-14's normality-concern disjunct by size
    alone, regardless of shape (matrix §4a: "n < 20" is the literal gate)."""
    skewed_n20 = [1.0] * 19 + [40.0]
    clean = [10.0, 10.1, 9.9, 10.05, 9.95, 10.02, 9.98, 10.03, 10.0, 10.1] * 2
    q = make_question(
        comparison_type="multi_group",
        groups=[GroupInput(label="skewed", values=skewed_n20), GroupInput(label="clean1", values=clean), GroupInput(label="clean2", values=clean)],
    )
    d = route_hypothesis(q)
    assert d.exit is None or d.exit.exit_id != "EXIT-14"
    assert d.route == "one_way_anova"


def test_exit14_both_ordinal_and_normality_concern_together_still_one_exit():
    skewed = [1.0, 1.1, 1.0, 1.05, 0.95, 1.0, 1.1, 1.0, 40.0]
    q = make_question(
        comparison_type="multi_group", declared_data_type="ordinal",
        groups=[GroupInput(label="skewed", values=skewed), GroupInput(label="g2", values=[1, 2, 3]), GroupInput(label="g3", values=[1, 2, 3])],
    )
    d = route_hypothesis(q)
    assert d.exit.exit_id == "EXIT-14"


def test_exit14_neither_condition_routes_to_anova_normally():
    clean = [10.0, 10.1, 9.9, 10.05, 9.95, 10.02, 9.98, 10.03, 10.0, 10.1]
    q = make_question(comparison_type="multi_group", groups=[GroupInput(label=f"g{i}", values=clean) for i in range(3)])
    d = route_hypothesis(q)
    assert d.exit is None
    assert d.route == "one_way_anova"


# --- EXIT-07: Cochran's rule (chi-square sparse-cell preflight) ------------


def test_exit07_fires_on_a_sparse_contingency_table():
    q = make_question(comparison_type="association_categorical", contingency_table=[[1, 1], [1, 20]])
    d = route_hypothesis(q)
    assert d.route is None
    assert d.exit.exit_id == "EXIT-07"


def test_exit07_does_not_fire_on_an_adequate_table():
    q = make_question(comparison_type="association_categorical", contingency_table=[[10, 20], [30, 15]])
    d = route_hypothesis(q)
    assert d.exit is None
    assert d.route == "chi_square_independence"


# --- EXIT-08: repeated measures beyond the paired design -------------------


@pytest.mark.parametrize("measurements_per_unit,should_fire", [(1, False), (2, False), (3, True), (4, True)])
def test_exit08_fires_only_beyond_two_measurements_per_unit(measurements_per_unit, should_fire):
    q = make_question(comparison_type="two_independent", measurements_per_unit=measurements_per_unit, groups=groups_of(11, 2))
    d = route_hypothesis(q)
    fired = d.exit is not None and d.exit.exit_id == "EXIT-08"
    assert fired is should_fire


# --- EXIT-11: rate/defect-count data ----------------------------------------


def test_exit11_fires_on_count_rate_data_regardless_of_comparison_type():
    q = make_question(comparison_type="two_independent", declared_data_type="count_rate", groups=groups_of(11, 2))
    d = route_hypothesis(q)
    assert d.route is None
    assert d.exit.exit_id == "EXIT-11"


# --- EXIT-12: multiplicity --------------------------------------------------


def test_exit12_fires_when_more_than_one_comparison_declared():
    q = make_question(comparison_type="two_independent", comparisons_declared=2, groups=groups_of(11, 2))
    d = route_hypothesis(q)
    assert d.exit.exit_id == "EXIT-12"


def test_exit12_fires_when_tests_run_exceed_declared():
    q = make_question(comparison_type="two_independent", comparisons_declared=1, tests_run_including_this_one=2, groups=groups_of(11, 2))
    d = route_hypothesis(q)
    assert d.exit.exit_id == "EXIT-12"


def test_exit12_does_not_fire_on_one_pre_declared_primary_comparison():
    q = make_question(comparison_type="two_independent", comparisons_declared=1, tests_run_including_this_one=1, groups=groups_of(11, 2))
    d = route_hypothesis(q)
    assert d.exit is None


# --- Structural errors surface as ValueError (422 at the route layer) -----


def test_two_independent_requires_exactly_two_groups():
    q = make_question(comparison_type="two_independent", groups=groups_of(10, 3))
    with pytest.raises(ValueError):
        route_hypothesis(q)


def test_association_categorical_requires_a_contingency_table():
    q = make_question(comparison_type="association_categorical")
    with pytest.raises(ValueError):
        route_hypothesis(q)


# --- Golden pin (matrix golden-coverage rule; evals/goldens/golden-id-map
# greps this literal id into its unit-test home) ----------------------------


def test_G_hyp_06_selector_exit14_kruskal_wallis_territory_is_a_named_refusal():
    """G-hyp-06 golden (matrix IASSC 3.5.2 row: "Kruskal-Wallis | EXIT-14
    in v1 (named, honest) ... G-hyp-06 (exit case)"; §4's registry:
    "an exit case appears in ... G-hyp-06"): 3+ groups with the data
    declared ordinal is Kruskal-Wallis territory no shipped v1 test covers
    honestly -- the selector must refuse by name (EXIT-14), print the
    branch in the decision path, and route the user to v1.1/a human,
    never compute an ANOVA over ranks and present it as trustworthy."""
    q = make_question(
        comparison_type="multi_group", declared_data_type="ordinal",
        groups=[
            GroupInput(label="branch A", values=[1.0, 2.0, 2.0, 3.0, 1.0]),
            GroupInput(label="branch B", values=[2.0, 3.0, 3.0, 4.0, 2.0]),
            GroupInput(label="branch C", values=[4.0, 4.0, 5.0, 3.0, 4.0]),
        ],
    )
    d = route_hypothesis(q)
    assert d.route is None  # a raised exit never carries a route
    assert d.exit is not None
    assert d.exit.exit_id == "EXIT-14"
    assert "Kruskal-Wallis" in d.exit.message
    assert "v1.1" in d.exit.routes_to
    assert any("EXIT-14" in node.branch for node in d.decision_path)  # the printed path names the refusal
