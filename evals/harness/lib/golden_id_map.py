"""Requirement #3: golden-id reconciliation.

For every `G-xxx-nn` cited in docs/traceability-matrix.md, find its home:
`unit-test` (the literal id string appears in an engine/tests/test_*.py
file), `harness-step` (one of this run's three scenario drivers exercises
the tool surface that golden belongs to), or `uncovered` (neither --
reported honestly, with a stated reason, never hidden).

GOLDEN_ID_SOURCES is the one hand-curated table in this module: which
(scenario_id, tool_id) pair(s) exercise a given golden's surface, or --
when none does -- a one-line honest reason why not. It's deliberately
coarse-grained (scenario+tool, not exact step name): the live manifest
steps for that scenario/tool are looked up at report time, so renaming a
step in a driver never silently desyncs this table. `test_eval_harness.py`
asserts this table's key set stays exactly equal to the matrix's
extracted golden-id set -- a matrix edit that adds/renames a golden
without updating this table fails the suite, not silently drifts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .matrix import extract_golden_ids
from .recorder import ManifestStep


@dataclass(frozen=True)
class GoldenIdSource:
    # (scenario_id, tool_id) pairs whose harness steps exercise this golden's
    # surface. Empty means "no harness step covers this by design" --
    # `uncovered_reason` is then required.
    scenario_tool_pairs: tuple[tuple[str, str], ...] = ()
    uncovered_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.scenario_tool_pairs and not self.uncovered_reason:
            raise ValueError("a GoldenIdSource with no scenario/tool pairs must state an uncovered_reason")


# --- the curated table -------------------------------------------------
GOLDEN_ID_SOURCES: dict[str, GoldenIdSource] = {
    "G-picker-01": GoldenIdSource((("coffee-bar", "T-01"), ("s1-helpdesk", "T-01"), ("s2-library", "T-01"))),
    "G-picker-02": GoldenIdSource(uncovered_reason=(
        "PDCA quick-path route: all three scenarios' Picker artifacts route full-DMAIC "
        "(none is a small-problem/PDCA story)."
    )),
    "G-charter-01": GoldenIdSource((("coffee-bar", "T-03"), ("s1-helpdesk", "T-03"), ("s2-library", "T-03"))),
    "G-spaghetti-01": GoldenIdSource((("coffee-bar", "T-07"),)),
    "G-procmap-01": GoldenIdSource((("coffee-bar", "T-06"), ("s1-helpdesk", "T-06"), ("s2-library", "T-06"))),
    "G-fmea-01": GoldenIdSource((("coffee-bar", "T-16"), ("s1-helpdesk", "T-16"))),
    "G-sipoc-01": GoldenIdSource((("coffee-bar", "T-04"), ("s1-helpdesk", "T-04"), ("s2-library", "T-04"))),
    "G-ctq-01": GoldenIdSource((("coffee-bar", "T-05"), ("s1-helpdesk", "T-05"), ("s2-library", "T-05"))),
    "G-tollgate-01": GoldenIdSource((("coffee-bar", "T-25"), ("s1-helpdesk", "T-25"), ("s2-library", "T-25"))),
    "G-a3-01": GoldenIdSource((("coffee-bar", "T-25"), ("s1-helpdesk", "T-25"), ("s2-library", "T-25"))),
    "G-copq-01": GoldenIdSource((("coffee-bar", "T-02"), ("s1-helpdesk", "T-02"), ("s2-library", "T-02"))),
    "G-yield-01": GoldenIdSource((("s2-library", "T-10"),)),  # also unit-test covered -- see grep pass below
    "G-baseline-01": GoldenIdSource((("coffee-bar", "T-13"), ("s1-helpdesk", "T-13"))),
    "G-baseline-02": GoldenIdSource(uncovered_reason=(
        "Unstable-baseline (EXIT-04) path: all three scenarios' baselines are engine-verified stable by "
        "construction (their data-notes' acceptance checks require zero rule-1/rule-4 signals) -- none tells "
        "an instability story."
    )),
    "G-baseline-03": GoldenIdSource(uncovered_reason=(
        "Non-normal / percentile-capability (EXIT-05) path: both continuous scenarios (Coffee Bar, S-1) read "
        "normality no_concern by construction; S-2's baseline is the attribute p-chart path (T-21/T-10), which "
        "never touches T-13's normal-theory/percentile capability code at all."
    )),
    "G-dcp-01": GoldenIdSource((("coffee-bar", "T-11"), ("s1-helpdesk", "T-11"), ("s2-library", "T-11"))),
    "G-checksheet-01": GoldenIdSource((("coffee-bar", "T-08"), ("s1-helpdesk", "T-08"), ("s2-library", "T-08"))),
    "G-hist-01": GoldenIdSource((("coffee-bar", "T-13"), ("s1-helpdesk", "T-13")), ),
    "G-timestudy-01": GoldenIdSource((("coffee-bar", "T-09"),)),
    "G-run-01": GoldenIdSource((("coffee-bar", "T-13"), ("s1-helpdesk", "T-13"))),
    "G-pareto-01": GoldenIdSource((("coffee-bar", "T-14"), ("s1-helpdesk", "T-14"), ("s2-library", "T-14"))),
    "G-scatter-01": GoldenIdSource(uncovered_reason=(
        "Scatter is visual-only in v1 (matrix A-2 / EXIT-15 deferral: no fitted line, no r) -- there is no "
        "engine computation behind it at all, so no backend-driven harness step can ever exercise it; it is a "
        "genuine desktop-only rendering surface."
    )),
    "G-msa-01": GoldenIdSource((("coffee-bar", "T-12"), ("s1-helpdesk", "T-12"), ("s2-library", "T-12"))),
    "G-msa-02": GoldenIdSource((("s2-library", "T-12"),)),
    "G-hyp-01": GoldenIdSource((("coffee-bar", "T-17"), ("coffee-bar", "T-20"), ("s1-helpdesk", "T-17"), ("s1-helpdesk", "T-20"))),
    "G-hyp-02": GoldenIdSource(uncovered_reason=(
        "One-way ANOVA (3+ groups): none of the three scenarios' declared primary or screening comparisons is "
        "an ANOVA -- S-1/Coffee Bar run two-independent Welch t, S-2 runs chi-square + two-proportion z."
    )),
    "G-hyp-03": GoldenIdSource((("s2-library", "T-17"),)),
    "G-hyp-04": GoldenIdSource((("s2-library", "T-17"),)),
    "G-hyp-05": GoldenIdSource(uncovered_reason=(
        "Nonparametric (Mann-Whitney / Wilcoxon) fallback: every scenario's continuous data clears the "
        "normality/shape checks by construction, so the selector never switches off its parametric default."
    )),
    "G-hyp-06": GoldenIdSource(uncovered_reason=(
        "A T-17 selector EXIT case (matrix §4: 'an exit case appears in ... G-hyp-06'): none of the three "
        "scenarios' hypothesis calls is engineered to trip a T-17 exit -- S-2's named exit is T-12's EXIT-02, "
        "not a hypothesis-selector case."
    )),
    "G-hyp-07": GoldenIdSource(uncovered_reason=(
        "One-sample-vs-target routes (matrix correction A-1): every declared comparison across all three "
        "scenarios is two-sample (Welch t, chi-square, two-proportion z) -- none compares one sample against a "
        "fixed target value."
    )),
    "G-imr-01": GoldenIdSource((("coffee-bar", "T-21"), ("s1-helpdesk", "T-21"))),
    "G-pchart-01": GoldenIdSource((("s2-library", "T-21"),)),
    "G-pilot-01": GoldenIdSource((("coffee-bar", "T-19"), ("s1-helpdesk", "T-19"), ("s2-library", "T-19"))),
    "G-proof-01": GoldenIdSource((("coffee-bar", "T-20"), ("s1-helpdesk", "T-20"), ("s2-library", "T-20"))),
    "G-solmatrix-01": GoldenIdSource((("coffee-bar", "T-18"), ("s1-helpdesk", "T-18"), ("s2-library", "T-18"))),
    "G-stdwork-01": GoldenIdSource((("coffee-bar", "T-24"), ("s1-helpdesk", "T-24"), ("s2-library", "T-24"))),
    "G-werules-01": GoldenIdSource((("coffee-bar", "T-21"), ("s1-helpdesk", "T-21"), ("s2-library", "T-21"))),
    "G-ctrlplan-01": GoldenIdSource((("coffee-bar", "T-22"), ("s1-helpdesk", "T-22"), ("s2-library", "T-22"))),
    "G-5s-01": GoldenIdSource((("coffee-bar", "T-23"), ("s2-library", "T-23"))),
    "G-fishbone-01": GoldenIdSource((("coffee-bar", "T-15"), ("s1-helpdesk", "T-15"), ("s2-library", "T-15"))),
}


# This harness's OWN test file necessarily mentions golden-id strings as
# test fixtures/data (asserting things like "the known id set contains
# G-hyp-07") -- that is a test of the HARNESS's plumbing, never of the
# underlying engine stats/schema surface a golden id names, so it must
# never count as that id's unit-test home. Excluded by filename, not by
# some heuristic on content, so the exclusion is obvious from reading
# this module alone.
_SELF_TEST_FILE = "test_eval_harness.py"


def find_unit_test_homes(engine_tests_dir: Path, golden_id: str) -> list[str]:
    """Every engine/tests/test_*.py file (excluding this harness's own
    test_eval_harness.py -- see _SELF_TEST_FILE above) whose text
    literally contains `golden_id` -- grep, not a hardcoded table, so this
    half of the map can never go stale relative to the actual test suite."""
    homes: list[str] = []
    pattern = re.compile(re.escape(golden_id))
    for path in sorted(engine_tests_dir.glob("test_*.py")):
        if path.name == _SELF_TEST_FILE:
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            homes.append(f"engine/tests/{path.name}")
    return homes


def assert_sources_match_matrix(matrix_path: Path) -> None:
    matrix_ids = extract_golden_ids(matrix_path)
    table_ids = set(GOLDEN_ID_SOURCES)
    missing = matrix_ids - table_ids
    extra = table_ids - matrix_ids
    if missing or extra:
        raise AssertionError(
            "golden_id_map.GOLDEN_ID_SOURCES is out of sync with docs/traceability-matrix.md's cited golden ids.\n"
            f"  in the matrix but missing from the table: {sorted(missing)}\n"
            f"  in the table but not cited in the matrix: {sorted(extra)}"
        )


def build_golden_id_map(
    matrix_path: Path, engine_tests_dir: Path, manifests: dict[str, list[ManifestStep]],
) -> dict[str, Any]:
    """`manifests` is {scenario_id: [ManifestStep, ...]} from THIS run's
    recorders (freeze or replay -- either way, the current driver code's
    real step list, never a stale on-disk copy)."""
    assert_sources_match_matrix(matrix_path)
    golden_ids = sorted(extract_golden_ids(matrix_path))

    steps_by_scenario_tool: dict[tuple[str, str], list[str]] = {}
    for scenario_id, steps in manifests.items():
        for step in steps:
            for tool_id in step.tool_ids:
                steps_by_scenario_tool.setdefault((scenario_id, tool_id), []).append(step.name)

    ids: dict[str, Any] = {}
    covered, uncovered = [], []
    for gid in golden_ids:
        source = GOLDEN_ID_SOURCES[gid]
        unit_test_files = find_unit_test_homes(engine_tests_dir, gid)
        harness_steps = [
            {"scenario": scenario_id, "tool_id": tool_id, "steps": steps_by_scenario_tool.get((scenario_id, tool_id), [])}
            for scenario_id, tool_id in source.scenario_tool_pairs
        ]
        homes = []
        if unit_test_files:
            homes.append("unit-test")
        if harness_steps:
            homes.append("harness-step")

        entry: dict[str, Any] = {"homes": homes}
        if unit_test_files:
            entry["unit_test_files"] = unit_test_files
        if harness_steps:
            entry["harness_steps"] = harness_steps
        if source.uncovered_reason:
            entry["design_note"] = source.uncovered_reason
        if not homes:
            entry["uncovered_reason"] = source.uncovered_reason or "no unit test and no harness step cover this id"

        ids[gid] = entry
        (covered if homes else uncovered).append(gid)

    return {
        "generated_from": {"matrix": "docs/traceability-matrix.md", "engine_tests_dir": "engine/tests"},
        "golden_id_count": len(golden_ids),
        "covered_count": len(covered),
        "uncovered_count": len(uncovered),
        "uncovered": uncovered,
        "ids": ids,
    }
