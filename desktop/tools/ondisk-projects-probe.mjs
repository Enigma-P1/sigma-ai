#!/usr/bin/env node
/** ON-DISK PROJECTS PROBE — is a never-opened project visible?
 *
 * WHY: the Open-a-project screen was backed only by a localStorage
 * recently-opened history, so a project unzipped into the projects folder
 * was invisible in the app — by construction, with no error. That is the
 * bug that cost a morning on the worked example.
 *
 * A route test cannot catch the regression, because the route was never the
 * problem: the screen simply didn't ask. So this uses a FRESH browser
 * context (empty localStorage, exactly like a new machine) and asserts the
 * project shows up anyway.
 *
 * Usage: build the bundle, start an engine over a projects root containing
 * the worked example, then:  node tools/ondisk-projects-probe.mjs
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
const PROBE_PORT = Number(process.env.PROBE_PORT || 4613);
const PROJECT_ID = process.env.PROJECT_ID || "coffee-bar-example";
const HOST = process.env.PROBE_HOST || "tauri.localhost";

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
// A brand-new context every run: empty localStorage is the whole point. If
// this probe ever reused a profile it would pass on the recent list alone
// and prove nothing.
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
await ctx.addInitScript(() => {
  window.__TAURI_INTERNALS__ = { invoke: async () => undefined, transformCallback: (c) => c };
});
const page = await ctx.newPage();
const problems = [];
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));

await page.goto(`http://${HOST}:${PROBE_PORT}/`, { waitUntil: "domcontentloaded" });
await page.getByRole("button", { name: /open a project/i }).first().click().catch(() => {});
await page.getByTestId("ondisk-heading").waitFor({ timeout: 20000 });
await page.waitForTimeout(1200);

const recentCount = await page.locator('[data-testid^="recent-project-"]').count();
const tile = page.getByTestId(`ondisk-project-${PROJECT_ID}`);
const listed = await tile.count();
console.log(`recently-opened entries: ${recentCount} (expected 0 — fresh profile)`);
console.log(`on-disk tile for ${PROJECT_ID}: ${listed > 0 ? "PRESENT" : "MISSING"}`);
if (listed > 0) console.log("tile text:", (await tile.innerText()).replace(/\n/g, " · "));

// And it must actually open from there, not merely be listed.
let opened = false;
if (listed > 0) {
  await tile.click();
  opened = (await page.getByTestId("phase-Define").count()) > 0 ||
    (await page.getByTestId("phase-Define").waitFor({ timeout: 20000 }).then(() => true).catch(() => false));
}
console.log("opened from the on-disk list:", opened);
if (problems.length) console.log("PROBLEMS:\n  " + problems.join("\n  "));

await browser.close();
site.close();
const pass = recentCount === 0 && listed > 0 && opened && problems.length === 0;
console.log(pass ? "RESULT: PASS (a never-opened project is visible and opens)" : "RESULT: FAIL");
process.exit(pass ? 0 : 1);
