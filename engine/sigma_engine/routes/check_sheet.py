"""POST .../check-sheet/{artifact_id}/to-dataset -- T-08's zero-re-entry
half: materialize a saved CheckSheetArtifact's entries as a stored project
dataset via the exact same DatasetStore every other import lands in
(datasets.py), so /stats/pareto (over the exported category column) needs
no re-typed intermediate copy (rubric R-MEA-06 #3). Generic CRUD (validate/
save/load/versions/prescore) for T-08 itself goes through the registry-
driven routes/artifacts.py and routes/prescore.py, same as every other
tool -- this router only adds the one T-08-specific action.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..artifacts.check_sheet import CheckSheetArtifact, check_sheet_export_csv_bytes
from ..datasets import DatasetMeta, DatasetStore
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project/{project_id}/check-sheet", tags=["check-sheet"])


class CheckSheetToDatasetRequest(BaseModel):
    # Caller-supplied, like DatasetSaveRequest.created_at -- never
    # datetime.now() on the server, so callers (and tests) control it.
    created_at: str


@router.post("/{artifact_id}/to-dataset", response_model=DatasetMeta)
def check_sheet_to_dataset(
    project_id: str, artifact_id: str, body: CheckSheetToDatasetRequest, store: ProjectStore = Depends(get_store)
) -> DatasetMeta:
    try:
        data = store.load_artifact(project_id, artifact_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact = CheckSheetArtifact.model_validate(data)
    try:
        csv_bytes = check_sheet_export_csv_bytes(artifact)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DatasetStore(store).save_dataset(
        project_id, f"{artifact_id}-check-sheet.csv", csv_bytes, None, body.created_at,
        source_artifact_id=artifact_id, source_tool_id="T-08",
    )
