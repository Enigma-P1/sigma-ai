"""T-20 Before/After Proof + Remaining-Gap Check -- where the Improve
loop closes (PLAN §4.1). Composes existing engine pieces, duplicating no
math of its own: stats/baseline.py's run_baseline (side-by-side stability
+ capability, before vs after) and stats/hypothesis_runner.py's
run_hypothesis (the appropriate Tier-A test, auto-selected by n/shape --
Welch t or Mann-Whitney U on the two independent before/after windows;
v1 scope is the two-independent-samples design, matching how a pilot's
`comparison_design` (before_period or parallel_group) always yields two
windows to compare, never per-unit pairs -- a documented scope choice,
not an oversight).

Like HypothesisRunArtifact and FishboneArtifact, every Computed[...] field
here is unconditionally server-recomputed on every validate, from fields
already present on the model -- this module stays free of file I/O
(baseline.py's own "this module stays free of file I/O" contract, applied
here too). The pieces a real T-20 needs that live in OTHER saved
artifacts (the pilot's declared threshold, the charter's baseline/goal,
which verified cause is next) are not loaded here -- they are ECHOED:
the caller (the desktop, which already has generic load access to T-19/
T-18/T-15/T-03 via the existing artifact routes) copies the relevant
numbers in before saving, exactly the same soft-cross-reference contract
`linked_cause_ids` already uses everywhere in this engine (pilot_plan.py,
solution_matrix.py) -- "echoed by ref," never independently re-fetched.

**Same metric/definition/measurement-system as baseline (rubric R-IMP-03
#1) is enforced by SHAPE, not a runtime check**: `metric_ref`,
`operational_definition_ref`, and `measurement_system_ref` are each a
SINGLE field applying to both before and after -- there is no second copy
for a validator to compare against the first, so "the yardstick changed
between before and after" cannot happen by construction (the same move
pilot_plan.py's `the_one_change` vs `changes[0]` cross-check exists to
prevent is here prevented by never having two fields to diverge).

**The threshold verdict renders AS DECLARED, never reworded**: `met` /
`not_met` are the only two Literal values `ProofVerdict.threshold_verdict`
can hold -- there is no free-text verdict field a caller (or a future UI
change) could soften into ambiguous prose.
"""

from __future__ import annotations

from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..provenance import Computed, compute
from ..stats.baseline import BaselineResult, run_baseline
from ..stats.descriptive import weighted_mean
from ..stats.hypothesis_common import GroupInput, HypothesisQuestion
from ..stats.hypothesis_runner import HypothesisRunResult, run_hypothesis
from .base import ArtifactBase
from .pilot_plan import ConfounderChecklist, Direction, SuccessThreshold

# Engine convention (PLAN §6: every tool's source stated, not implied) --
# NOT a NIST/published quantity. A guardrail worsening at or beyond this
# fraction of its before-value reads as "material" for the R-IMP-03 #5
# tradeoff sentence; below it, a worsening still renders honestly but
# isn't narrated as a tradeoff. Changeable only via a logged decision
# (matches the freeze-floor's own change-log discipline, tier-a-done-
# means.md's "changes only by a logged decision" precedent).
GUARDRAIL_MATERIAL_WORSENING_FRACTION = 0.05


class DataRef(BaseModel):
    """Before/after data: a dataset-column provenance record with the raw
    values inlined (module docstring's "stays free of file I/O" contract
    -- the caller resolves a dataset ref into `values` before this
    artifact ever validates, exactly HypothesisQuestion's own contract).

    `weights`, when given, is one positive weight per value -- semantically
    the subgroup size each value was itself already averaged/proportioned
    over (e.g. a daily defective-rate value paired with that day's order
    count). Optional and independent on before vs after (rubric R-IMP-03
    #1 same-yardstick, R-IMP-04 anchor): a same-yardstick metric can still
    need pooling on one side and not the other (a fixed-size daily sample
    before the pilot, a variable-size one after). None means every value
    counts equally -- the plain, unweighted mean this engine has always
    computed (stats/descriptive.py's weighted_mean(values, None) ==
    mean(values), byte-identical)."""

    dataset_id: str | None = None
    dataset_sha256: str | None = None
    column: str | None = None
    values: list[float] = Field(min_length=2)
    weights: list[float] | None = None

    @model_validator(mode="after")
    def _weights_match_values(self) -> "DataRef":
        if self.weights is None:
            return self
        if len(self.weights) != len(self.values):
            raise ValueError(
                f"weights ({len(self.weights)}) must be the same length as values ({len(self.values)}) when given"
            )
        if any(w <= 0 for w in self.weights):
            raise ValueError("weights must all be positive -- a zero or negative subgroup size isn't a real weight")
        return self


class GuardrailInput(BaseModel):
    metric_ref: str = Field(min_length=1)
    direction: Direction
    before_value: float
    after_value: float


class GuardrailCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_ref: str
    direction: Direction
    before_value: float
    after_value: float
    pct_change: float | None  # None when before_value == 0 (no relative base to divide by)
    moved: Literal["improved", "worse", "unchanged"]
    material_worsening: bool


def compute_guardrail_report(guardrails: Sequence[GuardrailInput]) -> Computed[list[GuardrailCheck]]:
    """Direction-aware before/after compare per guardrail (rubric R-IMP-03
    #5) -- a primary win is never narrated as plain "proven" when a
    material guardrail loss accompanies it; see ProofArtifact._recompute /
    compute_verdict for where the tradeoff sentence gets built."""
    checks: list[GuardrailCheck] = []
    for g in guardrails:
        delta = g.after_value - g.before_value
        improved = delta <= 0 if g.direction == "lower_is_better" else delta >= 0
        pct_change = (delta / abs(g.before_value)) if g.before_value != 0 else None
        moved: Literal["improved", "worse", "unchanged"] = "unchanged" if delta == 0 else ("improved" if improved else "worse")
        material = moved == "worse" and pct_change is not None and abs(pct_change) >= GUARDRAIL_MATERIAL_WORSENING_FRACTION
        checks.append(GuardrailCheck(
            metric_ref=g.metric_ref, direction=g.direction, before_value=g.before_value, after_value=g.after_value,
            pct_change=pct_change, moved=moved, material_worsening=material,
        ))
    return compute(
        checks,
        method=(
            f"direction-aware before/after compare per guardrail; material_worsening = worse AND |pct_change| >= "
            f"{GUARDRAIL_MATERIAL_WORSENING_FRACTION:.0%} of the before value (engine convention, not a published "
            "quantity -- rubric R-IMP-03 #5)"
        ),
        input_data=[g.model_dump(mode="json") for g in guardrails],
    )


class RankedSolutionRef(BaseModel):
    """One T-18 ranked_fix_list entry, as much as find_next_cause needs --
    a pure, no-I/O helper input (the caller assembles this list from a
    loaded SolutionMatrixArtifact.ranked_fix_list.value.ranked)."""

    rank: int
    solution_id: str
    name: str
    linked_cause_ids: list[str]


class NextCauseRef(BaseModel):
    """The GAP BLOCK's next-cause pointer -- echoed by ref (module
    docstring), never independently re-fetched by this artifact."""

    model_config = ConfigDict(frozen=True)

    cause_id: str = Field(min_length=1)
    cause_text: str = Field(min_length=1)
    via_solution_id: str = Field(min_length=1)
    via_solution_name: str = Field(min_length=1)
    rank: int


def find_next_cause(
    ranked_solutions: Sequence[RankedSolutionRef],
    verified_cause_ids: Sequence[str],
    verified_cause_text_by_id: dict[str, str],
    piloted_cause_ids: Sequence[str],
) -> NextCauseRef | None:
    """Walk T-18's ranked_fix_list (already rank-ordered) and return the
    first linked cause that is both verified (T-15) and not yet piloted
    (not linked_cause_ids on any saved T-19 in the project) -- "the top-
    ranked not-yet-piloted verified cause" (task brief), literally. Pure
    function, no I/O: the caller (a route or the desktop) gathers these
    three inputs from the project's saved T-15/T-18/T-19 artifacts via
    the existing generic load endpoints."""
    verified, piloted = set(verified_cause_ids), set(piloted_cause_ids)
    for sol in sorted(ranked_solutions, key=lambda s: s.rank):
        for cid in sol.linked_cause_ids:
            if cid in verified and cid not in piloted:
                return NextCauseRef(
                    cause_id=cid, cause_text=verified_cause_text_by_id.get(cid, cid),
                    via_solution_id=sol.solution_id, via_solution_name=sol.name, rank=sol.rank,
                )
    return None


class GapResult(BaseModel):
    """R-IMP-04's gap arithmetic + routing, IV.C.1 operationalized:
    original gap (charter goal vs baseline), how much this fix recovered,
    how much remains, and the loop's routing decision in plain language."""

    model_config = ConfigDict(frozen=True)

    charter_baseline_value: float
    charter_goal_value: float
    after_value: float
    direction: Direction
    original_gap: float
    recovered: float
    recovered_pct: float | None  # None when original_gap == 0 (already at goal at baseline)
    remaining: float
    goal_met: bool
    next_cause_ref: NextCauseRef | None
    loop_verdict: str


def compute_gap(
    *, charter_baseline_value: float, charter_goal_value: float, after_value: float,
    direction: Direction, next_cause_ref: NextCauseRef | None,
) -> Computed[GapResult]:
    if direction == "lower_is_better":
        original_gap = charter_baseline_value - charter_goal_value
        recovered = charter_baseline_value - after_value
    else:
        original_gap = charter_goal_value - charter_baseline_value
        recovered = after_value - charter_baseline_value
    remaining = original_gap - recovered
    recovered_pct = (recovered / original_gap * 100.0) if original_gap != 0 else None
    goal_met = remaining <= 0

    if goal_met:
        loop_verdict = "Goal met -- route to Control."
    elif next_cause_ref is not None:
        pct_note = f", {recovered_pct:.0f}% of the original gap recovered" if recovered_pct is not None else ""
        loop_verdict = (
            f"Gap remains ({remaining:g}{pct_note}) -- route to the next-ranked verified cause: "
            f"{next_cause_ref.cause_text!r} (via solution {next_cause_ref.via_solution_name!r}, rank "
            f"#{next_cause_ref.rank}), one change at a time."
        )
    else:
        loop_verdict = (
            "Gap remains and no further verified, not-yet-piloted cause is available -- route back to Analyze "
            "for more cause work, or exit to a human expert (rubric R-IMP-04 #2)."
        )

    result = GapResult(
        charter_baseline_value=charter_baseline_value, charter_goal_value=charter_goal_value, after_value=after_value,
        direction=direction, original_gap=original_gap, recovered=recovered, recovered_pct=recovered_pct,
        remaining=remaining, goal_met=goal_met, next_cause_ref=next_cause_ref, loop_verdict=loop_verdict,
    )
    return compute(
        result,
        method=(
            "gap = |goal - baseline| directionally; recovered = |after - baseline| directionally; remaining = "
            "gap - recovered; goal_met = remaining <= 0 (PLAN §4.1 Improve-loop gap arithmetic, rubric R-IMP-04, "
            "BoK IV.C.1)"
        ),
        input_data={
            "charter_baseline_value": charter_baseline_value, "charter_goal_value": charter_goal_value,
            "after_value": after_value, "direction": direction,
            "next_cause_ref": next_cause_ref.model_dump(mode="json") if next_cause_ref else None,
        },
    )


CONFOUNDER_FIELDS: tuple[str, ...] = ("staffing", "season", "demand", "measurement", "other")


class ProofVerdict(BaseModel):
    """The one rendered verdict object (rubric R-IMP-03): threshold AS
    DECLARED, confounder echo, stability tempering, guardrail tradeoff --
    composed into one plain-English headline the desktop renders verbatim."""

    model_config = ConfigDict(frozen=True)

    proof_form: Literal["inferential", "descriptive"]
    threshold_verdict: Literal["met", "not_met"]
    weakened: bool
    confounder_notes: tuple[str, ...]
    stability_caveat: str | None
    guardrail_tradeoff: str | None
    headline: str


def compute_verdict(
    *, threshold_met: bool, refused: bool, confounders: ConfounderChecklist, after_stable: bool | None,
    guardrail_checks: Sequence[GuardrailCheck], metric_ref: str, threshold_value: float,
    threshold_direction: str, after_mean: float,
) -> Computed[ProofVerdict]:
    proof_form: Literal["inferential", "descriptive"] = "descriptive" if refused else "inferential"
    threshold_verdict: Literal["met", "not_met"] = "met" if threshold_met else "not_met"

    changed = [(name, getattr(confounders, name)) for name in CONFOUNDER_FIELDS if getattr(confounders, name).changed]
    weakened = len(changed) > 0
    confounder_notes = tuple(f"{name}: {ans.note}" if ans.note else name for name, ans in changed)

    stability_caveat = None
    if threshold_met and after_stable is False:
        stability_caveat = (
            "Target hit on average, but the after-process is not yet stable -- not narrated as a clean win; the "
            "loop continues or monitoring extends until the after-process itself stabilizes (rubric R-IMP-03 #6)."
        )

    material_losses = [g for g in guardrail_checks if g.material_worsening]
    guardrail_tradeoff = None
    if threshold_met and material_losses:
        names = ", ".join(g.metric_ref for g in material_losses)
        guardrail_tradeoff = (
            f"Primary metric improved, but a material guardrail loss accompanies it ({names}) -- a stated tradeoff "
            "for the process owner to accept, never plain 'proven' (rubric R-IMP-03 #5)."
        )

    # Headline is fully determined by computed state (module docstring's
    # "renders AS DECLARED, never reworded" contract) -- every "improvement"
    # phrase below is gated on threshold_met; nothing here narrates
    # improvement past an unmet threshold (rubric R-IMP-03 Fail line,
    # R-WRAP-01 "claim upgraded in transit" -- critic-confirmed defect).
    parts = []
    if proof_form == "descriptive":
        # The descriptive branch always states met/not-met (it never did
        # before -- the critic-confirmed gap) and only uses "observed
        # improvement" language when the threshold was actually cleared;
        # a descriptive read against an unmet threshold is just as capable
        # of over-claiming as the inferential branch, so it gets the same
        # gate, not a free pass because there's no p-value attached.
        improvement_clause = (
            " -- observed improvement is shown, not statistically tested (this design can't carry an inferential "
            "test)." if threshold_met else
            " -- no improvement is claimed against the unmet threshold; this design can't carry an inferential "
            "test either way."
        )
        parts.append(
            f"Threshold {threshold_verdict.replace('_', ' ')}, as declared: {metric_ref} moved to {after_mean:g} "
            f"against a declared threshold of {threshold_value:g} ({threshold_direction})" + improvement_clause
        )
    else:
        parts.append(
            f"Threshold {threshold_verdict.replace('_', ' ')}, as declared: {metric_ref} = {after_mean:g} vs "
            f"{threshold_value:g} ({threshold_direction})."
        )
    if weakened:
        if threshold_met:
            parts.append("Improvement shown, but a reported confounder weakens this proof: " + "; ".join(confounder_notes) + ".")
        else:
            # Threshold not met -- there is no improvement claim to weaken.
            # The honest sentence weakens attribution on a FAILURE reading
            # instead (critic finding: this branch previously said
            # "Improvement shown" unconditionally, even here).
            parts.append(
                "Threshold not met, and a reported confounder additionally muddies attribution: "
                + "; ".join(confounder_notes) + "."
            )
    if stability_caveat:
        parts.append(stability_caveat)
    if guardrail_tradeoff:
        parts.append(guardrail_tradeoff)

    result = ProofVerdict(
        proof_form=proof_form, threshold_verdict=threshold_verdict, weakened=weakened,
        confounder_notes=confounder_notes, stability_caveat=stability_caveat,
        guardrail_tradeoff=guardrail_tradeoff, headline=" ".join(parts),
    )
    return compute(
        result,
        method=(
            "threshold check AS DECLARED (met|not_met, never reworded) + confounder echo (any changed=true "
            "weakens) + stability tempering (met-but-unstable) + guardrail tradeoff sentence (rubric R-IMP-03)"
        ),
        input_data={
            "threshold_met": threshold_met, "refused": refused, "after_stable": after_stable,
            "confounders_changed": [name for name, _ in changed], "material_worsening_metrics": [g.metric_ref for g in material_losses],
        },
    )


class ProofArtifact(ArtifactBase):
    tool_id: Literal["T-20"] = "T-20"

    pilot_ref: str = Field(min_length=1)  # links the T-19 plan (task brief: "required")

    # Single copy each -- see module docstring's "enforced by shape" note.
    metric_ref: str = Field(min_length=1)
    operational_definition_ref: str = Field(min_length=1)
    measurement_system_ref: str = Field(min_length=1)

    usl: float | None = None
    lsl: float | None = None
    operational_definition_ok: bool = True

    before: DataRef
    after: DataRef

    declared_threshold: SuccessThreshold  # echoed verbatim from T-19
    confounders: ConfounderChecklist  # re-answered at proof time (rubric R-IMP-02 #5 / R-IMP-03 #3)
    guardrails: list[GuardrailInput] = Field(default_factory=list)

    charter_ref: str = Field(min_length=1)
    charter_baseline_value: float
    charter_goal_value: float
    charter_goal_direction: Direction

    next_cause_ref: NextCauseRef | None = None  # echoed by ref (module docstring) -- see find_next_cause

    # --- server-computed, never hand-typed -- unconditionally recomputed
    # on every validate (module docstring), same contract as every other
    # Computed[...] field in this engine.
    before_baseline: BaselineResult | None = None
    after_baseline: BaselineResult | None = None
    test_result: HypothesisRunResult | None = None
    guardrail_report: Computed[list[GuardrailCheck]] | None = None
    gap: Computed[GapResult] | None = None
    verdict: Computed[ProofVerdict] | None = None

    @model_validator(mode="after")
    def _recompute(self) -> "ProofArtifact":
        self.before_baseline = run_baseline(
            self.before.values, usl=self.usl, lsl=self.lsl, operational_definition_ok=self.operational_definition_ok,
        )
        self.after_baseline = run_baseline(
            self.after.values, usl=self.usl, lsl=self.lsl, operational_definition_ok=self.operational_definition_ok,
        )

        question = HypothesisQuestion(
            question_text=f"Did the pilot change {self.metric_ref!r} between the before and after periods?",
            comparison_type="two_independent",
            groups=[GroupInput(label="before", values=self.before.values), GroupInput(label="after", values=self.after.values)],
        )
        self.test_result = run_hypothesis(question)

        # Weighted mean when after.weights is given (Fix: R-IMP-03 #1
        # same-yardstick / R-IMP-04 anchor) -- the pooled estimate for a
        # set of values that were each already an average/proportion over
        # a different-sized group (e.g. variable daily order counts), not
        # an unweighted mean-of-means that treats a light day and a heavy
        # day as equally informative. None (the continuous, no-weights
        # path) is byte-identical to the old plain mean(). Everything
        # downstream -- the threshold check, the gap block, the headline --
        # uses this one value.
        after_mean = weighted_mean(self.after.values, self.after.weights)
        threshold_met = (
            after_mean <= self.declared_threshold.value if self.declared_threshold.direction == "lower_is_better"
            else after_mean >= self.declared_threshold.value
        )

        self.guardrail_report = compute_guardrail_report(self.guardrails)
        self.gap = compute_gap(
            charter_baseline_value=self.charter_baseline_value, charter_goal_value=self.charter_goal_value,
            after_value=after_mean, direction=self.charter_goal_direction, next_cause_ref=self.next_cause_ref,
        )
        self.verdict = compute_verdict(
            threshold_met=threshold_met, refused=self.test_result.refused, confounders=self.confounders,
            after_stable=self.after_baseline.stable, guardrail_checks=self.guardrail_report.value,
            metric_ref=self.metric_ref, threshold_value=self.declared_threshold.value,
            threshold_direction=self.declared_threshold.direction, after_mean=after_mean,
        )
        return self
