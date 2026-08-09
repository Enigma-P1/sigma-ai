/** Cross-origin probe — the packaged-app condition, reproduced locally.
 *
 * WHY THIS EXISTS: two bugs shipped to a real user because nothing tested
 * the app the way it actually runs when installed. The dev/browser smoke
 * (smoke-browser.mjs) loads the UI from Vite, which PROXIES the engine
 * same-origin, so the browser never sends a CORS preflight. The packaged
 * Tauri webview is a different origin from the 127.0.0.1 sidecar, so it
 * preflights every call -- and the engine answered 405 (no CORS
 * middleware), which the app reported as "the engine didn't start".
 * curl-based CI smoke never caught it either, because curl doesn't
 * preflight.
 *
 * This drives a REAL browser from origin A against the engine on origin B,
 * which is exactly the packaged condition -- no installer, no CI, no cost.
 * Run it against any engine build before shipping one.
 *
 * Usage (engine must be running on ENGINE_PORT, default 8756):
 *   node tools/xorigin-probe.mjs
 * Env: ENGINE_PORT (default 8756), PROBE_PORT (default 5599)
 */
import { chromium } from "playwright";
import http from "node:http";

const ENGINE_PORT = process.env.ENGINE_PORT || "8756";
const PROBE_PORT = Number(process.env.PROBE_PORT || 5599);
const ENGINE = `http://127.0.0.1:${ENGINE_PORT}`;

// Serve a blank page from a DIFFERENT origin than the engine. That
// difference is the whole point: it makes the browser enforce CORS exactly
// as the packaged webview does.
const site = http.createServer((_req, res) => {
  res.writeHead(200, { "content-type": "text/html" });
  res.end("<!doctype html><title>xorigin probe</title><body>probe</body>");
});
await new Promise((r) => site.listen(PROBE_PORT, r));

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage();
const consoleErrors = [];
page.on("console", (m) => {
  // The blank probe page has no favicon; that 404 is noise, not a finding.
  if (m.type() === "error" && !m.text().includes("404")) consoleErrors.push(m.text());
});
await page.goto(`http://localhost:${PROBE_PORT}/`, { waitUntil: "domcontentloaded" });

const result = await page.evaluate(async (ENGINE) => {
  const out = {};
  const id = "xorigin-probe-" + Date.now();
  try {
    const h = await fetch(`${ENGINE}/health`);
    out.health = { status: h.status, body: await h.json() };
    // A JSON POST forces a real preflight -- this is the call that failed
    // for the first installed user.
    const c = await fetch(`${ENGINE}/project/create`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ project_id: id, name: "Cross-origin probe", created_at: "2026-08-09T00:00:00" }),
    });
    out.create = { status: c.status };
    const g = await fetch(`${ENGINE}/project/${id}`);
    out.read = { status: g.status };
    const s = await fetch(`${ENGINE}/smoke`);
    out.smoke = await s.json();
  } catch (e) {
    out.error = String(e);
  }
  return out;
}, ENGINE);

console.log(JSON.stringify(result, null, 2));
console.log("CONSOLE ERRORS:", consoleErrors.length ? consoleErrors : "none");

const pass =
  result.health?.status === 200 &&
  result.create?.status === 200 &&
  result.read?.status === 200 &&
  result.smoke?.match === true &&
  !result.error &&
  consoleErrors.length === 0;
console.log(pass ? "RESULT: PASS (cross-origin works end to end)" : "RESULT: FAIL");

await browser.close();
site.close();
process.exit(pass ? 0 : 1);
