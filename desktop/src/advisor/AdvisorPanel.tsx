import { useEffect, useState } from "react";
import { Button, Field, Panel, SelectInput, StatusPill, TextArea, TextInput, VerdictBanner } from "../design/components";
import { askAdvisor, getAdvisorStatus } from "../api/client";
import { ApiError } from "../api/errors";
import type {
  AdvisorAskRequest,
  AdvisorAskResponse,
  AdvisorMode,
  AdvisorProposal,
  AdvisorRemedyCandidate,
  AdvisorReviewCriterion,
  AdvisorTollgateAction,
  TollgatePhase,
} from "../api/types";
import { TOLLGATE_PHASES } from "../api/types";
import "./AdvisorPanel.css";

export interface AdvisorPanelProps {
  projectId: string;
  /** Threaded through from ToolScreen (M5 unit 2) -- not sent to the
   * engine (review mode derives the tool_id from artifact_id on its own
   * side), only used here for small UI text. */
  toolId: string;
  /** This tool's saved-artifact id, or undefined for T-13/T-14 (no saved
   * artifact -- see app/tools.ts's ToolDef.artifactId docstring). review /
   * help_me_think / explain all target "the current artifact," which is
   * this id; tollgate/remedy ignore it (their own context selectors look
   * up what they need by tool_id on the engine side). */
  artifactId?: string;
  onOpenSettings: () => void;
}

type StatusState =
  | { phase: "loading" }
  | { phase: "unconfigured" }
  | { phase: "configured"; model: string }
  | { phase: "unreachable"; message: string };

type AskState =
  | { phase: "idle" }
  | { phase: "asking" }
  | { phase: "answered"; response: AdvisorAskResponse }
  | { phase: "error"; message: string };

const MODE_LABELS: Record<AdvisorMode, string> = {
  generic: "Ask a question",
  review: "Review my artifact",
  help_me_think: "Help me think",
  explain: "Explain this",
  tollgate: "Tollgate review",
  remedy: "What do I do about this?",
};
const MODE_ORDER: AdvisorMode[] = ["generic", "review", "help_me_think", "explain", "tollgate", "remedy"];

const COST_BAND_TONE: Record<AdvisorRemedyCandidate["estimated_cost_band"], "pass" | "flag" | "fail"> = {
  low: "pass",
  medium: "flag",
  high: "fail",
};

/** Best-effort split of explain mode's prose into its three required parts
 * (advisor/modes.py's addendum: "what it means" / "what it does NOT mean" /
 * "what a Green Belt would do next"). Prose is never schema-validated
 * (explain has no output_parser, engine side) -- this is display polish
 * only; a model that doesn't use the exact headings just renders as plain
 * text below, nothing is ever hidden or lost. */
function splitExplainProse(text: string): { means: string; notMean: string; nextStep: string } | null {
  const markers: [key: "means" | "notMean" | "nextStep", re: RegExp][] = [
    ["means", /what it means/i],
    ["notMean", /what it does\s*not\s*mean/i],
    ["nextStep", /what a green belt would do next/i],
  ];
  const positions = markers.map(([key, re]) => ({ key, index: text.search(re) }));
  if (positions.some((p) => p.index === -1)) return null;
  const sorted = [...positions].sort((a, b) => a.index - b.index);
  const out: Record<string, string> = {};
  sorted.forEach((pos, i) => {
    const end = i + 1 < sorted.length ? sorted[i + 1].index : text.length;
    const chunk = text
      .slice(pos.index, end)
      .replace(/^[^a-zA-Z]*\d*\.?\s*/, "")
      .replace(/^(what it means|what it does\s*not\s*mean|what a green belt would do next)[:\-]?\s*/i, "")
      .trim();
    out[pos.key] = chunk;
  });
  if (!out.means || !out.notMean || !out.nextStep) return null;
  return out as { means: string; notMean: string; nextStep: string };
}

/** Best-effort clipboard copy (help_me_think / remedy's "copy for pasting"
 * affordance, PLAN §5.1 modes 2 and 5's v1 pattern) -- never throws; a
 * denied/unavailable clipboard just means the button silently doesn't
 * confirm, and the text is always ALSO visible on screen to select by
 * hand either way. */
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

function CopyButton({ text, testId }: { text: string; testId: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      variant="ghost"
      size="sm"
      data-testid={testId}
      onClick={async () => {
        const ok = await copyToClipboard(text);
        if (ok) {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        }
      }}
    >
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}

/** Collapsible "Advisor" panel on every ToolScreen (M5 brief) -- Layer 2,
 * strictly optional. The mode picker and every mode's input affordances
 * render regardless of configured state (M5 unit 2 brief: "with no key
 * configured, each mode's UI renders its input affordances and the
 * unconfigured state on submit paths") -- only the actual ask attempt is
 * gated on being configured. */
export function AdvisorPanel({ projectId, toolId, artifactId, onOpenSettings }: AdvisorPanelProps) {
  const [status, setStatus] = useState<StatusState>({ phase: "loading" });
  const [mode, setMode] = useState<AdvisorMode>("generic");
  const [question, setQuestion] = useState(""); // generic / review's optional question
  const [seedTopic, setSeedTopic] = useState(""); // help_me_think
  const [explainFocusText, setExplainFocusText] = useState(""); // explain's free-text fallback focus
  const [phase, setPhase] = useState<TollgatePhase>("Define"); // tollgate
  const [constraints, setConstraints] = useState(""); // remedy
  const [ask, setAsk] = useState<AskState>({ phase: "idle" });
  const [followUpPending, setFollowUpPending] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    getAdvisorStatus()
      .then((s) => {
        if (cancelled) return;
        setStatus(s.configured ? { phase: "configured", model: s.model } : { phase: "unconfigured" });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setStatus({ phase: "unreachable", message: err instanceof ApiError ? err.message : "Could not reach the engine." });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function handleModeChange(next: AdvisorMode) {
    setMode(next);
    setAsk({ phase: "idle" });
    setFollowUpPending([]);
  }

  function buildRequest(followUpArtifactId?: string): AdvisorAskRequest {
    const base: AdvisorAskRequest = { project_id: projectId, mode, artifact_id: artifactId };
    if (followUpArtifactId) base.follow_up_artifact_request = followUpArtifactId;
    if (mode === "generic" || mode === "review") {
      if (question.trim()) base.question = question.trim();
    } else if (mode === "help_me_think") {
      if (seedTopic.trim()) base.question = seedTopic.trim();
    } else if (mode === "explain") {
      if (explainFocusText.trim()) base.focus = { kind: "free_text", ref: explainFocusText.trim() };
    } else if (mode === "tollgate") {
      base.phase = phase;
    } else if (mode === "remedy") {
      if (constraints.trim()) base.question = constraints.trim();
    }
    return base;
  }

  async function submit(followUpArtifactId?: string) {
    setAsk({ phase: "asking" });
    try {
      const response = await askAdvisor(buildRequest(followUpArtifactId));
      setAsk({ phase: "answered", response });
      setFollowUpPending(response.requested_artifact_ids);
    } catch (err) {
      setAsk({ phase: "error", message: err instanceof ApiError ? err.message : "The advisor call failed." });
      setFollowUpPending([]);
    }
  }

  // Every mode's extra input is optional (tollgate's phase picker always
  // has a default selection) -- nothing here ever blocks submission the
  // way, say, a required field would; only an in-flight call disables it.

  return (
    <Panel
      title="Advisor"
      subtitle="Layer 2 -- optional AI advice"
      collapsible
      defaultOpen={false}
      className="sigma-advisor-panel"
      headerTestId="advisor-panel-toggle"
    >
      {status.phase === "loading" && <p className="sigma-advisor-panel__muted">Checking advisor status…</p>}

      {status.phase !== "loading" && (
        <div className="sigma-advisor-panel__body">
          <Field label="Mode" htmlFor="advisor-mode">
            <SelectInput
              id="advisor-mode"
              data-testid="advisor-mode-select"
              value={mode}
              onChange={(e) => handleModeChange(e.target.value as AdvisorMode)}
            >
              {MODE_ORDER.map((m) => (
                <option key={m} value={m}>
                  {MODE_LABELS[m]}
                </option>
              ))}
            </SelectInput>
          </Field>

          {(mode === "generic" || mode === "review") && (
            <Field label={mode === "review" ? "Anything specific to ask about? (optional)" : "Your question"} htmlFor="advisor-question">
              <TextArea
                id="advisor-question"
                data-testid="advisor-question"
                placeholder={mode === "review" ? "Optional -- leave blank for a full review" : "Ask about this project…"}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
              />
            </Field>
          )}

          {mode === "help_me_think" && (
            <Field label="Seed topic (optional)" htmlFor="advisor-seed-topic" helper="Point the brainstorm somewhere, or leave blank for a general pass.">
              <TextArea
                id="advisor-seed-topic"
                data-testid="advisor-help-me-think-seed-topic"
                placeholder="e.g. focus on the fixture-alignment branch"
                value={seedTopic}
                onChange={(e) => setSeedTopic(e.target.value)}
                rows={2}
              />
            </Field>
          )}

          {mode === "explain" && (
            <Field label="What would you like explained? (optional)" htmlFor="advisor-explain-focus" helper="Leave blank and the advisor picks the most important computed result.">
              <TextInput
                id="advisor-explain-focus"
                data-testid="advisor-explain-focus-input"
                placeholder="e.g. the Cpk value"
                value={explainFocusText}
                onChange={(e) => setExplainFocusText(e.target.value)}
              />
            </Field>
          )}

          {mode === "tollgate" && (
            <Field label="Phase" htmlFor="advisor-tollgate-phase">
              <SelectInput
                id="advisor-tollgate-phase"
                data-testid="advisor-tollgate-phase-select"
                value={phase}
                onChange={(e) => setPhase(e.target.value as TollgatePhase)}
              >
                {TOLLGATE_PHASES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </SelectInput>
            </Field>
          )}

          {mode === "remedy" && (
            <Field label="Constraints (optional)" htmlFor="advisor-remedy-constraints" helper="Budget, headcount, what can't change -- whatever's real.">
              <TextArea
                id="advisor-remedy-constraints"
                data-testid="advisor-remedy-constraints"
                placeholder="e.g. under $500, no new hires, can't touch the POS system"
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                rows={3}
              />
            </Field>
          )}

          {status.phase === "unreachable" && (
            <VerdictBanner tone="fail" headline="Could not reach the engine" detail={status.message} />
          )}

          {status.phase === "unconfigured" && (
            <div className="sigma-advisor-panel__unconfigured" data-testid="advisor-unconfigured">
              <p>
                Layer 1 (all tools, math, charts) runs entirely on your machine and sends nothing anywhere. The suite
                never needs this to be usable.
              </p>
              <p>
                The advisor is Layer 2 -- optional AI advice -- and isn&apos;t set up yet. When you use it, the current
                artifact and its computed results are sent to the Anthropic API.
              </p>
              <Button variant="secondary" size="sm" onClick={onOpenSettings} data-testid="advisor-open-settings">
                Set up the advisor
              </Button>
            </div>
          )}

          {status.phase === "configured" && (
            <div className="sigma-advisor-panel__configured" data-testid="advisor-configured">
              <p className="sigma-advisor-panel__muted">Model: {status.model}</p>
              <Button
                variant="primary"
                size="sm"
                onClick={() => submit()}
                disabled={ask.phase === "asking"}
                data-testid="advisor-ask-submit"
              >
                {ask.phase === "asking" ? "Asking…" : MODE_LABELS[mode]}
              </Button>

              {ask.phase === "error" && <VerdictBanner tone="fail" headline="The advisor call failed" detail={ask.message} />}

              {ask.phase === "answered" && (
                <AdvisorAnswer response={ask.response} toolId={toolId} />
              )}

              {followUpPending.length > 0 && (
                <div className="sigma-advisor-panel__followup" data-testid="advisor-requested-artifact-banner">
                  <p>The advisor asked to see {followUpPending[0]} in full -- send it?</p>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => submit(followUpPending[0])}
                    data-testid="advisor-requested-artifact-confirm"
                  >
                    Send {followUpPending[0]}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setFollowUpPending([])}>
                    No thanks
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}

function AdvisorAnswer({ response, toolId }: { response: AdvisorAskResponse; toolId: string }) {
  if (response.unstructured_fallback) {
    return (
      <div data-testid="advisor-answer">
        <VerdictBanner tone="flag" headline="The model returned unstructured output" detail="Showing its raw answer below." />
        <div className="sigma-advisor-panel__answer">{response.answer}</div>
      </div>
    );
  }

  if (response.mode === "review" && response.structured && "criteria" in response.structured) {
    return <ReviewResult criteria={response.structured.criteria} overallNote={response.structured.overall_note} />;
  }
  if (response.mode === "help_me_think" && response.structured && "proposals" in response.structured) {
    return <HelpMeThinkResult proposals={response.structured.proposals} />;
  }
  if (response.mode === "tollgate" && response.structured && "recommendation" in response.structured) {
    return (
      <TollgateResult
        recommendation={response.structured.recommendation}
        reasons={response.structured.reasons}
        actions={response.structured.actions}
      />
    );
  }
  if (response.mode === "remedy" && response.structured && "remedies" in response.structured) {
    return <RemedyResult remedies={response.structured.remedies} toolId={toolId} />;
  }

  // generic / explain -- plain prose.
  const explainParts = response.mode === "explain" ? splitExplainProse(response.answer) : null;
  if (explainParts) {
    return (
      <div className="sigma-advisor-panel__answer" data-testid="advisor-answer">
        <p>
          <strong>What it means:</strong> {explainParts.means}
        </p>
        <p>
          <strong>What it does NOT mean:</strong> {explainParts.notMean}
        </p>
        <p>
          <strong>What a Green Belt would do next:</strong> {explainParts.nextStep}
        </p>
      </div>
    );
  }
  return (
    <div className="sigma-advisor-panel__answer" data-testid="advisor-answer">
      {response.answer}
    </div>
  );
}

function ReviewResult({ criteria, overallNote }: { criteria: AdvisorReviewCriterion[]; overallNote: string }) {
  if (criteria.length === 0) {
    return <p className="sigma-advisor-panel__muted" data-testid="advisor-review-empty">Nothing to grade yet -- no rubric items for the current tool, or no artifact saved.</p>;
  }
  return (
    <div data-testid="advisor-review-result">
      <table className="sigma-advisor-panel__table">
        <thead>
          <tr>
            <th>Rubric item</th>
            <th>Verdict</th>
            <th>Fix</th>
          </tr>
        </thead>
        <tbody>
          {criteria.map((c) => (
            <tr key={c.criterion_id}>
              <td>{c.criterion_id}</td>
              <td>
                <StatusPill label={c.verdict === "pass" ? "Pass" : "Needs work"} tone={c.verdict === "pass" ? "pass" : "flag"} />
              </td>
              <td>{c.specific_fix || "--"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {overallNote && <p className="sigma-advisor-panel__overall-note">{overallNote}</p>}
    </div>
  );
}

function HelpMeThinkResult({ proposals }: { proposals: AdvisorProposal[] }) {
  if (proposals.length === 0) {
    return <p className="sigma-advisor-panel__muted">No proposals this time -- try a seed topic.</p>;
  }
  return (
    <ul className="sigma-advisor-panel__proposals" data-testid="advisor-proposals-list">
      {proposals.map((p, i) => (
        <li key={i} className="sigma-advisor-panel__proposal">
          <p>{p.text}</p>
          {p.evidence_question && <p className="sigma-advisor-panel__muted">What data would support this? {p.evidence_question}</p>}
          <CopyButton text={p.evidence_question ? `${p.text} -- ${p.evidence_question}` : p.text} testId={`advisor-proposal-copy-${i}`} />
        </li>
      ))}
    </ul>
  );
}

function TollgateResult({ recommendation, reasons, actions }: { recommendation: string; reasons: string[]; actions: AdvisorTollgateAction[] }) {
  const tone = recommendation === "go" ? "pass" : recommendation === "go_with_actions" ? "flag" : "fail";
  const headline =
    recommendation === "go" ? "Go" : recommendation === "go_with_actions" ? "Go, with actions" : "No go";
  return (
    <div data-testid="advisor-tollgate-result">
      <VerdictBanner
        tone={tone}
        headline={headline}
        detail="This is an advisor, not a lock -- you decide at the gate."
      />
      {reasons.length > 0 && (
        <ul className="sigma-advisor-panel__reasons">
          {reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}
      {actions.length > 0 && (
        <ul className="sigma-advisor-panel__actions" data-testid="advisor-tollgate-actions">
          {actions.map((a, i) => (
            <li key={i}>
              {a.action} <span className="sigma-advisor-panel__muted">({a.tied_to_question_id})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function RemedyResult({ remedies, toolId }: { remedies: AdvisorRemedyCandidate[]; toolId: string }) {
  if (remedies.length === 0) {
    return <p className="sigma-advisor-panel__muted">No remedies yet -- verified causes on the fishbone (T-15) are needed first.</p>;
  }
  const draftText = remedies
    .map(
      (r, i) =>
        `${i + 1}. ${r.title} (linked causes: ${r.cause_ids.join(", ")}; impact ~3, effort ~3 -- adjust in the matrix)\n   ${r.why_it_fits_the_verified_cause}`,
    )
    .join("\n\n");
  return (
    <div data-testid="advisor-remedy-result">
      <div className="sigma-advisor-panel__remedy-header">
        <p>Ranked remedies, tied to your verified causes:</p>
        <CopyButton text={draftText} testId="advisor-remedy-draft-copy" />
      </div>
      <p className="sigma-advisor-panel__muted">
        "Start solution matrix from these" copies a draft list (title, linked cause ids, one line of reasoning per
        remedy) -- paste it into {toolId === "T-18" ? "this" : "the Solution Selection Matrix (T-18)"} form and edit
        from there; the advisor never saves anything on its own.
      </p>
      <ol className="sigma-advisor-panel__remedy-cards" data-testid="advisor-remedy-cards">
        {remedies.map((r, i) => (
          <li key={i} className="sigma-advisor-panel__remedy-card">
            <div className="sigma-advisor-panel__remedy-card-title">
              {r.title} <StatusPill label={r.estimated_cost_band} tone={COST_BAND_TONE[r.estimated_cost_band]} />
            </div>
            <p>{r.why_it_fits_the_verified_cause}</p>
            <p className="sigma-advisor-panel__muted">Causes: {r.cause_ids.join(", ")}</p>
            {r.risks && (
              <p>
                <strong>Risks:</strong> {r.risks}
              </p>
            )}
            {r.pilot_first && (
              <p>
                <strong>Pilot first:</strong> {r.pilot_first}
              </p>
            )}
            {r.how_youd_know_it_worked && (
              <p>
                <strong>How you'd know it worked:</strong> {r.how_youd_know_it_worked}
              </p>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
