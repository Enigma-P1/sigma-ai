"""T-18 Solution Selection Matrix: candidate solutions for the top-ranked
verified cause, scored on impact/effort (and optionally a weighted-
criteria matrix), computed into the artifact's headline output -- the
RANKED FIX LIST the Improve loop works through (PLAN §4.1, rubric R-IMP-01).

A solution's `linked_cause_ids` is an unchecked cross-reference into T-15's
verified_causes (fishbone.py's Evidence.ref / Cause.parent_cause_id
pattern: plain strings, no project-store I/O at the schema layer) --
whether those ids actually resolve to verified causes is a project-level
concern outside this artifact's reach, same limitation Evidence.ref
states. What this schema DOES enforce: a solution pending linkage
(linked_cause_ids == []) is a legal, saveable in-progress state (PLAN
§4.2's soft/hard split -- "unlinked" is thin content, not a wrong number);
prescore/solution_matrix.py flags it, and compute_ranked_fix_list below
keeps it out of the ranked list entirely, in its own flagged section --
the rubric's Fail line ("a solution unlinked to any verified cause is
piloted anyway") can't happen through the ranked list's own shape.

Impact/effort quadrant: this engine's own convention (PLAN §6 -- every
tool's help panel cites its source, stated here, not implied), not a
licensed framework: both axes are the same 1-5 rating scale FmeaRow uses,
split at the scale's own midpoint (>=3 "high", <3 "low") so impact and
effort are judged by one consistent rule. Four quadrants, plain English:
quick_win (high impact, low effort), major_project (high impact, high
effort), fill_in (low impact, low effort), thankless_task (low impact,
high effort).

Weighted-criteria matrix (optional): named criteria carry a weight and a
declared_at timestamp (rubric R-IMP-01 #3's "weights set before scoring");
a solution's criterion_scores, once started, must cover every declared
criterion exactly once -- a partial score set would make weighted_total a
wrong number by construction, so that's a schema-level hard rule
(_criterion_scores_are_all_or_nothing below), not a prescore flag.
weighted_total = sum(score * weight) over the declared criteria, plain
arithmetic -- weights need not sum to 1; that normalization is a caller
convention prescore doesn't enforce (a judgment call, rubric's own split).

Ranked fix list (Computed[...], the artifact's headline output, PLAN
§4.1: "Output is a ranked fix list -- the queue the improvement loop
works through"): every linked solution, ranked by weighted_total desc
when that solution has one, else impact desc / effort asc -- "when
present" reads per-solution (a mixed project, some solutions scored
against criteria and some not, ranks the scored ones first, per-item, not
as an all-or-nothing artifact switch). Unlinked solutions never enter the
ranked list; they're listed separately, each carrying why.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase, validate_iso8601

Quadrant = Literal["quick_win", "major_project", "fill_in", "thankless_task"]


def compute_quadrant(impact: int, effort: int) -> Quadrant:
    high_impact = impact >= 3
    high_effort = effort >= 3
    if high_impact and not high_effort:
        return "quick_win"
    if high_impact and high_effort:
        return "major_project"
    if not high_impact and not high_effort:
        return "fill_in"
    return "thankless_task"


class WeightedCriterion(BaseModel):
    """One named criterion in the optional weighted matrix. `declared_at`
    is caller-supplied like every other timestamp in this schema layer
    (base.py's contract) -- prescore compares it against each matching
    CriterionScore.scored_at (rubric R-IMP-01 #3)."""

    criterion_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    weight: float = Field(gt=0)
    declared_at: str

    @model_validator(mode="after")
    def _declared_at_iso8601(self) -> "WeightedCriterion":
        validate_iso8601(self.declared_at)
        return self


class CriterionScore(BaseModel):
    criterion_id: str = Field(min_length=1)
    score: int = Field(ge=1, le=5)
    scored_at: str

    @model_validator(mode="after")
    def _scored_at_iso8601(self) -> "CriterionScore":
        validate_iso8601(self.scored_at)
        return self


class Solution(BaseModel):
    solution_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    # Unchecked cross-reference into T-15's verified causes (module
    # docstring) -- [] is the legal "pending linkage" state.
    linked_cause_ids: list[str] = Field(default_factory=list)
    impact: int = Field(ge=1, le=5)
    effort: int = Field(ge=1, le=5)
    criterion_scores: list[CriterionScore] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cause_ids_non_blank(self) -> "Solution":
        if any(not c.strip() for c in self.linked_cause_ids):
            raise ValueError(f"solution {self.solution_id!r}: linked_cause_ids entries must not be blank")
        return self


class SolutionScore(BaseModel):
    """Per-solution computed view -- always present for every solution,
    engine-only (FmeaRow.rpn's "nothing for a hand-typed number to
    overwrite" contract, applied at the artifact level like
    FishboneArtifact.verified_causes rather than as a per-row computed_field,
    since weighted_total needs the artifact's own `criteria` list too)."""

    solution_id: str
    quadrant: Quadrant
    weighted_total: float | None


class RankedEntry(BaseModel):
    rank: int
    solution_id: str
    name: str
    quadrant: Quadrant
    weighted_total: float | None
    impact: int
    effort: int
    linked_cause_ids: list[str]


class UnlinkedSolution(BaseModel):
    solution_id: str
    name: str
    reason: str


class RankedFixList(BaseModel):
    ranked: list[RankedEntry]
    unlinked: list[UnlinkedSolution]


def compute_solution_scores(solutions: list[Solution], criteria: list[WeightedCriterion]) -> Computed[list[SolutionScore]]:
    weights = {c.criterion_id: c.weight for c in criteria}
    scores = []
    for s in solutions:
        weighted_total = (
            round(sum(sc.score * weights[sc.criterion_id] for sc in s.criterion_scores), 4)
            if s.criterion_scores else None
        )
        scores.append(SolutionScore(solution_id=s.solution_id, quadrant=compute_quadrant(s.impact, s.effort), weighted_total=weighted_total))
    return compute(
        scores,
        method=(
            "quadrant = impact/effort each split at the 1-5 scale's midpoint (>=3 high, <3 low); weighted_total = "
            "sum(score * weight) over criterion_scores when a solution has scored every declared criterion, else "
            "None (nothing to weight yet -- schema guarantees criterion_scores is all-or-nothing per solution)"
        ),
        input_data=[
            {"solution_id": s.solution_id, "impact": s.impact, "effort": s.effort,
             "criterion_scores": [sc.model_dump(mode="json") for sc in s.criterion_scores]}
            for s in solutions
        ],
    )


def compute_ranked_fix_list(solutions: list[Solution], scores: list[SolutionScore]) -> Computed[RankedFixList]:
    by_id = {sc.solution_id: sc for sc in scores}
    linked = [s for s in solutions if s.linked_cause_ids]
    unlinked = [s for s in solutions if not s.linked_cause_ids]

    def sort_key(s: Solution) -> tuple[int, float, int, int, str]:
        wt = by_id[s.solution_id].weighted_total
        # Scored-first (group 0, weighted_total desc), then everyone else
        # (group 1, impact desc / effort asc) -- "weighted total when
        # present else impact-desc effort-asc" read per solution, so a
        # mixed project ranks its scored solutions first without waiting
        # for every solution to be scored.
        return (0, -wt, -s.impact, s.effort, s.solution_id) if wt is not None else (1, 0.0, -s.impact, s.effort, s.solution_id)

    ordered = sorted(linked, key=sort_key)
    ranked = [
        RankedEntry(
            rank=i + 1, solution_id=s.solution_id, name=s.name, quadrant=by_id[s.solution_id].quadrant,
            weighted_total=by_id[s.solution_id].weighted_total, impact=s.impact, effort=s.effort,
            linked_cause_ids=s.linked_cause_ids,
        )
        for i, s in enumerate(ordered)
    ]
    unlinked_flags = [
        UnlinkedSolution(
            solution_id=s.solution_id, name=s.name,
            reason="no linked_cause_ids -- not ranked until linked to a verified cause (rubric R-IMP-01 #2)",
        )
        for s in unlinked
    ]
    return compute(
        RankedFixList(ranked=ranked, unlinked=unlinked_flags),
        method=(
            "ranked = linked solutions (linked_cause_ids non-empty) ordered by weighted_total desc when present, "
            "else impact desc / effort asc, tie-broken by solution_id; unlinked solutions never enter the ranked "
            "list -- listed separately, each flagged (PLAN §4.1's ranked fix list, rubric R-IMP-01)"
        ),
        input_data=[
            {"solution_id": s.solution_id, "linked": bool(s.linked_cause_ids), "impact": s.impact, "effort": s.effort,
             "weighted_total": by_id[s.solution_id].weighted_total}
            for s in solutions
        ],
    )


class SolutionMatrixArtifact(ArtifactBase):
    tool_id: Literal["T-18"] = "T-18"

    # A solution mid-draft, or a matrix with zero solutions yet, are both
    # legal saveable states (PLAN §4.2 soft/hard split) -- rubric R-IMP-01
    # #1's "at least two candidate solutions" is prescore's job.
    solutions: list[Solution] = Field(default_factory=list)
    criteria: list[WeightedCriterion] = Field(default_factory=list)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as every other Computed[...] field in this engine.
    scores: Computed[list[SolutionScore]] | None = None
    ranked_fix_list: Computed[RankedFixList] | None = None

    @model_validator(mode="after")
    def _unique_ids(self) -> "SolutionMatrixArtifact":
        sol_ids = [s.solution_id for s in self.solutions]
        if len(sol_ids) != len(set(sol_ids)):
            raise ValueError("solution_id values must be unique")
        crit_ids = [c.criterion_id for c in self.criteria]
        if len(crit_ids) != len(set(crit_ids)):
            raise ValueError("criterion_id values must be unique")
        return self

    @model_validator(mode="after")
    def _criterion_scores_are_all_or_nothing(self) -> "SolutionMatrixArtifact":
        declared = {c.criterion_id for c in self.criteria}
        for s in self.solutions:
            if not s.criterion_scores:
                continue  # not started yet -- legal; weighted_total stays None
            scored = [sc.criterion_id for sc in s.criterion_scores]
            unknown = [cid for cid in scored if cid not in declared]
            if unknown:
                raise ValueError(f"solution {s.solution_id!r}: criterion_scores reference undeclared criterion_id(s) {unknown}")
            if len(scored) != len(set(scored)):
                raise ValueError(f"solution {s.solution_id!r}: criterion_scores has duplicate criterion_id entries")
            if set(scored) != declared:
                raise ValueError(
                    f"solution {s.solution_id!r}: criterion_scores must cover every declared criterion exactly once "
                    f"once started -- a partial score set can't produce a trustworthy weighted_total "
                    f"(missing {sorted(declared - set(scored))})"
                )
        return self

    @model_validator(mode="after")
    def _recompute(self) -> "SolutionMatrixArtifact":
        self.scores = compute_solution_scores(self.solutions, self.criteria)
        self.ranked_fix_list = compute_ranked_fix_list(self.solutions, self.scores.value)
        return self
