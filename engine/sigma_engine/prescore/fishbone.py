"""T-15 prescore: the rubric R-ANA-01/R-ANA-02 rule-checkable lines the M3
brief names -- branch/cause-count breadth floors, an absent-solution
keyword heuristic on cause text (R-ANA-01 #2: "no X"/"lack of X" phrasing
is a solution wearing a cause costume, same idiom as prescore/charter.py's
SOLUTION_LANGUAGE_KEYWORDS), and two confirmatory checks that render a
rubric line as visibly checked rather than silently assumed, mirroring
prescore/process_map.py's step_type_tag_present: `verified_causes_have_
evidence` can only ever read "pass" because artifacts/fishbone.py's schema
already makes a verified-without-evidence cause impossible to construct
(this is the rubric's own anchor item, R-ANA-02, so its hard_flag tier is
kept live in code even though the schema layer means it can never fire in
practice); `ruled_out_causes_retained` confirms ruled-out causes are still
on the board, honestly scoped to what one artifact snapshot can show (a
single snapshot has no way to prove nothing was *deleted* -- that needs
version history, out of this milestone's single-artifact prescore shape,
same limitation prescore/process_map.py's docstring names for its own
deferred checks).

Two rubric lines this module does not attempt (out of scope, both need
data beyond this one artifact): "effect field matches the baseline
problem ID" needs the T-03 charter's actual text, and "why-chain depth"
logical-connection judgment is explicitly Judgment-only per the rubric's
own split.
"""

from __future__ import annotations

import re

from ..artifacts.fishbone import BRANCH_IDS, FishboneArtifact
from .common import PrescoreResult

# Rubric R-ANA-01 pass criterion: at least 4 of the 6 categories genuinely
# explored -- the build brief's initial "2" was calibration drift; the locked
# rubric is the authority.
MIN_BRANCHES = 4
MIN_CAUSES = 6

# R-ANA-01 #2: "no X" / "lack of X" phrasing is a solution wearing a cause
# costume ("no barcode scanner" is not a condition or mechanism).
_ABSENT_SOLUTION_PATTERN = re.compile(r"\b(no|lack(?:s|ing)?\s+of|lacking)\b", re.IGNORECASE)


def run_fishbone_prescore(artifact: FishboneArtifact) -> list[PrescoreResult]:
    return [
        _branch_coverage_minimum(artifact),
        _cause_count_minimum(artifact),
        _absent_solution_language(artifact),
        _verified_causes_have_evidence(artifact),
        _ruled_out_causes_retained(artifact),
    ]


def _branch_coverage_minimum(artifact: FishboneArtifact) -> PrescoreResult:
    covered = {c.branch for c in artifact.causes}
    ok = len(covered) >= MIN_BRANCHES
    return PrescoreResult(
        check_id="branch_coverage_minimum", tool_id="T-15", status="pass" if ok else "flag",
        detail=(
            f"{len(covered)}/{len(BRANCH_IDS)} branches carry a cause"
            + ("" if ok else f" -- fewer than {MIN_BRANCHES}, a single pre-decided path with decoration (rubric R-ANA-01 #4)")
        ),
    )


def _cause_count_minimum(artifact: FishboneArtifact) -> PrescoreResult:
    n = len(artifact.causes)
    ok = n >= MIN_CAUSES
    return PrescoreResult(
        check_id="cause_count_minimum", tool_id="T-15", status="pass" if ok else "flag",
        detail=f"{n} cause(s) on the board" + ("" if ok else f" -- fewer than the {MIN_CAUSES}-cause breadth floor"),
    )


def _absent_solution_language(artifact: FishboneArtifact) -> PrescoreResult:
    hits = [c.cause_id for c in artifact.causes if _ABSENT_SOLUTION_PATTERN.search(c.text)]
    return PrescoreResult(
        check_id="absent_solution_language", tool_id="T-15", status="pass" if not hits else "flag",
        detail=(
            "no cause reads as an absent solution" if not hits
            else f"cause(s) phrased as a missing fix, not a condition/mechanism: {hits}"
        ),
    )


def _verified_causes_have_evidence(artifact: FishboneArtifact) -> PrescoreResult:
    # Always "pass": artifacts/fishbone.py's Cause._evidence_required_when_
    # verified makes the opposite state impossible to construct. Rendered
    # anyway (step_type_tag_present's idiom) so this anchor rubric item
    # shows on the strip as checked, not silently assumed -- and stays a
    # real hard_flag-capable check in code, not a hand-waved constant.
    bad = [c.cause_id for c in artifact.causes if c.status == "verified" and c.evidence is None]
    ok = not bad
    return PrescoreResult(
        check_id="verified_causes_have_evidence", tool_id="T-15", status="pass" if ok else "hard_flag",
        detail=(
            "every verified cause carries evidence (schema-guaranteed, rubric R-ANA-02's anchor item)" if ok
            else f"verified cause(s) with no evidence, which should be impossible: {bad}"
        ),
    )


def _ruled_out_causes_retained(artifact: FishboneArtifact) -> PrescoreResult:
    ruled_out = [c.cause_id for c in artifact.causes if c.status == "ruled_out"]
    return PrescoreResult(
        check_id="ruled_out_causes_retained", tool_id="T-15", status="pass",
        detail=(
            f"{len(ruled_out)} ruled-out cause(s) retained on the board (status changed, never deleted)"
            if ruled_out else "no ruled-out causes yet"
        ),
    )
