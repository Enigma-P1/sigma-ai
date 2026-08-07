"""T-02 prescore: total-matches-rows (the check named in the M1 brief),
plus period-consistency across rows (R-DEF-05's other buildable-now line).

total-matches-rows stays meaningful even though CopqRow.amount is a
computed_field the API can't hand-feed a wrong value into: a hand-edited
JSON file on disk could still carry a `total` that no longer matches its
`rows` after a manual tweak, and this is what catches that on load.
"""

from __future__ import annotations

from ..artifacts.copq import CopqArtifact
from .common import PrescoreResult

_RELATIVE_TOLERANCE = 1e-9


def run_copq_prescore(artifact: CopqArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []

    expected = sum(row.amount for row in artifact.rows)
    stored = artifact.total.value
    matches = abs(expected - stored) <= _RELATIVE_TOLERANCE * max(1.0, abs(expected))
    results.append(PrescoreResult(
        check_id="total_matches_rows",
        tool_id="T-02",
        status="pass" if matches else "flag",
        detail=(
            "stored total matches sum(quantity * rate) over rows" if matches
            else f"stored total {stored} != recomputed {expected}"
        ),
    ))

    periods = {row.period for row in artifact.rows}
    results.append(PrescoreResult(
        check_id="period_consistency",
        tool_id="T-02",
        status="pass" if len(periods) <= 1 else "flag",
        detail="all rows share one period" if len(periods) <= 1 else f"rows mix periods: {sorted(periods)}",
    ))

    return results
