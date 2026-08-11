"""T-35 Gage R&R artifact — the saved form of a full crossed study.

Sits alongside T-12 rather than replacing it. T-12 is the narrow
single-operator check a Green Belt can run in an afternoon and is honest
about what it cannot see; this is the full variance-decomposed study, and
it is what a quality engineer means by "Gage R&R".

`result` is server-computed and unconditionally replaced on validate --
CopqArtifact.total's contract. A client cannot post a flattering %GRR, and
a hand-edited project.json cannot leave a stale one behind, because the
value is re-derived from the readings before anyone sees it.

Readings are stored as a flat list of (part, operator, value) rather than
a nested grid on purpose. A grid has to encode "which row is which part" in
its shape, and every transposition bug in a measurement study comes from
exactly that. Labels travel with the reading.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..stats import gage_rr as gage_rr_mod
from .base import ArtifactBase


class GageRRReading(BaseModel):
    """One reading in the study."""

    part: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: float


class GageRRArtifact(ArtifactBase):
    tool_id: Literal["T-35"] = "T-35"

    gauge_name: str | None = None
    # Tolerance width (USL - LSL). Optional: a study can be judged against
    # study variation alone, but %tolerance is the more useful number when a
    # spec exists, because it answers "can this gauge police the spec".
    tolerance: float | None = None
    readings: list[GageRRReading] = Field(default_factory=list)
    # None lets the engine decide by the significance test; True/False force
    # the model, which a caller reproducing a published example needs.
    pool_interaction: bool | None = None

    # Server-computed, never hand-typed.
    result: gage_rr_mod.GageRRResult | None = None
    # An invalid DESIGN is not an invalid artifact: a half-entered study
    # must still save, or the tool would refuse to let anyone build one up
    # over two shifts. The reason is carried instead of raising.
    design_error: str | None = None

    @model_validator(mode="after")
    def _recompute(self) -> "GageRRArtifact":
        measurements = [
            gage_rr_mod.Measurement(part=r.part, operator=r.operator, value=r.value) for r in self.readings
        ]
        try:
            self.result = gage_rr_mod.compute_gage_rr(
                measurements, tolerance=self.tolerance, pool_interaction=self.pool_interaction
            )
            self.design_error = None
        except gage_rr_mod.GageRRError as exc:
            self.result = None
            self.design_error = str(exc)
        return self
