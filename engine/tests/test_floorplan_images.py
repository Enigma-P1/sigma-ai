"""Tests for floorplan_images.py: the hand-rolled PNG/JPEG dimension
parser and the FloorPlanImageStore save/load round trip."""

import struct
import zlib

import pytest

from sigma_engine.floorplan_images import FloorPlanImageStore, read_image_dimensions
from sigma_engine.project_store import ProjectStore


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data))


def make_real_png(width: int, height: int, gray_value: int = 180) -> bytes:
    """A genuinely valid, decodable 8-bit grayscale PNG (not just a header
    stub) -- built from stdlib zlib alone, no Pillow (build brief hard rule)."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # bit depth 8, color type 0 (grayscale)
    raw_scanlines = b"".join(b"\x00" + bytes([gray_value]) * width for _ in range(height))  # filter byte 0 per row
    idat = zlib.compress(raw_scanlines)
    return b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", ihdr) + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b"")


def make_minimal_jpeg(width: int, height: int) -> bytes:
    """Just enough real JPEG structure for the SOF0 parser to find width/
    height -- an APP0 segment then an SOF0 frame header, no scan data
    (this milestone never decodes pixels, only reads the header)."""
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x01\x01\x00" + struct.pack(">HH", 1, 1) + b"\x00\x00"
    sof0_data = struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00"
    sof0 = b"\xff\xc0" + struct.pack(">H", len(sof0_data) + 2) + sof0_data
    return soi + app0 + sof0


def test_png_dimensions_read_correctly():
    assert read_image_dimensions(make_real_png(120, 90), "floor.png") == (120, 90)


def test_jpeg_dimensions_read_correctly():
    assert read_image_dimensions(make_minimal_jpeg(200, 150), "floor.jpg") == (200, 150)


def test_png_rejects_bad_signature():
    with pytest.raises(ValueError, match="signature"):
        read_image_dimensions(b"not a png", "floor.png")


def test_jpeg_rejects_bad_soi_marker():
    with pytest.raises(ValueError, match="SOI"):
        read_image_dimensions(b"not a jpeg", "floor.jpg")


def test_unsupported_extension_raises():
    with pytest.raises(ValueError, match="unsupported image type"):
        read_image_dimensions(make_real_png(10, 10), "floor.gif")


def test_store_save_and_load_round_trip(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-08T00:00:00")
    store = FloorPlanImageStore(projects)
    content = make_real_png(100, 80)

    meta = store.save_image("proj-1", "floor.png", content, "2026-08-08T00:01:00")
    assert meta.width_px == 100
    assert meta.height_px == 80
    assert meta.content_type == "image/png"
    assert len(meta.sha256) == 64

    reloaded_meta = store.load_meta("proj-1", meta.image_id)
    assert reloaded_meta == meta
    assert store.load_bytes("proj-1", meta.image_id) == content


def test_store_save_404_on_missing_project(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    store = FloorPlanImageStore(projects)
    with pytest.raises(FileNotFoundError):
        store.save_image("no-such-project", "floor.png", make_real_png(10, 10), "2026-08-08T00:00:00")


def test_store_load_404_on_missing_image(tmp_path):
    projects = ProjectStore(tmp_path / "projects")
    projects.create_project("proj-1", "Coffee Bar", "2026-08-08T00:00:00")
    store = FloorPlanImageStore(projects)
    with pytest.raises(FileNotFoundError):
        store.load_meta("proj-1", "no-such-image")
