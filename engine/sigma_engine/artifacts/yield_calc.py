"""T-10 Yield Calculator (FPY/RTY + DPMO): a calculator over counts, no
dataset needed. Two independent blocks:

1. Process-steps table (>=1 step, ordered -- list order IS the process
   order; no separate step-number field, same "no id, no explicit order
   field" convention as artifacts/copq.py's CopqRow list). Each step
   states units_in and first_pass_correct -- the ONE input convention
   this tool uses (task brief: "pick ONE input convention, make the
   other derived"). defective_units_at_step is ALWAYS derived, never a
   second raw input, so the two numbers can never drift out of sync with
   each other. Named defective_units_at_step, not "defects_at_step": the
   raw input this tool counts is defect-free UNITS (first_pass_correct),
   so the derived count is defective UNITS too -- a unit that failed is
   one defective, no matter how many things were wrong with it. "Defects"
   (a count that can exceed 1 per unit) is a different, EXIT-11-named
   quantity this tool never asks for (matrix VI.A.3's defectives-vs-
   defects split, the same one control_chart.py's p-chart selector
   enforces) -- critic-confirmed defect: the old field name conflated them.

   Why first_pass_correct and not defects as the raw input: it is the
   quantity a Green Belt actually tallies on a shop floor (good units vs
   not, the same counting habit T-08's check sheet already teaches), and
   it is the one named first in the matrix/brief's own phrasing.

   fpy_at_step is the DIRECT observed ratio, first_pass_correct / units_in
   -- exactly the counted quantity rubric R-MEA-09 #2 asks for ("computed
   from good/rework/scrap counts"), not a modeled estimate on top of it.
   This tool used to run fpy_at_step through the Poisson-yield model
   (FPY = e^-DPU, stats/sigma_level.py's fpy_from_dpu/dpu) -- a model
   layered on top of a directly-counted quantity, and one that always
   flatters the direct ratio (e^-DPU > first_pass_correct/units_in for any
   DPU > 0 up to the point both round to 1). Critic-confirmed defect,
   fixed here: the DPU-driven estimate is a legitimate SEPARATE convention
   (stats/sigma_level.py's own documented use, "the estimate used when
   rolling several steps' yields together" from a DEFECT-count input) but
   it is not this tool's convention, because this tool's raw input was
   never a defect count -- it is a directly observed pass/fail tally, and
   direct counts get a direct ratio, matching the standard DMAIC.io-/
   Qualica-style definition of a step's throughput yield (matrix II.E.1).

   RTY exists only under the explicit serial assumption: `steps_in_series`
   is a required field with no default (the same "no silent default on a
   claim-bearing boolean" convention as T-11's operational-definition
   confirmation and T-13's operational_definition_ok). RTY is computed --
   and only computed -- when steps_in_series is True; a non-serial
   project gets rty_result=None, never a silently-produced rollup number
   the serial-product math doesn't actually support.

   Sanity constraints enforced, and one deliberately NOT enforced: units_in
   > 0 and 0 <= first_pass_correct <= units_in are schema-hard. A later
   step's units_in is NOT constrained against the prior step's
   first_pass_correct/defective_units_at_step -- real lines rework and
   scrap units between steps, so a step can legitimately receive more
   units than the previous step "passed" (rework replenishing the line) or
   fewer (units scrapped outright before reaching this step). Each step's
   FPY is computed from its own entering units only, independent of its
   neighbors, and RTY is the product of those independently-computed
   per-step FPYs -- exactly the standard definition the matrix cites, not
   a stricter one invented for this tool.

2. DPMO block (optional -- None on an artifact that only wants the steps
   table): defects, units, opportunities_per_unit (default 1.0, "one
   opportunity: the unit itself"). DPMO and sigma level reuse
   dpmo_from_defects() and compute_sigma_level() verbatim -- the same
   frozen 1.5-sigma-shift convention, always labeled, that stats/
   sigma_level.py and T-13's baseline already carry (matrix §4a / III.F.4).

   Opportunity-inflation honesty guard (rubric R-MEA-09's "reported
   honestly" framing, and the classic DPMO game this tool must not enable:
   inflating opportunities to flatter sigma): opportunities_per_unit > 1
   is schema-hard-blocked unless opportunity_justification is non-empty --
   the same shape as artifacts/copq.py's "custom category requires a
   label" model_validator. This is a floor, not the whole guard:
   prescore/yield_calc.py adds the part a bare non-empty check can't --
   screening the justification text itself for a placeholder non-answer.

Every artifact-level computed number (rty_result, dpmo_result) is a
Computed[...] provenance object, unconditionally recomputed on every
validation -- artifacts/copq.py's CopqArtifact.total pattern, applied here
to two independent results instead of one. Per-step defective_units_at_step/
fpy_at_step are lightweight computed_field properties (CopqRow.amount's
pattern): pure functions of sibling fields on that same step, no separate
provenance object needed per row, same as every other per-row computed
number in this engine (CopqRow.amount, FmeaRow.rpn).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

from ..provenance import Computed, compute
from ..stats.sigma_level import (
    SigmaLevelResult,
    compute_sigma_level,
    dpmo_from_defects,
    rty,
)
from .base import ArtifactBase


class YieldStep(BaseModel):
    """One process step. units_in and first_pass_correct are the raw
    inputs (the one input convention this tool uses); defective_units_at_step
    and fpy_at_step are always derived, never independently settable -- a
    client posting e.g. a `fpy_at_step` value in a step dict has nothing to
    overwrite (computed_field), the same contract as CopqRow.amount."""

    name: str = Field(min_length=1)
    units_in: float = Field(gt=0)
    first_pass_correct: float = Field(ge=0)

    @model_validator(mode="after")
    def _first_pass_correct_within_units_in(self) -> "YieldStep":
        if self.first_pass_correct > self.units_in:
            raise ValueError(
                f"step {self.name!r}: first_pass_correct ({self.first_pass_correct}) cannot exceed "
                f"units_in ({self.units_in})"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def defective_units_at_step(self) -> float:
        """Units that were NOT first-pass-correct -- a count of defective
        UNITS (pass/fail), not "defects" (a count that can exceed 1 per
        unit, matrix VI.A.3's EXIT-11 distinction). Named accordingly:
        the old name (defects_at_step) conflated the two."""
        return self.units_in - self.first_pass_correct

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fpy_at_step(self) -> float:
        """Direct observed first-pass yield: first_pass_correct / units_in
        -- the good/rework/scrap COUNT ratio rubric R-MEA-09 #2 asks for,
        computed straight from this step's own raw inputs, no model layered
        on top (this tool no longer runs its per-step FPY through the
        Poisson-yield e^-DPU estimate -- that convention needs a defect
        COUNT input, which this tool's raw input, a pass/fail unit tally,
        never was; critic-confirmed defect, fixed here)."""
        return self.first_pass_correct / self.units_in


class DpmoBlock(BaseModel):
    """Independent of the steps table: a defect-count DPMO/sigma-level
    calculation. opportunities_per_unit >= 1 -- an "opportunity" is a
    chance for a defect, and a unit always has at least the one chance of
    being defective itself, so a fractional-opportunity count under 1
    isn't a real quantity in this system. Default 1.0: "one opportunity,
    the unit itself," the honest floor with nothing to justify."""

    defects: float = Field(ge=0)
    units: float = Field(gt=0)
    opportunities_per_unit: float = Field(default=1.0, ge=1.0)
    # Required non-empty the moment opportunities_per_unit > 1 (validator
    # below): naming WHAT the extra opportunities are, so a reader can
    # judge whether the count is honest or inflated to flatter sigma.
    opportunity_justification: str = Field(default="")
    apply_sigma_shift: bool = Field(default=True)

    @model_validator(mode="after")
    def _opportunity_inflation_guard(self) -> "DpmoBlock":
        if self.opportunities_per_unit > 1 and not self.opportunity_justification.strip():
            raise ValueError(
                "opportunities_per_unit > 1 requires a non-empty opportunity_justification naming what the "
                "extra opportunities are -- the classic DPMO game is inflating opportunities to flatter sigma "
                "(rubric R-MEA-09). This is the schema-level floor; prescore/yield_calc.py additionally screens "
                "the justification text itself for a placeholder non-answer."
            )
        return self


def compute_rty_result(steps: list[YieldStep]) -> Computed[float]:
    """RTY = product of each step's own FPY (rty(), reused verbatim from
    stats/sigma_level.py) -- the standard rolled-throughput-yield rollup.
    Callers only invoke this once the artifact has confirmed the steps run
    in series (YieldCalcArtifact._recompute below is the only caller in
    this codebase)."""
    value = rty([s.fpy_at_step for s in steps])
    return compute(
        value,
        method=(
            "RTY = product(FPY_i for i in steps), FPY_i = first_pass_correct_i / units_in_i (direct observed "
            "ratio, not a modeled estimate -- rubric R-MEA-09 #2 'computed from good/rework/scrap counts'; "
            "rty() reused verbatim from stats/sigma_level.py) -- computed only under the artifact's explicit "
            "steps_in_series=true"
        ),
        input_data=[s.model_dump(mode="json") for s in steps],
        assumptions_checked=[
            "steps_in_series is true on this artifact -- RTY is a serial-line rollup and is never computed "
            "or claimed otherwise (matrix II.E.1)",
            "each step's FPY is computed from its own entering units only, independent of neighboring steps -- "
            "a step's units_in is not constrained against the prior step's output, since real lines rework/scrap "
            "units between steps",
        ],
    )


def compute_dpmo_result(block: DpmoBlock) -> Computed[SigmaLevelResult]:
    """DPMO (dpmo_from_defects, reused verbatim) feeding straight into
    compute_sigma_level -- the same frozen 1.5-sigma-shift convention,
    always labeled, that stats/sigma_level.py and T-13's baseline already
    carry (matrix §4a / III.F.4). No math is reimplemented here; this
    function only wires DpmoBlock's fields into the two already-tested
    house functions."""
    dpmo_value = dpmo_from_defects(block.defects, block.units, block.opportunities_per_unit)
    return compute_sigma_level(dpmo_value, apply_shift=block.apply_sigma_shift)


class YieldCalcArtifact(ArtifactBase):
    tool_id: Literal["T-10"] = "T-10"

    steps: list[YieldStep] = Field(min_length=1)
    # Required, no default -- an explicit claim, not an assumed one (same
    # convention as T-11's operational-definition confirmation and T-13's
    # operational_definition_ok): RTY is only computed/claimed under it.
    steps_in_series: bool
    dpmo_block: DpmoBlock | None = None

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as CopqArtifact.total. None is the honest "not
    # applicable" state (steps_in_series=false, or no dpmo_block), not a
    # missing computation.
    rty_result: Computed[float] | None = None
    dpmo_result: Computed[SigmaLevelResult] | None = None

    @model_validator(mode="after")
    def _recompute(self) -> "YieldCalcArtifact":
        self.rty_result = compute_rty_result(self.steps) if self.steps_in_series else None
        self.dpmo_result = compute_dpmo_result(self.dpmo_block) if self.dpmo_block is not None else None
        return self
