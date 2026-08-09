"""Tests for stats/hypothesis_runner.py: route+compute in one call, the
refuse-never-computes contract, and EXIT-13's both-sides-of-alpha
behavior end to end through run_hypothesis (dispatch + the
question_intent default)."""

import pytest

from sigma_engine.stats.hypothesis_common import GroupInput, HypothesisQuestion
from sigma_engine.stats.hypothesis_runner import run_hypothesis

NIST_PROCESS_1_OLD = [32, 37, 35, 28, 41, 44, 35, 31, 34, 38, 42]
NIST_PROCESS_2_NEW = [36, 31, 30, 31, 34, 36, 29, 32, 31]

ANOVA_SIGNIFICANT_GROUPS = [
    GroupInput(label="Level 1", values=[6.9, 5.4, 5.8, 4.6, 4.0]),
    GroupInput(label="Level 2", values=[8.3, 6.8, 7.8, 9.2, 6.5]),
    GroupInput(label="Level 3", values=[8.0, 10.5, 8.1, 6.9, 9.3]),
]
ANOVA_NOT_SIGNIFICANT_GROUPS = [
    GroupInput(label="A", values=[10.0, 10.1, 9.9, 10.05]),
    GroupInput(label="B", values=[10.02, 9.98, 10.03, 10.0]),
    GroupInput(label="C", values=[9.95, 10.05, 10.0, 10.01]),
]


def test_run_hypothesis_happy_welch_path():
    q = HypothesisQuestion(
        question_text="Is process 2 faster than process 1?", comparison_type="two_independent",
        groups=[GroupInput(label="Process 1", values=NIST_PROCESS_1_OLD), GroupInput(label="Process 2", values=NIST_PROCESS_2_NEW)],
    )
    r = run_hypothesis(q)
    assert r.refused is False
    assert r.routing.route == "welch_two_sample_t"
    assert r.result is not None
    assert r.result.value.statistic == pytest.approx(2.2694, abs=1e-4)


def test_run_hypothesis_exit06_refusal_never_computes():
    q = HypothesisQuestion(
        question_text="tiny groups", comparison_type="two_independent",
        groups=[GroupInput(label="A", values=[1, 2, 3]), GroupInput(label="B", values=[4, 5, 6])],
    )
    r = run_hypothesis(q)
    assert r.refused is True
    assert r.result is None
    assert r.routing.exit.exit_id == "EXIT-06"
    assert r.routing.route is None


def test_run_hypothesis_exit15_never_computes_anything():
    q = HypothesisQuestion(question_text="does x relate to y?", comparison_type="relationship_continuous")
    r = run_hypothesis(q)
    assert r.refused is True
    assert r.result is None
    assert r.routing.exit.exit_id == "EXIT-15"


# --- EXIT-13 both sides of alpha, end to end --------------------------------


def test_exit13_attaches_end_to_end_when_anova_is_significant_default_intent():
    q = HypothesisQuestion(question_text="do the 3 temperatures differ?", comparison_type="multi_group", groups=ANOVA_SIGNIFICANT_GROUPS)
    r = run_hypothesis(q)
    assert r.refused is False
    assert r.result.value.significant is True
    assert r.result.value.p_value < 0.05
    assert r.result.value.exit13 is not None
    assert r.result.value.exit13.exit_id == "EXIT-13"


def test_exit13_absent_end_to_end_when_anova_is_not_significant():
    q = HypothesisQuestion(question_text="do groups A/B/C differ?", comparison_type="multi_group", groups=ANOVA_NOT_SIGNIFICANT_GROUPS)
    r = run_hypothesis(q)
    assert r.refused is False
    assert r.result.value.significant is False
    assert r.result.value.p_value >= 0.05
    assert r.result.value.exit13 is None


def test_exit13_absent_when_significant_but_question_declared_omnibus():
    q = HypothesisQuestion(
        question_text="does any group differ?", comparison_type="multi_group", groups=ANOVA_SIGNIFICANT_GROUPS,
        question_intent="omnibus_any_group_differs",
    )
    r = run_hypothesis(q)
    assert r.result.value.significant is True
    assert r.result.value.exit13 is None  # matrix §4a round-2: omnibus question, no exit needed


def test_exit13_present_when_significant_and_question_declared_which_groups_differ():
    q = HypothesisQuestion(
        question_text="which temperature is different?", comparison_type="multi_group", groups=ANOVA_SIGNIFICANT_GROUPS,
        question_intent="which_groups_differ",
    )
    r = run_hypothesis(q)
    assert r.result.value.exit13 is not None


# --- Dispatch coverage: every non-exiting route reachable via run_hypothesis ---


def test_run_hypothesis_dispatches_paired_t():
    # Smoothly-varying diffs, deliberately not the lumpy 3-distinct-value
    # PAIRED_BEFORE/AFTER fixture used elsewhere for the hand-computed t
    # value -- that one triggers the switch's advisory-normality disjunct
    # (verified separately), which is not what this dispatch test checks.
    q = HypothesisQuestion(
        question_text="before vs after?", comparison_type="paired",
        paired_before=[10.0, 12.1, 8.9, 11.3, 9.8, 13.2, 7.6, 12.4], paired_after=[8.0, 9.2, 7.1, 9.4, 7.9, 10.3, 6.8, 9.1],
    )
    r = run_hypothesis(q)
    assert r.routing.route == "paired_t"
    assert r.result.value.test_name == "paired_t"


def test_run_hypothesis_dispatches_one_sample_t():
    q = HypothesisQuestion(question_text="vs target?", comparison_type="one_sample_vs_target", sample=[50, 48, 44, 56, 61, 52, 53, 55, 67, 51], target=50)
    r = run_hypothesis(q)
    assert r.routing.route == "one_sample_t"
    assert r.result.value.statistic == pytest.approx(1.782, abs=1e-3)


def test_run_hypothesis_dispatches_mann_whitney():
    q = HypothesisQuestion(
        question_text="ordinal comparison", comparison_type="two_independent", declared_data_type="ordinal",
        groups=[GroupInput(label="A", values=[1, 2, 3, 4, 5, 6]), GroupInput(label="B", values=[7, 8, 9, 10, 11, 12])],
    )
    r = run_hypothesis(q)
    assert r.routing.route == "mann_whitney_u"
    assert r.result.value.test_name == "mann_whitney_u"


def test_run_hypothesis_dispatches_wilcoxon_via_paired_switch():
    q = HypothesisQuestion(
        question_text="ordinal paired comparison", comparison_type="paired", declared_data_type="ordinal",
        paired_before=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], paired_after=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    )
    r = run_hypothesis(q)
    assert r.routing.route == "wilcoxon_signed_rank"
    assert r.result.value.test_name == "wilcoxon_signed_rank"


def test_run_hypothesis_dispatches_chi_square():
    q = HypothesisQuestion(question_text="associated?", comparison_type="association_categorical", contingency_table=[[10, 20], [30, 15]])
    r = run_hypothesis(q)
    assert r.routing.route == "chi_square_independence"


def test_run_hypothesis_dispatches_two_proportion_z():
    q = HypothesisQuestion(
        question_text="different rates?", comparison_type="proportions",
        groups=[GroupInput(label="A", successes=40, n=100), GroupInput(label="B", successes=25, n=100)],
    )
    r = run_hypothesis(q)
    assert r.routing.route == "two_proportion_z"


def test_run_hypothesis_dispatches_one_proportion():
    q = HypothesisQuestion(question_text="meets target?", comparison_type="proportions", groups=[GroupInput(label="s", successes=26, n=200)], target=0.10)
    r = run_hypothesis(q)
    assert r.routing.route == "one_proportion"


# --- Golden pins (matrix golden-coverage rule; evals/goldens/golden-id-map
# greps these literal ids into their unit-test homes) -----------------------


def test_G_hyp_05_nonparametric_fallback_route_fires_at_the_documented_trigger():
    """G-hyp-05 golden (matrix IV.B.2, nonparametric fallbacks): the
    documented switch rule (PLAN §4.1 / §4a) -- per-group n <
    HYP_SWITCH_MAX_GROUP_N (15) AND declared ordinal -- actually ROUTES to
    Mann-Whitney, names why, and computes it. Reference values hand-checked
    on two fully separated ordinal samples (no ties across groups):
      old=[1..8], new=[9..16] -> every old value ranks below every new one.
      R_old = 1+2+...+8 = 36; U_old = R_old - n1(n1+1)/2 = 36 - 36 = 0.
      Exact two-sided p = 2 * P(U <= 0) = 2 * 1/C(16,8) = 2/12870
        = 0.0001554001554... (one arrangement of 12870 puts all of `old`
        below all of `new`)."""
    q = HypothesisQuestion(
        question_text="Did the reworked form change the error scores?",
        comparison_type="two_independent", declared_data_type="ordinal",
        groups=[
            GroupInput(label="old", values=[1, 2, 3, 4, 5, 6, 7, 8]),
            GroupInput(label="new", values=[9, 10, 11, 12, 13, 14, 15, 16]),
        ],
    )
    r = run_hypothesis(q)
    assert r.refused is False
    assert r.routing.route == "mann_whitney_u"
    assert r.routing.recommend_nonparametric is True
    assert "declared ordinal" in r.routing.switch_reason  # never a silent swap
    assert "n=8 < 15" in r.routing.switch_reason
    v = r.result.value
    assert v.test_name == "mann_whitney_u"
    assert v.statistic == pytest.approx(0.0)
    assert v.p_value == pytest.approx(2 / 12870, abs=1e-15)
    assert v.significant is True


def test_G_hyp_07_one_proportion_vs_target_hand_checked_binomial():
    """G-hyp-07 golden (matrix §5a A-1 / IASSC 3.5.7, one-proportion vs
    target): the proportions route with one sample + a target runs the
    exact binomial test. Reference values hand-checked with binomial
    coefficients at p0 = 0.5 (symmetric, so the two-sided p doubles one
    tail exactly):
      x=13, n=20, phat = 0.65 exactly.
      P(X >= 13) = (C(20,13)+...+C(20,20))/2^20
        = (77520+38760+15504+4845+1140+190+20+1)/1048576 = 137980/1048576.
      two-sided p = 2 * 137980/1048576 = 275960/1048576
        = 0.26317596435546875 exactly (dyadic rational -- exact in float).
      Floor check (matrix §4a EXIT-06): n*phat = 13 >= 5, n*(1-phat) = 7 >= 5."""
    q = HypothesisQuestion(
        question_text="Is the first-pass approval rate different from the 50% target?",
        comparison_type="proportions",
        groups=[GroupInput(label="audited orders", successes=13, n=20)], target=0.5,
    )
    r = run_hypothesis(q)
    assert r.refused is False
    assert r.routing.route == "one_proportion"
    v = r.result.value
    assert v.test_name == "one_proportion"
    assert v.statistic == pytest.approx(0.65)
    assert v.p_value == 275960 / 1048576  # exact: scipy's two-sided sum lands on the same dyadic rational
    assert v.significant is False  # 0.263 > alpha 0.05
    assert v.risk_difference == pytest.approx(0.15)
