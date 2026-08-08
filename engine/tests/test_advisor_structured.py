"""structured.py: the shared fenced-JSON extractor + parse + the
one-retry-then-fallback orchestration (M5 unit 2 brief: "a malformed
response gets ONE retry with the parse error appended, then surfaces as a
plain-text fallback ... never a 500"). httpx.MockTransport via the
`http_client` seam (same idiom as test_advisor_client.py, reused --
structured.py's own docstring) -- no real network call ever happens here.
"""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel, Field

from sigma_engine.advisor.client import AdvisorCallFailed, AdvisorConfigured
from sigma_engine.advisor.structured import (
    StructuredOutputError,
    extract_fenced_json,
    parse_structured,
    run_structured_mode,
)


class _Widget(BaseModel):
    name: str = Field(min_length=1)
    count: int


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _canned_response(text: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    )


_CONFIG = AdvisorConfigured(api_key="sk-ant-test", base_url=None, model="claude-sonnet-5")


# ---- extract_fenced_json / parse_structured ----


def test_extract_fenced_json_parses_the_first_json_block():
    text = 'preamble\n```json\n{"a": 1}\n```\ntrailer'
    assert extract_fenced_json(text) == {"a": 1}


def test_extract_fenced_json_is_case_insensitive_on_the_language_tag():
    text = '```JSON\n{"a": 1}\n```'
    assert extract_fenced_json(text) == {"a": 1}


def test_extract_fenced_json_raises_when_no_fenced_block_present():
    with pytest.raises(StructuredOutputError, match="no ```json"):
        extract_fenced_json("just plain prose, no code fence at all")


def test_extract_fenced_json_raises_on_invalid_json_inside_the_fence():
    with pytest.raises(StructuredOutputError, match="did not parse as JSON"):
        extract_fenced_json("```json\n{not valid json,,,}\n```")


def test_parse_structured_happy_path():
    result = parse_structured('```json\n{"name": "widget", "count": 3}\n```', _Widget)
    assert result == _Widget(name="widget", count=3)


def test_parse_structured_raises_on_schema_mismatch():
    # count is required int -- a string there fails Pydantic validation.
    with pytest.raises(StructuredOutputError, match="did not match the expected schema"):
        parse_structured('```json\n{"name": "widget", "count": "not a number"}\n```', _Widget)


def test_parse_structured_raises_on_missing_required_field():
    with pytest.raises(StructuredOutputError):
        parse_structured('```json\n{"name": "widget"}\n```', _Widget)


# ---- run_structured_mode: happy path / retry / fallback ----


def test_run_structured_mode_happy_path_makes_exactly_one_call():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return _canned_response('```json\n{"name": "widget", "count": 3}\n```')

    outcome = run_structured_mode(
        _CONFIG, system="s", user_content="u", response_model=_Widget, max_output_tokens=100,
        http_client=_mock_client(handler),
    )

    assert len(calls) == 1
    assert outcome.parsed == _Widget(name="widget", count=3)
    assert outcome.raw_text == '```json\n{"name": "widget", "count": 3}\n```'
    assert outcome.unstructured_fallback is False
    assert outcome.retried is False


def test_run_structured_mode_retries_once_on_malformed_then_succeeds():
    responses = ["not json at all, sorry", '```json\n{"name": "fixed", "count": 7}\n```']
    seen_user_contents = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen_user_contents.append(body["messages"][0]["content"])
        return _canned_response(responses[len(seen_user_contents) - 1])

    outcome = run_structured_mode(
        _CONFIG, system="s", user_content="ORIGINAL_TURN_MARKER", response_model=_Widget, max_output_tokens=100,
        http_client=_mock_client(handler),
    )

    assert len(seen_user_contents) == 2
    assert outcome.parsed == _Widget(name="fixed", count=7)
    assert outcome.retried is True
    assert outcome.unstructured_fallback is False

    # The retry's user turn carries the original context + the model's own
    # bad answer + why it failed + the schema again (module docstring).
    retry_turn = seen_user_contents[1]
    assert "ORIGINAL_TURN_MARKER" in retry_turn
    assert "not json at all, sorry" in retry_turn
    assert "WHY IT DID NOT PARSE" in retry_turn
    assert '"count"' in retry_turn  # the JSON schema, generated from the model itself


def test_run_structured_mode_falls_back_after_a_second_malformed_response():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return _canned_response("still not json, even on retry")

    outcome = run_structured_mode(
        _CONFIG, system="s", user_content="u", response_model=_Widget, max_output_tokens=100,
        http_client=_mock_client(handler),
    )

    assert call_count == 2  # exactly one retry, never more (module docstring)
    assert outcome.parsed is None
    assert outcome.unstructured_fallback is True
    assert outcome.retried is True
    assert outcome.raw_text == "still not json, even on retry"


def test_run_structured_mode_never_raises_structured_output_error_itself():
    def handler(request: httpx.Request) -> httpx.Response:
        return _canned_response("garbage forever")

    # No StructuredOutputError should escape -- only a typed fallback
    # result (PLAN §5.1 mode 1: "never a 500").
    outcome = run_structured_mode(
        _CONFIG, system="s", user_content="u", response_model=_Widget, max_output_tokens=100,
        http_client=_mock_client(handler),
    )
    assert outcome.unstructured_fallback is True


def test_run_structured_mode_propagates_advisor_call_failed_uncaught():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"type": "error", "error": {"type": "authentication_error", "message": "bad key"}})

    with pytest.raises(AdvisorCallFailed):
        run_structured_mode(
            _CONFIG, system="s", user_content="u", response_model=_Widget, max_output_tokens=100,
            http_client=_mock_client(handler),
        )


def test_run_structured_mode_ignores_prose_around_the_fenced_block():
    def handler(request: httpx.Request) -> httpx.Response:
        return _canned_response('Here is my analysis:\n\n```json\n{"name": "ok", "count": 1}\n```\n\nHope that helps!')

    outcome = run_structured_mode(
        _CONFIG, system="s", user_content="u", response_model=_Widget, max_output_tokens=100,
        http_client=_mock_client(handler),
    )
    assert outcome.parsed == _Widget(name="ok", count=1)
