"""stats/hypothesis_runner.py -- T-17's /run contract: route_hypothesis()
then dispatch to the matching family function in one call, refusing with
the named EXIT when the selector raises one and never computing (let alone
storing) a result past a raised exit (rubric R-ANA-04's "exit honored"
pre-score line -- see prescore/hypothesis.py).

EXIT-13 default (documented judgment call, matrix §4a round-2 GPT
correction, same "name the reasoning, don't guess silently" standard as
stats/baseline.py's own EXIT-05 note): the frozen rule fires EXIT-13 only
when "the user's question asks which groups differ," and is explicit that
a pre-declared *omnibus* question ("does any group differ?") gets no exit.
`HypothesisQuestion.question_intent` carries that declaration, but it is
optional -- most real callers (this milestone's own curl smoke test
included) won't set it. Un-set (`None`) is treated the same as
"which_groups_differ" (one_way_anova's own `question_intent != "omnibus_
any_group_differs"` check, in hypothesis_parametric.py): the honest
default over-informs (always name the pairwise-comparison limitation on a
significant ANOVA) rather than silently under-informing when a caller
hasn't stated their intent either way -- consistent with every other
default in this engine (Welch-by-default, sigma-shift-applied-by-default)
leaning toward the more protective reading.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..provenance import Computed
from .hypothesis_categorical import chi_square_independence, one_proportion_exact, two_proportion_z
from .hypothesis_common import HypothesisQuestion, HypothesisTestResult
from .hypothesis_nonparametric import mann_whitney_u, wilcoxon_signed_rank
from .hypothesis_parametric import one_sample_t, one_way_anova, paired_t, welch_two_sample_t
from .hypothesis_selector import RoutingDecision, RouteName, route_hypothesis


class HypothesisRunResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_text: str
    routing: RoutingDecision
    result: Computed[HypothesisTestResult] | None  # None iff refused
    refused: bool


def _dispatch(route: RouteName, q: HypothesisQuestion) -> Computed[HypothesisTestResult]:
    if route == "welch_two_sample_t":
        a, b = q.groups[0], q.groups[1]
        return welch_two_sample_t(a.label, a.values or [], b.label, b.values or [])
    if route == "paired_t":
        return paired_t(q.paired_before_label, q.paired_before or [], q.paired_after_label, q.paired_after or [])
    if route == "one_sample_t":
        assert q.target is not None  # the selector's own route_hypothesis() guarantees this for this route
        return one_sample_t(q.sample_label, q.sample or [], q.target)
    if route == "one_way_anova":
        groups = [(g.label, g.values or []) for g in q.groups]
        return one_way_anova(groups, question_intent=q.question_intent)
    if route == "mann_whitney_u":
        a, b = q.groups[0], q.groups[1]
        return mann_whitney_u(a.label, a.values or [], b.label, b.values or [])
    if route == "wilcoxon_signed_rank":
        if q.paired_before is not None and q.paired_after is not None:
            diffs = [x - y for x, y in zip(q.paired_before, q.paired_after)]
            label = f"{q.paired_before_label} - {q.paired_after_label}"
        else:
            assert q.target is not None
            diffs = [x - q.target for x in (q.sample or [])]
            label = f"{q.sample_label} - target"
        return wilcoxon_signed_rank(label, diffs)
    if route == "chi_square_independence":
        assert q.contingency_table is not None
        return chi_square_independence(q.contingency_table, row_labels=q.row_labels, col_labels=q.col_labels)
    if route == "two_proportion_z":
        return two_proportion_z(q.groups[0], q.groups[1])
    if route == "one_proportion":
        assert q.target is not None
        return one_proportion_exact(q.groups[0], q.target)
    raise ValueError(f"no dispatch registered for route {route!r}")  # unreachable: route_hypothesis() only emits known RouteNames


def run_hypothesis(q: HypothesisQuestion) -> HypothesisRunResult:
    """Route + compute in one call (task brief). Refuses with the named
    EXIT when one fires -- `result` stays None, `refused` is True, and no
    test math runs at all past that point (never a formally-computed-but-
    wrong answer for a case the tree knows it can't handle)."""
    decision = route_hypothesis(q)
    if decision.exit is not None or decision.route is None:
        return HypothesisRunResult(question_text=q.question_text, routing=decision, result=None, refused=True)

    result = _dispatch(decision.route, q)
    return HypothesisRunResult(question_text=q.question_text, routing=decision, result=result, refused=False)
