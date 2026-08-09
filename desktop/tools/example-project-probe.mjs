#!/usr/bin/env node
/** EXAMPLE-PROJECT PROBE -- does the drop-in worked example actually render?
 *
 * WHY THIS EXISTS: the first coffee-bar-example zip opened to a project
 * whose rail said "Done" beside all 22 tools while every form rendered its
 * empty state and said "Not saved yet". Both were honest: the rail reads
 * project.json's artifact_index by TOOL id and found T-03, while the charter
 * form loads a hardcoded ARTIFACT id ("charter") and the file was named
 * "coffee-charter" -- the golden harness's naming. Every engine test passed,
 * every API call 200'd, and the app was useless.
 *
 * An endpoint-level check cannot catch that class of bug, because the
 * endpoints were never wrong -- the UI was asking for different ids than the
 * data provided. Only rendering the real screens against the real zip shows
 * it. So this drives the production bundle, cross-origin (the packaged
 * condition -- see packaged-sweep.mjs for why that matters), opens the
 * example BY ID the way the README now tells a user to, then visits every
 * tool in the rail and fails on any form still showing its empty state.
 *
 * Usage -- build the bundle, stage the example into an isolated projects
 * root, start an engine on it, then run:
 *
 *   cd desktop && npm run build
 *   python3 examples/make-example-project.py <harness-run> /tmp/p/coffee-bar-example
 *   cd engine && SIGMA_PROJECTS_ROOT=/tmp/p .venv/bin/python -m sigma_engine.main --port 8756
 *   cd desktop && node tools/example-project-probe.mjs
 *
 * Env: ENGINE_PORT (default 8756, must match runtime.ts), PROBE_PORT
 * (default 4601), PROJECT_ID (default coffee-bar-example), SHOT (a path to
 * write a full-page screenshot of the charter screen).
 */
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const DIST = path.join(HERE, "..", "dist");
const CHROMIUM_PATH = "/opt/pw-browsers/chromium";
const launchOptions = fs.existsSync(CHROMIUM_PATH) ? { executablePath: CHROMIUM_PATH } : {};

const ENGINE_PORT = process.env.ENGINE_PORT || "8756";
const PROBE_PORT = Number(process.env.PROBE_PORT || 4601);
const PROJECT_ID = process.env.PROJECT_ID || "coffee-bar-example";
const HOST = process.env.PROBE_HOST || "tauri.localhost";
const SHOT = process.env.SHOT || "";

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
const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
// Take the packaged branch: isTauriRuntime() keys off this, and only then
// does the app call the absolute http://127.0.0.1:8756 engine URL instead of
// the Vite proxy path.
await ctx.addInitScript(() => {
  window.__TAURI_INTERNALS__ = { invoke: async () => undefined, transformCallback: (c) => c };
});
const page = await ctx.newPage();

const problems = [];
page.on("console", (m) => { if (m.type() === "error" && !m.text().includes("favicon")) problems.push(`console: ${m.text()}`); });
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("requestfailed", (r) => problems.push(`requestfailed: ${r.url()}`));
page.on("response", (r) => { if (r.status() >= 400) problems.push(`http ${r.status()}: ${r.url()}`); });

await page.goto(`http://${HOST}:${PROBE_PORT}/`, { waitUntil: "domcontentloaded" });

// Open exactly the way examples/README.md tells a user to.
await page.getByRole("button", { name: /open a project/i }).first().click().catch(() => {});
await page.getByTestId("open-project-id").waitFor({ timeout: 15000 });
await page.getByTestId("open-project-id").fill(PROJECT_ID);
await page.getByTestId("open-project-submit").click();
await page.getByTestId("phase-Define").waitFor({ timeout: 15000 });

// Every tool the rail offers, in rail order.
const toolIds = await page.evaluate(() =>
  [...document.querySelectorAll('[data-testid^="nav-tool-"]')].map((el) => el.dataset.testid.replace("nav-tool-", "")),
);

// The exact string the broken zip showed under every tool heading. Matched
// literally and nothing looser: an earlier cut of this used /no .* yet/i,
// which the helper panel's own prose satisfies on every screen, so all 25
// tools "failed" while the data was in fact hydrating fine. A detector that
// fires everywhere is as useless as one that never fires.
const NOT_SAVED = /not saved yet/i;

// Canvas-and-chart tools legitimately have few or no <input>s -- T-14 Charts
// renders Plotly, T-15 Fishbone and T-07 Spaghetti are drawing surfaces. A
// zero field count there is correct, so they are judged on the "Not saved
// yet" marker alone rather than on a threshold they can never meet.
const FIELDLESS_BY_DESIGN = new Set(["T-13", "T-14", "T-15", "T-07", "T-21"]);

const rows = [];
for (const toolId of toolIds) {
  await page.getByTestId(`nav-tool-${toolId}`).click();
  await page.waitForTimeout(450); // hydration is a fetch, not synchronous state
  const text = await page.locator("main, body").first().innerText();
  const notSaved = NOT_SAVED.test(text);
  // A hydrated form has real values in its inputs; an empty one has only
  // placeholders. Placeholders are what the broken zip showed, and they read
  // as content in a screenshot -- so check .value, never rendered text.
  const filled = await page.evaluate(() =>
    [...document.querySelectorAll("input, textarea")].filter((el) => el.value && el.value.trim()).length,
  );
  const blank = notSaved || (filled === 0 && !FIELDLESS_BY_DESIGN.has(toolId));
  rows.push({ toolId, notSaved, filled, blank });
  if (SHOT && toolId === "T-03") await page.screenshot({ path: SHOT, fullPage: true });
}

const blank = rows.filter((r) => r.blank);
for (const r of rows) {
  console.log(`${r.blank ? "BLANK " : "filled"}  ${r.toolId}  ${r.filled} populated fields${r.notSaved ? '  <- says "Not saved yet"' : ""}`);
}
console.log(`\n${rows.length - blank.length}/${rows.length} tools rendered saved content`);

// Field counts and empty-state markers are heuristics: run against the
// BROKEN zip they caught 7 of 25 tools, because a form with no artifact
// still renders default rows and today's date, which count as "populated".
// These anchors are the actual assertion -- specific values that exist only
// if the Coffee Bar artifact really loaded. Cheap to extend, impossible to
// satisfy by accident.
const ANCHORS = [
  ["T-03", /Espresso-drink orders take too long/i, "charter problem statement"],
  ["T-03", /8\.4/, "charter baseline 8.4 min"],
  ["T-04", /espresso station/i, "SIPOC process step"],
  ["T-16", /grind|group head|hopper/i, "FMEA failure mode"],
  // These two were first written as /Priya Shah|Dana Ellis/ and
  // /A3|tollgate|closed/, and both matched the BROKEN zip -- the names appear
  // in the helper panel's worked example and "A3" is the page heading. An
  // anchor that page chrome satisfies proves nothing. Replaced with strings
  // that exist only inside the saved artifact.
  ["T-22", /every 4th espresso order|close of peak/i, "control plan monitored item"],
  ["T-25", /8\.4 minutes on average from register to handoff/i, "A3 background narrative"],
];
const anchorFails = [];
for (const [toolId, re, label] of ANCHORS) {
  await page.getByTestId(`nav-tool-${toolId}`).click();
  await page.waitForTimeout(450);
  const hay = await page.evaluate(() => {
    const vals = [...document.querySelectorAll("input, textarea")].map((el) => el.value).join("\n");
    return vals + "\n" + document.body.innerText;
  });
  const ok = re.test(hay);
  console.log(`${ok ? "  ok  " : "  MISS"}  ${toolId}  ${label}`);
  if (!ok) anchorFails.push(`${toolId} ${label}`);
}
if (problems.length) console.log("PROBLEMS:\n  " + problems.slice(0, 20).join("\n  "));

await browser.close();
site.close();
const pass = rows.length > 0 && blank.length === 0 && problems.length === 0 && anchorFails.length === 0;
console.log(
  pass
    ? "RESULT: PASS"
    : `RESULT: FAIL (${blank.length} blank, ${anchorFails.length} missing anchors, ${problems.length} problems)`,
);
process.exit(pass ? 0 : 1);
