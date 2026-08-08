"""T-09 prescore: rubric R-MEA-04's rule-checkable lines -- elements
defined (structurally before any cycle can reference them: the artifact's
own referential-integrity validator makes that a schema fact, not just a
UI convention, confirmed here), the cycle-count floor with the shortfall
named per element (flag, never fail -- PLAN §4.2's soft/hard split), spread
present once n>=2, flagged outliers carrying an explanatory note (the
rubric's "Needs work when... the flagged outliers are ignored" line), plus
the same hand-edited-on-disk-JSON defense in depth as prescore/msa.py's
result_matches_inputs."""

from __future__ import annotations

from ..artifacts.time_study import TimeStudyArtifact, compute_element_stats
from ..stats.constants import TIME_STUDY_MIN_CYCLES_GUIDANCE
from .common import PrescoreResult


def _cycle_note(artifact: TimeStudyArtifact, cycle_number: int) -> str:
    for c in artifact.cycles:
        if c.cycle_number == cycle_number:
            return c.observer_note
    return ""


def run_time_study_prescore(artifact: TimeStudyArtifact) -> list[PrescoreResult]:
    results: list[PrescoreResult] = []
    stats = artifact.element_stats.value if artifact.element_stats else []

    results.append(PrescoreResult(
        check_id="elements_defined_before_timing", tool_id="T-09", status="pass",
        detail=(
            f"{len(artifact.elements)} work element(s) declared; every cycle's element_times can only "
            "reference a declared element_id (schema-enforced referential integrity), so elements are "
            "structurally defined before any time against them can exist"
        ),
    ))

    untimed = [s.element_name for s in stats if s.n == 0]
    short = [s.element_name for s in stats if s.below_recommended_cycles and s.n > 0]
    if untimed:
        status, detail = "flag", f"not yet timed at all: {untimed}"
    elif short:
        status = "flag"
        detail = f"below the >= {TIME_STUDY_MIN_CYCLES_GUIDANCE}-cycle guidance (shortfall named on each element's own stats): {short}"
    else:
        status, detail = "pass", f"every element meets the >= {TIME_STUDY_MIN_CYCLES_GUIDANCE}-cycle guidance"
    results.append(PrescoreResult(check_id="cycle_count_floor", tool_id="T-09", status=status, detail=detail))

    no_spread = [s.element_name for s in stats if s.n >= 2 and s.descriptive is None]
    results.append(PrescoreResult(
        check_id="spread_present", tool_id="T-09",
        status="pass" if not no_spread else "flag",
        detail="every element with >= 2 recorded cycles reports mean/median/SD/IQR spread" if not no_spread
        else f"spread missing despite >= 2 recorded cycles (should not happen): {no_spread}",
    ))

    unexplained = [
        f"{s.element_name} cycle {o.cycle_number}"
        for s in stats for o in s.outliers
        if not _cycle_note(artifact, o.cycle_number).strip()
    ]
    results.append(PrescoreResult(
        check_id="outliers_have_notes", tool_id="T-09",
        status="pass" if not unexplained else "flag",
        detail="every flagged outlier cycle carries an observer note" if not unexplained
        else f"flagged outliers with no explanatory note (still retained, never dropped): {unexplained}",
    ))

    recomputed = compute_element_stats(artifact.elements, artifact.cycles)
    matches = artifact.element_stats is not None and recomputed.value == artifact.element_stats.value
    results.append(PrescoreResult(
        check_id="stats_match_recomputation", tool_id="T-09",
        status="pass" if matches else "flag",
        detail="stored per-element stats match a fresh recomputation from the raw cycles" if matches
        else "stored stats differ from a fresh recomputation -- the file may have been hand-edited",
    ))

    return results
