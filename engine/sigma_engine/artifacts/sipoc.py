"""T-04 SIPOC: five columns, modeled as three schema-paired lists.

Supplier<->input and output<->customer pairing (PLAN §4.1) is enforced by
construction, not by convention: each pair is one row, so a supplier can
never be entered without its input, or an output without its customer.
Process-step altitude (4-7 ideal, 8-9 tolerated, outside 4-9 hard-flagged --
rubric R-DEF-06 / matrix A-2) is a content-quality read, not a structural
one, so it lives in prescore/sipoc.py rather than as a schema length bound.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .base import ArtifactBase


class SupplierInputPair(BaseModel):
    supplier: str = Field(min_length=1)
    input: str = Field(min_length=1)


class ProcessStep(BaseModel):
    step_number: int = Field(ge=1)
    description: str = Field(min_length=1)


class OutputCustomerPair(BaseModel):
    output: str = Field(min_length=1)
    customer: str = Field(min_length=1)


class SipocArtifact(ArtifactBase):
    tool_id: Literal["T-04"] = "T-04"

    supplier_input_pairs: list[SupplierInputPair] = Field(min_length=1)
    process_steps: list[ProcessStep] = Field(min_length=1)
    output_customer_pairs: list[OutputCustomerPair] = Field(min_length=1)
    # The process column's start/end, for the (deferred -- see build report)
    # cross-check against the charter's scope in/out.
    scope_start: str = Field(min_length=1)
    scope_end: str = Field(min_length=1)
