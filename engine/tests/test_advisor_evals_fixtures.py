"""Tests for the M6 advisor-evals unit (evals/advisor-evals/, PLAN §9's
"Advisor evals" paragraph). This file does NOT grade the advisor's actual
judgment -- there is no Anthropic API key in this environment and no live
model call happens anywhere in this file (see evals/advisor-evals/README.md
for the two-layer design this implies). What it proves, in order:

1. Every fixture body in evals/advisor-evals/fixtures/*.json validates
   against its own schema via TestClient -- the fixture-set's own
   commitment ("the advisor only ever sees schema-legal drafts").
2. Every fixture's *.expect.json "deterministic_layer.prescore_flags" is
   re-derived from a FRESH live prescore run and compared byte-for-byte --
   if a prescore check's behavior ever changes, this test catches the
   drift instead of the recorded expectation silently going stale.
3. evals/advisor-evals/run_advisor_evals.py's own grading mechanics: the
   canned "would pass" response for every fixture grades pass, the canned
   "would fail" response grades fail, and the grader never raises on
   garbage input. `advisor-evals` has a hyphen and is therefore not a
   legal Python package/module name, so the runner is loaded by file path
   (importlib), not a dotted import.
4. One true end-to-end mock-transport pass per structured mode (review,
   tollgate, validate) -- PLAN §9 unit constraint #3, "mock-transport
   validation that the runner's mechanics work end to end": a real POST
   /advisor/ask or /advisor/validate call, through the actual FastAPI
   route stack (context assembly, budget, structured-output parsing,
   route dispatch all run for real), with respx intercepting only the
   real Anthropic Messages endpoint and returning one of this suite's own
   canned fixtures/mock-responses/*.json payloads as the fenced-JSON model
   text -- the exact technique test_routes_advisor.py already uses for
   the advisor's other tests, reused here rather than forked.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from sigma_engine.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
ADVISOR_EVALS_DIR = REPO_ROOT / "evals" / "advisor-evals"
FIXTURES_DIR = ADVISOR_EVALS_DIR / "fixtures"

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


def _load_runner_module() -> ModuleType:
    """`evals/advisor-evals/run_advisor_evals.py`, loaded by file path.
    `advisor-evals` (hyphenated) can never be a dotted Python package name,
    hyphen or not -- this is the only way to reach it from here, and it is
    also exactly how a user is told to run the script (as a standalone
    file under engine/.venv/bin/python), not as an installed package."""
    spec = importlib.util.spec_from_file_location("run_advisor_evals", ADVISOR_EVALS_DIR / "run_advisor_evals.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered in sys.modules BEFORE exec_module: the module's own
    # `@dataclass` decorators (Fixture, GradeResult) resolve their owning
    # module via sys.modules[cls.__module__] while executing, which is
    # only populated once exec_module actually runs a module that was
    # already registered -- omitting this line raises AttributeError
    # ('NoneType' object has no attribute '__dict__') from inside
    # dataclasses._is_type, not from anything this test file does wrong.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


def _fixture_ids() -> list[str]:
    ids = sorted(p.name[: -len(".expect.json")] for p in FIXTURES_DIR.glob("*.expect.json"))
    assert ids, f"no fixtures found under {FIXTURES_DIR}"
    return ids


FIXTURE_IDS = _fixture_ids()


def _load_fixture(fixture_id: str) -> tuple[dict, dict]:
    body = json.loads((FIXTURES_DIR / f"{fixture_id}.json").read_text(encoding="utf-8"))
    expect = json.loads((FIXTURES_DIR / f"{fixture_id}.expect.json").read_text(encoding="utf-8"))
    return body, expect


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return TestClient(app)


# ================================================================
# 0. The fixture set's own shape -- the sidecar schema the build brief
# itself specifies (fixture_id, tool_id, mode, defect, must_catch,
# deterministic_layer{schema_blocks, prescore_flags}), plus this unit's
# own "grading" extension (checks + text_fallback_keywords). Cheap and
# catches a malformed fixture before the more expensive tests below try
# to use it.
# ================================================================


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_expectation_file_has_the_required_shape(fixture_id):
    _, expect = _load_fixture(fixture_id)
    assert expect["fixture_id"] == fixture_id
    assert expect["tool_id"].startswith("T-")
    assert expect["mode"] in ("review", "tollgate", "validate")
    assert isinstance(expect["defect"], str) and expect["defect"]
    assert isinstance(expect["must_catch"], list) and expect["must_catch"]
    det = expect["deterministic_layer"]
    assert isinstance(det["schema_blocks"], bool)
    assert isinstance(det["prescore_flags"], list)
    grading = expect["grading"]
    assert isinstance(grading["checks"], list) and grading["checks"]
    assert isinstance(grading["text_fallback_keywords"], list) and grading["text_fallback_keywords"]
    live_setup = expect["live_setup"]
    assert "project_id" in live_setup and "advisor_ask" in live_setup


def test_six_fixtures_cover_the_plan_9_defect_list():
    """PLAN §9 names exactly six: two crude, three subtle, one tollgate."""
    assert FIXTURE_IDS == [
        "crude-charter-solution-shaped",
        "crude-fishbone-zero-evidence",
        "subtle-capability-on-unstable",
        "subtle-controlplan-no-owner",
        "subtle-proof-confounded",
        "tollgate-premature-improve",
    ]


# ================================================================
# 1. Every fixture body validates against its own schema (the fixture
# set's own commitment: the advisor only ever sees schema-legal drafts).
# ================================================================


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_fixture_body_validates_against_its_schema(client, fixture_id):
    body, expect = _load_fixture(fixture_id)
    resp = client.post(f"/artifacts/{expect['tool_id']}/validate", json=body)
    assert resp.status_code == 200, resp.text
    assert resp.json()["valid"] is True
    # The expectation file's own recorded claim must agree with reality.
    assert expect["deterministic_layer"]["validate_status"] == 200
    assert expect["deterministic_layer"]["schema_blocks"] is False


# ================================================================
# 2. Recorded prescore flags match a fresh live run, exactly.
# ================================================================


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_fixture_prescore_matches_the_recorded_deterministic_layer(client, fixture_id):
    body, expect = _load_fixture(fixture_id)
    resp = client.post(f"/prescore/{expect['tool_id']}", json=body)
    assert resp.status_code == 200, resp.text
    fresh = resp.json()
    recorded = expect["deterministic_layer"]["prescore_flags"]
    assert fresh == recorded, (
        f"{fixture_id}: a fresh live prescore run no longer matches the recorded deterministic_layer -- "
        f"either a prescore check's behavior changed (re-freeze the expectation file and say why in the commit "
        f"message, evals/harness/'s own re-freezing convention) or this is a real regression.\nfresh={fresh}\n"
        f"recorded={recorded}"
    )


# ================================================================
# 3. The mock runner's own grading mechanics.
# ================================================================


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_mock_grader_scores_the_passing_canned_response_as_pass(fixture_id):
    _, expect = _load_fixture(fixture_id)
    canned = runner.load_mock_response(fixture_id, "pass")
    grade = runner.grade_response(expect, canned)
    assert grade.passed is True, grade.reason


@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_mock_grader_scores_the_failing_canned_response_as_fail(fixture_id):
    _, expect = _load_fixture(fixture_id)
    canned = runner.load_mock_response(fixture_id, "fail")
    grade = runner.grade_response(expect, canned)
    assert grade.passed is False, grade.reason


def test_mock_mode_end_to_end_self_check_passes():
    """The same invocation `engine/.venv/bin/python run_advisor_evals.py
    --mock` makes: every canned pass/fail pair, for every fixture, must be
    classified correctly, or the exit code (asserted here as the return
    code) is non-zero."""
    fixtures = runner.load_fixtures()
    code, output = runner.run_mock(fixtures)
    assert code == 0, output
    assert output["summary"]["grader_mechanics_ok"] is True
    assert output["summary"]["self_checks_failed"] == 0
    assert output["summary"]["total_canned_responses"] == len(fixtures) * 2


_GARBAGE_RESPONSES = [
    {},
    None,
    "a plain string, not a dict",
    42,
    [],
    {"structured": None},
    {"structured": {}},
    {"structured": {"criteria": "not a list"}},
    {"structured": {"criteria": [None, 42, "oops"]}},
    {"structured": {"criteria": [{"criterion_id": 123, "verdict": None}]}},
    {"flags": "not a list"},
    {"flags": [None, 42, {"field_path": None, "severity": 7}]},
    {"unstructured_fallback": True},  # no "answer"/"raw_answer" at all
    {"unstructured_fallback": "not even a bool"},
]


@pytest.mark.parametrize("garbage", _GARBAGE_RESPONSES, ids=[repr(g)[:40] for g in _GARBAGE_RESPONSES])
@pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
def test_grader_never_crashes_on_garbage(fixture_id, garbage):
    _, expect = _load_fixture(fixture_id)
    grade = runner.grade_response(expect, garbage)  # must not raise
    assert grade.passed is False  # garbage never accidentally scores a pass
    assert isinstance(grade.reason, str) and grade.reason


# ================================================================
# 4. Mock-transport end-to-end: a real advisor call through the real route
# stack, one per structured mode this fixture set uses.
# ================================================================


def _fenced_json(obj: dict) -> str:
    return "```json\n" + json.dumps(obj) + "\n```"


def _canned_anthropic_message(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 5, "output_tokens": 5},
        },
    )


def _configure_and_create_project(client: TestClient, project_id: str) -> None:
    resp = client.put("/advisor/settings", json={"api_key": "sk-ant-mock-transport-test", "enabled": True})
    assert resp.status_code == 200, resp.text
    resp = client.post("/project/create", json={"project_id": project_id, "name": "mock-transport", "created_at": "2026-08-08T00:00:00"})
    assert resp.status_code == 200, resp.text


@respx.mock
def test_mock_transport_review_mode_end_to_end(client):
    fixture_id = "crude-charter-solution-shaped"
    body, expect = _load_fixture(fixture_id)
    project_id = "mock-transport-review"
    _configure_and_create_project(client, project_id)
    assert client.post(f"/project/{project_id}/artifacts/{expect['tool_id']}", json=body).status_code == 200

    passing = runner.load_mock_response(fixture_id, "pass")
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_anthropic_message(_fenced_json(passing["structured"])))

    resp = client.post("/advisor/ask", json={"project_id": project_id, "mode": "review", "artifact_id": body["artifact_id"]})
    assert resp.status_code == 200, resp.text
    assert route.call_count == 1

    payload = resp.json()
    assert payload["unstructured_fallback"] is False
    assert payload["structured"] is not None
    grade = runner.grade_response(expect, payload)
    assert grade.passed is True, grade.reason


@respx.mock
def test_mock_transport_tollgate_mode_end_to_end(client):
    fixture_id = "tollgate-premature-improve"
    body, expect = _load_fixture(fixture_id)
    project_id = "mock-transport-tollgate"
    _configure_and_create_project(client, project_id)
    assert client.post(f"/project/{project_id}/artifacts/{expect['tool_id']}", json=body).status_code == 200

    passing = runner.load_mock_response(fixture_id, "pass")
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_anthropic_message(_fenced_json(passing["structured"])))

    resp = client.post("/advisor/ask", json={"project_id": project_id, "mode": "tollgate", "phase": expect["phase"]})
    assert resp.status_code == 200, resp.text
    assert route.call_count == 1

    payload = resp.json()
    assert payload["structured"]["recommendation"] == "no_go"
    grade = runner.grade_response(expect, payload)
    assert grade.passed is True, grade.reason


@respx.mock
def test_mock_transport_validate_mode_end_to_end(client):
    fixture_id = "subtle-capability-on-unstable"
    body, expect = _load_fixture(fixture_id)
    project_id = "mock-transport-validate"
    _configure_and_create_project(client, project_id)
    # validate mode is a pre-save DRAFT check -- deliberately not saved first.

    passing = runner.load_mock_response(fixture_id, "pass")
    canned_model_payload = {"flags": passing["flags"], "checked_field_count": passing["checked_field_count"]}
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_anthropic_message(_fenced_json(canned_model_payload)))

    resp = client.post("/advisor/validate", json={"project_id": project_id, "tool_id": expect["tool_id"], "body": body})
    assert resp.status_code == 200, resp.text
    assert route.call_count == 1

    payload = resp.json()
    assert payload["unstructured_fallback"] is False
    assert len(payload["flags"]) == 1
    grade = runner.grade_response(expect, payload)
    assert grade.passed is True, grade.reason


@respx.mock
def test_mock_transport_a_malformed_model_reply_never_500s(client):
    """Belt-and-braces: the real structured.py retry path (never forked by
    this eval unit) still governs -- a model reply with no fenced JSON
    block degrades to unstructured_fallback, never a 500, exactly like
    every other advisor caller in this engine."""
    fixture_id = "crude-charter-solution-shaped"
    body, expect = _load_fixture(fixture_id)
    project_id = "mock-transport-malformed"
    _configure_and_create_project(client, project_id)
    assert client.post(f"/project/{project_id}/artifacts/{expect['tool_id']}", json=body).status_code == 200

    # Two calls: the first (malformed) attempt, then structured.py's one retry -- also malformed.
    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_anthropic_message("I refuse to use JSON today."))

    resp = client.post("/advisor/ask", json={"project_id": project_id, "mode": "review", "artifact_id": body["artifact_id"]})
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["unstructured_fallback"] is True
    assert payload["structured"] is None

    grade = runner.grade_response(expect, payload)
    assert grade.passed is False  # the text fallback keywords aren't in "I refuse to use JSON today."
