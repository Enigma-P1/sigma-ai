"""S-2 -- Ashford Public Library, Marion Street branch, re-shelving
accuracy (attribute / defectives). Held-out scenario carrying PLAN §9's
required named-exit trap: T-12 round 1 on `msa-round1.csv` MUST fail the
engine's kappa check (EXIT-02) before any baseline opens; the honest
recovery is rewriting the operational definition, passing T-12 round 2,
and baselining only on the written-definition audit -- never the bait
(`prelog-daily.csv`, deliberately never charted by this driver at all).

Artifacts are built FROM evals/scenarios/s2-library/spec.md's story and
frontmatter `ground_truth`; the numbers that come back from the engine are
the binding verdicts spec.md's own engine-verification transcript
records, which this driver must reproduce.
"""

from __future__ import annotations

from collections import defaultdict

from ..lib.client import EngineClient
from ..lib.recorder import Recorder
from . import common

PROJECT_ID = "eval-s2-library"
DATA = common.SCENARIOS_DATA_ROOT / "s2-library" / "data"
CHARTER_REF = "s2-charter"
SECTIONS = ("adult", "juvenile", "nonfiction")


def _daily_subgroups(rows: list[dict[str, str]]) -> list[dict]:
    """One p-chart subgroup per date, summing items_audited/misshelved
    across the day's rotating sections (spec: "subgroup = one day's
    audited books across the rotating ranges, both shifts' shelving
    mixed")."""
    by_date: dict[str, list[int, int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        d = by_date[row["date"]]
        d[0] += int(row["items_audited"])
        d[1] += int(row["misshelved"])
    return [{"label": date, "n": n, "defective_count": defective} for date, (n, defective) in sorted(by_date.items())]


def _by_section_totals(rows: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    totals: dict[str, list[int]] = {s: [0, 0] for s in SECTIONS}
    for row in rows:
        t = totals[row["section"]]
        t[0] += int(row["items_audited"])
        t[1] += int(row["misshelved"])
    return {s: (n, d) for s, (n, d) in totals.items()}


def run(recorder: Recorder, engine: EngineClient) -> None:
    common.reset_project(engine, PROJECT_ID, "S-2 Ashford Library (held-out golden, named-exit trap)", "2026-08-01T09:00:00Z")

    baseline_rows = common.read_csv_rows(DATA / "baseline-audit.csv")
    after_rows = common.read_csv_rows(DATA / "after-audit.csv")
    baseline_marks = common.read_csv_rows(DATA / "baseline-defect-marks.csv")
    after_marks = common.read_csv_rows(DATA / "after-defect-marks.csv")
    baseline_subgroups = _daily_subgroups(baseline_rows)
    after_subgroups = _daily_subgroups(after_rows)
    baseline_n = sum(s["n"] for s in baseline_subgroups)
    baseline_defects = sum(s["defective_count"] for s in baseline_subgroups)
    after_n = sum(s["n"] for s in after_subgroups)
    after_defects = sum(s["defective_count"] for s in after_subgroups)
    baseline_pbar = baseline_defects / baseline_n
    goal_p = baseline_pbar / 2.0

    # ---------------------------------------------------------------- Define
    picker = {
        "schema_version": 1, "artifact_id": "s2-picker", "tool_id": "T-01",
        "created_at": "2026-08-01T09:10:00Z", "updated_at": "2026-08-01T09:10:00Z",
        "notes": "Five intake criteria, all Yes; training, sorting, and audit practice are all suspect -- no single obvious fix -- full DMAIC.",
        "scope_narrow": {"answer": True, "detail": "Re-shelving of returned items at the Marion Street branch; new-acquisition shelving and branch transfers are out of scope."},
        "measurable_outcome": {"answer": True, "detail": "Audited misshelve proportion from the daily shelf-read audit."},
        "data_obtainable": {"answer": True, "detail": "Audits are staffed and already run daily; the written definition just needs finishing."},
        "process_owner_engaged": {"answer": True, "detail": "Ruth Delgado, circulation supervisor, is named owner-in-waiting; branch manager Colette Marchand sponsors."},
        "business_impact_plausible": {"answer": True, "detail": "Search time, replacement copies, and hold-cancellation handling put Q3 cost near $2,195/quarter -- small in dollars, large in patron trust."},
        "route": "full-DMAIC",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-01", "T-01", picker)
    common.gate_check(recorder, PROJECT_ID, "intake_picker_present")
    common.gate_check(recorder, PROJECT_ID, "intake_picker_not_exit01")

    # Row 1's quantity is the QUARTERLY staff-hours (spec ground truth:
    # "≈ $2,195/quarter (≈ $1,530.10 search time + $407.40 replacements +
    # $257.40 hold handling)"): the 3-week desk-log sample (74 searches x
    # 11 min) extrapolates to ~321 searches/quarter = 58.85 staff-hours,
    # 58.85 x $26 = $1,530.10. FL-12 fix: this driver used to post the raw
    # 3-week sample hours (13.57) here, producing a $1,017.62 total that
    # contradicted the same scenario's charter basis ("$2,195 x 4") and the
    # spec's own cost block -- the spec's arithmetic is internally
    # consistent; the driver was the wrong side.
    copq = {
        "schema_version": 1, "artifact_id": "s2-copq", "tool_id": "T-02",
        "created_at": "2026-08-01T10:00:00Z", "updated_at": "2026-08-01T10:00:00Z",
        "notes": "Q3 ingredients per the charter's cost case; the engine computes each row amount and the total.",
        "rows": [
            {"category": "custom", "custom_label": "Catalog-said-available searches (desk staff time)", "quantity": 58.85, "rate": 26.0,
             "period": "Q3 2026", "basis": "74 searches averaging 11 staff-minutes each in a 3-week desk-log sample, extrapolated to the quarter (~321 searches, 58.85 staff-hours); loaded staff rate $26/hour", "is_estimate": True},
            {"category": "scrap", "custom_label": None, "quantity": 21.0, "rate": 19.40,
             "period": "Q3 2026", "basis": "21 replacement copies traced to shelving losses, average $19.40 each", "is_estimate": False},
            {"category": "custom", "custom_label": "Holds cancelled 'missing' (desk + ILL handling)", "quantity": 9.9, "rate": 26.0,
             "period": "Q3 2026", "basis": "66 holds cancelled 'missing' per quarter, ~9 minutes desk+ILL handling each (9.9 staff-hours); loaded staff rate $26/hour", "is_estimate": False},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-02", "T-02", copq)

    charter = {
        "schema_version": 1, "artifact_id": CHARTER_REF, "tool_id": "T-03",
        "created_at": "2026-08-01T11:00:00Z", "updated_at": "2026-08-27T09:00:00Z",
        "notes": "Problem statement written AFTER the definition fix (2026-08-28), per the spec's honesty ordering; the pre-log's ~3.8% is recorded here as history with its measurement caveat, not as the baseline.",
        "problem_statement": {
            "what": "Re-shelved books at the Marion Street branch fail the shelf-read audit under the written shelving-defect definition -- roughly one book in fifteen is somewhere a catalog-guided patron will not find it.",
            "where": "Ashford Public Library, Marion Street branch.",
            "when": "Baseline window 2026-08-31 to 2026-09-24.",
            "magnitude": {"number": 6.53, "unit": "percent audited misshelve rate (90 of 1,379 audited)", "period": "baseline window 2026-08-31 to 2026-09-24"},
        },
        "goal": {
            "statement": "Halve the audited misshelve proportion from 0.0653 to at most 0.0326 by 2026-11-30, without dropping shelving throughput more than 10%.",
            "metric_name": "Audited misshelve proportion (daily shelf-read audit)", "baseline_value": 0.0653, "target_value": 0.0326,
            "unit": "proportion", "target_date": "2026-11-30",
            "consequential_metrics": ["Shelving throughput (items/staff-hour)", "Holds cancelled as missing, per week"],
        },
        "scope": {"in_scope": "Re-shelving of returned items across adult/juvenile/nonfiction.", "out_scope": "New-acquisition shelving and branch transfers."},
        "team": [
            {"name": "Ruth Delgado", "role": "Circulation supervisor (process owner)"}, {"name": "Alan Wexford", "role": "Senior page"},
            {"name": "Mira Chen", "role": "Evening circulation clerk"}, {"name": "Colette Marchand", "role": "Branch manager (sponsor)"},
        ],
        "process_owner": {"name": "Ruth Delgado", "role": "Circulation supervisor -- runs the shelving operation daily"},
        "timeline": [
            {"name": "Define complete", "date": "2026-08-28"}, {"name": "Measure complete (baseline in hand)", "date": "2026-09-25"},
            {"name": "Analyze complete (causes verified)", "date": "2026-09-27"}, {"name": "Improve complete (fix proven)", "date": "2026-10-31"},
            {"name": "Control plan in place", "date": "2026-11-04"},
        ],
        "business_impact": {"amount": 8780, "unit": "dollars per year", "basis": "COPQ calculator Q3 2026 total ($2,195) x 4 -- labeled projection, Q3 actuals x4 basis stated"},
        "risks": [
            {"risk": "New-page turnover (3 of 4 shelving pages under six months' experience)", "likelihood": "high", "impact": "medium",
             "mitigation": "Written shelving-defect rules + observed-demonstration training on the T-24 SOP", "owner": "Ruth Delgado"},
            {"risk": "Fall reading-program returns push shelving volume up through October, confounding the after-window proof", "likelihood": "high", "impact": "medium",
             "mitigation": "Declare the confound before the pilot window opens; read its direction on the proof honestly", "owner": "Ruth Delgado"},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-03", "T-03", charter)

    sipoc = {
        "schema_version": 1, "artifact_id": "s2-sipoc", "tool_id": "T-04",
        "created_at": "2026-08-02T09:00:00Z", "updated_at": "2026-08-02T09:00:00Z", "notes": "Boundaries match the charter scope.",
        "supplier_input_pairs": [
            {"supplier": "Patron", "input": "Returned item"}, {"supplier": "Check-in desk", "input": "Scanned return, rough-sorted onto a cart"},
        ],
        "process_steps": [
            {"step_number": 1, "description": "Item returned and check-in scanned"}, {"step_number": 2, "description": "Item rough-sorted onto a sorting-room cart"},
            {"step_number": 3, "description": "Page sorts and shelves the item at the shelf"}, {"step_number": 4, "description": "Daily shelf-read audit checks a sample of shelved items"},
        ],
        "output_customer_pairs": [
            {"output": "Correctly shelved item, findable by call number", "customer": "Patron (catalog-guided search)"},
            {"output": "Audit record", "customer": "Circulation supervisor (process monitoring)"},
        ],
        "scope_start": "Check-in scan", "scope_end": "Item audited on the shelf",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-04", "T-04", sipoc)

    voc_ctq = {
        "schema_version": 1, "artifact_id": "s2-voc-ctq", "tool_id": "T-05",
        "created_at": "2026-08-02T10:00:00Z", "updated_at": "2026-08-02T10:00:00Z", "notes": "Binary CTQ: found-where-the-catalog-points, pass/fail per the four written rules.",
        "customers": [{"role": "External -- patron searching by catalog call number", "is_internal": False}],
        "statements": [
            {"statement_id": "S1", "customer_role": "External -- patron searching by catalog call number", "text": "The catalog says it's on the shelf, and it isn't there.",
             "source": "complaint_log", "source_detail": "Recurring desk complaint, logged daily since early August 2026"},
        ],
        "needs": [{"need_id": "N1", "statement_ids": ["S1"], "text": "Find the book exactly where the catalog's call-number order says it should be."}],
        "ctqs": [{"ctq_id": "C1", "need_id": "N1", "measure": "Re-shelved book found where the call-number walk finds it (pass/fail per the four written rules)",
                    "direction": "lower_is_better", "target": "Audited misshelve proportion <= 0.0326 by 2026-11-30",
                    "critical_vs_easy_check": "Customer-critical: S1 is literally about findability, not shelving speed or tidiness."}],
        "primary_ctq_id": "C1",
        "charter_metric_link": "C1 is the charter's primary metric: audited misshelve proportion, target 0.0326 by 2026-11-30 -- hold-cancellation churn (C2) is a consequential metric, not a second primary.",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-05", "T-05", voc_ctq)

    common.gate_check(recorder, PROJECT_ID, "define_to_measure")

    # --------------------------------------------------------------- Measure
    process_map = {
        "schema_version": 1, "artifact_id": "s2-process-map", "tool_id": "T-06",
        "created_at": "2026-08-15T09:00:00Z", "updated_at": "2026-08-15T09:00:00Z",
        "notes": "The physical reality: check-in scan, rough sort onto sorting-room carts, then pages sort AT THE SHELF while balancing an armload -- the verified root the fishbone names.",
        "lanes": [
            {"lane_id": "checkin", "name": "Check-in desk", "owner": "Circulation desk staff"},
            {"lane_id": "sorting-room", "name": "Sorting room", "owner": "Ruth Delgado"},
            {"lane_id": "page", "name": "Shelving page", "owner": "Alan Wexford / Mira Chen / pages"},
            {"lane_id": "audit", "name": "Shelf-read audit", "owner": "Ruth Delgado"},
        ],
        "steps": [
            {"step_id": "s1", "lane_id": "checkin", "name": "Check-in scan", "order": 1, "step_type": "enabling", "time_minutes": 0.5, "defect_point": False, "strata": [], "reason": "Required system update, no transformation", "wastes": []},
            {"step_id": "s2", "lane_id": "sorting-room", "name": "Rough-sort onto sorting-room cart", "order": 2, "step_type": "non_value_add", "time_minutes": 2.0, "defect_point": True, "strata": ["section"],
             "reason": "Cramped room, unlabeled sort shelves, a standing pile nobody owns", "wastes": [{"waste_id": "motion", "note": "No sortable standard exists yet at this step -- order is created later, at the worst possible place"}]},
            {"step_id": "s3", "lane_id": "page", "name": "Page sorts and shelves at the shelf", "order": 3, "step_type": "value_add", "time_minutes": 3.0, "defect_point": True, "strata": ["section"],
             "reason": "The transformation the patron needs, but interleaving happens here while balancing an armload", "wastes": [{"waste_id": "defects", "note": "Out-of-order and wrong-bay placements dominate the Pareto (81.1% vital few)"}]},
            {"step_id": "s4", "lane_id": "audit", "name": "Daily shelf-read audit", "order": 4, "step_type": "enabling", "time_minutes": 5.0, "defect_point": False, "strata": ["section"],
             "reason": "Verification step, not a transformation", "wastes": []},
        ],
        "connectors": [{"from_step": "s1", "to_step": "s2", "label": None}, {"from_step": "s2", "to_step": "s3", "label": None}, {"from_step": "s3", "to_step": "s4", "label": None}],
        "demand": {"available_time_minutes": 480, "demand_units": 65},
        "layout": {"s1": {"x": 60, "y": 40}, "s2": {"x": 240, "y": 40}, "s3": {"x": 420, "y": 40}, "s4": {"x": 600, "y": 40}},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-06", "T-06", process_map)

    # -- T-11 first draft: no written definition yet ("who judges, by what rule" unanswered)
    collection_plan_v1 = {
        "schema_version": 1, "artifact_id": "s2-collection-plan", "tool_id": "T-11",
        "created_at": "2026-08-20T09:00:00Z", "updated_at": "2026-08-20T09:00:00Z",
        "notes": "First draft: proposes auditing daily assigned ranges, but the measurement question -- who judges, by what rule -- has no written answer yet. The honest next step is T-12, not trusting any count (including the pre-existing closers' log).",
        "metric_name": "Audited misshelve proportion", "charter_metric_id": "C1",
        "operational_definition": {
            "what_measured": "Whether a re-shelved book is where the call-number walk finds it (pass/fail)",
            "how_instrument": "Daily shelf-read audit of that day's two assigned ranges per section -- judgment rule not yet written down",
            "precision_unit": "pass/fail per book", "starts_when": "Book is scanned into the audit range", "stops_when": "Auditor records pass/fail",
            "two_people_confirmed": False,
        },
        "data_type": "attribute_defective",
        "stratification_factors": [{"name": "section", "values_expected": list(SECTIONS)}],
        "no_stratification_reason": "",
        "logistics": {"who_collects": "Rotating audit assignment, both shifts", "where_collected": "Shelf-read audit of daily assigned ranges",
                        "when_how_often": "Daily", "planned_n": 1300, "sample_size_rationale": "Pending -- the judgment rule must be written and pass T-12 before a real sample-size panel means anything."},
        "bias_note": "A pre-existing informal misshelve log exists (the closers' daily tally) but has never been checked for rater agreement -- not trusted until T-12 passes.",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-11", "T-11.v1", collection_plan_v1)

    # -- T-12 round 1: the named-exit trap fires here.
    msa_round1_rows = common.read_csv_rows(DATA / "msa-round1.csv")
    msa_round1 = {
        "schema_version": 1, "artifact_id": "s2-msa", "tool_id": "T-12",
        "created_at": "2026-08-27T09:00:00Z", "updated_at": "2026-08-27T09:00:00Z",
        "notes": "Round 1: 50 flagged shelf positions, judged independently by Alan Wexford (rater A) and Mira Chen (rater B) under their own two PRIVATE definitions -- no written standard existed yet.",
        "data_type": "attribute", "operator": "Ruth Delgado (study coordinator)",
        "attribute_items": [
            {"item_id": row["item_id"], "rater_a": bool(int(row["rater_a_pass"])), "rater_b": bool(int(row["rater_b_pass"]))}
            for row in msa_round1_rows
        ],
    }
    round1 = common.save_and_prescore(recorder, engine, PROJECT_ID, "T-12", "T-12.round1", msa_round1)
    exit02 = round1["result"]["exit02"]
    if exit02 is None or round1["result"]["verdict"] != "fail":
        raise AssertionError(
            "S-2's headline requirement did not fire: T-12 round 1 must come back verdict='fail' with an EXIT-02 "
            f"payload attached (matrix §4a). Got verdict={round1['result']['verdict']!r}, exit02={exit02!r}"
        )
    print(f"[s2-library] EXIT-02 captured: {exit02['message']!r}")

    # The engine's own gate agrees: capability language is hard-blocked
    # while T-12 reads fail (matrix §4a) -- checked right where the story
    # says the run stops.
    gate_after_fail = common.gate_check(recorder, PROJECT_ID, "measure_capability_language_requires_msa_pass", suffix=".after_round1_fail")
    if gate_after_fail["status"] != "HARD_BLOCK":
        raise AssertionError(f"gate should HARD_BLOCK while T-12 reads fail; got {gate_after_fail!r}")

    # -- The fix: the four written rules go into T-11's operational definition.
    written_rules = (
        "A book is correctly shelved only if a patron walking the call-number order would find it: "
        "(1) exact call-number order -- ANY out-of-order placement fails, one slot or one bay; "
        "(2) juvenile series shelve by the posted series-title-then-volume scheme -- by-author placement in a "
        "series section fails; (3) oversize titles belong in the oversize section WITH a dummy marker at the "
        "home slot -- marker present passes, absent fails; (4) a book lying flat on top of a row is not "
        "shelved -- fails."
    )
    collection_plan_v2 = {
        **collection_plan_v1, "updated_at": "2026-08-28T09:00:00Z",
        "notes": "Rework after T-12 round 1 failed (kappa 0.336, EXIT-02): the four written shelving-defect rules now pin the judgment call. Sampling scheme for T-21: subgroup = one day's audited books across the rotating ranges, both shifts' shelving mixed.",
        "operational_definition": {
            "what_measured": written_rules, "how_instrument": "Daily shelf-read audit of that day's two assigned ranges per section, judged against the four written rules above",
            "precision_unit": "pass/fail per book", "starts_when": "Book is scanned into the audit range", "stops_when": "Auditor records pass/fail against the written rules",
            "two_people_confirmed": True,
        },
        "logistics": {**collection_plan_v1["logistics"], "sample_size_rationale": "Engine sample-size panel, proportion calculator: planning p 0.05, margin 1.5 points at 95% confidence returns n=811; 21 audit days at ~65/day (~1,380) clears it."},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-11", "T-11.v2", collection_plan_v2)
    recorder.call("T-11.sample_size", "POST", "/stats/sample-size",
                   {"calculator": "proportion", "planning_p": 0.05, "margin_of_error": 0.015, "confidence_level": 0.95}, tool_ids=["T-11"])

    # -- T-12 round 2: passes.
    msa_round2_rows = common.read_csv_rows(DATA / "msa-round2.csv")
    msa_round2 = {
        **msa_round1, "updated_at": "2026-08-29T09:00:00Z",
        "notes": "Round 2: a fresh 50-position planted set two days after the written definition, same raters, round-1 sheets sealed.",
        "attribute_items": [
            {"item_id": row["item_id"], "rater_a": bool(int(row["rater_a_pass"])), "rater_b": bool(int(row["rater_b_pass"]))}
            for row in msa_round2_rows
        ],
    }
    round2 = common.save_and_prescore(recorder, engine, PROJECT_ID, "T-12", "T-12.round2", msa_round2)
    if round2["result"]["verdict"] != "acceptable":
        raise AssertionError(f"T-12 round 2 should read acceptable; got {round2['result']['verdict']!r}")

    # The gate clears now that the latest T-12 passes -- the baseline window may open.
    gate_after_pass = common.gate_check(recorder, PROJECT_ID, "measure_capability_language_requires_msa_pass", suffix=".after_round2_pass")
    if gate_after_pass["status"] != "CLEAR":
        raise AssertionError(f"gate should CLEAR once T-12 round 2 passes; got {gate_after_pass!r}")

    check_sheet_categories = sorted({row["defect_type"] for row in baseline_marks})
    check_sheet = {
        "schema_version": 1, "artifact_id": "s2-check-sheet", "tool_id": "T-08",
        "created_at": "2026-08-31T08:00:00Z", "updated_at": "2026-09-24T17:00:00Z",
        "notes": "One mark per misshelved book found on the written-definition baseline audit (90 marks, 2026-08-31 to 2026-09-24).",
        "categories": [{"category_id": f"cat-{i}", "label": label} for i, label in enumerate(check_sheet_categories)],
        "strata_fields": [{"key": "date", "label": "Date"}, {"key": "section", "label": "Section"}],
        "entries": [
            {"entry_id": f"E{i+1:03d}", "category_id": f"cat-{check_sheet_categories.index(row['defect_type'])}",
             "timestamp": f"{row['date']}T17:00:00", "strata": {"date": row["date"], "section": row["section"]}, "note": ""}
            for i, row in enumerate(baseline_marks)
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-08", "T-08", check_sheet)
    recorder.call("T-08.to_dataset", "POST", f"/project/{PROJECT_ID}/check-sheet/{check_sheet['artifact_id']}/to-dataset",
                   {"created_at": "2026-09-24T17:05:00Z"}, tool_ids=["T-08"])
    recorder.call("T-14.pareto.defect_types", "POST", "/stats/pareto",
                   {"categories": [row["defect_type"] for row in baseline_marks]}, tool_ids=["T-14"])

    baseline_ds = common.upload_dataset(recorder, engine, PROJECT_ID, "dataset.baseline_audit",
                                          DATA / "baseline-audit.csv", "2026-09-24T17:10:00Z", tool_ids=["T-11"])
    after_ds = common.upload_dataset(recorder, engine, PROJECT_ID, "dataset.after_audit",
                                       DATA / "after-audit.csv", "2026-10-31T17:00:00Z", tool_ids=["T-11"], do_preview=False)

    # T-13's attribute path is T-21 (p-chart) + T-10 (DPMO), not /stats/baseline
    # (continuous-only) -- see the control-chart and yield sections below.

    yield_calc = {
        "schema_version": 1, "artifact_id": "s2-yield", "tool_id": "T-10",
        "created_at": "2026-09-25T09:00:00Z", "updated_at": "2026-09-25T09:00:00Z",
        "notes": "The honest floor: one opportunity per book. No serial-steps claim (steps_in_series=false) -- RTY is not computed.",
        "steps": [{"name": "Shelf-read audit (written definition)", "units_in": float(baseline_n), "first_pass_correct": float(baseline_n - baseline_defects)}],
        "steps_in_series": False,
        "dpmo_block": {"defects": float(baseline_defects), "units": float(baseline_n), "opportunities_per_unit": 1.0, "opportunity_justification": "", "apply_sigma_shift": True},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-10", "T-10", yield_calc)

    common.gate_check(recorder, PROJECT_ID, "measure_to_analyze")

    # -------------------------------------------------------------- Analyze
    section_totals = _by_section_totals(baseline_rows)
    chi_sq = {
        "schema_version": 1, "artifact_id": "s2-hyp-section", "tool_id": "T-17",
        "created_at": "2026-09-26T09:00:00Z", "updated_at": "2026-09-26T09:00:00Z",
        "notes": "Declared before the section split was cut, as a screen -- not the primary comparison.",
        "declared_primary": False,
        "question": {
            "question_text": "Does the misshelved-vs-ok proportion differ by section (baseline window)?",
            "comparison_type": "association_categorical", "declared_data_type": "nominal_categorical",
            "groups": [], "paired_before": None, "paired_after": None, "paired_before_label": "before", "paired_after_label": "after",
            "sample": None, "sample_label": "sample", "target": None,
            "contingency_table": [[section_totals[s][1] for s in SECTIONS], [section_totals[s][0] - section_totals[s][1] for s in SECTIONS]],
            "row_labels": ["misshelved", "ok"], "col_labels": list(SECTIONS),
            "time_ordered": False, "user_shape_concern": False, "measurements_per_unit": 1, "question_intent": None,
            "comparisons_declared": 1, "tests_run_including_this_one": 1, "declared_primary": False,
        },
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-17", "T-17.section_screen", chi_sq)

    fishbone = {
        "schema_version": 1, "artifact_id": "s2-fishbone", "tool_id": "T-15",
        "created_at": "2026-09-26T10:00:00Z", "updated_at": "2026-09-27T09:00:00Z",
        "notes": "The pre-log's Alan/Mira gap (2.99% vs 4.83%) is quotable here as the measurement lesson, never as a people finding.",
        "effect": {"text": "6.53% of re-shelved books fail the shelf-read audit under the written definition (baseline n=1,379, stable, p-chart)", "charter_ref": CHARTER_REF},
        "causes": [
            {"cause_id": "c-sort-at-shelf", "branch": "method", "text": "Sorting happens at the shelf -- pages interleave books while balancing an armload",
             "parent_cause_id": None, "status": "verified", "evidence": {"kind": "check_sheet", "ref": "s2-check-sheet"}, "why_chain_position": None},
            {"cause_id": "c-no-standard", "branch": "method", "text": "The sorting room has no sortable standard -- order is created at the worst possible place",
             "parent_cause_id": "c-sort-at-shelf", "status": "verified",
             "evidence": {"kind": "observation_note", "ref": "Process map s2: cramped sorting room, unlabeled sort shelves, a standing pile nobody owns"}, "why_chain_position": 1},
            {"cause_id": "c-unwritten-conventions", "branch": "method", "text": "Series/exception shelving conventions were unwritten until 2026-08-28",
             "parent_cause_id": None, "status": "verified",
             "evidence": {"kind": "observation_note", "ref": "The definition fix itself is evidence: the branch had no written standard for the pages to learn before T-12 round 1 failed"}, "why_chain_position": None},
            {"cause_id": "c-lighting", "branch": "environment", "text": "Lighting in the juvenile aisles may make call numbers hard to read", "parent_cause_id": None, "status": "candidate", "evidence": None, "why_chain_position": None},
            {"cause_id": "c-cart-overload", "branch": "method", "text": "Carts overloaded before pages reach the shelf", "parent_cause_id": None, "status": "candidate", "evidence": None, "why_chain_position": None},
            {"cause_id": "c-rater-drift", "branch": "measurement", "text": "Rater drift could be inflating the measured rate", "parent_cause_id": None, "status": "ruled_out",
             "evidence": {"kind": "observation_note", "ref": "T-12 round 2 passed at kappa 0.878; a quarterly kappa re-run is scheduled to keep it that way"}, "why_chain_position": None},
            {"cause_id": "c-shift-mix", "branch": "people", "text": "Shift mix (which shift shelved a given cart) drives the rate", "parent_cause_id": None, "status": "ruled_out",
             "evidence": {"kind": "observation_note", "ref": "Both shifts are sampled by the rotation; no shift term survives the section split (chi-square screen)"}, "why_chain_position": None},
        ],
        "layout": {},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-15", "T-15", fishbone)

    common.gate_check(recorder, PROJECT_ID, "analyze_to_improve")

    # -------------------------------------------------------------- Improve
    solution_matrix = {
        "schema_version": 1, "artifact_id": "s2-solution-matrix", "tool_id": "T-18",
        "created_at": "2026-09-27T09:00:00Z", "updated_at": "2026-09-27T11:00:00Z",
        "notes": "Pre-sort ranks first -- it moves sorting to a bench with both hands free and the standard on the wall, directly at the verified root.",
        "solutions": [
            {"solution_id": "sol-presort", "name": "Pre-sorted carts + posted sorting standard",
             "description": "Returns sorted into final shelf order in the sorting room against the posted standard, exception flags clipped at sort time -- pages place at the shelf, they no longer sort there. ~$60 in dividers and flags.",
             "linked_cause_ids": ["c-sort-at-shelf", "c-no-standard"], "impact": 5, "effort": 3,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 5, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 3, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 5, "scored_at": "2026-09-27T11:00:00Z"}]},
            {"solution_id": "sol-double-check", "name": "Double-check every cart at the shelf",
             "description": "A second person re-checks placement at the shelf -- permanent added labor, addresses the symptom not the root.",
             "linked_cause_ids": ["c-sort-at-shelf"], "impact": 3, "effort": 1,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 2, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 1, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 1, "scored_at": "2026-09-27T11:00:00Z"}]},
            {"solution_id": "sol-retrain", "name": "Retrain-everyone workshop",
             "description": "Fades without a standard to retrain to -- the training content should ride the posted standard rather than replace it.",
             "linked_cause_ids": ["c-unwritten-conventions"], "impact": 2, "effort": 2,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 2, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 3, "scored_at": "2026-09-27T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 4, "scored_at": "2026-09-27T11:00:00Z"}]},
        ],
        "criteria": [
            {"criterion_id": "crit-gap-impact", "name": "Gap impact (5 = attacks the largest verified block)", "weight": 0.5, "declared_at": "2026-09-27T09:00:00Z"},
            {"criterion_id": "crit-effort", "name": "Effort/speed to implement", "weight": 0.25, "declared_at": "2026-09-27T09:00:00Z"},
            {"criterion_id": "crit-cost", "name": "Cost (5 = near-zero spend)", "weight": 0.25, "declared_at": "2026-09-27T09:00:00Z"},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-18", "T-18", solution_matrix)

    pilot = {
        "schema_version": 1, "artifact_id": "s2-pilot", "tool_id": "T-19",
        "created_at": "2026-09-25T09:00:00Z", "updated_at": "2026-10-31T17:00:00Z",
        "notes": "One change only -- bundling the December training refresher into this pilot would be EXIT-10 territory; the refresher stays in the implementation plan instead.",
        "the_one_change": {"statement": "Pre-sorted carts: returns are sorted into final shelf order in the sorting room against the posted standard, exception flags clipped at sort time; pages place at the shelf, they no longer sort there.",
                             "linked_solution_id": "sol-presort", "linked_cause_ids": ["c-sort-at-shelf", "c-no-standard"]},
        "changes": [{"change_id": "chg-1", "text": "Pre-sorted carts: returns are sorted into final shelf order in the sorting room against the posted standard, exception flags clipped at sort time; pages place at the shelf, they no longer sort there."}],
        "comparison_design": {"kind": "before_period", "description": "The frozen written-definition baseline (baseline-audit.csv, 21 days, p-bar 0.065265, stable) vs the measured after window."},
        "inclusion": {"who_or_what": "All re-shelved returns across adult/juvenile/nonfiction, both shifts, the daily shelf-read audit's rotating ranges",
                        "how_selected": "Same rotating-range audit rule as the baseline",
                        "honesty_note": "One branch, one sorting room -- no randomization across sites."},
        "success_threshold": {"metric_ref": "audited misshelve rate (charter C1) -- settled-window rate", "direction": "lower_is_better", "value": 0.04, "declared_at": "2026-09-25T09:00:00Z"},
        "analysis_plan": {"expected_route": "two_proportion_z", "rationale": "Two independent windows of pass/fail audit counts -- two-proportion z is the engine's proportions-comparison route."},
        "falsification_line": "Two settled weeks above 4.0% audited rate -> revert to unsorted carts and take the next-ranked cause.",
        "confounder_checklist": {
            "staffing": {"changed": False, "note": "Same pages and rotation throughout."},
            "season": {"changed": True, "note": "Fall reading-program returns push shelving volume up through October -- can only push the rate up, never manufacture a win."},
            "demand": {"changed": True, "note": "Same driver as season: higher return volume through the after window."},
            "measurement": {"changed": False, "note": "Same written definition and audit procedure as the baseline; T-12 round 2 still stands."},
            "other": {"changed": False, "note": "No other process change landed in the window."},
        },
        "status": "complete",
    }
    bundled = dict(pilot)
    bundled["changes"] = [*pilot["changes"], {"change_id": "chg-2", "text": "December series-convention refresher for winter new hires -- bundled in to save a second pilot round."}]
    common.validate_only(recorder, engine, "T-19", "T-19.exit10_probe", bundled, expect_status=(422,))
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-19", "T-19", pilot)

    settled_rows = [r for r in after_rows if "2026-10-05" <= r["date"] <= "2026-10-17"]
    settled_n = sum(int(r["items_audited"]) for r in settled_rows)
    settled_defects = sum(int(r["misshelved"]) for r in settled_rows)
    proportions = {
        "schema_version": 1, "artifact_id": "s2-hyp-primary", "tool_id": "T-17",
        "created_at": "2026-10-17T17:00:00Z", "updated_at": "2026-10-17T17:00:00Z",
        "notes": "The pre-declared primary: baseline vs the settled-weeks slice of the after window (2026-10-05 to 2026-10-17).",
        "declared_primary": True,
        "question": {
            "question_text": "Did the audited misshelve rate drop between the baseline window and the settled post-pilot weeks?",
            "comparison_type": "proportions", "declared_data_type": "nominal_categorical",
            "groups": [{"label": "baseline", "values": None, "successes": baseline_defects, "n": baseline_n},
                        {"label": "settled_weeks", "values": None, "successes": settled_defects, "n": settled_n}],
            "paired_before": None, "paired_after": None, "paired_before_label": "before", "paired_after_label": "after",
            "sample": None, "sample_label": "sample", "target": None, "contingency_table": None, "row_labels": None, "col_labels": None,
            "time_ordered": False, "user_shape_concern": False, "measurements_per_unit": 1, "question_intent": None,
            "comparisons_declared": 1, "tests_run_including_this_one": 1, "declared_primary": True,
        },
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-17", "T-17.primary", proportions)

    proof = {
        "schema_version": 1, "artifact_id": "s2-proof", "tool_id": "T-20",
        "created_at": "2026-10-31T17:30:00Z", "updated_at": "2026-10-31T17:30:00Z",
        "notes": "Measured after window 2026-10-05 to 2026-10-31 (24 service days); the 2026-09-28..10-03 bedding-in week excluded by declaration. before/after values are DAILY proportions weighted by that day's audited count, so the weighted mean reproduces the pooled rate exactly.",
        "pilot_ref": "s2-pilot", "metric_ref": "audited misshelve rate (charter C1)",
        "operational_definition_ref": "s2-collection-plan", "measurement_system_ref": "s2-msa",
        "usl": None, "lsl": None, "operational_definition_ok": True,
        "before": {"dataset_id": baseline_ds["dataset_id"], "dataset_sha256": baseline_ds["sha256"], "column": "misshelved_rate",
                    "values": [s["defective_count"] / s["n"] for s in baseline_subgroups], "weights": [float(s["n"]) for s in baseline_subgroups]},
        "after": {"dataset_id": after_ds["dataset_id"], "dataset_sha256": after_ds["sha256"], "column": "misshelved_rate",
                   "values": [s["defective_count"] / s["n"] for s in after_subgroups], "weights": [float(s["n"]) for s in after_subgroups]},
        "declared_threshold": {"metric_ref": "audited misshelve rate (charter C1) -- settled-window rate", "direction": "lower_is_better", "value": 0.04, "declared_at": "2026-09-25T09:00:00Z"},
        "confounders": {
            "staffing": {"changed": False, "note": "Same pages and rotation throughout."},
            "season": {"changed": True, "note": "Fall reading-program returns pushed shelving volume up through October -- direction stated: can only push the rate up, never manufacture a win."},
            "demand": {"changed": True, "note": "Same driver as season."},
            "measurement": {"changed": False, "note": "Same written definition and audit procedure as the baseline."},
            "other": {"changed": False, "note": "No other process change landed in the window."},
        },
        "guardrails": [
            {"metric_ref": "shelving throughput (items/staff-hour, guardrail)", "direction": "higher_is_better", "before_value": 34.2, "after_value": 33.6},
            {"metric_ref": "holds cancelled as missing per week (consequential)", "direction": "lower_is_better", "before_value": 5.1, "after_value": 2.3},
        ],
        "charter_ref": CHARTER_REF, "charter_baseline_value": baseline_pbar, "charter_goal_value": goal_p, "charter_goal_direction": "lower_is_better",
        "next_cause_ref": {"cause_id": "c-unwritten-conventions", "cause_text": "Series/exception shelving conventions were unwritten until 2026-08-28",
                             "via_solution_id": "sol-retrain", "via_solution_name": "Retrain-everyone workshop (rides the posted standard)", "rank": 2},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-20", "T-20", proof)

    common.gate_check(recorder, PROJECT_ID, "improve_to_control")

    # -------------------------------------------------------------- Control
    # (1) Baseline freeze, 21 daily subgroups.
    control_chart_v1 = common.prepare_control_chart({
        "schema_version": 1, "artifact_id": "s2-control-chart", "tool_id": "T-21",
        "created_at": "2026-09-25T09:00:00Z", "updated_at": "2026-09-25T09:00:00Z",
        "notes": "(1) Baseline freeze, 21 daily subgroups, written-definition audit.",
        "chart_type": "p", "metric_ref": "audited misshelve rate (charter C1)",
        "selector": {"data_shape": "attribute", "defectives_or_defects": "defectives"},
        "source": {"kind": "dataset", "dataset_id": baseline_ds["dataset_id"], "dataset_sha256": baseline_ds["sha256"], "column": "misshelved"},
        "p_subgroups": baseline_subgroups, "recalculation_log": [], "armed": {"monitoring_started": True, "cadence_note": "Ruth enters each day's audit at close."}, "acknowledgments": {},
    }, action_at="2026-09-25T09:00:00Z")
    v1 = common.save_and_prescore(recorder, engine, PROJECT_ID, "T-21", "T-21.freeze", control_chart_v1, strip=False)

    # (2) The improvement arrives on the FROZEN limits -- extend p_subgroups
    # with the 24 post-window days, no re-freeze (freeze_requested stays
    # False, so _freeze_or_recalculate no-ops and the frozen p_baseline
    # from (1) passes through unchanged while `signals` recomputes fresh).
    control_chart_v2 = common.merge(
        v1, updated_at="2026-10-31T09:00:00Z",
        notes="(2) The improvement itself arrives on the frozen limits: 24 post-window days appended, no re-freeze -- exactly one rule-4 signal expected (24 consecutive points below center).",
        p_subgroups=[*baseline_subgroups, *after_subgroups], freeze_requested=False, recalculate_reason=None, action_at=None,
    )
    v2 = common.save_and_prescore(recorder, engine, PROJECT_ID, "T-21", "T-21.extend_no_refreeze", control_chart_v2, strip=False)
    signal_ids = [s["signal"]["rule_id"] for s in v2["signals"]["value"]]
    if "rule4" not in signal_ids:
        raise AssertionError(f"expected a rule4 signal when the post window arrives on the frozen baseline; got {signal_ids!r}")

    # (3) The logged recalculation: freeze floor met (24 >= 20), post window alone.
    control_chart_v3 = common.merge(
        v2, updated_at="2026-10-31T17:00:00Z",
        notes="(3) Logged recalculation on the 24-day post window alone -- the whole limits history stays on this one artifact.",
        p_subgroups=after_subgroups, freeze_requested=False,
        recalculate_reason="Post-pilot recalculation: pre-sorted carts held for the full 24-day settled window; moving the center is a deliberate, logged decision, not an informal recenter.",
        action_at="2026-10-31T17:00:00Z",
    )
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-21", "T-21.recalculate", control_chart_v3, strip=False)

    five_s = {
        "schema_version": 1, "artifact_id": "s2-five-s", "tool_id": "T-23",
        "created_at": "2026-09-28T09:00:00Z", "updated_at": "2026-11-04T09:00:00Z",
        "notes": "The fix's physical home: labeled sort shelves by range, cart staging lanes, exception-flag bin at the bench, the orphan pile dispositioned. Photos omitted for this eval fixture (schema allows an empty photos list per round).",
        "rounds": [
            {"round_id": "r1", "date": "2026-09-28", "area": "Sorting room",
             "scores": [{"category": "sort", "score": 2, "note": "Standing orphan pile, no owner"}, {"category": "set_in_order", "score": 2, "note": "No labeled sort shelves by range yet"},
                          {"category": "shine", "score": 3, "note": "Swept daily but no inspection standard"}, {"category": "standardize", "score": 1, "note": "Nothing posted"},
                          {"category": "sustain", "score": 3, "note": "First audit ever"}],
             "improvement_action": "Label sort shelves by range and post the sorting standard", "improvement_action_owner": "Ruth Delgado"},
            {"round_id": "r2", "date": "2026-10-15", "area": "Sorting room",
             "scores": [{"category": "sort", "score": 3, "note": "Orphan pile dispositioned"}, {"category": "set_in_order", "score": 4, "note": "Labeled sort shelves and cart staging lanes in"},
                          {"category": "shine", "score": 3, "note": "Unchanged"}, {"category": "standardize", "score": 3, "note": "Posted standard on the wall"},
                          {"category": "sustain", "score": 3, "note": "One on-schedule round behind it"}],
             "improvement_action": "Add the exception-flag bin at the sorting bench", "improvement_action_owner": "Ruth Delgado"},
            {"round_id": "r3", "date": "2026-11-04", "area": "Sorting room",
             "scores": [{"category": "sort", "score": 4, "note": "Holding"}, {"category": "set_in_order", "score": 4, "note": "Exception-flag bin in place"},
                          {"category": "shine", "score": 4, "note": "Inspection standard now posted alongside sorting standard"}, {"category": "standardize", "score": 4, "note": "Standard referenced on the T-24 SOP"},
                          {"category": "sustain", "score": 3, "note": "Two consecutive on-schedule rounds"}],
             "improvement_action": "Fold the audit into the existing weekly staff meeting for structural sustain", "improvement_action_owner": "Ruth Delgado"},
        ],
        "schedule": {"cadence_note": "Biweekly through the pilot, monthly from November", "next_round_due": "2026-12-04"},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-23", "T-23", five_s)

    control_plan = common.prepare_control_plan({
        "schema_version": 1, "artifact_id": "s2-control-plan", "tool_id": "T-22",
        "created_at": "2026-10-31T18:00:00Z", "updated_at": "2026-11-04T09:00:00Z",
        "notes": "Monitors the audited rate weekly, the throughput guardrail, and the method itself (do carts leave the sorting room in final order?). Quarterly kappa re-run guards the definition as staff turn over.",
        "monitored_items": [
            {"item_id": "mi-rate", "characteristic": "Audited misshelve rate (charter C1, primary CTQ)", "how_measured": "Daily shelf-read audit against the written definition, weekly roll-up",
             "operational_definition_ref": "s2-collection-plan", "where": "Shelving floor, rotating ranges", "frequency": "Weekly", "frequency_reason": "Matches the sampling cadence the limits were frozen from",
             "is_primary_ctq": True, "is_improve_change": False, "owner_name": "Ruth Delgado", "owner_accepted": True, "per_shift_owners": []},
            {"item_id": "mi-throughput", "characteristic": "Shelving throughput (items/staff-hour, guardrail)", "how_measured": "Shelving log, weekly roll-up",
             "operational_definition_ref": "", "where": "Shelving log", "frequency": "Weekly", "frequency_reason": "Same cadence as the primary CTQ",
             "is_primary_ctq": False, "is_improve_change": False, "owner_name": "Ruth Delgado", "owner_accepted": True, "per_shift_owners": []},
            {"item_id": "mi-method", "characteristic": "Pre-sort method adherence: do carts leave the sorting room in final shelf order?",
             "how_measured": "Spot-check a sample cart at the sorting-room exit, unannounced", "operational_definition_ref": "",
             "where": "Sorting room", "frequency": "Twice weekly", "frequency_reason": "Method backsliding grows in days, not months",
             "is_primary_ctq": False, "is_improve_change": True, "owner_name": "Ruth Delgado", "owner_accepted": True, "per_shift_owners": []},
        ],
        "ocap_entries": [
            {"ocap_id": "ocap-rate", "monitored_item_id": "mi-rate", "trigger_signal": "Any point beyond the frozen band, or 8 consecutive points one side of center",
             "action_steps": ["First response: spot-check the pre-sort method before anything else.", "Containment: re-run the mi-method spot-check on the next three carts and re-train on the spot if it fails."],
             "escalation_trigger": "Two signals inside one rolling month", "escalation_contact": "Colette Marchand (branch manager, sponsor)", "acting_owner": "Ruth Delgado"},
        ],
        "training_rows": [
            {"row_id": "tr-pages", "who": "Theo Brandt, Keisha Monroe, Sam Whitaker (shelving pages)", "sop_ref": "s2-standard-work", "by_whom": "Ruth Delgado",
             "by_when": "2026-11-10", "verified_how": "Observed demonstration of the pre-sort method against the written rules", "verified_at": "2026-11-04", "done": True},
        ],
        "as_of": "2026-11-04T09:00:00Z",
    })
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-22", "T-22", control_plan, strip=False)

    standard_work = {
        "schema_version": 1, "artifact_id": "s2-standard-work", "tool_id": "T-24",
        "created_at": "2026-11-01T09:00:00Z", "updated_at": "2026-11-01T09:00:00Z",
        "notes": "The sorting-room standard + the four shelving-defect rules as one page each.",
        "title": "Pre-sorted carts + written shelving-defect rules", "version": 1, "owner": "Ruth Delgado", "effective_date": "2026-09-28",
        "supersedes": "The unwritten, sort-at-the-shelf practice", "seeded_from_process_map_id": "s2-process-map", "linked_control_plan_id": "s2-control-plan",
        "steps": [
            {"step_id": "st-1", "order": 1, "action": "Sort returns into final shelf order in the sorting room, against the posted standard",
             "standard": "Every cart leaves the sorting room in call-number order for its range", "changed_from_prior": True, "source_step_ref": "s2", "note": "Pilot change"},
            {"step_id": "st-2", "order": 2, "action": "Clip an exception flag at sort time for series/oversize items", "standard": "Every series/oversize exception flagged before leaving the sorting room",
             "changed_from_prior": True, "source_step_ref": "s2", "note": "Pilot change"},
            {"step_id": "st-3", "order": 3, "action": "Place at the shelf from the pre-sorted cart", "standard": "Book placed in call-number order per the four written rules", "changed_from_prior": True, "source_step_ref": "s3", "note": "Pages no longer sort at the shelf"},
        ],
        "change_log": [{"version": 1, "at": "2026-11-01T09:00:00Z", "note": "v1 effective: pre-sort written as the one standard method."}],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-24", "T-24", standard_work)

    common.gate_check(recorder, PROJECT_ID, "control_to_wrap")

    # ----------------------------------------------------------------- Wrap
    a3 = {
        "schema_version": 1, "artifact_id": "s2-a3", "tool_id": "T-25",
        "created_at": "2026-11-05T09:00:00Z", "updated_at": "2026-11-05T09:00:00Z",
        "notes": "The measurement stop is told as a finding, not an embarrassment: round-1 kappa, the fix, round 2, and the baseline that came back HIGHER than the broken pre-log.",
        "panels": [
            {"panel": "background", "seeded_from": {"artifact_ref": CHARTER_REF, "tool_id": "T-03", "fields": ["problem_statement", "business_impact"]},
             "narrative": "Patrons and desk staff report the catalog says a book is on the shelf and it isn't there. An informal closers' log suggested ~3.8% -- but the two counters had never agreed on a definition (a fingerprint hiding in the logged_by column).", "seeded_at": "2026-11-05T09:05:00Z"},
            {"panel": "current_condition", "seeded_from": {"artifact_ref": "written-definition baseline audit (T-13 via T-21/T-10)", "tool_id": "T-13", "fields": ["p_bar", "stable"]},
             "narrative": f"The measurement stop: T-12 round 1 failed (kappa 0.336, EXIT-02) -- the run stopped, no baseline, no chart. After the written-definition fix, round 2 passed (kappa 0.878), and the baseline came back HIGHER than the broken log: p-bar {baseline_pbar:.4f} (stable, 21 subgroups), not the pre-log's ~3.8% -- the broken gauge had hidden roughly two-fifths of the problem.", "seeded_at": "2026-11-05T09:10:00Z"},
            {"panel": "goal", "seeded_from": {"artifact_ref": CHARTER_REF, "tool_id": "T-03", "fields": ["goal"]},
             "narrative": f"Halve the audited misshelve proportion from {baseline_pbar:.4f} to {goal_p:.4f} by 2026-11-30, without dropping shelving throughput more than 10%.", "seeded_at": "2026-11-05T09:12:00Z"},
            {"panel": "analysis", "seeded_from": {"artifact_ref": "s2-fishbone", "tool_id": "T-15", "fields": ["causes", "effect"]},
             "narrative": "Out-of-order-within-bay (48.9%) and wrong-bay (32.2%) are the engine-verified 81.1% vital few. Root cause: sorting happens at the shelf, on a room with no sortable standard -- the section chi-square screen shows juvenile hit hardest, where series conventions bite.", "seeded_at": "2026-11-05T09:16:00Z"},
            {"panel": "countermeasures", "seeded_from": {"artifact_ref": "s2-solution-matrix", "tool_id": "T-18", "fields": ["ranked_fix_list"]},
             "narrative": "Pre-sorted carts + posted standard ranked first, directly at the verified root; double-checking at the shelf and a training-only workshop both ranked lower (symptom, not root).", "seeded_at": "2026-11-05T09:20:00Z"},
            {"panel": "results", "seeded_from": {"artifact_ref": "s2-proof", "tool_id": "T-20", "fields": ["gap", "verdict", "test_result"]},
             "narrative": "Settled-weeks two-proportion z: baseline vs settled weeks, z=4.01, p=6.0e-05 -- significant. Full 24-day after window: threshold met (rate under 4.0%), verdict weakened by the declared fall reading-program confound (direction: can only push the rate up). Gap recovery over 100% of the halving goal.", "seeded_at": "2026-11-05T09:26:00Z"},
            {"panel": "follow_up_control", "seeded_from": {"artifact_ref": "s2-control-plan", "tool_id": "T-22", "fields": ["monitored_items", "ocap_entries"]},
             "narrative": "p-chart limits history on one artifact: baseline freeze, the improvement arriving as a rule-4 run on the old limits, then a logged recalculation on the 24-day post window. Control plan monitors the rate weekly, throughput, and the method itself; Ruth Delgado accepted the owner role 2026-11-04. Quarterly kappa re-run guards the definition.", "seeded_at": "2026-11-05T09:30:00Z"},
            {"panel": "lessons", "seeded_from": {"artifact_ref": "s2-proof", "tool_id": "T-20", "fields": ["gap", "verdict"]},
             "narrative": "The measurement stop is the project's real lesson: a plausible-looking log would have frozen a ~3.8% baseline nobody could trust, and every downstream number would have inherited an unchecked gauge. Stopping at EXIT-02, fixing the definition, and re-baselining found a HIGHER, honest number -- the strongest argument for having stopped.", "seeded_at": "2026-11-05T09:34:00Z"},
        ],
        "closure": {"objectives_input": {"charter_baseline_value": baseline_pbar, "charter_goal_value": goal_p, "achieved_value": after_defects / after_n, "direction": "lower_is_better"}},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-25", "T-25", a3)
