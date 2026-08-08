"""T-08 Check Sheet / Tally artifact: categories declared up front, strata
fields declared up front (a free-schema key list -- e.g. shift, station),
then entries tally a category at a caller-supplied ISO timestamp with the
current strata selections + an optional note.

No computed statistics live here -- counting/sorting/vital-few is T-14's
job (stats/pareto.py) over the *exported dataset* this module's CSV-builder
produces for routes/check_sheet.py's `to_dataset` action, which reuses
datasets.py's DatasetStore exactly like a real upload would (never a
parallel path) -- the zero-re-entry contract made engine-side (rubric
R-MEA-06 #3: "the collection artifact IS the dataset [Pareto] runs on")."""

from __future__ import annotations

import csv
import io
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import ArtifactBase, DeletionInfo, validate_iso8601


class CheckSheetCategory(BaseModel):
    category_id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class StrataFieldDef(BaseModel):
    """One declared stratification column (e.g. key="shift", label="Shift").
    Entries below carry values keyed by `key`, never a key that wasn't
    declared here -- CheckSheetArtifact._referential_integrity enforces it."""

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)


class CheckSheetEntry(BaseModel):
    """One tally tap: which category, when (caller-supplied ISO8601 --
    never generated server-side, base.py's validate_iso8601 pattern, same
    as every other artifact's timestamps), the strata values in effect at
    tap time, and an optional note.

    `deleted` is a soft-delete marker (rubric R-MEA-04's "logged reason"
    rule, generalized to this tool too): a mis-tapped entry stays on the
    artifact, struck through in the UI, but is excluded from the exported
    dataset check_sheet_export_rows builds -- the same "row stays, stats
    don't see it" contract as time_study.py's Cycle.deleted."""

    entry_id: str = Field(min_length=1)
    category_id: str = Field(min_length=1)
    timestamp: str
    strata: dict[str, str] = Field(default_factory=dict)
    note: str = ""
    deleted: DeletionInfo | None = None

    @field_validator("timestamp")
    @classmethod
    def _timestamp_is_iso8601(cls, v: str) -> str:
        return validate_iso8601(v)


class CheckSheetArtifact(ArtifactBase):
    tool_id: Literal["T-08"] = "T-08"

    # A check sheet needs >=1 category to mean anything (categories are
    # "defined up front," PLAN §4.1 T-08 row); entries default empty --
    # that's the honest "categories set up, nothing tallied yet" state.
    categories: list[CheckSheetCategory] = Field(min_length=1)
    strata_fields: list[StrataFieldDef] = Field(default_factory=list)
    entries: list[CheckSheetEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def _referential_integrity(self) -> "CheckSheetArtifact":
        cat_ids = [c.category_id for c in self.categories]
        if len(cat_ids) != len(set(cat_ids)):
            raise ValueError("category_id values must be unique")
        cat_labels = [c.label for c in self.categories]
        if len(cat_labels) != len(set(cat_labels)):
            raise ValueError("category labels must be unique -- to_dataset exports the Pareto category column by label")
        cat_id_set = set(cat_ids)

        strata_keys = [f.key for f in self.strata_fields]
        if len(strata_keys) != len(set(strata_keys)):
            raise ValueError("strata field keys must be unique")
        strata_key_set = set(strata_keys)

        entry_ids = [e.entry_id for e in self.entries]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("entry_id values must be unique")

        for entry in self.entries:
            if entry.category_id not in cat_id_set:
                raise ValueError(f"entry {entry.entry_id!r} references unknown category_id {entry.category_id!r}")
            unknown = set(entry.strata) - strata_key_set
            if unknown:
                raise ValueError(f"entry {entry.entry_id!r} carries undeclared strata key(s) {sorted(unknown)!r}")
        return self


def check_sheet_export_rows(artifact: CheckSheetArtifact) -> tuple[list[str], list[dict[str, str]]]:
    """(header, rows) for `to_dataset`: one row per LIVE entry (a
    soft-deleted one -- entry.deleted, rubric R-MEA-04 -- is excluded here
    exactly like a deleted time-study cycle is excluded from element
    stats; it stays in artifact.entries, just not in what Pareto counts),
    `category` as the human-readable label (unique, enforced above) so
    Pareto's category column needs no id -> label join downstream. Sorted
    by timestamp so the exported dataset reads as an event log, not
    tap-entry order."""
    live_entries = [e for e in artifact.entries if e.deleted is None]
    if not live_entries:
        raise ValueError("this check sheet has no entries yet -- nothing to export")
    label_by_id = {c.category_id: c.label for c in artifact.categories}
    strata_keys = [f.key for f in artifact.strata_fields]
    header = ["category", "timestamp", *strata_keys, "note"]
    rows = [
        {
            "category": label_by_id[e.category_id],
            "timestamp": e.timestamp,
            **{k: e.strata.get(k, "") for k in strata_keys},
            "note": e.note,
        }
        for e in sorted(live_entries, key=lambda e: e.timestamp)
    ]
    return header, rows


def check_sheet_export_csv_bytes(artifact: CheckSheetArtifact) -> bytes:
    """Same shape as datasets.py's own internal CSV writer -- duplicated
    rather than imported since that one is module-private (same call
    floorplan_images.py's _atomic_write makes about datasets.py's)."""
    header, rows = check_sheet_export_rows(artifact)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")
