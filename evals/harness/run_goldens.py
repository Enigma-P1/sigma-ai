#!/usr/bin/env python3
"""M6 golden-scenario eval harness driver (PLAN §9).

Usage (via engine/.venv/bin/python -- this package imports nothing from
sigma_engine, only httpx, but the pinned interpreter is the one venv
guaranteed to have httpx installed):

    engine/.venv/bin/python evals/harness/run_goldens.py            # replay (default)
    engine/.venv/bin/python evals/harness/run_goldens.py --freeze   # (re-)freeze goldens
    engine/.venv/bin/python evals/harness/run_goldens.py --scenario s1-helpdesk

Replay mode drives every scenario, diffs every step's response against
its frozen golden, and exits 1 with a readable summary if anything
differs (a missing golden, a mismatched value, or an orphaned golden file
a removed/renamed step no longer produces). Freeze mode runs the same
drivers and writes/overwrites the goldens instead of diffing.

Also runs, every invocation, freeze or replay: the collective in-scope-
tools coverage check (build brief requirement #2) and the golden-id
reconciliation report (requirement #3) -- both are re-derived from the
CURRENT run's manifests, never a stale cached copy.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # repo root, for `evals.harness.*` imports

from evals.harness.lib.client import EngineClient
from evals.harness.lib.coverage import build_coverage_table, check_collective_coverage
from evals.harness.lib.golden_id_map import build_golden_id_map
from evals.harness.lib.matrix import assert_tier_a_count
from evals.harness.lib.recorder import Recorder, ScenarioReport
from evals.harness.scenarios import coffee_bar, s1_helpdesk, s2_library

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MATRIX_PATH = REPO_ROOT / "docs" / "traceability-matrix.md"
S1_SPEC = REPO_ROOT / "evals" / "scenarios" / "s1-helpdesk" / "spec.md"
S2_SPEC = REPO_ROOT / "evals" / "scenarios" / "s2-library" / "spec.md"
GOLDENS_ROOT = REPO_ROOT / "evals" / "goldens"
ENGINE_TESTS_DIR = REPO_ROOT / "engine" / "tests"

SCENARIOS = {
    "coffee-bar": coffee_bar,
    "s1-helpdesk": s1_helpdesk,
    "s2-library": s2_library,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--freeze", action="store_true", help="write goldens instead of diffing against them")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), action="append",
                     help="restrict to one scenario (repeatable); default: all three")
    ap.add_argument("--engine-url", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    mode = "freeze" if args.freeze else "replay"
    scenario_ids = args.scenario or list(SCENARIOS)

    print(f"[run_goldens] mode={mode} scenarios={scenario_ids} engine={args.engine_url}")

    # Fail loudly, first, if the matrix's own Tier-A count has drifted --
    # every downstream check assumes 25 (build brief requirement #2).
    assert_tier_a_count(MATRIX_PATH, 25)

    with EngineClient(base_url=args.engine_url) as engine:
        engine.wait_healthy()

        reports: list[ScenarioReport] = []
        recorders: dict[str, Recorder] = {}
        hard_errors: list[str] = []

        for sid in scenario_ids:
            module = SCENARIOS[sid]
            recorder = Recorder(sid, engine, GOLDENS_ROOT, mode)
            print(f"[run_goldens] --- {sid} ---")
            try:
                module.run(recorder, engine)
            except Exception as exc:  # noqa: BLE001 - report, don't let one scenario crash the whole run
                hard_errors.append(f"{sid}: {exc}\n{traceback.format_exc()}")
                print(f"[run_goldens] {sid} RAISED before completing: {exc}", file=sys.stderr)
            report = recorder.finalize()
            reports.append(report)
            recorders[sid] = recorder
            print(f"[run_goldens] {sid}: {report.steps_run} step(s) run, {len(report.diffs)} diff(s)")

        # --- requirement #2: collective coverage (always checked, both modes)
        try:
            check_collective_coverage(MATRIX_PATH, S1_SPEC, S2_SPEC)
            print("[run_goldens] collective in-scope-tools coverage == matrix Tier-A 25: OK")
        except AssertionError as exc:
            hard_errors.append(str(exc))
            print(f"[run_goldens] COVERAGE DRIFT: {exc}", file=sys.stderr)

        # coverage.json and golden-id-map.json are inherently CROSS-scenario
        # reports (a tool/golden's coverage can come from any of the three
        # scenarios) -- only written/diffed on a full run across all three,
        # never on a --scenario-restricted one, so restricting scope for
        # local debugging can never manufacture a spurious "drift" against
        # tools/goldens that a skipped scenario alone accounts for.
        if set(scenario_ids) == set(SCENARIOS):
            coverage_table = build_coverage_table(MATRIX_PATH, S1_SPEC, S2_SPEC)
            _write_report_json(GOLDENS_ROOT, "coverage.json", coverage_table, mode)

            manifests = {sid: r.manifest_steps for sid, r in recorders.items()}
            gid_map = build_golden_id_map(MATRIX_PATH, ENGINE_TESTS_DIR, manifests)
            _write_report_json(GOLDENS_ROOT, "golden-id-map.json", gid_map, mode)
            print(
                f"[run_goldens] golden ids: {gid_map['covered_count']}/{gid_map['golden_id_count']} covered, "
                f"uncovered: {gid_map['uncovered']}"
            )
        else:
            print("[run_goldens] --scenario restricts this run -- skipping the cross-scenario coverage.json / "
                  "golden-id-map.json report (run all three scenarios for those).")

        return _summarize(mode, reports, hard_errors)


def _write_report_json(goldens_root: Path, filename: str, obj: dict, mode: str) -> None:
    """coverage.json / golden-id-map.json: written fresh every run
    (freeze AND replay -- both are cheap, pure functions of the matrix +
    specs + this run's manifests) so they're always current; ALSO
    diffed in replay mode via a throwaway Recorder-less path so drift
    there is caught the same way a step's own golden drift is."""
    from evals.harness.lib.normalize import canonical_json_bytes, canonicalize_for_golden
    import json

    path = goldens_root / filename
    canon = canonicalize_for_golden(obj)
    if mode == "freeze":
        goldens_root.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes(canon))
        return
    if not path.exists():
        print(f"[run_goldens] WARNING: {filename} has no frozen golden yet (run --freeze first)", file=sys.stderr)
        return
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    if on_disk != canon:
        print(f"[run_goldens] DRIFT in {filename}: live output no longer matches the frozen file.", file=sys.stderr)
        raise _ReportDrift(filename)


class _ReportDrift(RuntimeError):
    pass


def _summarize(mode: str, reports: list[ScenarioReport], hard_errors: list[str]) -> int:
    print()
    print("=" * 72)
    total_steps = sum(r.steps_run for r in reports)
    total_diffs = sum(len(r.diffs) for r in reports)
    print(f"[run_goldens] SUMMARY ({mode}): {len(reports)} scenario(s), {total_steps} step(s) total")
    for r in reports:
        print(f"  {r.scenario_id}: {r.steps_run} step(s), {len(r.diffs)} diff(s)")

    if mode == "freeze":
        if hard_errors:
            print(f"\n[run_goldens] {len(hard_errors)} scenario(s) raised during freeze -- goldens are INCOMPLETE:")
            for e in hard_errors:
                print(e)
            return 1
        print("[run_goldens] freeze complete.")
        return 0

    # replay
    if hard_errors:
        print(f"\n[run_goldens] {len(hard_errors)} scenario(s) raised during replay:")
        for e in hard_errors:
            print(e)
    if total_diffs:
        print(f"\n[run_goldens] {total_diffs} diff(s) found:\n")
        for r in reports:
            for d in r.diffs:
                print(f"--- {r.scenario_id} / {d.step} [{d.kind}] ---")
                print(d.detail)
                print()
    if hard_errors or total_diffs:
        print("[run_goldens] REPLAY FAILED.")
        return 1
    print("[run_goldens] replay clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
