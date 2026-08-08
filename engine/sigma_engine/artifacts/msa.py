"""T-12 Measurement Check artifact: continuous (test/retest repeatability%)
or attribute (two-rater kappa) study design + readings, with the result
always server-recomputed from the stored readings -- exactly
CopqArtifact's "no hand-typed totals anywhere" pattern (artifacts/copq.py),
applied here to `result`/`verdict` instead of `total` (rubric R-MEA-07's
"verdict recorded" pre-score line): never something a client, or a hand-
edited on-disk JSON file, can set independently of the data.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..stats import msa as msa_mod
from .base import ArtifactBase


class ContinuousItemRow(BaseModel):
    """One item's repeat readings (>=2 slots; a null slot is a missing/
    invalid repeat -- msa.py excludes it from s_repeat and logs the
    exclusion, it is never silently treated as zero)."""

    item_id: str = Field(min_length=1)
    readings: list[float | None] = Field(min_length=2)


class AttributeJudgmentRow(BaseModel):
    """One item's two-rater pass/fail judgment (attribute path)."""

    item_id: str = Field(min_length=1)
    rater_a: bool
    rater_b: bool


class MsaArtifact(ArtifactBase):
    tool_id: Literal["T-12"] = "T-12"

    data_type: Literal["continuous", "attribute"]
    # Single-operator test/retest design (matrix §4a: "same operator, same
    # procedure") -- who ran the study, required on both paths.
    operator: str = Field(min_length=1)

    # Continuous-only study-design fields (left at their defaults on an
    # attribute-typed artifact).
    gauge_name: str | None = None
    gauge_increment: float | None = None
    usl: float | None = None
    lsl: float | None = None
    continuous_items: list[ContinuousItemRow] = Field(default_factory=list)

    # Attribute-only.
    attribute_items: list[AttributeJudgmentRow] = Field(default_factory=list)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as CopqArtifact.total (artifacts/copq.py).
    result: msa_mod.MsaResult | None = None

    @model_validator(mode="after")
    def _recompute_result(self) -> "MsaArtifact":
        if self.data_type == "continuous":
            if self.gauge_increment is None or self.gauge_increment <= 0:
                raise ValueError("a continuous study requires gauge_increment > 0")
            if not self.continuous_items:
                raise ValueError("a continuous study requires at least one item")
            items = [msa_mod.ItemRepeats(item_id=r.item_id, readings=tuple(r.readings)) for r in self.continuous_items]
            self.result = msa_mod.run_continuous_msa(items, gauge_increment=self.gauge_increment, usl=self.usl, lsl=self.lsl)
        else:
            if not self.attribute_items:
                raise ValueError("an attribute study requires at least one item")
            ratings = [msa_mod.AttributeRating(item_id=r.item_id, rater_a=r.rater_a, rater_b=r.rater_b) for r in self.attribute_items]
            self.result = msa_mod.run_attribute_msa(ratings)
        return self
