"""client.py: config resolution (settings vs env, disabled vs no-key) and
the wire call, using httpx.MockTransport (M5 brief: "mock the SDK
transport ... use respx or a stub transport") -- no real network call ever
happens in this file."""

from __future__ import annotations

import json

import anthropic
import httpx
import pytest

from sigma_engine.advisor.client import (
    ADVISOR_MODEL_ENV_VAR,
    ANTHROPIC_API_KEY_ENV_VAR,
    ANTHROPIC_BASE_URL_ENV_VAR,
    DEFAULT_MODEL,
    AdvisorCallFailed,
    AdvisorConfigured,
    AdvisorUnavailable,
    ask,
    resolve_config,
    resolve_model,
)
from sigma_engine.advisor.settings_store import AdvisorSettings


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _canned_response(text: str = "hello from the advisor") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": "claude-sonnet-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    )


# ---- resolve_config ----


def test_disabled_settings_are_unavailable_even_with_a_key(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV_VAR, raising=False)
    result = resolve_config(AdvisorSettings(api_key="sk-ant-real", enabled=False))
    assert isinstance(result, AdvisorUnavailable)
    assert result.reason == "disabled"


def test_no_key_anywhere_is_unavailable(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV_VAR, raising=False)
    result = resolve_config(AdvisorSettings(api_key=None, enabled=True))
    assert isinstance(result, AdvisorUnavailable)
    assert result.reason == "no_api_key"
    # Never an exception, and the message never contains the word "Traceback".
    assert "Traceback" not in result.detail


def test_unavailable_result_never_carries_any_key_fragment(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV_VAR, raising=False)
    result = resolve_config(AdvisorSettings(api_key=None, enabled=True))
    assert isinstance(result, AdvisorUnavailable)
    assert "sk-ant" not in result.detail  # the messages are static copy, not echoing any key


def test_settings_key_is_used_when_present(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_API_KEY_ENV_VAR, raising=False)
    result = resolve_config(AdvisorSettings(api_key="sk-ant-from-settings", enabled=True))
    assert isinstance(result, AdvisorConfigured)
    assert result.api_key == "sk-ant-from-settings"


def test_env_var_key_is_the_fallback_when_settings_has_none(monkeypatch):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV_VAR, "sk-ant-from-env")
    result = resolve_config(AdvisorSettings(api_key=None, enabled=True))
    assert isinstance(result, AdvisorConfigured)
    assert result.api_key == "sk-ant-from-env"


def test_settings_key_takes_priority_over_env_var(monkeypatch):
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV_VAR, "sk-ant-from-env")
    result = resolve_config(AdvisorSettings(api_key="sk-ant-from-settings", enabled=True))
    assert isinstance(result, AdvisorConfigured)
    assert result.api_key == "sk-ant-from-settings"


def test_base_url_resolution_prefers_settings_then_env_then_none(monkeypatch):
    monkeypatch.delenv(ANTHROPIC_BASE_URL_ENV_VAR, raising=False)
    monkeypatch.setenv(ANTHROPIC_API_KEY_ENV_VAR, "sk-ant-x")

    none_case = resolve_config(AdvisorSettings(enabled=True))
    assert isinstance(none_case, AdvisorConfigured)
    assert none_case.base_url is None

    monkeypatch.setenv(ANTHROPIC_BASE_URL_ENV_VAR, "https://env.example.test")
    env_case = resolve_config(AdvisorSettings(enabled=True))
    assert isinstance(env_case, AdvisorConfigured)
    assert env_case.base_url == "https://env.example.test"

    settings_case = resolve_config(AdvisorSettings(enabled=True, base_url="https://settings.example.test"))
    assert isinstance(settings_case, AdvisorConfigured)
    assert settings_case.base_url == "https://settings.example.test"


def test_model_defaults_and_env_override(monkeypatch):
    monkeypatch.delenv(ADVISOR_MODEL_ENV_VAR, raising=False)
    assert resolve_model() == DEFAULT_MODEL

    monkeypatch.setenv(ADVISOR_MODEL_ENV_VAR, "claude-custom-override")
    assert resolve_model() == "claude-custom-override"


def test_advisor_configured_repr_never_shows_the_real_key():
    config = AdvisorConfigured(api_key="sk-ant-super-secret", base_url=None, model=DEFAULT_MODEL)
    assert "sk-ant-super-secret" not in repr(config)


# ---- ask() / the wire call ----


def test_ask_sends_system_and_user_in_the_right_roles():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
        return _canned_response("the answer")

    config = AdvisorConfigured(api_key="sk-ant-test-key", base_url=None, model="claude-sonnet-5")
    result = ask(config, system="SYSTEM FRAME", user_content="USER TURN CONTENT", http_client=_mock_client(handler))

    assert result.text == "the answer"
    body = captured["body"]
    assert body["system"] == "SYSTEM FRAME"
    assert body["messages"] == [{"role": "user", "content": "USER TURN CONTENT"}]
    assert body["model"] == "claude-sonnet-5"
    # The key travels as a header the SDK sets, never inside the JSON body.
    assert "sk-ant-test-key" not in json.dumps(body)
    assert captured["headers"].get("x-api-key") == "sk-ant-test-key"


def test_ask_caps_max_tokens_at_the_given_output_budget():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return _canned_response()

    config = AdvisorConfigured(api_key="sk-ant-test", base_url=None, model="claude-sonnet-5")
    ask(config, system="s", user_content="u", max_output_tokens=777, http_client=_mock_client(handler))
    assert captured["body"]["max_tokens"] == 777


def test_ask_concatenates_multiple_text_blocks():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "msg_multi", "type": "message", "role": "assistant", "model": "claude-sonnet-5",
                "content": [{"type": "text", "text": "part one. "}, {"type": "text", "text": "part two."}],
                "stop_reason": "end_turn", "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 2},
            },
        )

    config = AdvisorConfigured(api_key="sk-ant-test", base_url=None, model="claude-sonnet-5")
    result = ask(config, system="s", user_content="u", http_client=_mock_client(handler))
    assert result.text == "part one. part two."


def test_ask_raises_advisor_call_failed_on_api_error_without_leaking_the_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}})

    config = AdvisorConfigured(api_key="sk-ant-should-not-leak", base_url=None, model="claude-sonnet-5")
    with pytest.raises(AdvisorCallFailed) as exc_info:
        ask(config, system="s", user_content="u", http_client=_mock_client(handler))
    assert "sk-ant-should-not-leak" not in str(exc_info.value)


def test_ask_raises_advisor_call_failed_on_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    config = AdvisorConfigured(api_key="sk-ant-test", base_url=None, model="claude-sonnet-5")
    with pytest.raises(AdvisorCallFailed):
        ask(config, system="s", user_content="u", http_client=_mock_client(handler))


def test_build_client_uses_configured_base_url():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return _canned_response()

    config = AdvisorConfigured(api_key="sk-ant-test", base_url="https://custom.example.test", model="claude-sonnet-5")
    ask(config, system="s", user_content="u", http_client=_mock_client(handler))
    assert captured["url"].startswith("https://custom.example.test")


def test_anthropic_error_hierarchy_is_what_client_py_assumes():
    # A cheap guard against a future SDK upgrade silently renaming/removing
    # the base error class client.py's except clause depends on.
    assert issubclass(anthropic.AuthenticationError, anthropic.AnthropicError)
