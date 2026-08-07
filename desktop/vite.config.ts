import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async ({ mode }) => {
  // "." rather than process.cwd() -- resolves the same (npm/vite both run
  // from desktop/) without needing Node's ambient `process` global, which
  // this project's tsconfig doesn't have types for (see the TAURI_DEV_HOST
  // line below for the existing, more invasive way around the same gap).
  const env = loadEnv(mode, ".", "");
  // Sidecar/dev wiring (M1 brief): in plain browser dev mode the engine is
  // read from VITE_ENGINE_URL, default http://127.0.0.1:8000.
  const engineUrl = env.VITE_ENGINE_URL || "http://127.0.0.1:8000";

  // The engine (engine/sigma_engine/main.py) sends no CORS headers, and
  // engine/ is out of scope for this milestone to edit -- a browser fetch
  // straight to `engineUrl` from the Vite dev origin would be blocked by
  // the browser before src/api/client.ts ever saw a response. Proxying
  // `/engine-api/*` through the dev server's own origin sidesteps CORS
  // entirely; see src/api/runtime.ts for the client-side half of this.
  const engineProxy = {
    "/engine-api": {
      target: engineUrl,
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/engine-api/, ""),
    },
  };

  return {
    plugins: [react()],

    // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
    //
    // 1. prevent Vite from obscuring rust errors
    clearScreen: false,
    // 2. tauri expects a fixed port, fail if that port is not available
    server: {
      port: 1420,
      strictPort: true,
      host: host || false,
      hmr: host
        ? {
            protocol: "ws",
            host,
            port: 1421,
          }
        : undefined,
      watch: {
        // 3. tell Vite to ignore watching `src-tauri`
        ignored: ["**/src-tauri/**"],
      },
      proxy: engineProxy,
    },
    // Same proxy for `vite preview` (a production build served outside
    // Tauri) -- not exercised by this milestone's smoke test, but free to
    // keep consistent with `server.proxy` above.
    preview: {
      proxy: engineProxy,
    },
  };
});
