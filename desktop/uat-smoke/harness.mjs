/** UAT HARNESS — put a real user in front of the real app.
 *
 * Serves the PRODUCTION bundle (desktop/dist) from its own origin and
 * injects window.__TAURI_INTERNALS__, which is exactly what the installed
 * app does: cross-origin engine calls, real CORS, real download handling.
 * See desktop/tools/packaged-sweep.mjs for why that condition matters.
 *
 * ONE DIFFERENCE FROM THE SHIPPED APP, ON PURPOSE: the client hard-codes
 * the sidecar at 127.0.0.1:8756, and two testers running at once cannot
 * share one port. So window.fetch rewrites 8756 -> the port this run was
 * given. Still absolute, still cross-origin, still preflighted — only the
 * port differs.
 *
 * Usage from a step script:
 *
 *   import { openApp } from "/tmp/uat/harness.mjs";
 *   const app = await openApp({ enginePort: 8801, out: "/tmp/uat/dave", chunk: "01-first-open" });
 *   await app.shot("welcome", "what the app shows before I touch anything");
 *   app.note("step 1", "expected a welcome screen", "got X");
 *   await app.close();
 */
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
// docs/uat/method -> desktop/dist. Overridable so the harness can be copied
// somewhere scratch and still find a bundle.
const DIST = process.env.SIGMA_DIST || path.resolve(HERE, "..", "..", "..", "desktop", "dist");
const CHROMIUM_PATH = "/opt/pw-browsers/chromium";

const MIME = {
  ".html": "text/html", ".js": "text/javascript", ".css": "text/css",
  ".svg": "image/svg+xml", ".json": "application/json",
  ".woff2": "font/woff2", ".woff": "font/woff", ".png": "image/png",
  ".jpg": "image/jpeg", ".ico": "image/x-icon",
};

export async function openApp({ enginePort, out, chunk, sitePort, viewport }) {
  if (!fs.existsSync(path.join(DIST, "index.html"))) throw new Error("no desktop/dist — run npm run build");
  fs.mkdirSync(path.join(out, "shots"), { recursive: true });
  fs.mkdirSync(path.join(out, "video"), { recursive: true });

  const port = sitePort || 4700 + (enginePort % 100);
  const site = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = path.join(DIST, rel);
    if (!file.startsWith(DIST) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(DIST, "index.html");
    res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
    res.end(fs.readFileSync(file));
  });
  await new Promise((r) => site.listen(port, r));

  const browser = await chromium.launch(fs.existsSync(CHROMIUM_PATH) ? { executablePath: CHROMIUM_PATH } : {});
  const ctx = await browser.newContext({
    viewport: viewport || { width: 1440, height: 950 },
    acceptDownloads: true,
    recordVideo: { dir: path.join(out, "video"), size: viewport || { width: 1440, height: 950 } },
  });
  await ctx.addInitScript(`
    window.__TAURI_INTERNALS__ = { invoke: async () => undefined, transformCallback: (c) => c };
    const _fetch = window.fetch;
    window.fetch = (input, init) => {
      const url = typeof input === "string" ? input : (input && input.url) || String(input);
      if (url.includes("127.0.0.1:8756")) {
        return _fetch(url.replace("127.0.0.1:8756", "127.0.0.1:${enginePort}"), init);
      }
      return _fetch(input, init);
    };
  `);

  const page = await ctx.newPage();
  const problems = [];
  page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text().slice(0, 300)}`); });
  page.on("response", (r) => { if (r.status() >= 400) problems.push(`http ${r.status()} ${r.request().method()} ${r.url()}`); });

  const transcript = path.join(out, `transcript-${chunk}.md`);
  const shotsDir = path.join(out, "shots");
  let shotN = 0;
  fs.appendFileSync(transcript, `# ${chunk}\n\n`);

  await page.goto(`http://tauri.localhost:${port}/`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);

  const app = {
    page, ctx, browser, problems, out,

    /** A screenshot with a caption. Returns the file path. */
    async shot(name, caption = "") {
      shotN += 1;
      const file = path.join(shotsDir, `${chunk}-${String(shotN).padStart(2, "0")}-${name}.png`);
      await page.screenshot({ path: file, fullPage: false });
      fs.appendFileSync(transcript, `![${name}](${path.relative(out, file)})\n_${caption}_\n\n`);
      console.log(`SHOT ${file}  ${caption}`);
      return file;
    },

    /** Full-page screenshot, for when the screen is taller than the window. */
    async shotFull(name, caption = "") {
      shotN += 1;
      const file = path.join(shotsDir, `${chunk}-${String(shotN).padStart(2, "0")}-${name}-full.png`);
      await page.screenshot({ path: file, fullPage: true });
      fs.appendFileSync(transcript, `![${name}](${path.relative(out, file)})\n_${caption}_\n\n`);
      console.log(`SHOT ${file}  ${caption}`);
      return file;
    },

    /** One plan step: what was tried, what was expected, what happened. */
    note(step, expected, actual) {
      fs.appendFileSync(transcript, `**${step}**\n\n- expected: ${expected}\n- actual: ${actual}\n\n`);
      console.log(`NOTE ${step}\n  expected: ${expected}\n  actual:   ${actual}`);
    },

    /** Free text into the transcript. */
    say(text) {
      fs.appendFileSync(transcript, `${text}\n\n`);
      console.log(text);
    },

    /** Every word visible on screen right now — for "what does it actually say". */
    async text() {
      return (await page.locator("body").innerText()).replace(/\n{3,}/g, "\n\n");
    },

    /** Click whatever is on screen with this visible name, like a person would. */
    async clickText(name, opts = {}) {
      await page.getByRole("button", { name }).first().click({ timeout: opts.timeout || 10000 });
      await page.waitForTimeout(opts.settle ?? 600);
    },

    /** Download whatever the click produces; saves under out/files. */
    async download(clickFn, label) {
      fs.mkdirSync(path.join(out, "files"), { recursive: true });
      const dl = page.waitForEvent("download", { timeout: 90000 });
      await clickFn();
      const d = await dl;
      const dest = path.join(out, "files", d.suggestedFilename());
      await d.saveAs(dest);
      const bytes = fs.statSync(dest).size;
      fs.appendFileSync(transcript, `- downloaded **${d.suggestedFilename()}** (${bytes} bytes) — ${label || ""}\n\n`);
      console.log(`FILE ${dest} ${bytes} bytes`);
      return dest;
    },

    async close() {
      if (problems.length) {
        fs.appendFileSync(transcript, `\n### Things the browser reported (not visible to the user)\n\n` +
          problems.map((p) => `- ${p}`).join("\n") + "\n\n");
        console.log("PROBLEMS:\n  " + problems.slice(0, 20).join("\n  "));
      }
      const video = page.video();
      await ctx.close();
      await browser.close();
      site.close();
      if (video) {
        const dest = path.join(out, "video", `${chunk}.webm`);
        try { fs.renameSync(await video.path(), dest); console.log(`VIDEO ${dest}`); } catch { /* already moved */ }
      }
      console.log(`TRANSCRIPT ${transcript}`);
    },
  };
  return app;
}

/** Convenience: open an existing project by id from the start screen. */
export async function openProject(app, projectId) {
  const { page } = app;
  await page.getByRole("button", { name: /open a project/i }).first().click().catch(() => {});
  await page.getByTestId("open-project-id").waitFor({ timeout: 20000 });
  await page.getByTestId("open-project-id").fill(projectId);
  await page.getByTestId("open-project-submit").click();
  await page.getByTestId("phase-Define").waitFor({ timeout: 20000 });
  await page.waitForTimeout(500);
}
