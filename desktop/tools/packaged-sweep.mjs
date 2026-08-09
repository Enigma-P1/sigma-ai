#!/usr/bin/env node
/** PACKAGED-CONDITION SWEEP -- the installed app's failure modes, for free.
 *
 * WHY THIS EXISTS: two bugs reached a real user and each cost a paid
 * Windows+Mac installer build to find, because every test we had loaded the
 * UI from Vite. Vite PROXIES the engine same-origin (/engine-api ->
 * 127.0.0.1:8000), so the browser never preflights and never resolves an
 * absolute cross-origin engine URL. The packaged app is the opposite: the
 * webview origin is http://tauri.localhost (Windows) / tauri://localhost
 * (mac) and it calls the engine at an ABSOLUTE http://127.0.0.1:8756.
 *
 * This script reproduces that condition with no installer and no CI:
 *   1. serves desktop/dist (the PRODUCTION build, not the dev server) from
 *      its own origin, so the engine really is cross-origin;
 *   2. injects window.__TAURI_INTERNALS__ before any app code runs, which is
 *      exactly what Tauri v2 does, so isTauriRuntime() takes the packaged
 *      branch and resolveEngineBaseUrl() returns the absolute sidecar URL;
 *   3. drives a real Chromium through a substantial DMAIC flow against a
 *      live engine, failing on any console error, page error, failed
 *      request, or unexpected >=400 response.
 *
 * It is deliberately stricter than tools/smoke-browser.mjs: that one only
 * fails on page errors, this one fails on network faults too, because the
 * packaged bugs we shipped WERE network faults.
 *
 * Usage -- build the production bundle first, then start an engine on 8756
 * with an isolated projects root, then run the sweep:
 *
 *   cd desktop && npm run build
 *   cd engine && SIGMA_PROJECTS_ROOT=/tmp/sweep-projects \
 *     .venv/bin/python -m sigma_engine.main --port 8756
 *   cd desktop && node tools/packaged-sweep.mjs
 *
 * Run it a SECOND time against the frozen sidecar, which is what actually
 * ships -- that is the only local way to catch a PyInstaller-only failure
 * (missing hidden import, missing data file, ReportLab fonts):
 *
 *   cd engine && .venv/bin/pyinstaller sigma_engine.spec --noconfirm
 *   SIGMA_PROJECTS_ROOT=/tmp/sweep-projects ./dist/sigma-engine --port 8756
 *
 * Env:
 *   ENGINE_PORT  default 8756 -- must match TAURI_SIDECAR_BASE_URL in
 *                src/api/runtime.ts, which is a hardcoded constant; any
 *                other value cannot be reached by the packaged branch and
 *                the script refuses to pretend otherwise.
 *   SWEEP_PORT   default 4599 -- the origin the production build is served
 *                from.
 *   SWEEP_HOST   default "tauri.localhost" -- a *.localhost name Chromium
 *                resolves to loopback, so the page origin reads
 *                http://tauri.localhost:<port>, the closest local analogue
 *                to the real Windows webview origin. Set to "localhost" if
 *                the *.localhost resolution ever misbehaves.
 */
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ENGINE_PORT = Number(process.env.ENGINE_PORT || 8756);
const SWEEP_PORT = Number(process.env.SWEEP_PORT || 4599);
const SWEEP_HOST = process.env.SWEEP_HOST || "tauri.localhost";
const CHROMIUM_PATH = process.env.PW_CHROMIUM_PATH || "/opt/pw-browsers/chromium";
const TIMEOUT_MS = 30_000;

const ENGINE_ORIGIN = `http://127.0.0.1:${ENGINE_PORT}`;
const APP_ORIGIN = `http://${SWEEP_HOST}:${SWEEP_PORT}`;

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.join(SCRIPT_DIR, "..", "dist");
const FIXTURE_CSV_PATH = path.join(SCRIPT_DIR, "fixtures", "coffee-bar-wait-times.csv");
const FIXTURE_LABEL = "coffee-bar-wait-times.csv (24 rows)";
const FIXTURE_PNG_PATH = path.join(SCRIPT_DIR, "fixtures", "floorplan-fixture.png");

const CRITERIA_KEYS = [
  "scope_narrow",
  "measurable_outcome",
  "data_obtainable",
  "process_owner_engaged",
  "business_impact_plausible",
];

// ---------------------------------------------------------------------------
// Failure collectors. Everything here is a hard fail unless explicitly
// allow-listed below -- the whole point of this sweep is that a packaged bug
// shows up as a network fault, not as a thrown assertion.
// ---------------------------------------------------------------------------
const steps = [];
const pageErrors = [];
const consoleErrors = [];
const failedRequests = [];
const badResponses = [];
const engineRequestUrls = new Set();

/** Deliberate refusals: the engine says no ON PURPOSE and the UI renders
 * that refusal. Allow-listed by (method, url-substring, status) so a real
 * regression on the same route with a different status still fails. Each
 * entry must be armed by the step that expects it (`expectRefusal`) so a
 * refusal firing at the wrong moment is still caught. */
const armedRefusals = [];

/** Set only by the steps that deliberately cut the engine off (the failure-
 * gate step), so the aborts they cause aren't reported as findings. */
let suppressRequestFailures = false;

/** "live" | "slow" | "dead" -- drives the /health interceptor used by the
 * two engine-gate steps. Every other step runs with the engine live. */
let healthMode = "live";

/** Set only by the route-coverage probe, which deliberately calls every
 * endpoint with a nonexistent id: its 404s/422s are the expected answer and
 * the step asserts on them directly rather than through the collectors. */
let corsProbeMode = false;

function armRefusal(match, note) {
  armedRefusals.push({ ...match, note, seen: 0 });
}

function isArmedRefusal(method, url, status) {
  for (const r of armedRefusals) {
    if (r.method === method && url.includes(r.url) && r.status === status) {
      r.seen += 1;
      return true;
    }
  }
  return false;
}

function log(status, name, detail) {
  const line = `[${status}] ${name}${detail ? " -- " + detail : ""}`;
  console.log(line);
  steps.push({ status, name, detail });
}

async function step(name, fn) {
  try {
    await fn();
    log("PASS", name);
  } catch (err) {
    log("FAIL", name, err instanceof Error ? err.message : String(err));
    throw err;
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function numeric(text) {
  if (text == null) return NaN;
  return Number(text.replace(/[^\d.-]/g, ""));
}

// ---------------------------------------------------------------------------
// Static server for the PRODUCTION build. Plain http on its own origin --
// that separation is what makes the browser enforce CORS the way the
// packaged webview does.
// ---------------------------------------------------------------------------
const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".map": "application/json; charset=utf-8",
};

function startStaticServer() {
  const server = http.createServer((req, res) => {
    let urlPath = decodeURIComponent(new URL(req.url, APP_ORIGIN).pathname);
    if (urlPath.endsWith("/")) urlPath += "index.html";
    let filePath = path.join(DIST_DIR, path.normalize(urlPath));
    // Directory traversal guard -- trivial here, but this server is a real
    // http server and should not be able to serve outside dist/.
    if (!filePath.startsWith(DIST_DIR)) {
      res.writeHead(403).end("forbidden");
      return;
    }
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      // SPA fallback, same as any static host serving a Vite build.
      filePath = path.join(DIST_DIR, "index.html");
    }
    const body = fs.readFileSync(filePath);
    res.writeHead(200, {
      "content-type": MIME[path.extname(filePath)] || "application/octet-stream",
      "cache-control": "no-store",
    });
    res.end(body);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(SWEEP_PORT, "127.0.0.1", () => resolve(server));
  });
}

// ---------------------------------------------------------------------------
// The Tauri v2 global, injected before any app code runs. Tauri v2 defines
// window.__TAURI_INTERNALS__ in the webview's initialization script; the
// app's isTauriRuntime() keys off exactly that, so defining it here makes
// the production bundle take the packaged branch with NO source change.
// invoke() is stubbed to the two commands src-tauri/src/lib.rs actually
// registers, and throws for anything else -- same as the real IPC would.
// ---------------------------------------------------------------------------
const TAURI_INIT_SCRIPT = `
(() => {
  const SIDECAR_LOG = "/tmp/sigma-ai-packaged-sweep/sidecar.log";
  window.__TAURI_INTERNALS__ = {
    metadata: { currentWindow: { label: "main" }, currentWebview: { label: "main", windowLabel: "main" } },
    plugins: {},
    transformCallback(callback) {
      const id = Math.floor(Math.random() * 2 ** 32);
      Object.defineProperty(window, "_" + id, { value: callback, writable: true, configurable: true });
      return id;
    },
    convertFileSrc(filePath) { return filePath; },
    async invoke(cmd) {
      if (cmd === "sidecar_log_path") return SIDECAR_LOG;
      if (cmd === "sidecar_log_tail") return "";
      throw new Error("packaged-sweep: unregistered Tauri command " + cmd);
    },
  };
  window.__TAURI_EVENT_PLUGIN_INTERNALS__ = { unregisterListener() {} };
})();
`;

async function main() {
  if (!fs.existsSync(path.join(DIST_DIR, "index.html"))) {
    console.error(`No production build at ${DIST_DIR}. Run \`npm run build\` in desktop/ first.`);
    process.exit(1);
  }
  if (ENGINE_PORT !== 8756) {
    console.error(
      `ENGINE_PORT=${ENGINE_PORT}, but src/api/runtime.ts hardcodes the packaged sidecar URL as ` +
        `http://127.0.0.1:8756. The packaged branch cannot reach any other port, so this sweep would ` +
        `silently test nothing. Run the engine on 8756.`,
    );
    process.exit(1);
  }

  // Fail fast and clearly if the engine isn't up -- otherwise every step
  // below fails for the same uninteresting reason.
  try {
    const probe = await fetch(`${ENGINE_ORIGIN}/health`);
    if (!probe.ok) throw new Error(`HTTP ${probe.status}`);
  } catch (err) {
    console.error(`Engine not reachable at ${ENGINE_ORIGIN}/health: ${err.message}`);
    console.error("Start it first, e.g. SIGMA_PROJECTS_ROOT=/tmp/sweep .venv/bin/python -m sigma_engine.main --port 8756");
    process.exit(1);
  }

  let site;
  try {
    site = await startStaticServer();
  } catch (err) {
    console.error(`Could not bind the static server on ${SWEEP_PORT}: ${err.message}. Set SWEEP_PORT.`);
    process.exit(1);
  }
  console.log(`app origin:    ${APP_ORIGIN} (production build from ${DIST_DIR})`);
  console.log(`engine origin: ${ENGINE_ORIGIN}`);
  console.log("");

  const browser = await chromium.launch({
    executablePath: CHROMIUM_PATH,
    args: [
      "--no-sandbox",
      // Resolve the *.localhost app host to loopback explicitly, so the page
      // origin is a real cross-origin peer of 127.0.0.1 regardless of the
      // container's resolver.
      `--host-resolver-rules=MAP ${SWEEP_HOST} 127.0.0.1`,
      // Chromium's Local Network Access checks block a page in a less
      // private address space from reaching loopback. WebView2 is Chromium
      // and will inherit this; the whole app is a webview talking to
      // 127.0.0.1, so run the sweep with the checks ON. Verified locally
      // that a public-space origin IS blocked under this flag ("the request
      // client is not a secure context and the resource is in more-private
      // address space `loopback`") while the packaged-shaped
      // http://tauri.localhost origin is not -- so this asserts something
      // real rather than being decoration.
      "--enable-features=LocalNetworkAccessChecks",
    ],
  });
  const context = await browser.newContext({ acceptDownloads: true });
  await context.addInitScript(TAURI_INIT_SCRIPT);
  const page = await context.newPage();
  page.setDefaultTimeout(TIMEOUT_MS);

  page.on("pageerror", (err) => {
    pageErrors.push(err.message);
    console.error(`[PAGE ERROR] ${err.message}`);
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      // The failure-gate step cuts the engine off on purpose; the browser's
      // "Failed to load resource" noise from that is expected, not a finding.
      if (suppressRequestFailures || corsProbeMode) return;
      // Chromium echoes EVERY non-2xx fetch and every transport error as a
      // console error with no method and no way to tell a deliberate
      // refusal from a regression. The response/requestfailed listeners
      // above already cover both cases with full URL + method + status
      // precision, so this echo carries no information the sweep doesn't
      // already check -- dropping it is what keeps the armed-refusal
      // allow-list meaningful instead of blanket-muting console errors.
      if (msg.text().startsWith("Failed to load resource:")) return;
      consoleErrors.push(msg.text());
      console.error(`[CONSOLE ERROR] ${msg.text()}`);
    }
  });
  page.on("requestfailed", (req) => {
    const failure = req.failure()?.errorText ?? "unknown";
    // Playwright reports an aborted download as a failed request; the
    // download itself is asserted separately.
    if (failure === "net::ERR_ABORTED" && req.url().startsWith("blob:")) return;
    if (suppressRequestFailures || corsProbeMode) return;
    failedRequests.push(`${req.method()} ${req.url()} -- ${failure}`);
    console.error(`[REQUEST FAILED] ${req.method()} ${req.url()} -- ${failure}`);
  });
  page.on("response", (res) => {
    const url = res.url();
    const method = res.request().method();
    if (url.startsWith(ENGINE_ORIGIN)) engineRequestUrls.add(`${method} ${url}`);
    if (res.status() >= 400) {
      if (corsProbeMode) return;
      if (isArmedRefusal(method, url, res.status())) return;
      badResponses.push(`${method} ${url} -- HTTP ${res.status()}`);
      console.error(`[BAD RESPONSE] ${method} ${url} -- HTTP ${res.status()}`);
    }
  });

  const runId = Date.now();
  const projectName = `Packaged Sweep ${runId}`;

  try {
    await runFlow(page, projectName);
  } catch (err) {
    await finish(browser, site, false, err);
    return;
  }
  await finish(browser, site, true, null);
}

/** Static packaging invariants -- the packaged-only failures that no browser
 * can observe, because they live in the Tauri shell rather than in the page.
 * A grep-and-parse check is a weak instrument, and it is used here only
 * where the alternative is no check at all (verifying these for real needs
 * a Mac and a signed build). Each one is a bug that already has a root
 * cause and a fix in this repo; the assertion exists so the fix cannot be
 * silently undone. */
function checkStaticPackagingInvariants() {
  const confPath = path.join(SCRIPT_DIR, "..", "src-tauri", "tauri.conf.json");
  const libPath = path.join(SCRIPT_DIR, "..", "src-tauri", "src", "lib.rs");
  const conf = JSON.parse(fs.readFileSync(confPath, "utf8"));
  const lib = fs.readFileSync(libPath, "utf8");

  const mainWindow = conf.app?.windows?.[0];
  assert(mainWindow, "tauri.conf.json defines no window");
  // If the window goes back to being created from config, Tauri builds it
  // with no download handler, and on macOS wry answers every <a download>
  // navigation with Cancel -- the charter's Export PDF button then does
  // nothing at all, silently. See the comment on the builder in lib.rs.
  assert(
    mainWindow.create === false,
    'tauri.conf.json\'s main window must keep "create": false -- a config-created window cannot carry the download handler macOS needs for Export PDF',
  );
  assert(
    lib.includes(".on_download("),
    "src-tauri/src/lib.rs must build the main window with .on_download(...) -- without it macOS silently cancels the charter PDF download",
  );
  assert(
    lib.includes("WebviewWindowBuilder::from_config"),
    "src-tauri/src/lib.rs must create the main window itself now that tauri.conf.json has create:false, or the app opens with no window at all",
  );
  log("PASS", "static packaging invariants (window/download wiring in the Tauri shell)");
}

async function runFlow(page, projectName) {
  checkStaticPackagingInvariants();

  // -- Packaging preconditions -------------------------------------------

  await step("load the production build from a cross-origin host, in the Tauri branch", async () => {
    await page.goto(`${APP_ORIGIN}/`, { waitUntil: "domcontentloaded" });
    const isTauri = await page.evaluate(() => "__TAURI_INTERNALS__" in window);
    assert(isTauri, "window.__TAURI_INTERNALS__ was not injected before app code ran");
    // The readiness gate is Tauri-only, and it resolves by polling the
    // ABSOLUTE sidecar /health. Reaching the create-project screen at all
    // therefore proves the packaged branch ran and cross-origin /health
    // succeeded; step 2 below proves the URL was absolute, not proxied.
    await page.locator('[data-testid="create-project-name"]').waitFor();
  });

  await step("every engine call resolved to the ABSOLUTE sidecar URL, not the dev proxy", async () => {
    const seen = [...engineRequestUrls];
    assert(seen.length > 0, "no request to the absolute engine origin was observed -- the app is not using the packaged branch");
    assert(
      seen.some((u) => u.includes(`${ENGINE_ORIGIN}/health`)),
      `expected a GET ${ENGINE_ORIGIN}/health from the readiness gate, saw ${JSON.stringify(seen)}`,
    );
    const proxied = await page.evaluate(() =>
      performance.getEntriesByType("resource").map((e) => e.name).filter((n) => n.includes("/engine-api/")),
    );
    assert(proxied.length === 0, `the app hit the Vite dev-proxy path under packaged conditions: ${JSON.stringify(proxied)}`);
  });

  await step("a cross-origin preflight really happened (packaged condition confirmed)", async () => {
    // A JSON POST from a different origin is a non-simple request, so the
    // browser MUST have sent an OPTIONS first. If the engine had no CORS
    // middleware this is the exact call that 405s.
    const out = await page.evaluate(async (origin) => {
      const res = await fetch(`${origin}/health`, {
        method: "GET",
        headers: { "content-type": "application/json" },
      });
      return { status: res.status, allowOrigin: res.headers.get("access-control-allow-origin") };
    }, ENGINE_ORIGIN);
    assert(out.status === 200, `cross-origin GET with a content-type header returned ${out.status}`);
  });

  // -- The readiness gate: packaged-only UI. It exists because the onefile
  // sidecar takes seconds to self-extract, and it is the screen the first
  // installed user actually saw. Neither phase is reachable from the dev
  // smoke, which never enters the Tauri branch. ---------------------------

  // One persistent interceptor whose behaviour is switched by `healthMode`;
  // installing/removing routes mid-flight races the in-flight handlers.
  await page.route(`${ENGINE_ORIGIN}/health`, async (route) => {
    if (healthMode === "slow") await new Promise((r) => setTimeout(r, 2500));
    if (healthMode === "dead") {
      await route.abort("connectionrefused").catch(() => {});
      return;
    }
    await route.continue().catch(() => {});
  });

  await step("engine gate: the 'starting' phase renders while the sidecar is slow", async () => {
    // The reload below aborts whatever /health poll is already in flight;
    // that abort is this step's own doing, not a finding.
    suppressRequestFailures = true;
    healthMode = "slow";
    await page.reload({ waitUntil: "domcontentloaded" });
    const gate = page.locator('[data-testid="engine-gate"]');
    await gate.waitFor();
    const text = await gate.textContent();
    assert(text?.includes("Starting the engine"), `expected the starting gate copy, got ${JSON.stringify(text)}`);
    healthMode = "live";
    await page.locator('[data-testid="create-project-name"]').waitFor();
  });

  await step("engine gate: the 'failed' phase is self-diagnosing (log path from the Tauri IPC)", async () => {
    suppressRequestFailures = true;
    healthMode = "dead";
    await page.reload({ waitUntil: "domcontentloaded" });
    // useEngineReadiness gives up after 30s, then asks Rust for the log.
    const retry = page.locator('[data-testid="engine-gate-retry"]');
    await retry.waitFor({ timeout: 60_000 });
    const text = await page.locator('[data-testid="engine-gate"]').textContent();
    assert(text?.includes("The engine didn't start"), `expected the failure gate copy, got ${JSON.stringify(text)}`);
    assert(
      text?.includes("sidecar.log"),
      `the failure gate must show the sidecar log path it got over Tauri IPC, got ${JSON.stringify(text)}`,
    );
    // Retry, with the engine reachable again, must recover in place.
    healthMode = "live";
    await retry.click();
    await page.locator('[data-testid="create-project-name"]').waitFor();
    suppressRequestFailures = false;
  });

  // -- Project + Define ---------------------------------------------------

  await step("create project", async () => {
    await page.locator('[data-testid="create-project-name"]').fill(projectName);
    await page.locator('[data-testid="create-project-submit"]').click();
    await page.locator('[data-testid="topbar-project-name"]').waitFor();
    const shown = await page.locator('[data-testid="topbar-project-name"]').textContent();
    assert(shown?.trim() === projectName, `top bar shows ${JSON.stringify(shown)}, expected ${JSON.stringify(projectName)}`);
  });

  await step("T-01 Project Picker: fill to a full-DMAIC route and save", async () => {
    await page.locator('[data-testid="nav-tool-T-01"]').click();
    await page.locator('[data-testid="picker-save"]').waitFor();
    for (const key of CRITERIA_KEYS) {
      await page.locator(`[data-testid="picker-${key}-yes"]`).click();
      await page.locator(`[data-testid="picker-${key}-detail"]`).fill(`Packaged-sweep evidence for ${key}.`);
    }
    await page.locator('[data-testid="picker-route-full-DMAIC"]').click();
    await page.locator('[data-testid="picker-save"]').click();
    await page.locator('[data-testid="picker-version-badge"]').waitFor();
    const badge = await page.locator('[data-testid="picker-version-badge"]').textContent();
    assert(badge?.includes("v1"), `expected version badge to show v1, got ${JSON.stringify(badge)}`);
  });

  await step("T-03 Charter: fill a solution-shaped problem statement and save", async () => {
    await page.locator('[data-testid="nav-tool-T-03"]').click();
    await page.locator('[data-testid="charter-save"]').waitFor();

    await page.locator('[data-testid="charter-problem-what"]').fill("Train the operators on the new molding process");
    await page.locator('[data-testid="charter-problem-where"]').fill("Line 2, Plant A");
    await page.locator('[data-testid="charter-problem-when"]').fill("Q2 2026");
    await page.locator('[data-testid="charter-magnitude-number"]').fill("6.2");
    await page.locator('[data-testid="charter-magnitude-unit"]').fill("%");
    await page.locator('[data-testid="charter-magnitude-period"]').fill("Q2 2026");

    await page.locator('[data-testid="charter-goal-statement"]').fill("Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026.");
    await page.locator('[data-testid="charter-goal-metric-name"]').fill("line-2 scrap rate");
    await page.locator('[data-testid="charter-goal-baseline"]').fill("6.2");
    await page.locator('[data-testid="charter-goal-target"]').fill("3");
    await page.locator('[data-testid="charter-goal-unit"]').fill("%");
    await page.locator('[data-testid="charter-goal-target-date"]').fill("2026-11-30");

    await page.locator('[data-testid="charter-scope-in"]').fill("Line 2 molding station only");
    await page.locator('[data-testid="charter-scope-out"]').fill("Lines 1 and 3, packaging");
    await page.locator('[data-testid="charter-owner-name"]').fill("Maria Ortiz");
    await page.locator('[data-testid="charter-owner-role"]').fill("Line-2 supervisor");
    await page.locator('[data-testid="charter-team-0-name"]').fill("Maria Ortiz");
    await page.locator('[data-testid="charter-team-0-role"]').fill("Line-2 supervisor");
    await page.locator('[data-testid="charter-timeline-0-name"]').fill("Define complete");
    await page.locator('[data-testid="charter-timeline-0-date"]').fill("2026-08-21");
    await page.locator('[data-testid="charter-impact-amount"]').fill("40000");
    await page.locator('[data-testid="charter-impact-unit"]').fill("dollars");
    await page.locator('[data-testid="charter-impact-basis"]').fill("Q2 actuals x 4");

    await page.locator('[data-testid="charter-save"]').click();
    await page.locator('[data-testid="charter-version-badge"]').waitFor();
    const badge = await page.locator('[data-testid="charter-version-badge"]').textContent();
    assert(badge?.includes("v1"), `expected version badge to show v1, got ${JSON.stringify(badge)}`);
  });

  await step("prescore strip renders the solution-language flag (cross-origin POST /prescore)", async () => {
    const pill = page.locator('[data-testid="prescore-check-problem_statement_solution_language"]');
    await pill.waitFor();
    const status = await pill.getAttribute("data-status");
    assert(status === "flag", `expected prescore check status "flag", got ${JSON.stringify(status)}`);
    const text = await pill.textContent();
    assert(
      text?.toLowerCase().includes("solution language"),
      `expected the pill's label to mention solution language, got ${JSON.stringify(text)}`,
    );
    const whatField = page.locator('[data-testid="charter-problem-what"]').locator("..");
    await whatField.locator(".sigma-field__flag-message").waitFor();
  });

  // -- PDF export: a cross-origin BINARY GET. Frozen-binary builds commonly
  // lack ReportLab's font/data files, and a blob download from a non-file
  // origin is its own packaged-only path -- neither is reachable from the
  // dev smoke, which only checks the button's enabled state. ---------------

  await step("Export PDF actually downloads a real PDF cross-origin", async () => {
    const exportBtn = page.locator('[data-testid="charter-export-pdf"]');
    await exportBtn.waitFor();
    assert(await exportBtn.isEnabled(), "Export PDF button should be enabled once a charter version is saved");

    const downloadPromise = page.waitForEvent("download", { timeout: TIMEOUT_MS });
    await exportBtn.click();
    const download = await downloadPromise;
    const file = await download.path();
    assert(file, "the PDF download produced no file on disk");
    const bytes = fs.readFileSync(file);
    assert(bytes.length > 1000, `the exported PDF is suspiciously small (${bytes.length} bytes)`);
    assert(
      bytes.subarray(0, 5).toString("latin1") === "%PDF-",
      `the exported file is not a PDF (first bytes: ${JSON.stringify(bytes.subarray(0, 16).toString("latin1"))})`,
    );
    assert(
      (await page.locator('[data-testid="charter-form"] .sigma-verdict--fail').count()) === 0,
      "the charter panel rendered an export error banner",
    );
  });

  // -- COPQ / SIPOC / gates ------------------------------------------------

  await step("T-02 COPQ: two rows save and the engine-computed total renders", async () => {
    await page.locator('[data-testid="nav-tool-T-02"]').click();
    await page.locator('[data-testid="copq-save"]').waitFor();
    await page.locator('[data-testid="copq-row-0-quantity"]').fill("500");
    await page.locator('[data-testid="copq-row-0-rate"]').fill("12");
    await page.locator('[data-testid="copq-row-0-period"]').fill("Q2 2026");
    await page.locator('[data-testid="copq-row-0-basis"]').fill("Q2 scrap log export");
    await page.getByRole("button", { name: "+ Add cost row" }).click();
    await page.locator('[data-testid="copq-row-1-category"]').selectOption("rework");
    await page.locator('[data-testid="copq-row-1-quantity"]').fill("80");
    await page.locator('[data-testid="copq-row-1-rate"]').fill("45");
    await page.locator('[data-testid="copq-row-1-period"]').fill("Q2 2026");
    await page.locator('[data-testid="copq-row-1-basis"]').fill("labor hours x loaded rate");

    await page.locator('[data-testid="copq-save"]').click();
    await page.locator('[data-testid="copq-version-badge"]').waitFor();
    await page.waitForFunction(() => document.querySelector('[data-testid="copq-row-0-amount"]')?.value !== "not yet computed");
    const totalHeadline = await page.locator('[data-testid="copq-total"] .sigma-verdict__headline').textContent();
    assert(
      totalHeadline?.includes("$9,600"),
      `expected the server-computed total to read $9,600, got ${JSON.stringify(totalHeadline)}`,
    );
  });

  await step("T-04 SIPOC: five steps save and the step-count prescore reads clean", async () => {
    await page.locator('[data-testid="nav-tool-T-04"]').click();
    await page.locator('[data-testid="sipoc-save"]').waitFor();
    await page.locator('[data-testid="sipoc-supplier-0"]').fill("Resin vendor");
    await page.locator('[data-testid="sipoc-input-0"]').fill("Raw resin pellets");
    const stepNames = ["Receive order", "Prep", "Mold", "Inspect", "Package"];
    await page.locator('[data-testid="sipoc-step-0"]').fill(stepNames[0]);
    for (let i = 1; i < stepNames.length; i++) {
      await page.getByRole("button", { name: "+ Add step" }).click();
      await page.locator(`[data-testid="sipoc-step-${i}"]`).fill(stepNames[i]);
    }
    await page.locator('[data-testid="sipoc-scope-start"]').fill("Order received");
    await page.locator('[data-testid="sipoc-scope-end"]').fill("Order handed off");
    await page.locator('[data-testid="sipoc-output-0"]').fill("Molded part");
    await page.locator('[data-testid="sipoc-customer-0"]').fill("Assembly line");
    await page.locator('[data-testid="sipoc-save"]').click();
    await page.locator('[data-testid="sipoc-version-badge"]').waitFor();
    const pill = page.locator('[data-testid="prescore-check-step_count_range"]');
    await pill.waitFor();
    assert((await pill.getAttribute("data-status")) === "pass", "expected 5 steps to read a clean step-count range");
  });

  await step("gates: the Define exit gate soft-blocks and an override clears it with a note", async () => {
    await page.locator('[data-testid="nav-tool-T-06"]').click();
    await page.locator('[data-testid="gate-override-open"]').waitFor();
    const overrideReason = "Charter, COPQ, and SIPOC are done; unblocking Measure prep while VoC/CTQ is finished.";
    await page.locator('[data-testid="gate-override-open"]').click();
    await page.locator('[data-testid="gate-override-reason"]').fill(overrideReason);
    await page.locator('[data-testid="gate-override-submit"]').click();
    const clearedNote = page.locator(".sigma-verdict", { hasText: "cleared, override logged" });
    await clearedNote.waitFor();
    const bannerText = await clearedNote.textContent();
    assert(bannerText?.includes(overrideReason), "expected the cleared-with-note banner to include the logged override reason");
  });

  await step("T-05 VoC -> CTQ: build one statement -> need -> CTQ and save", async () => {
    await page.locator('[data-testid="nav-tool-T-05"]').click();
    await page.locator('[data-testid="voc-ctq-save"]').waitFor();
    await page.locator('[data-testid="voc-customer-0-role"]').fill("external - end buyer");
    await page.locator('[data-testid="voc-statement-0-role"]').fill("external - end buyer");
    await page.locator('[data-testid="voc-statement-0-text"]').fill("Parts sometimes arrive cracked.");
    await page.locator('[data-testid="voc-statement-0-detail"]').fill("2026 Q2 complaint log");
    await page.locator('[data-testid="voc-need-0-text"]').fill("Parts must arrive intact");
    await page.locator('[data-testid="voc-need-0-statement-S1"]').check();
    await page.locator('[data-testid="voc-ctq-0-need"]').selectOption("N1");
    await page.locator('[data-testid="voc-ctq-0-measure"]').fill("crack rate at receiving");
    await page.locator('[data-testid="voc-ctq-0-target"]').fill("<1%");
    await page
      .locator('[data-testid="voc-ctq-0-critical-check"]')
      .fill("Customer-critical: cracked parts are returned and re-ordered; not chosen for ease of measurement.");
    await page.locator('[data-testid="voc-primary-ctq"]').selectOption("C1");
    await page.locator('[data-testid="voc-charter-link"]').fill("matches charter primary metric: line-2 scrap rate");
    await page.locator('[data-testid="voc-ctq-save"]').click();
    await page.locator('[data-testid="voc-ctq-version-badge"]').waitFor();
    const pill = page.locator('[data-testid="prescore-check-tree_completeness"]');
    await pill.waitFor();
    assert((await pill.getAttribute("data-status")) === "pass", "expected the VoC/CTQ tree to read complete (pass)");
  });

  // -- File upload: base64-in-JSON, but the File/FileReader half is browser
  // work and the POST is a large cross-origin body. Classic packaged
  // failure point. ---------------------------------------------------------

  await step("T-11: CSV upload -> preview -> quality scan -> save, all cross-origin", async () => {
    await page.locator('[data-testid="nav-tool-T-11"]').click();
    await page.locator('[data-testid="dataimport-file-input"]').setInputFiles(FIXTURE_CSV_PATH);
    await page.locator('[data-testid="dataimport-column-preview"]').waitFor();
    await page.locator('[data-testid="dataimport-quality-scan"]').waitFor();
    const scanText = await page.locator('[data-testid="dataimport-quality-scan"]').textContent();
    assert(scanText?.includes("24 total rows scanned"), `expected the quality scan to report 24 rows, got ${JSON.stringify(scanText)}`);
    await page.locator('[data-testid="dataimport-save"]').click();
    await page.locator('[data-testid="dataimport-save-confirmation"]').waitFor();
    const confirmText = await page.locator('[data-testid="dataimport-save-confirmation"]').textContent();
    assert(confirmText?.includes("24 rows"), `expected the save confirmation to mention 24 rows, got ${JSON.stringify(confirmText)}`);
  });

  // -- Stats + charts ------------------------------------------------------

  await step("T-13 Baseline: run against the imported dataset and read the engine's verdicts", async () => {
    await page.locator('[data-testid="nav-tool-T-13"]').click();
    await page.locator('[data-testid="baseline-dataset-select"]').waitFor();
    await page.locator('[data-testid="baseline-dataset-select"]').selectOption({ label: FIXTURE_LABEL });
    await page.locator('[data-testid="baseline-column-select"]').selectOption("wait_seconds");
    await page.locator('[data-testid="baseline-usl-input"]').fill("105");
    await page.locator('[data-testid="baseline-lsl-input"]').fill("85");
    await page.locator('[data-testid="baseline-op-def-checkbox"]').check();
    await page.locator('[data-testid="baseline-run"]').click();
    await page.locator('[data-testid="baseline-stability-verdict"]').waitFor();
    const stabilityHeadline = await page.locator('[data-testid="baseline-stability-verdict"] .sigma-verdict__headline').textContent();
    assert(
      stabilityHeadline?.includes("stable: 24 points"),
      `expected the I-MR verdict headline to carry the stable-24-points note, got ${JSON.stringify(stabilityHeadline)}`,
    );
    await page.locator('[data-testid="baseline-sigma-level"]').waitFor();
    const sigmaHeadline = await page.locator('[data-testid="baseline-sigma-level"] .sigma-verdict__headline').textContent();
    assert(sigmaHeadline?.includes("with 1.5σ shift"), `expected the sigma-shift convention label, got ${JSON.stringify(sigmaHeadline)}`);
  });

  await step("Plotly actually renders in the production bundle (I-MR chart draws real marks)", async () => {
    // A minified production Plotly that fails to initialize is invisible to
    // the dev smoke, which never loads the production bundle at all.
    const plot = page.locator(".js-plotly-plot").first();
    await plot.waitFor();
    const drawn = await plot.evaluate((el) => {
      const paths = [...el.querySelectorAll("svg.main-svg path")].filter((p) => (p.getAttribute("d") || "").length > 3);
      return {
        traces: el.data?.length ?? 0,
        svgs: el.querySelectorAll("svg.main-svg").length,
        drawnPaths: paths.length,
        traceGroups: el.querySelectorAll("g.trace").length,
        classes: [...new Set([...el.querySelectorAll("svg.main-svg g")].map((g) => g.getAttribute("class")).filter(Boolean))].slice(0, 25),
      };
    });
    assert(drawn.traces > 0, "the I-MR Plotly div holds no traces -- Plotly.react never ran");
    assert(drawn.svgs > 0, "the I-MR chart drew no SVG -- Plotly failed to initialize in the production bundle");
    assert(
      drawn.traceGroups > 0 && drawn.drawnPaths > 0,
      `the I-MR chart drew no marks (${JSON.stringify(drawn)})`,
    );
  });

  await step("T-14 Pareto: chart renders and the engine's vital-few headline appears", async () => {
    await page.locator('[data-testid="nav-tool-T-14"]').click();
    await page.locator('[data-testid="chartset-dataset-select"]').waitFor();
    await page.locator('[data-testid="chartset-dataset-select"]').selectOption({ label: FIXTURE_LABEL });
    await page.locator('[data-testid="chartset-pareto-column"]').waitFor();
    await page.locator('[data-testid="chartset-pareto-column"]').selectOption("delay_cause");
    const paretoHeadline = page.locator('[data-testid="chartset-pareto"] .sigma-verdict__headline');
    await paretoHeadline.waitFor();
    // The panel renders the previously-selected column's verdict until the
    // new /stats/pareto round trip lands, so poll for the new headline
    // rather than reading whatever is on screen the instant after the
    // select changes.
    await page
      .waitForFunction(
        () =>
          document
            .querySelector('[data-testid="chartset-pareto"] .sigma-verdict__headline')
            ?.textContent?.includes("register") ?? false,
        undefined,
        { timeout: TIMEOUT_MS },
      )
      .catch(() => {});
    const text = await paretoHeadline.textContent();
    assert(
      text?.toLowerCase().includes("vital few") && text?.includes("register"),
      `expected the Pareto headline to name the vital few including "register", got ${JSON.stringify(text)}`,
    );
    const plot = page.locator('[data-testid="chartset-pareto"] .js-plotly-plot').first();
    await plot.waitFor();
    const bars = await plot.evaluate((el) => el.querySelectorAll(".barlayer .point path, .barlayer .trace path").length);
    assert(bars > 0, "the Pareto Plotly chart rendered no bars");
  });

  // -- Canvas tools (Konva) ------------------------------------------------

  await step("T-06 Process Map: build 2 lanes + 4 steps on the Konva canvas and save", async () => {
    await page.locator('[data-testid="nav-tool-T-06"]').click();
    await page.locator('[data-testid="processmap-save"]').waitFor();
    await page.locator('[data-testid="processmap-add-lane"]').click();
    await page.locator('[data-testid="processmap-add-lane"]').click();
    await page.locator('[data-testid="processmap-lane-0-name"]').fill("Customer");
    await page.locator('[data-testid="processmap-lane-0-owner"]').fill("Front counter lead");
    await page.locator('[data-testid="processmap-lane-1-name"]').fill("Barista");
    await page.locator('[data-testid="processmap-lane-1-owner"]').fill("Shift lead");

    await page.locator('[data-testid="processmap-add-step-0"]').click();
    await page.locator('[data-testid="processmap-step-name"]').fill("Place order");
    await page.locator('[data-testid="processmap-step-reason"]').fill("Customer directly asks for what they want.");
    await page.locator('[data-testid="processmap-step-time"]').fill("2");
    await page.locator('[data-testid="processmap-add-step-1"]').click();
    await page.locator('[data-testid="processmap-step-name"]').fill("Wait for register");
    await page.locator('[data-testid="processmap-step-type"]').selectOption("non_value_add");
    await page.locator('[data-testid="processmap-step-reason"]').fill("Customer gets nothing while waiting.");
    await page.locator('[data-testid="processmap-step-time"]').fill("9");
    await page.locator('[data-testid="processmap-add-step-0"]').click();
    await page.locator('[data-testid="processmap-step-name"]').fill("Make drink");
    await page.locator('[data-testid="processmap-step-reason"]').fill("Directly produces what the customer is paying for.");
    await page.locator('[data-testid="processmap-step-time"]').fill("3");
    await page.locator('[data-testid="processmap-add-step-1"]').click();
    await page.locator('[data-testid="processmap-step-name"]').fill("Hand off");
    await page.locator('[data-testid="processmap-step-type"]').selectOption("enabling");
    await page.locator('[data-testid="processmap-step-time"]').fill("1");

    const rows = page.locator('[data-testid^="processmap-step-row-"]');
    await rows.first().waitFor();
    assert((await rows.count()) === 4, `expected 4 step rows to render, got ${await rows.count()}`);
    // The Konva stage must have actually painted -- a blank canvas in the
    // production bundle would be invisible to any DOM-only assertion.
    const canvas = page.locator('[data-testid="processmap-canvas"] canvas').first();
    await canvas.waitFor();
    const painted = await canvas.evaluate((el) => {
      const ctx = el.getContext("2d");
      const { data } = ctx.getImageData(0, 0, el.width, el.height);
      for (let i = 3; i < data.length; i += 4) if (data[i] !== 0) return true;
      return false;
    });
    assert(painted, "the Konva process-map canvas is entirely transparent -- nothing was drawn");

    await page.locator('[data-testid="processmap-demand-time"]').fill("240");
    await page.locator('[data-testid="processmap-demand-units"]').fill("48");
    await page.locator('[data-testid="processmap-save"]').click();
    await page.locator('[data-testid="processmap-version-badge"]').waitFor();
    // The version badge lands when the save POST resolves; the banner only
    // fills in after the separate reload-after-save GET, so poll for the
    // engine-computed text rather than reading the pre-save placeholder.
    await page
      .waitForFunction(
        () =>
          document
            .querySelector('[data-testid="processmap-constraint-banner"] .sigma-verdict__headline')
            ?.textContent?.includes("Make drink") ?? false,
        undefined,
        { timeout: TIMEOUT_MS },
      )
      .catch(() => {});
    const headline = await page.locator('[data-testid="processmap-constraint-banner"] .sigma-verdict__headline').textContent();
    assert(
      headline?.includes("Make drink") && headline?.includes("5.00"),
      `expected the constraint banner to name "Make drink" against a 5.00 pace, got ${JSON.stringify(headline)}`,
    );
  });

  await step("T-07 Spaghetti: upload a PNG floor plan cross-origin and calibrate on the canvas", async () => {
    await page.locator('[data-testid="nav-tool-T-07"]').click();
    await page.locator('[data-testid="spaghetti-save"]').waitFor();
    await page.locator('[data-testid="spaghetti-floorplan-input"]').setInputFiles(FIXTURE_PNG_PATH);
    await page.locator('[data-testid="spaghetti-floorplan-loaded"]').waitFor();
    const canvas = page.locator('[data-testid="spaghetti-canvas"] canvas').first();
    await page.locator('[data-testid="spaghetti-mode-calibrate"]').click();
    await canvas.click({ position: { x: 50, y: 50 } });
    await canvas.click({ position: { x: 150, y: 50 } });
    await page.locator('[data-testid="spaghetti-calibration-length"]').fill("10");
    await page.locator('[data-testid="spaghetti-calibration-unit"]').selectOption("meters");
    await page.locator('[data-testid="spaghetti-calibration-confirm"]').click();
    const badge = await page.locator('[data-testid="spaghetti-calibration-badge"]').textContent();
    assert(badge?.includes("10") && badge?.includes("meters"), `expected the calibration badge to show 10 meters, got ${JSON.stringify(badge)}`);
  });

  // -- A deliberate refusal, cross-origin. A 4xx must still carry CORS
  // headers or the browser eats the body and the app shows a generic
  // "couldn't reach the engine" instead of the named refusal. --------------

  await step("T-21: a deliberate EXIT-11 refusal still renders its body cross-origin", async () => {
    armRefusal({ method: "POST", url: "/artifacts/T-21", status: 422 }, "EXIT-11 attribute-data refusal");

    await page.locator('[data-testid="nav-tool-T-21"]').click();
    await page.locator('[data-testid="controlchart-freeze"]').waitFor();
    await page.locator('[data-testid="controlchart-metric-ref"]').fill("order-to-handoff wait seconds");
    await page.locator('[data-testid="controlchart-data-shape"]').selectOption("attribute");
    await page.locator('[data-testid="controlchart-defectives-or-defects"]').selectOption("defects");
    await page.locator('[data-testid="controlchart-freeze"]').click();
    const banner = page.locator('[data-testid="controlchart-exit11-banner"]');
    await banner.waitFor();
    const bannerText = await banner.textContent();
    assert(bannerText?.includes("EXIT-11"), `expected the EXIT-11 refusal to render, got ${JSON.stringify(bannerText)}`);
    assert(
      !bannerText?.toLowerCase().includes("could not reach the engine"),
      "the refusal came back as a transport failure -- the 4xx response was blocked by CORS",
    );
  });

  // -- Advisor (Layer 2, unconfigured) -------------------------------------

  await step("advisor panel renders the honest unconfigured state (409 handled, not thrown)", async () => {
    // On T-03, which has a saved v1 artifact -- the export step below needs
    // one, and T-21's freeze was refused on purpose above.
    await page.locator('[data-testid="nav-tool-T-03"]').click();
    await page.locator('[data-testid="charter-version-badge"]').waitFor();
    await page.locator('[data-testid="advisor-panel-toggle"]').click();
    const unconfigured = page.locator('[data-testid="advisor-unconfigured"]');
    await unconfigured.waitFor();
    const text = await unconfigured.textContent();
    assert(
      text?.includes("Layer 1") && text?.includes("sends nothing anywhere"),
      `expected the honest unconfigured explanation, got ${JSON.stringify(text)}`,
    );
    assert((await page.locator('[data-testid="advisor-configured"]').count()) === 0, "must not show the configured ask box with no key");
    const options = await page.locator('[data-testid="advisor-mode-select"] option').allTextContents();
    assert(options.length === 6, `expected 6 advisor modes, got ${options.length}`);
  });

  await step("advisor export for chatbot works with no key (cross-origin GET /advisor/export)", async () => {
    await page.locator('[data-testid="advisor-export-tool-button"]').click();
    const preview = page.locator('[data-testid="advisor-export-preview"]');
    await preview.waitFor();
    const text = await preview.inputValue();
    assert(text.length > 0, "expected a non-empty combined export block");
    assert(text.includes("MY ARTIFACT:"), "expected the MY ARTIFACT: heading in the combined block");
  });

  // -- Diagnostics ---------------------------------------------------------

  await step("diagnostics screen reports the sidecar target and passes the NIST smoke check", async () => {
    await page.locator('[data-testid="topbar-diagnostics"]').click();
    const subtitle = page.locator(".sigma-diag__subtitle");
    await subtitle.waitFor();
    const subtitleText = await subtitle.textContent();
    assert(
      subtitleText?.includes("Tauri sidecar (127.0.0.1:8756)"),
      `diagnostics must report the packaged sidecar target under packaged conditions, got ${JSON.stringify(subtitleText)}`,
    );
    const online = page.locator(".sigma-diag__panel", { hasText: "Online — engine_version" });
    await online.waitFor();
    const nist = page.locator(".sigma-verdict__headline", { hasText: "NIST smoke check PASSED" });
    await nist.waitFor();
    await page.locator('[data-testid="diagnostics-back"]').click();
  });

  // -- Reload: the packaged app reopens an existing project from disk ------

  await step("full reload under packaged conditions comes back clean", async () => {
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator('[data-testid="engine-gate"]').waitFor({ state: "attached", timeout: 5000 }).catch(() => {});
    await page.locator('[data-testid="create-project-name"]').waitFor();
  });

  // -- Route-level CORS coverage. The flow above exercises the endpoints a
  // user walks through; this enumerates EVERY route from the engine's own
  // OpenAPI schema and proves each one is readable cross-origin. It is the
  // regression guard for "a new route ships without CORS": nobody has to
  // remember to add it to this file. ------------------------------------

  await step("every route in the engine's OpenAPI schema is readable cross-origin", async () => {
    corsProbeMode = true;
    const result = await page.evaluate(async (origin) => {
      const schema = await (await fetch(`${origin}/openapi.json`)).json();
      const blocked = [];
      const checked = [];
      for (const [rawPath, ops] of Object.entries(schema.paths)) {
        for (const method of Object.keys(ops)) {
          const m = method.toUpperCase();
          if (!["GET", "POST", "PUT", "DELETE", "PATCH"].includes(m)) continue;
          // A path that cannot exist, so nothing is created or mutated --
          // we only care whether the browser lets us READ the response.
          const url =
            origin +
            rawPath.replace(/\{[^}]+\}/g, "packaged-sweep-cors-probe-nonexistent");
          try {
            const res = await fetch(url, {
              method: m,
              // Forces a real preflight on every route, including GETs.
              headers: { "content-type": "application/json" },
              body: m === "GET" ? undefined : "{}",
            });
            // Reading the body proves the response was not opaque.
            await res.text();
            checked.push(`${m} ${rawPath} -> ${res.status}`);
          } catch (err) {
            blocked.push(`${m} ${rawPath} -- ${String(err)}`);
          }
        }
      }
      return { blocked, checked };
    }, ENGINE_ORIGIN);
    corsProbeMode = false;
    console.log(`    probed ${result.checked.length} route/method pairs cross-origin`);
    assert(result.checked.length >= 25, `expected the schema to yield a substantial route list, got ${result.checked.length}`);
    assert(
      result.blocked.length === 0,
      `these routes are NOT reachable cross-origin (they work through the dev proxy, they will fail in the packaged app):\n  ${result.blocked.join("\n  ")}`,
    );
  });

  await step("error responses are readable cross-origin, not blocked by the browser", async () => {
    // JS can never read Access-Control-Allow-Origin itself (it isn't an
    // exposed header), so the only browser-side proof is that fetch()
    // RESOLVES: a response with no CORS header makes fetch reject before
    // the app sees anything, which client.ts turns into "Could not reach
    // the engine" -- a server error disguised as the engine being down.
    // The 500 half of this contract is pinned in
    // engine/tests/test_cors_packaged.py, which can raise a genuine
    // unhandled exception without shipping a crash route in production.
    corsProbeMode = true;
    const out = await page.evaluate(async (origin) => {
      const results = {};
      for (const [name, url, init] of [
        ["notFound", `${origin}/no-such-route`, { method: "GET", headers: { "content-type": "application/json" } }],
        [
          "validationRefusal",
          `${origin}/artifacts/T-03/validate`,
          { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ nonsense: true }) },
        ],
      ]) {
        try {
          const res = await fetch(url, init);
          results[name] = { status: res.status, body: (await res.text()).slice(0, 80) };
        } catch (err) {
          results[name] = { blocked: String(err) };
        }
      }
      return results;
    }, ENGINE_ORIGIN);
    corsProbeMode = false;
    assert(out.notFound.blocked === undefined, `a 404 was blocked cross-origin: ${out.notFound.blocked}`);
    assert(out.notFound.status === 404, `expected 404, got ${out.notFound.status}`);
    assert(
      out.validationRefusal.blocked === undefined,
      `a 422 refusal body was blocked cross-origin -- the UI would show a transport failure instead of the refusal: ${out.validationRefusal.blocked}`,
    );
    assert(out.validationRefusal.status === 422, `expected a 422 refusal, got ${out.validationRefusal.status}`);
    assert(
      out.validationRefusal.body.includes("detail"),
      `the refusal body was empty cross-origin: ${JSON.stringify(out.validationRefusal.body)}`,
    );
  });

  // -- Final packaging assertions -----------------------------------------

  await step("no engine call ever went anywhere but the absolute sidecar origin", async () => {
    const seen = [...engineRequestUrls];
    assert(seen.length > 30, `expected a substantial cross-origin call volume, only saw ${seen.length}`);
    const offOrigin = await page.evaluate(
      (origin) =>
        performance
          .getEntriesByType("resource")
          .map((e) => e.name)
          .filter((n) => /\/(project|artifacts|prescore|gates|stats|advisor|health|smoke)\b/.test(n) && !n.startsWith(origin)),
      ENGINE_ORIGIN,
    );
    assert(offOrigin.length === 0, `engine-shaped requests went off the sidecar origin: ${JSON.stringify(offOrigin)}`);
  });

  await step("every armed deliberate refusal actually fired (the allow-list isn't hiding a real failure)", async () => {
    console.log(
      "    armed refusals: " +
        armedRefusals.map((r) => `${r.method} ${r.url} ${r.status} x${r.seen}`).join(", "),
    );
    // An allow-list entry that never fires is an exemption with nothing
    // behind it -- exactly how a real 4xx regression would get waved
    // through later. Fail so it has to be deleted or made to fire.
    const unused = armedRefusals.filter((r) => r.seen === 0);
    assert(
      unused.length === 0,
      `these refusal exemptions never fired and must be removed: ${unused.map((r) => `${r.method} ${r.url} ${r.status}`).join(", ")}`,
    );
  });
}

async function finish(browser, site, ok, err) {
  await browser.close();
  site.close();

  const failedSteps = steps.filter((s) => s.status === "FAIL");
  const overallOk =
    ok &&
    failedSteps.length === 0 &&
    pageErrors.length === 0 &&
    consoleErrors.length === 0 &&
    failedRequests.length === 0 &&
    badResponses.length === 0;

  console.log("\n========== PACKAGED SWEEP SUMMARY ==========");
  console.log(`App origin:    ${APP_ORIGIN} (production build)`);
  console.log(`Engine origin: ${ENGINE_ORIGIN} (cross-origin, absolute URL)`);
  console.log(`Steps: ${steps.length} run, ${steps.filter((s) => s.status === "PASS").length} passed, ${failedSteps.length} failed`);
  console.log(`Distinct engine calls observed: ${engineRequestUrls.size}`);
  console.log(`Page errors: ${pageErrors.length}`);
  console.log(`Console errors: ${consoleErrors.length}`);
  console.log(`Failed requests: ${failedRequests.length}`);
  console.log(`Unexpected >=400 responses: ${badResponses.length}`);
  if (err) console.log(`Thrown error: ${err instanceof Error ? err.message : String(err)}`);
  for (const e of pageErrors) console.log(`  [page error] ${e}`);
  for (const e of consoleErrors) console.log(`  [console error] ${e}`);
  for (const e of failedRequests) console.log(`  [request failed] ${e}`);
  for (const e of badResponses) console.log(`  [bad response] ${e}`);
  console.log(overallOk ? "RESULT: PASS" : "RESULT: FAIL");
  console.log("============================================");

  process.exit(overallOk ? 0 : 1);
}

main().catch((err) => {
  console.error("Unhandled error in packaged sweep:", err);
  process.exit(1);
});
