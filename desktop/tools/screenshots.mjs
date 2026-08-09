#!/usr/bin/env node
// Screenshot capture for docs/demo-walkthrough.md (M6 ship docs). Assumes
// the engine (uvicorn, port 8000) and `npm run dev` (Vite, port 1420) are
// already running -- this script only seeds a scratch project over the
// engine API and drives Chromium against the app, same conventions as
// smoke-browser.mjs (chromium at /opt/pw-browsers, data-testid selectors,
// step logging, fail on any uncaught page error).
//
// What it does: builds a fresh project from the shipped Coffee Bar demo's
// own artifact JSONs (demo/coffee-bar/**/*.json, read-only -- exactly the
// files the eval harness replays, re-keyed to the UI's fixed artifact ids),
// then walks the workspace stop by stop and captures the twelve
// walkthrough screenshots to docs/screenshots/*.png at a consistent
// 1280x800 viewport. Where a stop's honest-number moment needs a real UI
// action (the flawed charter's prescore flags, the T-13 baseline run, the
// T-17 hypothesis run, the T-19 EXIT-10 refusal), the action is driven
// live against the engine -- nothing pasted in, nothing mocked.
//
// Usage: node tools/screenshots.mjs
// Env:   APP_URL          (default http://localhost:1420)
//        SIGMA_ENGINE_URL (default http://127.0.0.1:8000)
//        PW_CHROMIUM_PATH (default /opt/pw-browsers/chromium)
//        SIGMA_PROJECTS_ROOT (default ~/.sigma-ai/projects -- must match
//                             the running engine's own projects root, so
//                             the stale walkthrough project can be reset)

import { chromium } from "playwright";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const APP_URL = process.env.APP_URL || "http://localhost:1420";
const ENGINE_URL = process.env.SIGMA_ENGINE_URL || "http://127.0.0.1:8000";
const CHROMIUM_PATH = process.env.PW_CHROMIUM_PATH || "/opt/pw-browsers/chromium";
const TIMEOUT_MS = 30_000;

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(SCRIPT_DIR, "..", "..");
const DEMO_ROOT = path.join(REPO_ROOT, "demo", "coffee-bar");
const SHOT_DIR = path.join(REPO_ROOT, "docs", "screenshots");
const PROJECTS_ROOT = process.env.SIGMA_PROJECTS_ROOT || path.join(os.homedir(), ".sigma-ai", "projects");

const PROJECT_ID = "coffee-bar-walkthrough";
const PROJECT_NAME = "Coffee Bar (walkthrough)";

// ---------------------------------------------------------------- logging

const pageErrors = [];
const consoleErrors = [];

function log(status, name, detail) {
  console.log(`[${status}] ${name}${detail ? " -- " + detail : ""}`);
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

// ------------------------------------------------------------ engine API

async function api(method, route, body) {
  const res = await fetch(`${ENGINE_URL}${route}`, {
    method,
    headers: { "content-type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${method} ${route} -> ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json();
}

function loadDemo(rel) {
  return JSON.parse(fs.readFileSync(path.join(DEMO_ROOT, rel), "utf-8"));
}

// The UI's tool screens each load/save one fixed artifact id (e.g.
// CharterForm's ARTIFACT_ID = "charter"), while the shipped demo files use
// "coffee-*" ids. Re-key every exact-match occurrence (id fields and
// cross-refs like proof.pilot_ref) so the workspace finds the artifacts;
// prose mentions inside notes are left untouched (exact match only).
const ID_MAP = {
  "coffee-picker": "picker",
  "coffee-copq": "copq",
  "coffee-copq-wrap": "copq",
  "coffee-charter": "charter",
  "coffee-sipoc": "sipoc",
  "coffee-voc-ctq": "voc-ctq",
  "coffee-process-map": "process-map",
  "coffee-spaghetti": "spaghetti",
  "coffee-check-sheet": "checksheet",
  "coffee-time-study": "timestudy",
  "coffee-collection-plan": "collection-plan",
  "coffee-msa": "msa",
  "coffee-fishbone": "fishbone",
  "coffee-fmea": "fmea",
  "coffee-hypothesis-daypart": "hypothesis",
  "coffee-solution-matrix": "solution-matrix",
  "coffee-pilot-round1": "pilot-plan",
  "coffee-pilot-round2": "pilot-plan",
  "coffee-proof-round1": "proof",
  "coffee-proof-round2": "proof",
  "coffee-control-chart": "control-chart",
  "coffee-control-plan": "control-plan",
  "coffee-five-s": "five-s",
  "coffee-standard-work": "sop",
  "coffee-a3": "a3",
};

function rekey(value) {
  if (typeof value === "string") return ID_MAP[value] ?? value;
  if (Array.isArray(value)) return value.map(rekey);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, rekey(v)]));
  }
  return value;
}

// Mirror of evals/harness/scenarios/common.py's TOP_LEVEL_COMPUTED_FIELDS:
// engine-computed fields are dropped before save so the live engine
// recomputes them fresh (they are recomputed on every validate anyway;
// submitting a stale shape risks tripping schema growth).
const COMPUTED_FIELDS = {
  "T-02": ["total"],
  "T-06": ["longest_step", "constraint_step"],
  "T-07": ["metrics"],
  "T-09": ["element_stats", "work_sampling_summary"],
  "T-12": ["result"],
  "T-15": ["verified_causes"],
  "T-16": ["blocking_flags", "sorted_view"],
  "T-17": ["routing", "result", "refused"],
  "T-18": ["scores", "ranked_fix_list"],
  "T-19": ["package_attribution_note"],
  "T-20": ["before_baseline", "after_baseline", "test_result", "guardrail_report", "gap", "verdict"],
};

async function saveArtifact(toolId, rel, transform) {
  let body = rekey(loadDemo(rel));
  for (const key of COMPUTED_FIELDS[toolId] ?? []) delete body[key];
  if (transform) body = transform(body);
  return api("POST", `/project/${PROJECT_ID}/artifacts/${toolId}`, body);
}

// Mirror of common.py's prepare_control_chart: clear the frozen/derived
// fields and ask the engine to (re)compute the freeze from imr_values.
function prepareControlChart(body) {
  for (const key of [
    "imr_baseline", "p_baseline", "signals", "frozen_at", "source_dataset_hash",
    "frozen_window_values", "frozen_window_subgroups",
  ]) body[key] = null;
  body.recalculation_log = [];
  body.acknowledgments = {};
  body.freeze_requested = true;
  body.recalculate_reason = null;
  body.action_at = "2026-09-22T09:00:00Z";
  return body;
}

// Mirror of common.py's prepare_control_plan.
function prepareControlPlan(body) {
  body.plan_health = null;
  if (body.check_in_schedule) {
    body.check_in_schedule.next_due = null;
    body.check_in_schedule.completed = (body.check_in_schedule.completed ?? []).map((c) => ({ ...c, result: null }));
  }
  return body;
}

async function uploadFile(route, absPath, createdAt) {
  const content = fs.readFileSync(absPath);
  return api("POST", route, {
    source_filename: path.basename(absPath),
    content_base64: content.toString("base64"),
    created_at: createdAt,
  });
}

// SEEDING (part 1 of 2): everything the first nine stops need -- Define
// through Improve round 1, in the demo's own DMAIC order. The flawed
// charter draft is seeded as v1 on purpose: stop 2 re-saves it through the
// real UI so the engine's solution-language prescore flags render live.
async function seedPhaseOne() {
  fs.rmSync(path.join(PROJECTS_ROOT, PROJECT_ID), { recursive: true, force: true });
  await api("POST", "/project/create", { project_id: PROJECT_ID, name: PROJECT_NAME, created_at: "2026-07-02T14:00:00Z" });

  await saveArtifact("T-01", "define/picker.json");
  await saveArtifact("T-02", "define/copq.json");
  await saveArtifact("T-03", "define/charter-flawed.json"); // v1: the flawed draft (stop 2)
  await saveArtifact("T-04", "define/sipoc.json");
  await saveArtifact("T-05", "define/voc-ctq.json");

  const ds = await uploadFile(`/project/${PROJECT_ID}/datasets`, path.join(DEMO_ROOT, "measure/wait-times.csv"), "2026-07-31T17:00:00Z");

  await saveArtifact("T-06", "measure/process-map.json");
  const plan = await uploadFile(`/project/${PROJECT_ID}/floorplans`, path.join(DEMO_ROOT, "measure/floorplan.png"), "2026-07-21T14:15:00Z");
  await saveArtifact("T-07", "measure/spaghetti.json", (b) => ({
    ...b,
    floor_plan: {
      image_id: plan.image_id, source_filename: plan.source_filename,
      sha256: plan.sha256, width_px: plan.width_px, height_px: plan.height_px,
    },
  }));
  await saveArtifact("T-08", "measure/check-sheet.json");
  await saveArtifact("T-09", "measure/time-study.json");
  await saveArtifact("T-11", "measure/collection-plan.json");
  await saveArtifact("T-12", "measure/msa-study.json");

  // The demo fishbone ships with layout {} (card positions are a canvas
  // drag concern the engine never computes), which renders every card at
  // the origin. Seed the positions a user's drags would have stored --
  // spread along each 6M branch, why-chain cards stepped outward.
  await saveArtifact("T-15", "analyze/fishbone.json", (b) => ({
    ...b,
    layout: {
      "c-staffing": { x: 150, y: 155 },
      "c-queue": { x: 150, y: 385 },
      "c-grinder": { x: 280, y: 165 },
      "c-register-hw": { x: 285, y: 60 },
      "c-station-serial": { x: 430, y: 165 },
      "c-one-head": { x: 505, y: 110 },
      "c-batch-locked": { x: 580, y: 55 },
      "c-grind-drift": { x: 500, y: 390 },
      "c-ticket-skew": { x: 735, y: 150 },
      "c-music": { x: 690, y: 385 },
      "c-cup-placement": { x: 845, y: 440 },
    },
  }));
  await saveArtifact("T-16", "analyze/fmea.json");
  await saveArtifact("T-17", "analyze/hypothesis-run.json");
  await saveArtifact("T-18", "improve/solution-matrix.json");
  // The pilot screen treats change_id "the-one-change" as the primary
  // statement's own row (pilotPlanLogic.ts PRIMARY_CHANGE_ID) and renders
  // any OTHER id as an extra-change row -- re-key the demo's single change
  // so the loaded plan reads as what it is: one change, no extras.
  await saveArtifact("T-19", "improve/pilot-plan-round1.json", (b) => ({
    ...b,
    changes: b.changes.length === 1 ? [{ ...b.changes[0], change_id: "the-one-change" }] : b.changes,
  }));
  await saveArtifact("T-20", "improve/proof-round1.json");

  return ds;
}

// SEEDING (part 2 of 2): run after the round-1 stops are captured --
// Improve round 2 (the declared package) and the full Control/Wrap close,
// so the last two stops show the project as the demo ships it: frozen
// chart, owned control plan, 5S rounds, SOP, wrap COPQ re-run, closed A3.
async function seedPhaseTwo() {
  await saveArtifact("T-19", "improve/pilot-plan-round2.json"); // v2
  await saveArtifact("T-20", "improve/proof-round2.json"); // v2
  await saveArtifact("T-21", "control/control-chart.json", prepareControlChart);
  await saveArtifact("T-22", "control/control-plan.json", prepareControlPlan);

  const fiveS = rekey(loadDemo("control/five-s.json"));
  for (let i = 0; i < fiveS.rounds.length; i++) {
    const png = path.join(DEMO_ROOT, `control/five-s-round${i + 1}.png`);
    const meta = await uploadFile(`/project/${PROJECT_ID}/floorplans`, png, `${fiveS.rounds[i].date}T09:00:00Z`);
    fiveS.rounds[i].photos = [{
      image_id: meta.image_id, source_filename: meta.source_filename,
      sha256: meta.sha256, width_px: meta.width_px, height_px: meta.height_px,
    }];
  }
  await api("POST", `/project/${PROJECT_ID}/artifacts/T-23`, fiveS);

  await saveArtifact("T-24", "control/standard-work.json");
  await saveArtifact("T-02", "control/copq-wrap.json"); // v2: the wrap re-run
  await saveArtifact("T-25", "control/a3.json");
}

// ----------------------------------------------------- stops 1-9 (round 1)

async function capturePhaseOne(page, shoot, openTool) {
  await step("open the walkthrough project", async () => {
    await page.goto(`${APP_URL}/#/project/${PROJECT_ID}`, { waitUntil: "domcontentloaded" });
    await page.locator('[data-testid="topbar-project-name"]').waitFor();
    const shown = await page.locator('[data-testid="topbar-project-name"]').textContent();
    assert(shown?.trim() === PROJECT_NAME, `top bar shows ${JSON.stringify(shown)}`);
  });

  await step("stop 1: T-01 Project Picker (loaded five-criteria route)", async () => {
    await openTool("T-01", '[data-testid="picker-save"]');
    // The loaded demo picker answers all five criteria Yes with evidence
    // and routes to full DMAIC -- wait for the loaded state to land.
    await page.locator('[data-testid="picker-version-badge"]').waitFor();
    await shoot("01-picker.png");
  });

  await step("stop 2: T-03 flawed charter draft -- prescore flags render live", async () => {
    await openTool("T-03", '[data-testid="charter-save"]');
    await page.locator('[data-testid="charter-version-badge"]').waitFor(); // flawed v1 loaded
    // Re-save the loaded flawed draft through the real UI so the engine's
    // prescore runs and the solution-language flags render (strip + field).
    await page.locator('[data-testid="charter-save"]').click();
    const pill = page.locator('[data-testid="prescore-check-problem_statement_solution_language"]');
    await pill.waitFor();
    assert((await pill.getAttribute("data-status")) !== "pass", "expected the flawed draft to flag solution language");
    // Frame the flawed sentence itself with its field-level flag on screen.
    const whatField = page.locator('[data-testid="charter-problem-what"]').locator("..");
    await whatField.locator(".sigma-field__flag-message").waitFor();
    await page.locator('[data-testid="charter-problem-what"]').evaluate((el) => el.scrollIntoView({ block: "start" }));
    await shoot("02-charter-flawed.png");
  });

  await step("stop 3: T-03 corrected charter -- clean prescore", async () => {
    await saveArtifact("T-03", "define/charter.json"); // corrected, via API
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator('[data-testid="topbar-project-name"]').waitFor();
    await openTool("T-03", '[data-testid="charter-save"]');
    await page.locator('[data-testid="charter-version-badge"]').waitFor();
    await page.locator('[data-testid="charter-save"]').click();
    const pill = page.locator('[data-testid="prescore-check-problem_statement_solution_language"]');
    await pill.waitFor();
    assert((await pill.getAttribute("data-status")) === "pass", "expected the corrected charter to prescore clean");
    await shoot("03-charter-clean.png");
  });

  await step("stop 4: T-12 Measurement Check -- repeatability verdict", async () => {
    await openTool("T-12", '[data-testid="msa-run"]');
    await page.locator('[data-testid="msa-result-view"]').waitFor();
    const pct = await page.locator('[data-testid="msa-repeatability-percent"]').textContent();
    assert(pct && pct.includes("8.9"), `expected the demo's 8.94% repeatability, got ${JSON.stringify(pct)}`);
    await page.locator('[data-testid="msa-result-view"]').scrollIntoViewIfNeeded();
    await shoot("04-msa.png");
  });

  await step("stops 5-6: T-13 Baseline -- stability, then capability, live", async () => {
    await openTool("T-13", '[data-testid="baseline-dataset-select"]');
    await page.locator('[data-testid="baseline-dataset-select"]').selectOption({ label: "wait-times.csv (120 rows)" });
    await page.locator('[data-testid="baseline-column-select"]').selectOption("wait_minutes");
    await page.locator('[data-testid="baseline-usl-input"]').fill("5.0"); // the customer's 5-minute line; no LSL
    await page.locator('[data-testid="baseline-op-def-checkbox"]').check();
    await page.locator('[data-testid="baseline-run"]').click();
    await page.locator('[data-testid="baseline-stability-verdict"]').waitFor();
    const headline = await page.locator('[data-testid="baseline-stability-verdict"] .sigma-verdict__headline').textContent();
    assert(headline?.includes("stable"), `expected the stable-baseline verdict, got ${JSON.stringify(headline)}`);
    await page.locator('[data-testid="baseline-stability-verdict"]').scrollIntoViewIfNeeded();
    await shoot("05-baseline-stability.png");
    // Second frame: the capability half of "stable but not capable" --
    // align the sigma-level banner to the bottom so the Cp/Cpk panel and
    // normality advisory above it fill the viewport.
    await page.locator('[data-testid="baseline-sigma-level"]').waitFor();
    await page.locator('[data-testid="baseline-sigma-level"]').evaluate((el) => el.scrollIntoView({ block: "end" }));
    await shoot("06-baseline-capability.png");
  });

  await step("stop 7: T-15 Fishbone -- evidence discipline on the cause board", async () => {
    await openTool("T-15", '[data-testid="fishbone-save"]');
    await page.locator('[data-testid="fishbone-verified-summary"]').waitFor();
    // Select a still-candidate cause so the no-evidence chip is visible in
    // the inspector next to the verified summary.
    await page.locator('[data-testid^="fishbone-cause-row-"]', { hasText: "Up-tempo peak playlist" }).click();
    await page.locator('[data-testid="fishbone-inspector-unproven-chip"]').waitFor();
    // Frame the fishbone canvas itself (status-colored cause cards on the
    // 6M branches), with the panels row starting below it. The stage is
    // wider than the tool column, so zoom out with the canvas's own wheel
    // affordance (anchored top-left) until the whole fish fits.
    await page.locator('[data-testid="fishbone-canvas"]').evaluate((el) => el.scrollIntoView({ block: "start" }));
    const canvasBox = await page.locator('[data-testid="fishbone-canvas"] canvas').first().boundingBox();
    assert(canvasBox, "expected the fishbone canvas to have a bounding box");
    await page.mouse.move(canvasBox.x + 8, canvasBox.y + 8);
    for (let i = 0; i < 16; i++) await page.mouse.wheel(0, 120);
    await shoot("07-fishbone.png");
  });

  await step("stop 8: T-17 Hypothesis -- run the saved daypart question live", async () => {
    await openTool("T-17", '[data-testid="hyp-question-text"]');
    // The saved artifact restores the question + routing; the run itself
    // re-executes live so the result panel is the engine's, not a replay.
    await page.locator('[data-testid="hyp-run"]').click();
    await page.locator('[data-testid="hyp-plain-language-headline"]').waitFor();
    const headline = await page.locator('[data-testid="hyp-plain-language-headline"] .sigma-verdict__headline').textContent();
    assert(headline?.toLowerCase().includes("welch"), `expected a Welch headline, got ${JSON.stringify(headline)}`);
    await page.locator('[data-testid="hyp-plain-language-headline"]').evaluate((el) => el.scrollIntoView({ block: "start" }));
    await shoot("08-hypothesis.png");
  });

  await step("stop 9: T-19 Pilot Plan -- the EXIT-10 refusal, live", async () => {
    await openTool("T-19", '[data-testid="pilot-save"]');
    await page.locator('[data-testid="pilot-version-badge"]').waitFor(); // round-1 plan loaded
    await page.locator('[data-testid="pilot-add-another-change"]').click();
    await page.locator('[data-testid="pilot-extra-change-0"]').fill("Also add the backup grinder in the same window");
    await page.locator('[data-testid="pilot-save"]').click();
    const banner = page.locator('[data-testid="pilot-exit10-banner"]');
    await banner.waitFor();
    const text = await banner.textContent();
    assert(text?.includes("EXIT-10"), `expected the EXIT-10 refusal banner, got ${JSON.stringify(text)}`);
    await banner.scrollIntoViewIfNeeded();
    await shoot("09-pilot-exit10.png");
    // The refused save never wrote a version; reload so the top bar's
    // (accurate) "Save failed" state from this deliberate refusal doesn't
    // bleed into the next stop's frame.
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator('[data-testid="topbar-project-name"]').waitFor();
  });

  await step("stop 10: T-20 Proof -- round 1's remaining-gap arithmetic", async () => {
    await openTool("T-20", '[data-testid="proof-save"]');
    await page.locator('[data-testid="proof-gap-recovered"]').waitFor();
    const remaining = await page.locator('[data-testid="proof-gap-remaining"]').textContent();
    assert(remaining && remaining.trim().length > 0, "expected the gap panel's remaining figure to render");
    const nextCause = await page.locator('[data-testid="proof-next-cause-card"]').textContent();
    assert(nextCause?.toLowerCase().includes("grinder"), `expected the next-cause card to name the grinder cause, got ${JSON.stringify(nextCause)}`);
    await page.locator('[data-testid="proof-gap-recovered"]').scrollIntoViewIfNeeded();
    await shoot("10-proof-gap.png");
  });
}

// --------------------------------------------------- stops 10-11 (close)

async function capturePhaseTwo(page, shoot, openTool) {
  await step("stop 11: T-21 Control Chart -- frozen I-MR limits", async () => {
    await openTool("T-21", '[data-testid="controlchart-freeze"]');
    await page.locator('[data-testid="controlchart-freeze-banner"]').waitFor();
    await page.locator('[data-testid="controlchart-imr-chart"]').waitFor();
    await page.locator('[data-testid="controlchart-freeze-banner"]').evaluate((el) => el.scrollIntoView({ block: "start" }));
    await shoot("11-control-chart.png");
  });

  await step("stop 12: T-25 A3 -- the honest close", async () => {
    await openTool("T-25", '[data-testid="a3-save"]');
    await page.locator('[data-testid="a3-version-badge"]').waitFor();
    // The objectives-vs-charter panel mounts collapsed (its default-open
    // state was captured before the artifact finished loading) -- expand
    // it so the engine's goal-met verdict is on screen.
    await page.locator("button.sigma-panel__header--collapsible", { hasText: "Objectives vs. charter" }).click();
    await page.locator('[data-testid="a3-objectives-verdict"]').waitFor();
    await page.locator('[data-testid="a3-objectives-verdict"]').scrollIntoViewIfNeeded();
    await shoot("12-a3-close.png");
  });
}

// ---------------------------------------------------------- browser pass

async function main() {
  fs.mkdirSync(SHOT_DIR, { recursive: true });

  const health = await api("GET", "/health");
  assert(health.status === "ok", `engine /health not ok: ${JSON.stringify(health)}`);

  await step("seed phase 1 (Define -> Improve round 1, flawed charter as v1)", seedPhaseOne);

  const browser = await chromium.launch({ executablePath: CHROMIUM_PATH, args: ["--no-sandbox"] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.setDefaultTimeout(TIMEOUT_MS);
  page.on("pageerror", (err) => {
    pageErrors.push(err.message);
    console.error(`[PAGE ERROR] ${err.message}`);
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
      console.error(`[CONSOLE ERROR] ${msg.text()}`);
    }
  });

  async function shoot(name) {
    await page.waitForTimeout(400); // let charts/canvas settle
    await page.screenshot({ path: path.join(SHOT_DIR, name) });
    log("SHOT", name);
  }

  async function openTool(toolId, readySelector) {
    await page.locator(`[data-testid="nav-tool-${toolId}"]`).click();
    await page.locator(readySelector).waitFor();
  }

  try {
    // STOPS 1-9 are inserted here by the sections below.
    await capturePhaseOne(page, shoot, openTool);

    await step("seed phase 2 (Improve round 2 -> Control -> Wrap close)", seedPhaseTwo);
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.locator('[data-testid="topbar-project-name"]').waitFor();

    await capturePhaseTwo(page, shoot, openTool);
  } finally {
    await browser.close();
  }

  assert(pageErrors.length === 0, `uncaught page errors: ${pageErrors.join(" | ")}`);
  const shots = fs.readdirSync(SHOT_DIR).filter((f) => f.endsWith(".png"));
  console.log(`\nDone: ${shots.length} screenshots in ${SHOT_DIR}`);
  for (const f of shots.sort()) console.log(`  ${f}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
