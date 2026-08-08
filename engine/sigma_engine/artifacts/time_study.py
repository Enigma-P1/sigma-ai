"""T-09 Guided Time Study / Work Sampling artifact: work elements defined
first, cycles time each element in seconds, per-element stats (n, mean,
median, spread as SD + IQR, outliers via a stated 1.5xIQR fence rule) are
computed here -- never hand-typed, same "server recomputes unconditionally"
contract as MsaArtifact.result / SpaghettiArtifact.metrics. Outliers are
flagged, never dropped: an element's descriptive stats are always computed
over ALL of its recorded times (rubric R-MEA-04: "never silently deleted").
A cycle can still be struck from the record, but only with a logged,
non-empty reason (Cycle.deleted, an artifacts/base.py DeletionInfo) -- that
is a soft delete, not a silent one: the cycle stays on the artifact, and
only the computed stats/exports below stop counting it.
An optional work-sampling mode (interval observations tagged
working/waiting/moving/other) gets its own computed share-per-category.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..provenance import Computed, compute
from ..stats.constants import TIME_STUDY_IQR_FENCE_MULTIPLIER, TIME_STUDY_MIN_CYCLES_GUIDANCE
from ..stats.descriptive import DescriptiveStats, mean, median, quartiles, sample_sd
from .base import ArtifactBase, DeletionInfo, validate_iso8601

WorkSamplingCategory = Literal["working", "waiting", "moving", "other"]
WORK_SAMPLING_CATEGORIES: tuple[WorkSamplingCategory, ...] = ("working", "waiting", "moving", "other")


class WorkElement(BaseModel):
    element_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""


class ElementTime(BaseModel):
    element_id: str = Field(min_length=1)
    seconds: float = Field(ge=0)


class Cycle(BaseModel):
    """One timed repetition: >=1 element time (a cycle with none timed is
    not a cycle) plus an observer note -- the note is also where a flagged
    outlier's explanation lives (ElementStats.outliers points back at
    cycle_number, never a separate free-floating reason field).

    `deleted` is a soft-delete marker (rubric R-MEA-04): a mis-timed cycle
    stays on the artifact for the record, struck through in the UI, but is
    excluded from every computed stat below -- see _element_times_for's
    `c.deleted is None` filter. Never a hard removal from `cycles`."""

    cycle_number: int = Field(ge=1)
    element_times: list[ElementTime] = Field(min_length=1)
    observer_note: str = ""
    deleted: DeletionInfo | None = None

    @model_validator(mode="after")
    def _unique_element_ids_within_cycle(self) -> "Cycle":
        ids = [et.element_id for et in self.element_times]
        if len(ids) != len(set(ids)):
            raise ValueError(f"cycle {self.cycle_number}: element_id values must be unique within one cycle")
        return self


class IntervalObservation(BaseModel):
    """One work-sampling tick: what the operator was doing at this instant."""

    observation_id: str = Field(min_length=1)
    timestamp: str
    category: WorkSamplingCategory
    note: str = ""

    @field_validator("timestamp")
    @classmethod
    def _timestamp_is_iso8601(cls, v: str) -> str:
        return validate_iso8601(v)


class WorkSamplingShare(BaseModel):
    category: WorkSamplingCategory
    count: int
    share: float


class WorkSamplingSummary(BaseModel):
    total_observations: int
    shares: list[WorkSamplingShare]


class OutlierFlag(BaseModel):
    cycle_number: int
    seconds: float
    direction: Literal["low", "high"]
    fence_value: float
    reason: str


class ElementStats(BaseModel):
    element_id: str
    element_name: str
    n: int
    # None below n=2 -- sample_sd's own floor (stats/descriptive.py), the
    # same n>=2 requirement /stats/descriptive already enforces at the
    # route layer. Never fabricated at n<2.
    descriptive: DescriptiveStats | None
    outliers: list[OutlierFlag]
    below_recommended_cycles: bool
    cycle_count_note: str


# ---- Computed stats (this module's MsaArtifact/SpaghettiArtifact pattern) --


def _cycle_count_note(n: int) -> str:
    if n < TIME_STUDY_MIN_CYCLES_GUIDANCE:
        return f"{n} cycle{'s' if n != 1 else ''}; tool recommends >= {TIME_STUDY_MIN_CYCLES_GUIDANCE} -- treat spread as rough"
    return f"{n} cycles (meets the >= {TIME_STUDY_MIN_CYCLES_GUIDANCE} guidance)"


def _element_times_for(element_id: str, cycles: list[Cycle]) -> list[tuple[int, float]]:
    """[(cycle_number, seconds), ...] for one element, cycle-number order --
    a soft-deleted cycle (rubric R-MEA-04) is excluded here so it never
    enters n/mean/median/SD/IQR/outliers, even though it still exists on
    `cycles` itself (soft delete: the row stays, the stats don't see it)."""
    return [
        (c.cycle_number, et.seconds)
        for c in sorted(cycles, key=lambda c: c.cycle_number)
        if c.deleted is None
        for et in c.element_times
        if et.element_id == element_id
    ]


def _stats_for_element(element: WorkElement, cycles: list[Cycle]) -> ElementStats:
    pairs = _element_times_for(element.element_id, cycles)
    times = [seconds for _, seconds in pairs]
    n = len(times)
    descriptive: DescriptiveStats | None = None
    outliers: list[OutlierFlag] = []

    if n >= 2:
        q1, q3 = quartiles(times)
        iqr_value = q3 - q1
        lo = q1 - TIME_STUDY_IQR_FENCE_MULTIPLIER * iqr_value
        hi = q3 + TIME_STUDY_IQR_FENCE_MULTIPLIER * iqr_value
        descriptive = DescriptiveStats(
            n=n, mean=mean(times), sd=sample_sd(times), median=median(times),
            q1=q1, q3=q3, iqr=iqr_value, min=min(times), max=max(times),
        )
        for cycle_number, seconds in pairs:
            if seconds < lo:
                outliers.append(OutlierFlag(
                    cycle_number=cycle_number, seconds=seconds, direction="low", fence_value=lo,
                    reason=f"{seconds:g}s is below the lower fence Q1 - 1.5xIQR = {lo:g}s (Q1={q1:g}, Q3={q3:g}, IQR={iqr_value:g})",
                ))
            elif seconds > hi:
                outliers.append(OutlierFlag(
                    cycle_number=cycle_number, seconds=seconds, direction="high", fence_value=hi,
                    reason=f"{seconds:g}s is above the upper fence Q3 + 1.5xIQR = {hi:g}s (Q1={q1:g}, Q3={q3:g}, IQR={iqr_value:g})",
                ))

    return ElementStats(
        element_id=element.element_id, element_name=element.name, n=n, descriptive=descriptive,
        outliers=outliers, below_recommended_cycles=n < TIME_STUDY_MIN_CYCLES_GUIDANCE,
        cycle_count_note=_cycle_count_note(n),
    )


def compute_element_stats(elements: list[WorkElement], cycles: list[Cycle]) -> Computed[list[ElementStats]]:
    """Every declared element's stats, recomputed here and stamped once
    through provenance.compute() -- SpaghettiMetrics' "compute the whole
    stack once, stamp once" pattern, reused. Outliers are flagged, never
    excluded: n/mean/sd/median/IQR are computed over ALL of an element's
    recorded times, outlier or not (rubric R-MEA-04)."""
    stats_list = [_stats_for_element(el, cycles) for el in elements]
    return compute(
        stats_list,
        method=(
            "per-element n/mean/median/sample-SD(n-1, NIST SS1.3.5.6)/IQR (stats/descriptive.py) once n>=2; "
            f"outliers flagged via Tukey's 1.5xIQR inner fence (NIST/SEMATECH SS7.1.6 'mild outlier': "
            f"Q1-{TIME_STUDY_IQR_FENCE_MULTIPLIER}xIQR / Q3+{TIME_STUDY_IQR_FENCE_MULTIPLIER}xIQR), never dropped from "
            f"the stats; cycle-count guidance floor n>={TIME_STUDY_MIN_CYCLES_GUIDANCE} flagged (prescore), never "
            "enforced (schema)"
        ),
        input_data={
            "elements": [e.model_dump(mode="json") for e in elements],
            "cycles": [c.model_dump(mode="json") for c in cycles],
        },
    )


def compute_work_sampling_summary(observations: list[IntervalObservation]) -> Computed[WorkSamplingSummary] | None:
    """None when there are no observations yet (nothing to summarize) --
    the same "honest nothing yet" convention as SpaghettiArtifact.metrics."""
    if not observations:
        return None
    total = len(observations)
    counts = Counter(o.category for o in observations)
    shares = [
        WorkSamplingShare(category=cat, count=counts.get(cat, 0), share=counts.get(cat, 0) / total)
        for cat in WORK_SAMPLING_CATEGORIES
    ]
    result = WorkSamplingSummary(total_observations=total, shares=shares)
    return compute(
        result,
        method="work sampling: share per category = count / total observations, across the 4 fixed categories "
        "(working/waiting/moving/other), zero-filled for a category never observed",
        input_data=[o.model_dump(mode="json") for o in observations],
    )


# ---- Per-element CSV export (to_dataset, routes/time_study.py) ------------


def element_cycle_export_rows(artifact: "TimeStudyArtifact", element_id: str) -> tuple[list[str], list[dict[str, str]]]:
    """(header, rows) for one element's `to_dataset` action -- every
    recorded cycle time for this element, outliers included (flagged, never
    dropped, so T-13's own I-MR/normality reads see the real data). A
    soft-deleted cycle (rubric R-MEA-04) is excluded, same as
    _element_times_for -- the exported dataset stays consistent with the
    stats panel, never re-including a row the study owner struck out."""
    if element_id not in {e.element_id for e in artifact.elements}:
        raise ValueError(f"unknown element_id {element_id!r}")
    pairs = [
        (c.cycle_number, et.seconds, c.observer_note)
        for c in sorted(artifact.cycles, key=lambda c: c.cycle_number)
        if c.deleted is None
        for et in c.element_times
        if et.element_id == element_id
    ]
    if not pairs:
        raise ValueError(f"element {element_id!r} has no recorded cycle times yet -- nothing to export")
    header = ["cycle_number", "seconds", "observer_note"]
    rows = [{"cycle_number": str(cn), "seconds": str(secs), "observer_note": note} for cn, secs, note in pairs]
    return header, rows


def element_cycle_export_csv_bytes(artifact: "TimeStudyArtifact", element_id: str) -> bytes:
    """Same csv.DictWriter shape as check_sheet.py's export helper and
    datasets.py's own internal writer -- duplicated, not imported, per this
    codebase's module-private-helper convention (floorplan_images.py)."""
    header, rows = element_cycle_export_rows(artifact, element_id)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


class TimeStudyArtifact(ArtifactBase):
    tool_id: Literal["T-09"] = "T-09"

    # Elements are "defined first" (PLAN §4.1 T-09 row): >=1 required, and
    # every cycle's element_times can only reference a declared element_id
    # (validator below) -- the ordering is structural, not a UI convention.
    elements: list[WorkElement] = Field(min_length=1)
    cycles: list[Cycle] = Field(default_factory=list)
    interval_observations: list[IntervalObservation] = Field(default_factory=list)

    # Server-computed, never hand-typed -- unconditionally replaced below,
    # same contract as MsaArtifact.result / SpaghettiArtifact.metrics.
    element_stats: Computed[list[ElementStats]] | None = None
    work_sampling_summary: Computed[WorkSamplingSummary] | None = None

    @model_validator(mode="after")
    def _referential_integrity(self) -> "TimeStudyArtifact":
        element_ids = [e.element_id for e in self.elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("element_id values must be unique")
        element_id_set = set(element_ids)

        cycle_numbers = [c.cycle_number for c in self.cycles]
        if len(cycle_numbers) != len(set(cycle_numbers)):
            raise ValueError("cycle_number values must be unique")

        for cycle in self.cycles:
            for et in cycle.element_times:
                if et.element_id not in element_id_set:
                    raise ValueError(
                        f"cycle {cycle.cycle_number}: element_times references unknown element_id {et.element_id!r}"
                    )

        observation_ids = [o.observation_id for o in self.interval_observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation_id values must be unique")
        return self

    @model_validator(mode="after")
    def _recompute(self) -> "TimeStudyArtifact":
        self.element_stats = compute_element_stats(self.elements, self.cycles)
        self.work_sampling_summary = compute_work_sampling_summary(self.interval_observations)
        return self
