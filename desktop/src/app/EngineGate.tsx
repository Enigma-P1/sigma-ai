import { Button, Panel, VerdictBanner } from "../design/components";
import type { EngineReadiness } from "./useEngineReadiness";
import "./EngineGate.css";

export interface EngineGateProps {
  /** Only the two non-ready phases render a gate -- once ready, App renders
   * the real app instead of this. */
  state: Extract<EngineReadiness, { phase: "starting" } | { phase: "failed" }>;
  onRetry: () => void;
}

/** The startup gate shown while the local engine comes up (Tauri runtime
 * only). "starting" is a brief waiting state; "failed" is the honest
 * dead-end that shows where the sidecar log is and what it last said, with a
 * Retry that re-polls. */
export function EngineGate({ state, onRetry }: EngineGateProps) {
  return (
    <div className="sigma-engine-gate" data-testid="engine-gate">
      <div className="sigma-engine-gate__inner">
        <h1 className="sigma-engine-gate__title">Sigma AI</h1>

        {state.phase === "starting" ? (
          <VerdictBanner
            tone="neutral"
            headline="Starting the engine…"
            detail="The local statistics engine is starting up. On first launch this can take a few seconds."
          />
        ) : (
          <>
            <VerdictBanner
              tone="fail"
              headline="The engine didn't start"
              detail="Sigma AI couldn't reach its local statistics engine, so nothing can run yet. The sidecar log below has the details — please retry, and share the log if it keeps failing."
            />

            <Panel title="Sidecar log" className="sigma-engine-gate__panel">
              <p className="sigma-engine-gate__logpath">
                {state.logPath ? (
                  <>
                    Log file: <code>{state.logPath}</code>
                  </>
                ) : (
                  "Log file location unavailable."
                )}
              </p>
              {state.logTail ? (
                <pre className="sigma-engine-gate__logtail" data-testid="engine-gate-log-tail">
                  {state.logTail}
                </pre>
              ) : (
                <p className="sigma-engine-gate__logempty">The sidecar log is empty or could not be read.</p>
              )}
            </Panel>

            <div className="sigma-engine-gate__actions">
              <Button variant="primary" onClick={onRetry} data-testid="engine-gate-retry">
                Retry
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
