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

**declared_package -- R-IMP-02 #1's "one honest carve-out" (M4 addition)**:
a genuinely inseparable package (components that cannot deploy apart) may
run as one pilot when declared as the package up front, with attribution
limited to the package as a whole and every component listed -- never a
component-level claim. Schema-hard when `declared_package` is present:
`changes` must carry exactly one entry per listed component (1:1, the
same "no silent divergence" move `the_one_change` vs `changes[0]` already
makes) -- EXIT-10 does not fire for that declared set (the whole point of
the carve-out), and the mismatched-count case fails with its own message,
distinct from EXIT-10, since it isn't an undeclared bundle. What stays
soft (prescore/pilot_plan.py's `package_declaration_quality`): whether the
package reads as a REAL package -- >=2 listed components and a stated
rationale -- a 1-component "package" is schema-legal (structurally it
changes nothing: with one component, `changes` still caps at one entry,
same as no package at all) but flagged, since it's just a change wearing
a costume, not the carve-out the rubric describes. `package_attribution_
note` is stamped (Computed[str], same provenance contract as every other
engine-derived value here) whenever `declared_package` is present, so the
artifact itself carries the "package-level credit only" statement rather
than leaving it to be reconstructed downstream.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..provenance import Computed, compute
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


class DeclaredPackage(BaseModel):
    """Rubric R-IMP-02 #1's "one honest carve-out" (module docstring): a
    genuinely inseparable package, declared up front. Schema-hard: non-
    empty rationale, at least one non-blank component -- a package needs
    something declared to mean anything structurally. The qualitative bar
    that makes this a REAL package rather than a change wearing a costume
    (>=2 components, a substantive rationale) is prescore's job
    (package_declaration_quality, prescore/pilot_plan.py) -- same soft/
    hard split the falsification line already draws (module docstring)."""

    rationale: str = Field(min_length=1)  # why the components cannot be deployed apart
    components: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _components_non_blank(self) -> "DeclaredPackage":
        if any(not c.strip() for c in self.components):
            raise ValueError("declared_package.components entries must be non-empty -- a blank component isn't a listed component")
        return self


def compute_package_attribution_note(package: DeclaredPackage) -> Computed[str]:
    """Stamped onto PilotPlanArtifact.package_attribution_note whenever
    declared_package is present -- the artifact carries its own honest
    attribution statement (module docstring) rather than leaving proof.py
    (or a human reader) to reconstruct "this was a package, not a single
    change" from the component list alone."""
    text = (
        f"Declared package of {len(package.components)} component(s) ({', '.join(package.components)}) -- proof "
        "credit is package-level only; nothing here is attributable to a single component (rubric R-IMP-02's "
        "carve-out)."
    )
    return compute(
        text,
        method=(
            "stamped whenever declared_package is present -- package-level attribution only, never a "
            "component-level claim (rubric R-IMP-02's carve-out, matrix EXIT-10)"
        ),
        input_data={"rationale": package.rationale, "components": list(package.components)},
    )


class PilotPlanArtifact(ArtifactBase):
    tool_id: Literal["T-19"] = "T-19"

    the_one_change: TheOneChange
    # The structural EXIT-10 trigger (module docstring) -- required,
    # capped at 1 by _one_change_only below (or, when declared_package is
    # present, capped at len(declared_package.components) instead).
    changes: list[ChangeDescription] = Field(min_length=1)
    comparison_design: ComparisonDesign
    inclusion: Inclusion
    success_threshold: SuccessThreshold
    analysis_plan: AnalysisPlan
    # Required non-empty (rubric R-IMP-02 #4); prescore/pilot_plan.py
    # additionally checks it reads as substantive, not just a negation.
    falsification_line: str = Field(min_length=1)
    confounder_checklist: ConfounderChecklist
    # Optional: R-IMP-02 #1's carve-out (module docstring). None (the
    # default) is the ordinary single-change pilot -- everything below
    # behaves exactly as it did before this field existed.
    declared_package: DeclaredPackage | None = None
    package_attribution_note: Computed[str] | None = None  # server-stamped -- see _stamp_package_attribution
    status: PilotStatus = "designed"

    @model_validator(mode="after")
    def _one_change_only(self) -> "PilotPlanArtifact":
        if self.declared_package is not None:
            n_components = len(self.declared_package.components)
            if len(self.changes) != n_components:
                # Deliberately never writes the four-character exit code as
                # a literal substring anywhere in this message: usePilotPlanForm.ts
                # detects the undeclared-bundle refusal by searching validation
                # text for that exact substring, and this is a different
                # failure (a declared package's own count mismatch, a data-
                # entry error to fix, not a bundle to split apart) -- it must
                # never light up that banner.
                raise ValueError(
                    f"declared_package lists {n_components} component(s), but changes carries {len(self.changes)} "
                    "entries -- a declared package's changes must align 1:1 with its listed components (rubric "
                    "R-IMP-02's carve-out: every component listed, none hidden, none invented) before this can "
                    "save. This is a component/changes count mismatch on a DECLARED package, not an undeclared "
                    "bundle -- fix the count instead of removing the package declaration."
                )
            # No changes[0]-vs-the_one_change cross-check here: with N>=1
            # changes entries mapped 1:1 to N components, "the one change"
            # is the package as a whole, not any single changes[] entry
            # (module docstring). the_one_change.statement is still
            # required non-empty by its own field type -- it just isn't
            # forced to equal any one component's text.
            return self
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

    @model_validator(mode="after")
    def _stamp_package_attribution(self) -> "PilotPlanArtifact":
        self.package_attribution_note = (
            compute_package_attribution_note(self.declared_package) if self.declared_package is not None else None
        )
        return self
