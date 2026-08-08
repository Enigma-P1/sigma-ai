"""POST /advisor/ask, GET/PUT /advisor/settings, POST /advisor/status
(PLAN §5, M5 brief unit 1). The advisor is Layer 2 and strictly optional:
every response here is a clean typed result even with no API key
configured (client.py's AdvisorUnavailable renders as a 409, never a
500) -- and no other router in this engine ever imports from `advisor/`,
so Layer 1 is unaffected regardless of what happens here.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..advisor.client import AdvisorCallFailed, AdvisorConfigured, AdvisorUnavailable
from ..advisor.client import ask as client_ask
from ..advisor.client import resolve_config, resolve_model
from ..advisor.context import AssembledContext, BudgetReport, assemble_context, parse_requested_artifact_ids, wrap_untrusted
from ..advisor.settings_store import AdvisorSettings, AdvisorSettingsStore, mask_api_key
from ..project_store import ProjectStore
from .deps import get_store

router = APIRouter(prefix="/advisor", tags=["advisor"])

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
    # Plumbing supports "generic" only -- modes land in the next unit
    # (M5 brief). A Literal here, not a bare str, so an unsupported mode
    # fails schema validation (422) instead of silently falling back.
    mode: Literal["generic"] = "generic"
    artifact_id: str | None = None
    question: str | None = None
    # The ask-by-ID follow-up turn (M5 brief): an id the model asked for
    # via a REQUEST_ARTIFACT: line on a prior call, sent back so this call
    # gets that artifact's full JSON instead of just its summary.
    follow_up_artifact_request: str | None = None


class AdvisorAskResponse(BaseModel):
    answer: str
    budget_report: BudgetReport
    requested_artifact_ids: list[str] = []


def _build_user_turn(assembled: AssembledContext, question: str | None) -> str:
    """Compose the single user-role message: facts + pre-score (engine-
    produced, unwrapped) then every untrusted block, then the user's own
    question -- wrapped exactly like artifact content, since a typed
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
    if assembled.untrusted_blocks:
        parts += ["", "=== PROJECT ARTIFACTS (user-authored content follows, delimited below) ==="]
        parts += assembled.untrusted_blocks
    parts += ["", "=== QUESTION ==="]
    if question:
        parts.append(wrap_untrusted("user_question", question))
    else:
        parts.append("(no question asked -- give a general read of what's above)")
    return "\n".join(parts)


@router.post("/ask", response_model=AdvisorAskResponse)
def ask(body: AdvisorAskRequest, store: ProjectStore = Depends(get_store)) -> AdvisorAskResponse:
    config = _require_configured(store)

    try:
        assembled = assemble_context(
            store,
            project_id=body.project_id,
            mode=body.mode,
            artifact_id=body.artifact_id,
            follow_up_artifact_id=body.follow_up_artifact_request,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    user_content = _build_user_turn(assembled, body.question)

    try:
        answer = client_ask(
            config,
            system=assembled.system_prompt_frame,
            user_content=user_content,
            max_output_tokens=assembled.budget_report.output_budget_tokens,
        )
    except AdvisorCallFailed as exc:
        raise HTTPException(status_code=_CALL_FAILED_STATUS_CODE, detail=f"The Anthropic API call failed: {exc}") from exc

    return AdvisorAskResponse(
        answer=answer.text,
        budget_report=assembled.budget_report,
        requested_artifact_ids=parse_requested_artifact_ids(answer.text),
    )


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
