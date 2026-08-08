import { useEffect, useState } from "react";
import type { PillTone } from "../design/components";
import { Button, Field, Panel, SelectInput, StatusPill, TextArea, TextInput, VerdictBanner } from "../design/components";
import { askAdvisor, getAdvisorExport, getAdvisorStatus, loadArtifact, validateAdvisor } from "../api/client";
import { ApiError } from "../api/errors";
import { ADVISOR_PRIVACY_STATEMENT } from "./privacyStatement";
import type {
  AdvisorAskRequest,
  AdvisorAskResponse,
  AdvisorExportResponse,
  AdvisorMode,
  AdvisorProposal,
  AdvisorRemedyCandidate,
  AdvisorReviewCriterion,
  AdvisorTollgateAction,
  TollgatePhase,
  ValidatorFlag,
  ValidatorReport,
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

/** "Check my claims" (PLAN §5.3.6's validator pass, M5 unit 3) checks the
 * last SAVED version of this tool's artifact, not necessarily whatever is
 * currently unsaved in the form below it -- there is no single shared save
 * path across the 24 tool forms (each builds its own save body inline; see
 * the build report), so this reuses the same "current artifact" concept
 * review/help_me_think/explain already read off `artifactId`, rather than
 * threading live draft state through every tool screen. In practice this
 * is rarely far from what's about to be saved. */
type ValidateState =
  | { phase: "idle" }
  | { phase: "checking" }
  | { phase: "checked"; report: ValidatorReport }
  | { phase: "no_artifact" }
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

type ExportState =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "ready"; response: AdvisorExportResponse }
  | { phase: "error"; message: string };

/** "Export for chatbot" (M5 unit 4, PLAN §5.2) -- the portable prompt
 * pack's in-app surface. Renders independent of the configured/unconfigured
 * split because it is exactly for people WITHOUT in-app Layer 2: one call
 * to GET /advisor/export (no model behind it, no key needed) produces the
 * tool's expert prompt + this tool's saved artifact JSON + the app's
 * computed results as one block to paste into any chatbot. The tollgate
 * variant swaps in the phase's Champion prompt + phase artifact summaries. */
function ExportForChatbot({ projectId, toolId, artifactId }: { projectId: string; toolId: string; artifactId?: string }) {
  const [state, setState] = useState<ExportState>({ phase: "idle" });
  const [exportPhase, setExportPhase] = useState<TollgatePhase>("Define");

  async function run(kind: "tool" | "tollgate") {
    setState({ phase: "loading" });
    try {
      const response = await getAdvisorExport(
        projectId,
        toolId,
        kind === "tollgate" ? { mode: "tollgate", phase: exportPhase } : { artifactId },
      );
      setState({ phase: "ready", response });
    } catch (err) {
      setState({ phase: "error", message: err instanceof ApiError ? err.message : "The export call failed." });
    }
  }

  return (
    <div className="sigma-advisor-panel__export" data-testid="advisor-export-section">
      <p className="sigma-advisor-panel__muted">
        No API key? Use the portable prompt pack: one block -- this tool&apos;s expert prompt, your saved artifact,
        and the app&apos;s computed results -- to paste into any chatbot.
      </p>
      <div className="sigma-advisor-panel__export-actions">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => run("tool")}
          disabled={state.phase === "loading"}
          data-testid="advisor-export-tool-button"
        >
          Export for chatbot
        </Button>
        <SelectInput
          aria-label="Tollgate export phase"
          data-testid="advisor-export-phase-select"
          value={exportPhase}
          onChange={(e) => setExportPhase(e.target.value as TollgatePhase)}
        >
          {TOLLGATE_PHASES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </SelectInput>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => run("tollgate")}
          disabled={state.phase === "loading"}
          data-testid="advisor-export-tollgate-button"
        >
          Export tollgate
        </Button>
      </div>

      {state.phase === "error" && <VerdictBanner tone="fail" headline="The export call failed" detail={state.message} />}

      {state.phase === "ready" && (
        <div className="sigma-advisor-panel__export-result" data-testid="advisor-export-result">
          <TextArea
            aria-label="Paste-ready chatbot block"
            data-testid="advisor-export-preview"
            value={state.response.combined}
            readOnly
            rows={8}
          />
          <CopyButton text={state.response.combined} testId="advisor-export-copy" />
          <p className="sigma-advisor-panel__muted">
            Paste the whole block into any chatbot. Numbers that come back are not authoritative -- the app&apos;s
            computed results are the record.
          </p>
        </div>
      )}
    </div>
  );
}

/** Collapsible "Advisor" panel on every ToolScreen (M5 brief) -- Layer 2,
 * strictly optional. The mode picker and every mode's input affordances
 * render regardless of configured state (M5 unit 2 brief: "with no key
 * configured, each mode's UI renders its input affordances and the
 * unconfigured state on submit paths") -- only the actual ask attempt is
 * gated on being configured. M5 unit 4 adds the ExportForChatbot section,
 * also configured-state-independent -- see its own docstring. */
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
  const [validateState, setValidateState] = useState<ValidateState>({ phase: "idle" });

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

  /** Loads this tool's last-saved artifact (same id review/help_me_think/
   * explain already use) and sends it to POST /advisor/validate. A 404
   * from the load means nothing has been saved for this tool yet -- an
   * honest, distinct state from a real error. */
  async function checkClaims() {
    if (!artifactId) return;
    setValidateState({ phase: "checking" });
    let body: Record<string, unknown>;
    try {
      body = await loadArtifact(projectId, artifactId);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setValidateState({ phase: "no_artifact" });
      } else {
        setValidateState({ phase: "error", message: err instanceof ApiError ? err.message : "Could not load the saved artifact." });
      }
      return;
    }
    try {
      const report = await validateAdvisor({ project_id: projectId, tool_id: toolId, body });
      setValidateState({ phase: "checked", report });
    } catch (err) {
      setValidateState({ phase: "error", message: err instanceof ApiError ? err.message : "The validator call failed." });
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

          <ExportForChatbot projectId={projectId} toolId={toolId} artifactId={artifactId} />

          {status.phase === "unreachable" && (
            <VerdictBanner tone="fail" headline="Could not reach the engine" detail={status.message} />
          )}

          {status.phase === "unconfigured" && (
            <div className="sigma-advisor-panel__unconfigured" data-testid="advisor-unconfigured">
              <p>
                Layer 1 (all tools, math, charts) runs entirely on your machine and sends nothing anywhere. The suite
                never needs this to be usable.
              </p>
              <p data-testid="advisor-privacy-statement">
                The advisor is Layer 2 -- optional AI advice -- and isn&apos;t set up yet. {ADVISOR_PRIVACY_STATEMENT}
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
                  {/* M5 exit critic (bullet finding): a model can emit more than one
                   * REQUEST_ARTIFACT line in a single turn, but this used to only ever
                   * offer followUpPending[0] -- every other requested id was silently
                   * unreachable. Each pending id now gets its own row, confirmed or
                   * declined independently; declining one leaves the rest pending. */}
                  {followUpPending.map((id) => (
                    <div key={id} className="sigma-advisor-panel__followup-row" data-testid={`advisor-requested-artifact-row-${id}`}>
                      <p>The advisor asked to see {id} in full -- send it?</p>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => submit(id)}
                        data-testid={`advisor-requested-artifact-confirm-${id}`}
                      >
                        Send {id}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setFollowUpPending((prev) => prev.filter((pendingId) => pendingId !== id))}
                      >
                        No thanks
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {artifactId && (
                <div className="sigma-advisor-panel__validator" data-testid="advisor-validator-section">
                  <p className="sigma-advisor-panel__muted">
                    Check the saved {toolId} artifact&apos;s free-text claims against your project data.
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={checkClaims}
                    disabled={validateState.phase === "checking"}
                    data-testid="advisor-check-claims-button"
                  >
                    {validateState.phase === "checking" ? "Checking…" : "Check my claims"}
                  </Button>

                  {validateState.phase === "no_artifact" && (
                    <p className="sigma-advisor-panel__muted" data-testid="advisor-validator-no-artifact">
                      Save this artifact at least once, then check its claims.
                    </p>
                  )}

                  {validateState.phase === "error" && (
                    <VerdictBanner tone="fail" headline="The validator call failed" detail={validateState.message} />
                  )}

                  {validateState.phase === "checked" && (
                    <ValidatorResult report={validateState.report} onDismiss={() => setValidateState({ phase: "idle" })} />
                  )}
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
  // Fix 4 (M5 exit critic): checked BEFORE unstructured_fallback below --
  // a truncated attempt (stop_reason == "max_tokens") never reaches the
  // parser (structured.py's StructuredOutcome contract), so the two are
  // mutually exclusive, but this ordering states that plainly rather than
  // relying on it. A cut-off answer is an honest, distinct case from a
  // malformed one -- "hit the output limit," never the unstructured-output
  // message, which would misdescribe why.
  if (response.truncated) {
    return (
      <div data-testid="advisor-answer">
        <VerdictBanner
          tone="flag"
          headline="The answer hit the output limit"
          detail="The model's response was cut off before it finished. Try a narrower question, or ask again."
        />
        <div className="sigma-advisor-panel__answer">{response.answer}</div>
      </div>
    );
  }

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
    return (
      <RemedyResult
        remedies={response.structured.remedies}
        toolId={toolId}
        unverifiedCauseNote={response.structured.unverified_cause_note}
      />
    );
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

function RemedyResult({
  remedies,
  toolId,
  unverifiedCauseNote,
}: {
  remedies: AdvisorRemedyCandidate[];
  toolId: string;
  unverifiedCauseNote: string;
}) {
  if (remedies.length === 0) {
    return <p className="sigma-advisor-panel__muted">No remedies yet -- verified causes on the fishbone (T-15) are needed first.</p>;
  }
  // Fix 5 (M5 exit critic): a remedy citing a cause_id that isn't a
  // currently VERIFIED fishbone cause is still shown below -- flagged,
  // never hidden -- but left out of the paste-ready draft by default,
  // since T-18 is meant to start from grounded remedies. The bullet
  // finding's invented "impact ~3, effort ~3" numbers are gone too -- the
  // advisor was never asked for those, and inventing them for a matrix the
  // user hasn't scored yet is exactly the kind of number this app doesn't
  // put in front of a Green Belt student without provenance.
  const draftRemedies = remedies.filter((r) => r.unverified_cause_refs.length === 0);
  const draftText = draftRemedies
    .map(
      (r, i) =>
        `${i + 1}. ${r.title} (linked causes: ${r.cause_ids.join(", ")} -- score these in the matrix)\n   ${r.why_it_fits_the_verified_cause}`,
    )
    .join("\n\n");
  return (
    <div data-testid="advisor-remedy-result">
      {unverifiedCauseNote && (
        <VerdictBanner
          tone="flag"
          headline="Some remedies cite an unverified cause"
          detail={unverifiedCauseNote}
        />
      )}
      <div className="sigma-advisor-panel__remedy-header">
        <p>Ranked remedies, tied to your verified causes:</p>
        <CopyButton text={draftText} testId="advisor-remedy-draft-copy" />
      </div>
      <p className="sigma-advisor-panel__muted">
        "Start solution matrix from these" copies a draft list (title, linked cause ids, one line of reasoning per
        remedy) -- paste it into {toolId === "T-18" ? "this" : "the Solution Selection Matrix (T-18)"} form and edit
        from there; the advisor never saves anything on its own. Flagged remedies below are left out of the draft
        until their causes are verified.
      </p>
      <ol className="sigma-advisor-panel__remedy-cards" data-testid="advisor-remedy-cards">
        {remedies.map((r, i) => (
          <li key={i} className="sigma-advisor-panel__remedy-card">
            <div className="sigma-advisor-panel__remedy-card-title">
              {r.title} <StatusPill label={r.estimated_cost_band} tone={COST_BAND_TONE[r.estimated_cost_band]} />
              {r.unverified_cause_refs.length > 0 && <StatusPill label="Unverified cause" tone="flag" />}
            </div>
            <p>{r.why_it_fits_the_verified_cause}</p>
            <p className="sigma-advisor-panel__muted">Causes: {r.cause_ids.join(", ")}</p>
            {r.unverified_cause_refs.length > 0 && (
              <p className="sigma-advisor-panel__muted" data-testid={`advisor-remedy-unverified-${i}`}>
                Not currently verified: {r.unverified_cause_refs.join(", ")} -- excluded from the paste-ready draft.
              </p>
            )}
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

const SEVERITY_LABEL: Record<ValidatorFlag["severity"], string> = {
  cant_trace: "Can't trace",
  contradicts: "Contradicts",
};
const SEVERITY_TONE: Record<ValidatorFlag["severity"], PillTone> = {
  cant_trace: "flag",
  contradicts: "fail",
};

/** The validator pass's result (PLAN §5.3.6, M5 unit 3): a dismissible
 * flags list plus the fixed disclaimer, rendered from the report exactly
 * as the engine sent it -- ValidatorReport.disclaimer, never UI copy of
 * our own, so this can never drift from what the architecture doc
 * promises. Zero flags is shown as a plain, unexcited line, not a "pass" —
 * the whole point of the disclaimer is that a clean read here is not a
 * guarantee. */
function ValidatorResult({ report, onDismiss }: { report: ValidatorReport; onDismiss: () => void }) {
  return (
    <div className="sigma-advisor-panel__validator-result" data-testid="advisor-validator-result">
      {report.unstructured_fallback && (
        <VerdictBanner
          tone="flag"
          headline="The validator returned unstructured output"
          detail="Saving is never blocked by this -- you can still save as-is."
        />
      )}

      {!report.unstructured_fallback && report.flags.length === 0 && (
        <p className="sigma-advisor-panel__muted" data-testid="advisor-validator-empty">
          No claims flagged out of {report.checked_field_count} field(s) checked.
        </p>
      )}

      {!report.unstructured_fallback && report.flags.length > 0 && (
        <ul className="sigma-advisor-panel__validator-flags" data-testid="advisor-validator-flags-list">
          {report.flags.map((f, i) => (
            <li key={i} className="sigma-advisor-panel__validator-flag" data-testid={`advisor-validator-flag-${i}`}>
              <div className="sigma-advisor-panel__validator-flag-head">
                <StatusPill label={SEVERITY_LABEL[f.severity]} tone={SEVERITY_TONE[f.severity]} />
                <span className="sigma-advisor-panel__validator-flag-field">{f.field_path}</span>
              </div>
              <p>&quot;{f.claim_text}&quot;</p>
              <p className="sigma-advisor-panel__muted">{f.why_flagged}</p>
            </li>
          ))}
        </ul>
      )}

      <p className="sigma-advisor-panel__muted" data-testid="advisor-validator-disclaimer">
        {report.disclaimer}
      </p>

      <Button variant="ghost" size="sm" onClick={onDismiss} data-testid="advisor-validator-dismiss">
        Dismiss
      </Button>
    </div>
  );
}
