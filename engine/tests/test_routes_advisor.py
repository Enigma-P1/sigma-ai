"""Route-level tests for /advisor/ask, /advisor/settings, /advisor/status
(M5 brief). respx intercepts the real Anthropic Messages endpoint globally
-- no http_client test seam anywhere in routes/advisor.py or client.py's
production call path, so these exercise the actual code the app runs, not
a stand-in."""

from __future__ import annotations

import json

import httpx
import respx
import pytest
from factories import make_copq, make_fishbone
from fastapi.testclient import TestClient

from sigma_engine.advisor.client import ANTHROPIC_API_KEY_ENV_VAR
from sigma_engine.advisor.context import MAX_QUESTION_LENGTH, REQUEST_ARTIFACT_PREFIX
from sigma_engine.main import app

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGMA_PROJECTS_ROOT", str(tmp_path / "projects"))
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV_VAR, raising=False)
    return TestClient(app)


def _canned_message(text: str = "an answer") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 5, "output_tokens": 5},
        },
    )


def _create_project_and_copq(client: TestClient) -> None:
    resp = client.post(
        "/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"}
    )
    assert resp.status_code == 200, resp.text
    saved = client.post("/project/proj-1/artifacts/T-02", json=make_copq())
    assert saved.status_code == 200, saved.text


def _create_project_and_fishbone(client: TestClient) -> None:
    resp = client.post(
        "/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"}
    )
    assert resp.status_code == 200, resp.text
    saved = client.post("/project/proj-1/artifacts/T-15", json=make_fishbone())
    assert saved.status_code == 200, saved.text


def _fully_configure(client: TestClient) -> None:
    resp = client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    assert resp.status_code == 200, resp.text


# ---- /advisor/status ----


def test_status_reports_unconfigured_with_no_key(client):
    resp = client.post("/advisor/status")
    assert resp.status_code == 200
    assert resp.json() == {"configured": False, "model": "claude-sonnet-5"}


def test_status_reports_configured_once_a_key_is_saved(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-realkey1234", "enabled": True})
    resp = client.post("/advisor/status")
    assert resp.json() == {"configured": True, "model": "claude-sonnet-5"}


def test_status_reports_unconfigured_when_disabled_even_with_a_key(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-realkey1234", "enabled": False})
    resp = client.post("/advisor/status")
    assert resp.json()["configured"] is False


# ---- /advisor/settings ----


def test_settings_default_get_is_honest_and_unset(client):
    resp = client.get("/advisor/settings")
    assert resp.status_code == 200
    assert resp.json() == {"api_key_masked": None, "base_url": None, "enabled": True}


def test_settings_put_then_get_masks_the_key(client):
    put = client.put("/advisor/settings", json={"api_key": "sk-ant-abcdefgh1234", "base_url": None, "enabled": True})
    assert put.status_code == 200, put.text
    assert put.json()["api_key_masked"] == "********1234"
    assert put.json()["enabled"] is True
    assert "sk-ant-abcdefgh1234" not in put.text  # the real key never appears on the wire back out

    get = client.get("/advisor/settings")
    assert get.json()["api_key_masked"] == "********1234"


def test_settings_put_with_blank_api_key_leaves_the_stored_key_unchanged(client):
    first = client.put("/advisor/settings", json={"api_key": "sk-ant-original1234", "enabled": True})
    assert first.json()["api_key_masked"] == "********1234"

    second = client.put(
        "/advisor/settings", json={"api_key": "", "base_url": "https://new.example.test", "enabled": True}
    )
    assert second.json()["api_key_masked"] == "********1234"  # unchanged
    assert second.json()["base_url"] == "https://new.example.test"  # this field DID update

    third = client.put("/advisor/settings", json={"enabled": False})  # api_key omitted entirely
    assert third.json()["api_key_masked"] == "********1234"
    assert third.json()["enabled"] is False


def test_settings_put_new_key_overwrites(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-firstkey1111", "enabled": True})
    second = client.put("/advisor/settings", json={"api_key": "sk-ant-secondkey2222", "enabled": True})
    assert second.json()["api_key_masked"] == "********2222"


def test_settings_put_enabled_false_round_trips(client):
    # The exact round trip the desktop smoke test drives (no live API call).
    resp = client.put("/advisor/settings", json={"enabled": False})
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"api_key_masked": None, "base_url": None, "enabled": False}
    get = client.get("/advisor/settings")
    assert get.json()["enabled"] is False


def test_settings_put_requires_enabled(client):
    resp = client.put("/advisor/settings", json={"api_key": "sk-ant-x"})
    assert resp.status_code == 422


def test_settings_file_lands_beside_projects_not_inside_one(client, tmp_path):
    client.post(
        "/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"}
    )
    client.put("/advisor/settings", json={"api_key": "sk-ant-x", "enabled": True})
    root = tmp_path / "projects"
    assert (root / "settings.json").exists()
    assert not (root / "proj-1" / "settings.json").exists()


# ---- /advisor/ask: unavailable / rejected paths (no HTTP call should ever happen) ----


def test_ask_with_no_key_is_a_clean_409_not_a_500(client):
    resp = client.post("/advisor/ask", json={"project_id": "whatever", "mode": "generic", "question": "hi"})
    assert resp.status_code == 409
    assert resp.status_code != 500
    assert "API key" in resp.json()["detail"]


def test_ask_when_disabled_is_a_clean_409(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": False})
    resp = client.post("/advisor/ask", json={"project_id": "whatever", "mode": "generic"})
    assert resp.status_code == 409


def test_ask_rejects_an_unsupported_mode_with_422(client):
    # "tollgate" itself is a real mode as of M5 unit 2 -- a genuinely
    # nonexistent mode name is the fixture for "unsupported mode" now
    # (this test's own invariant, unchanged); tollgate's *own* schema
    # requirement (needs `phase`) gets its own test right below.
    resp = client.post("/advisor/ask", json={"project_id": "whatever", "mode": "not-a-real-mode"})
    assert resp.status_code == 422


def test_ask_tollgate_without_phase_is_422(client):
    resp = client.post("/advisor/ask", json={"project_id": "whatever", "mode": "tollgate"})
    assert resp.status_code == 422


def test_ask_missing_project_is_404_once_configured(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    resp = client.post("/advisor/ask", json={"project_id": "no-such-project", "mode": "generic"})
    assert resp.status_code == 404


# ---- /advisor/ask: the real wire call, mocked only at the HTTP transport
# boundary (respx) -- routes/advisor.py and client.py run unmodified. ----


@respx.mock
def test_ask_wire_call_carries_the_assembled_blocks_in_the_right_roles(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("here is my answer"))

    resp = client.post(
        "/advisor/ask",
        json={"project_id": "proj-1", "mode": "generic", "artifact_id": "copq-001", "question": "How does this look?"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == "here is my answer"
    assert body["budget_report"]["dropped"] == []
    assert body["truncated"] is False  # an ordinary end_turn completion (Fix 4, M5 exit critic)

    assert route.call_count == 1
    wire_body = json.loads(route.calls[0].request.content)
    assert wire_body["model"] == "claude-sonnet-5"

    # System role: the frame only -- injection-defense instructions present.
    assert 'trust="untrusted"' in wire_body["system"]
    assert "never calculate" in wire_body["system"].lower()

    # User role: exactly one message, carrying facts/pre-score/artifacts/question.
    assert len(wire_body["messages"]) == 1
    user_msg = wire_body["messages"][0]
    assert user_msg["role"] == "user"
    content = user_msg["content"]
    assert "FACTS" in content
    assert "PRE-SCORE" in content
    assert 'id="copq-001"' in content
    assert 'id="user_question"' in content
    assert "How does this look?" in content

    # The key travels as a header, never inside the JSON body.
    assert "sk-ant-real1234" not in json.dumps(wire_body)


@respx.mock
def test_ask_surfaces_requested_artifact_ids_parsed_from_the_answer(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    _create_project_and_copq(client)

    answer_text = f"I can partly answer.\n{REQUEST_ARTIFACT_PREFIX} copq-001\nMore prose after the marker."
    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(answer_text))

    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "generic"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["requested_artifact_ids"] == ["copq-001"]
    assert resp.json()["answer"] == answer_text


@respx.mock
def test_ask_follow_up_artifact_request_is_threaded_through_to_the_assembler(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("ok"))
    resp = client.post(
        "/advisor/ask",
        json={"project_id": "proj-1", "mode": "generic", "follow_up_artifact_request": "copq-001"},
    )
    assert resp.status_code == 200, resp.text
    wire_body = json.loads(route.calls[0].request.content)
    assert "FULL content of artifact copq-001" in wire_body["messages"][0]["content"]


@respx.mock
def test_ask_maps_a_failed_upstream_call_to_502_not_500(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    _create_project_and_copq(client)

    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=httpx.Response(
            401, json={"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}}
        )
    )

    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "generic"})
    assert resp.status_code == 502
    assert resp.status_code != 500
    assert "sk-ant-real1234" not in resp.text


@respx.mock
def test_ask_with_no_question_still_produces_a_sensible_prompt(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": True})
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("a general read"))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "generic", "artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text
    wire_body = json.loads(route.calls[0].request.content)
    assert "no question asked" in wire_body["messages"][0]["content"]


# ---- Truncation (M5 exit critic, Fix 4): stop_reason == "max_tokens" is
# its own honest outcome, surfaced as `truncated`, never conflated with the
# "model returned unstructured output" message -- and, for a structured
# mode, never spends the one retry on a call that would truncate the same
# way again. ----


@respx.mock
def test_ask_prose_mode_surfaces_truncated_honestly(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_trunc", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
                "content": [{"type": "text", "text": "Cpk is quite low, here's why the process is"}],
                "stop_reason": "max_tokens", "stop_sequence": None,
                "usage": {"input_tokens": 5, "output_tokens": 4096},
            },
        )
    )
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "generic", "artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["truncated"] is True
    assert body["unstructured_fallback"] is False  # a distinct, honest outcome -- never conflated
    assert body["answer"] == "Cpk is quite low, here's why the process is"
    assert route.call_count == 1


@respx.mock
def test_ask_structured_mode_truncated_on_first_call_makes_no_retry(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_trunc", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
                "content": [{"type": "text", "text": '```json\n{"criteria": [{"criterion_id": "R-DEF-05"'}],
                "stop_reason": "max_tokens", "stop_sequence": None,
                "usage": {"input_tokens": 5, "output_tokens": 4096},
            },
        )
    )
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "review", "artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["truncated"] is True
    assert body["structured"] is None
    assert body["unstructured_fallback"] is False
    assert route.call_count == 1  # no retry spent on a call that would truncate the same way again


# ---- The live question's length cap and budget accounting (M5 exit
# critic, Fix 6): it used to be composed OUTSIDE assemble_context, so the
# budget never counted it and nothing capped its length. ----


def test_ask_oversized_question_is_422(client):
    _fully_configure(client)
    resp = client.post(
        "/advisor/ask",
        json={"project_id": "whatever", "mode": "generic", "question": "x" * (MAX_QUESTION_LENGTH + 1)},
    )
    assert resp.status_code == 422


def test_ask_oversized_focus_ref_is_422(client):
    _fully_configure(client)
    resp = client.post(
        "/advisor/ask",
        json={
            "project_id": "whatever", "mode": "explain",
            "focus": {"kind": "free_text", "ref": "x" * (MAX_QUESTION_LENGTH + 1)},
        },
    )
    assert resp.status_code == 422


@respx.mock
def test_ask_budget_report_reflects_the_questions_tokens(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("ok"))
    resp = client.post(
        "/advisor/ask",
        json={"project_id": "proj-1", "mode": "generic", "artifact_id": "copq-001", "question": "How does this look?"},
    )
    assert resp.status_code == 200, resp.text
    assert "question_block" in resp.json()["budget_report"]["included"]


# ---- The five modes (M5 unit 2): one structured happy path + one
# malformed->retry->fallback per structured mode, plus explain's prose-only
# path and tollgate/remedy's context shape on the wire. ----

_REVIEW_JSON = (
    '```json\n{"criteria": [{"criterion_id": "R-DEF-05", "verdict": "pass", "specific_fix": ""}], '
    '"overall_note": "Looks solid."}\n```'
)
_HELP_ME_THINK_JSON = (
    '```json\n{"proposals": [{"text": "Fixture drifts out of alignment overnight", '
    '"evidence_question": "What does a shift-start alignment check show over two weeks?"}]}\n```'
)
_TOLLGATE_JSON = (
    '```json\n{"recommendation": "go_with_actions", "reasons": ["Charter is thin but present"], '
    '"actions": [{"action": "Name a process owner", "tied_to_question_id": "define-2"}]}\n```'
)
_REMEDY_JSON = (
    '```json\n{"remedies": [{"title": "Add a pre-shift alignment checklist", '
    '"why_it_fits_the_verified_cause": "Directly targets cause c-1 (fixture alignment not checked).", '
    '"cause_ids": ["c-1"], "estimated_cost_band": "low", "risks": "Operators may skip it under time pressure", '
    '"pilot_first": "One line, two weeks", "how_youd_know_it_worked": "Scrap rate on that line drops"}]}\n```'
)


@respx.mock
def test_ask_review_mode_structured_happy_path(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(_REVIEW_JSON))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "review", "artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == "review"
    assert body["unstructured_fallback"] is False
    assert body["structured"]["criteria"][0]["criterion_id"] == "R-DEF-05"
    assert body["structured"]["criteria"][0]["verdict"] == "pass"
    assert route.call_count == 1

    wire_body = json.loads(route.calls[0].request.content)
    assert "R-DEF-05" in wire_body["messages"][0]["content"]
    assert "MODE CONTEXT" in wire_body["messages"][0]["content"]


@respx.mock
def test_ask_review_mode_malformed_response_retries_once_then_falls_back(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        side_effect=[_canned_message("not json, sorry"), _canned_message("still not json")]
    )
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "review", "artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text  # never a 500, per PLAN §5.1 mode 1
    body = resp.json()
    assert body["unstructured_fallback"] is True
    assert body["structured"] is None
    assert body["answer"] == "still not json"
    assert route.call_count == 2


@respx.mock
def test_ask_help_me_think_mode_structured_happy_path(client):
    _fully_configure(client)
    _create_project_and_fishbone(client)

    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(_HELP_ME_THINK_JSON))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "help_me_think", "artifact_id": "fishbone-001"})
    assert resp.status_code == 200, resp.text
    proposals = resp.json()["structured"]["proposals"]
    assert proposals[0]["evidence_question"]


@respx.mock
def test_ask_explain_mode_is_prose_only_with_focus_folded_into_the_question(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("Cpk of 0.7 means..."))
    resp = client.post(
        "/advisor/ask",
        json={
            "project_id": "proj-1", "mode": "explain", "artifact_id": "copq-001",
            "focus": {"kind": "computed_field", "ref": "total"},
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == "Cpk of 0.7 means..."
    assert body["structured"] is None
    assert body["unstructured_fallback"] is False

    wire_body = json.loads(route.calls[0].request.content)
    content = wire_body["messages"][0]["content"]
    assert 'id="user_question"' in content
    assert "computed_field" in content
    assert "total" in content


@respx.mock
def test_ask_tollgate_mode_structured_happy_path_and_context_shape(client):
    _fully_configure(client)
    resp = client.post(
        "/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"}
    )
    assert resp.status_code == 200, resp.text

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(_TOLLGATE_JSON))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "tollgate", "phase": "Define"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["structured"]["recommendation"] == "go_with_actions"
    assert body["structured"]["actions"][0]["tied_to_question_id"] == "define-2"

    wire_body = json.loads(route.calls[0].request.content)
    content = wire_body["messages"][0]["content"]
    assert "define-1" in content and "define-2" in content and "define-3" in content  # a3.py's real question ids
    assert "Tollgate review for phase: Define" in content


@respx.mock
def test_ask_remedy_mode_structured_happy_path(client):
    _fully_configure(client)
    _create_project_and_fishbone(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(_REMEDY_JSON))
    resp = client.post(
        "/advisor/ask", json={"project_id": "proj-1", "mode": "remedy", "question": "Budget is under $500."}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    remedy = body["structured"]["remedies"][0]
    assert remedy["cause_ids"] == ["c-1"]
    assert remedy["estimated_cost_band"] == "low"
    # Fix 5 (M5 exit critic): c-1 is "verified" in factories.make_fishbone()
    # -- a remedy citing only a genuinely verified cause passes clean.
    assert remedy["unverified_cause_refs"] == []
    assert body["structured"]["unverified_cause_note"] == ""

    wire_body = json.loads(route.calls[0].request.content)
    content = wire_body["messages"][0]["content"]
    assert "Budget is under $500." in content
    assert 'id="user_question"' in content  # the constraints text is untrusted-wrapped like any other question
    assert "FULL content of artifact fishbone-001" in content


@respx.mock
def test_ask_remedy_mode_flags_remedies_citing_unverified_or_invented_causes(client):
    # M5 exit critic, Fix 5: modes.py's cause_ids validation is deterministic
    # and runs AFTER parsing, never trusting the model's own addendum
    # compliance. factories.make_fishbone_causes(): c-1 is "verified", c-2
    # is only "candidate" -- and c-999 does not exist on this fishbone at
    # all. All three must be kept (never silently dropped) but only the
    # verified one passes clean.
    _fully_configure(client)
    _create_project_and_fishbone(client)

    remedy_json = (
        '```json\n{"remedies": ['
        '{"title": "Post the checklist at the fixture station", '
        '"why_it_fits_the_verified_cause": "Targets verified cause c-1.", '
        '"cause_ids": ["c-1"], "estimated_cost_band": "low", "risks": "", "pilot_first": "", '
        '"how_youd_know_it_worked": ""}, '
        '{"title": "Recalibrate injector pressure sensor", '
        '"why_it_fits_the_verified_cause": "Targets cause c-2, still only a candidate.", '
        '"cause_ids": ["c-2"], "estimated_cost_band": "medium", "risks": "", "pilot_first": "", '
        '"how_youd_know_it_worked": ""}, '
        '{"title": "A remedy for a cause that does not exist", '
        '"why_it_fits_the_verified_cause": "Targets cause c-999.", '
        '"cause_ids": ["c-999"], "estimated_cost_band": "high", "risks": "", "pilot_first": "", '
        '"how_youd_know_it_worked": ""}'
        ']}\n```'
    )
    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(remedy_json))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "remedy"})
    assert resp.status_code == 200, resp.text
    structured = resp.json()["structured"]
    remedies = structured["remedies"]
    assert len(remedies) == 3  # nothing dropped -- flagged, not hidden
    assert remedies[0]["unverified_cause_refs"] == []  # c-1: verified, clean
    assert remedies[1]["unverified_cause_refs"] == ["c-2"]  # c-2: real cause, still only a candidate
    assert remedies[2]["unverified_cause_refs"] == ["c-999"]  # invented outright
    assert structured["unverified_cause_note"] != ""


@respx.mock
def test_ask_remedy_mode_with_no_fishbone_is_honest_not_a_500(client):
    _fully_configure(client)
    client.post(
        "/project/create", json={"project_id": "proj-1", "name": "Coffee Bar", "created_at": "2026-08-07T00:00:00"}
    )
    empty_remedies_json = "```json\n" + json.dumps({"remedies": []}) + "\n```"
    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(empty_remedies_json))
    resp = client.post("/advisor/ask", json={"project_id": "proj-1", "mode": "remedy"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["structured"]["remedies"] == []


# ---- POST /advisor/validate (M5 unit 3, PLAN §5.3.6): same unavailable/404
# contract as /advisor/ask, reused via the same _require_configured -- these
# only add what's specific to this route (its own request shape, and that a
# save is never triggered). validator.py's own module-level tests
# (test_advisor_validator.py) cover context assembly, the retry/fallback
# contract, the disclaimer, and injection defense in depth. ----


def test_validate_with_no_key_is_a_clean_409_not_a_500(client):
    resp = client.post("/advisor/validate", json={"project_id": "whatever", "tool_id": "T-02", "body": {}})
    assert resp.status_code == 409
    assert resp.status_code != 500
    assert "API key" in resp.json()["detail"]


def test_validate_when_disabled_is_a_clean_409(client):
    client.put("/advisor/settings", json={"api_key": "sk-ant-real1234", "enabled": False})
    resp = client.post("/advisor/validate", json={"project_id": "whatever", "tool_id": "T-02", "body": {}})
    assert resp.status_code == 409


def test_validate_missing_fields_is_422(client):
    _fully_configure(client)
    assert client.post("/advisor/validate", json={"tool_id": "T-02", "body": {}}).status_code == 422
    assert client.post("/advisor/validate", json={"project_id": "proj-1", "body": {}}).status_code == 422
    # `body` itself is optional (defaults to {}) -- omitting it is not
    # malformed, only the wrong TYPE for it is.
    assert client.post("/advisor/validate", json={"project_id": "proj-1", "tool_id": "T-02", "body": "not-a-dict"}).status_code == 422


def test_validate_missing_project_is_404_once_configured(client):
    _fully_configure(client)
    resp = client.post(
        "/advisor/validate", json={"project_id": "no-such-project", "tool_id": "T-02", "body": make_copq()}
    )
    assert resp.status_code == 404


def test_validate_unknown_tool_id_is_404_once_configured(client):
    _fully_configure(client)
    _create_project_and_copq(client)
    resp = client.post("/advisor/validate", json={"project_id": "proj-1", "tool_id": "T-99", "body": {}})
    assert resp.status_code == 404
    assert "T-99" in resp.json()["detail"]


@respx.mock
def test_validate_oversized_draft_is_a_distinct_422_with_no_model_call(client):
    # M5 exit critic, Fix 8: a draft too large to fit alongside the
    # (never-trimmed) system prompt fails honestly, before ever calling the
    # model -- distinct from AdvisorValidateRequest's own schema-shape 422s
    # above (this request is perfectly well-formed; the draft itself just
    # doesn't fit in any amount of budget).
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message("unused"))
    huge_notes = "x" * 200_000  # ~50k estimated tokens, comfortably past the 30k default budget alone
    resp = client.post(
        "/advisor/validate",
        json={"project_id": "proj-1", "tool_id": "T-02", "body": make_copq(notes=huge_notes)},
    )
    assert resp.status_code == 422
    assert resp.status_code != 500
    assert "too large to check" in resp.json()["detail"]
    assert route.call_count == 0  # never even attempted


@respx.mock
def test_validate_wire_call_happy_path_and_response_shape(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    flag_json = (
        '```json\n{"flags": [{"field_path": "notes", "claim_text": "Scrap is the worst it has ever been.", '
        '"why_flagged": "No historical baseline is given anywhere to compare against.", '
        '"severity": "cant_trace"}], "checked_field_count": 2}\n```'
    )
    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(flag_json))

    resp = client.post(
        "/advisor/validate",
        json={"project_id": "proj-1", "tool_id": "T-02", "body": make_copq(notes="Scrap is the worst it has ever been.")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["checked_field_count"] == 2
    assert len(body["flags"]) == 1
    assert body["flags"][0]["severity"] == "cant_trace"
    assert body["unstructured_fallback"] is False
    # The fixed disclaimer is a real response field, present on every call.
    assert "not a guarantee" in body["disclaimer"]
    assert "layers 1-5" in body["disclaimer"]
    # Fix 8 (M5 exit critic): budget_report is always present, same shape
    # AdvisorAskResponse's own budget reporting uses; nothing needed
    # trimming for a request this small.
    assert body["budget_report"]["dropped"] == []
    assert body["budget_report"]["estimated_input_tokens"] > 0

    assert route.call_count == 1
    wire_body = json.loads(route.calls[0].request.content)
    assert wire_body["model"] == "claude-haiku-4-5-20251001"  # the cheap tier, not the advisor's main model
    assert "sk-ant-real1234" not in json.dumps(wire_body)


@respx.mock
def test_validate_malformed_body_never_blocks_a_response_never_a_500(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    route = respx.post(ANTHROPIC_MESSAGES_URL).mock(
        side_effect=[_canned_message("not json"), _canned_message("still not json")]
    )
    resp = client.post("/advisor/validate", json={"project_id": "proj-1", "tool_id": "T-02", "body": make_copq()})
    assert resp.status_code == 200, resp.text  # never a 500
    body = resp.json()
    assert body["unstructured_fallback"] is True
    assert body["flags"] == []
    assert "not a guarantee" in body["disclaimer"]
    assert route.call_count == 2


@respx.mock
def test_validate_maps_a_failed_upstream_call_to_502_not_500(client):
    _fully_configure(client)
    _create_project_and_copq(client)

    respx.post(ANTHROPIC_MESSAGES_URL).mock(
        return_value=httpx.Response(
            401, json={"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}}
        )
    )
    resp = client.post("/advisor/validate", json={"project_id": "proj-1", "tool_id": "T-02", "body": make_copq()})
    assert resp.status_code == 502
    assert resp.status_code != 500
    assert "sk-ant-real1234" not in resp.text


@respx.mock
def test_validate_never_creates_or_changes_a_saved_artifact(client):
    _fully_configure(client)
    _create_project_and_copq(client)
    before = client.get("/project/proj-1/info").json()["artifact_index"]

    empty_flags_json = '```json\n{"flags": [], "checked_field_count": 1}\n```'
    respx.post(ANTHROPIC_MESSAGES_URL).mock(return_value=_canned_message(empty_flags_json))
    resp = client.post(
        "/advisor/validate",
        json={"project_id": "proj-1", "tool_id": "T-02", "body": make_copq(notes="A claim to check, not to save.")},
    )
    assert resp.status_code == 200, resp.text

    after = client.get("/project/proj-1/info").json()["artifact_index"]
    assert after == before  # the validator call saved nothing and changed nothing


# ---- GET /advisor/export/{project_id}/{tool_id} (M5 unit 4, PLAN §5.2) ----
# The paste-ready chatbot export. Every test here runs with NO key
# configured (the client fixture clears the env and nothing calls
# _fully_configure) -- proving the route's whole point: it works with
# Layer 2 entirely unconfigured, because the pack exists for exactly the
# users who have no key.

from sigma_engine.advisor.prompt_pack import FIXED_FOOTER, TOOL_PROMPT_FILES, TOLLGATE_PROMPT_FILES  # noqa: E402


def test_export_tool_combines_prompt_artifact_json_and_facts(client):
    _create_project_and_copq(client)
    resp = client.get("/advisor/export/proj-1/T-02", params={"artifact_id": "copq-001"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["prompt_text"] == TOOL_PROMPT_FILES["T-02"][1]
    assert '"artifact_id": "copq-001"' in body["artifact_json"]
    # The COPQ total is a Computed[T] leaf -- engine-computed facts present.
    assert "total" in body["facts_block"]

    combined = body["combined"]
    assert combined.index(body["prompt_text"].rstrip("\n")) == 0
    assert "MY ARTIFACT:" in combined
    assert combined.index("MY ARTIFACT:") < combined.index("COMPUTED RESULTS (authoritative, from the app):")
    assert '"artifact_id": "copq-001"' in combined
    assert FIXED_FOOTER in combined
    assert "the app's computed results are the record" in combined


def test_export_tool_without_artifact_id_still_ships_the_prompt(client):
    _create_project_and_copq(client)
    resp = client.get("/advisor/export/proj-1/T-13")  # T-13 never has a saved artifact
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["artifact_json"] == ""
    assert body["facts_block"] == ""
    assert body["prompt_text"] == TOOL_PROMPT_FILES["T-13"][1]
    assert "no saved artifact in the app for this tool" in body["combined"]


def test_export_404s_for_unknown_project_tool_and_artifact(client):
    _create_project_and_copq(client)
    assert client.get("/advisor/export/nope/T-02").status_code == 404
    assert client.get("/advisor/export/proj-1/T-99").status_code == 404
    assert client.get("/advisor/export/proj-1/T-02", params={"artifact_id": "ghost"}).status_code == 404


def test_export_409s_when_the_artifact_belongs_to_a_different_tool(client):
    _create_project_and_copq(client)
    resp = client.get("/advisor/export/proj-1/T-03", params={"artifact_id": "copq-001"})
    assert resp.status_code == 409
    assert "belongs to tool T-02" in resp.json()["detail"]


def test_export_tollgate_combines_phase_prompt_summaries_and_facts(client):
    _create_project_and_fishbone(client)
    resp = client.get("/advisor/export/proj-1/T-15", params={"mode": "tollgate", "phase": "Analyze"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["prompt_text"] == TOLLGATE_PROMPT_FILES["Analyze"][1]
    assert "analyze-1" in body["prompt_text"]
    # The phase summaries block reuses summarize_artifact -- the saved T-15
    # appears by id in the summaries slot.
    assert "fishbone-001" in body["artifact_json"]
    combined = body["combined"]
    assert "MY PHASE ARTIFACTS (summaries from the app):" in combined
    assert "fishbone-001" in combined
    assert FIXED_FOOTER in combined


def test_export_tollgate_with_empty_phase_says_so_honestly(client):
    _create_project_and_fishbone(client)  # nothing saved in Improve
    resp = client.get("/advisor/export/proj-1/T-15", params={"mode": "tollgate", "phase": "Improve"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["artifact_json"] == ""
    assert "no artifacts saved for this phase yet" in body["combined"]


def test_export_tollgate_requires_phase(client):
    _create_project_and_copq(client)
    assert client.get("/advisor/export/proj-1/T-02", params={"mode": "tollgate"}).status_code == 422
    # An invalid phase name fails the TollgatePhase Literal's own validation.
    assert client.get("/advisor/export/proj-1/T-02", params={"mode": "tollgate", "phase": "Sprint"}).status_code == 422
