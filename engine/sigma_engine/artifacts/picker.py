"""T-01 Project Picker: five intake criteria + full-DMAIC/PDCA/EXIT-01 routing.

Frozen routing rule (docs/traceability-matrix.md §4a, EXIT-01 trigger =
"any of the five intake criteria answered No"): a route of "full-DMAIC"
requires every criterion to be Yes; a route of "EXIT-01" requires at least
one criterion to be No. "PDCA" is legal either way -- PLAN §4.1's quick
path for small wins that don't warrant full rigor, regardless of which
criterion (if any) came back No. `route_is_consistent` is the single
source of truth for that rule: the schema validator below hard-rejects a
violation at construction, and prescore/picker.py's routing-consistency
check calls the same function so the two can never drift apart.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .base import ArtifactBase

Route = Literal["full-DMAIC", "PDCA", "EXIT-01"]


class IntakeCriterion(BaseModel):
    """One of the five intake criteria: a yes/no plus project-specific text."""

    answer: bool
    detail: str = Field(min_length=1)


def route_is_consistent(criteria: list[bool], route: Route) -> bool:
    any_no = not all(criteria)
    if route == "full-DMAIC":
        return not any_no
    if route == "EXIT-01":
        return any_no
    return True  # PDCA is legal regardless of the criteria answers.


class PickerArtifact(ArtifactBase):
    tool_id: Literal["T-01"] = "T-01"

    scope_narrow: IntakeCriterion
    measurable_outcome: IntakeCriterion
    data_obtainable: IntakeCriterion
    process_owner_engaged: IntakeCriterion
    business_impact_plausible: IntakeCriterion
    route: Route

    def criteria_answers(self) -> list[bool]:
        """The five criteria in a fixed order, for the routing rule."""
        return [
            self.scope_narrow.answer,
            self.measurable_outcome.answer,
            self.data_obtainable.answer,
            self.process_owner_engaged.answer,
            self.business_impact_plausible.answer,
        ]

    @model_validator(mode="after")
    def _route_matches_criteria(self) -> "PickerArtifact":
        if not route_is_consistent(self.criteria_answers(), self.route):
            raise ValueError(
                "route inconsistent with intake criteria answers: "
                f"route={self.route!r} criteria={self.criteria_answers()} "
                "(matrix §4a: any No means route must not be full-DMAIC)"
            )
        return self
