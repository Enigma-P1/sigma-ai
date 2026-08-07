"""T-03 Project Charter: problem statement, SMART goal, scope, team, timeline,
business impact, and the A-4 key-risks-&-mitigations block (matrix §5a).

Content-quality issues (solution-shaped language, a placeholder owner name,
a missing guardrail metric) are prescore *flags*, not schema rejections --
PLAN §4.2's hard-guard line is "the math/logic would be wrong," and none of
those are. What the schema does hard-require are the fields a charter is
structurally meaningless without: a named process owner, non-empty scope,
at least one team member and one timeline milestone. See prescore/charter.py
for the flagged-not-rejected checks.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .base import ArtifactBase, validate_iso8601


class Magnitude(BaseModel):
    """Number + unit + period (rubric R-DEF-02). unit/period may arrive
    empty -- that's a prescore flag (magnitude_pattern), not a rejection."""

    number: float
    unit: str = ""
    period: str = ""


class ProblemStatement(BaseModel):
    what: str = Field(min_length=1)
    where: str = Field(min_length=1)
    when: str = Field(min_length=1)
    magnitude: Magnitude


class SmartGoal(BaseModel):
    statement: str = Field(min_length=1)  # the SMART sentence, student's words
    metric_name: str = Field(min_length=1)
    baseline_value: float | None = None
    target_value: float
    unit: str = Field(min_length=1)
    target_date: str
    consequential_metrics: list[str] = Field(default_factory=list)

    @field_validator("target_date")
    @classmethod
    def _target_date_is_iso8601(cls, v: str) -> str:
        return validate_iso8601(v)


class ScopeBlock(BaseModel):
    in_scope: str = Field(min_length=1)
    out_scope: str = Field(min_length=1)


class TeamMember(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)


class TimelineMilestone(BaseModel):
    name: str = Field(min_length=1)
    date: str

    @field_validator("date")
    @classmethod
    def _date_is_iso8601(cls, v: str) -> str:
        return validate_iso8601(v)


class BusinessImpact(BaseModel):
    amount: float
    unit: str = Field(min_length=1)  # "dollars" | "hours" | ...
    basis: str = Field(min_length=1)  # e.g. "Q2 actuals x 4"


class RiskRow(BaseModel):
    """One row of the A-4 key-risks-&-mitigations block (matrix §5a)."""

    risk: str = Field(min_length=1)
    likelihood: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    mitigation: str = Field(min_length=1)
    owner: str = Field(min_length=1)


class CharterArtifact(ArtifactBase):
    tool_id: Literal["T-03"] = "T-03"

    problem_statement: ProblemStatement
    goal: SmartGoal
    scope: ScopeBlock
    team: list[TeamMember] = Field(min_length=1)
    process_owner: TeamMember
    timeline: list[TimelineMilestone] = Field(min_length=1)
    business_impact: BusinessImpact
    # A-4: risks may start empty (a charter-in-progress); prescore flags an
    # empty block rather than the schema rejecting it (PLAN §4.2 soft/hard
    # split -- an empty risk list isn't a wrong number, it's thin content).
    risks: list[RiskRow] = Field(default_factory=list)
