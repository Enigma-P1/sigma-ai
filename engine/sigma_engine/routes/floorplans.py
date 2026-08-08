"""POST .../floorplans, GET .../floorplans/{image_id} -- T-07's floor-plan
image upload (PLAN §4.1 Spaghetti Diagram row). Same base64-in-JSON shape
as routes/datasets.py, for the same reason (no python-multipart on the
pinned-dependency list). No separate preview step: unlike a CSV/XLSX
import, there's no column-type confirmation equivalent for an image, so
upload IS save.
"""

from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..floorplan_images import FloorPlanImageMeta, FloorPlanImageStore
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/project/{project_id}/floorplans", tags=["floorplans"])


class FloorPlanUploadRequest(BaseModel):
    source_filename: str = Field(min_length=1)
    content_base64: str = Field(min_length=1)
    # Caller-supplied, like DatasetSaveRequest.created_at -- never
    # datetime.now() on the server, so callers (and tests) control it.
    created_at: str


def _decode(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"content_base64 is not valid base64: {exc}") from exc


@router.post("", response_model=FloorPlanImageMeta)
def upload_floorplan(project_id: str, body: FloorPlanUploadRequest, store: ProjectStore = Depends(get_store)) -> FloorPlanImageMeta:
    content = _decode(body.content_base64)
    try:
        return FloorPlanImageStore(store).save_image(project_id, body.source_filename, content, body.created_at)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class FloorPlanDetailResponse(BaseModel):
    meta: FloorPlanImageMeta
    content_base64: str


@router.get("/{image_id}", response_model=FloorPlanDetailResponse)
def get_floorplan(project_id: str, image_id: str, store: ProjectStore = Depends(get_store)) -> FloorPlanDetailResponse:
    image_store = FloorPlanImageStore(store)
    try:
        meta = image_store.load_meta(project_id, image_id)
        content = image_store.load_bytes(project_id, image_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FloorPlanDetailResponse(meta=meta, content_base64=base64.b64encode(content).decode("ascii"))
