"""T-24 Standard Work / SOP: the improved method written down so it
survives the author (PLAN §4.1). A plan a person writes, like
DataCollectionPlanArtifact/PilotPlanArtifact -- no Computed[...] field
lives here.

Steps seed from the T-06 process map's current step list (or hand-entered)
-- `source_step_ref` is fmea.py's `process_step_ref` idiom, an unchecked
cross-reference the desktop resolves; the actual copy-in is a desktop
action (PilotPlanForm's T-18 prefill precedent), not engine computation.
`changed_from_prior` is rubric R-CTL-06 #1's "the points that changed from
the old method highlighted," schema-present on every step (defaults
False) so a fresh, never-superseded SOP can still validate cleanly.

`version`/`owner`/`effective_date` are schema-hard (rubric R-CTL-06 #2:
"version, owner, and date fields are set" is a Pass condition stated
flatly, not a graded content-quality judgment call like the rest of this
rubric item) -- unlike a control-plan owner, there is no "theater" framing
here to preserve by staying schema-loose.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .base import ArtifactBase, validate_iso8601


class SopStep(BaseModel):
    step_id: str = Field(min_length=1)
    order: int = Field(ge=1)
    action: str = Field(min_length=1)  # what a qualified-but-new person does
    standard: str = Field(min_length=1)  # what right looks like
    changed_from_prior: bool = False
    source_step_ref: str | None = None  # unchecked cross-ref -> T-06 ProcessMapArtifact step_id
    note: str = ""


class ChangeLogEntry(BaseModel):
    version: int = Field(ge=1)
    at: str
    note: str = Field(min_length=1)

    @model_validator(mode="after")
    def _iso(self) -> "ChangeLogEntry":
        validate_iso8601(self.at)
        return self


class StandardWorkArtifact(ArtifactBase):
    tool_id: Literal["T-24"] = "T-24"

    title: str = Field(min_length=1)
    version: int = Field(ge=1, default=1)
    owner: str = Field(min_length=1)
    effective_date: str
    # "If an older instruction existed, the SOP names what it supersedes"
    # (rubric #2) -- None when this is the first version.
    supersedes: str | None = None
    seeded_from_process_map_id: str | None = None  # unchecked cross-ref -> T-06 artifact_id
    linked_control_plan_id: str | None = None  # unchecked cross-ref -> T-22 artifact_id (the training block that points here)
    steps: list[SopStep] = Field(min_length=1)
    change_log: list[ChangeLogEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate(self) -> "StandardWorkArtifact":
        validate_iso8601(self.effective_date)
        step_ids = [s.step_id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_id values must be unique")
        if self.supersedes is not None and not self.supersedes.strip():
            raise ValueError("supersedes, if given, must name what it supersedes (non-empty) -- omit the field entirely if there is no prior instruction")
        return self
