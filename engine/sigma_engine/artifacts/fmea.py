"""T-16 process FMEA: failure-mode rows tied to a process step (an
optional T-06 step_id link, plus a free-text step name that's always
present so a row never floats with no step at all), rated against
original-wording 1-10 severity/occurrence/detection anchor scales (PLAN
§6: industry-standard anchor *structure*, no AIAG/ASQ licensed text --
every sentence below is this engine's own). RPN is a per-row computed_field
(severity * occurrence * detection), the same "nothing for a hand-typed
number to overwrite" contract as CopqRow.amount -- there is no settable
`rpn` field to tamper with, only a property derived from the three rating
fields every time they're read.

Two artifact-level computed results, both engine-only (unconditionally
recomputed on every validate, CopqArtifact.total's contract): `sorted_view`
is the severity-first-then-RPN row order rubric R-ANA-03 calls the tool's
default view (#3: "severity-first is the tool's default view, not a
graded requirement" -- RPN alone would let a high-RPN, low-severity row
outrank a high-severity one, exactly the misuse the rubric warns about).
`blocking_flags` is the rubric's Fail line made machine-checkable: a
severity-9/10 row whose effect text reads safety/regulatory AND carries no
action -- unaddressed, that's this item's invalidator, and (R-WRAP-03) it
blocks "project may close" at Wrap however clean the rest of the stack.
The keyword match is a heuristic screen, not a certified determination --
stated in the provenance, not hidden.

`anchors` embeds the reference table directly on the artifact (this
engine's own generic wording, never a client-supplied value) so a saved/
exported FMEA carries the scale it was rated against, self-contained.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase, validate_iso8601

ActionStatus = Literal["open", "done", "na"]

# Original generic wording (PLAN §6 / matrix I.C.2: "industry-standard 1-10
# anchor structure, original generic wording -- no AIAG or ASQ licensed
# text reproduced"). Same 10-point structure the field uses; every
# sentence below is this engine's own, not quoted from any standard.
SEVERITY_ANCHORS: dict[int, str] = {
    10: "Extreme -- safety hazard or a regulatory violation, with no warning before it happens.",
    9: "Extreme -- safety hazard or a regulatory violation, but with some warning beforehand.",
    8: "Very high -- the product or process becomes unusable; the customer is very dissatisfied.",
    7: "High -- major function is lost; most customers are significantly dissatisfied.",
    6: "Moderate-high -- performance is noticeably degraded; the customer is dissatisfied.",
    5: "Moderate -- performance is reduced in a way most customers notice and dislike.",
    4: "Low-moderate -- a minor loss of performance; many customers notice.",
    3: "Low -- a slight, easily-tolerated effect; only a discerning customer notices.",
    2: "Very low -- a minor nuisance most customers would never notice.",
    1: "None -- no discernible effect on the customer or the process.",
}
OCCURRENCE_ANCHORS: dict[int, str] = {
    10: "Very high -- the cause is present on nearly every unit or cycle.",
    9: "Very high -- frequent, roughly 1 in 3.",
    8: "High -- repeated failures, roughly 1 in 8.",
    7: "High -- roughly 1 in 20.",
    6: "Moderate -- occasional failures, roughly 1 in 80.",
    5: "Moderate -- roughly 1 in 400.",
    4: "Moderate-low -- roughly 1 in 2,000.",
    3: "Low -- relatively few failures, roughly 1 in 15,000.",
    2: "Low -- rare, roughly 1 in 150,000.",
    1: "Remote -- failure from this cause is unlikely; no known history of it.",
}
DETECTION_ANCHORS: dict[int, str] = {
    10: "No current control could detect this cause or mode before it reaches the next step.",
    9: "Very remote chance the current controls catch it in time.",
    8: "Remote chance of detection with the current controls.",
    7: "Very low chance of detection with the current controls.",
    6: "Low chance of detection with the current controls.",
    5: "Moderate chance the current controls catch it.",
    4: "Moderately high chance the current controls catch it.",
    3: "High chance the current controls catch it.",
    2: "Very high chance the current controls catch it before it moves on.",
    1: "Almost certain -- current controls will catch it before it ever leaves this step.",
}

# Rubric R-ANA-03's Fail line, made rule-checkable: a heuristic keyword scan
# over each row's effect text (prescore/charter.py's SOLUTION_LANGUAGE_
# KEYWORDS is the same "one reviewable list" idiom).
SAFETY_REGULATORY_KEYWORDS: tuple[str, ...] = (
    "safety", "safe", "injur", "hazard", "harm", "accident", "osha",
    "regulatory", "regulation", "compliance", "violation", "epa", "fda",
    "shock", "fire", "toxic", "exposure", "fatal", "burn",
)
_SAFETY_PATTERN = re.compile(r"\b(" + "|".join(re.escape(k) for k in SAFETY_REGULATORY_KEYWORDS) + r")", re.IGNORECASE)
HIGH_SEVERITY: frozenset[int] = frozenset({9, 10})


class FmeaAnchors(BaseModel):
    severity: dict[int, str]
    occurrence: dict[int, str]
    detection: dict[int, str]


def _default_anchors() -> FmeaAnchors:
    return FmeaAnchors(severity=dict(SEVERITY_ANCHORS), occurrence=dict(OCCURRENCE_ANCHORS), detection=dict(DETECTION_ANCHORS))


class FmeaRow(BaseModel):
    row_id: str = Field(min_length=1)
    # Optional link to a T-06 ProcessMapArtifact step_id -- unchecked cross-
    # reference (same contract as DataCollectionPlanArtifact.charter_metric_id,
    # no project-store I/O at the schema layer). `step_name` is always
    # present so a row never floats with no named step at all, linked or not.
    process_step_ref: str | None = None
    step_name: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    effect: str = Field(min_length=1)
    cause: str = Field(min_length=1)
    severity: int = Field(ge=1, le=10)
    occurrence: int = Field(ge=1, le=10)
    detection: int = Field(ge=1, le=10)
    action: str = ""
    action_owner: str = ""
    action_due: str | None = None
    action_status: ActionStatus = "open"
    # Honest self-report (T-11 OperationalDefinition.two_people_confirmed's
    # "checklist confirmation" idiom, PLAN §4.1): the desktop sets this once
    # the anchor text has actually been shown for this row's rating.
    anchors_consulted: bool = False

    @field_validator("action_due")
    @classmethod
    def _action_due_iso8601_if_present(cls, v: str | None) -> str | None:
        return v if v is None else validate_iso8601(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rpn(self) -> int:
        # CopqRow.amount's pattern: a property, not a settable field --
        # there is nothing for a hand-typed number to overwrite.
        return self.severity * self.occurrence * self.detection


class BlockingFlag(BaseModel):
    row_id: str
    failure_mode: str
    effect: str
    severity: int
    reason: str


def compute_blocking_flags(rows: list[FmeaRow]) -> Computed[list[BlockingFlag]]:
    flags = [
        BlockingFlag(
            row_id=r.row_id, failure_mode=r.failure_mode, effect=r.effect, severity=r.severity,
            reason=f"severity {r.severity}, effect reads safety/regulatory, and no action is recorded",
        )
        for r in rows
        if r.severity in HIGH_SEVERITY and _SAFETY_PATTERN.search(r.effect) and not r.action.strip()
    ]
    return compute(
        flags,
        method=(
            "blocking_flags = rows with severity in {9,10} AND effect text matching a safety/regulatory keyword "
            "AND action blank (rubric R-ANA-03 Fail line; R-WRAP-03 blocks project-close on any non-empty result)"
        ),
        input_data=[{"row_id": r.row_id, "severity": r.severity, "effect": r.effect, "action": r.action} for r in rows],
        assumptions_checked=["keyword match is a heuristic screen, not a certified safety/regulatory determination"],
    )


def compute_sorted_view(rows: list[FmeaRow]) -> Computed[list[str]]:
    ordered = sorted(rows, key=lambda r: (-r.severity, -r.rpn, r.row_id))
    return compute(
        [r.row_id for r in ordered],
        method=(
            "sorted_view = row_ids ordered severity desc, then rpn (severity*occurrence*detection) desc, tie-"
            "broken by row_id -- severity-first per rubric R-ANA-03 #3 (the RPN limitation: equal RPNs are not "
            "equal risks, and a lower-severity row can never outrank a higher-severity one here on RPN alone)"
        ),
        input_data=[{"row_id": r.row_id, "severity": r.severity, "rpn": r.rpn} for r in rows],
    )


class FmeaArtifact(ArtifactBase):
    tool_id: Literal["T-16"] = "T-16"

    rows: list[FmeaRow] = Field(min_length=1)

    # Reference data, never client-supplied -- unconditionally overwritten
    # below to this engine's own original wording (module docstring).
    anchors: FmeaAnchors | None = None

    # Server-computed, never hand-typed -- unconditionally replaced below.
    # Always non-None after validation; Optional only so a POST body can
    # omit them (Computed[...] isn't trivially default-constructible) --
    # an empty blocking_flags list is itself the honest "nothing to block"
    # state, not "nothing computed yet".
    blocking_flags: Computed[list[BlockingFlag]] | None = None
    sorted_view: Computed[list[str]] | None = None

    @model_validator(mode="after")
    def _recompute(self) -> "FmeaArtifact":
        ids = [r.row_id for r in self.rows]
        if len(ids) != len(set(ids)):
            raise ValueError("row_id values must be unique")
        self.anchors = _default_anchors()
        self.blocking_flags = compute_blocking_flags(self.rows)
        self.sorted_view = compute_sorted_view(self.rows)
        return self
