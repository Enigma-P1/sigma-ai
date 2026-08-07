/** Where the engine lives, per runtime (M1 brief, "Sidecar/dev wiring"). */

/** True inside the Tauri webview (packaged app or `tauri dev`) — Tauri v2
 * injects this global before any app code runs. */
export function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

// Must match SIDECAR_PORT in desktop/src-tauri/src/lib.rs and
// sigma_engine.main.DEFAULT_PORT in engine/sigma_engine/main.py.
const TAURI_SIDECAR_BASE_URL = "http://127.0.0.1:8756";

// Same-origin path proxied by Vite's dev server (vite.config.ts) through to
// VITE_ENGINE_URL. Used instead of fetching VITE_ENGINE_URL directly because
// the engine sends no CORS headers (engine/ is out of scope to edit this
// milestone) -- a real browser blocks a direct cross-origin fetch's response
// before this app ever sees it. Proxying through the same origin as the Vite
// dev server sidesteps CORS entirely. See vite.config.ts for the proxy and
// the "Conflicts" note in the build report.
const BROWSER_DEV_PROXY_BASE_URL = "/engine-api";

export function resolveEngineBaseUrl(): string {
  return isTauriRuntime() ? TAURI_SIDECAR_BASE_URL : BROWSER_DEV_PROXY_BASE_URL;
}

/** The configured (or default) engine URL, for display purposes only (e.g.
 * the diagnostics screen) -- actual browser-mode requests go through the
 * same-origin proxy above, not this URL directly. */
export const CONFIGURED_ENGINE_URL: string =
  (import.meta.env.VITE_ENGINE_URL as string | undefined) || "http://127.0.0.1:8000";
