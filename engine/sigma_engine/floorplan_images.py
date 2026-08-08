"""Floor-plan image storage (T-07's floor_plan field, PLAN §4.1 Spaghetti
Diagram row): the same shape as datasets.py's DatasetStore -- image bytes
land in the project folder (floorplans/<image_id>/original.<ext> +
meta.json), a SHA-256 over the exact bytes saved is the provenance anchor,
and SpaghettiArtifact.floor_plan carries only the metadata (id/sha256/
dimensions), never the bytes themselves (same split as DatasetMeta vs the
v1.csv it describes). Base64-in-JSON transport for the same reason as
datasets.py: no python-multipart on the pinned-dependency list.

Dimensions are read with a hand-rolled PNG/JPEG header parser -- no Pillow
on the pinned-dependency list (build brief hard rule), and a width/height
header read is the only thing this milestone needs from the file.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .project_store import ProjectStore

ImageContentType = Literal["image/png", "image/jpeg"]

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# SOF0..SOF15, excluding DHT(C4)/JPG(C8)/DAC(CC) which share the marker
# range but aren't frame headers -- the standard JPEG "which markers carry
# width/height" list.
_JPEG_SOF_MARKERS = frozenset({0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF})


def _png_dimensions(content: bytes) -> tuple[int, int]:
    if content[:8] != _PNG_SIGNATURE:
        raise ValueError("not a valid PNG file (bad signature)")
    if len(content) < 24 or content[12:16] != b"IHDR":
        raise ValueError("not a valid PNG file (missing IHDR chunk)")
    width, height = struct.unpack(">II", content[16:24])
    return width, height


def _jpeg_dimensions(content: bytes) -> tuple[int, int]:
    if content[:2] != b"\xff\xd8":
        raise ValueError("not a valid JPEG file (bad SOI marker)")
    pos, n = 2, len(content)
    while pos + 4 <= n:
        if content[pos] != 0xFF:
            pos += 1  # resync past a stray fill byte
            continue
        marker = content[pos + 1]
        if marker in _JPEG_SOF_MARKERS:
            # segment shape: length(2) precision(1) height(2) width(2) ...
            height, width = struct.unpack(">HH", content[pos + 5 : pos + 9])
            return width, height
        if marker == 0xD8 or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            pos += 2  # markers that carry no length-prefixed payload
            continue
        seg_len = struct.unpack(">H", content[pos + 2 : pos + 4])[0]
        pos += 2 + seg_len
    raise ValueError("could not find a JPEG SOF marker to read dimensions")


def read_image_dimensions(content: bytes, source_filename: str) -> tuple[int, int]:
    suffix = Path(source_filename).suffix.lower()
    if suffix == ".png":
        return _png_dimensions(content)
    if suffix in (".jpg", ".jpeg"):
        return _jpeg_dimensions(content)
    raise ValueError(f"unsupported image type {suffix!r} -- only .png and .jpg/.jpeg are supported")


def _content_type_for_suffix(suffix: str) -> ImageContentType:
    return "image/png" if suffix == ".png" else "image/jpeg"


class FloorPlanImageMeta(BaseModel):
    """The persisted record (meta.json) -- plain and mutable-by-convention
    like DatasetMeta, not frozen like a Computed[T] result: this is a
    stored file record, not a scientific computation whose immutability
    the schema itself should enforce."""

    schema_version: int = 1
    image_id: str
    project_id: str
    source_filename: str
    created_at: str
    sha256: str
    content_type: ImageContentType
    width_px: int
    height_px: int


def _atomic_write(path: Path, data: bytes) -> None:
    # Same temp-file+rename technique as datasets.py's _atomic_write --
    # duplicated rather than imported, since that one is module-private.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class FloorPlanImageStore:
    """Sibling of DatasetStore -- the same project-folder-plus-meta.json
    shape, under a different subdirectory (floorplans/ instead of
    datasets/)."""

    def __init__(self, project_store: ProjectStore) -> None:
        self.projects = project_store

    def _image_dir(self, project_id: str, image_id: str) -> Path:
        return self.projects.resolved_project_path(project_id) / "floorplans" / image_id

    def save_image(self, project_id: str, source_filename: str, content: bytes, created_at: str) -> FloorPlanImageMeta:
        self.projects.load_project(project_id)  # FileNotFoundError -> 404 at the route layer
        width, height = read_image_dimensions(content, source_filename)
        suffix = Path(source_filename).suffix.lower()
        meta = FloorPlanImageMeta(
            image_id=uuid.uuid4().hex, project_id=project_id, source_filename=source_filename,
            created_at=created_at, sha256=hashlib.sha256(content).hexdigest(),
            content_type=_content_type_for_suffix(suffix), width_px=width, height_px=height,
        )
        d = self._image_dir(project_id, meta.image_id)
        _atomic_write(d / f"original{suffix}", content)
        _atomic_write(d / "meta.json", json.dumps(meta.model_dump(mode="json"), indent=2, sort_keys=True).encode("utf-8"))
        return meta

    def load_meta(self, project_id: str, image_id: str) -> FloorPlanImageMeta:
        path = self._image_dir(project_id, image_id) / "meta.json"
        if not path.exists():
            raise FileNotFoundError(f"floor-plan image {image_id!r} not found in project {project_id!r}")
        return FloorPlanImageMeta.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def load_bytes(self, project_id: str, image_id: str) -> bytes:
        meta = self.load_meta(project_id, image_id)
        suffix = Path(meta.source_filename).suffix.lower()
        return (self._image_dir(project_id, image_id) / f"original{suffix}").read_bytes()
