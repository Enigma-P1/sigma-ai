"""Structured-output parsing shared by every mode whose output contract is
STRUCTURED (M5 unit 2 brief: "one shared fenced-JSON extractor + per-mode
Pydantic response models; the retry appends the validation error to a
follow-up user turn. All parsing failures are typed responses, never
500s.") -- review, help_me_think, tollgate, remedy. "explain" and
"generic" are prose-only and never call into this module.

Contract, end to end:

1. The mode's addendum (advisor/modes.py) instructs the model to answer
   with exactly one fenced ```json code block matching that mode's
   Pydantic response model.
2. extract_fenced_json() finds and parses that block; parse_structured()
   then validates it against the model. Either step failing raises
   StructuredOutputError -- never an uncaught exception a caller has to
   guess about.
3. run_structured_mode() drives the retry: one client.ask() call, and on
   a StructuredOutputError, exactly ONE more call whose user turn is the
   original turn plus the model's own prior (malformed) answer plus the
   parse error plus a repeat of the required JSON schema (generated from
   the Pydantic model itself, response_model.model_json_schema() -- one
   source of truth, no hand-maintained schema text to drift from the
   real model). A second failure returns unstructured_fallback=True
   rather than raising -- routes/advisor.py turns that into the "model
   returned unstructured output" flag on AdvisorAskResponse, never a 500
   (PLAN §5.1 mode 1's contract, reused by every structured mode here).

AdvisorCallFailed (client.py -- a real API/network failure, as opposed to
a parse failure) is deliberately NOT caught here and propagates through
both attempts unchanged; routes/advisor.py's existing except clause turns
that into the same 502 it always has.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .client import AdvisorConfigured
from .client import ask as client_ask

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)

# The one fenced-block convention every structured-mode addendum instructs
# the model to use: a ```json ... ``` block, first occurrence wins (a
# well-behaved model emits exactly one; if it emits prose before/after the
# block, that prose is simply not part of the parsed result).
_FENCED_JSON_RE = re.compile(r"```json\s*\n(.*?)\n?```", re.DOTALL | re.IGNORECASE)


class StructuredOutputError(Exception):
    """Either no fenced ```json block was found, the block's contents
    didn't parse as JSON, or the parsed JSON didn't validate against the
    mode's response model. str(exc) is always safe to fold into a retry
    prompt or a diagnostic -- it never contains anything beyond the
    model's own answer text and Pydantic's own validation message."""


def extract_fenced_json(text: str) -> object:
    """The first ```json fenced block in `text`, json-parsed. Raises
    StructuredOutputError (never json.JSONDecodeError) so every caller has
    one exception type to catch."""
    match = _FENCED_JSON_RE.search(text)
    if not match:
        raise StructuredOutputError("no ```json fenced code block found in the model's response")
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"the ```json fenced block did not parse as JSON: {exc}") from exc


def parse_structured(text: str, response_model: type[ResponseModelT]) -> ResponseModelT:
    """extract_fenced_json() + Pydantic validation against `response_model`,
    both failure modes folded into one StructuredOutputError."""
    raw = extract_fenced_json(text)
    try:
        return response_model.model_validate(raw)
    except ValidationError as exc:
        raise StructuredOutputError(f"the response JSON did not match the expected schema: {exc}") from exc


@dataclass(frozen=True)
class StructuredOutcome:
    """run_structured_mode's result. `parsed` is None exactly when
    `unstructured_fallback` is True -- routes/advisor.py checks the flag,
    never `parsed is None`, so the two can never accidentally disagree in
    caller code."""

    parsed: BaseModel | None
    raw_text: str  # the LAST attempt's raw answer text -- always present, retried or not
    unstructured_fallback: bool
    retried: bool


def _build_retry_user_content(
    original_user_content: str, previous_answer: str, parse_error: str, response_model: type[BaseModel]
) -> str:
    """The "follow-up user turn" the M5 unit 2 brief specifies: not a
    multi-message conversation (client.ask() stays a single-user-turn call,
    per client.py's own "thin wrapper" contract -- unmodified here) but a
    fresh user turn that carries the original context plus the model's own
    prior answer plus why it didn't parse plus the schema again, generated
    from the Pydantic model itself so it can never drift from what
    parse_structured() actually checks."""
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    return "\n".join([
        original_user_content,
        "",
        "=== YOUR PREVIOUS RESPONSE (this is a retry -- that response did not parse) ===",
        previous_answer,
        "",
        "=== WHY IT DID NOT PARSE ===",
        parse_error,
        "",
        "=== RETRY INSTRUCTIONS ===",
        "Respond again. This time, respond with EXACTLY one fenced ```json code block, containing an object that "
        "validates against this JSON schema, and nothing else malformed around it:",
        schema_json,
    ])


def run_structured_mode(
    config: AdvisorConfigured,
    *,
    system: str,
    user_content: str,
    response_model: type[ResponseModelT],
    max_output_tokens: int,
    http_client: httpx.Client | None = None,
) -> StructuredOutcome:
    """One call, parse, and on failure exactly one retry with the parse
    error appended (module docstring). Never raises StructuredOutputError
    itself -- a second failure comes back as unstructured_fallback=True.
    AdvisorCallFailed (a real API failure, either attempt) propagates
    uncaught, same as client.ask() always does. `http_client` is test-only
    plumbing threaded straight through to both client.ask() calls --
    client.py's own MockTransport test seam (test_advisor_client.py),
    reused here rather than a second one; production callers never pass it."""
    first = client_ask(config, system=system, user_content=user_content, max_output_tokens=max_output_tokens, http_client=http_client)
    try:
        parsed = parse_structured(first.text, response_model)
        return StructuredOutcome(parsed=parsed, raw_text=first.text, unstructured_fallback=False, retried=False)
    except StructuredOutputError as exc:
        retry_user_content = _build_retry_user_content(user_content, first.text, str(exc), response_model)
        second = client_ask(
            config, system=system, user_content=retry_user_content, max_output_tokens=max_output_tokens, http_client=http_client
        )
        try:
            parsed = parse_structured(second.text, response_model)
            return StructuredOutcome(parsed=parsed, raw_text=second.text, unstructured_fallback=False, retried=True)
        except StructuredOutputError:
            return StructuredOutcome(parsed=None, raw_text=second.text, unstructured_fallback=True, retried=True)
