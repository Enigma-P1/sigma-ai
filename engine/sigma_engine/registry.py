"""tool_id -> (artifact model, prescore function), so the FastAPI routes are
one generic CRUD set parameterized by tool_id rather than five near-copies.

Also home to `collect_standing_hard_flags` (M6 fidelity-panel fix 7): the
server-side sweep of a project's saved artifacts for standing prescore
hard_flags, run through these same two registries -- it lives here because
this module is the one place that already owns both halves of that call.
"""

from __future__ import annotations

from typing import Callable

from pydantic import ValidationError

from .project_store import ProjectStore
from .artifacts import (
    A3Artifact,
    ArtifactBase,
    StandingHardFlag,
    CharterArtifact,
    CheckSheetArtifact,
    ControlChartArtifact,
    ControlPlanArtifact,
    CopqArtifact,
    DataCollectionPlanArtifact,
    FishboneArtifact,
    FiveSArtifact,
    FmeaArtifact,
    GageRRArtifact,
    HypothesisRunArtifact,
    MsaArtifact,
    PickerArtifact,
    PilotPlanArtifact,
    ProcessMapArtifact,
    ProofArtifact,
    SipocArtifact,
    SolutionMatrixArtifact,
    SpaghettiArtifact,
    StandardWorkArtifact,
    TimeStudyArtifact,
    VocCtqArtifact,
    YieldCalcArtifact,
)
from .prescore import (
    PrescoreResult,
    run_a3_prescore,
    run_charter_prescore,
    run_check_sheet_prescore,
    run_control_chart_prescore,
    run_control_plan_prescore,
    run_copq_prescore,
    run_data_collection_plan_prescore,
    run_fishbone_prescore,
    run_five_s_prescore,
    run_fmea_prescore,
    run_gage_rr_prescore,
    run_hypothesis_prescore,
    run_msa_prescore,
    run_picker_prescore,
    run_pilot_plan_prescore,
    run_process_map_prescore,
    run_proof_prescore,
    run_sipoc_prescore,
    run_solution_matrix_prescore,
    run_spaghetti_prescore,
    run_standard_work_prescore,
    run_time_study_prescore,
    run_voc_ctq_prescore,
    run_yield_calc_prescore,
)

ARTIFACT_REGISTRY: dict[str, type[ArtifactBase]] = {
    "T-01": PickerArtifact,
    "T-02": CopqArtifact,
    "T-03": CharterArtifact,
    "T-04": SipocArtifact,
    "T-05": VocCtqArtifact,
    "T-06": ProcessMapArtifact,
    "T-07": SpaghettiArtifact,
    "T-08": CheckSheetArtifact,
    "T-09": TimeStudyArtifact,
    "T-10": YieldCalcArtifact,
    "T-11": DataCollectionPlanArtifact,
    "T-12": MsaArtifact,
    "T-15": FishboneArtifact,
    "T-16": FmeaArtifact,
    "T-17": HypothesisRunArtifact,
    "T-18": SolutionMatrixArtifact,
    "T-19": PilotPlanArtifact,
    "T-20": ProofArtifact,
    "T-21": ControlChartArtifact,
    "T-22": ControlPlanArtifact,
    "T-23": FiveSArtifact,
    "T-24": StandardWorkArtifact,
    "T-25": A3Artifact,
    "T-35": GageRRArtifact,
}

PRESCORE_REGISTRY: dict[str, Callable[[ArtifactBase], list[PrescoreResult]]] = {
    "T-01": run_picker_prescore,
    "T-02": run_copq_prescore,
    "T-03": run_charter_prescore,
    "T-04": run_sipoc_prescore,
    "T-05": run_voc_ctq_prescore,
    "T-06": run_process_map_prescore,
    "T-07": run_spaghetti_prescore,
    "T-08": run_check_sheet_prescore,
    "T-09": run_time_study_prescore,
    "T-10": run_yield_calc_prescore,
    "T-11": run_data_collection_plan_prescore,
    "T-12": run_msa_prescore,
    "T-15": run_fishbone_prescore,
    "T-16": run_fmea_prescore,
    "T-17": run_hypothesis_prescore,
    "T-18": run_solution_matrix_prescore,
    "T-19": run_pilot_plan_prescore,
    "T-20": run_proof_prescore,
    "T-21": run_control_chart_prescore,
    "T-22": run_control_plan_prescore,
    "T-23": run_five_s_prescore,
    "T-24": run_standard_work_prescore,
    "T-25": run_a3_prescore,
    "T-35": run_gage_rr_prescore,
}


def collect_standing_hard_flags(
    store: ProjectStore, project_id: str, *, exclude_artifact_id: str | None = None,
) -> list[StandingHardFlag]:
    """Every prescore hard_flag currently standing on this project's saved
    artifacts (latest version each), for the A3 close check (M6 fidelity
    panel: closure must not treat an unresolved deterministic finding as a
    clean pass). Runs each stored artifact back through its own model and
    prescore via the two registries above -- the exact code path
    /prescore/{tool_id} serves -- so the sweep can never drift from what
    the routes themselves would report. `exclude_artifact_id` skips the
    artifact being saved right now (the A3 itself): its PRIOR stored
    version's flags describe a state this very save may be fixing, and its
    own current-state checks run on their own prescore call.

    Deterministic: artifacts visited in sorted-artifact_id order. A stored
    artifact that no longer validates against the current schema is itself
    reported as a standing flag (check_id `artifact_fails_validation`) --
    a store entry the engine can no longer even read is not a clean pass
    either. Raises FileNotFoundError for an unknown project, same contract
    as every other store-backed lookup."""
    meta = store.load_project(project_id)  # FileNotFoundError propagates
    flags: list[StandingHardFlag] = []
    for artifact_id in sorted(meta.artifact_index):
        if artifact_id == exclude_artifact_id:
            continue
        entry = meta.artifact_index[artifact_id]
        model = ARTIFACT_REGISTRY.get(entry.tool_id)
        prescore_fn = PRESCORE_REGISTRY.get(entry.tool_id)
        if model is None or prescore_fn is None:
            continue  # nothing outside the registries writes artifacts; defensive only
        data = store.load_artifact(project_id, artifact_id, entry.latest_version)
        try:
            artifact = model.model_validate(data)
        except ValidationError as exc:
            first = exc.errors()[0] if exc.errors() else {}
            flags.append(StandingHardFlag(
                artifact_id=artifact_id, tool_id=entry.tool_id, check_id="artifact_fails_validation",
                detail=f"stored v{entry.latest_version} no longer validates against its own schema: {first.get('msg', 'validation error')}",
            ))
            continue
        for result in prescore_fn(artifact):
            if result.status == "hard_flag":
                flags.append(StandingHardFlag(
                    artifact_id=artifact_id, tool_id=entry.tool_id, check_id=result.check_id, detail=result.detail,
                ))
    return flags


def refresh_computed_fields(tool_id: str, data: dict) -> dict:
    """Re-derive an artifact's server-computed fields on READ.

    WHY: project_store.load_artifact returns the JSON exactly as it was
    written, and every computed field (CopqArtifact.total,
    ProcessMapArtifact.constraint_step, the value-add ratio, ...) is produced
    by a model_validator that only runs on SAVE. So an artifact saved before
    a computed field existed comes back without it forever, and the screen
    that reads it shows its empty state on a project that is in fact
    complete. That is the same shape as the blank-forms bug in the worked
    example: two honest components disagreeing, with no error anywhere.

    Running the artifact back through its model on read fixes it for every
    tool at once, and keeps derived values honest in a second way -- a
    hand-edited project.json cannot leave a stale computed number in place,
    because it is recomputed from the inputs before anyone sees it.

    FALLS BACK TO THE RAW DATA on any validation failure. An artifact written
    by an older schema that no longer validates must still be readable: a
    user losing access to their own work is far worse than a missing derived
    field, and refusing to load would be exactly the "you can't get your work
    out" failure this codebase keeps having to fix.
    """
    model = ARTIFACT_REGISTRY.get(tool_id)
    if model is None:
        return data
    try:
        return model.model_validate(data).model_dump(mode="json")
    except ValidationError:
        return data
