"""Valid-by-default dict factories for every Define/Intake artifact. Tests
mutate a specific field off these bases to exercise one accept/reject path
at a time, instead of re-typing a full artifact per test. Not a test module
itself (no test_ prefix) -- pytest won't collect it.
"""

from __future__ import annotations

from typing import Any

from sigma_engine.artifacts.copq import CopqRow, compute_copq_total

TS = "2026-08-07T00:00:00"


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
