"""Valid-by-default dict factories for every Define/Intake artifact. Tests
mutate a specific field off these bases to exercise one accept/reject path
at a time, instead of re-typing a full artifact per test. Not a test module
itself (no test_ prefix) -- pytest won't collect it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sigma_engine.artifacts.copq import CopqRow, compute_copq_total

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
