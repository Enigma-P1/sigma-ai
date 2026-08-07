import { useEffect, useState } from "react";
import "./App.css";

// Must match SIDECAR_PORT in desktop/src-tauri/src/lib.rs and
// sigma_engine.main.DEFAULT_PORT in engine/sigma_engine/main.py. Plain
// `fetch` to 127.0.0.1 needs no Tauri IPC/capability grant -- it's an
// ordinary web request the webview makes on its own.
const ENGINE_BASE_URL = "http://127.0.0.1:8756";
const HEALTH_POLL_INTERVAL_MS = 400;
const HEALTH_POLL_TIMEOUT_MS = 20_000;

interface HealthResponse {
  status: string;
  engine_version: string;
}

interface SmokeResponse {
  dataset: string;
  n: number;
  mean: number;
  stdev: number;
  certified_mean: number;
  certified_stdev: number;
  match: boolean;
}

type EngineState =
  | { phase: "connecting" }
  | { phase: "online"; health: HealthResponse }
  | { phase: "unreachable"; detail: string };

function App() {
  const [engine, setEngine] = useState<EngineState>({ phase: "connecting" });
  const [smoke, setSmoke] = useState<SmokeResponse | null>(null);
  const [smokeError, setSmokeError] = useState<string | null>(null);

  // Poll /health until the sidecar answers (cold start -- process spawn +
  // scipy import -- can take a couple of seconds) or we give up.
  useEffect(() => {
    let cancelled = false;
    const startedAt = Date.now();

    async function pollHealth() {
      while (!cancelled) {
        try {
          const res = await fetch(`${ENGINE_BASE_URL}/health`);
          if (res.ok) {
            const health = (await res.json()) as HealthResponse;
            if (!cancelled) setEngine({ phase: "online", health });
            return;
          }
        } catch {
          // Connection refused while the sidecar is still starting up is
          // expected here, not an error -- just keep polling.
        }
        if (Date.now() - startedAt > HEALTH_POLL_TIMEOUT_MS) {
          if (!cancelled) {
            setEngine({
              phase: "unreachable",
              detail: `no response from ${ENGINE_BASE_URL}/health after ${
                HEALTH_POLL_TIMEOUT_MS / 1000
              }s`,
            });
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

  // Once the engine is up, run the smoke check exactly once.
  useEffect(() => {
    if (engine.phase !== "online") return;
    let cancelled = false;

    fetch(`${ENGINE_BASE_URL}/smoke`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<SmokeResponse>;
      })
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
    <main className="container">
      <h1>Sigma AI — Packaging Spike</h1>
      <p className="subtitle">
        Tauri shell + packaged Python sidecar, proving the pipeline with one
        NIST-verified calculation.
      </p>

      <section className="card">
        <h2>Engine</h2>
        {engine.phase === "connecting" && (
          <p className="status status-pending">Connecting to sidecar…</p>
        )}
        {engine.phase === "unreachable" && (
          <p className="status status-fail">Engine unreachable — {engine.detail}</p>
        )}
        {engine.phase === "online" && (
          <p className="status status-ok">
            Online — engine_version {engine.health.engine_version}
          </p>
        )}
      </section>

      {engine.phase === "online" && (
        <section className="card">
          <h2>NIST smoke check</h2>
          {smokeError && (
            <p className="status status-fail">Smoke check failed — {smokeError}</p>
          )}
          {!smoke && !smokeError && <p className="status status-pending">Running…</p>}
          {smoke && (
            <>
              <p className="dataset-line">
                Dataset: NIST StRD &ldquo;{smoke.dataset}&rdquo; (n = {smoke.n})
              </p>
              <table className="smoke-table">
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
              <p
                className={
                  smoke.match ? "status status-ok result-line" : "status status-fail result-line"
                }
              >
                {smoke.match ? "NIST smoke check PASSED" : "NIST smoke check FAILED"}
              </p>
            </>
          )}
        </section>
      )}
    </main>
  );
}

export default App;
