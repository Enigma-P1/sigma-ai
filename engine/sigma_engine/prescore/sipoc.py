"""T-04 prescore: process step-count range (rubric R-DEF-06 / matrix A-2 --
one declared range, 4-7 pass, 8-9 tolerated-but-flagged, outside 4-9
hard-flagged). This is the one Define-phase check that uses the three-tier
PrescoreResult status.
"""

from __future__ import annotations

from ..artifacts.sipoc import SipocArtifact
from .common import PrescoreResult

PASS_RANGE = range(4, 8)  # 4-7 inclusive
TOLERATED_RANGE = range(8, 10)  # 8-9 inclusive


def run_sipoc_prescore(artifact: SipocArtifact) -> list[PrescoreResult]:
    n = len(artifact.process_steps)
    if n in PASS_RANGE:
        status, detail = "pass", f"{n} steps is within the declared 4-7 range"
    elif n in TOLERATED_RANGE:
        status, detail = "flag", f"{n} steps is in the tolerated 8-9 band"
    else:
        status, detail = "hard_flag", f"{n} steps is outside the 4-9 range"
    return [PrescoreResult(check_id="step_count_range", tool_id="T-04", status=status, detail=detail)]
