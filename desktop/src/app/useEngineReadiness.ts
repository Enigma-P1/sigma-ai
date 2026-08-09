import { useCallback, useEffect, useState } from "react";
import { getHealth } from "../api/client";
import { isTauriRuntime } from "../api/runtime";
import { getSidecarLogPath, getSidecarLogTail } from "../api/sidecarLog";

/** The onefile sidecar self-extracts on first launch (~1-3s slower than the
 * old onedir), so the app must wait for the engine before declaring failure.
 * This hook gates the app on the engine's /health in the Tauri runtime, and
 * is a hard no-op in browser/dev mode (dev talks to the engine on 8000 via
 * the Vite proxy -- unchanged, and the smoke test depends on it). */
export type EngineReadiness =
  | { phase: "ready" }
  | { phase: "starting" }
  | { phase: "failed"; logPath: string; logTail: string };

// ~500ms between polls, up to ~30s total -- comfortably covers the onefile
// unpack + uvicorn bind, without leaving a hung app waiting forever.
const POLL_INTERVAL_MS = 500;
const POLL_TIMEOUT_MS = 30_000;

export interface EngineReadinessHook {
  state: EngineReadiness;
  /** Re-run the health poll from the top (the failure screen's Retry). */
  retry: () => void;
}

export function useEngineReadiness(): EngineReadinessHook {
  // Browser/dev runtime: start already "ready" so the very first render is
  // the normal app, with no flash of a gate screen and no behavior change for
  // the browser smoke test. Only the Tauri runtime starts in "starting".
  const [state, setState] = useState<EngineReadiness>(() =>
    isTauriRuntime() ? { phase: "starting" } : { phase: "ready" },
  );
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => {
    setState({ phase: "starting" });
    setAttempt((n) => n + 1);
  }, []);

  useEffect(() => {
    // The gate only exists inside Tauri; outside it there is nothing to poll
    // and the state is already "ready".
    if (!isTauriRuntime()) return;

    let cancelled = false;
    const startedAt = Date.now();

    async function poll() {
      while (!cancelled) {
        try {
          await getHealth();
          if (!cancelled) setState({ phase: "ready" });
          return;
        } catch {
          // Connection refused while the sidecar self-extracts and uvicorn
          // binds the port is the expected case here, not an error -- keep
          // polling until the timeout below.
        }
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          // Give up: surface the log path + tail so the failure is
          // self-diagnosing. Both degrade to "" on any error.
          const [logPath, logTail] = await Promise.all([getSidecarLogPath(), getSidecarLogTail()]);
          if (!cancelled) setState({ phase: "failed", logPath, logTail });
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
      }
    }

    void poll();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  return { state, retry };
}
