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

Two M5 exit critic findings land in this module:

- Severity 3: _build_retry_user_content spliced the model's own previous
  answer and the Pydantic parse-error text straight into the next user
  turn, OUTSIDE any untrusted region. Both can carry hostile content that
  originated in a project artifact -- a model that echoes injected text
  in a malformed answer, or a validation error whose message quotes the
  bad field's value verbatim (Pydantic's own "input_value=..." framing) --
  and the retry turn is the one place in this codebase that content could
  reach the wire unwrapped, since context.py's own assembly never sees a
  model's answer text. Both pieces now go through wrap_untrusted() (the
  exact same delimiter every other untrusted block in this codebase uses,
  and the system frame's injection-defense instructions already cover it
  generically -- see context.py's _INJECTION_DEFENSE_INSTRUCTIONS).
- Severity 5 (adjacent): a stop_reason of "max_tokens" on the FIRST call
  means the model's JSON was cut off mid-output, not malformed -- retrying
  re-sends the same input under the same output budget and would truncate
  the same way again. run_structured_mode treats this as its own outcome
  (StructuredOutcome.truncated) rather than spending the one retry on a
  call that can't succeed, and rather than folding it into
  unstructured_fallback (a different, honest-but-distinct failure mode --
  see that field's own docstring).
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
from .context import wrap_untrusted

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
    `unstructured_fallback` is True OR `truncated` is True -- routes/
    advisor.py checks those flags, never `parsed is None` on its own, so
    they can never accidentally disagree in caller code. `unstructured_fallback`
    and `truncated` are mutually exclusive: a truncated first/retry
    response is reported as truncated and never even reaches the parser
    (module docstring), so it can't also count as an unstructured-fallback
    parse failure."""

    parsed: BaseModel | None
    raw_text: str  # the LAST attempt's raw answer text -- always present, retried or not
    unstructured_fallback: bool
    retried: bool
    # True when the attempt that produced `raw_text` hit stop_reason ==
    # "max_tokens" -- the model's output was cut off, not malformed. No
    # retry is spent on this outcome (module docstring); False in every
    # other case, including the ordinary unstructured_fallback path.
    truncated: bool = False


def _build_retry_user_content(
    original_user_content: str, previous_answer: str, parse_error: str, response_model: type[BaseModel]
) -> str:
    """The "follow-up user turn" the M5 unit 2 brief specifies: not a
    multi-message conversation (client.ask() stays a single-user-turn call,
    per client.py's own "thin wrapper" contract -- unmodified here) but a
    fresh user turn that carries the original context plus the model's own
    prior answer plus why it didn't parse plus the schema again, generated
    from the Pydantic model itself so it can never drift from what
    parse_structured() actually checks.

    `previous_answer` and `parse_error` are both wrap_untrusted()-wrapped
    (M5 exit critic, severity 3 -- see module docstring): both can carry
    text that originated in a project artifact -- the model's raw answer
    can echo hostile artifact content verbatim, and a Pydantic
    ValidationError's own message quotes the offending value
    ("input_value=..."), which is exactly as untrusted as the field it
    came from. `original_user_content` is NOT re-wrapped here -- it is
    already a fully-assembled turn (context.py's own untrusted blocks
    included) from the first call, unchanged."""
    schema_json = json.dumps(response_model.model_json_schema(), indent=2)
    return "\n".join([
        original_user_content,
        "",
        "=== YOUR PREVIOUS RESPONSE (this is a retry -- that response did not parse) ===",
        wrap_untrusted("previous_model_answer", previous_answer),
        "",
        "=== WHY IT DID NOT PARSE ===",
        wrap_untrusted("parse_error", parse_error),
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
    if first.stop_reason == "max_tokens":
        # Truncated, not malformed -- no retry (module docstring): a retry
        # re-sends this same input under the same output budget and would
        # truncate the same way again.
        return StructuredOutcome(parsed=None, raw_text=first.text, unstructured_fallback=False, retried=False, truncated=True)
    try:
        parsed = parse_structured(first.text, response_model)
        return StructuredOutcome(parsed=parsed, raw_text=first.text, unstructured_fallback=False, retried=False)
    except StructuredOutputError as exc:
        retry_user_content = _build_retry_user_content(user_content, first.text, str(exc), response_model)
        second = client_ask(
            config, system=system, user_content=retry_user_content, max_output_tokens=max_output_tokens, http_client=http_client
        )
        if second.stop_reason == "max_tokens":
            return StructuredOutcome(parsed=None, raw_text=second.text, unstructured_fallback=False, retried=True, truncated=True)
        try:
            parsed = parse_structured(second.text, response_model)
            return StructuredOutcome(parsed=parsed, raw_text=second.text, unstructured_fallback=False, retried=True)
        except StructuredOutputError:
            return StructuredOutcome(parsed=None, raw_text=second.text, unstructured_fallback=True, retried=True)
