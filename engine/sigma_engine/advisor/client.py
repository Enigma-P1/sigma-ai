"""Thin wrapper over the official `anthropic` Python SDK (M5 brief: "a thin
wrapper," not a reimplementation). This is the only module in the engine
that imports `anthropic` or ever holds a real API key in memory.

No key configured is a first-class typed result (AdvisorUnavailable), never
an exception: PLAN §5.1 is explicit that Layer 2 is optional and Layer 1
must be completely unaffected, so a missing/disabled advisor can never
surface as an uncaught exception (or a 500) anywhere above this module --
routes/advisor.py turns AdvisorUnavailable into a clean 4xx response
instead.

Key/base-URL resolution order (M5 brief): the app's own settings.json
first (advisor/settings_store.py), then the SDK's own native environment
variables (ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL). Both are resolved
explicitly here rather than left to the SDK's own env-reading, because
resolve_config() has to decide configured-vs-not *before* any SDK client
object exists -- the AdvisorUnavailable branch never touches `anthropic`.

Thinking (M5 exit critic, severity 5-in-order/adjacent-code finding):
claude-sonnet-5 runs ADAPTIVE thinking the moment the `thinking` param is
omitted -- unlike the Opus-4.x models this codebase was first built
against, omitting it is not "no thinking." Adaptive thinking is billed
INSIDE max_tokens (DEFAULT_MAX_OUTPUT_TOKENS, 4096), so a thinking-heavy
turn could silently truncate the JSON the advisor's structured modes need,
and the caller would only ever see "the model returned unstructured
output" -- true in the narrow sense, dishonest about the actual cause.
ask() now sends `thinking={"type": "disabled"}` on every call: the
advisor's job here is judgment on top of what the engine already computed
(context.py's own system-frame text), not multi-step reasoning, so
disabling thinking costs nothing the product needs and buys back the
whole 4096-token budget for the answer. (claude-sonnet-5 accepts
`{"type": "disabled"}` unconditionally -- unlike claude-opus-5, it isn't
gated to effort <= "high" -- so no effort parameter is needed alongside
it; reverify against the installed anthropic SDK's thinking-config types
if the configured model ever changes.) stop_reason is read off every
response and carried through AdvisorAnswer so callers (structured.py,
routes/advisor.py) can tell a genuine truncation apart from every other
outcome instead of only inferring it from a parse failure.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

import anthropic
import httpx
from pydantic import BaseModel

from .settings_store import AdvisorSettings

# The SDK's own native env vars (anthropic.Anthropic()'s documented
# fallback) -- read explicitly here, not left implicit; see module
# docstring for why.
ANTHROPIC_API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
ANTHROPIC_BASE_URL_ENV_VAR = "ANTHROPIC_BASE_URL"

# NOT an SDK-native env var -- this engine's own override switch (M5
# brief: "a settings override exists but don't build a model picker UI").
# No route reads or writes this; an operator sets it in the environment.
ADVISOR_MODEL_ENV_VAR = "SIGMA_ADVISOR_MODEL"
DEFAULT_MODEL = "claude-sonnet-5"

# ~4k out (PLAN §5.1's provisional context budget). Unlike the chars/4
# input estimate (context.py), this is an exact cap the real API enforces
# server-side.
DEFAULT_MAX_OUTPUT_TOKENS = 4096

AdvisorUnavailableReason = Literal["disabled", "no_api_key"]


class AdvisorUnavailable(BaseModel):
    """The typed "Layer 2 isn't usable right now" result (M5 brief) --
    every caller checks for this instead of catching an exception. Never
    carries the key or any fragment of it."""

    reason: AdvisorUnavailableReason
    detail: str


@dataclass(frozen=True)
class AdvisorConfigured:
    """Resolved, ready-to-call advisor configuration. Deliberately a plain
    dataclass, not a pydantic BaseModel: this is the one place in the
    engine that holds a real API key in memory, and a bare dataclass can't
    be handed to FastAPI as a `response_model` by accident the way a
    BaseModel could be -- routes/advisor.py has no way to leak this even
    by a careless return-type mistake. `repr=False` on api_key additionally
    keeps it out of any stray debug repr/log line."""

    api_key: str = field(repr=False)
    base_url: str | None
    model: str


def resolve_model() -> str:
    return os.environ.get(ADVISOR_MODEL_ENV_VAR) or DEFAULT_MODEL


def resolve_config(settings: AdvisorSettings) -> AdvisorConfigured | AdvisorUnavailable:
    """Settings first, env vars second (module docstring). Re-checked on
    every call -- nothing cached -- so a key added to settings.json or the
    environment takes effect on the very next request with no restart."""
    if not settings.enabled:
        return AdvisorUnavailable(
            reason="disabled",
            detail="The advisor is turned off in Advisor settings. Turn it on there to use it.",
        )

    api_key = settings.api_key or os.environ.get(ANTHROPIC_API_KEY_ENV_VAR)
    if not api_key:
        return AdvisorUnavailable(
            reason="no_api_key",
            detail=(
                "No Anthropic API key is configured. Layer 1 (all tools, math, charts) works fully without one -- "
                "add a key in Advisor settings to turn on Layer 2 advice."
            ),
        )

    base_url = settings.base_url or os.environ.get(ANTHROPIC_BASE_URL_ENV_VAR)
    return AdvisorConfigured(api_key=api_key, base_url=base_url, model=resolve_model())


class AdvisorAnswer(BaseModel):
    text: str
    # The raw Messages API stop_reason ("end_turn", "max_tokens", ...) --
    # None only in the defensive case the SDK's own typing allows
    # (Message.stop_reason: Optional[StopReason]); a real completed call
    # always sets one. Callers check this for "max_tokens" (a genuine
    # truncation) rather than inferring it from a downstream parse failure
    # (M5 exit critic finding -- see module docstring).
    stop_reason: str | None = None


class AdvisorCallFailed(Exception):
    """Raised when a *configured* client's actual call to the Anthropic API
    fails (bad key rejected server-side, network error, rate limit, ...).
    Deliberately distinct from AdvisorUnavailable -- that type means "never
    even tried," this means "tried, and the API/network said no." str(exc)
    on the wrapped anthropic.AnthropicError is safe to surface to the
    route/UI layer: the SDK's own error bodies carry the API's status and
    message, never the request's Authorization/x-api-key header (verified
    against the real SDK while building this module -- see the build
    report)."""


def build_client(config: AdvisorConfigured, *, http_client: httpx.Client | None = None) -> anthropic.Anthropic:
    """The one call site in this engine that constructs an
    `anthropic.Anthropic`. `http_client` is test-only plumbing (a
    MockTransport-backed httpx.Client, PLAN §5.1's verification step) --
    production callers never pass it, so the SDK builds its own real
    transport. `base_url=None` is the SDK's own default (its documented
    production endpoint), not a broken call."""
    return anthropic.Anthropic(api_key=config.api_key, base_url=config.base_url, http_client=http_client)


def ask(
    config: AdvisorConfigured,
    *,
    system: str,
    user_content: str,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    http_client: httpx.Client | None = None,
) -> AdvisorAnswer:
    """One non-streaming Messages call. `system` and `user_content` are
    carried onto the wire exactly as given -- this function does no prompt
    assembly of its own (that is context.py's and routes/advisor.py's job);
    it only places the two roles correctly (M5 brief: "the wire call
    carries the assembled blocks in the right roles, system vs user")."""
    client = build_client(config, http_client=http_client)
    try:
        message = client.messages.create(
            model=config.model,
            max_tokens=max_output_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
            # Disabled, not omitted -- see module docstring. On
            # claude-sonnet-5, omitting this parameter runs ADAPTIVE
            # thinking billed inside max_output_tokens, which can truncate
            # a structured mode's JSON with no honest signal why.
            thinking={"type": "disabled"},
        )
    except anthropic.AnthropicError as exc:
        # Never log/echo the key (M5 brief) -- str(exc) is safe here, see
        # AdvisorCallFailed's docstring.
        raise AdvisorCallFailed(str(exc)) from exc

    text = "".join(block.text for block in message.content if block.type == "text")
    return AdvisorAnswer(text=text, stop_reason=message.stop_reason)
