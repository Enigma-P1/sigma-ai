"""Coffee Bar -- the third scenario in PLAN §9's trio. Unlike the two
held-out scenarios, its artifacts already exist on disk as engine-echo
JSONs (demo/coffee-bar/**/*.json): this driver re-posts them, in the
demo's own DMAIC dependency order, patching in freshly-uploaded dataset/
floorplan ids where a step genuinely depends on one (T-13's baseline
needs a real dataset to compute against; T-07/T-23's photo refs need a
real image upload). Every other field is the demo's own content,
untouched -- demo/ is a read-only input (never written by this driver).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..lib.client import EngineClient
from ..lib.recorder import Recorder
from . import common

PROJECT_ID = "eval-coffee-bar"
ROOT = common.DEMO_ROOT / "coffee-bar"

# evals/scenarios/README.md's collective-coverage table: every Tier-A tool
# except T-10 (a continuous-metric project has no per-step pass/fail
# counts for the yield calculator). Kept here as the driver's own record
# of what it exercises; lib/coverage.py's COFFEE_BAR_NA_TOOLS is the
# authoritative copy the coverage checker reads.
IN_SCOPE_TOOLS = tuple(f"T-{n:02d}" for n in range(1, 26) if n != 10)


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _pareto_categories(check_sheet: dict) -> list[str]:
    label_by_id = {c["category_id"]: c["label"] for c in check_sheet["categories"]}
    return [label_by_id[e["category_id"]] for e in check_sheet["entries"] if e.get("deleted") is None]


def run(recorder: Recorder, engine: EngineClient) -> None:
    common.reset_project(engine, PROJECT_ID, "Coffee Bar (golden replay)", "2026-07-02T14:00:00Z")

    # ---------------------------------------------------------------- Define
    picker = _load("define/picker.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-01", "T-01", picker)
    common.gate_check(recorder, PROJECT_ID, "intake_picker_present")
    common.gate_check(recorder, PROJECT_ID, "intake_picker_not_exit01")

    copq = _load("define/copq.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-02", "T-02", copq)

    # The flawed-then-corrected charter is the demo's own flagged-example
    # teaching moment (matrix's Tier-A "flawed-example teaching" attribute,
    # T-03 row) -- validate the flawed draft (captures the prescore's
    # solution-language flags) before saving the real, corrected charter.
    charter_flawed = _load("define/charter-flawed.json")
    common.validate_only(recorder, engine, "T-03", "T-03.flawed.validate", charter_flawed)
    common.prescore_only(recorder, "T-03", "T-03.flawed.prescore", charter_flawed)

    charter = _load("define/charter.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-03", "T-03", charter)
    recorder.call("T-03.load", "GET", f"/project/{PROJECT_ID}/artifacts/{charter['artifact_id']}", tool_ids=["T-03"])
    recorder.call("T-03.versions", "GET", f"/project/{PROJECT_ID}/artifacts/{charter['artifact_id']}/versions", tool_ids=["T-03"])

    sipoc = _load("define/sipoc.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-04", "T-04", sipoc)

    voc_ctq = _load("define/voc-ctq.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-05", "T-05", voc_ctq)

    common.gate_check(recorder, PROJECT_ID, "define_to_measure")

    # --------------------------------------------------------------- Measure
    wait_ds = common.upload_dataset(
        recorder, engine, PROJECT_ID, "dataset.wait_times", ROOT / "measure/wait-times.csv",
        "2026-07-31T17:00:00Z", tool_ids=["T-11"],
    )

    process_map = _load("measure/process-map.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-06", "T-06", process_map)

    floorplan_meta = common.upload_floorplan(
        recorder, engine, PROJECT_ID, "floorplan.station", ROOT / "measure/floorplan.png",
        "2026-07-21T14:15:00Z", tool_ids=["T-07"],
    )
    spaghetti = _load("measure/spaghetti.json")
    spaghetti["floor_plan"] = {
        "image_id": floorplan_meta["image_id"], "source_filename": floorplan_meta["source_filename"],
        "sha256": floorplan_meta["sha256"], "width_px": floorplan_meta["width_px"], "height_px": floorplan_meta["height_px"],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-07", "T-07", spaghetti)

    check_sheet = _load("measure/check-sheet.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-08", "T-08", check_sheet)
    recorder.call(
        "T-08.to_dataset", "POST", f"/project/{PROJECT_ID}/check-sheet/{check_sheet['artifact_id']}/to-dataset",
        {"created_at": "2026-07-31T17:10:00Z"}, tool_ids=["T-08"],
    )
    recorder.call(
        "T-14.pareto.delay_reasons", "POST", "/stats/pareto",
        {"categories": _pareto_categories(check_sheet)}, tool_ids=["T-14"],
    )

    time_study = _load("measure/time-study.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-09", "T-09", time_study)

    collection_plan = _load("measure/collection-plan.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-11", "T-11", collection_plan)
    recorder.call(
        "T-11.sample_size", "POST", "/stats/sample-size",
        {"calculator": "mean", "planning_sd": 1.1, "margin_of_error": 0.2, "confidence_level": 0.95},
        tool_ids=["T-11"],
    )

    msa = _load("measure/msa-study.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-12", "T-12", msa)

    common.gate_check(recorder, PROJECT_ID, "measure_capability_language_requires_msa_pass")

    recorder.call(
        "T-13.baseline", "POST", "/stats/baseline",
        {"project_id": PROJECT_ID, "dataset_id": wait_ds["dataset_id"], "column": "wait_minutes",
         "usl": 5.0, "lsl": None, "operational_definition_ok": True},
        tool_ids=["T-13"],
    )
    wait_values = common.read_csv_column(ROOT / "measure/wait-times.csv", "wait_minutes")
    recorder.call("T-14.descriptive.wait_times", "POST", "/stats/descriptive", {"data": wait_values}, tool_ids=["T-14"])

    common.gate_check(recorder, PROJECT_ID, "measure_to_analyze")

    # -------------------------------------------------------------- Analyze
    fishbone = _load("analyze/fishbone.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-15", "T-15", fishbone)

    fmea = _load("analyze/fmea.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-16", "T-16", fmea)

    hyp = _load("analyze/hypothesis-run.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-17", "T-17", hyp)

    common.gate_check(recorder, PROJECT_ID, "analyze_to_improve")

    # -------------------------------------------------------------- Improve
    solution_matrix = _load("improve/solution-matrix.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-18", "T-18", solution_matrix)

    pilot1 = _load("improve/pilot-plan-round1.json")
    # improve-run.md's own recorded refusal: a bundled 2-change draft trips
    # EXIT-10 by name before the real, 1-change plan is saved.
    bundled = dict(pilot1)
    bundled["changes"] = [*pilot1["changes"], {"change_id": "chg-bogus", "text": "An extra bundled change, proving EXIT-10 fires."}]
    common.validate_only(recorder, engine, "T-19", "T-19.round1.exit10_probe", bundled, expect_status=(422,))
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-19", "T-19.round1", pilot1)

    proof1 = _load("improve/proof-round1.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-20", "T-20.round1", proof1)

    pilot2 = _load("improve/pilot-plan-round2.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-19", "T-19.round2", pilot2)

    proof2 = _load("improve/proof-round2.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-20", "T-20.round2", proof2)

    common.gate_check(recorder, PROJECT_ID, "improve_to_control")

    # -------------------------------------------------------------- Control
    control_chart = common.prepare_control_chart(_load("control/control-chart.json"), action_at="2026-09-22T09:00:00Z")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-21", "T-21", control_chart, strip=False)

    control_plan = common.prepare_control_plan(_load("control/control-plan.json"))
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-22", "T-22", control_plan, strip=False)

    five_s = _load("control/five-s.json")
    for i, round_ in enumerate(five_s["rounds"], start=1):
        png = ROOT / f"control/five-s-round{i}.png"
        meta = common.upload_floorplan(
            recorder, engine, PROJECT_ID, f"floorplan.five_s_round{i}", png,
            f"{round_['date']}T09:00:00Z", tool_ids=["T-23"],
        )
        round_["photos"] = [{
            "image_id": meta["image_id"], "source_filename": meta["source_filename"],
            "sha256": meta["sha256"], "width_px": meta["width_px"], "height_px": meta["height_px"],
        }]
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-23", "T-23", five_s)

    standard_work = _load("control/standard-work.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-24", "T-24", standard_work)

    common.gate_check(recorder, PROJECT_ID, "control_to_wrap")

    # ----------------------------------------------------------------- Wrap
    copq_wrap = _load("control/copq-wrap.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-02", "T-02.wrap", copq_wrap)

    a3 = _load("control/a3.json")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-25", "T-25", a3)
    recorder.call("T-25.load", "GET", f"/project/{PROJECT_ID}/artifacts/{a3['artifact_id']}", tool_ids=["T-25"])

    recorder.call("project.info", "GET", f"/project/{PROJECT_ID}/info", tool_ids=[])
