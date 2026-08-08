"""T-23 5S Audit (scored): audit rounds scored 0-5 per S category with
photos, and a trend line across rounds (PLAN §4.1: "promoted from
explain-only ... the single most-digitized lean activity at SMB level").

`photos` reuses spaghetti.py's `FloorPlanRef` verbatim as `PhotoRef` --
same shape (image_id/source_filename/sha256/width_px/height_px), same
backing store (floorplan_images.py's FloorPlanImageStore, routes/
floorplans.py's existing upload endpoint -- no new store or route for 5S
photos, task brief's "photo refs via the floorplan-image store pattern").

`total` and `lowest_category` are per-round computed_field properties
(CopqRow.amount / FmeaRow.rpn's "nothing for a hand-typed number to
overwrite" pattern) -- simple same-row arithmetic needs no provenance
wrapper. `trend` is the artifact-level Computed[...] rollup (rubric
R-CTL-05 #3's "recurrence is real ... a trend line").

Score honesty (a 4 should look like the checklist's 4, spot-checked
against the photos) and uniform-scores-by-reflex are prescore/judgment
concerns (prescore/five_s.py) -- never schema rejections, this engine's
usual hard/soft split (PLAN §4.2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

from ..provenance import Computed, compute
from .base import ArtifactBase, validate_iso8601
from .spaghetti import FloorPlanRef as PhotoRef

FiveSCategory = Literal["sort", "set_in_order", "shine", "standardize", "sustain"]
FIVE_S_CATEGORIES: tuple[FiveSCategory, ...] = ("sort", "set_in_order", "shine", "standardize", "sustain")


class CategoryScore(BaseModel):
    category: FiveSCategory
    score: int = Field(ge=0, le=5)
    note: str = ""


class RecurrenceSchedule(BaseModel):
    """Rubric R-CTL-05 #3's first path to "recurrence is real" (the second
    path is >=2 existing trend points -- see prescore/five_s.py)."""

    cadence_note: str = Field(min_length=1)
    next_round_due: str | None = None

    @model_validator(mode="after")
    def _iso_if_present(self) -> "RecurrenceSchedule":
        if self.next_round_due is not None:
            validate_iso8601(self.next_round_due)
        return self


class AuditRound(BaseModel):
    round_id: str = Field(min_length=1)
    date: str
    area: str = Field(min_length=1)
    scores: list[CategoryScore]
    photos: list[PhotoRef] = Field(default_factory=list)
    # The action tied to THIS round's lowest-scoring category (rubric
    # R-CTL-05 #3: "the lowest-scoring category carries an action").
    improvement_action: str = ""
    improvement_action_owner: str = ""

    @model_validator(mode="after")
    def _covers_every_category_exactly_once(self) -> "AuditRound":
        validate_iso8601(self.date)
        cats = [s.category for s in self.scores]
        if sorted(cats) != sorted(FIVE_S_CATEGORIES) or len(cats) != len(FIVE_S_CATEGORIES):
            raise ValueError(f"scores must cover exactly the 5 categories {FIVE_S_CATEGORIES} once each, got {cats}")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> int:
        return sum(s.score for s in self.scores)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lowest_category(self) -> FiveSCategory:
        return min(self.scores, key=lambda s: (s.score, s.category)).category


class TrendPoint(BaseModel):
    round_id: str
    date: str
    area: str
    total: int
    per_category: dict[str, int]
    lowest_category: FiveSCategory


def compute_trend(rounds: list[AuditRound]) -> Computed[list[TrendPoint]]:
    ordered = sorted(rounds, key=lambda r: (r.date, r.round_id))
    points = [
        TrendPoint(
            round_id=r.round_id, date=r.date, area=r.area, total=r.total,
            per_category={s.category: s.score for s in r.scores}, lowest_category=r.lowest_category,
        )
        for r in ordered
    ]
    return compute(
        points,
        method=(
            "trend = audit rounds ordered by date then round_id, each point's total/per_category/lowest_category "
            "read straight off that round's own scores (rubric R-CTL-05 #3: recurrence made visible as a trend line)"
        ),
        input_data=[{"round_id": r.round_id, "date": r.date, "scores": [s.model_dump(mode="json") for s in r.scores]} for r in rounds],
    )


class FiveSArtifact(ArtifactBase):
    tool_id: Literal["T-23"] = "T-23"

    rounds: list[AuditRound] = Field(min_length=1)
    schedule: RecurrenceSchedule | None = None

    # Server-computed, never hand-typed -- unconditionally replaced below.
    trend: Computed[list[TrendPoint]] | None = None

    @model_validator(mode="after")
    def _unique_round_ids(self) -> "FiveSArtifact":
        ids = [r.round_id for r in self.rounds]
        if len(ids) != len(set(ids)):
            raise ValueError("round_id values must be unique")
        return self

    @model_validator(mode="after")
    def _recompute_trend(self) -> "FiveSArtifact":
        self.trend = compute_trend(self.rounds)
        return self
