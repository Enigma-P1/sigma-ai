"""T-25 A3 Final Report + Tollgate Checklists: a GUIDED NARRATIVE BUILDER
(PLAN §4.1), not field concatenation. Eight panels, each carrying where its
narrative was seeded from (artifact ref + which fields) and editable
narrative text -- the actual seeding (loading the source artifact, drafting
opening text) is a desktop action, echoed-by-ref here (proof.py's
`next_cause_ref` contract): this module stores and recomputes, it does not
reach into the project store.

The realized-benefits panel additionally carries `RealizedBenefits`, whose
`before_amount`/`after_amount` are the COPQ re-run's own numbers (reused as
plain floats -- rubric R-WRAP-02: "the COPQ re-run at Wrap") and whose
`result` is engine-computed (CopqRow.amount's "nothing for a hand-typed
number to overwrite" discipline, at Computed[...] scale since this is an
artifact-level rollup, not a per-row property).

Tollgate checklists per phase carry this engine's own original-wording
standard questions (PLAN §6: no licensed rubric text), stamped onto the
artifact the same way fmea.py's FmeaAnchors are -- engine-owned reference
content, unconditionally overwritten, never client-supplied; only the
user's `answers` survive a round trip.

Closure reuses proof.py's `compute_gap`/`GapResult` VERBATIM for the
objectives-vs-charter reconciliation (rubric R-WRAP-03 #1: "consistent with
the Improve conclusion (R-IMP-05)" -- literally the same formula, so
consistency is true by construction, not a cross-check). The FMEA
sev-block close check reuses fmea.py's `BlockingFlag` verbatim (task
brief's reuse instruction): `close_blocked` is computed from a
caller-resolved snapshot of the linked FMEA's own `blocking_flags`
(FmeaCloseCheckInput -- the same echoed-by-ref contract as everything
else here), and marking the project `closed` while blocked is a hard
ValueError (R-WRAP-03/R-ANA-03's rule -- this is "the claim would be
false," control_chart.py's EXIT-11 bar, not a content-quality flag).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase, validate_iso8601
from .fmea import BlockingFlag
from .pilot_plan import Direction
from .proof import GapResult, compute_gap

PanelKind = Literal[
    "background", "current_condition", "goal", "analysis",
    "countermeasures", "results", "follow_up_control", "lessons",
]
PANEL_ORDER: tuple[PanelKind, ...] = (
    "background", "current_condition", "goal", "analysis",
    "countermeasures", "results", "follow_up_control", "lessons",
)

# Which tool a "re-seed from artifact" affordance would pull from by
# default (desktop-side hint only -- any artifact_ref validates; PLAN
# §4.1's "each panel pre-seeded from its source artifact").
PANEL_SEED_TOOL_HINT: dict[PanelKind, str] = {
    "background": "T-03", "current_condition": "T-13", "goal": "T-03",
    "analysis": "T-15", "countermeasures": "T-18", "results": "T-20",
    "follow_up_control": "T-22", "lessons": "T-20",
}


class SeededFrom(BaseModel):
    artifact_ref: str = Field(min_length=1)
    tool_id: str = Field(min_length=1)
    fields: list[str] = Field(default_factory=list)  # which source fields this narrative drew from


class A3Panel(BaseModel):
    panel: PanelKind
    seeded_from: SeededFrom | None = None
    narrative: str = ""  # user-editable prose -- the story, not a field dump
    seeded_at: str | None = None

    @model_validator(mode="after")
    def _iso_if_present(self) -> "A3Panel":
        if self.seeded_at is not None:
            validate_iso8601(self.seeded_at)
        return self


class RealizedBenefitsResult(BaseModel):
    realized_to_date: float
    net_of_fix_cost: float


def compute_realized_benefits(before_amount: float, after_amount: float, fix_cost: float) -> Computed[RealizedBenefitsResult]:
    realized = before_amount - after_amount
    result = RealizedBenefitsResult(realized_to_date=realized, net_of_fix_cost=realized - fix_cost)
    return compute(
        result,
        method=(
            "realized_to_date = before_amount - after_amount (the COPQ re-run's own before/after money, rubric "
            "R-WRAP-02 #2: ties to the measured improvement, not the original COPQ hope); net_of_fix_cost = "
            "realized_to_date - fix_cost (#3: costs of the fix netted, or at least named beside the benefit)"
        ),
        input_data={"before_amount": before_amount, "after_amount": after_amount, "fix_cost": fix_cost},
    )


class RealizedBenefits(BaseModel):
    """The results panel's extra structured block (module docstring).
    `window` is rubric R-WRAP-02 #1's stated realized-to-date window (a
    student project may have weeks, not quarters); `annualized_projection`
    is optional and, when given, is labeled projection, never realized."""

    copq_rerun_artifact_id: str = Field(min_length=1)  # the T-02 re-run this panel is built on
    window: str = Field(min_length=1)  # e.g. "6 weeks post-rollout"
    before_amount: float
    after_amount: float
    fix_cost: float = 0.0
    annualized_projection: float | None = None
    result: Computed[RealizedBenefitsResult] | None = None  # server-computed -- see A3Artifact._recompute_realized_benefits


TollgatePhase = Literal["Define", "Measure", "Analyze", "Improve", "Control", "Wrap"]
TOLLGATE_PHASES: tuple[TollgatePhase, ...] = ("Define", "Measure", "Analyze", "Improve", "Control", "Wrap")


class TollgateQuestion(BaseModel):
    question_id: str
    text: str


# This engine's own original wording (PLAN §6: no licensed rubric text
# reproduced) -- the standard Champion tollgate questions per phase exit.
# Engine-owned reference content, stamped unconditionally (never
# client-supplied) by A3Artifact._stamp_tollgates below, FmeaAnchors'
# pattern.
TOLLGATE_QUESTIONS: dict[TollgatePhase, tuple[TollgateQuestion, ...]] = {
    "Define": (
        TollgateQuestion(question_id="define-1", text="Is the problem stated in measurable terms, with no cause and no fix implied?"),
        TollgateQuestion(question_id="define-2", text="Does the charter name a process owner who has actually agreed to the scope?"),
        TollgateQuestion(question_id="define-3", text="Is the business impact stated in dollars or hours, and does it hold up against an independent number?"),
    ),
    "Measure": (
        TollgateQuestion(question_id="measure-1", text="Is the baseline built on a process the data shows is stable, not just assumed to be?"),
        TollgateQuestion(question_id="measure-2", text="Has the measurement system itself been checked, and did it pass?"),
        TollgateQuestion(question_id="measure-3", text="Is the operational definition tight enough that two different people would measure the same thing the same way?"),
    ),
    "Analyze": (
        TollgateQuestion(question_id="analyze-1", text="Does every candidate cause carry actual evidence, not just an opinion in the room?"),
        TollgateQuestion(question_id="analyze-2", text="Are the verified causes the ones the data points to, not just the easiest ones to fix?"),
        TollgateQuestion(question_id="analyze-3", text="Has every severity-9/10 failure mode been given an action, not just logged and left?"),
    ),
    "Improve": (
        TollgateQuestion(question_id="improve-1", text="Was exactly one change piloted at a time, with a success threshold set before the data came in?"),
        TollgateQuestion(question_id="improve-2", text="Does the before/after proof account honestly for anything else that changed during the pilot?"),
        TollgateQuestion(question_id="improve-3", text="How much of the original gap does this fix close, and what is the plan for what's left?"),
    ),
    "Control": (
        TollgateQuestion(question_id="control-1", text="Does every monitored item have a real, named owner who has accepted the role?"),
        TollgateQuestion(question_id="control-2", text="Is there an out-of-control response path a person could actually follow, today, without asking what it means?"),
        TollgateQuestion(question_id="control-3", text="Is someone trained on the new method, by name, with a way to verify they can actually do it?"),
    ),
    "Wrap": (
        TollgateQuestion(question_id="wrap-1", text="Does the realized benefit trace to the measured improvement, not to the original COPQ hope?"),
        TollgateQuestion(question_id="wrap-2", text="Are the lessons learned substantive, including at least one thing that didn't work?"),
        TollgateQuestion(question_id="wrap-3", text="Is every open item handed off to a named owner, not left to fall through?"),
    ),
}


class TollgateAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answered: bool = False
    response: str = ""
    evidence_ref: str | None = None


class TollgateChecklist(BaseModel):
    phase: TollgatePhase
    questions: tuple[TollgateQuestion, ...] = ()  # engine-stamped -- see A3Artifact._stamp_tollgates
    answers: list[TollgateAnswer] = Field(default_factory=list)


class ObjectivesInput(BaseModel):
    """Echoed from the charter (T-03) + the current measured/achieved value
    -- the same three-plus-direction shape proof.py's gap block takes."""

    charter_baseline_value: float
    charter_goal_value: float
    achieved_value: float
    direction: Direction


class LessonEntry(BaseModel):
    lesson_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    went_wrong: bool = False  # rubric R-WRAP-03 #2: at least one lesson must flag this


class OpenItem(BaseModel):
    item_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner: str = ""  # blank -> prescore flag (R-WRAP-03 #3: "open items are handed off with owners")


class FmeaCloseCheckInput(BaseModel):
    """Caller-resolved snapshot of the linked FMEA's own computed
    `blocking_flags` (fmea.py, reused verbatim per the task brief) -- the
    desktop loads the project's latest T-16 artifact and copies its
    blocking_flags in before this artifact validates, the same
    echoed-by-ref contract as every cross-reference in this engine."""

    fmea_artifact_id: str = Field(min_length=1)
    blocking_flags: list[BlockingFlag] = Field(default_factory=list)


class CloseBlockResult(BaseModel):
    close_blocked: bool
    blocking_rows: list[BlockingFlag]
    reason: str


def compute_close_block(fmea_check: FmeaCloseCheckInput | None) -> Computed[CloseBlockResult]:
    flags = list(fmea_check.blocking_flags) if fmea_check else []
    blocked = bool(flags)
    reason = (
        f"{len(flags)} unaddressed severity-9/10 safety/regulatory row(s) on the linked FMEA "
        f"({fmea_check.fmea_artifact_id if fmea_check else 'none linked'}) -- project may not close until each "
        "carries an action (R-WRAP-03 / R-ANA-03)."
        if blocked else
        "No unaddressed severity-9/10 safety/regulatory row on the linked FMEA -- this check does not block closure."
    )
    result = CloseBlockResult(close_blocked=blocked, blocking_rows=flags, reason=reason)
    return compute(
        result,
        method=(
            "close_blocked = the linked FMEA's own blocking_flags (fmea.py) carried non-empty -- R-ANA-03's Fail "
            "line, echoed here per R-WRAP-03: an unaddressed severity-9/10 safety/regulatory row blocks 'project "
            "may close' however clean the rest of the stack"
        ),
        input_data={"fmea_artifact_id": fmea_check.fmea_artifact_id if fmea_check else None, "n_blocking": len(flags)},
    )


class ClosureBlock(BaseModel):
    objectives_input: ObjectivesInput | None = None
    objectives_verdict: Computed[GapResult] | None = None  # server-computed via proof.compute_gap, reused verbatim
    lessons: list[LessonEntry] = Field(default_factory=list)
    open_items: list[OpenItem] = Field(default_factory=list)
    fmea_check: FmeaCloseCheckInput | None = None
    close_check: Computed[CloseBlockResult] | None = None  # server-computed -- see A3Artifact._recompute_closure
    project_status: Literal["open", "closed"] = "open"


class A3Artifact(ArtifactBase):
    tool_id: Literal["T-25"] = "T-25"

    panels: list[A3Panel] = Field(min_length=len(PANEL_ORDER), max_length=len(PANEL_ORDER))
    realized_benefits: RealizedBenefits | None = None
    tollgates: list[TollgateChecklist] = Field(default_factory=list)
    closure: ClosureBlock = Field(default_factory=ClosureBlock)

    @model_validator(mode="after")
    def _panels_cover_every_kind_exactly_once(self) -> "A3Artifact":
        kinds = [p.panel for p in self.panels]
        if sorted(kinds) != sorted(PANEL_ORDER):
            raise ValueError(f"panels must cover exactly {PANEL_ORDER}, one each -- got {kinds}")
        by_kind = {p.panel: p for p in self.panels}
        self.panels = [by_kind[k] for k in PANEL_ORDER]  # canonical order, panel-by-panel (module docstring)
        return self

    @model_validator(mode="after")
    def _stamp_tollgates(self) -> "A3Artifact":
        by_phase = {t.phase: t for t in self.tollgates}
        self.tollgates = [
            TollgateChecklist(
                phase=phase, questions=TOLLGATE_QUESTIONS[phase],
                answers=by_phase[phase].answers if phase in by_phase else [],
            )
            for phase in TOLLGATE_PHASES
        ]
        return self

    @model_validator(mode="after")
    def _recompute_realized_benefits(self) -> "A3Artifact":
        if self.realized_benefits is not None:
            rb = self.realized_benefits
            rb.result = compute_realized_benefits(rb.before_amount, rb.after_amount, rb.fix_cost)
        return self

    @model_validator(mode="after")
    def _recompute_closure(self) -> "A3Artifact":
        self.closure.close_check = compute_close_block(self.closure.fmea_check)
        if self.closure.objectives_input is not None:
            oi = self.closure.objectives_input
            self.closure.objectives_verdict = compute_gap(
                charter_baseline_value=oi.charter_baseline_value, charter_goal_value=oi.charter_goal_value,
                after_value=oi.achieved_value, direction=oi.direction, next_cause_ref=None,
            )
        if self.closure.project_status == "closed" and self.closure.close_check.value.close_blocked:
            raise ValueError(
                "R-WRAP-03/R-ANA-03: project may not be marked closed -- " + self.closure.close_check.value.reason
            )
        return self
