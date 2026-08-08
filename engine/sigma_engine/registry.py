"""tool_id -> (artifact model, prescore function), so the FastAPI routes are
one generic CRUD set parameterized by tool_id rather than five near-copies.
"""

from __future__ import annotations

from typing import Callable

from .artifacts import (
    ArtifactBase,
    CharterArtifact,
    CheckSheetArtifact,
    CopqArtifact,
    DataCollectionPlanArtifact,
    HypothesisRunArtifact,
    MsaArtifact,
    PickerArtifact,
    ProcessMapArtifact,
    SipocArtifact,
    SpaghettiArtifact,
    TimeStudyArtifact,
    VocCtqArtifact,
)
from .prescore import (
    PrescoreResult,
    run_charter_prescore,
    run_check_sheet_prescore,
    run_copq_prescore,
    run_data_collection_plan_prescore,
    run_hypothesis_prescore,
    run_msa_prescore,
    run_picker_prescore,
    run_process_map_prescore,
    run_sipoc_prescore,
    run_spaghetti_prescore,
    run_time_study_prescore,
    run_voc_ctq_prescore,
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
    "T-11": DataCollectionPlanArtifact,
    "T-12": MsaArtifact,
    "T-17": HypothesisRunArtifact,
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
    "T-11": run_data_collection_plan_prescore,
    "T-12": run_msa_prescore,
    "T-17": run_hypothesis_prescore,
}
