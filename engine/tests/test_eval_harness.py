"""Tests for the M6 golden-scenario eval harness (evals/harness/) -- run
from engine/tests per the build brief so `pytest -q` picks them up
alongside the rest of the suite, even though the harness itself is a
separate package outside sigma_engine (repo-root sys.path insert below,
the same move evals/harness/run_goldens.py makes).

Covers exactly the four things the build brief calls out: normalizer
determinism, the manifest schema, the coverage-check failure mode, and
the matrix parser against the real file -- plus the golden-id table's
own sync check, since a stale table would otherwise fail silently.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.harness.lib import coverage as coverage_mod
from evals.harness.lib import golden_id_map as golden_id_map_mod
from evals.harness.lib.client import EngineClient
from evals.harness.lib.matrix import assert_tier_a_count, extract_golden_ids, parse_tier_a_ids, parse_tool_inventory
from evals.harness.lib.normalize import canonical_json_bytes, canonicalize_for_golden, hash_value, normalize
from evals.harness.lib.recorder import Recorder

MATRIX_PATH = REPO_ROOT / "docs" / "traceability-matrix.md"
S1_SPEC = REPO_ROOT / "evals" / "scenarios" / "s1-helpdesk" / "spec.md"
S2_SPEC = REPO_ROOT / "evals" / "scenarios" / "s2-library" / "spec.md"
ENGINE_TESTS_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# 1. Normalizer determinism (same input -> same bytes)
# --------------------------------------------------------------------------

def test_canonical_json_bytes_is_byte_identical_across_calls():
    obj = {"b": 2, "a": [1, 2, {"z": 3.5, "y": None}], "c": "text"}
    assert canonical_json_bytes(obj) == canonical_json_bytes(obj) == canonical_json_bytes(json.loads(json.dumps(obj)))


def test_canonical_json_bytes_is_insensitive_to_key_order():
    a = {"one": 1, "two": {"x": 1, "y": 2}}
    b = {"two": {"y": 2, "x": 1}, "one": 1}
    assert canonical_json_bytes(a) == canonical_json_bytes(b)


def test_hash_value_is_deterministic_and_content_sensitive():
    obj = {"path": "/x", "method": "POST", "body": {"a": 1}}
    assert hash_value(obj) == hash_value(json.loads(json.dumps(obj)))
    other = {"path": "/x", "method": "POST", "body": {"a": 2}}
    assert hash_value(obj) != hash_value(other)


def test_normalize_strips_dataset_id_and_image_id_by_key_name():
    obj = {"dataset_id": "9b1b8c167bbf45079f5c6de910dd31f0", "image_id": "1288cebacc404cb584cc42aa7bd75c24", "column": "wait_minutes"}
    normalized = normalize(obj)
    assert normalized["dataset_id"] == "<normalized>"
    assert normalized["image_id"] == "<normalized>"
    assert normalized["column"] == "wait_minutes"  # untouched


def test_normalize_also_catches_a_uuid4_hex_value_under_an_unrelated_key():
    """Regression case found while building the S-1 driver: an A3 panel's
    `seeded_from.artifact_ref` held a raw dataset_id string -- a real
    uuid4().hex leaking under a key name the NORMALIZED_KEYS set doesn't
    know about. The value-shape rule is the defense-in-depth fix."""
    leaked = {"seeded_from": {"artifact_ref": "880afc15ef9c4f369f28fbb72d755a7a", "tool_id": "T-13"}}
    normalized = normalize(leaked)
    assert normalized["seeded_from"]["artifact_ref"] == "<normalized>"


def test_normalize_does_not_touch_sha256_hashes_or_ordinary_ids():
    sha = "6d31a43fbf305e84fad004cb20d0d06b02a395c3a59f9e6ba89aaf2ba1c72dc0"  # 64 hex chars, not 32
    obj = {"dataset_sha256": sha, "artifact_id": "coffee-charter", "input_hash": sha}
    normalized = normalize(obj)
    assert normalized == obj  # byte-for-byte unchanged -- these are deterministic, keep them for drift detection


def test_canonicalize_for_golden_round_trips_through_json_the_same_way_it_was_frozen():
    obj = {"dataset_id": "9b1b8c167bbf45079f5c6de910dd31f0", "value": 1.0}
    written = json.loads(canonical_json_bytes(normalize(obj)))
    assert canonicalize_for_golden(obj) == written


# --------------------------------------------------------------------------
# 2. Manifest schema
# --------------------------------------------------------------------------

def _mock_engine(handler) -> EngineClient:
    return EngineClient(transport=httpx.MockTransport(handler))


def test_manifest_schema_shape(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/project/create":
            return httpx.Response(200, json={"project_id": "p", "name": "n", "created_at": "2026-01-01T00:00:00Z",
                                                "updated_at": "2026-01-01T00:00:00Z", "artifact_index": {}})
        return httpx.Response(200, json={"ok": True, "path": request.url.path})

    engine = _mock_engine(handler)
    recorder = Recorder("unit-test-scenario", engine, tmp_path, "freeze")
    recorder.call("project.create", "POST", "/project/create", {"project_id": "p", "name": "n", "created_at": "2026-01-01T00:00:00Z"})
    recorder.call("T-03.validate", "POST", "/artifacts/T-03/validate", {"x": 1}, tool_ids=["T-03"])
    report = recorder.finalize()

    assert report.clean
    manifest = json.loads((tmp_path / "unit-test-scenario" / "manifest.json").read_text())
    assert manifest["scenario_id"] == "unit-test-scenario"
    assert manifest["step_count"] == 2
    assert [s["name"] for s in manifest["steps"]] == ["project.create", "T-03.validate"]
    step = manifest["steps"][1]
    assert set(step) == {"name", "tool_ids", "method", "path", "status_code", "input_hash"}
    assert step["tool_ids"] == ["T-03"]
    assert step["method"] == "POST"
    assert step["path"] == "/artifacts/T-03/validate"
    assert step["status_code"] == 200
    assert step["input_hash"] == hash_value({"path": "/artifacts/T-03/validate", "method": "POST", "body": {"x": 1}})


def test_manifest_input_hash_is_stable_even_when_the_body_carries_a_fresh_dataset_id(tmp_path):
    """Two runs that mint DIFFERENT random dataset_ids must still produce
    the SAME manifest input_hash for an otherwise-identical step -- the
    whole point of normalizing before hashing (lib/recorder.py's
    `hash_value` call)."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    engine = _mock_engine(handler)
    r1 = Recorder("s", engine, tmp_path / "r1", "freeze")
    r1.call("x", "POST", "/artifacts/T-01/validate", {"dataset_id": "9b1b8c167bbf45079f5c6de910dd31f0", "v": 1}, tool_ids=["T-01"])
    r2 = Recorder("s", engine, tmp_path / "r2", "freeze")
    r2.call("x", "POST", "/artifacts/T-01/validate", {"dataset_id": "3ed53e71a08e46ec8a37f5c89d51d202", "v": 1}, tool_ids=["T-01"])

    assert r1.manifest_steps[0].input_hash == r2.manifest_steps[0].input_hash


def test_recorder_call_rejects_unexpected_status(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "boom"})

    engine = _mock_engine(handler)
    recorder = Recorder("s", engine, tmp_path, "freeze")
    with pytest.raises(RuntimeError, match="500"):
        recorder.call("x", "POST", "/whatever", {})


def test_recorder_call_rejects_duplicate_step_names(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    engine = _mock_engine(handler)
    recorder = Recorder("s", engine, tmp_path, "freeze")
    recorder.call("x", "POST", "/a", {})
    with pytest.raises(RuntimeError, match="duplicate step name"):
        recorder.call("x", "POST", "/b", {})


def test_replay_reports_a_readable_diff_and_missing_golden(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"n": 2})

    engine = _mock_engine(handler)
    freezer = Recorder("s", engine, tmp_path, "freeze")
    freezer.call("only_step", "POST", "/x", {})
    freezer.finalize()

    def handler_changed(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"n": 3})

    engine2 = _mock_engine(handler_changed)
    replayer = Recorder("s", engine2, tmp_path, "replay")
    replayer.call("only_step", "POST", "/x", {})
    replayer.call("new_step_not_frozen", "POST", "/y", {})
    report = replayer.finalize()

    assert not report.clean
    kinds = {d.kind for d in report.diffs}
    assert "mismatch" in kinds
    assert "missing_golden" in kinds
    mismatch = next(d for d in report.diffs if d.kind == "mismatch")
    assert "-  " in mismatch.detail or "-" in mismatch.detail  # a unified diff, not a blob dump
    assert "+" in mismatch.detail


# --------------------------------------------------------------------------
# 3. Coverage-check failure mode
# --------------------------------------------------------------------------

def test_collective_coverage_passes_on_the_real_files():
    result = coverage_mod.check_collective_coverage(MATRIX_PATH, S1_SPEC, S2_SPEC)
    assert result["tier_a"] == {f"T-{n:02d}" for n in range(1, 26)}


def test_collective_coverage_trips_when_a_tool_is_missing_from_every_scenario(monkeypatch):
    """T-07 and T-09 are, in the real data, exercised by the Coffee Bar
    ALONE (both held-out specs declare them honestly N/A) -- so widening
    the Coffee Bar's own hardcoded N/A set to also drop T-07 makes T-07
    uncovered by all three scenarios at once: a fake scenario set missing
    a tool, using the real matrix and real specs, tripping the hard
    assertion with that exact tool named."""
    fake_na = {**coverage_mod.COFFEE_BAR_NA_TOOLS, "T-07": "test double: pretend the Coffee Bar doesn't cover T-07 either"}
    monkeypatch.setattr(coverage_mod, "COFFEE_BAR_NA_TOOLS", fake_na)

    with pytest.raises(coverage_mod.CoverageDriftError, match=r"T-07"):
        coverage_mod.check_collective_coverage(MATRIX_PATH, S1_SPEC, S2_SPEC)


def test_collective_coverage_trips_on_matrix_tier_a_count_drift(tmp_path):
    fake_matrix = tmp_path / "fake-matrix.md"
    fake_matrix.write_text(
        "## 1. Authoritative tool inventory\n\n"
        "| ID | Tool | Phase | Tier |\n|---|---|---|---|\n"
        "| T-01 | Project Picker | Intake | A |\n"
        "| T-02 | COPQ | Define | A |\n",
        encoding="utf-8",
    )
    with pytest.raises(coverage_mod.CoverageDriftError, match="found 2 tool"):
        coverage_mod.check_collective_coverage(fake_matrix, S1_SPEC, S2_SPEC)


def test_coffee_bar_in_scope_is_every_tier_a_tool_except_t10():
    tier_a = parse_tier_a_ids(MATRIX_PATH)
    assert coverage_mod.coffee_bar_in_scope(tier_a) == tuple(sorted(tier_a - {"T-10"}))


def test_build_coverage_table_reports_zero_uncovered_on_the_real_files():
    table = coverage_mod.build_coverage_table(MATRIX_PATH, S1_SPEC, S2_SPEC)
    assert table["tier_a_tool_count"] == 25
    assert table["uncovered_tools"] == []
    assert table["by_tool"]["T-12"]["s2-library"] == "in_scope"  # the named-exit tool, never accidentally N/A'd


# --------------------------------------------------------------------------
# 4. Matrix parser against the real file
# --------------------------------------------------------------------------

def test_matrix_parser_finds_exactly_25_tier_a_tools():
    ids = parse_tier_a_ids(MATRIX_PATH)
    assert ids == {f"T-{n:02d}" for n in range(1, 26)}


def test_matrix_parser_finds_the_expected_b_v1_1_v2_rows_too():
    rows = parse_tool_inventory(MATRIX_PATH)
    by_tier: dict[str, int] = {}
    for r in rows:
        by_tier[r.tier] = by_tier.get(r.tier, 0) + 1
    assert by_tier == {"A": 25, "B": 3, "v1.1": 6, "v2": 9}


def test_matrix_parser_tool_row_shape():
    rows = {r.tool_id: r for r in parse_tool_inventory(MATRIX_PATH)}
    t12 = rows["T-12"]
    assert t12.phase == "Measure"
    assert t12.tier == "A"
    assert "Measurement Check" in t12.name


def test_assert_tier_a_count_raises_on_wrong_expected_count():
    with pytest.raises(AssertionError, match="expected 26"):
        assert_tier_a_count(MATRIX_PATH, expected=26)


def test_assert_tier_a_count_passes_for_25():
    assert assert_tier_a_count(MATRIX_PATH, expected=25) == {f"T-{n:02d}" for n in range(1, 26)}


def test_extract_golden_ids_finds_the_known_set():
    ids = extract_golden_ids(MATRIX_PATH)
    assert len(ids) == 41
    for expected in ("G-imr-01", "G-msa-02", "G-yield-01", "G-5s-01", "G-hyp-07"):
        assert expected in ids


# --------------------------------------------------------------------------
# Bonus: the golden-id table's own sync check (a stale table would
# otherwise silently under- or over-report coverage).
# --------------------------------------------------------------------------

def test_golden_id_sources_table_matches_the_matrix_exactly():
    golden_id_map_mod.assert_sources_match_matrix(MATRIX_PATH)


def test_golden_id_sources_table_out_of_sync_is_detected(tmp_path, monkeypatch):
    stale = {k: v for k, v in golden_id_map_mod.GOLDEN_ID_SOURCES.items() if k != "G-yield-01"}
    monkeypatch.setattr(golden_id_map_mod, "GOLDEN_ID_SOURCES", stale)
    with pytest.raises(AssertionError, match="G-yield-01"):
        golden_id_map_mod.assert_sources_match_matrix(MATRIX_PATH)


@pytest.fixture
def isolated_tests_dir(tmp_path):
    """A copy of JUST test_artifacts_yield_calc.py in its own directory --
    the real engine/tests/ also contains THIS file, which (being a test
    file about golden ids) necessarily mentions golden-id strings like
    "G-yield-01"/"G-scatter-01" in its own source, which would otherwise
    make find_unit_test_homes() find itself. Scanning an isolated copy of
    only the one real fixture file keeps these two tests independent of
    what this file happens to say about itself."""
    import shutil

    d = tmp_path / "isolated_tests"
    d.mkdir()
    shutil.copy(ENGINE_TESTS_DIR / "test_artifacts_yield_calc.py", d / "test_artifacts_yield_calc.py")
    return d


def test_build_golden_id_map_resolves_g_yield_01_to_both_unit_test_and_harness_step(isolated_tests_dir):
    from evals.harness.lib.recorder import ManifestStep

    manifests = {
        "coffee-bar": [], "s1-helpdesk": [],
        "s2-library": [ManifestStep(name="T-10.validate", tool_ids=["T-10"], method="POST", path="/artifacts/T-10/validate", status_code=200, input_hash="x")],
    }
    result = golden_id_map_mod.build_golden_id_map(MATRIX_PATH, isolated_tests_dir, manifests)
    entry = result["ids"]["G-yield-01"]
    assert set(entry["homes"]) == {"unit-test", "harness-step"}
    assert entry["unit_test_files"] == ["engine/tests/test_artifacts_yield_calc.py"]
    assert entry["harness_steps"][0]["steps"] == ["T-10.validate"]


def test_build_golden_id_map_reports_uncovered_ids_honestly(isolated_tests_dir):
    manifests = {"coffee-bar": [], "s1-helpdesk": [], "s2-library": []}
    result = golden_id_map_mod.build_golden_id_map(MATRIX_PATH, isolated_tests_dir, manifests)
    assert "G-scatter-01" in result["uncovered"]
    reason = result["ids"]["G-scatter-01"]["uncovered_reason"]
    assert isinstance(reason, str) and len(reason) > 20  # a real explanation, not a placeholder
