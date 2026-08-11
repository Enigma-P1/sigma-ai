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

// Artifact-backed reports, no chart capture needed for most of them.
// A few screens need a step before the button is reachable. T-11 is
// tabbed and the collection plan is not the default tab -- its button
// renders but stays hidden, which is correct product behaviour and would
// read as a broken button if the probe did not open the tab.
const CANVAS_SETTLE_MS = 900;
const settleCanvas = async () => page.waitForTimeout(CANVAS_SETTLE_MS);

const PREPARE = {
  // The Konva stages register their capturer on mount; give them a beat
  // before asking for the image, or the report prints "chart not captured"
  // and still passes as a PDF.
  "T-06": settleCanvas,
  "T-07": settleCanvas,
  "T-15": settleCanvas,
  "T-11": async () => {
    await page.getByTestId("t11-tab-plan").click();
    await page.waitForTimeout(300);
  },
};

for (const tool of [
  "T-01", "T-02", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09",
  "T-11", "T-12", "T-15", "T-16", "T-17", "T-18", "T-19", "T-20",
  "T-21", "T-22", "T-23", "T-24",
]) {
  await grab(tool, PREPARE[tool]);
}

// T-35: nothing is saved in the example, so this both builds a study from
// scratch through the entry grid and then exports it -- the only check that
// the grid, the resize, the save and the components chart hold together.
// A small study on purpose: 3x2x2 is 12 cells to type, and the arithmetic
// under test is the same at any size.
await grab("T-35", async () => {
  await page.getByTestId("grr-parts-count").fill("3");
  await page.getByTestId("grr-operators-count").fill("2");
  await page.getByTestId("grr-trials-count").fill("2");
  await page.getByTestId("grr-tolerance").fill("20");
  // Parts far apart, operators close together, small repeat spread: an
  // acceptable gauge, so a broken verdict shows up as a wrong one rather
  // than as an empty report.
  const base = [10, 20, 30];
  for (let p = 0; p < 3; p++) {
    for (let o = 0; o < 2; o++) {
      for (let t = 0; t < 2; t++) {
        await page.getByTestId(`grr-cell-${p}-${o}-${t}`).fill(String(base[p] + o * 0.2 + t * 0.1));
      }
    }
  }
  await page.getByTestId("grr-run").click();
  await page.getByTestId("grr-result").waitFor({ timeout: 30000 });
  // The components chart must paint before its capturer registers, and the
  // fingerprint lands a tick later still.
  await page.waitForTimeout(1200);
});

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
