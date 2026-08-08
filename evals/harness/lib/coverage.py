"""Requirement #2: the three scenarios' declared in-scope sets must
collectively equal the matrix's Tier-A 25, checked in code, failing loudly
on drift -- plus the coverage-by-scenario table written to
evals/goldens/coverage.json.

The Coffee Bar demo has no machine-readable spec (evals/scenarios/*/spec.md's
YAML frontmatter is a held-out-scenario-only convention) -- its declared
scope is evals/scenarios/README.md's own collective-coverage table ("the
Coffee Bar threads 24 of 25 -- everything except T-10"), so that one list
is hardcoded here with the doc line cited, the single place it could ever
drift from that table.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .matrix import ToolRow, parse_tool_inventory
from .spec_frontmatter import ScenarioSpec, parse_scenario_spec

# evals/scenarios/README.md, "Collective coverage" table: Coffee Bar covers
# every Tier-A tool except T-10 (a continuous-metric demo has no per-step
# pass/fail counts for the yield calculator to tally).
COFFEE_BAR_SCENARIO_ID = "coffee-bar"
COFFEE_BAR_NA_TOOLS = {"T-10": "Continuous-metric demo: no per-step pass/fail counts or opportunity structure for T-10 to tally (evals/scenarios/README.md coverage table)."}


class CoverageDriftError(AssertionError):
    pass


def coffee_bar_in_scope(all_tier_a_ids: set[str]) -> tuple[str, ...]:
    return tuple(sorted(all_tier_a_ids - set(COFFEE_BAR_NA_TOOLS)))


def load_specs(s1_path: Path, s2_path: Path) -> tuple[ScenarioSpec, ScenarioSpec]:
    return parse_scenario_spec(s1_path), parse_scenario_spec(s2_path)


def check_collective_coverage(
    matrix_path: Path, s1_spec_path: Path, s2_spec_path: Path,
) -> dict[str, Any]:
    """Requirement #2's hard assertion: parse the matrix's Tier-A 25, parse
    both held-out specs' declared in_scope_tools, union with the Coffee Bar
    hardcoded list, and require the union to equal the Tier-A set exactly
    (no missing tool, no stray id nobody in the matrix recognizes as
    Tier-A). Raises CoverageDriftError with the specific drift on failure;
    returns the raw pieces so callers (coverage.json writer, tests) don't
    have to re-parse."""
    rows = parse_tool_inventory(matrix_path)
    tier_a = {r.tool_id for r in rows if r.tier == "A"}
    if len(tier_a) != 25:
        raise CoverageDriftError(
            f"matrix §1 Tier-A count drifted: found {len(tier_a)} tool(s), expected 25 "
            f"(PLAN §9 / matrix §6: 'one authoritative count, no drift'). Got: {sorted(tier_a)}"
        )

    s1, s2 = load_specs(s1_spec_path, s2_spec_path)
    coffee = coffee_bar_in_scope(tier_a)

    union = set(s1.in_scope_tools) | set(s2.in_scope_tools) | set(coffee)
    missing = tier_a - union
    extra = union - tier_a
    if missing or extra:
        raise CoverageDriftError(
            "collective scenario coverage no longer equals the matrix's Tier-A 25.\n"
            f"  missing from the scenario set (in the matrix, not in any scenario's scope): {sorted(missing)}\n"
            f"  extra in the scenario set (not a matrix Tier-A id -- typo, or the matrix moved a tool's tier): {sorted(extra)}\n"
            "This is a hard failure by design (build brief requirement #2: 'fail loudly on drift')."
        )

    return {"rows": rows, "tier_a": tier_a, "s1": s1, "s2": s2, "coffee_bar_in_scope": coffee}


def build_coverage_table(matrix_path: Path, s1_spec_path: Path, s2_spec_path: Path) -> dict[str, Any]:
    """The coverage-by-scenario table (requirement #2's second half),
    independent of whether the hard assertion above passes -- called only
    after check_collective_coverage succeeds, so by construction every
    tool below is 'in_scope' in at least one scenario."""
    parts = check_collective_coverage(matrix_path, s1_spec_path, s2_spec_path)
    rows: list[ToolRow] = parts["rows"]
    tier_a_rows = sorted((r for r in rows if r.tier == "A"), key=lambda r: r.tool_id)
    s1: ScenarioSpec = parts["s1"]
    s2: ScenarioSpec = parts["s2"]
    coffee_scope = set(parts["coffee_bar_in_scope"])

    scenario_scopes = {
        COFFEE_BAR_SCENARIO_ID: (coffee_scope, COFFEE_BAR_NA_TOOLS),
        "s1-helpdesk": (set(s1.in_scope_tools), s1.na_tools),
        "s2-library": (set(s2.in_scope_tools), s2.na_tools),
    }

    by_tool: dict[str, Any] = {}
    for row in tier_a_rows:
        entry: dict[str, Any] = {"name": row.name, "phase": row.phase}
        covered_by = 0
        for scenario_id, (scope, na) in scenario_scopes.items():
            if row.tool_id in scope:
                entry[scenario_id] = "in_scope"
                covered_by += 1
            elif row.tool_id in na:
                entry[scenario_id] = "na"
                entry[f"{scenario_id}_na_reason"] = na[row.tool_id]
            else:
                entry[scenario_id] = "MISSING"  # unreachable once check_collective_coverage passed
        entry["covered_by_count"] = covered_by
        by_tool[row.tool_id] = entry

    uncovered = [tid for tid, e in by_tool.items() if e["covered_by_count"] == 0]

    return {
        "tier_a_tool_count": len(tier_a_rows),
        "scenarios": [COFFEE_BAR_SCENARIO_ID, "s1-helpdesk", "s2-library"],
        "by_tool": by_tool,
        "uncovered_tools": uncovered,
        "generated_from": {
            "matrix": "docs/traceability-matrix.md §1",
            "s1_spec": "evals/scenarios/s1-helpdesk/spec.md (frontmatter)",
            "s2_spec": "evals/scenarios/s2-library/spec.md (frontmatter)",
            "coffee_bar": "evals/scenarios/README.md collective-coverage table (no machine-readable spec exists for the shipped demo)",
        },
    }
