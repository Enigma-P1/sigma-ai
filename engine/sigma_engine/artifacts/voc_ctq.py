"""T-05 VoC -> CTQ Tree: statements -> needs -> CTQs, tree-linked child to
parent (PLAN §4.1). Every CTQ carries the tool's namesake check question --
"is this what the customer critically needs, or what the process finds
easy to measure?" -- as a required field, answered in the student's words
(rubric R-DEF-07 Pass #4). Referential integrity of the tree (does every
need_id/statement_id actually resolve?) is a prescore check, not a schema
validator -- see prescore/voc_ctq.py for why.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .base import ArtifactBase

Direction = Literal["higher_is_better", "lower_is_better", "target_is_best"]
StatementSource = Literal["interview", "complaint_log", "survey", "direct_observation", "other"]


class Customer(BaseModel):
    role: str = Field(min_length=1)  # e.g. "internal - QA reviewer", "external - end buyer"
    is_internal: bool


class VocStatement(BaseModel):
    statement_id: str = Field(min_length=1)
    customer_role: str = Field(min_length=1)
    text: str = Field(min_length=1)  # captured close to verbatim
    source: StatementSource
    source_detail: str = ""


class CustomerNeed(BaseModel):
    need_id: str = Field(min_length=1)
    statement_ids: list[str] = Field(min_length=1)  # >=1 parent statement
    text: str = Field(min_length=1)


class Ctq(BaseModel):
    ctq_id: str = Field(min_length=1)
    need_id: str = Field(min_length=1)  # parent need
    measure: str = Field(min_length=1)
    direction: Direction
    target: str | None = None
    critical_vs_easy_check: str = Field(min_length=1)


class VocCtqArtifact(ArtifactBase):
    tool_id: Literal["T-05"] = "T-05"

    customers: list[Customer] = Field(min_length=1)
    statements: list[VocStatement] = Field(min_length=1)
    needs: list[CustomerNeed] = Field(min_length=1)
    ctqs: list[Ctq] = Field(min_length=1)
    primary_ctq_id: str = Field(min_length=1)
    # R-DEF-07 Pass #5: the primary CTQ is the charter's primary metric, or
    # the mismatch is explained here. Self-contained field (no live charter
    # cross-check yet -- see build report).
    charter_metric_link: str = Field(min_length=1)
