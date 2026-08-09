"""Route-level tests for T-22..T-25 (build brief: "Registry/routes/tests"):
the generic artifact CRUD + prescore routes (routes/artifacts.py, routes/
prescore.py) need no bespoke route file for any of the four -- same design
finding as T-18..T-21 (test_full_loop.py). Also exercises the close-block
loop end-to-end over real HTTP: an FMEA saved with an unaddressed
severity-9 row blocks an A3 from closing; adding the action and re-saving
the FMEA clears it."""

import base64
import struct
import zlib

import pytest
from fastapi.testclient import TestClient

from factories import TS, make_a3, make_a3_closure, make_control_plan, make_five_s, make_five_s_round, make_fmea, make_fmea_rows, make_standard_work
from sigma_engine.main import app


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data))


def _make_png(width: int, height: int) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(b"".join(b"\x00" + bytes([180]) * width for _ in range(height)))
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    return TestClient(app)


def _create_project(client):
    resp = client.post("/project/create", json={"project_id": "m4-1", "name": "Milestone 4", "created_at": TS})
    assert resp.status_code == 200, resp.text


def test_t22_control_plan_saves_loads_and_prescores_through_the_generic_routes(client):
    _create_project(client)
    save = client.post("/project/m4-1/artifacts/T-22", json=make_control_plan())
    assert save.status_code == 200, save.text
    assert save.json() == {"artifact_id": "control-plan-001", "tool_id": "T-22", "version": 1}

    loaded = client.get("/project/m4-1/artifacts/control-plan-001").json()
    assert loaded["plan_health"]["value"]["is_theater"] is False
    assert loaded["check_in_schedule"]["next_due"]["value"] == "2026-08-10"

    prescore = client.post("/prescore/T-22", json=make_control_plan()).json()
    ids = {r["check_id"] for r in prescore}
    assert "owner_named" in ids
    assert all(r["status"] == "pass" for r in prescore), prescore


def test_t23_five_s_saves_and_prescores_through_the_generic_routes(client):
    _create_project(client)
    save = client.post("/project/m4-1/artifacts/T-23", json=make_five_s())
    assert save.status_code == 200, save.text
    prescore = client.post("/prescore/T-23", json=make_five_s()).json()
    assert any(r["check_id"] == "scores_in_range" and r["status"] == "pass" for r in prescore)


def test_t23_photos_reuse_the_existing_floorplan_image_store_and_route(client):
    # Task brief's reuse instruction: 5S photos ride the SAME store/route
    # T-07's floor-plan image uses (floorplan_images.py, routes/
    # floorplans.py) -- no new store, no new route, for a 5S photo.
    _create_project(client)
    content_b64 = base64.b64encode(_make_png(80, 60)).decode("ascii")
    upload = client.post("/project/m4-1/floorplans", json={"source_filename": "5s-round1.png", "content_base64": content_b64, "created_at": TS})
    assert upload.status_code == 200, upload.text
    meta = upload.json()
    assert meta["width_px"] == 80 and meta["height_px"] == 60

    photo_ref = {"image_id": meta["image_id"], "source_filename": meta["source_filename"], "sha256": meta["sha256"], "width_px": meta["width_px"], "height_px": meta["height_px"]}
    round_with_photo = make_five_s_round(photos=[photo_ref])
    save = client.post("/project/m4-1/artifacts/T-23", json=make_five_s(rounds=[round_with_photo]))
    assert save.status_code == 200, save.text

    fetched = client.get(f"/project/m4-1/floorplans/{meta['image_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["content_base64"] == content_b64

    prescore = client.post("/prescore/T-23", json=make_five_s(rounds=[round_with_photo])).json()
    assert next(r for r in prescore if r["check_id"] == "photos_present")["status"] == "pass"


def test_t24_standard_work_saves_and_prescores_through_the_generic_routes(client):
    _create_project(client)
    save = client.post("/project/m4-1/artifacts/T-24", json=make_standard_work())
    assert save.status_code == 200, save.text
    prescore = client.post("/prescore/T-24", json=make_standard_work()).json()
    assert any(r["check_id"] == "metadata_present" and r["status"] == "pass" for r in prescore)


def test_t25_a3_saves_and_prescores_through_the_generic_routes(client):
    _create_project(client)
    save = client.post("/project/m4-1/artifacts/T-25", json=make_a3())
    assert save.status_code == 200, save.text
    loaded = client.get("/project/m4-1/artifacts/a3-001").json()
    assert loaded["closure"]["close_check"]["value"]["close_blocked"] is False


def test_close_block_loop_over_http_blocks_then_clears_when_fmea_is_actioned(client):
    _create_project(client)

    # An FMEA with row-a left severity-9, safety-worded, unaddressed.
    fmea_save = client.post("/project/m4-1/artifacts/T-16", json=make_fmea())
    assert fmea_save.status_code == 200, fmea_save.text
    fmea_loaded = client.get("/project/m4-1/artifacts/fmea-001").json()
    blocking_flags = fmea_loaded["blocking_flags"]["value"]
    assert len(blocking_flags) == 1 and blocking_flags[0]["row_id"] == "row-a"

    fmea_check = {"fmea_artifact_id": "fmea-001", "blocking_flags": blocking_flags}

    # A3 sees the block.
    open_body = make_a3(closure=make_a3_closure(fmea_check=fmea_check, project_status="open"))
    open_save = client.post("/project/m4-1/artifacts/T-25", json=open_body)
    assert open_save.status_code == 200, open_save.text
    open_loaded = client.get("/project/m4-1/artifacts/a3-001").json()
    assert open_loaded["closure"]["close_check"]["value"]["close_blocked"] is True

    # Declaring the project closed while blocked is refused (422), not silently accepted.
    closed_attempt = make_a3(closure=make_a3_closure(fmea_check=fmea_check, project_status="closed"))
    refused = client.post("/project/m4-1/artifacts/T-25", json=closed_attempt)
    assert refused.status_code == 422
    assert "R-WRAP-03" in str(refused.json())

    # Fix the FMEA row (action + owner added) and re-save.
    fixed_rows = make_fmea_rows()
    fixed_rows[0]["action"] = "Add a second injector-pressure check before mold"
    fixed_rows[0]["action_owner"] = "Sam Lee"
    fixed_save = client.post("/project/m4-1/artifacts/T-16", json=make_fmea(rows=fixed_rows))
    assert fixed_save.status_code == 200, fixed_save.text
    fixed_loaded = client.get("/project/m4-1/artifacts/fmea-001").json()
    assert fixed_loaded["blocking_flags"]["value"] == []

    # The A3 now closes cleanly.
    cleared_check = {"fmea_artifact_id": "fmea-001", "blocking_flags": []}
    closed_body = make_a3(closure=make_a3_closure(fmea_check=cleared_check, project_status="closed"))
    closed_save = client.post("/project/m4-1/artifacts/T-25", json=closed_body)
    assert closed_save.status_code == 200, closed_save.text
    closed_loaded = client.get("/project/m4-1/artifacts/a3-001").json()
    assert closed_loaded["closure"]["close_check"]["value"]["close_blocked"] is False
    assert closed_loaded["closure"]["project_status"] == "closed"


def test_prescore_t21_with_project_id_runs_the_measurement_check_on_file_check(client):
    """M6 eval fix (persona FL-07): /prescore/T-21?project_id=... threads
    the project's T-12 state into the T-21 prescore -- flag when a frozen
    chart has no T-12 on file, pass naming the verdict once one exists.
    Without project_id the response keeps its artifact-only shape."""
    from factories import make_continuous_msa, make_control_chart_imr

    _create_project(client)

    body = make_control_chart_imr()
    plain = client.post("/prescore/T-21", json=body)
    assert plain.status_code == 200, plain.text
    assert "measurement_check_on_file" not in {r["check_id"] for r in plain.json()}

    flagged = client.post("/prescore/T-21?project_id=m4-1", json=body)
    assert flagged.status_code == 200, flagged.text
    by_id = {r["check_id"]: r for r in flagged.json()}
    check = by_id["measurement_check_on_file"]
    assert check["status"] == "flag"
    assert "no measurement check (T-12) on file" in check["detail"]

    save_msa = client.post("/project/m4-1/artifacts/T-12", json=make_continuous_msa())
    assert save_msa.status_code == 200, save_msa.text

    passed = client.post("/prescore/T-21?project_id=m4-1", json=body)
    by_id = {r["check_id"]: r for r in passed.json()}
    check = by_id["measurement_check_on_file"]
    assert check["status"] == "pass"
    assert "latest T-12 verdict" in check["detail"]

    missing = client.post("/prescore/T-21?project_id=no-such-project", json=body)
    assert missing.status_code == 404
