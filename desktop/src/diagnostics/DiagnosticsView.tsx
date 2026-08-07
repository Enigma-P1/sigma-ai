import { useEffect, useState } from "react";
import { Panel, VerdictBanner } from "../design/components";
import { getHealth, getSmoke } from "../api/client";
import { CONFIGURED_ENGINE_URL, isTauriRuntime } from "../api/runtime";
import type { HealthResponse, SmokeResponse } from "../api/types";
import "./DiagnosticsView.css";

export interface DiagnosticsViewProps {
  onBack: () => void;
}

const HEALTH_POLL_INTERVAL_MS = 400;
const HEALTH_POLL_TIMEOUT_MS = 20_000;

type EngineState =
  | { phase: "connecting" }
  | { phase: "online"; health: HealthResponse }
  | { phase: "unreachable"; detail: string };

/** The original packaging-spike smoke check (NIST-verified stats), kept
 * reachable per the M1 brief -- not the main screen anymore, a diagnostics
 * view off the top bar. All calls now go through src/api/client.ts instead
 * of a local hardcoded fetch. */
export function DiagnosticsView({ onBack }: DiagnosticsViewProps) {
  const [engine, setEngine] = useState<EngineState>({ phase: "connecting" });
  const [smoke, setSmoke] = useState<SmokeResponse | null>(null);
  const [smokeError, setSmokeError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const startedAt = Date.now();

    async function pollHealth() {
      while (!cancelled) {
        try {
          const health = await getHealth();
          if (!cancelled) setEngine({ phase: "online", health });
          return;
        } catch {
          // Connection refused while the sidecar is still starting up is
          // expected here, not an error -- just keep polling.
        }
        if (Date.now() - startedAt > HEALTH_POLL_TIMEOUT_MS) {
          if (!cancelled) {
            setEngine({ phase: "unreachable", detail: `no response after ${HEALTH_POLL_TIMEOUT_MS / 1000}s` });
          }
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, HEALTH_POLL_INTERVAL_MS));
      }
    }

    void pollHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (engine.phase !== "online") return;
    let cancelled = false;
    getSmoke()
      .then((data) => {
        if (!cancelled) setSmoke(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setSmokeError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [engine.phase]);

  return (
    <div className="sigma-diag">
      <button type="button" className="sigma-diag__back" onClick={onBack} data-testid="diagnostics-back">
        ← Back
      </button>
      <h1>Diagnostics</h1>
      <p className="sigma-diag__subtitle">
        Sidecar target: {isTauriRuntime() ? "Tauri sidecar (127.0.0.1:8756)" : `${CONFIGURED_ENGINE_URL} (via dev proxy)`}
      </p>

      <Panel title="Engine" className="sigma-diag__panel">
        {engine.phase === "connecting" && <VerdictBanner tone="neutral" headline="Connecting to sidecar…" />}
        {engine.phase === "unreachable" && <VerdictBanner tone="fail" headline="Engine unreachable" detail={engine.detail} />}
        {engine.phase === "online" && (
          <VerdictBanner tone="pass" headline={`Online — engine_version ${engine.health.engine_version}`} />
        )}
      </Panel>

      {engine.phase === "online" && (
        <Panel title="NIST smoke check" className="sigma-diag__panel">
          {smokeError && <VerdictBanner tone="fail" headline="Smoke check failed" detail={smokeError} />}
          {!smoke && !smokeError && <VerdictBanner tone="neutral" headline="Running…" />}
          {smoke && (
            <>
              <p>
                Dataset: NIST StRD &ldquo;{smoke.dataset}&rdquo; (n = {smoke.n})
              </p>
              <table>
                <thead>
                  <tr>
                    <th></th>
                    <th>Computed</th>
                    <th>NIST certified</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Mean</td>
                    <td>{smoke.mean}</td>
                    <td>{smoke.certified_mean}</td>
                  </tr>
                  <tr>
                    <td>Std dev</td>
                    <td>{smoke.stdev}</td>
                    <td>{smoke.certified_stdev}</td>
                  </tr>
                </tbody>
              </table>
              <div style={{ marginTop: "var(--space-3)" }}>
                <VerdictBanner
                  tone={smoke.match ? "pass" : "fail"}
                  headline={smoke.match ? "NIST smoke check PASSED" : "NIST smoke check FAILED"}
                />
              </div>
            </>
          )}
        </Panel>
      )}
    </div>
  );
}
