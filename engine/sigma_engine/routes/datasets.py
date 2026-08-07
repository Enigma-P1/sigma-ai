"""POST .../datasets/preview, POST .../datasets, GET .../datasets,
GET .../datasets/{dataset_id} -- T-11's import half (PLAN §4.1 Data
Collection Plan row): parse+infer+scan without persisting (preview,
replayable as the user tries different column-type overrides), then
persist for real (save). See datasets.py's module docstring for why this
is JSON+base64 rather than multipart.
"""

from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..datasets import ColumnType, DatasetMeta, DatasetPreview, DatasetStore, build_preview
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project/{project_id}/datasets", tags=["datasets"])


class DatasetImportRequest(BaseModel):
    source_filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    # A caller's confirmed column-type overrides; any column not present
    # here keeps its inferred type (datasets.py's build_columns).
    column_types: dict[str, ColumnType] | None = None


class DatasetSaveRequest(DatasetImportRequest):
    # Caller-supplied, like ProjectCreateRequest.created_at (routes/
    # projects.py) -- never datetime.now() on the server, so callers
    # (and tests) control the timestamp.
    created_at: str


def _decode(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"content_base64 is not valid base64: {exc}") from exc


@router.post("/preview", response_model=DatasetPreview)
def preview_dataset(project_id: str, body: DatasetImportRequest) -> DatasetPreview:
    content = _decode(body.content_base64)
    try:
        return build_preview(content, body.source_filename, body.column_types)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("", response_model=DatasetMeta)
def save_dataset(project_id: str, body: DatasetSaveRequest, store: ProjectStore = Depends(get_store)) -> DatasetMeta:
    content = _decode(body.content_base64)
    try:
        return DatasetStore(store).save_dataset(project_id, body.source_filename, content, body.column_types, body.created_at)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[DatasetMeta])
def list_datasets(project_id: str, store: ProjectStore = Depends(get_store)) -> list[DatasetMeta]:
    return DatasetStore(store).list_datasets(project_id)


class DatasetDetailResponse(BaseModel):
    meta: DatasetMeta
    rows: list[dict[str, str]]


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
def get_dataset(project_id: str, dataset_id: str, store: ProjectStore = Depends(get_store)) -> DatasetDetailResponse:
    dataset_store = DatasetStore(store)
    try:
        meta = dataset_store.load_meta(project_id, dataset_id)
        rows = dataset_store.load_rows(project_id, dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DatasetDetailResponse(meta=meta, rows=rows)
