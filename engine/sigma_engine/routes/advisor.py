"""POST /advisor/ask, GET/PUT /advisor/settings, POST /advisor/status,
POST /advisor/validate (PLAN §5, M5 unit 1 plumbing + M5 unit 2's five
modes + M5 unit 3's validator pass). The advisor is Layer 2 and strictly
optional: every response here is a clean typed result even with no API key
configured (client.py's AdvisorUnavailable renders as a 409, never a 500)
-- and no other router in this engine ever imports from `advisor/`, so
Layer 1 is unaffected regardless of what happens here.

M5 unit 2 adds mode-aware dispatch through advisor/modes.py's
MODE_REGISTRY: every mode (including "generic", re-registered there so
this file never special-cases it) resolves to a ModeSpec whose
context_selector replaces the old direct assemble_context() call and
whose output_parser (a Pydantic model, or None for a prose-only mode)
decides whether the wire call goes through structured.run_structured_mode
(one retry on a malformed response, never a 500 -- see that module) or
the plain single client.ask() call every mode used before this unit.

M5 unit 3 adds POST /advisor/validate (PLAN §5.3.6, anti-hallucination
layer 6): the SAME "resolve config or 409" gate as /advisor/ask
(_require_configured, unchanged, reused as-is) in front of
advisor/validator.py's run_validator -- a second, cheaper-model call that
flags free-text claims it can't trace to project data. It never blocks a
save (validator.py's own module docstring); this route only ever reads.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..advisor import modes as modes_module
from ..advisor import prompt_pack
from ..advisor.client import AdvisorCallFailed, AdvisorConfigured, AdvisorUnavailable
from ..advisor.client import ask as client_ask
from ..advisor.client import resolve_config, resolve_model
from ..advisor.context import (
    AssembledContext,
    BudgetReport,
    parse_requested_artifact_ids,
    render_facts_block,
    summarize_artifact,
    wrap_untrusted,
)
from ..advisor.modes import PHASE_TOOL_IDS, AdvisorFocusRef, ModeSpec
from ..advisor.settings_store import AdvisorSettings, AdvisorSettingsStore, mask_api_key
from ..advisor.structured import run_structured_mode
from ..advisor.validator import ValidatorReport, run_validator
from ..artifacts.a3 import TollgatePhase
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/advisor", tags=["advisor"])

# The six mode names this route accepts -- MODE_REGISTRY's own keys,
# re-declared as a Literal (rather than validated dynamically against the
# dict) so FastAPI's OpenAPI schema and the 422-on-bad-mode behavior both
# come from ordinary Pydantic validation, exactly like the M5 unit 1
# plumbing's Literal["generic"] did. test_routes_advisor.py asserts this
# stays in sync with MODE_REGISTRY's keys.
AdvisorMode = Literal["generic", "review", "help_me_think", "explain", "tollgate", "remedy"]

# A missing/disabled key is a clean refusal, never a 500 (M5 brief: "a
# clean 409/412-style response"). 409 for consistency with the one other
# non-404/422/403 status this engine already uses (routes/projects.py's
# "already exists" -- the current state, advisor not configured, conflicts
# with the request).
_UNAVAILABLE_STATUS_CODE = 409
# A *configured* call whose actual request to the Anthropic API fails
# (bad key rejected server-side, network error, rate limit, ...) is a
# different case -- 502 Bad Gateway: this engine proxied to a remote API
# that errored.
_CALL_FAILED_STATUS_CODE = 502


def _require_configured(store: ProjectStore) -> AdvisorConfigured:
    settings = AdvisorSettingsStore(store.root).load()
    config = resolve_config(settings)
    if isinstance(config, AdvisorUnavailable):
        # Plain string detail (not a dict): flows straight through the
        # desktop's existing ApiError string-detail path (api/client.ts)
        # with no new parsing needed there.
        raise HTTPException(status_code=_UNAVAILABLE_STATUS_CODE, detail=config.detail)
    return config


# ---- POST /advisor/ask ----


class AdvisorAskRequest(BaseModel):
    project_id: str
    mode: AdvisorMode = "generic"
    artifact_id: str | None = None
    # Free-text user input, reused across modes rather than one new field
    # per mode (M5 unit 2 scope call -- see the build report): help_me_think's
    # optional seed topic and remedy's optional constraints both travel here,
    # exactly like generic's question always has; each mode's addendum
    # (advisor/modes.py) tells the model how to read whatever's in it.
    question: str | None = None
    # The ask-by-ID follow-up turn (M5 brief): an id the model asked for
    # via a REQUEST_ARTIFACT: line on a prior call, sent back so this call
    # gets that artifact's full JSON instead of just its summary.
    follow_up_artifact_request: str | None = None
    # tollgate mode's request shape (PLAN §5.1 mode 4: "Request: {phase}").
    # TollgatePhase (a3.py) reused, not redefined -- an invalid phase name
    # fails schema validation the same way an invalid mode name does.
    phase: TollgatePhase | None = None
    # explain mode's optional focus (PLAN §5.1 mode 3). Untrusted like any
    # other user/UI-sourced text -- see AdvisorFocusRef's docstring.
    focus: AdvisorFocusRef | None = None

    @model_validator(mode="after")
    def _tollgate_requires_phase(self) -> "AdvisorAskRequest":
        if self.mode == "tollgate" and self.phase is None:
            raise ValueError("tollgate mode requires `phase`")
        return self


class AdvisorAskResponse(BaseModel):
    mode: str
    # Always present: for a prose mode (generic/explain), the model's
    # answer text; for a structured mode, the raw text of its LAST attempt
    # -- useful for debugging/display even when `structured` is None.
    answer: str
    # The mode-specific parsed payload (ReviewResponse/HelpMeThinkResponse/
    # TollgateResponse/RemedyResponse, model_dump()'d) when a structured
    # mode's response parsed successfully; always None for a prose mode.
    structured: dict[str, Any] | None = None
    # True exactly when a structured mode's response failed to parse even
    # after its one retry (PLAN §5.1 mode 1: "surfaces as a plain-text
    # fallback with a 'model returned unstructured output' flag -- never a
    # 500"). `answer` still carries the model's raw text either way.
    unstructured_fallback: bool = False
    budget_report: BudgetReport
    requested_artifact_ids: list[str] = []


def _effective_question(question: str | None, focus: AdvisorFocusRef | None) -> str | None:
    """Folds explain mode's `focus` into the same single question string
    every mode already carries, rather than adding a second wrap_untrusted
    call site (RULES: "All user-authored text untrusted-wrapped --
    including mode-specific inputs (constraints, seed topic, focus)" --
    satisfied here because the combined string below still goes through
    _build_user_turn's one wrap_untrusted("user_question", ...) call,
    unchanged)."""
    if focus is None:
        return question
    focus_text = f"(explain this result) {focus.kind}: {focus.ref}"
    return f"{focus_text}\n\n{question}" if question else focus_text


def _build_user_turn(assembled: AssembledContext, question: str | None) -> str:
    """Compose the single user-role message: facts + pre-score (engine-
    produced, unwrapped), the mode-specific engine-authored block if any
    (M5 unit 2: rubric text / tollgate questions+phase context / remedy's
    charter-baseline note -- assembled.mode_block, itself already
    wrap_untrusted()-safe per-piece where it needed to be, see that
    field's docstring), every untrusted artifact block, then the user's
    own question -- wrapped exactly like artifact content, since a typed
    question is user-authored too (context.py assembles the project-derived
    blocks only; wrapping the live question is this route's job, using the
    same wrap_untrusted the assembler uses internally, imported from there
    so there is exactly one delimiter definition in this codebase)."""
    parts = [
        "=== FACTS (computed by the engine; not user-authored) ===",
        assembled.facts_block or "(none)",
        "",
        "=== PRE-SCORE (deterministic rubric checks; not user-authored) ===",
        assembled.prescore_block or "(none)",
    ]
    if assembled.mode_block:
        parts += ["", "=== MODE CONTEXT (engine-authored; not user-authored) ===", assembled.mode_block]
    if assembled.untrusted_blocks:
        parts += ["", "=== PROJECT ARTIFACTS (user-authored content follows, delimited below) ==="]
        parts += assembled.untrusted_blocks
    parts += ["", "=== QUESTION ==="]
    if question:
        parts.append(wrap_untrusted("user_question", question))
    else:
        parts.append("(no question asked -- give a general read of what's above)")
    return "\n".join(parts)


def _mode_spec(mode: str) -> ModeSpec:
    # MODE_REGISTRY is keyed by every value AdvisorMode allows (asserted
    # in test_routes_advisor.py), so this lookup can't miss for a request
    # that already passed schema validation.
    return modes_module.MODE_REGISTRY[mode]


@router.post("/ask", response_model=AdvisorAskResponse)
def ask(body: AdvisorAskRequest, store: ProjectStore = Depends(get_store)) -> AdvisorAskResponse:
    config = _require_configured(store)
    spec = _mode_spec(body.mode)

    try:
        assembled = spec.context_selector(
            store,
            project_id=body.project_id,
            artifact_id=body.artifact_id,
            follow_up_artifact_id=body.follow_up_artifact_request,
            phase=body.phase,
            focus=body.focus,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # `focus` is explain mode's field (PLAN §5.1 mode 3); no other mode's
    # desktop UI ever sends it, so folding it in unconditionally here is
    # a no-op (returns `question` unchanged) for every other mode.
    question = _effective_question(body.question, body.focus)
    user_content = _build_user_turn(assembled, question)

    try:
        if spec.output_parser is None:
            answer = client_ask(
                config, system=assembled.system_prompt_frame, user_content=user_content,
                max_output_tokens=assembled.budget_report.output_budget_tokens,
            )
            answer_text, structured, unstructured_fallback = answer.text, None, False
        else:
            outcome = run_structured_mode(
                config, system=assembled.system_prompt_frame, user_content=user_content,
                response_model=spec.output_parser, max_output_tokens=assembled.budget_report.output_budget_tokens,
            )
            answer_text = outcome.raw_text
            structured = outcome.parsed.model_dump(mode="json") if outcome.parsed is not None else None
            unstructured_fallback = outcome.unstructured_fallback
    except AdvisorCallFailed as exc:
        raise HTTPException(status_code=_CALL_FAILED_STATUS_CODE, detail=f"The Anthropic API call failed: {exc}") from exc

    # M5 exit red-team fix: only surface REQUEST_ARTIFACT ids that actually
    # exist in this project. The model's answer text can echo hostile
    # artifact content (which may plant fake REQUEST_ARTIFACT lines), and
    # the UI's confirm prompt must never offer an id the project doesn't
    # hold -- filtering here keeps the confirm-first loop honest.
    known_ids = set(store.load_project(body.project_id).artifact_index)
    requested = [rid for rid in parse_requested_artifact_ids(answer_text) if rid in known_ids]

    return AdvisorAskResponse(
        mode=body.mode,
        answer=answer_text,
        structured=structured,
        unstructured_fallback=unstructured_fallback,
        budget_report=assembled.budget_report,
        requested_artifact_ids=requested,
    )


# ---- GET /advisor/export/{project_id}/{tool_id} (M5 unit 4, PLAN §5.2) ----
#
# The paste-ready chatbot export: the tool's portable prompt (prompt_pack.py,
# shipped inside the engine -- no filesystem read of prompts/) + the current
# artifact's JSON + the engine-computed facts, combined into one copyable
# block. Deliberately NOT behind _require_configured: the prompt pack exists
# exactly for users with no API key, so this route works with Layer 2
# entirely unconfigured. Nothing here calls a model -- it only reads the
# project store and string-assembles.

# The combined block's fixed section headings (PLAN §5.2's one copy action:
# "prompt + artifact JSON + computed stats"). The facts heading carries the
# authority label in-line so the pasted chat itself says which numbers are
# the record.
_EXPORT_ARTIFACT_HEADING = "MY ARTIFACT:"
_EXPORT_SUMMARIES_HEADING = "MY PHASE ARTIFACTS (summaries from the app):"
_EXPORT_FACTS_HEADING = "COMPUTED RESULTS (authoritative, from the app):"

ExportMode = Literal["tool", "tollgate"]


class AdvisorExportResponse(BaseModel):
    prompt_text: str
    # mode=tool: the current artifact's pretty-printed JSON ("" when no
    # artifact_id was given -- T-13/T-14 have no saved artifact, and the
    # prompt alone is still a valid export). mode=tollgate: the phase's
    # artifact summaries block (summarize_artifact per saved phase tool,
    # plain text) -- the same "user's work" slot, phase-shaped.
    artifact_json: str
    # Engine-computed facts (render_facts_block): the current artifact's
    # Computed[T] leaves, or in tollgate mode every phase artifact's,
    # labeled by artifact id. "" when nothing is computed.
    facts_block: str
    # The one block the desktop copies to the clipboard: prompt_text +
    # headings + artifact/facts content, in paste order.
    combined: str


def _combine_export(prompt_text: str, work_heading: str, work_block: str, facts_block: str) -> str:
    return "\n\n".join(
        [
            prompt_text.rstrip("\n"),
            f"{work_heading}\n{work_block}",
            f"{_EXPORT_FACTS_HEADING}\n{facts_block if facts_block else '(none computed yet)'}",
        ]
    )


def _export_tool(store: ProjectStore, project_id: str, tool_id: str, artifact_id: str | None) -> AdvisorExportResponse:
    prompt_text = prompt_pack.tool_prompt_text(tool_id)
    if prompt_text is None:
        raise HTTPException(status_code=404, detail=f"no prompt exists for tool {tool_id!r}")

    meta = store.load_project(project_id)  # FileNotFoundError -> 404 below

    artifact_json = ""
    facts_block = ""
    if artifact_id is not None:
        entry = meta.artifact_index.get(artifact_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"artifact {artifact_id!r} not found in project {project_id!r}")
        if entry.tool_id != tool_id:
            # Same "current state conflicts with the request" convention as
            # the 409s above -- exporting T-03's prompt around a T-02
            # artifact would produce a block that lies about itself.
            raise HTTPException(
                status_code=409,
                detail=f"artifact {artifact_id!r} belongs to tool {entry.tool_id}, not {tool_id}",
            )
        data = store.load_artifact(project_id, artifact_id)
        artifact_json = json.dumps(data, indent=2, sort_keys=True)
        facts_block = render_facts_block(data)

    work_block = artifact_json if artifact_json else "(no saved artifact in the app for this tool -- paste or describe your work here)"
    return AdvisorExportResponse(
        prompt_text=prompt_text,
        artifact_json=artifact_json,
        facts_block=facts_block,
        combined=_combine_export(prompt_text, _EXPORT_ARTIFACT_HEADING, work_block, facts_block),
    )


def _export_tollgate(store: ProjectStore, project_id: str, phase: TollgatePhase) -> AdvisorExportResponse:
    prompt_text = prompt_pack.tollgate_prompt_text(phase)
    if prompt_text is None:  # unreachable behind the TollgatePhase Literal; honest fallback anyway
        raise HTTPException(status_code=404, detail=f"no tollgate prompt exists for phase {phase!r}")

    meta = store.load_project(project_id)  # FileNotFoundError -> 404 below

    summaries: list[str] = []
    facts_sections: list[str] = []
    for tool_id in PHASE_TOOL_IDS.get(phase, ()):
        data = store.latest_artifact_for_tool(project_id, meta, tool_id)
        if data is None:
            continue
        artifact_id = data["artifact_id"]
        summaries.append(summarize_artifact(artifact_id, tool_id, data))
        facts = render_facts_block(data)
        if facts:
            facts_sections.append(f"{artifact_id} ({tool_id}):\n{facts}")

    summaries_block = "\n\n".join(summaries)
    facts_block = "\n\n".join(facts_sections)
    work_block = summaries_block if summaries_block else "(no artifacts saved for this phase yet -- paste or describe the phase's work here)"
    return AdvisorExportResponse(
        prompt_text=prompt_text,
        artifact_json=summaries_block,
        facts_block=facts_block,
        combined=_combine_export(prompt_text, _EXPORT_SUMMARIES_HEADING, work_block, facts_block),
    )


@router.get("/export/{project_id}/{tool_id}", response_model=AdvisorExportResponse)
def export_for_chatbot(
    project_id: str,
    tool_id: str,
    artifact_id: str | None = None,
    mode: ExportMode = "tool",
    phase: TollgatePhase | None = None,
    store: ProjectStore = Depends(get_store),
) -> AdvisorExportResponse:
    """mode=tool (default): this tool's prompt + the named artifact's JSON +
    its computed facts. mode=tollgate: the phase's Champion prompt + phase
    artifact summaries + per-artifact facts (tool_id and artifact_id are
    ignored -- the phase names its own tools via PHASE_TOOL_IDS, mirroring
    tollgate ask mode's own contract of targeting the project, not the
    screen the panel happened to be open on)."""
    try:
        if mode == "tollgate":
            if phase is None:
                raise HTTPException(status_code=422, detail="mode=tollgate requires `phase`")
            return _export_tollgate(store, project_id, phase)
        return _export_tool(store, project_id, tool_id, artifact_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---- POST /advisor/validate (PLAN §5.3.6, M5 unit 3) ----


class AdvisorValidateRequest(BaseModel):
    project_id: str = Field(min_length=1)
    tool_id: str = Field(min_length=1)
    # The pre-save artifact body -- whatever the desktop would otherwise
    # POST to /project/{project_id}/artifacts/{tool_id}. Untrusted like any
    # other artifact content (validator.py wraps it, never this route).
    body: dict[str, Any] = Field(default_factory=dict)


@router.post("/validate", response_model=ValidatorReport)
def validate(request: AdvisorValidateRequest, store: ProjectStore = Depends(get_store)) -> ValidatorReport:
    """Same unavailable-when-no-key contract as POST /advisor/ask (409,
    plain message) -- _require_configured is reused unchanged, not forked.
    Never blocks a save: this route only reads and reports; nothing here
    ever calls store.save_artifact. A tool_id not in ARTIFACT_REGISTRY, or
    a project_id that doesn't exist, is a 404 (run_validator raises
    FileNotFoundError for both -- see that function's docstring), matching
    routes/artifacts.py's own "unknown tool_id" convention. A malformed
    request body (missing project_id/tool_id) is a plain 422 from
    AdvisorValidateRequest's own schema, no extra handling needed."""
    config = _require_configured(store)
    try:
        return run_validator(request.project_id, request.tool_id, request.body, store, config=config)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AdvisorCallFailed as exc:
        raise HTTPException(status_code=_CALL_FAILED_STATUS_CODE, detail=f"The Anthropic API call failed: {exc}") from exc


# ---- GET/PUT /advisor/settings ----


class AdvisorSettingsResponse(BaseModel):
    # Masked (last-4 only) or null if nothing is stored -- never the real
    # key (M5 brief: "the settings GET must mask it"). Named _masked, not
    # `api_key`, so nothing reading this response can mistake it for a
    # usable value.
    api_key_masked: str | None
    base_url: str | None
    enabled: bool


class AdvisorSettingsUpdateRequest(BaseModel):
    # None or "" both mean "leave the stored key unchanged." The GET
    # response never echoes the real key back, so a settings form has no
    # way to round-trip it into this field -- a blank submit must not be
    # read as "clear the key." A non-empty string sets/overwrites it.
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool


def _to_response(settings: AdvisorSettings) -> AdvisorSettingsResponse:
    return AdvisorSettingsResponse(
        api_key_masked=mask_api_key(settings.api_key), base_url=settings.base_url, enabled=settings.enabled
    )


@router.get("/settings", response_model=AdvisorSettingsResponse)
def get_settings(store: ProjectStore = Depends(get_store)) -> AdvisorSettingsResponse:
    return _to_response(AdvisorSettingsStore(store.root).load())


@router.put("/settings", response_model=AdvisorSettingsResponse)
def put_settings(
    body: AdvisorSettingsUpdateRequest, store: ProjectStore = Depends(get_store)
) -> AdvisorSettingsResponse:
    settings_store = AdvisorSettingsStore(store.root)
    current = settings_store.load()
    next_api_key = body.api_key if body.api_key else current.api_key
    updated = AdvisorSettings(api_key=next_api_key, base_url=body.base_url, enabled=body.enabled)
    settings_store.save(updated)
    return _to_response(updated)


# ---- POST /advisor/status ----


class AdvisorStatusResponse(BaseModel):
    configured: bool
    model: str


@router.post("/status", response_model=AdvisorStatusResponse)
def status(store: ProjectStore = Depends(get_store)) -> AdvisorStatusResponse:
    settings = AdvisorSettingsStore(store.root).load()
    config = resolve_config(settings)
    if isinstance(config, AdvisorUnavailable):
        return AdvisorStatusResponse(configured=False, model=resolve_model())
    return AdvisorStatusResponse(configured=True, model=config.model)
