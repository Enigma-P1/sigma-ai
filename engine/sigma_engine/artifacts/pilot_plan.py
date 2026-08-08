"""T-19 Pilot Plan: the small-study designer PLAN §4.1 calls for, not a
form -- one change at a time, a comparison defined before running,
who/what included and how selected, a success threshold and analysis plan
declared BEFORE data collection, a falsification line with teeth, and the
plain-English confounder checklist that carries into T-20's proof (rubric
R-IMP-02). Like DataCollectionPlanArtifact, this is a plan a person writes
down, not a result the engine derives -- no Computed[...] field lives here.

**The one-change discipline is schema-enforced, not a prescore flag**
(matrix §4a EXIT-10: "pilot plan declares more than one change"): `changes`
is the append-only list a "+ add another change" affordance would write
to, capped at length 1 -- a second entry raises EXIT-10 by name, teaching
the rule in the error rather than silently rejecting or truncating.
`the_one_change` is the declared content for that one entry (statement +
what it traces back to); a validator below keeps the two views from
silently diverging. This mirrors the same soft/hard split PLAN §4.2 draws
everywhere else: a second change isn't thin content, it's the exact wrong
number this whole tool exists to prevent.

**The declared_at fields are the pre-declaration record, honestly framed**
(rubric R-IMP-02 #3's own caveat): a timestamp only proves entry order,
never observation order -- a spreadsheet can defeat it. prescore/
pilot_plan.py's threshold-before-data check is stated as advisory for
exactly that reason; it is never a hard gate here.

Content-quality fields (whether the falsification line has real teeth,
whether unit selection reads as convenience sampling) are prescore flags,
not schema rejections -- the same PLAN §4.2 hard/soft split every other
artifact in this engine draws. What IS schema-hard: falsification_line
non-empty, every confounder answered, and the one-change rule above.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .base import ArtifactBase, validate_iso8601

ComparisonKind = Literal["before_period", "parallel_group"]
Direction = Literal["higher_is_better", "lower_is_better"]
PilotStatus = Literal["designed", "running", "complete"]


class ChangeDescription(BaseModel):
    """One entry in the append-only `changes` list -- the structural
    EXIT-10 trigger (module docstring). change_id is a client-generated
    id, same free-form-string convention as every other *_id field in
    this engine (Cause.cause_id, FmeaRow.row_id)."""

    change_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class TheOneChange(BaseModel):
    """The single declared change's content (rubric R-IMP-02 #1: "one
    change per pilot, stated in one sentence"). `linked_solution_id`/
    `linked_cause_ids` are unchecked cross-references into T-18/T-15
    (Evidence.ref's contract, fishbone.py) -- plain strings, no
    project-store I/O at the schema layer."""

    statement: str = Field(min_length=1)
    linked_solution_id: str | None = None
    linked_cause_ids: list[str] = Field(default_factory=list)


class ComparisonDesign(BaseModel):
    """Rubric R-IMP-02 #2: "the comparison is defined before running:
    baseline period or parallel comparison, stated." `description` is
    the period/group itself, in the student's words ("last 4 weeks of
    baseline data" / "line 3 runs unchanged as the parallel control")."""

    kind: ComparisonKind
    description: str = Field(min_length=1)


class Inclusion(BaseModel):
    """Who/what is in the pilot and how they were picked, plus the
    honesty-note field the build brief names explicitly: a place to say
    the quiet part about selection (e.g. "chosen by convenience -- the
    two lines closest to the supervisor's office") rather than let it go
    unstated. All three are free text; content-quality (a blank honesty
    note, a selection method that reads as convenience with no
    disclosure) is prescore's job, not a schema rejection (§10: "unit-
    selection bias is graded at stated honestly, not sampling-theory
    rigor")."""

    who_or_what: str = Field(min_length=1)
    how_selected: str = Field(min_length=1)
    honesty_note: str = ""


class SuccessThreshold(BaseModel):
    """Rubric R-IMP-02 #3: declared BEFORE data collection. `declared_at`
    is the pre-declaration timestamp (module docstring's honesty
    caveat) -- caller-supplied like every other timestamp in this
    schema layer, never generated server-side."""

    metric_ref: str = Field(min_length=1)
    direction: Direction
    value: float
    declared_at: str

    @model_validator(mode="after")
    def _declared_at_iso8601(self) -> "SuccessThreshold":
        validate_iso8601(self.declared_at)
        return self


class AnalysisPlan(BaseModel):
    """Which T-17 route is expected, declared up front alongside the
    threshold (rubric R-IMP-02 #3) -- `expected_route` is a free pick
    from stats.hypothesis_common.RouteName's names, but kept a plain
    string here rather than importing that Literal: the plan is a
    forecast written before T-20 re-runs the engine for real, and the
    actual route the data calls for at proof time is allowed to differ
    (the desktop's picklist offers the real route names; the schema
    doesn't lock the artifact to only-ever-correct forecasts)."""

    expected_route: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ConfounderAnswer(BaseModel):
    changed: bool
    note: str = ""


class ConfounderChecklist(BaseModel):
    """Rubric R-IMP-02 #5: staffing/season/demand/measurement/other,
    answered up front, to be re-answered at proof (T-20 re-asks the same
    five questions against what actually happened). All five required --
    a checklist with a silently-skipped question isn't a checklist."""

    staffing: ConfounderAnswer
    season: ConfounderAnswer
    demand: ConfounderAnswer
    measurement: ConfounderAnswer
    other: ConfounderAnswer


class PilotPlanArtifact(ArtifactBase):
    tool_id: Literal["T-19"] = "T-19"

    the_one_change: TheOneChange
    # The structural EXIT-10 trigger (module docstring) -- required,
    # capped at 1 by _one_change_only below.
    changes: list[ChangeDescription] = Field(min_length=1)
    comparison_design: ComparisonDesign
    inclusion: Inclusion
    success_threshold: SuccessThreshold
    analysis_plan: AnalysisPlan
    # Required non-empty (rubric R-IMP-02 #4); prescore/pilot_plan.py
    # additionally checks it reads as substantive, not just a negation.
    falsification_line: str = Field(min_length=1)
    confounder_checklist: ConfounderChecklist
    status: PilotStatus = "designed"

    @model_validator(mode="after")
    def _one_change_only(self) -> "PilotPlanArtifact":
        if len(self.changes) > 1:
            raise ValueError(
                "EXIT-10: more than one change described for a single pilot (matrix §4a trigger: \"pilot plan "
                "declares more than one change\"). The Improve loop is one-change-at-a-time by design (PLAN §4.1, "
                "rubric R-IMP-02 #1): run the extra change as its own sequential pilot once this one is proven, "
                "declare a genuinely inseparable PACKAGE explicitly if the components truly cannot deploy apart "
                "(R-IMP-02's carve-out -- attribution then goes to the package only, never a component), or route "
                f"to the advisor / v1.1 Experiment Planner / a human expert for a real multi-factor question. "
                f"Remove the extra entry from `changes` (got {len(self.changes)}) before saving."
            )
        if self.changes[0].text.strip() != self.the_one_change.statement.strip():
            raise ValueError(
                "the_one_change.statement must match changes[0].text -- the one declared change can't read two "
                "different ways in the same artifact"
            )
        return self
