#!/usr/bin/env node
/** TOOL-REPORT PROBE — does "Download report" put a real PDF on disk?
 *
 * WHY A BROWSER: the report route can be exercised from pytest, and that
 * proves nothing about the button. Three failures live only in the client:
 * the Tauri webview cancels downloads with no error unless the window
 * carries a download handler; a CORS regression fails the POST the same
 * silent way; and the chart capture can return null, or return an image
 * whose fingerprint the engine then refuses. All three end with a user
 * clicking a button and getting nothing, which is indistinguishable from
 * a working button until you look for the file.
 *
 * Runs against the packaged origin condition (see packaged-sweep.mjs).
 *
 * Usage: build the bundle, start an engine on 8756 over a projects root
 * holding the worked example, then:  node tools/tool-report-probe.mjs
 */
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(HERE, "..", "dist");
const CHROMIUM_PATH = "/opt/pw-browsers/chromium";
const launchOptions = fs.existsSync(CHROMIUM_PATH) ? { executablePath: CHROMIUM_PATH } : {};

const PROBE_PORT = Number(process.env.PROBE_PORT || 4609);
const PROJECT_ID = process.env.PROJECT_ID || "coffee-bar-example";
const HOST = process.env.PROBE_HOST || "tauri.localhost";
const OUT = process.env.OUT || fs.mkdtempSync(path.join(os.tmpdir(), "sigma-report-"));

if (!fs.existsSync(path.join(DIST, "index.html"))) {
  console.error("no desktop/dist -- run `npm run build` first");
  process.exit(1);
}

const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".json": "application/json", ".woff2": "font/woff2", ".png": "image/png" };
const site = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
  let file = path.join(DIST, rel);
  if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(DIST, "index.html");
  res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
  res.end(fs.readFileSync(file));
});
await new Promise((r) => site.listen(PROBE_PORT, r));

const browser = await chromium.launch(launchOptions);
const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, acceptDownloads: true });
await ctx.addInitScript(() => {
  window.__TAURI_INTERNALS__ = { invoke: async () => undefined, transformCallback: (c) => c };
});
const page = await ctx.newPage();
const problems = [];
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("response", (r) => { if (r.status() >= 400) problems.push(`http ${r.status()}: ${r.url()}`); });

await page.goto(`http://${HOST}:${PROBE_PORT}/`, { waitUntil: "domcontentloaded" });
await page.getByRole("button", { name: /open a project/i }).first().click().catch(() => {});
await page.getByTestId("open-project-id").waitFor({ timeout: 20000 });
await page.getByTestId("open-project-id").fill(PROJECT_ID);
await page.getByTestId("open-project-submit").click();
await page.getByTestId("phase-Define").waitFor({ timeout: 20000 });

const results = [];

async function grab(toolId, prepare) {
  await page.getByTestId(`nav-tool-${toolId}`).click();
  await page.waitForTimeout(700);
  if (prepare) await prepare();
  const btn = page.getByTestId(`report-button-${toolId}`);
  await btn.waitFor({ timeout: 20000 });
  if (await btn.isDisabled()) {
    results.push({ toolId, ok: false, note: "button disabled" });
    return;
  }
  const dl = page.waitForEvent("download", { timeout: 90000 });
  await btn.click();
  const download = await dl;
  const dest = path.join(OUT, download.suggestedFilename());
  await download.saveAs(dest);
  const bytes = fs.readFileSync(dest);
  const err = await page.getByTestId(`report-error-${toolId}`).count();
  results.push({
    toolId,
    ok: bytes.subarray(0, 5).toString() === "%PDF-" && bytes.length > 2000 && err === 0,
    bytes: bytes.length,
    file: download.suggestedFilename(),
    note: err ? await page.getByTestId(`report-error-${toolId}`).innerText() : "",
  });
}

// T-16: saved artifact, no chart -- the dense-table path.
await grab("T-16");

// T-13: the report button only exists after a baseline has been run, which
// is correct -- there is nothing to report on before that. Running it here
// is also the only way to exercise the chart-capture path end to end, which
// is the genuinely new mechanism in this feature.
await grab("T-13", async () => {
  await page.getByTestId("baseline-dataset-select").selectOption({ index: 1 });
  await page.waitForTimeout(400);
  const columns = page.getByTestId("baseline-column-select");
  const options = await columns.locator("option").allTextContents();
  const numeric = options.findIndex((o) => /wait|minute|time|value/i.test(o));
  await columns.selectOption({ index: numeric > 0 ? numeric : 1 });
  await page.getByTestId("baseline-usl-input").fill("5");
  await page.getByTestId("baseline-op-def-checkbox").check();
  await page.getByTestId("baseline-run").click();
  // The I-MR chart must actually paint before its capturer registers, and
  // the fingerprint lands a tick later still.
  await page.getByTestId(`report-button-T-13`).waitFor({ timeout: 30000 });
  await page.waitForTimeout(1200);
});

for (const r of results) {
  console.log(`${r.ok ? "PASS" : "FAIL"}  ${r.toolId}  ${r.bytes ?? 0} bytes  ${r.file ?? ""} ${r.note}`);
}
if (problems.length) console.log("PROBLEMS:\n  " + problems.slice(0, 10).join("\n  "));

await browser.close();
site.close();
const pass = results.length > 0 && results.every((r) => r.ok) && problems.length === 0;
console.log(pass ? "RESULT: PASS" : "RESULT: FAIL");
process.exit(pass ? 0 : 1);
