"""validator.py: the sixth anti-hallucination layer (PLAN §5.3.6) -- a
second, CHEAP-tier model call that reads one artifact's draft body against
the project's own data and flags free-text claims it can't trace to a
given input or computed fact. This is a heuristic reviewer, not a source of
truth: ValidatorReport.disclaimer says so on every call, flags or not
(PLAN's own words, verbatim framing: "a heuristic reviewer that catches
some errors, not a guarantee -- the guarantees live in layers 1-5 and the
provenance objects, which are deterministic").

Builds directly on the M5 unit 1/2 plumbing rather than forking it:

- wrap_untrusted() (context.py) wraps the draft, every other saved
  artifact's summary, and every dataset summary -- the exact same
  delimiter, same injection-defense contract, as every other advisor call
  in this engine.
- _INJECTION_DEFENSE_INSTRUCTIONS (context.py) is reused VERBATIM in this
  module's own system prompt (imported, not copied) so the one delimiter
  contract can never quietly drift between context.py's five modes and
  this sixth layer.
- _extract_computed_facts (context.py) is reused VERBATIM for the same
  reason on the correctness side: it already encodes the one rule that
  matters here (a bare number/bool inside a Computed[T] is safe to lift out
  unwrapped; a structured value that might echo user text is not) --
  forking that logic would risk the two copies silently disagreeing.
- structured.run_structured_mode() -- the exact one-retry-then-fallback
  contract every structured advisor mode already uses (modes.py's
  ReviewResponse etc.), reused here for ValidatorModelResponse.
- client.AdvisorConfigured / AdvisorCallFailed -- this module never
  resolves settings or ever touches `anthropic` itself; it takes an
  already-resolved config (routes/advisor.py's `_require_configured`, the
  SAME 409-before-any-call contract POST /advisor/ask already has) and lets
  AdvisorCallFailed propagate uncaught, same as every other advisor call
  site.

What is deliberately NOT reused from context.py: prescore_block (this is
claim-tracing, not rubric grading -- PLAN §5.3.6 never mentions pre-score)
and the input-token BUDGET/trim system (context.py's _apply_budget). The
brief for this unit does not ask for one, and a single artifact-plus-
summaries prompt is small enough that the M5 unit 1 budget machinery would
be scope creep here, not a requirement -- noted plainly as a scope call in
the build report for this unit.

The validator NEVER writes anything and NEVER blocks a save (PLAN §5.3.6:
"user sees flags before saving" -- not "flags prevent saving"). Nothing in
this module, or in routes/advisor.py's /advisor/validate, ever calls
ProjectStore.save_artifact.
"""

from __future__ import annotations

import json
import os
from dataclasses import replace
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from ..datasets import DatasetStore
from ..project_store import ProjectStore
from ..registry import ARTIFACT_REGISTRY
from .client import AdvisorConfigured
from .context import (
    _INJECTION_DEFENSE_INSTRUCTIONS,
    _extract_computed_facts,
    summarize_artifact,
    summarize_dataset,
    wrap_untrusted,
)
from .structured import run_structured_mode

# ---- Model tier: cheap/fast, a separate constant from the advisor's own
# DEFAULT_MODEL (client.py) -- PLAN §5.3.6: "a second cheap-model call."
# Same env-var-override convention as client.py's ADVISOR_MODEL_ENV_VAR /
# resolve_model() (this unit's brief: "overridable in settings the same
# way, but do NOT build new UI for it") -- no settings.json field, no route
# reads or writes this; an operator sets it in the environment only. ----

VALIDATOR_MODEL_ENV_VAR = "SIGMA_VALIDATOR_MODEL"
DEFAULT_VALIDATOR_MODEL = "claude-haiku-4-5-20251001"


def resolve_validator_model() -> str:
    return os.environ.get(VALIDATOR_MODEL_ENV_VAR) or DEFAULT_VALIDATOR_MODEL


# Flags are short structured objects, not prose -- a smaller cap than the
# advisor's own DEFAULT_MAX_OUTPUT_TOKENS (4096, client.py) reflects the
# cheap tier's job being narrower, not just cheaper per token. Provisional,
# same "measured and tuned" spirit as context.py's own budget constants.
VALIDATOR_MAX_OUTPUT_TOKENS = 2048

# The draft's fixed wrap_untrusted() id -- it has no artifact_id of its own
# yet (pre-save), unlike every other block here which uses a real saved
# artifact_id or dataset_id.
DRAFT_CONTENT_ID = "draft"

# The fixed disclaimer (PLAN §5.3.6, verbatim framing): a real
# ValidatorReport field the UI renders every time, flags or not -- not UI
# copy that could drift from what the architecture doc actually promises.
VALIDATOR_DISCLAIMER = (
    "Heuristic reviewer, not a guarantee: it catches some errors, not all, and zero flags does not mean this "
    "artifact is error-free. The guarantees live in layers 1-5 (schema-constrained output, code-computed numbers, "
    "rule-based tool selection, grounded fields, phase gates) and the provenance objects -- all deterministic."
)

ValidatorSeverity = Literal["cant_trace", "contradicts"]


class ValidatorFlag(BaseModel):
    field_path: str = Field(min_length=1)
    claim_text: str = Field(min_length=1)
    why_flagged: str = Field(min_length=1)
    severity: ValidatorSeverity


class ValidatorModelResponse(BaseModel):
    """The model's own raw structured shape -- structured.py's
    response_model. Deliberately just these two fields, nothing engine-
    added: structured.py's retry prompt generates its JSON schema straight
    from this class, so it must name only what the model is actually asked
    to produce (modes.py's ReviewResponse/HelpMeThinkResponse etc. follow
    the identical discipline -- see structured.py's module docstring)."""

    flags: list[ValidatorFlag] = Field(default_factory=list)
    checked_field_count: int = Field(default=0, ge=0)


class ValidatorReport(BaseModel):
    """run_validator's return type and POST /advisor/validate's
    response_model. Engine-level: the model's parsed flags/count plus
    metadata no prompt ever produces (unstructured_fallback, raw_answer,
    disclaimer) -- see ValidatorModelResponse for the narrower shape the
    model itself must match."""

    flags: list[ValidatorFlag] = Field(default_factory=list)
    checked_field_count: int = Field(default=0, ge=0)
    # True exactly when the model's response failed to parse even after its
    # one retry (structured.py's contract) -- flags is [] in that case, not
    # a guess; rendered honestly rather than implying a clean pass.
    unstructured_fallback: bool = False
    # The last attempt's raw answer text, always present -- same "useful for
    # debugging/display even when parsing failed" contract as
    # AdvisorAskResponse.answer (routes/advisor.py).
    raw_answer: str = ""
    disclaimer: str = VALIDATOR_DISCLAIMER


# ================================================================
# System prompt: this module's own role frame + addendum, but the
# INJECTION-DEFENSE PARAGRAPH ITSELF is imported verbatim from context.py
# (module docstring) rather than restated -- the delimiter it explains is
# the exact one wrap_untrusted() below produces. No ask-by-id instructions
# here (context.py's _ASK_BY_ID_INSTRUCTIONS): this is a single-shot check,
# never a follow-up conversation, and the addendum tells the model so.
# ================================================================

_VALIDATOR_ROLE_FRAME = (
    "You are the validator pass inside Sigma AI, a guided Lean Six Sigma Green Belt suite -- anti-hallucination "
    "layer 6 of 6. A second, cheaper model call reads one DRAFT artifact -- a Green Belt student's work, not yet "
    "saved -- against the project's own data, before the student saves it. You are a heuristic reviewer, not a "
    "source of truth: you never calculate, you never decide what is factually true in the world, and you are not "
    "grading quality or completeness. Your only job is claim-tracing."
)

_VALIDATOR_ADDENDUM = (
    "Find factual claims in the DRAFT's free-text fields -- numbers, comparisons (\"twice as many\", \"the "
    "leading cause\"), cause-effect assertions (\"X caused Y\"), and references to data (\"the data shows...\"). "
    "Ignore fields that are just labels, names, or structural choices with no factual claim in them.\n\n"
    "For every claim you find, decide: does it trace to something given to you below -- the DRAFT FACTS section, "
    "the draft's own content, an OTHER PROJECT ARTIFACT summary, or a PROJECT DATASET summary? If yes, do not flag "
    "it. If it does not trace to anything given to you, flag it with severity \"cant_trace\". If it actively "
    "contradicts a number or fact given to you, flag it with severity \"contradicts\" and name the contradiction "
    "plainly in why_flagged.\n\n"
    "Never flag a bare number that already appears in DRAFT FACTS or the draft's own computed fields, and never "
    "invent a claim that isn't actually present in the draft's text. This is a single pass -- you will not get a "
    "chance to ask for more information, so work only with what is given below.\n\n"
    "Respond with EXACTLY one fenced ```json code block, and nothing else meaningfully outside it, containing an "
    "object with this shape:\n"
    '{"flags": [{"field_path": "<dotted path to the field, e.g. problem_statement.what>", '
    '"claim_text": "<the exact claim text from the draft>", '
    '"why_flagged": "<one sentence: what you checked and why it does not trace, or exactly what it contradicts>", '
    '"severity": "cant_trace" or "contradicts"}], '
    '"checked_field_count": <integer -- how many free-text fields you examined>}\n\n'
    "An empty flags list is a legitimate, common result when every claim traces cleanly -- never invent a flag "
    "just to have something to say."
)


def _build_validator_system_prompt() -> str:
    return f"{_VALIDATOR_ROLE_FRAME}\n\n{_VALIDATOR_ADDENDUM}\n\n{_INJECTION_DEFENSE_INSTRUCTIONS}"


# ================================================================
# Draft canonicalization + context assembly
# ================================================================


def _canonicalize_draft(model_cls: type[BaseModel], artifact_body: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Best-effort validate + recompute the draft through its OWN registered
    schema, so any Computed[T] field the model sees (in the draft's full
    JSON, and in facts_block below) is the engine's own fresh arithmetic --
    never a client-supplied number rendered as if it were engine-computed
    (the same "unconditionally server-recomputed... never accepted verbatim
    from a client" discipline every artifact in this engine already
    enforces on save, e.g. CopqArtifact._recompute_total).

    Unlike context.py's run_prescore_for_artifact (which only ever sees an
    ALREADY-SAVED, already-validated artifact, and treats a validation
    failure there as "extremely unlikely"), this runs on a genuinely
    pre-save DRAFT -- a student mid-edit is routinely, legitimately
    incomplete. A ValidationError here is expected, not exceptional: fall
    back to the raw client-submitted dict rather than failing the whole
    validator call, and say so honestly via the returned bool (the caller
    folds that into the draft's own header text -- this engine's usual
    "never trim/fudge silently" rule)."""
    try:
        validated = model_cls.model_validate(artifact_body)
    except ValidationError:
        return artifact_body, False
    return validated.model_dump(mode="json"), True


def _draft_block(tool_id: str, draft_data: dict[str, Any], validated: bool) -> str:
    header = f"DRAFT (pre-save) content for tool {tool_id}:\n"
    if not validated:
        header += (
            f"(note: this draft does not currently validate against the {tool_id} schema -- computed fields below "
            "may be missing or stale; shown exactly as submitted)\n"
        )
    body_json = json.dumps(draft_data, indent=2, sort_keys=True)
    return wrap_untrusted(DRAFT_CONTENT_ID, header + body_json)


def _build_validator_user_turn(
    *, draft_block: str, facts_block: str, other_artifact_blocks: list[str], dataset_blocks: list[str],
) -> str:
    parts = [
        "=== DRAFT FACTS (computed/provenance values already on the draft; engine-produced, not user-authored) ===",
        facts_block or "(none)",
        "",
        "=== DRAFT (the artifact being checked, pre-save; delimited below) ===",
        draft_block,
    ]
    if other_artifact_blocks:
        parts += ["", "=== OTHER PROJECT ARTIFACTS (already saved, summarized; delimited below) ==="]
        parts += other_artifact_blocks
    if dataset_blocks:
        parts += ["", "=== PROJECT DATASETS (summarized; delimited below) ==="]
        parts += dataset_blocks
    parts += [
        "",
        "=== TASK ===",
        "Check the DRAFT's free-text claims against everything above, per your instructions.",
    ]
    return "\n".join(parts)


def run_validator(
    project_id: str,
    tool_id: str,
    artifact_body: dict[str, Any],
    store: ProjectStore,
    *,
    config: AdvisorConfigured,
    http_client: httpx.Client | None = None,
) -> ValidatorReport:
    """PLAN §5.3.6's validator pass. `config` is an ALREADY-RESOLVED
    AdvisorConfigured -- same split of responsibility as client.ask() and
    structured.run_structured_mode(): this module never resolves settings
    or checks for a missing key itself (routes/advisor.py's
    `_require_configured` does that, exactly as it already does for
    POST /advisor/ask, and raises the same 409 before this function is ever
    called). Only the MODEL differs from the main advisor call -- swapped
    to the cheap tier below, never the key/base_url resolution.

    Raises FileNotFoundError for an unknown project_id (routes/advisor.py
    maps that to 404, same as every other store-backed advisor call) or an
    unknown tool_id (same 404 convention routes/artifacts.py's _model_for
    already uses for "unknown tool_id"). Never raises on a draft that fails
    its own schema validation -- see _canonicalize_draft. AdvisorCallFailed
    (a real API/network failure) propagates uncaught, same as every other
    advisor call site in this engine."""
    meta = store.load_project(project_id)  # FileNotFoundError -> 404 at the route layer

    model_cls = ARTIFACT_REGISTRY.get(tool_id)
    if model_cls is None:
        raise FileNotFoundError(f"unknown tool_id {tool_id!r}")

    draft_data, validated = _canonicalize_draft(model_cls, artifact_body)
    draft_content = _draft_block(tool_id, draft_data, validated)
    # _extract_computed_facts is context.py's own module-private helper,
    # imported rather than forked -- see module docstring.
    facts_block = "\n".join(_extract_computed_facts(draft_data))

    other_blocks: list[str] = []
    for other_id, entry in sorted(meta.artifact_index.items()):
        data = store.load_artifact(project_id, other_id)
        other_blocks.append(wrap_untrusted(other_id, summarize_artifact(other_id, entry.tool_id, data)))

    dataset_store = DatasetStore(store)
    dataset_blocks = [
        wrap_untrusted(ds_meta.dataset_id, summarize_dataset(ds_meta))
        for ds_meta in dataset_store.list_datasets(project_id)
    ]

    system = _build_validator_system_prompt()
    user_content = _build_validator_user_turn(
        draft_block=draft_content, facts_block=facts_block, other_artifact_blocks=other_blocks, dataset_blocks=dataset_blocks,
    )

    # The one place this module differs from the main advisor call: the
    # cheap tier, swapped in on TOP of the already-resolved key/base_url --
    # see resolve_validator_model()'s own comment on why this can't just be
    # `config` unmodified.
    validator_config = replace(config, model=resolve_validator_model())

    outcome = run_structured_mode(
        validator_config, system=system, user_content=user_content,
        response_model=ValidatorModelResponse, max_output_tokens=VALIDATOR_MAX_OUTPUT_TOKENS,
        http_client=http_client,
    )

    if outcome.parsed is not None:
        # Guaranteed by run_structured_mode's own contract (structured.py's
        # StructuredOutcome docstring): parsed is an instance of whatever
        # response_model was passed in, exactly when it isn't None.
        assert isinstance(outcome.parsed, ValidatorModelResponse)
        flags = outcome.parsed.flags
        checked_field_count = outcome.parsed.checked_field_count
    else:
        flags = []
        checked_field_count = 0

    return ValidatorReport(
        flags=flags,
        checked_field_count=checked_field_count,
        unstructured_fallback=outcome.unstructured_fallback,
        raw_answer=outcome.raw_text,
    )
