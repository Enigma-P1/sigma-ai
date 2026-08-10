#!/usr/bin/env node
/** EXPORT PROBE -- does "Export project" actually put a file on disk?
 *
 * WHY THIS EXISTS: for the whole of v1, the only artifact that could leave
 * this app was the T-03 charter. A user could complete all 23 tools and
 * have nothing to hand anybody, which is the difference between a tool
 * people can use and one they cannot.
 *
 * Testing the ROUTE is not enough. The download path has two failure modes
 * that only exist in a browser, and both produce a button that looks like
 * it worked:
 *   1. The packaged Tauri webview CANCELS every download unless the window
 *      was built with a download handler (src-tauri/src/lib.rs .on_download).
 *      There is no error -- the click just does nothing.
 *   2. The engine is cross-origin from the packaged webview, so the blob
 *      fetch is preflighted; a CORS regression fails it the same silent way
 *      (this is the bug class that already cost two installer builds --
 *      see packaged-sweep.mjs).
 * So this drives a REAL browser, in the packaged origin condition, clicks
 * the real button, and asserts a real PDF landed.
 *
 * Usage -- build the bundle, start an engine on 8756 over a projects root
 * containing the project, then:
 *   node tools/export-project-probe.mjs
 * Env: ENGINE_PORT (8756), PROBE_PORT (4607), PROJECT_ID, OUT (download dir)
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

const PROBE_PORT = Number(process.env.PROBE_PORT || 4607);
const PROJECT_ID = process.env.PROJECT_ID || "coffee-bar-example";
const HOST = process.env.PROBE_HOST || "tauri.localhost";
const OUT = process.env.OUT || fs.mkdtempSync(path.join(os.tmpdir(), "sigma-export-"));

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
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
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
await page.getByTestId("topbar-export-project").waitFor({ timeout: 20000 });

const downloadPromise = page.waitForEvent("download", { timeout: 120000 });
await page.getByTestId("topbar-export-project").click();
const download = await downloadPromise;
const dest = path.join(OUT, download.suggestedFilename());
await download.saveAs(dest);

const bytes = fs.readFileSync(dest);
const isPdf = bytes.subarray(0, 5).toString() === "%PDF-";
const pages = (bytes.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
const inlineError = await page.getByTestId("topbar-export-error").count();

console.log(`file      : ${dest}`);
console.log(`filename  : ${download.suggestedFilename()}`);
console.log(`bytes     : ${bytes.length}`);
console.log(`is pdf    : ${isPdf}`);
console.log(`pages     : ${pages}`);
console.log(`inline err: ${inlineError ? await page.getByTestId("topbar-export-error").innerText() : "none"}`);
if (problems.length) console.log("PROBLEMS:\n  " + problems.slice(0, 10).join("\n  "));

await browser.close();
site.close();
const pass = isPdf && bytes.length > 20000 && pages >= 5 && inlineError === 0 && problems.length === 0;
console.log(pass ? "RESULT: PASS (a real PDF reached the disk)" : "RESULT: FAIL");
process.exit(pass ? 0 : 1);
