"""POST .../time-study/{artifact_id}/to-dataset -- T-09's per-element
zero-re-entry half: materialize one work element's recorded cycle times as
a stored project dataset (same DatasetStore as T-08/T-11), so /stats/
baseline can run against it via dataset_id+column with no re-typed copy.
Generic CRUD for T-09 itself goes through routes/artifacts.py + routes/
prescore.py like every other tool -- this router only adds the one
T-09-specific, per-element action.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..artifacts.time_study import TimeStudyArtifact, element_cycle_export_csv_bytes
from ..datasets import DatasetMeta, DatasetStore
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project/{project_id}/time-study", tags=["time-study"])


class TimeStudyToDatasetRequest(BaseModel):
    element_id: str = Field(min_length=1)
    created_at: str


def _safe_slug(name: str, fallback: str) -> str:
    slug = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    return slug or fallback


@router.post("/{artifact_id}/to-dataset", response_model=DatasetMeta)
def time_study_to_dataset(
    project_id: str, artifact_id: str, body: TimeStudyToDatasetRequest, store: ProjectStore = Depends(get_store)
) -> DatasetMeta:
    try:
        data = store.load_artifact(project_id, artifact_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    artifact = TimeStudyArtifact.model_validate(data)
    try:
        csv_bytes = element_cycle_export_csv_bytes(artifact, body.element_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    element = next((e for e in artifact.elements if e.element_id == body.element_id), None)
    slug = _safe_slug(element.name, body.element_id) if element else body.element_id
    return DatasetStore(store).save_dataset(
        project_id, f"{artifact_id}-{slug}-cycle-times.csv", csv_bytes, None, body.created_at,
        source_artifact_id=artifact_id, source_tool_id="T-09",
    )
