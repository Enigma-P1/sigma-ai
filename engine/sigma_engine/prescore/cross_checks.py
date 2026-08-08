"""/prescore/cross/{project_id}: reconciliation checks that need TWO tools'
data at once, so they can't live in any one tool's own prescore module
(registry.py's PRESCORE_REGISTRY shape takes only the one artifact being
scored -- see prescore/process_map.py's docstring on the same split).

Three independent checks, each running only when every side it needs
actually exists for this project -- an absent side is "nothing to check
yet" (the check is simply omitted from the response), never a flag:

  (a) charter_business_impact_vs_copq_total -- the charter's hand-carried
      business-impact number against the COPQ engine's own computed total;
      a relative mismatch beyond 25% is a flag naming both numbers (green-
      belt-rubric.md R-DEF-05 / R-MEA-11's "two versions of the truth").

  (b) charter_goal_vs_measured_baseline -- the charter's goal target
      against an independently measured baseline mean (a saved project
      dataset's column, computed fresh here via stats/descriptive.py,
      never trusted from the caller): a goal that reads worse than or
      equal to the measured baseline, in the direction the goal's own
      baseline/target pair implies, cannot land as improvement even if it
      is met exactly (R-MEA-11's charter-vs-measured-baseline
      reconciliation, promoted to a Green Belt anchor item).

  (c) check_sheet_burst_entry -- more than 10 live tap-mode check-sheet
      entries inside any 60-second window reads like a paper tally typed
      in after the fact rather than tapped live; ADVISORY only (never a
      hard flag -- entering fast is not itself wrong) and it names the
      honest way out: check_sheet.py's `entry_mode="transcribed"` path,
      which this check always excludes (a real transcription session's
      timestamps cluster on purpose).
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Literal, Sequence

from pydantic import BaseModel

from ..artifacts.charter import CharterArtifact
from ..artifacts.check_sheet import CheckSheetArtifact
from ..artifacts.copq import CopqArtifact
from ..project_store import ProjectStore
from ..stats.descriptive import compute_descriptive_stats

CrossCheckStatus = Literal["pass", "flag", "advisory"]

# (a) charter business-impact vs COPQ total.
BUSINESS_IMPACT_MISMATCH_MAX_RELATIVE = 0.25

# (c) check-sheet burst entry.
BURST_MAX_ENTRIES = 10
BURST_WINDOW_SECONDS = 60


class CrossCheckResult(BaseModel):
    check_id: str
    status: CrossCheckStatus
    detail: str


_ANNUALIZE_FACTORS: list[tuple[str, float]] = [
    # order matters: "quarter" must not lose to a bare "year" substring match,
    # and Q1-Q4 labels ("Q2 2026") carry no period word at all.
    ("quarter", 4.0),
    ("month", 12.0),
    ("week", 52.0),
    ("year", 1.0),
    ("annual", 1.0),
]


def _annualize(amount: float, period_text: str | None) -> float | None:
    """Annualized amount, or None when the period can't be recognized.
    Comparing dollars across different periods without this is how the
    coffee-bar demo's own correct numbers ($4,021/quarter = $16,084/yr)
    initially false-flagged."""
    if not period_text:
        return None
    text = period_text.lower()
    if re.search(r"\bq[1-4]\b", text):
        return amount * 4.0
    for token, factor in _ANNUALIZE_FACTORS:
        if token in text:
            return amount * factor
    return None


def _charter_vs_copq(charter_data: dict | None, copq_data: dict | None) -> CrossCheckResult | None:
    if charter_data is None or copq_data is None:
        return None
    impact = CharterArtifact.model_validate(charter_data).business_impact
    copq = CopqArtifact.model_validate(copq_data)
    copq_total = copq.total.value
    row_periods = {row.period for row in copq.rows}
    copq_period = row_periods.pop() if len(row_periods) == 1 else None
    charter_annual = _annualize(impact.amount, impact.unit)
    copq_annual = _annualize(copq_total, copq_period)
    if charter_annual is None or copq_annual is None:
        return CrossCheckResult(
            check_id="charter_business_impact_vs_copq_total",
            status="advisory",
            detail=(
                f"charter business impact {impact.amount:g} ({impact.unit}) and COPQ total {copq_total:g} "
                f"({'mixed row periods' if copq_period is None and len({r.period for r in copq.rows}) > 1 else copq_period or 'no period'}) "
                "can't be compared across periods -- state both on the same basis (per year is the convention)"
            ),
        )
    denominator = max(abs(charter_annual), abs(copq_annual))
    relative = abs(charter_annual - copq_annual) / denominator if denominator > 0 else 0.0
    matches = relative <= BUSINESS_IMPACT_MISMATCH_MAX_RELATIVE
    return CrossCheckResult(
        check_id="charter_business_impact_vs_copq_total",
        status="pass" if matches else "flag",
        detail=(
            f"charter business impact {impact.amount:g} ({impact.unit}) vs COPQ engine total {copq_total:g} "
            f"-- annualized {charter_annual:g} vs {copq_annual:g}, relative difference {relative:.1%}, "
            f"{'within' if matches else 'beyond'} the {BUSINESS_IMPACT_MISMATCH_MAX_RELATIVE:.0%} tolerance"
            + ("" if matches else " -- reconcile the two numbers, or state the basis that explains the gap")
        ),
    )


def _charter_vs_baseline(charter_data: dict | None, baseline_mean: float | None) -> CrossCheckResult | None:
    if charter_data is None or baseline_mean is None:
        return None
    goal = CharterArtifact.model_validate(charter_data).goal
    if goal.baseline_value is None or goal.target_value == goal.baseline_value:
        return None  # no stated direction to judge against -- not this check's job
    lower_is_better = goal.target_value < goal.baseline_value
    direction = "lower is better" if lower_is_better else "higher is better"
    worse_or_equal = goal.target_value >= baseline_mean if lower_is_better else goal.target_value <= baseline_mean
    return CrossCheckResult(
        check_id="charter_goal_vs_measured_baseline",
        status="flag" if worse_or_equal else "pass",
        detail=(
            f"goal target {goal.target_value:g} {goal.unit} ({direction}) vs measured baseline mean {baseline_mean:g} -- "
            + (
                "the goal is no better than where the process actually measures right now; it cannot read as "
                "improvement even if it is met exactly"
                if worse_or_equal
                else "the goal is a genuine improvement over the measured baseline"
            )
        ),
    )


def _burst_window_max_count(timestamps: Sequence[dt.datetime]) -> int:
    """The largest number of timestamps falling inside any BURST_WINDOW_
    SECONDS-wide window -- a sliding window over the sorted timestamps."""
    ts = sorted(timestamps)
    left = 0
    max_count = 0
    for right in range(len(ts)):
        while (ts[right] - ts[left]).total_seconds() > BURST_WINDOW_SECONDS:
            left += 1
        max_count = max(max_count, right - left + 1)
    return max_count


def _check_sheet_burst(check_sheet_data: dict | None) -> CrossCheckResult | None:
    if check_sheet_data is None:
        return None
    artifact = CheckSheetArtifact.model_validate(check_sheet_data)
    live_taps = [e for e in artifact.entries if e.deleted is None and e.entry_mode == "tap"]
    if not live_taps:
        return None
    max_count = _burst_window_max_count([dt.datetime.fromisoformat(e.timestamp) for e in live_taps])
    is_burst = max_count > BURST_MAX_ENTRIES
    return CrossCheckResult(
        check_id="check_sheet_burst_entry",
        status="advisory" if is_burst else "pass",
        detail=(
            f"{max_count} tap-mode entries land inside a single {BURST_WINDOW_SECONDS}-second window -- entered "
            "in one burst -- if transcribing a paper tally, use tally-transcription mode and say so"
            if is_burst
            else f"no {BURST_WINDOW_SECONDS}-second window carries more than {BURST_MAX_ENTRIES} tap-mode entries"
        ),
    )


def run_cross_checks(
    store: ProjectStore, project_id: str, *, dataset_id: str | None = None, column: str | None = None,
) -> list[CrossCheckResult]:
    """The project's cross-artifact checks -- only the ones both sides
    currently support are returned. `dataset_id`/`column`, when both
    given, name the saved project dataset column whose mean stands in for
    check (b)'s "measured baseline" -- computed fresh here (never a
    client-supplied number), the same server-recomputes-everything
    contract every other engine result in this suite follows."""
    from ..datasets import DatasetStore  # local import: avoids a routes/prescore.py <-> datasets.py cycle

    meta = store.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
    charter_data = store.latest_artifact_for_tool(project_id, meta, "T-03")
    # oldest=True: this check wants the DEFINE-phase COPQ the charter's
    # business_impact figure actually quoted, not a later Wrap re-run --
    # "newest wins" (this helper's default, matching gates.py/stats.py)
    # would silently swap in the Wrap COPQ (a much smaller number, post-
    # improvement) the moment a project re-runs COPQ at Wrap (T-02, R-WRAP-
    # 02), which reconciles against a different sentence than this one.
    # Critic-confirmed: Coffee Bar already carries two T-02 artifacts
    # (coffee-copq, coffee-copq-wrap) and this check's correctness was, up
    # to this fix, a sort accident (alphabetical happened to put the
    # Define-phase one first).
    copq_data = store.latest_artifact_for_tool(project_id, meta, "T-02", oldest=True)
    check_sheet_data = store.latest_artifact_for_tool(project_id, meta, "T-08")

    baseline_mean: float | None = None
    if dataset_id is not None and column is not None:
        data, _dataset_meta = DatasetStore(store).load_numeric_column(project_id, dataset_id, column)
        baseline_mean = compute_descriptive_stats(data).value.mean

    checks = (
        _charter_vs_copq(charter_data, copq_data),
        _charter_vs_baseline(charter_data, baseline_mean),
        _check_sheet_burst(check_sheet_data),
    )
    return [c for c in checks if c is not None]
