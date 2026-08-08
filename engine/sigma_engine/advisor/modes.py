"""The five advisor modes (M5 unit 2, PLAN §5.1's exact five: review,
help_me_think, explain, tollgate, remedy) on top of the M5 unit 1 plumbing
(client.py, context.py, routes/advisor.py, settings_store.py) -- honoring
that plumbing's conventions exactly rather than forking them:

- wrap_untrusted() (context.py) for every mode-specific piece of
  user-authored text this unit adds (remedy's constraints, help_me_think's
  seed topic, explain's focus -- all folded into routes/advisor.py's
  existing `question` wrapping, see that file's _build_user_turn) and for
  any user-typed field a context selector surfaces outside the normal
  current-artifact/summary path (remedy's charter-baseline block below).
- MODE_ADDENDA (context.py) stays the one extension point for per-mode
  system-frame text -- _register() below ADDS this unit's five addenda to
  that same dict rather than inventing a second one; "generic" keeps its
  exact M5-unit-1 addendum, re-registered here too so routes/advisor.py's
  dispatch is uniform across all six mode names.
- REQUEST_ARTIFACT ask-by-ID marker (context.py) -- untouched; every mode
  below inherits it for free through build_system_prompt_frame(mode).
- Budget priority order (context.py) -- untouched; the one new tier this
  unit adds (mode_block) rides with the system frame, see context.py's
  assemble_context docstring for why that's safe.
- Prescore-first -- every context selector below either reuses
  assemble_context's own current-artifact prescore (review, help_me_think,
  explain, remedy's T-15) or calls context.run_prescore_for_artifact()
  directly for additional tools (tollgate's phase-tool loop), never
  re-derives a check by hand.

This module is a registry, not a router: MODE_REGISTRY maps a mode name to
a ModeSpec{addendum, context_selector, output_parser, postprocess_structured};
routes/advisor.py is the one caller that walks it (resolve spec -> call
context_selector -> call client.ask or structured.run_structured_mode
depending on output_parser -> call postprocess_structured on a successful
structured parse, if the mode registered one -- see that file for the
dispatch). postprocess_structured (M5 exit critic, Fix 5) is the one
extension this module adds past M5 unit 2: a deterministic pass over an
already-parsed structured response, run by routes/advisor.py right after
structured.py returns -- remedy mode's own cause_ids validation
(_flag_unverified_remedy_causes below) is the only user of it today, but
it's registered generically on ModeSpec so routes/advisor.py never
special-cases remedy by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Sequence

from pydantic import BaseModel, Field

from ..artifacts.a3 import TOLLGATE_QUESTIONS, TollgatePhase
from ..gates import GateResult, build_project_snapshot
from ..gates import check as gate_check
from ..project_store import ProjectStore
from . import rubric_items
from .context import (
    DEFAULT_INPUT_BUDGET_TOKENS,
    DEFAULT_OUTPUT_BUDGET_TOKENS,
    MAX_QUESTION_LENGTH,
    MODE_ADDENDA,
    AssembledContext,
    assemble_context,
    run_prescore_for_artifact,
    wrap_untrusted,
)

# ---- A request-side type shared with routes/advisor.py's AdvisorAskRequest ----


class AdvisorFocusRef(BaseModel):
    """explain mode's optional focus (PLAN §5.1 mode 3: "request carries an
    optional focus: {kind, path/id}"). `ref` is ALWAYS user-influenced --
    either a path the desktop read off its own result state (still
    something the app assembled from a screen the user was looking at, not
    engine-authored) or, in the free-text-fallback case the M5 unit 2
    brief's Desktop section names, literally user-typed -- so both `kind`
    and `ref` get folded into the same wrap_untrusted()-wrapped question
    text every other mode-specific input uses (routes/advisor.py), never
    treated as trusted just because `kind` might be a fixed short string
    on the happy path. `ref` carries the same MAX_QUESTION_LENGTH cap as
    AdvisorAskRequest.question (Fix 6, M5 exit critic) -- it ends up folded
    into that same question text, so it needs the same ceiling."""

    kind: str = Field(min_length=1)
    ref: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)


# ---- Phase -> tool_ids, hand-mirrored from PLAN §4.1's DMAIC table the
# same way desktop/src/app/tools.ts's TOOLS already mirrors it (that
# file's own comment: "mirrored by hand ... 25 tools, phases + ids + names
# verbatim from that table"). Intake (T-01) has no tollgate -- a3.py's
# TollgatePhase covers Define..Wrap only, and this table matches that. ----

PHASE_TOOL_IDS: dict[TollgatePhase, tuple[str, ...]] = {
    "Define": ("T-02", "T-03", "T-04", "T-05"),
    "Measure": ("T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14"),
    "Analyze": ("T-15", "T-16", "T-17"),
    "Improve": ("T-18", "T-19", "T-20"),
    "Control": ("T-21", "T-22", "T-23", "T-24"),
    "Wrap": ("T-25",),
}

# Phase -> the gate_id(s) gating LEAVING that phase (gates.GATE_TABLE is
# keyed by (from_phase, to_phase), not by a single phase, and Measure has
# two gates leaving it -- both included). "Wrap" has none: Wrap is the
# last phase, so gates.GATE_TABLE defines no transition out of it.
TOLLGATE_PHASE_GATE_IDS: dict[TollgatePhase, tuple[str, ...]] = {
    "Define": ("define_to_measure",),
    "Measure": ("measure_to_analyze", "measure_capability_language_requires_msa_pass"),
    "Analyze": ("analyze_to_improve",),
    "Improve": ("improve_to_control",),
    "Control": ("control_to_wrap",),
    "Wrap": (),
}


# ================================================================
# Response models -- one per structured mode (review, help_me_think,
# tollgate, remedy). "explain" is prose-only (no response model, no
# retry -- see routes/advisor.py's dispatch). Every field the model must
# fill carries Field(min_length=1) or an equivalent non-blank constraint
# so a technically-valid-JSON-but-empty answer still fails validation and
# earns its one retry, rather than silently shipping a blank card to the UI.
# ================================================================


class ReviewCriterion(BaseModel):
    criterion_id: str = Field(min_length=1)  # the rubric item id given in MODE CONTEXT, e.g. "R-DEF-05"
    verdict: Literal["pass", "needs_work"]
    specific_fix: str = ""  # required in substance by the addendum when verdict == "needs_work"; not schema-enforced (see modes.py docstring on judgment vs schema)


class ReviewResponse(BaseModel):
    criteria: list[ReviewCriterion] = Field(default_factory=list)
    overall_note: str = ""


class Proposal(BaseModel):
    text: str = Field(min_length=1)
    # Required in substance for a T-15 proposal (PLAN §5.1 mode 2: "make
    # the mode addendum require it") -- enforced by the addendum's prompt
    # instruction, not by a schema rule keyed on which tool_id is current
    # (the response model has no way to see that; see _help_me_think_addendum).
    evidence_question: str | None = None


class HelpMeThinkResponse(BaseModel):
    proposals: list[Proposal] = Field(default_factory=list)


class TollgateAction(BaseModel):
    action: str = Field(min_length=1)
    tied_to_question_id: str = Field(min_length=1)


class TollgateResponse(BaseModel):
    recommendation: Literal["go", "go_with_actions", "no_go"]
    reasons: list[str] = Field(default_factory=list)
    actions: list[TollgateAction] = Field(default_factory=list)


class RemedyCandidate(BaseModel):
    title: str = Field(min_length=1)
    why_it_fits_the_verified_cause: str = Field(min_length=1)
    # Structured alongside the prose field above (PLAN §5.1 mode 5: "must
    # reference a cause id") so the desktop's "start solution matrix from
    # these" affordance has a real T-15 cause_id to carry into a draft
    # T-18 Solution.linked_cause_ids -- min_length=1 makes "references a
    # cause id" a schema fact, not just a prompt request.
    cause_ids: list[str] = Field(min_length=1)
    estimated_cost_band: Literal["low", "medium", "high"]
    risks: str = ""
    pilot_first: str = ""
    how_youd_know_it_worked: str = ""
    # Fix 5 (M5 exit critic): cause_ids above is model-authored text --
    # nothing stops the model from citing a cause_id that was never
    # verified (still candidate/investigating/ruled_out) or doesn't exist
    # on the fishbone at all. Filled by _flag_unverified_remedy_causes
    # AFTER parsing, deterministically -- NEVER by the model itself (the
    # addendum's JSON shape example never mentions this field, so a
    # well-behaved model never emits it; if some model output did include
    # it anyway, the post-parse check below overwrites it regardless, so
    # nothing here can be gamed). The subset of cause_ids that did NOT
    # match a currently VERIFIED cause_id on the fishbone -- empty when
    # every cited id matched.
    unverified_cause_refs: list[str] = Field(default_factory=list)


class RemedyResponse(BaseModel):
    remedies: list[RemedyCandidate] = Field(default_factory=list)
    # Response-level companion to unverified_cause_refs (Fix 5) -- "" unless
    # at least one remedy was flagged, in which case this is the one
    # plain-English sentence the UI shows once instead of repeating the
    # explanation on every flagged card.
    unverified_cause_note: str = ""


# ================================================================
# Per-mode addenda (context.py's MODE_ADDENDA extension point). Every
# structured mode's addendum both names its output shape AND includes it
# inline (belt-and-braces with structured.py's schema-in-the-retry-prompt:
# fewer malformed first attempts means fewer retries means lower cost).
# ================================================================

_REVIEW_ADDENDUM = (
    "Mode: review. The user wants their CURRENT artifact graded against the rubric items listed in the "
    "\"=== MODE CONTEXT ===\" section below (the same rubric text the tool's own \"what good looks like\" panel "
    "restates, docs/green-belt-rubric.md). Grade ONLY the rubric items given to you there, one verdict per item, "
    "based strictly on what the current artifact's own content (inside <artifact_content> tags) and its pre-score "
    "results actually show -- never on assumed best practice the artifact doesn't evidence. If MODE CONTEXT says no "
    "rubric items are mapped to this tool, or there is no current artifact, return an empty criteria list and say so "
    "plainly in overall_note -- do not invent criteria.\n\n"
    "Respond with EXACTLY one fenced ```json code block, and nothing else meaningfully outside it, containing an "
    "object with this shape:\n"
    '{"criteria": [{"criterion_id": "<the rubric item id exactly as given, e.g. R-DEF-05>", '
    '"verdict": "pass" or "needs_work", "specific_fix": "<one or two sentences, concrete and actionable; empty '
    'string when verdict is pass>"}], "overall_note": "<a short overall read, one or two sentences>"}\n\n'
    "Include exactly one criteria entry per rubric item given to you, in the order given. A \"needs_work\" verdict "
    "must always carry a non-empty specific_fix naming the concrete gap."
)

_HELP_ME_THINK_ADDENDUM = (
    "Mode: help_me_think. Socratic brainstorm for a divergent tool (fishbone causes / 5-Whys on T-15, VoC themes "
    "on T-05, solution ideas on T-18 -- whichever the current artifact below is). You PROPOSE candidates; you never "
    "decide which are right. The user reviews every proposal in the app's own UI and accepts or rejects it there -- "
    "nothing you propose enters any artifact automatically; the advisor never writes artifacts.\n\n"
    "Respond with EXACTLY one fenced ```json code block containing an object with this shape:\n"
    '{"proposals": [{"text": "<one candidate cause / theme / idea, plain English, one sentence>", '
    '"evidence_question": "<see rule below, or null>"}]}\n\n'
    "RULE: if the current artifact is a T-15 fishbone, every proposal is a candidate CAUSE, and evidence_question "
    "is REQUIRED and must not be null on every proposal -- your own \"what data would support this?\" question for "
    "that specific cause. For every other divergent tool, evidence_question may be null.\n\n"
    "Offer a handful of genuinely different proposals, not near-duplicates restating the same idea. Ground every "
    "proposal in what the artifact/facts/pre-score below actually show, not generic textbook filler."
)

_EXPLAIN_ADDENDUM = (
    "Mode: explain. Explain ONE computed result from the CURRENT artifact in plain English for a Green Belt "
    "student. If the user named a specific result to explain, it is described in the QUESTION section below "
    "(delimited as untrusted user/UI-sourced text); if none was named, explain the single most important computed "
    "result the FACTS or PRE-SCORE sections carry. Every number you cite must come from FACTS, PRE-SCORE, or the "
    "current artifact's own content below -- you never calculate or restate a number that was not given to you.\n\n"
    "Respond in prose, structured as exactly three short, clearly labeled parts:\n"
    "1. What it means -- the plain-English read of the number/result.\n"
    "2. What it does NOT mean -- the nearby misreading a student would make.\n"
    "3. What a Green Belt would do next -- the concrete next step this result points to.\n\n"
    "Do not respond with a fenced JSON block for this mode -- plain labeled prose only."
)

_TOLLGATE_ADDENDUM = (
    "Mode: tollgate. You are playing the Champion at a phase-exit tollgate review, for the phase named in the "
    "\"=== MODE CONTEXT ===\" section below. You are given that phase's standard tollgate questions, SUMMARIES "
    "(not full dumps) of that phase's tools, that phase's pre-score results, and this project's automated gate-"
    "check output. Weigh the standard questions against what is actually in front of you and give a "
    "recommendation. The user can always override you -- you are advice, not a lock.\n\n"
    "If you genuinely need a phase tool's full content (not just its summary) to judge fairly, ask for it with a "
    "REQUEST_ARTIFACT line (see the convention above) instead of guessing.\n\n"
    "Respond with EXACTLY one fenced ```json code block containing an object with this shape:\n"
    '{"recommendation": "go" or "go_with_actions" or "no_go", "reasons": ["<short reason>", ...], '
    '"actions": [{"action": "<a concrete, assignable action>", '
    '"tied_to_question_id": "<the tollgate question id this action answers, e.g. define-2>"}]}\n\n'
    "\"go_with_actions\" or \"no_go\" must carry at least one reason. Every action must be concrete enough that a "
    "named person could do it, and must name which tollgate question it answers."
)

_REMEDY_ADDENDUM = (
    "Mode: remedy -- the flagship advisor mode. The user has verified causes on their fishbone (T-15, given to you "
    "in full below, with evidence) and wants candidate remedies. You are also given the charter summary, the FMEA "
    "summary if one exists, relevant baseline/goal numbers, and the current solution matrix (T-18) if one has been "
    "started -- use all of it. If the user typed constraints (budget, headcount, what can't change), they are in "
    "the QUESTION section below, delimited as untrusted user text; honor them.\n\n"
    "Propose remedies ONLY for causes whose status is verified (never for a candidate/investigating/ruled_out "
    "cause) -- every remedy must reference at least one real verified cause_id from the fishbone given to you. If "
    "a T-18 solution matrix is shown and already covers a remedy you were about to propose, say so instead of "
    "repeating it.\n\n"
    "Respond with EXACTLY one fenced ```json code block containing an object with this shape:\n"
    '{"remedies": [{"title": "<short remedy name>", '
    '"why_it_fits_the_verified_cause": "<ties this remedy to a specific verified cause, naming it>", '
    '"cause_ids": ["<verified cause_id from the fishbone below>", ...], '
    '"estimated_cost_band": "low" or "medium" or "high", "risks": "<what could go wrong>", '
    '"pilot_first": "<the smallest first pilot of this remedy>", '
    '"how_youd_know_it_worked": "<the metric/signal that would prove it>"}]}\n\n'
    "Rank the remedies with the best-fitting, most-actionable first. This output feeds a draft solution matrix the "
    "user reviews and edits themselves -- you are proposing, never saving anything."
)


# ================================================================
# Context selectors -- each one calls into context.py's assemble_context()
# (module docstring: extend, don't fork). Uniform keyword signature across
# all six so routes/advisor.py can dispatch without a per-mode branch;
# each selector ignores the kwargs it doesn't need.
# ================================================================

ModeContextSelector = Callable[..., AssembledContext]


def _generic_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    """"generic" (M5 unit 1) and "help_me_think"/"explain" (this unit)
    share this exact shape: the current artifact in full, its prescore,
    its facts -- no mode-specific extra_block. Same call
    routes/advisor.py's ask() made directly before this unit existed."""
    return assemble_context(
        store, project_id=project_id, mode="generic", artifact_id=artifact_id,
        follow_up_artifact_id=follow_up_artifact_id, question=question,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


def _help_me_think_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    return assemble_context(
        store, project_id=project_id, mode="help_me_think", artifact_id=artifact_id,
        follow_up_artifact_id=follow_up_artifact_id, question=question,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


def _explain_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    return assemble_context(
        store, project_id=project_id, mode="explain", artifact_id=artifact_id,
        follow_up_artifact_id=follow_up_artifact_id, question=question,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


def _review_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    """PLAN §5.1 mode 1: full current artifact + its prescore (both
    already assemble_context's default current-artifact behavior) + the
    relevant rubric items' text, looked up from rubric_items.py by the
    current artifact's tool_id. Engine-authored (never wrapped untrusted --
    see AssembledContext.mode_block's docstring)."""
    extra_block = ""
    if artifact_id is not None:
        meta = store.load_project(project_id)  # FileNotFoundError propagates -- same 404 contract as assemble_context
        entry = meta.artifact_index.get(artifact_id)
        if entry is not None:
            extra_block = rubric_items.render_rubric_items_block(entry.tool_id)
        # entry is None (a bad artifact_id) is left for assemble_context's
        # own lookup below to raise FileNotFoundError -- one error path.
    return assemble_context(
        store, project_id=project_id, mode="review", artifact_id=artifact_id,
        follow_up_artifact_id=follow_up_artifact_id, extra_block=extra_block, question=question,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


def _render_gate_result(gate_id: str, result: GateResult) -> str:
    """One compact line per gate. gate_id/status/`reason`/`missing` are all
    engine-controlled (`reason` is always GATE_TABLE.description or a
    hardcoded message -- never user text); `override_reason` is the ONE
    field that isn't: gates.check() sets it from OverrideLogEntry.reason
    (gates.py), which is the free-text justification a human typed into
    POST /gates/override -- genuinely user-authored, so it gets the same
    wrap_untrusted() treatment as any other user-typed field surfacing
    outside the normal artifact path (this module's own docstring),
    exactly the way render_prescore_line wraps only `detail` and leaves
    check_id/tool_id/status bare. Caught by
    test_tollgate_injection_defense_on_an_override_reason."""
    bits = [f"{gate_id}: {result.status}"]
    if result.reason:
        bits.append(result.reason)
    if result.missing:
        bits.append(f"missing: {', '.join(result.missing)}")
    if result.overridden:
        wrapped = wrap_untrusted(f"{gate_id}-override-reason", result.override_reason or "")
        bits.append(f"overridden ({wrapped})")
    return " -- ".join(bits)


def _tollgate_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    """PLAN §5.1 mode 4: the phase's TOLLGATE_QUESTIONS (a3.py, REUSED --
    see test_advisor_modes.py's reuse assertion), artifact SUMMARIES for
    the phase's tools (assemble_context's summary_tool_ids, NOT full
    dumps), all of those tools' prescore results, and gates/check output.
    No single artifact is "current" here (no artifact_id) -- PLAN §5.1's
    request shape for this mode is just {phase}."""
    if phase is None:
        raise ValueError("tollgate mode requires a phase")

    meta = store.load_project(project_id)  # FileNotFoundError propagates -- 404 at the route layer
    phase_tool_ids = PHASE_TOOL_IDS.get(phase, ())

    questions = TOLLGATE_QUESTIONS[phase]  # a3.py's own dict -- reused, not copied
    questions_text = "\n".join(f"  {q.question_id}: {q.text}" for q in questions)

    prescore_lines: list[str] = []
    for tool_id in phase_tool_ids:
        data = store.latest_artifact_for_tool(project_id, meta, tool_id)
        if data is None:
            continue
        block = run_prescore_for_artifact(tool_id, data, data["artifact_id"])
        if block:
            prescore_lines.append(block)
    prescore_text = "\n".join(prescore_lines) if prescore_lines else "(no phase tool has a saved artifact yet, or none has a registered prescore)"

    overrides = store.list_overrides(project_id)
    snapshot = build_project_snapshot(store, project_id)
    gate_lines = [_render_gate_result(gid, gate_check(gid, snapshot, overrides)) for gid in TOLLGATE_PHASE_GATE_IDS.get(phase, ())]
    gate_text = "\n".join(f"  {line}" for line in gate_lines) if gate_lines else "  (no automated gate is defined for this phase yet)"

    extra_block = (
        f"Tollgate review for phase: {phase}\n\n"
        f"Standard tollgate questions:\n{questions_text}\n\n"
        f"Phase-tool pre-score results:\n{prescore_text}\n\n"
        f"Gate-check output:\n{gate_text}"
    )

    return assemble_context(
        store, project_id=project_id, mode="tollgate", artifact_id=None,
        follow_up_artifact_id=follow_up_artifact_id, summary_tool_ids=phase_tool_ids,
        extra_block=extra_block, question=question,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


_CHARTER_BASELINE_FIELDS_NOTE = (
    "(charter fields mix engine-safe numbers with user-typed labels/units -- wrapped below like any other "
    "artifact content, not split apart)"
)


def _charter_baseline_block(artifact_id: str, data: dict[str, Any]) -> str:
    """remedy's "relevant computed baselines" (PLAN §5.1 mode 5), pulled
    from the charter's own declared goal/problem-statement/business-impact
    numbers -- the one thing the generic summarize_artifact() would hide:
    SmartGoal alone has 7 top-level fields, one field short of
    summarize_artifact's <=6-scalar-field inline-render cutoff
    (context.py), so a plain charter summary would show "goal: 7
    field(s)" instead of the actual baseline/target values. This is
    exactly the "reasonable upgrade... layered on top of [the generic
    summarizer], rather than replacing it" summarize_artifact's own
    docstring anticipates for the modes unit.

    Mixes user-typed strings (metric_name, units, the problem statement
    text) with plain numbers -- wrapped untrusted AS A WHOLE by the
    caller (never split into a "the numbers are safe" / "the labels
    aren't" pair -- simpler, and always the safe side of the line)."""
    problem = data.get("problem_statement") or {}
    magnitude = problem.get("magnitude") or {}
    goal = data.get("goal") or {}
    impact = data.get("business_impact") or {}
    lines = [f"Charter {artifact_id} -- declared baseline/goal/impact:"]
    if magnitude:
        lines.append(f"  problem magnitude: {magnitude.get('number')} {magnitude.get('unit', '')} ({magnitude.get('period', '')})")
    if goal:
        lines.append(
            f"  goal metric: {goal.get('metric_name')} -- baseline {goal.get('baseline_value')}, "
            f"target {goal.get('target_value')} {goal.get('unit', '')} by {goal.get('target_date')}"
        )
        if goal.get("consequential_metrics"):
            lines.append(f"  guardrail metrics: {', '.join(goal['consequential_metrics'])}")
    if impact:
        lines.append(f"  business impact: {impact.get('amount')} {impact.get('unit', '')} ({impact.get('basis', '')})")
    lines.append(f"  {_CHARTER_BASELINE_FIELDS_NOTE}")
    return "\n".join(lines)


def _remedy_context(
    store: ProjectStore,
    *,
    project_id: str,
    artifact_id: str | None = None,
    follow_up_artifact_id: str | None = None,
    phase: TollgatePhase | None = None,
    focus: AdvisorFocusRef | None = None,
    question: str | None = None,
    input_budget_tokens: int = DEFAULT_INPUT_BUDGET_TOKENS,
    output_budget_tokens: int = DEFAULT_OUTPUT_BUDGET_TOKENS,
) -> AssembledContext:
    """PLAN §5.1 mode 5 (the flagship): charter summary, the verified
    causes WITH evidence from the current T-15 (full -- set as the
    "current" artifact so it also gets prescore+facts for free), FMEA
    summary if present, relevant computed baselines (charter's declared
    numbers, see _charter_baseline_block), and the T-18 artifact if
    started (full, via additional_full_artifact_ids). `artifact_id` from
    the request is deliberately ignored here -- remedy always targets the
    project's own T-15/T-03/T-16/T-18 by tool_id, regardless which tool
    screen the advisor panel happened to be open on when the user asked."""
    meta = store.load_project(project_id)  # FileNotFoundError propagates -- 404 at the route layer

    fishbone_data = store.latest_artifact_for_tool(project_id, meta, "T-15")
    fishbone_id = fishbone_data["artifact_id"] if fishbone_data else None
    # Fix 5 (M5 exit critic): the current fishbone's VERIFIED cause ids,
    # derived directly from the raw causes list (never from the model's
    # own answer) -- carried through to AssembledContext so routes/
    # advisor.py can flag any RemedyCandidate.cause_id that doesn't match
    # one of these AFTER the model responds. See
    # _flag_unverified_remedy_causes below and AssembledContext.
    # verified_cause_ids's own docstring.
    verified_cause_ids = tuple(
        cause["cause_id"]
        for cause in (fishbone_data or {}).get("causes", [])
        if cause.get("status") == "verified" and cause.get("cause_id")
    )

    solution_matrix_data = store.latest_artifact_for_tool(project_id, meta, "T-18")
    solution_matrix_id = solution_matrix_data["artifact_id"] if solution_matrix_data else None
    additional_full = [solution_matrix_id] if solution_matrix_id else []

    charter_data = store.latest_artifact_for_tool(project_id, meta, "T-03")

    notes: list[str] = []
    if fishbone_id is None:
        notes.append(
            "No fishbone (T-15) has been saved in this project yet -- verified causes with evidence are required "
            "before the advisor can propose grounded remedies. Say so instead of inventing causes."
        )
    if charter_data is None:
        notes.append("No charter (T-03) has been saved in this project yet -- no baseline/goal numbers to work from.")
    elif charter_data.get("artifact_id"):
        # wrap_untrusted() here is load-bearing, not decorative: this block
        # embeds user-typed charter strings (metric_name, units, the
        # problem-statement text) -- see _charter_baseline_block's own
        # docstring. Caught by
        # test_remedy_context_charter_baseline_block_is_wrapped_untrusted.
        note_text = _charter_baseline_block(charter_data["artifact_id"], charter_data)
        notes.append(wrap_untrusted(f"{charter_data['artifact_id']}-baseline", note_text))

    extra_block = "\n\n".join(notes)

    return assemble_context(
        store, project_id=project_id, mode="remedy", artifact_id=fishbone_id,
        follow_up_artifact_id=follow_up_artifact_id, additional_full_artifact_ids=additional_full,
        summary_tool_ids=("T-03", "T-16"), extra_block=extra_block, question=question,
        verified_cause_ids=verified_cause_ids,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


# ================================================================
# Post-response validation (Fix 5, M5 exit critic). Runs AFTER
# structured.py has already parsed the model's answer into RemedyResponse
# -- a deterministic check, not a prompt instruction, so it can't be
# talked around by a model that ignores the addendum's "ONLY verified
# causes" rule.
# ================================================================


def _flag_unverified_remedy_causes(response: RemedyResponse, verified_cause_ids: Sequence[str]) -> RemedyResponse:
    """The T-15 fishbone is in the SAME request context remedy mode already
    assembled (assembled.verified_cause_ids, computed by _remedy_context
    above from the fishbone's own raw causes list -- never from the
    model's answer). A remedy citing a cause_id that isn't in that set --
    invented outright, or a real cause_id that's still candidate/
    investigating/ruled_out -- is KEPT, never silently dropped (the
    model's reasoning may still be useful to a human reviewing it), but
    flagged: unverified_cause_refs names exactly which of its cause_ids
    didn't match, and the response carries one plain-English note whenever
    ANY remedy was flagged. AdvisorPanel.tsx renders the flag on the card
    and excludes flagged remedies from the T-18 paste draft by default."""
    verified = set(verified_cause_ids)
    any_flagged = False
    for remedy in response.remedies:
        unmatched = [cause_id for cause_id in remedy.cause_ids if cause_id not in verified]
        if unmatched:
            remedy.unverified_cause_refs = unmatched
            any_flagged = True
    if any_flagged:
        response.unverified_cause_note = (
            "One or more remedies cite a cause id that is not a currently VERIFIED cause on the fishbone "
            "(invented, or still candidate/investigating/ruled_out). Flagged remedies are excluded from the "
            "paste-ready draft by default -- review them before acting on them."
        )
    return response


def _postprocess_remedy(response: BaseModel, assembled: AssembledContext) -> BaseModel:
    assert isinstance(response, RemedyResponse)  # guaranteed by ModeSpec pairing this with output_parser=RemedyResponse
    return _flag_unverified_remedy_causes(response, assembled.verified_cause_ids)


# ================================================================
# The registry (module docstring). ModeSpec.output_parser is the
# structured mode's Pydantic response model class, or None for a
# prose-only mode -- routes/advisor.py's ask() branches on that, not on
# the mode name, so adding a sixth structured mode later needs no new
# if-branch there.
# ================================================================


@dataclass(frozen=True)
class ModeSpec:
    addendum: str
    context_selector: ModeContextSelector
    output_parser: type[BaseModel] | None
    # Optional deterministic pass over an already-parsed structured
    # response (Fix 5) -- routes/advisor.py calls this right after
    # structured.py returns a non-None `parsed`, passing the SAME
    # AssembledContext the context_selector built (so it can reach
    # mode-specific side-channel data, e.g. verified_cause_ids, with no
    # second store read) plus the parsed response; returns the (possibly
    # mutated) response. None for every mode that needs no such check.
    postprocess_structured: Callable[[BaseModel, AssembledContext], BaseModel] | None = None


MODE_REGISTRY: dict[str, ModeSpec] = {}


def _register(name: str, spec: ModeSpec) -> None:
    """Populates both registries from one ModeSpec: context.py's
    MODE_ADDENDA (the extension point build_system_prompt_frame reads --
    module docstring) and this module's own MODE_REGISTRY (what
    routes/advisor.py walks for context selection + output parsing)."""
    MODE_ADDENDA[name] = spec.addendum
    MODE_REGISTRY[name] = spec


_register("generic", ModeSpec(addendum=MODE_ADDENDA["generic"], context_selector=_generic_context, output_parser=None))
_register("review", ModeSpec(addendum=_REVIEW_ADDENDUM, context_selector=_review_context, output_parser=ReviewResponse))
_register(
    "help_me_think",
    ModeSpec(addendum=_HELP_ME_THINK_ADDENDUM, context_selector=_help_me_think_context, output_parser=HelpMeThinkResponse),
)
_register("explain", ModeSpec(addendum=_EXPLAIN_ADDENDUM, context_selector=_explain_context, output_parser=None))
_register("tollgate", ModeSpec(addendum=_TOLLGATE_ADDENDUM, context_selector=_tollgate_context, output_parser=TollgateResponse))
_register(
    "remedy",
    ModeSpec(
        addendum=_REMEDY_ADDENDUM, context_selector=_remedy_context, output_parser=RemedyResponse,
        postprocess_structured=_postprocess_remedy,
    ),
)
