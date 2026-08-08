"""Route tests for /project/{id}/floorplans*, plus T-07 end-to-end through
the generic registry-driven artifact/prescore routes (test_routes.py's
test_process_map_crud_and_prescore_via_registry pattern, applied to T-07)."""

import base64
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from factories import make_spaghetti
from sigma_engine.main import app


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data))


def _make_png(width: int, height: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(b"".join(b"\x00" + bytes([180]) * width for _ in range(height)))
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


PNG_BYTES = _make_png(120, 90)
B64_PNG = base64.b64encode(PNG_BYTES).decode("ascii")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client, project_id="proj-1"):
    resp = client.post("/project/create", json={"project_id": project_id, "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"})
    assert resp.status_code == 200, resp.text


def test_upload_and_get_floorplan_round_trip(client):
    _create_project(client)
    upload = client.post(
        "/project/proj-1/floorplans",
        json={"source_filename": "floor.png", "content_base64": B64_PNG, "created_at": "2026-08-07T01:00:00"},
    )
    assert upload.status_code == 200, upload.text
    meta = upload.json()
    assert meta["width_px"] == 120
    assert meta["height_px"] == 90
    assert len(meta["sha256"]) == 64

    detail = client.get(f"/project/proj-1/floorplans/{meta['image_id']}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["meta"] == meta
    assert body["content_base64"] == B64_PNG


def test_upload_404_on_missing_project(client):
    resp = client.post(
        "/project/no-such-project/floorplans",
        json={"source_filename": "floor.png", "content_base64": B64_PNG, "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 404


def test_get_404_for_missing_image(client):
    _create_project(client)
    assert client.get("/project/proj-1/floorplans/no-such-image").status_code == 404


def test_upload_422_on_bad_base64(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/floorplans",
        json={"source_filename": "floor.png", "content_base64": "not-valid-base64!!", "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 422


def test_upload_422_on_unsupported_extension(client):
    _create_project(client)
    resp = client.post(
        "/project/proj-1/floorplans",
        json={"source_filename": "floor.gif", "content_base64": B64_PNG, "created_at": "2026-08-07T01:00:00"},
    )
    assert resp.status_code == 422


def test_spaghetti_crud_and_prescore_via_registry(client):
    """T-07 end-to-end through the generic registry-driven routes: upload
    the image, validate, save (metrics computed server-side), load, and
    prescore -- the same shape as T-06's own registry test."""
    _create_project(client)
    upload = client.post(
        "/project/proj-1/floorplans",
        json={"source_filename": "floor.png", "content_base64": B64_PNG, "created_at": "2026-08-07T01:00:00"},
    )
    image_meta = upload.json()

    body = make_spaghetti(floor_plan={
        "image_id": image_meta["image_id"], "source_filename": image_meta["source_filename"],
        "sha256": image_meta["sha256"], "width_px": image_meta["width_px"], "height_px": image_meta["height_px"],
    })
    validated = client.post("/artifacts/T-07/validate", json=body)
    assert validated.status_code == 200, validated.text
    assert validated.json()["artifact"]["metrics"]["value"]["routes"][0]["distance_per_trip"] == pytest.approx(70.0)

    saved = client.post("/project/proj-1/artifacts/T-07", json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"artifact_id": "spaghetti-001", "tool_id": "T-07", "version": 1}

    loaded = client.get("/project/proj-1/artifacts/spaghetti-001")
    assert loaded.status_code == 200
    assert loaded.json()["metrics"]["value"]["total_daily_distance_all"] == pytest.approx(420.0)

    prescore = client.post("/prescore/T-07", json=body)
    assert prescore.status_code == 200, prescore.text
    statuses = {r["check_id"]: r["status"] for r in prescore.json()}
    assert statuses["calibration_present"] == "pass"
    assert statuses["metrics_consistency"] == "pass"
