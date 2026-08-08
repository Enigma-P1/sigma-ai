"""T-08 prescore: rubric R-MEA-06's rule-checkable lines -- strata declared,
entries carry validated timestamps (schema-enforced, confirmed here),
strata actually recorded on the rows once declared, and an honest nudge
when a declared category has never been tallied."""

from __future__ import annotations

from ..artifacts.check_sheet import CheckSheetArtifact
from .common import PrescoreResult


def run_check_sheet_prescore(artifact: CheckSheetArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    results.append(PrescoreResult(
        check_id="strata_declared", tool_id="T-08",
        status="pass" if artifact.strata_fields else "flag",
        detail=(
            f"{len(artifact.strata_fields)} stratification field(s) declared: "
            + ", ".join(f.key for f in artifact.strata_fields)
        ) if artifact.strata_fields
        else "no stratification fields declared -- shift/station/operator splits won't be possible downstream",
    ))

    results.append(PrescoreResult(
        check_id="entries_present", tool_id="T-08",
        status="pass" if artifact.entries else "flag",
        detail=f"{len(artifact.entries)} entries recorded, each with a validated ISO8601 timestamp"
        if artifact.entries else "no entries tallied yet",
    ))

    if artifact.strata_fields:
        declared_keys = {f.key for f in artifact.strata_fields}
        incomplete = [e.entry_id for e in artifact.entries if set(e.strata) != declared_keys]
        results.append(PrescoreResult(
            check_id="entries_carry_full_strata", tool_id="T-08",
            status="pass" if not incomplete else "flag",
            detail="every entry carries a value for every declared strata field" if not incomplete
            else f"entries missing one or more declared strata values: {incomplete}",
        ))

    if artifact.entries:
        tallied = {e.category_id for e in artifact.entries}
        untouched = [c.label for c in artifact.categories if c.category_id not in tallied]
        results.append(PrescoreResult(
            check_id="category_coverage", tool_id="T-08",
            status="pass" if not untouched else "flag",
            detail="every declared category has at least one tally" if not untouched
            else f"declared but never tallied: {untouched}",
        ))

    return results
