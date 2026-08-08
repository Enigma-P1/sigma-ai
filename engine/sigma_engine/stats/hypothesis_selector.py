"""stats/hypothesis_selector.py -- T-17's routing tree (matrix §4a /
rubric R-ANA-04's "printed decision path"): input = the question structure
-> output = a RoutingDecision carrying the chosen route, the printed
decision path (one DecisionNode per branch taken), and any EXIT raised
instead. Every §4a exit detectable from the inputs is checked here, in a
fixed order, and every check is unit-tested (see
tests/test_stats_hypothesis_selector.py).

Order of checks (fixed, so the printed decision path is reproducible):
  1. EXIT-12 (multiplicity) -- a study-design integrity check, ahead of
     any route-specific math.
  2. EXIT-11 (rate/defect-count data) -- no v1 route carries this honestly,
     checked before any route-specific branching.
  3. EXIT-08 (repeated measures) -- a declared design mismatch, same tier.
  4. Route on comparison_type: relationship_continuous -> EXIT-15 outright;
     association_categorical -> the chi-square path (EXIT-07); proportions
     -> the proportions path; everything else -> the continuous/ordinal
     path (EXIT-09, the nonparametric switch, EXIT-14, EXIT-06).

The nonparametric switch (task brief / PLAN §4.1): the engine recommends,
and actually ROUTES to, the rank test when per-group n < HYP_SWITCH_MAX_
GROUP_N and (declared ordinal OR a user-flagged shape concern OR an
advisory normality concern on that group) -- for two_independent, paired,
and one_sample_vs_target only, because those are the routes with a shipped
rank-based alternate (Mann-Whitney, Wilcoxon signed-rank). multi_group has
no shipped nonparametric alternate (Kruskal-Wallis is v1.1, matrix A-3) --
the analogous 3+-group condition raises EXIT-14 instead of switching.
This is a real routing choice, not a coin flip hidden from the caller: the
switch_reason field and a DecisionNode both name exactly why, which is
what "the engine never silently swaps" (task brief) means here -- never
SILENT, not never-swapping. See RoutingDecision.switch_reason.
"""

from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel, ConfigDict

from .constants import (
    CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR,
    CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION,
    CHI_SQUARE_COCHRAN_MIN_EXPECTED,
    HYP_EXIT14_MAX_GROUP_N_FOR_NORMALITY_CONCERN,
    HYP_MAX_PRIMARY_COMPARISONS,
    HYP_MIN_GROUPS_ANOVA,
    HYP_MIN_N_ONE_SAMPLE_T,
    HYP_MIN_N_PER_GROUP_ANOVA,
    HYP_MIN_N_PER_GROUP_MANN_WHITNEY,
    HYP_MIN_N_WELCH_T,
    HYP_MIN_NONZERO_DIFFS_WILCOXON,
    HYP_MIN_PAIRS_PAIRED_T,
    HYP_PROPORTION_MIN_N_PHAT,
    HYP_SWITCH_MAX_GROUP_N,
)
from .hypothesis_categorical import cochran_preflight
from .hypothesis_common import HypothesisQuestion, RouteName, advisory_normality_concern, check_autocorrelation, group_successes_n, nonzero_diff_count


class DecisionNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str
    answer: str
    branch: str


class HypothesisExitPayload(BaseModel):
    """One entry per matrix §4 registry row this selector can raise.
    EXIT-13 is never produced here -- see hypothesis_common.RouteName's
    module note; it is a post-hoc annotation on a successful ANOVA result."""

    model_config = ConfigDict(frozen=True)

    exit_id: str
    message: str
    routes_to: str
    detail: str


class RoutingDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str
    comparison_type: str
    decision_path: tuple[DecisionNode, ...]
    route: RouteName | None  # None iff an exit fired instead
    exit: HypothesisExitPayload | None
    switch_reason: str | None
    recommend_nonparametric: bool


# --- matrix §4 registry: message + routes_to, one place, cited once --------

_EXIT_REGISTRY: dict[str, tuple[str, str]] = {
    "EXIT-06": (
        "Sample size below the stated floor for the routed test -- a named refusal, not an underpowered "
        "p-value shown as if it were trustworthy.",
        "Collect more data (T-11 sample-size calculator), or route to the applicable rank-based fallback if that "
        "clears its own floor.",
    ),
    "EXIT-07": (
        "This table is too sparse for a trustworthy chi-square (Cochran's rule: fewer than 80% of cells have "
        "expected count >= 5, or some cell's expected count is below 1).",
        "Collect more data, or honestly merge categories; otherwise a human expert.",
    ),
    "EXIT-08": (
        "More than one related measurement per unit beyond a paired (before/after) design -- this is repeated-"
        "measures territory, beyond what the paired case here carries.",
        "A human expert / Black Belt; the advisor can explain the study structure.",
    ),
    "EXIT-09": (
        "The data shows material, statistically-significant lag-1 autocorrelation -- time-dependence that "
        "violates this test's (and an I-MR chart's) independence assumption; a standard result here would mislead.",
        "Time-ordered analysis guidance; a human expert.",
    ),
    "EXIT-11": (
        "This is rate-with-exposure or defects-per-unit/area (Poisson-family) data -- defectives are pass/fail "
        "units, defects are counts on units, and no v1 route carries counts honestly.",
        "c/u chart family (T-29, v1.1) for monitoring; a human expert for rate comparisons; DPMO/yield (T-10) "
        "remains available as a descriptive summary.",
    ),
    "EXIT-12": (
        "More than one primary comparison was declared, or more tests have been run than were declared.",
        "Declare one pre-declared primary comparison, or consult a human expert about a multiplicity correction.",
    ),
    "EXIT-14": (
        "3+ groups with data declared ordinal, or a normality concern in a group with n<20 -- Kruskal-Wallis "
        "territory the shipped tests don't cover honestly in v1.",
        "Kruskal-Wallis route ships at v1.1; a human expert meanwhile.",
    ),
    "EXIT-15": (
        "This is a continuous-x vs continuous-y relationship question (correlation/regression), not a group "
        "comparison -- quantified correlation/regression is deferred by name in v1.",
        "T-30 (v1.1); the advisor can explain correlation vs causation meanwhile.",
    ),
}


def _exit(exit_id: str, detail: str) -> HypothesisExitPayload:
    message, routes_to = _EXIT_REGISTRY[exit_id]
    return HypothesisExitPayload(exit_id=exit_id, message=message, routes_to=routes_to, detail=detail)


def _decision(
    q: HypothesisQuestion, path: list[DecisionNode], *,
    route: RouteName | None = None, exit_payload: HypothesisExitPayload | None = None,
    switch_reason: str | None = None,
) -> RoutingDecision:
    return RoutingDecision(
        question=q.question_text, comparison_type=q.comparison_type, decision_path=tuple(path),
        route=route, exit=exit_payload, switch_reason=switch_reason, recommend_nonparametric=switch_reason is not None,
    )


# --- Universal pre-checks (run before any route-specific branching) --------


def _check_exit12(q: HypothesisQuestion) -> tuple[DecisionNode, HypothesisExitPayload | None]:
    fires = q.comparisons_declared > HYP_MAX_PRIMARY_COMPARISONS or q.tests_run_including_this_one > q.comparisons_declared
    detail = f"comparisons_declared={q.comparisons_declared}, tests_run_including_this_one={q.tests_run_including_this_one}"
    node = DecisionNode(
        question="Is exactly one primary comparison declared, and does the test count stay within it?",
        answer=detail, branch="EXIT-12 -- multiplicity" if fires else "one pre-declared primary comparison -- continue",
    )
    return node, (_exit("EXIT-12", detail) if fires else None)


def _check_exit11(q: HypothesisQuestion) -> tuple[DecisionNode, HypothesisExitPayload | None]:
    fires = q.declared_data_type == "count_rate"
    node = DecisionNode(
        question="Is the outcome a rate-with-exposure or a defect count per unit/area?",
        answer=f"declared_data_type={q.declared_data_type!r}",
        branch="EXIT-11 -- no v1 route carries count/rate data honestly" if fires else "not count/rate data -- continue",
    )
    return node, (_exit("EXIT-11", f"declared_data_type={q.declared_data_type!r}") if fires else None)


def _check_exit08(q: HypothesisQuestion) -> tuple[DecisionNode, HypothesisExitPayload | None]:
    fires = q.measurements_per_unit > 2
    node = DecisionNode(
        question="How many related measurements per unit are there?",
        answer=f"measurements_per_unit={q.measurements_per_unit}",
        branch="EXIT-08 -- repeated measures beyond the paired design" if fires else "at most paired (<=2) -- continue",
    )
    return node, (_exit("EXIT-08", f"measurements_per_unit={q.measurements_per_unit}") if fires else None)


def _check_exit09(label: str, data: Sequence[float]) -> tuple[DecisionNode, HypothesisExitPayload | None]:
    check = check_autocorrelation(label, data)
    if check.r1 is None:
        answer = f"{label}: autocorrelation not computable (n={check.n} or constant data)"
    else:
        answer = f"{label}: r1={check.r1:.3f}, threshold=2/sqrt(n)={check.significance_threshold:.3f}, |r1|>=0.3 material={check.is_material}"
    node = DecisionNode(
        question=f"Is {label} time-ordered with material, statistically-significant lag-1 autocorrelation?",
        answer=answer, branch="EXIT-09 -- autocorrelated data" if check.fires_exit09 else "no material autocorrelation signal -- continue",
    )
    return node, (_exit("EXIT-09", answer) if check.fires_exit09 else None)


# --- Nonparametric switch eligibility (two_independent / paired / one_sample_vs_target only) ---


def _switch_eligible(q: HypothesisQuestion, label: str, values: Sequence[float] | None, n: int) -> tuple[bool, str]:
    """One group/sample's switch eligibility (PLAN §4.1 / task brief,
    literally as stated): per-group n < HYP_SWITCH_MAX_GROUP_N AND
    (declared ordinal OR user-flagged shape concern OR an advisory
    normality concern on that group's own values). All three disjuncts
    are checked even though, for tiny n, ordinal/shape-concern are the
    only ones that can realistically fire (advisory_normality_concern
    needs n>=3 to compute at all -- see its docstring)."""
    if n >= HYP_SWITCH_MAX_GROUP_N:
        return False, f"{label}: n={n} >= {HYP_SWITCH_MAX_GROUP_N}"
    reasons: list[str] = []
    if q.declared_data_type == "ordinal":
        reasons.append("declared ordinal")
    if q.user_shape_concern:
        reasons.append("user-flagged shape concern")
    if values is not None and advisory_normality_concern(values):
        reasons.append("advisory normality concern (Anderson-Darling p<0.05)")
    if reasons:
        return True, f"{label}: n={n} < {HYP_SWITCH_MAX_GROUP_N} and {', '.join(reasons)}"
    return False, f"{label}: n={n} < {HYP_SWITCH_MAX_GROUP_N} but no ordinal/shape/normality flag"


def _switch_check(q: HypothesisQuestion, members: Sequence[tuple[str, Sequence[float] | None, int]]) -> tuple[bool, str]:
    checked = [_switch_eligible(q, label, values, n) for label, values, n in members]
    fired = [detail for ok, detail in checked if ok]
    if fired:
        return True, "; ".join(fired)
    return False, "; ".join(detail for _, detail in checked)


# --- Route bodies, one per comparison_type ----------------------------------


def _route_multi_group(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    groups = q.groups
    n_groups = len(groups)
    path.append(DecisionNode(
        question="How many groups?", answer=str(n_groups),
        branch="3+ groups -- ANOVA family" if n_groups >= HYP_MIN_GROUPS_ANOVA else f"fewer than {HYP_MIN_GROUPS_ANOVA} groups given",
    ))

    ordinal = q.declared_data_type == "ordinal"
    concern_groups = [
        g.label for g in groups
        if g.values is not None and len(g.values) < HYP_EXIT14_MAX_GROUP_N_FOR_NORMALITY_CONCERN and advisory_normality_concern(g.values)
    ]
    fires14 = n_groups >= HYP_MIN_GROUPS_ANOVA and (ordinal or bool(concern_groups))
    detail14 = f"declared_ordinal={ordinal}; groups flagged (n<{HYP_EXIT14_MAX_GROUP_N_FOR_NORMALITY_CONCERN} + normality concern): {concern_groups}"
    path.append(DecisionNode(
        question=f"Is the data declared ordinal, or does any group show a normality concern at n<{HYP_EXIT14_MAX_GROUP_N_FOR_NORMALITY_CONCERN}?",
        answer=detail14, branch="EXIT-14 -- the shipped tests don't cover this case honestly" if fires14 else "continue to the ANOVA route",
    ))
    if fires14:
        return _decision(q, path, exit_payload=_exit("EXIT-14", detail14))

    route: RouteName = "one_way_anova"
    path.append(DecisionNode(
        question="Which test fits 3+ independent groups by default?",
        answer="one-way ANOVA (no shipped nonparametric alternate in v1 -- Kruskal-Wallis is v1.1, matrix A-3)",
        branch=f"route={route}",
    ))

    group_ns = [len(g.values or []) for g in groups]
    floor_ok = n_groups >= HYP_MIN_GROUPS_ANOVA and all(n >= HYP_MIN_N_PER_GROUP_ANOVA for n in group_ns)
    detail06 = f"{n_groups} groups (need >={HYP_MIN_GROUPS_ANOVA}); per-group n={group_ns} (need >={HYP_MIN_N_PER_GROUP_ANOVA} each)"
    path.append(DecisionNode(
        question="Does the design clear the ANOVA EXIT-06 floor?", answer=detail06,
        branch="floor cleared -- compute" if floor_ok else "EXIT-06",
    ))
    if not floor_ok:
        return _decision(q, path, exit_payload=_exit("EXIT-06", detail06))
    return _decision(q, path, route=route)


def _route_two_independent(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    groups = q.groups
    if len(groups) != 2:
        raise ValueError("two_independent requires exactly 2 groups")
    a, b = groups
    va, vb = a.values or [], b.values or []
    switch, reason = _switch_check(q, [(a.label, a.values, len(va)), (b.label, b.values, len(vb))])
    path.append(DecisionNode(
        question=f"Does either group have n<{HYP_SWITCH_MAX_GROUP_N} with a declared-ordinal, shape-concern, or advisory-normality flag?",
        answer=reason, branch="switch to the rank route (Mann-Whitney)" if switch else "use the parametric default (Welch t)",
    ))

    route: RouteName = "mann_whitney_u" if switch else "welch_two_sample_t"
    floor = HYP_MIN_N_PER_GROUP_MANN_WHITNEY if switch else HYP_MIN_N_WELCH_T
    floor_ok = len(va) >= floor and len(vb) >= floor
    path.append(DecisionNode(question="Which test fits two independent continuous/ordinal samples?", answer=route, branch=f"route={route}"))

    detail = f"{a.label} n={len(va)}, {b.label} n={len(vb)} (need >={floor} per sample)"
    path.append(DecisionNode(
        question=f"Does each sample clear the EXIT-06 floor (n>={floor} per sample)?", answer=detail,
        branch="floor cleared -- compute" if floor_ok else "EXIT-06",
    ))
    switch_reason = reason if switch else None
    if not floor_ok:
        return _decision(q, path, exit_payload=_exit("EXIT-06", detail), switch_reason=switch_reason)
    return _decision(q, path, route=route, switch_reason=switch_reason)


def _route_paired(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    a, b = q.paired_before or [], q.paired_after or []
    if len(a) != len(b) or not a:
        raise ValueError("paired requires paired_before and paired_after, equal length, at least 1 pair")
    diffs = [x - y for x, y in zip(a, b)]
    switch, reason = _switch_check(q, [("the paired difference", diffs, len(diffs))])
    path.append(DecisionNode(
        question=f"Does the paired-difference series have n<{HYP_SWITCH_MAX_GROUP_N} with a declared-ordinal, shape-concern, or advisory-normality flag?",
        answer=reason, branch="switch to the rank route (Wilcoxon signed-rank)" if switch else "use the parametric default (paired t)",
    ))

    if switch:
        route: RouteName = "wilcoxon_signed_rank"
        n_nonzero = nonzero_diff_count(diffs)
        floor_ok = n_nonzero >= HYP_MIN_NONZERO_DIFFS_WILCOXON
        detail = f"{n_nonzero} non-zero differences out of {len(diffs)} pairs (need >={HYP_MIN_NONZERO_DIFFS_WILCOXON} non-zero)"
    else:
        route = "paired_t"
        floor_ok = len(diffs) >= HYP_MIN_PAIRS_PAIRED_T
        detail = f"{len(diffs)} pairs (need >={HYP_MIN_PAIRS_PAIRED_T})"
    path.append(DecisionNode(question="Which test fits this paired design?", answer=route, branch=f"route={route}"))
    path.append(DecisionNode(
        question="Does the design clear the EXIT-06 floor for this route?", answer=detail,
        branch="floor cleared -- compute" if floor_ok else "EXIT-06",
    ))
    switch_reason = reason if switch else None
    if not floor_ok:
        return _decision(q, path, exit_payload=_exit("EXIT-06", detail), switch_reason=switch_reason)
    return _decision(q, path, route=route, switch_reason=switch_reason)


def _route_one_sample(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    sample = q.sample or []
    if q.target is None or not sample:
        raise ValueError("one_sample_vs_target requires `sample` (non-empty) and `target`")
    diffs = [x - q.target for x in sample]
    switch, reason = _switch_check(q, [("the sample", sample, len(sample))])
    path.append(DecisionNode(
        question=f"Does the sample have n<{HYP_SWITCH_MAX_GROUP_N} with a declared-ordinal, shape-concern, or advisory-normality flag?",
        answer=reason, branch="switch to the rank route (one-sample Wilcoxon)" if switch else "use the parametric default (one-sample t)",
    ))

    if switch:
        route: RouteName = "wilcoxon_signed_rank"
        n_nonzero = nonzero_diff_count(diffs)
        floor_ok = n_nonzero >= HYP_MIN_NONZERO_DIFFS_WILCOXON
        detail = f"{n_nonzero} non-zero (sample - target) differences out of {len(sample)} (need >={HYP_MIN_NONZERO_DIFFS_WILCOXON} non-zero)"
    else:
        route = "one_sample_t"
        floor_ok = len(sample) >= HYP_MIN_N_ONE_SAMPLE_T
        detail = f"n={len(sample)} (need >={HYP_MIN_N_ONE_SAMPLE_T})"
    path.append(DecisionNode(question="Which test fits a single sample against a target?", answer=route, branch=f"route={route}"))
    path.append(DecisionNode(
        question="Does the design clear the EXIT-06 floor for this route?", answer=detail,
        branch="floor cleared -- compute" if floor_ok else "EXIT-06",
    ))
    switch_reason = reason if switch else None
    if not floor_ok:
        return _decision(q, path, exit_payload=_exit("EXIT-06", detail), switch_reason=switch_reason)
    return _decision(q, path, route=route, switch_reason=switch_reason)


def _route_proportions(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    groups = q.groups
    path.append(DecisionNode(
        question="How many samples for the proportions comparison?", answer=str(len(groups)),
        branch="one-proportion vs target" if len(groups) == 1 else "two-proportion" if len(groups) == 2 else "unsupported group count",
    ))
    if len(groups) == 1:
        if q.target is None:
            raise ValueError("proportions with one group requires `target`")
        x, n = group_successes_n(groups[0])
        route: RouteName = "one_proportion"
        phat = x / n if n else 0.0
        floor_ok = n * phat >= HYP_PROPORTION_MIN_N_PHAT and n * (1 - phat) >= HYP_PROPORTION_MIN_N_PHAT
        detail = f"{groups[0].label}: n*phat={n * phat:.2f}, n*(1-phat)={n * (1 - phat):.2f} (both need >={HYP_PROPORTION_MIN_N_PHAT:g})"
    elif len(groups) == 2:
        route = "two_proportion_z"
        checks, floor_ok = [], True
        for g in groups:
            x, n = group_successes_n(g)
            phat = x / n if n else 0.0
            ok = n * phat >= HYP_PROPORTION_MIN_N_PHAT and n * (1 - phat) >= HYP_PROPORTION_MIN_N_PHAT
            floor_ok = floor_ok and ok
            checks.append(f"{g.label}: n*phat={n * phat:.2f}, n*(1-phat)={n * (1 - phat):.2f}")
        detail = "; ".join(checks) + f" (each needs >={HYP_PROPORTION_MIN_N_PHAT:g})"
    else:
        raise ValueError("proportions requires 1 group (vs target) or exactly 2 groups")

    path.append(DecisionNode(question="Which test fits this proportions comparison?", answer=route, branch=f"route={route}"))
    path.append(DecisionNode(
        question="Does each sample clear the EXIT-06 floor (n*phat>=5 and n*(1-phat)>=5)?", answer=detail,
        branch="floor cleared -- compute" if floor_ok else "EXIT-06",
    ))
    if not floor_ok:
        return _decision(q, path, exit_payload=_exit("EXIT-06", detail))
    return _decision(q, path, route=route)


def _route_chi_square(q: HypothesisQuestion, path: list[DecisionNode]) -> RoutingDecision:
    if not q.contingency_table:
        raise ValueError("association_categorical requires `contingency_table`")
    check = cochran_preflight(q.contingency_table)
    detail = (
        f"{check.fraction_at_or_above_min_expected:.0%} of cells have expected>={CHI_SQUARE_COCHRAN_MIN_EXPECTED:g} "
        f"(need >={CHI_SQUARE_COCHRAN_MIN_CELL_FRACTION:.0%}); smallest expected cell={check.min_cell_expected:.2f} "
        f"(need >={CHI_SQUARE_COCHRAN_ABSOLUTE_FLOOR:g})"
    )
    path.append(DecisionNode(question="Does the table clear Cochran's rule?", answer=detail, branch="cleared -- compute" if check.passed else "EXIT-07"))
    if not check.passed:
        return _decision(q, path, exit_payload=_exit("EXIT-07", detail))
    return _decision(q, path, route="chi_square_independence")


# --- Top-level entry point ---------------------------------------------------


def route_hypothesis(q: HypothesisQuestion) -> RoutingDecision:
    path: list[DecisionNode] = []

    for check_fn in (_check_exit12, _check_exit11, _check_exit08):
        node, exit_ = check_fn(q)
        path.append(node)
        if exit_:
            return _decision(q, path, exit_payload=exit_)

    path.append(DecisionNode(
        question="What kind of comparison is this?", answer=q.comparison_type, branch=f"the {q.comparison_type} path",
    ))

    if q.comparison_type == "relationship_continuous":
        return _decision(q, path, exit_payload=_exit("EXIT-15", "comparison_type=relationship_continuous"))
    if q.comparison_type == "association_categorical":
        return _route_chi_square(q, path)
    if q.comparison_type == "proportions":
        return _route_proportions(q, path)

    # two_independent / paired / one_sample_vs_target / multi_group share
    # the continuous/ordinal path: EXIT-09 first (on whichever series that
    # comparison_type actually tests), then the route-specific tree.
    if q.comparison_type == "multi_group":
        primary_series = [(g.label, g.values or []) for g in q.groups]
    elif q.comparison_type == "two_independent":
        primary_series = [(g.label, g.values or []) for g in q.groups[:2]]
    elif q.comparison_type == "paired":
        primary_series = [("the paired difference", [x - y for x, y in zip(q.paired_before or [], q.paired_after or [])])]
    elif q.comparison_type == "one_sample_vs_target":
        primary_series = [("the sample", q.sample or [])]
    else:
        raise ValueError(f"unknown comparison_type {q.comparison_type!r}")

    if q.time_ordered:
        for label, series in primary_series:
            node, exit_ = _check_exit09(label, series)
            path.append(node)
            if exit_:
                return _decision(q, path, exit_payload=exit_)
    else:
        path.append(DecisionNode(question="Is this data time-ordered?", answer="no (time_ordered=False)", branch="EXIT-09 not applicable -- continue"))

    if q.comparison_type == "multi_group":
        return _route_multi_group(q, path)
    if q.comparison_type == "two_independent":
        return _route_two_independent(q, path)
    if q.comparison_type == "paired":
        return _route_paired(q, path)
    return _route_one_sample(q, path)
