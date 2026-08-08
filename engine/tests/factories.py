"""Valid-by-default dict factories for every Define/Intake artifact. Tests
mutate a specific field off these bases to exercise one accept/reject path
at a time, instead of re-typing a full artifact per test. Not a test module
itself (no test_ prefix) -- pytest won't collect it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sigma_engine.artifacts.a3 import PANEL_ORDER
from sigma_engine.artifacts.copq import CopqRow, compute_copq_total
from sigma_engine.artifacts.five_s import FIVE_S_CATEGORIES

TS = "2026-08-07T00:00:00"

DEMO_CHARTER_PATH = Path(__file__).resolve().parents[2] / "demo" / "coffee-bar" / "define" / "charter.json"


def load_demo_charter() -> dict[str, Any]:
    """The real Coffee Bar demo charter (M1 export brief's test fixture),
    as a plain dict -- callers validate it against CharterArtifact."""
    return json.loads(DEMO_CHARTER_PATH.read_text(encoding="utf-8"))


def make_picker(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1,
        "artifact_id": "picker-001",
        "tool_id": "T-01",
        "created_at": TS,
        "updated_at": TS,
        "scope_narrow": {"answer": True, "detail": "Only line-2 scrap, not the whole plant."},
        "measurable_outcome": {"answer": True, "detail": "Scrap % is tracked daily in the QC log."},
        "data_obtainable": {"answer": True, "detail": "QC log exports to CSV weekly."},
        "process_owner_engaged": {"answer": True, "detail": "Line-2 supervisor Maria asked for this."},
        "business_impact_plausible": {"answer": True, "detail": "Scrap is costing about $40k/quarter."},
        "route": "full-DMAIC",
    }
    base.update(overrides)
    return base


def make_copq_rows() -> list[dict[str, Any]]:
    return [
        {
            "category": "scrap", "custom_label": None, "quantity": 500, "rate": 12.0,
            "period": "Q2 2026", "basis": "Q2 scrap log export", "is_estimate": False,
        },
        {
            "category": "rework", "custom_label": None, "quantity": 80, "rate": 45.0,
            "period": "Q2 2026", "basis": "labor hours x loaded rate", "is_estimate": False,
        },
    ]


def make_copq(**overrides: Any) -> dict[str, Any]:
    rows = overrides.pop("rows") if "rows" in overrides else make_copq_rows()
    total = compute_copq_total([CopqRow.model_validate(r) for r in rows])
    base = {
        "schema_version": 1,
        "artifact_id": "copq-001",
        "tool_id": "T-02",
        "created_at": TS,
        "updated_at": TS,
        "rows": rows,
        "total": total.model_dump(mode="json"),
    }
    base.update(overrides)
    return base


def make_sipoc(step_count: int = 5, **overrides: Any) -> dict[str, Any]:
    steps = [{"step_number": i + 1, "description": f"Step {i + 1}"} for i in range(step_count)]
    base = {
        "schema_version": 1,
        "artifact_id": "sipoc-001",
        "tool_id": "T-04",
        "created_at": TS,
        "updated_at": TS,
        "supplier_input_pairs": [{"supplier": "Resin vendor", "input": "Raw resin pellets"}],
        "process_steps": steps,
        "output_customer_pairs": [{"output": "Molded part", "customer": "Assembly line"}],
        "scope_start": "Resin received",
        "scope_end": "Molded part inspected",
    }
    base.update(overrides)
    return base


def make_voc_ctq(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1,
        "artifact_id": "voc-001",
        "tool_id": "T-05",
        "created_at": TS,
        "updated_at": TS,
        "customers": [{"role": "external - end buyer", "is_internal": False}],
        "statements": [
            {
                "statement_id": "S1", "customer_role": "external - end buyer",
                "text": "Parts sometimes arrive cracked.", "source": "complaint_log",
                "source_detail": "2026 Q2 complaint log",
            }
        ],
        "needs": [{"need_id": "N1", "statement_ids": ["S1"], "text": "Parts must arrive intact"}],
        "ctqs": [
            {
                "ctq_id": "C1", "need_id": "N1", "measure": "crack rate at receiving",
                "direction": "lower_is_better", "target": "<1%",
                "critical_vs_easy_check": (
                    "Customer-critical: cracked parts are returned and re-ordered; "
                    "not chosen for ease of measurement."
                ),
            }
        ],
        "primary_ctq_id": "C1",
        "charter_metric_link": "matches charter primary metric: line-2 scrap rate",
    }
    base.update(overrides)
    return base


def make_continuous_msa(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1,
        "artifact_id": "msa-001",
        "tool_id": "T-12",
        "created_at": TS,
        "updated_at": TS,
        "data_type": "continuous",
        "operator": "Sam Lee",
        "gauge_name": "digital calipers",
        "gauge_increment": 0.01,
        "usl": 20.0,
        "lsl": 0.0,
        "continuous_items": [
            {"item_id": f"item-{i}", "readings": [10.0 + i * 0.5, 10.0 + i * 0.5 + 0.02]} for i in range(10)
        ],
    }
    base.update(overrides)
    return base


def make_attribute_msa(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1,
        "artifact_id": "msa-attr-001",
        "tool_id": "T-12",
        "created_at": TS,
        "updated_at": TS,
        "data_type": "attribute",
        "operator": "Sam Lee",
        "attribute_items": [
            {"item_id": f"item-{i}", "rater_a": i % 2 == 0, "rater_b": i % 2 == 0} for i in range(12)
        ],
    }
    base.update(overrides)
    return base


def make_process_map_lanes() -> list[dict[str, Any]]:
    return [
        {"lane_id": "lane-1", "name": "Customer", "owner": "Front counter lead"},
        {"lane_id": "lane-2", "name": "Barista", "owner": "Shift lead"},
    ]


def make_process_map_steps() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "step-1", "lane_id": "lane-1", "name": "Place order", "order": 1,
            "step_type": "value_add", "reason": "Customer directly asks for what they want.",
            "time_minutes": 1.0, "defect_point": False, "strata": ["morning"], "wastes": [],
        },
        {
            "step_id": "step-2", "lane_id": "lane-2", "name": "Wait for register", "order": 1,
            "step_type": "non_value_add", "reason": "Customer gets nothing while waiting.",
            "time_minutes": 4.0, "defect_point": False, "strata": [],
            "wastes": [{"waste_id": "waiting", "note": "Line backs up ~4 min at the morning peak."}],
        },
        {
            "step_id": "step-3", "lane_id": "lane-2", "name": "Make drink", "order": 2,
            "step_type": "value_add", "reason": "Directly produces what the customer is paying for.",
            "time_minutes": 3.0, "defect_point": True, "strata": [], "wastes": [],
        },
    ]


def make_process_map(**overrides: Any) -> dict[str, Any]:
    lanes = overrides.pop("lanes") if "lanes" in overrides else make_process_map_lanes()
    steps = overrides.pop("steps") if "steps" in overrides else make_process_map_steps()
    connectors = (
        overrides.pop("connectors") if "connectors" in overrides
        else [{"from_step": "step-1", "to_step": "step-2", "label": None}, {"from_step": "step-2", "to_step": "step-3", "label": None}]
    )
    base = {
        "schema_version": 1,
        "artifact_id": "process-map-001",
        "tool_id": "T-06",
        "created_at": TS,
        "updated_at": TS,
        "lanes": lanes,
        "steps": steps,
        "connectors": connectors,
        "demand": None,
        "layout": {},
    }
    base.update(overrides)
    return base


def make_floor_plan_ref(**overrides: Any) -> dict[str, Any]:
    base = {
        "image_id": "floorplan-1", "source_filename": "floor.png",
        "sha256": "a" * 64, "width_px": 800, "height_px": 600,
    }
    base.update(overrides)
    return base


def make_operators() -> list[dict[str, Any]]:
    return [
        {"operator_id": "op-1", "name": "Maria Ortiz", "color_index": 0},
        {"operator_id": "op-2", "name": "Sam Lee", "color_index": 1},
    ]


def make_calibration(**overrides: Any) -> dict[str, Any]:
    # 100px = 10m -> 10 px/m, chosen so every hand-computable fixture route
    # below (multiples of 10px) converts to a round number of meters.
    base = {"point_a": {"x": 0.0, "y": 0.0}, "point_b": {"x": 100.0, "y": 0.0}, "real_length": 10.0, "unit": "meters"}
    base.update(overrides)
    return base


def make_spaghetti_routes() -> list[dict[str, Any]]:
    return [
        {
            # Two legs of a right angle, 300px + 400px = 700px -> 70m at
            # 10px/m -- the smoke test's own hand-computable fixture route.
            "route_id": "route-1", "operator_id": "op-1", "trip_label": "Register to grinder",
            "frequency_per_day": 6, "layout_mode": "current",
            "points": [{"x": 0.0, "y": 0.0}, {"x": 300.0, "y": 0.0}, {"x": 300.0, "y": 400.0}],
        },
    ]


def make_spaghetti(**overrides: Any) -> dict[str, Any]:
    operators = overrides.pop("operators") if "operators" in overrides else make_operators()
    routes = overrides.pop("routes") if "routes" in overrides else make_spaghetti_routes()
    floor_plan = overrides.pop("floor_plan") if "floor_plan" in overrides else make_floor_plan_ref()
    calibration = overrides.pop("calibration") if "calibration" in overrides else make_calibration()
    base = {
        "schema_version": 1,
        "artifact_id": "spaghetti-001",
        "tool_id": "T-07",
        "created_at": TS,
        "updated_at": TS,
        "floor_plan": floor_plan,
        "calibration": calibration,
        "operators": operators,
        "routes": routes,
        "walk_speed_override_per_minute": None,
        "observation_window": {"when": "Tuesday morning rush", "duration": "45 min", "shift": "AM shift"},
    }
    base.update(overrides)
    return base


def make_charter(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1,
        "artifact_id": "charter-001",
        "tool_id": "T-03",
        "created_at": TS,
        "updated_at": TS,
        "problem_statement": {
            "what": "Line 2 scrap rate",
            "where": "Line 2, Plant A",
            "when": "Q2 2026",
            "magnitude": {"number": 6.2, "unit": "%", "period": "Q2 2026"},
        },
        "goal": {
            "statement": "Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026.",
            "metric_name": "line-2 scrap rate",
            "baseline_value": 6.2,
            "target_value": 3.0,
            "unit": "%",
            "target_date": "2026-11-30",
            "consequential_metrics": ["line-2 throughput"],
        },
        "scope": {"in_scope": "Line 2 molding station only", "out_scope": "Lines 1 and 3, packaging"},
        "team": [
            {"name": "Maria Ortiz", "role": "Line-2 supervisor"},
            {"name": "Sam Lee", "role": "QC analyst"},
        ],
        "process_owner": {"name": "Maria Ortiz", "role": "Line-2 supervisor"},
        "timeline": [
            {"name": "Define complete", "date": "2026-08-21"},
            {"name": "Project close", "date": "2026-11-30"},
        ],
        "business_impact": {"amount": 40000.0, "unit": "dollars", "basis": "Q2 actuals x 4"},
        "risks": [
            {
                "risk": "Key operator on leave during pilot",
                "likelihood": "medium",
                "impact": "medium",
                "mitigation": "Cross-train a backup operator",
                "owner": "Maria Ortiz",
            }
        ],
    }
    base.update(overrides)
    return base


def make_check_sheet_categories() -> list[dict[str, Any]]:
    return [
        {"category_id": "cat-scratch", "label": "Scratch"},
        {"category_id": "cat-crack", "label": "Crack"},
        {"category_id": "cat-short-pour", "label": "Short pour"},
    ]


def make_check_sheet_entries() -> list[dict[str, Any]]:
    return [
        {"entry_id": "e1", "category_id": "cat-scratch", "timestamp": "2026-08-07T08:00:00", "strata": {"shift": "morning"}, "note": ""},
        {"entry_id": "e2", "category_id": "cat-scratch", "timestamp": "2026-08-07T08:05:00", "strata": {"shift": "morning"}, "note": ""},
        {"entry_id": "e3", "category_id": "cat-crack", "timestamp": "2026-08-07T13:00:00", "strata": {"shift": "afternoon"}, "note": "chipped on drop"},
    ]


def make_check_sheet(**overrides: Any) -> dict[str, Any]:
    categories = overrides.pop("categories") if "categories" in overrides else make_check_sheet_categories()
    strata_fields = overrides.pop("strata_fields") if "strata_fields" in overrides else [{"key": "shift", "label": "Shift"}]
    entries = overrides.pop("entries") if "entries" in overrides else make_check_sheet_entries()
    base = {
        "schema_version": 1,
        "artifact_id": "checksheet-001",
        "tool_id": "T-08",
        "created_at": TS,
        "updated_at": TS,
        "categories": categories,
        "strata_fields": strata_fields,
        "entries": entries,
    }
    base.update(overrides)
    return base


# Hand-computable 5-cycle fixture (task brief): element "steam-milk"'s times
# [9, 8, 40, 10, 9] sort to [8, 9, 9, 10, 40] -- n=5 makes every quartile an
# exact array index (no interpolation): Q1 = sorted[1] = 9, Q3 = sorted[3] =
# 10, IQR = 1, fences = (9 - 1.5*1, 10 + 1.5*1) = (7.5, 11.5) -- cycle 3's
# 40s is the one obvious outlier. Element "pull-shot" is a clean control:
# [11, 12, 12, 13, 13] -> Q1=12, Q3=13, IQR=1, fences=(10.5, 14.5), nothing
# flagged.
def make_time_study_elements() -> list[dict[str, Any]]:
    return [
        {"element_id": "steam-milk", "name": "Steam milk", "description": "From pitcher-down to pitcher-up."},
        {"element_id": "pull-shot", "name": "Pull shot", "description": "Grinder start to cup full."},
    ]


def make_time_study_cycles() -> list[dict[str, Any]]:
    steam_times = [9, 8, 40, 10, 9]
    shot_times = [11, 12, 12, 13, 13]
    return [
        {
            "cycle_number": i + 1,
            "element_times": [
                {"element_id": "steam-milk", "seconds": steam_times[i]},
                {"element_id": "pull-shot", "seconds": shot_times[i]},
            ],
            "observer_note": "milk pitcher slipped, redone" if i == 2 else "",
        }
        for i in range(5)
    ]


def make_data_collection_plan(**overrides: Any) -> dict[str, Any]:
    """A complete, prescore-clean T-11 Data Collection Plan -- every field
    a real plan would carry, so tests mutate one field off this base to
    exercise a single flag/rejection at a time (this module's own
    convention, e.g. make_check_sheet above)."""
    base = {
        "schema_version": 1,
        "artifact_id": "dcp-001",
        "tool_id": "T-11",
        "created_at": TS,
        "updated_at": TS,
        "metric_name": "order-to-handoff minutes",
        "charter_metric_id": "line-2 scrap rate",
        "operational_definition": {
            "what_measured": "Minutes from order placed to order handed to customer",
            "how_instrument": "POS timestamp minus order timestamp, read from the register log",
            "precision_unit": "minutes, to the nearest 0.1",
            "starts_when": "Order is placed at the register",
            "stops_when": "Drink is handed across the counter",
            "two_people_confirmed": True,
        },
        "data_type": "continuous",
        "stratification_factors": [
            {"name": "shift", "values_expected": ["morning", "afternoon"]},
            {"name": "order_type", "values_expected": ["register", "mobile"]},
        ],
        "no_stratification_reason": "",
        "logistics": {
            "who_collects": "Shift lead, via the POS export",
            "where_collected": "Front counter register",
            "when_how_often": "Continuously; exported weekly",
            "planned_n": 30,
            "sample_size_rationale": "I-MR baseline rule of thumb: 25-30 points (T-11 sample-size panel)",
        },
        "bias_note": "POS log captures every order -- not a convenience sample.",
    }
    base.update(overrides)
    return base


def make_hypothesis(**overrides: Any) -> dict[str, Any]:
    """A complete, routable T-17 HypothesisRunArtifact -- defaults to the
    NIST §7.3.1 two-independent-samples worked example (welch_two_sample_t,
    clears every floor), so most tests mutate one `question` field off
    this base rather than re-typing a full question per test."""
    question = overrides.pop("question") if "question" in overrides else {
        "question_text": "Is process 2 faster than process 1?",
        "comparison_type": "two_independent",
        "groups": [
            {"label": "Process 1 (Old)", "values": [32, 37, 35, 28, 41, 44, 35, 31, 34, 38, 42]},
            {"label": "Process 2 (New)", "values": [36, 31, 30, 31, 34, 36, 29, 32, 31]},
        ],
    }
    base = {
        "schema_version": 1,
        "artifact_id": "hyp-001",
        "tool_id": "T-17",
        "created_at": TS,
        "updated_at": TS,
        "question": question,
        "declared_primary": True,
    }
    base.update(overrides)
    return base


def make_fishbone_causes() -> list[dict[str, Any]]:
    return [
        {
            "cause_id": "c-1", "branch": "method", "text": "Fixture alignment not checked before shift start",
            "parent_cause_id": None, "status": "verified", "why_chain_position": None,
            "evidence": {"kind": "check_sheet", "ref": "checksheet-001"},
        },
        {
            "cause_id": "c-1-why2", "branch": "method", "text": "Checklist never posted at the fixture station",
            "parent_cause_id": "c-1", "status": "investigating", "why_chain_position": 2, "evidence": None,
        },
        {
            "cause_id": "c-2", "branch": "machine", "text": "Injector pressure drifts low over a shift",
            "parent_cause_id": None, "status": "candidate", "why_chain_position": None, "evidence": None,
        },
        {
            "cause_id": "c-3", "branch": "machine", "text": "Preventive maintenance skipped on several scheduled intervals",
            "parent_cause_id": None, "status": "ruled_out", "why_chain_position": None,
            "evidence": {"kind": "observation_note", "ref": "PM log shows maintenance done on schedule for all of Q2."},
        },
    ]


def make_fishbone(**overrides: Any) -> dict[str, Any]:
    causes = overrides.pop("causes") if "causes" in overrides else make_fishbone_causes()
    base = {
        "schema_version": 1,
        "artifact_id": "fishbone-001",
        "tool_id": "T-15",
        "created_at": TS,
        "updated_at": TS,
        "effect": {"text": "Line 2 scrap rate averaged 6.2% in Q2", "charter_ref": "charter-001"},
        "causes": causes,
        "layout": {},
    }
    base.update(overrides)
    return base


# Hand-checkable RPN + severity-first-then-RPN ordering fixture (task
# brief): row-a (sev 9, occ 3, det 2 -> rpn 54) and row-c (sev 9, occ 2,
# det 2 -> rpn 36) both outrank row-b (sev 7, occ 8, det 8 -> rpn 448)
# despite row-b's RPN being the largest of the three -- severity-first
# means a lower-severity row can never outrank a higher-severity one on
# RPN alone (rubric R-ANA-03's stated RPN limitation). row-a's effect is
# deliberately safety-worded and left without an action, so it is also the
# fixture for blocking_flags.
def make_fmea_rows() -> list[dict[str, Any]]:
    return [
        {
            "row_id": "row-a", "process_step_ref": None, "step_name": "Mold part",
            "failure_mode": "Short pour incomplete fill", "effect": "Part fails safety inspection, unsafe to ship",
            "cause": "Injector pressure drifts low", "severity": 9, "occurrence": 3, "detection": 2,
            "action": "", "action_owner": "", "action_due": None, "action_status": "open", "anchors_consulted": True,
        },
        {
            "row_id": "row-b", "process_step_ref": None, "step_name": "Package",
            "failure_mode": "Wrong label applied", "effect": "Customer receives wrong item, reorder needed",
            "cause": "Label roll swapped by mistake", "severity": 7, "occurrence": 8, "detection": 8,
            "action": "Add barcode scan check before sealing", "action_owner": "Sam Lee", "action_due": "2026-09-01",
            "action_status": "open", "anchors_consulted": True,
        },
        {
            "row_id": "row-c", "process_step_ref": "step-3", "step_name": "Mold part",
            "failure_mode": "Flash on edge", "effect": "Sharp edge injury risk to assembler",
            "cause": "Mold halves misaligned", "severity": 9, "occurrence": 2, "detection": 2,
            "action": "Daily alignment check before first shift", "action_owner": "Maria Ortiz",
            "action_due": "2026-08-15", "action_status": "open", "anchors_consulted": True,
        },
    ]


def make_fmea(**overrides: Any) -> dict[str, Any]:
    rows = overrides.pop("rows") if "rows" in overrides else make_fmea_rows()
    base = {
        "schema_version": 1,
        "artifact_id": "fmea-001",
        "tool_id": "T-16",
        "created_at": TS,
        "updated_at": TS,
        "rows": rows,
    }
    base.update(overrides)
    return base


def make_time_study(**overrides: Any) -> dict[str, Any]:
    elements = overrides.pop("elements") if "elements" in overrides else make_time_study_elements()
    cycles = overrides.pop("cycles") if "cycles" in overrides else make_time_study_cycles()
    interval_observations = overrides.pop("interval_observations") if "interval_observations" in overrides else []
    base = {
        "schema_version": 1,
        "artifact_id": "timestudy-001",
        "tool_id": "T-09",
        "created_at": TS,
        "updated_at": TS,
        "elements": elements,
        "cycles": cycles,
        "interval_observations": interval_observations,
    }
    base.update(overrides)
    return base


# Hand-checkable weighted-matrix fixture (task brief): criteria cost(w=2)/
# speed(w=3). s-1 scores cost=4,speed=5 -> weighted_total = 4*2 + 5*3 = 23.
# s-2 scores cost=5,speed=2 -> weighted_total = 5*2 + 2*3 = 16. s-1 outranks
# s-2 (23 > 16) despite s-2's higher impact/effort ratings -- weighted
# total wins whenever a solution has one. s-3 is deliberately unlinked
# (linked_cause_ids=[]) and unscored: the ranked-list/unlinked-flag fixture.
def make_solution_matrix_criteria() -> list[dict[str, Any]]:
    return [
        {"criterion_id": "cost", "name": "Cost to implement", "weight": 2.0, "declared_at": TS},
        {"criterion_id": "speed", "name": "Speed to roll out", "weight": 3.0, "declared_at": TS},
    ]


def make_solution_matrix_solutions() -> list[dict[str, Any]]:
    return [
        {
            "solution_id": "s-1", "name": "Add fixture alignment checklist", "description": "Pre-shift checklist at the fixture station.",
            "linked_cause_ids": ["c-1"], "impact": 4, "effort": 2,
            "criterion_scores": [{"criterion_id": "cost", "score": 4, "scored_at": TS}, {"criterion_id": "speed", "score": 5, "scored_at": TS}],
        },
        {
            "solution_id": "s-2", "name": "Replace the injector", "description": "Swap the drifting injector for a new unit.",
            "linked_cause_ids": ["c-2"], "impact": 5, "effort": 5,
            "criterion_scores": [{"criterion_id": "cost", "score": 5, "scored_at": TS}, {"criterion_id": "speed", "score": 2, "scored_at": TS}],
        },
        {
            "solution_id": "s-3", "name": "Unlinked brainstorm idea", "description": "Not yet tied to a verified cause.",
            "linked_cause_ids": [], "impact": 3, "effort": 3, "criterion_scores": [],
        },
    ]


def make_solution_matrix(**overrides: Any) -> dict[str, Any]:
    solutions = overrides.pop("solutions") if "solutions" in overrides else make_solution_matrix_solutions()
    criteria = overrides.pop("criteria") if "criteria" in overrides else make_solution_matrix_criteria()
    base = {
        "schema_version": 1, "artifact_id": "solmatrix-001", "tool_id": "T-18",
        "created_at": TS, "updated_at": TS, "solutions": solutions, "criteria": criteria,
    }
    base.update(overrides)
    return base


# Hand-checkable UNWEIGHTED fixture (no criteria -- impact-desc/effort-asc
# fallback): s-a and s-b tie impact=5; s-a's lower effort (2 < 4) ranks it
# first. s-c's impact=2 is lowest, so it ranks last regardless of effort.
# Expected order: s-a, s-b, s-c.
def make_unweighted_solutions() -> list[dict[str, Any]]:
    return [
        {"solution_id": "s-a", "name": "Quick label fix", "description": "", "linked_cause_ids": ["c-1"], "impact": 5, "effort": 2, "criterion_scores": []},
        {"solution_id": "s-b", "name": "Bigger rework", "description": "", "linked_cause_ids": ["c-1"], "impact": 5, "effort": 4, "criterion_scores": []},
        {"solution_id": "s-c", "name": "Low-value tweak", "description": "", "linked_cause_ids": ["c-2"], "impact": 2, "effort": 1, "criterion_scores": []},
    ]


def make_pilot_plan_confounder_checklist(**overrides: Any) -> dict[str, Any]:
    base = {
        "staffing": {"changed": False, "note": "No staffing changes planned during the pilot window."},
        "season": {"changed": False, "note": "No seasonal demand shift expected in this window."},
        "demand": {"changed": False, "note": "Order volume has been steady for six weeks."},
        "measurement": {"changed": False, "note": "Same QC log, same operational definition as baseline."},
        "other": {"changed": False, "note": "No other process changes planned."},
    }
    base.update(overrides)
    return base


def make_pilot_plan(**overrides: Any) -> dict[str, Any]:
    """A complete, prescore-clean T-19 Pilot Plan -- one declared change,
    matching the single entry in `changes` (the EXIT-10 trigger fixture is
    built by appending a second entry to `changes` off this base, task
    brief's own hand-checkable case)."""
    statement = "Add a fixture alignment checklist before each shift"
    changes = overrides.pop("changes") if "changes" in overrides else [{"change_id": "ch-1", "text": statement}]
    confounder_checklist = overrides.pop("confounder_checklist") if "confounder_checklist" in overrides else make_pilot_plan_confounder_checklist()
    base = {
        "schema_version": 1, "artifact_id": "pilot-001", "tool_id": "T-19",
        "created_at": TS, "updated_at": TS,
        "the_one_change": {"statement": statement, "linked_solution_id": "s-1", "linked_cause_ids": ["c-1"]},
        "changes": changes,
        "comparison_design": {"kind": "before_period", "description": "Prior 4 weeks of Line-2 scrap-rate data before the checklist starts."},
        "inclusion": {
            "who_or_what": "Line 2, all three shifts",
            "how_selected": "Line 2 is the only line with the fixture-alignment issue.",
            "honesty_note": "Not randomized -- Line 2 was picked because it's the only line affected.",
        },
        "success_threshold": {"metric_ref": "line-2 scrap rate", "direction": "lower_is_better", "value": 4.5, "declared_at": TS},
        "analysis_plan": {"expected_route": "welch_two_sample_t", "rationale": "Two independent time windows of continuous scrap-rate data."},
        "falsification_line": "If scrap rate stays above 4.5% for two full weeks after rollout, the checklist did not fix it.",
        "confounder_checklist": confounder_checklist,
        "status": "designed",
    }
    base.update(overrides)
    return base


def make_declared_package(**overrides: Any) -> dict[str, Any]:
    base = {
        "rationale": (
            "The fixture head and drive motor ship from the vendor as one sealed cartridge -- replacing one "
            "without the other voids the seal, and the vendor will not sell them separately."
        ),
        "components": ["fixture head", "drive motor"],
    }
    base.update(overrides)
    return base


def make_pilot_plan_with_package(**overrides: Any) -> dict[str, Any]:
    """A pilot plan declaring a 2-component inseparable package (rubric
    R-IMP-02's carve-out, task brief's own hand-checkable case) --
    changes[] aligned 1:1 with declared_package.components (task brief:
    "align them 1:1"), so EXIT-10 does not fire even with two entries."""
    package = overrides.pop("declared_package") if "declared_package" in overrides else make_declared_package()
    changes = overrides.pop("changes") if "changes" in overrides else [
        {"change_id": "ch-1", "text": "Replace the fixture head"},
        {"change_id": "ch-2", "text": "Replace the drive motor"},
    ]
    the_one_change = overrides.pop("the_one_change") if "the_one_change" in overrides else {
        "statement": "Replace the fixture-head/drive-motor cartridge (declared package -- see declared_package)",
        "linked_solution_id": "s-1", "linked_cause_ids": ["c-1"],
    }
    return make_pilot_plan(changes=changes, declared_package=package, the_one_change=the_one_change, **overrides)


# T-21 Control Chart fixtures. IMR: the same 24-point coffee-bar
# wait_seconds column already asserted stable by the desktop smoke test
# (tools/fixtures/coffee-bar-wait-times.csv) -- one real demo dataset
# threaded through both the T-13 baseline and the T-21 control chart.
COFFEE_BAR_WAIT_SECONDS = [95, 91, 98, 93, 97, 92, 99, 94, 96, 90, 98, 93, 95, 91, 99, 94, 97, 92, 96, 90, 98, 93, 95, 91]

# WECO rules 2/3: opt-in, verified default-off (docs/traceability-matrix.md
# §4a / §VI.A.1). Shared between test_stats_imr.py (the stats-module-level
# proof) and test_artifacts_control_chart.py (the T-21 artifact-level proof
# that the toggle threads through to monitoring signals) -- one canonical
# fixture, not two copies that could quietly drift apart.
#
# n=20 (clears the EXIT-04 companion floor), tightly alternating baseline
# (MR always 0.4) so sigma_within is small and predictable, then 2 of the
# last 3 points pushed to 2-3 sigma above center (zone-A territory) --
# verified by construction to trigger rule 2 alone: xbar=50.11,
# sigma_within=0.41993, zone-A upper=50.95, and no point ever reaches the
# 3-sigma UCL (51.37), so rule 1 never fires.
RULE2_ONLY_DATA = [
    50, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2,
    49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8,
    51.0, 50.2, 51.0,
]

# Same baseline shape; last 5 points are 4-of-5 beyond 1-sigma (zone-B),
# never reaching zone-A or the 3-sigma UCL -- rule 3 alone.
RULE3_ONLY_DATA = [
    50, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8, 50.2,
    49.8, 50.2, 49.8, 50.2, 49.8, 50.2, 49.8,
    50.5, 50.5, 50.5, 50.5, 49.8,
]


def make_control_chart_imr(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": 1, "artifact_id": "cc-imr-001", "tool_id": "T-21",
        "created_at": TS, "updated_at": TS,
        "chart_type": "imr", "metric_ref": "order-to-handoff wait seconds",
        "selector": {"data_shape": "continuous"},
        "source": {"kind": "dataset", "dataset_id": "ds-coffee-bar", "dataset_sha256": "c" * 64, "column": "wait_seconds"},
        "imr_values": list(COFFEE_BAR_WAIT_SECONDS),
        "freeze_requested": True, "action_at": TS,
    }
    base.update(overrides)
    return base


# p-chart: 20 clean subgroups (n=100, 20 defective each -- p=0.20, well
# inside its own limits) -- the freeze-floor-clearing, no-signal fixture.
def make_control_chart_p_subgroups(count: int = 20, n: int = 100, defective: int = 20) -> list[dict[str, Any]]:
    return [{"label": f"day-{i + 1}", "n": n, "defective_count": defective} for i in range(count)]


def make_control_chart_p(**overrides: Any) -> dict[str, Any]:
    subgroups = overrides.pop("p_subgroups") if "p_subgroups" in overrides else make_control_chart_p_subgroups()
    base = {
        "schema_version": 1, "artifact_id": "cc-p-001", "tool_id": "T-21",
        "created_at": TS, "updated_at": TS,
        "chart_type": "p", "metric_ref": "print-shop defective-order rate",
        "selector": {"data_shape": "attribute", "defectives_or_defects": "defectives"},
        "source": {"kind": "dataset", "dataset_id": "ds-print-shop", "dataset_sha256": "d" * 64, "column": "defective"},
        "p_subgroups": subgroups,
        "freeze_requested": True, "action_at": TS,
    }
    base.update(overrides)
    return base


# T-20 Before/After Proof fixture, threaded onto the same pilot demo as
# make_pilot_plan above (metric "line-2 scrap rate", threshold <=4.5,
# charter baseline 6.2 -> goal 3.0, matching make_charter's own goal
# block): before mean = 61.8/10 = 6.18; after mean = 40.3/10 = 4.03,
# clearing the 4.5 threshold (met) but not yet the charter's 3.0 goal --
# original_gap = 6.2-3.0 = 3.2, recovered = 6.2-4.03 = 2.17 (67.8%),
# remaining = 1.03 (partial recovery, hand-checkable).
PROOF_BEFORE_VALUES = [6.0, 6.4, 6.1, 6.3, 5.9, 6.5, 6.2, 6.0, 6.3, 6.1]
PROOF_AFTER_VALUES_MET = [4.2, 3.9, 4.1, 4.0, 3.8, 4.3, 4.0, 3.9, 4.1, 4.0]
PROOF_AFTER_VALUES_NOT_MET = [5.0, 4.9, 5.1, 5.0, 4.8, 5.2, 5.0, 4.9, 5.1, 5.0]

# Fix 3 (weighted DataRef): the "Print Shop shape" fixture -- 24 daily
# subgroups, variable n. Same raw (n, defective_count) pairs as the real
# demo/print-shop/control/control-chart.json p-chart freeze window (k=24,
# total_defectives=69, total_n=1821, p_bar=0.03789126853377265),
# reproduced here as a hand-checkable engine-test fixture rather than a
# file dependency on demo/ (which the director reconciles separately).
# Each day's own proportion (defective_count/n) is a DataRef `value`; that
# day's `n` is the matching `weight`. Pooled (weighted) mean = 69/1821 =
# 0.03789126853377265; unweighted mean-of-daily-proportions = 0.03682244848264809
# -- both real numbers off the same 24 days' counts, materially different
# (the exact divergence rubric R-IMP-03 #1 / R-IMP-04 exists to prevent).
PRINT_SHOP_AFTER_N = [80, 72, 76, 74, 69, 58, 85, 82, 69, 72, 87, 60, 79, 71, 73, 73, 80, 58, 90, 91, 85, 89, 81, 67]
PRINT_SHOP_AFTER_DEFECTIVE = [3, 3, 3, 1, 2, 1, 6, 2, 2, 3, 4, 0, 4, 1, 4, 2, 3, 2, 6, 2, 2, 5, 5, 3]
PRINT_SHOP_AFTER_PROPORTIONS = [d / n for d, n in zip(PRINT_SHOP_AFTER_DEFECTIVE, PRINT_SHOP_AFTER_N)]


def make_proof(**overrides: Any) -> dict[str, Any]:
    """A complete, prescore-clean T-20 Before/After Proof -- threshold
    met, gap partially recovered, a next-ranked verified cause named."""
    confounders = overrides.pop("confounders") if "confounders" in overrides else make_pilot_plan_confounder_checklist()
    after_values = overrides.pop("after_values") if "after_values" in overrides else PROOF_AFTER_VALUES_MET
    base = {
        "schema_version": 1, "artifact_id": "proof-001", "tool_id": "T-20",
        "created_at": TS, "updated_at": TS,
        "pilot_ref": "pilot-001",
        "metric_ref": "line-2 scrap rate",
        "operational_definition_ref": "scrap units / units produced, read from the QC log",
        "measurement_system_ref": "QC log export, same as baseline",
        "usl": 10.0, "lsl": 0.0,
        "before": {"dataset_id": "ds-before", "column": "scrap_pct", "dataset_sha256": "a" * 64, "values": list(PROOF_BEFORE_VALUES)},
        "after": {"dataset_id": "ds-after", "column": "scrap_pct", "dataset_sha256": "b" * 64, "values": list(after_values)},
        "declared_threshold": {"metric_ref": "line-2 scrap rate", "direction": "lower_is_better", "value": 4.5, "declared_at": TS},
        "confounders": confounders,
        "guardrails": [{"metric_ref": "line-2 throughput", "direction": "higher_is_better", "before_value": 100.0, "after_value": 99.0}],
        "charter_ref": "charter-001", "charter_baseline_value": 6.2, "charter_goal_value": 3.0, "charter_goal_direction": "lower_is_better",
        "next_cause_ref": {
            "cause_id": "c-2", "cause_text": "Injector pressure drifts low over a shift",
            "via_solution_id": "s-2", "via_solution_name": "Replace the injector", "rank": 2,
        },
    }
    base.update(overrides)
    return base


# T-22 Control Plan fixtures. FrozenLimitsRef carries the coffee-bar IMR
# baseline's OWN frozen i_ucl/i_lcl/i_cl -- the exact numbers
# compute_imr_chart(COFFEE_BAR_WAIT_SECONDS) produces (test_artifacts_
# control_chart.py's stable, no-signal fixture) -- so a check-in's pass/
# fail is tested against a REAL frozen band, not an invented one. 95.0 is
# inside [81.28, 107.64] (pass); 150.0 is clearly beyond ucl (fail).
COFFEE_BAR_FROZEN_LIMITS: dict[str, Any] = {
    "control_chart_artifact_id": "cc-imr-001", "chart_type": "imr",
    "center": 94.45833333333333, "ucl": 107.64057200123342, "lcl": 81.27609466543323,
    "p_bar": None, "frozen_at": TS,
}


def make_monitored_item(**overrides: Any) -> dict[str, Any]:
    base = {
        "item_id": "item-wait-time", "characteristic": "order-to-handoff wait time",
        "how_measured": "POS timestamp minus order timestamp, per the T-11 operational definition",
        "operational_definition_ref": "dcp-001", "where": "front counter register",
        "frequency": "weekly", "frequency_reason": "matches the check-in cadence and the volume of orders per week",
        "is_primary_ctq": True, "is_improve_change": True,
        "owner_name": "Maria Ortiz", "owner_accepted": True, "per_shift_owners": [],
    }
    base.update(overrides)
    return base


def make_check_in(check_in_id: str = "chk-1", value: float = 95.0, **overrides: Any) -> dict[str, Any]:
    base = {
        "check_in_id": check_in_id, "label": "week 1: is the fix holding?",
        "due_date": "2026-08-10", "completed_at": "2026-08-10",
        "entered": {"kind": "manual", "dataset_id": None, "values": [value], "subgroup": None},
        "note": "",
    }
    base.update(overrides)
    return base


def make_check_in_schedule(**overrides: Any) -> dict[str, Any]:
    base = {
        "cadence": {"unit": "weeks", "interval": 1}, "start_date": "2026-08-10",
        "control_chart_ref": "cc-imr-001", "frozen_limits": dict(COFFEE_BAR_FROZEN_LIMITS), "completed": [],
    }
    base.update(overrides)
    return base


def make_control_plan(**overrides: Any) -> dict[str, Any]:
    items = overrides.pop("monitored_items") if "monitored_items" in overrides else [make_monitored_item()]
    schedule = overrides.pop("check_in_schedule") if "check_in_schedule" in overrides else make_check_in_schedule()
    base = {
        "schema_version": 1, "artifact_id": "control-plan-001", "tool_id": "T-22",
        "created_at": TS, "updated_at": TS,
        "monitored_items": items,
        "ocap_entries": [
            {
                "ocap_id": "ocap-1", "monitored_item_id": items[0]["item_id"] if items else "item-wait-time",
                "trigger_signal": "a beyond-limits or 8-in-a-row signal fires on the T-21 wait-time chart",
                "action_steps": [
                    "Barista on shift checks the register timestamp clock against the wall clock",
                    "Shift lead pulls the last hour's orders and looks for a common cause",
                ],
                "escalation_trigger": "the signal repeats on the next shift",
                "escalation_contact": "Maria Ortiz (line-2 supervisor)", "acting_owner": "Shift lead",
            }
        ],
        "training_rows": [
            {
                "row_id": "train-1", "who": "Sam Lee", "sop_ref": "sop-001", "by_whom": "Maria Ortiz",
                "by_when": "2026-08-14", "verified_how": "observed demonstration on shift",
                "verified_at": "2026-08-13", "done": True,
            }
        ],
        "check_in_schedule": schedule,
        "as_of": "2026-08-10",
    }
    base.update(overrides)
    return base


# T-23 5S Audit fixtures.
def make_five_s_round(round_id: str = "round-1", date: str = "2026-08-01", scores: dict[str, int] | None = None, **overrides: Any) -> dict[str, Any]:
    scores = scores or {"sort": 4, "set_in_order": 3, "shine": 4, "standardize": 3, "sustain": 2}
    base = {
        "round_id": round_id, "date": date, "area": "front counter",
        "scores": [{"category": c, "score": scores[c], "note": f"{c} looked {scores[c]}/5"} for c in FIVE_S_CATEGORIES],
        "photos": [], "improvement_action": "Label the syrup shelf and retrain on the new layout",
        "improvement_action_owner": "Maria Ortiz",
    }
    base.update(overrides)
    return base


def make_five_s(**overrides: Any) -> dict[str, Any]:
    rounds = overrides.pop("rounds") if "rounds" in overrides else [make_five_s_round()]
    base = {
        "schema_version": 1, "artifact_id": "five-s-001", "tool_id": "T-23",
        "created_at": TS, "updated_at": TS, "rounds": rounds,
        "schedule": {"cadence_note": "monthly, first Monday", "next_round_due": "2026-09-01"},
    }
    base.update(overrides)
    return base


# T-24 Standard Work / SOP fixtures.
def make_standard_work_steps() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "sw-1", "order": 1,
            "action": "Check the fixture alignment against the taped guide before the first drink of the shift",
            "standard": "Guide marks line up within 1mm, confirmed visually before the first order",
            "changed_from_prior": True, "source_step_ref": "step-1", "note": "new step -- the old method had no pre-shift check",
        },
        {
            "step_id": "sw-2", "order": 2,
            "action": "Steam the milk to 150F using the thermometer clipped to the pitcher",
            "standard": "Thermometer reads 150F +/-5F before pouring", "changed_from_prior": False,
            "source_step_ref": "step-3", "note": "",
        },
    ]


def make_standard_work(**overrides: Any) -> dict[str, Any]:
    steps = overrides.pop("steps") if "steps" in overrides else make_standard_work_steps()
    base = {
        "schema_version": 1, "artifact_id": "sop-001", "tool_id": "T-24",
        "created_at": TS, "updated_at": TS,
        "title": "Coffee Bar Fixture Alignment SOP", "version": 1, "owner": "Maria Ortiz",
        "effective_date": "2026-08-14", "supersedes": None,
        "seeded_from_process_map_id": "process-map-001", "linked_control_plan_id": "control-plan-001",
        "steps": steps, "change_log": [],
    }
    base.update(overrides)
    return base


# T-25 A3 fixtures.
def make_a3_panels(narrative_overrides: dict[str, str] | None = None) -> list[dict[str, Any]]:
    narrative_overrides = narrative_overrides or {}
    return [
        {
            "panel": kind,
            "seeded_from": {"artifact_ref": "charter-001", "tool_id": "T-03", "fields": ["problem_statement"]} if kind == "background" else None,
            "narrative": narrative_overrides.get(kind, f"{kind} narrative text describing what happened, in the student's own words."),
            "seeded_at": TS if kind == "background" else None,
        }
        for kind in PANEL_ORDER
    ]


def make_a3_closure(**overrides: Any) -> dict[str, Any]:
    base = {
        "objectives_input": {"charter_baseline_value": 6.2, "charter_goal_value": 3.0, "achieved_value": 4.03, "direction": "lower_is_better"},
        "lessons": [
            {"lesson_id": "l-1", "text": "The fixture checklist worked once posted at eye level.", "went_wrong": False},
            {"lesson_id": "l-2", "text": "The first posting failed -- nobody looked at a checklist taped behind the register.", "went_wrong": True},
        ],
        "open_items": [{"item_id": "oi-1", "description": "Injector-pressure cause still unverified", "owner": "Sam Lee"}],
        "fmea_check": None,
        "project_status": "open",
    }
    base.update(overrides)
    return base


# T-10 Yield Calculator fixtures. Also this module's G-yield-01 golden
# fixture (same convention as make_copq_rows() doubling as its own hand-
# checkable reference): a 3-step line, each step's DPU/FPY hand-verified
# via dpu()/fpy_from_dpu() in test_artifacts_yield_calc.py's golden test --
# step 1: 100 in, 95 first-pass-correct -> 5 defects, DPU=0.05.
# step 2: 95 in, 90 first-pass-correct -> 5 defects, DPU=5/95.
# step 3: 90 in, 88 first-pass-correct -> 2 defects, DPU=2/90.
# RTY = e^-(0.05 + 5/95 + 2/90) ~= 0.882626.
# DPMO block: 1242 defects / 100000 units / 2 opportunities-per-unit ->
# DPMO = 1e6*1242/(100000*2) = 6210 -- the published Wikipedia/MoreSteam
# 4-sigma-with-shift table value already reference-tested in
# test_stats_sigma_level.py, so this golden is independently NIST/
# published-table-grounded, not just internally self-consistent.
def make_yield_calc_steps() -> list[dict[str, Any]]:
    return [
        {"name": "Mix", "units_in": 100, "first_pass_correct": 95},
        {"name": "Mold", "units_in": 95, "first_pass_correct": 90},
        {"name": "Inspect", "units_in": 90, "first_pass_correct": 88},
    ]


def make_dpmo_block(**overrides: Any) -> dict[str, Any]:
    base = {
        "defects": 1242,
        "units": 100000,
        "opportunities_per_unit": 2,
        "opportunity_justification": "Counting both the fill-weight opportunity and the seal-integrity opportunity separately, per the packaging QC spec.",
        "apply_sigma_shift": True,
    }
    base.update(overrides)
    return base


def make_yield_calc(**overrides: Any) -> dict[str, Any]:
    steps = overrides.pop("steps") if "steps" in overrides else make_yield_calc_steps()
    dpmo_block = overrides.pop("dpmo_block") if "dpmo_block" in overrides else make_dpmo_block()
    base = {
        "schema_version": 1,
        "artifact_id": "yieldcalc-001",
        "tool_id": "T-10",
        "created_at": TS,
        "updated_at": TS,
        "steps": steps,
        "steps_in_series": True,
        "dpmo_block": dpmo_block,
    }
    base.update(overrides)
    return base


def make_a3(**overrides: Any) -> dict[str, Any]:
    panels = overrides.pop("panels") if "panels" in overrides else make_a3_panels()
    realized_benefits = overrides.pop("realized_benefits") if "realized_benefits" in overrides else {
        "copq_rerun_artifact_id": "copq-002", "window": "6 weeks post-rollout",
        "before_amount": 40000.0, "after_amount": 15000.0, "fix_cost": 2000.0, "annualized_projection": 100000.0,
        # R-WRAP-02's Needs-work line ("a projection presented without its
        # basis") -- schema-hard as of M4 (artifacts/a3.py's
        # _projection_requires_a_basis); every annualized_projection in
        # this factory's default fixture needs one.
        "annualized_projection_basis": "6-week realized-to-date x (52/6 weeks) -- a straight-line annualization, no seasonality adjustment.",
    }
    closure = overrides.pop("closure") if "closure" in overrides else make_a3_closure()
    base = {
        "schema_version": 1, "artifact_id": "a3-001", "tool_id": "T-25",
        "created_at": TS, "updated_at": TS,
        "panels": panels, "realized_benefits": realized_benefits, "tollgates": [], "closure": closure,
    }
    base.update(overrides)
    return base
