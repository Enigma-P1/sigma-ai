#!/usr/bin/env node
/** SUMMARY EXHIBITS — the pages RELEASE-v0.2.md's Gate 3 says ship with the
 * release, produced the only honest way: by clicking the app's own
 * "One-page summary" button and keeping whatever lands on disk.
 *
 * Three pages, three project states both ship re-reviews cared about:
 *   1. coffee-bar-example — a coherent, fully-worked project (the case the
 *      second-pass review said it could not see: "I cannot see how this
 *      template behaves on a coherent project").
 *   2. wrong-part-in-the-box — the data-first supervisor path: a fresh
 *      project whose ONLY content is a messy real import (ErrorLog_Sept.xlsx
 *      from the 2026-08-12 UAT) charted on T-14. This is the page the
 *      ungated front door now leads to, with the user's own selection and
 *      the mounted Pareto's fingerprint-checked capture on it.
 *   3. fresh-empty — nothing saved at all, so the gaps-named rendering is
 *      on the record next to the populated ones.
 *
 * Runs against the packaged origin condition (see packaged-sweep.mjs).
 *
 * Usage: build the bundle, start an engine on 8756 over a projects root
 * holding the worked example (exhibits 2 and 3 create their projects via
 * the engine API), then:  node tools/summary-exhibits.mjs
 * Env: OUT (default: a fresh temp dir; the three PDFs land there)
 */
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(HERE, "..", "dist");
const REPO = path.join(HERE, "..", "..");
const CHROMIUM_PATH = "/opt/pw-browsers/chromium";
const launchOptions = fs.existsSync(CHROMIUM_PATH) ? { executablePath: CHROMIUM_PATH } : {};

const PROBE_PORT = Number(process.env.PROBE_PORT || 4613);
const HOST = process.env.PROBE_HOST || "tauri.localhost";
const ENGINE = "http://127.0.0.1:8756";
const OUT = process.env.OUT || fs.mkdtempSync(path.join(os.tmpdir(), "sigma-summaries-"));
const MESSY_FILE = path.join(REPO, "docs", "uat", "method", "data", "ErrorLog_Sept.xlsx");

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

async function api(method, route, body) {
  const res = await fetch(`${ENGINE}${route}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${method} ${route} -> ${res.status}: ${(await res.text()).slice(0, 300)}`);
  return res.json();
}

const browser = await chromium.launch(launchOptions);
const ctx = await browser.newContext({ viewport: { width: 1400, height: 950 }, acceptDownloads: true });
await ctx.addInitScript(() => {
  window.__TAURI_INTERNALS__ = { invoke: async () => undefined, transformCallback: (c) => c };
});
const page = await ctx.newPage();
const problems = [];
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("response", (r) => { if (r.status() >= 400) problems.push(`http ${r.status()}: ${r.url()}`); });

async function openProject(id) {
  await page.goto(`http://${HOST}:${PROBE_PORT}/`, { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /open a project/i }).first().click().catch(() => {});
  await page.getByTestId("open-project-id").waitFor({ timeout: 20000 });
  await page.getByTestId("open-project-id").fill(id);
  await page.getByTestId("open-project-submit").click();
  await page.getByTestId("phase-Define").waitFor({ timeout: 20000 });
}

/** Select a dataset + Pareto column on T-14 and wait for the live plot, so
 * the capture registry holds a real picture (and its counts fingerprint)
 * before the top bar asks for it. Column picked by preference regex, else
 * whatever the panel already chose. */
async function mountPareto(columnPreference) {
  await page.getByTestId("nav-tool-T-14").click();
  const datasetSelect = page.getByTestId("chartset-dataset-select");
  await datasetSelect.waitFor({ timeout: 20000 });
  const values = await datasetSelect.locator("option").evaluateAll((os_) => os_.map((o) => o.value).filter(Boolean));
  // Prefer the dataset that actually carries a preference-matching column —
  // a project can hold several (the worked example has two), and "first one
  // with any text column" once picked order_id over the category column
  // sitting in the other file.
  let fallback = null;
  let pick = null;
  for (const v of values) {
    await datasetSelect.selectOption(v);
    await page.waitForTimeout(600);
    if (!(await page.getByTestId("chartset-pareto-column").count())) continue;
    const cols = await page.getByTestId("chartset-pareto-column").locator("option").evaluateAll((os_) => os_.map((o) => o.value).filter(Boolean));
    if (!fallback && cols.length) fallback = { dataset: v, column: cols[0] };
    const match = cols.find((c) => columnPreference.test(c));
    if (match) {
      pick = { dataset: v, column: match };
      break;
    }
  }
  if (!pick) pick = fallback;
  if (!pick) throw new Error("no dataset offers a categorical column for a Pareto");
  await datasetSelect.selectOption(pick.dataset);
  await page.waitForTimeout(600);
  const columnSelect = page.getByTestId("chartset-pareto-column");
  await columnSelect.waitFor({ timeout: 20000 });
  await columnSelect.selectOption(pick.column);
  pick = pick.column;
  await page.locator('[data-testid="chartset-pareto"] .js-plotly-plot').waitFor({ timeout: 20000 });
  // The capturer registers on mount and the fingerprint lands via async
  // state; a beat here is the same settle every capture-carrying probe uses.
  await page.waitForTimeout(1200);
  return pick;
}

const results = [];
async function summarize(name) {
  const dl = page.waitForEvent("download", { timeout: 90000 });
  await page.getByTestId("topbar-summary").click();
  const download = await dl;
  const dest = path.join(OUT, name);
  await download.saveAs(dest);
  const bytes = fs.readFileSync(dest);
  const errCount = await page.getByTestId("topbar-export-error").count();
  results.push({
    name,
    ok: bytes.subarray(0, 5).toString() === "%PDF-" && bytes.length > 2000 && errCount === 0,
    bytes: bytes.length,
  });
}

// 1 — the coherent, fully-worked project.
await openProject("coffee-bar-example");
const coffeeCol = await mountPareto(/category/i);
await summarize("coffee-bar-example-summary.pdf");
console.log(`[exhibit 1] coffee-bar-example, Pareto column: ${coffeeCol}`);

// 2 — the data-first path: import the messy UAT file, chart it, summarize.
await api("POST", "/project/create", { project_id: "wrong-part-in-the-box", name: "Wrong part in the box", created_at: new Date().toISOString() });
await openProject("wrong-part-in-the-box");
await page.getByTestId("nav-tool-T-11").click();
await page.getByTestId("dataimport-file-input").waitFor({ timeout: 20000 });
await page.getByTestId("dataimport-file-input").setInputFiles(MESSY_FILE);
await page.getByTestId("dataimport-quality-scan").waitFor({ timeout: 30000 });
const saveBtn = page.getByTestId("dataimport-save");
await saveBtn.waitFor({ timeout: 20000 });
await saveBtn.click();
await page.getByTestId("dataimport-save-confirmation").waitFor({ timeout: 30000 });
const messyCol = await mountPareto(/part/i);
await summarize("wrong-part-summary.pdf");
console.log(`[exhibit 2] wrong-part-in-the-box, Pareto column: ${messyCol}`);

// 3 — nothing saved at all: the gaps-named rendering, on the record.
await api("POST", "/project/create", { project_id: "fresh-empty", name: "Fresh project", created_at: new Date().toISOString() });
await openProject("fresh-empty");
await summarize("fresh-empty-summary.pdf");
console.log("[exhibit 3] fresh-empty");

await browser.close();
site.close();

console.log(`\nOUT=${OUT}`);
for (const r of results) console.log(`${r.ok ? "PASS" : "FAIL"} ${r.name} (${r.bytes} bytes)`);
if (problems.length) {
  console.log("\npage problems:");
  for (const p of problems) console.log("  " + p);
}
process.exit(results.every((r) => r.ok) && problems.length === 0 ? 0 : 1);
