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
claim-tracing, not rubric grading -- PLAN §5.3.6 never mentions pre-score).

M5 exit critic, Fix 8: this module used to send the draft body plus EVERY
other artifact's summary plus EVERY dataset's summary with no budget at
all -- unlike every other advisor surface, which has gone through
context.py's _apply_budget since M5 unit 1. A project with enough saved
artifacts and datasets could blow well past what the model can usefully
read, silently. The input-token budget is reused here now (same 30k
default as context.py's DEFAULT_INPUT_BUDGET_TOKENS, same estimate_tokens
heuristic, same "never trim silently" contract -- see
_apply_validator_budget below), in a priority order specific to this
module's own tiers: draft > draft facts > other-artifact summaries >
dataset summaries; the system prompt is never trimmed, same as every
other advisor surface. The draft itself is exempt from ordinary trimming
-- it's the one thing being checked, so shrinking it would mean grading a
draft the user didn't actually write -- but IS hard-capped: if the draft
alone (plus the system prompt) already exceeds the budget, no amount of
trimming the other tiers can fix that, so run_validator raises
DraftExceedsBudgetError instead of ever calling the model (routes/
advisor.py turns that into an honest 422).

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
    DEFAULT_INPUT_BUDGET_TOKENS,
    BudgetDroppedEntry,
    BudgetReport,
    _extract_computed_facts,
    estimate_tokens,
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


class DraftExceedsBudgetError(Exception):
    """Raised (Fix 8, M5 exit critic) when the draft artifact alone --
    together with the system prompt, which is never trimmed -- already
    exceeds the validator's input budget. No amount of trimming the
    optional context tiers (draft facts, other-artifact summaries, dataset
    summaries; see _apply_validator_budget) can fix this: the draft itself
    is the problem, so run_validator raises this BEFORE ever calling the
    model, rather than silently truncating the one thing the user actually
    asked to have checked. routes/advisor.py turns this into an honest 422
    (distinct from the plain request-shape 422 AdvisorValidateRequest's own
    schema already produces)."""


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
    # Fix 8 (M5 exit critic): same BudgetReport shape context.py's own
    # AssembledContext.budget_report uses (imported, not a second type) --
    # what actually made it into the model's context and what got trimmed
    # to fit, in the priority order _apply_validator_budget documents.
    # Always present; dropped is [] when nothing needed trimming.
    budget_report: BudgetReport


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


# ================================================================
# Input budget (Fix 8, M5 exit critic) -- module docstring. Priority,
# highest kept-priority first: system prompt (never trimmed) > draft
# (never trimmed here -- see DraftExceedsBudgetError instead) > draft
# facts > other-artifact summaries > dataset summaries. Trimming removes
# tiers in the REVERSE of that order (dataset summaries first), and the
# two summaries tiers are each many independent blocks dropped one at a
# time (largest first) -- context.py's own "summaries" tier pattern,
# split into two tiers here because they're conceptually different data
# (other artifacts vs. imported datasets) even though both trim the same
# way.
# ================================================================

_TIER_DATASET_SUMMARIES = "dataset_summaries"
_TIER_OTHER_ARTIFACT_SUMMARIES = "other_artifact_summaries"
_TIER_DRAFT_FACTS = "draft_facts"


def _apply_validator_budget(
    *,
    system_prompt: str,
    draft_block: str,
    facts_block: str,
    other_artifact_items: list[tuple[str, str]],
    dataset_items: list[tuple[str, str]],
    input_budget_tokens: int,
    output_budget_tokens: int,
) -> tuple[BudgetReport, str, list[tuple[str, str]], list[tuple[str, str]]]:
    """Trims draft facts / other-artifact summaries / dataset summaries to
    fit `input_budget_tokens`, in the tier order above. `system_prompt` and
    `draft_block` are counted honestly but never trimmed by this function
    -- the caller (run_validator) has already confirmed the two of them
    fit on their own before this ever runs (DraftExceedsBudgetError
    otherwise)."""
    dropped: list[BudgetDroppedEntry] = []

    system_cost = estimate_tokens(system_prompt)
    draft_cost = estimate_tokens(draft_block)
    facts_cost = estimate_tokens(facts_block) if facts_block else 0
    kept_other = [(cid, text, estimate_tokens(text)) for cid, text in other_artifact_items]
    kept_datasets = [(cid, text, estimate_tokens(text)) for cid, text in dataset_items]
    keep_facts = bool(facts_block)

    def total() -> int:
        return (
            system_cost
            + draft_cost
            + (facts_cost if keep_facts else 0)
            + sum(c for _, _, c in kept_other)
            + sum(c for _, _, c in kept_datasets)
        )

    # Tier 4 (dropped first): dataset summaries, largest first.
    kept_datasets.sort(key=lambda item: (-item[2], item[0]))
    while total() > input_budget_tokens and kept_datasets:
        did, _text, cost = kept_datasets.pop(0)
        dropped.append(BudgetDroppedEntry(tier=_TIER_DATASET_SUMMARIES, id=did, estimated_tokens=cost))
    kept_datasets.sort(key=lambda item: item[0])  # restore deterministic id order for what's left

    # Tier 3: other-artifact summaries, largest first.
    kept_other.sort(key=lambda item: (-item[2], item[0]))
    while total() > input_budget_tokens and kept_other:
        oid, _text, cost = kept_other.pop(0)
        dropped.append(BudgetDroppedEntry(tier=_TIER_OTHER_ARTIFACT_SUMMARIES, id=oid, estimated_tokens=cost))
    kept_other.sort(key=lambda item: item[0])

    # Tier 2: draft facts, all-or-nothing, dropped only as a last resort.
    if total() > input_budget_tokens and keep_facts:
        keep_facts = False
        dropped.append(BudgetDroppedEntry(tier=_TIER_DRAFT_FACTS, id="facts_block", estimated_tokens=facts_cost))

    # Tier 1 (draft_block) and tier 0 (system_prompt) are never dropped
    # here -- run_validator has already ruled out the case where the two
    # of them together can't fit; any remaining overage is reported
    # honestly via estimated_input_tokens, never hidden.

    included: list[str] = ["system_prompt", "draft"]
    if keep_facts:
        included.append("facts_block")
    included.extend(f"other_artifact:{cid}" for cid, _t, _c in kept_other)
    included.extend(f"dataset:{cid}" for cid, _t, _c in kept_datasets)

    report = BudgetReport(
        input_budget_tokens=input_budget_tokens,
        output_budget_tokens=output_budget_tokens,
        estimated_input_tokens=total(),
        included=included,
        dropped=dropped,
    )

    final_facts = facts_block if keep_facts else ""
    final_other = [(cid, text) for cid, text, _c in kept_other]
    final_datasets = [(cid, text) for cid, text, _c in kept_datasets]

    return report, final_facts, final_other, final_datasets


def run_validator(
    project_id: str,
    tool_id: str,
    artifact_body: dict[str, Any],
    store: ProjectStore,
    *,
    config: AdvisorConfigured,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
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
    its own schema validation -- see _canonicalize_draft. Raises
    DraftExceedsBudgetError (Fix 8) when the draft alone, plus the system
    prompt, already exceeds `input_budget_tokens` -- before any model call.
    AdvisorCallFailed (a real API/network failure) propagates uncaught,
    same as every other advisor call site in this engine."""
    meta = store.load_project(project_id)  # FileNotFoundError -> 404 at the route layer

    model_cls = ARTIFACT_REGISTRY.get(tool_id)
    if model_cls is None:
        raise FileNotFoundError(f"unknown tool_id {tool_id!r}")

    draft_data, validated = _canonicalize_draft(model_cls, artifact_body)
    draft_content = _draft_block(tool_id, draft_data, validated)
    # _extract_computed_facts is context.py's own module-private helper,
    # imported rather than forked -- see module docstring.
    facts_block = "\n".join(_extract_computed_facts(draft_data))

    other_items: list[tuple[str, str]] = []
    for other_id, entry in sorted(meta.artifact_index.items()):
        data = store.load_artifact(project_id, other_id)
        other_items.append((other_id, wrap_untrusted(other_id, summarize_artifact(other_id, entry.tool_id, data))))

    dataset_store = DatasetStore(store)
    dataset_items: list[tuple[str, str]] = [
        (ds_meta.dataset_id, wrap_untrusted(ds_meta.dataset_id, summarize_dataset(ds_meta)))
        for ds_meta in dataset_store.list_datasets(project_id)
    ]

    system = _build_validator_system_prompt()

    # Fix 8: the draft is never trimmed by _apply_validator_budget (it's
    # the one thing being checked -- shrinking it would mean grading a
    # draft the user didn't write), so if it doesn't fit ALONGSIDE the
    # (also never-trimmed) system prompt, no amount of trimming the
    # optional tiers below can save this call. Fail honestly, before ever
    # reaching the model.
    system_and_draft_cost = estimate_tokens(system) + estimate_tokens(draft_content)
    if system_and_draft_cost > input_budget_tokens:
        raise DraftExceedsBudgetError(
            f"the draft for tool {tool_id!r} is too large to check: it alone (~{system_and_draft_cost} estimated "
            f"tokens with the system prompt) exceeds the {input_budget_tokens}-token input budget"
        )

    budget_report, kept_facts_block, kept_other_items, kept_dataset_items = _apply_validator_budget(
        system_prompt=system,
        draft_block=draft_content,
        facts_block=facts_block,
        other_artifact_items=other_items,
        dataset_items=dataset_items,
        input_budget_tokens=input_budget_tokens,
        output_budget_tokens=VALIDATOR_MAX_OUTPUT_TOKENS,
    )

    user_content = _build_validator_user_turn(
        draft_block=draft_content,
        facts_block=kept_facts_block,
        other_artifact_blocks=[text for _cid, text in kept_other_items],
        dataset_blocks=[text for _did, text in kept_dataset_items],
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
        budget_report=budget_report,
    )
