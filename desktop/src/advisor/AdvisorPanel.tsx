import { useEffect, useState } from "react";
import { Button, Panel, TextArea, VerdictBanner } from "../design/components";
import { askAdvisor, getAdvisorStatus } from "../api/client";
import { ApiError } from "../api/errors";
import type { AdvisorAskResponse } from "../api/types";
import "./AdvisorPanel.css";

export interface AdvisorPanelProps {
  projectId: string;
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

/** Collapsible "Advisor" panel on every ToolScreen (M5 brief) -- Layer 2,
 * strictly optional. Unconfigured (no key, or turned off) shows the
 * plain-language explanation and a link to settings; configured shows a
 * generic ask box. Mode is fixed to "generic" here on purpose -- the
 * review/tollgate/remedy modes land in the next unit; this panel's job for
 * now is just to prove the plumbing end to end, not to pick a mode. */
export function AdvisorPanel({ projectId, onOpenSettings }: AdvisorPanelProps) {
  const [status, setStatus] = useState<StatusState>({ phase: "loading" });
  const [question, setQuestion] = useState("");
  const [ask, setAsk] = useState<AskState>({ phase: "idle" });

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

  async function handleAsk() {
    const trimmed = question.trim();
    if (!trimmed) return;
    setAsk({ phase: "asking" });
    try {
      const response = await askAdvisor({ project_id: projectId, mode: "generic", question: trimmed });
      setAsk({ phase: "answered", response });
    } catch (err) {
      setAsk({ phase: "error", message: err instanceof ApiError ? err.message : "The advisor call failed." });
    }
  }

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
          <TextArea
            data-testid="advisor-question"
            placeholder="Ask about this project…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
          />
          <Button
            variant="primary"
            size="sm"
            onClick={handleAsk}
            disabled={ask.phase === "asking" || !question.trim()}
            data-testid="advisor-ask-submit"
          >
            {ask.phase === "asking" ? "Asking…" : "Ask"}
          </Button>

          {ask.phase === "error" && <VerdictBanner tone="fail" headline="The advisor call failed" detail={ask.message} />}
          {ask.phase === "answered" && (
            <div className="sigma-advisor-panel__answer" data-testid="advisor-answer">
              {ask.response.answer}
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}
