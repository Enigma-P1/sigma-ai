"""T-02 COPQ / Benefit Calculator: category rows -> server-computed total.

Rubric R-DEF-05 Pass #1 is explicit: each bucket is "quantity x rate
computed by the tool -- no hand-typed totals anywhere." Rows therefore
never carry a settable amount field; `amount` is a Pydantic computed_field
(quantity * rate) so there is nothing for a hand-typed number to overwrite,
row or total. The grand total is stamped through provenance.compute() so
it carries the same input-hash/method/warnings contract as every other
computed result in the engine (PLAN §4.5).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase

Category = Literal["scrap", "rework", "overtime", "expediting", "lost_business", "custom"]


class CopqRow(BaseModel):
    category: Category
    custom_label: str | None = None
    quantity: float = Field(ge=0)
    rate: float = Field(ge=0)
    period: str = Field(min_length=1)  # e.g. "Q2 2026", "per month"
    basis: str = Field(min_length=1)  # e.g. "Q2 scrap log export", "estimate from operator interview"
    is_estimate: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def amount(self) -> float:
        return self.quantity * self.rate

    @model_validator(mode="after")
    def _custom_needs_label(self) -> "CopqRow":
        if self.category == "custom" and not (self.custom_label or "").strip():
            raise ValueError("custom_label is required when category is 'custom'")
        return self


class CopqArtifact(ArtifactBase):
    tool_id: Literal["T-02"] = "T-02"
    rows: list[CopqRow] = Field(min_length=1)
    total: Computed[float]


def compute_copq_total(rows: list[CopqRow]) -> Computed[float]:
    """Server-side COPQ total. The only supported way to produce the
    `total` field a CopqArtifact carries -- never hand-assemble one."""
    total_value = sum(row.amount for row in rows)
    return compute(
        total_value,
        method="copq_total = sum(quantity * rate per row)",
        input_data=[row.model_dump(mode="json") for row in rows],
        assumptions_checked=["each row's amount is quantity * rate, never hand-entered"],
    )
