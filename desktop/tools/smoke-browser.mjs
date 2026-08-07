#!/usr/bin/env node
// Real-browser smoke test for the M1 app shell (M1 brief verification
// step). Assumes the engine (uvicorn) and `npm run dev` (Vite, port 1420)
// are already running -- this script only drives Chromium against them.
//
// Flow: load the app -> create a project -> fill T-01 (Project Picker) to
// a full-DMAIC route -> save -> see the version badge -> open T-03
// (Charter) -> type a solution-shaped problem statement -> save -> assert
// the solution-language prescore flag renders, both in the prescore strip
// and as a field-level flag. Fails on any uncaught page error.
//
// Usage: node tools/smoke-browser.mjs
// Env:   APP_URL (default http://localhost:1420)

import { chromium } from "playwright";

const APP_URL = process.env.APP_URL || "http://localhost:1420";
const CHROMIUM_PATH = process.env.PW_CHROMIUM_PATH || "/opt/pw-browsers/chromium";
const TIMEOUT_MS = 20_000;

const steps = [];
const pageErrors = [];
const consoleErrors = [];

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

const CRITERIA_KEYS = [
  "scope_narrow",
  "measurable_outcome",
  "data_obtainable",
  "process_owner_engaged",
  "business_impact_plausible",
];

async function main() {
  const browser = await chromium.launch({
    executablePath: CHROMIUM_PATH,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
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

  const runId = Date.now();
  const projectName = `Smoke Test Coffee Bar ${runId}`;

  try {
    await step("load app", async () => {
      await page.goto(APP_URL, { waitUntil: "domcontentloaded" });
      await page.locator('[data-testid="create-project-name"]').waitFor();
    });

    await step("create project", async () => {
      await page.locator('[data-testid="create-project-name"]').fill(projectName);
      await page.locator('[data-testid="create-project-submit"]').click();
      await page.locator('[data-testid="topbar-project-name"]').waitFor();
      const shown = await page.locator('[data-testid="topbar-project-name"]').textContent();
      assert(shown?.trim() === projectName, `top bar shows ${JSON.stringify(shown)}, expected ${JSON.stringify(projectName)}`);
    });

    await step("open T-01 Project Picker", async () => {
      await page.locator('[data-testid="nav-tool-T-01"]').click();
      await page.locator('[data-testid="picker-save"]').waitFor();
    });

    await step("fill T-01 to a full-DMAIC route", async () => {
      for (const key of CRITERIA_KEYS) {
        await page.locator(`[data-testid="picker-${key}-yes"]`).click();
        await page.locator(`[data-testid="picker-${key}-detail"]`).fill(`Smoke-test evidence for ${key}.`);
      }
      await page.locator('[data-testid="picker-route-full-DMAIC"]').click();
      const saveBtn = page.locator('[data-testid="picker-save"]');
      assert(await saveBtn.isEnabled(), "Save button should be enabled once all criteria + route are set");
    });

    await step("save T-01 and see the version badge", async () => {
      await page.locator('[data-testid="picker-save"]').click();
      await page.locator('[data-testid="picker-version-badge"]').waitFor();
      const badge = await page.locator('[data-testid="picker-version-badge"]').textContent();
      assert(badge?.includes("v1"), `expected version badge to show v1, got ${JSON.stringify(badge)}`);
    });

    await step("open T-03 Project Charter", async () => {
      await page.locator('[data-testid="nav-tool-T-03"]').click();
      await page.locator('[data-testid="charter-save"]').waitFor();
    });

    await step("fill T-03 with a solution-shaped problem statement", async () => {
      // Solution-shaped on purpose (contains "train" -- prescore/charter.py's
      // SOLUTION_LANGUAGE_KEYWORDS) so the flag this test is checking for
      // actually has something to catch.
      await page.locator('[data-testid="charter-problem-what"]').fill("Train the operators on the new molding process");
      await page.locator('[data-testid="charter-problem-where"]').fill("Line 2, Plant A");
      await page.locator('[data-testid="charter-problem-when"]').fill("Q2 2026");
      await page.locator('[data-testid="charter-magnitude-number"]').fill("6.2");
      await page.locator('[data-testid="charter-magnitude-unit"]').fill("%");
      await page.locator('[data-testid="charter-magnitude-period"]').fill("Q2 2026");

      await page.locator('[data-testid="charter-goal-statement"]').fill("Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026.");
      await page.locator('[data-testid="charter-goal-metric-name"]').fill("line-2 scrap rate");
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

      assert(await page.locator('[data-testid="charter-save"]').isEnabled(), "Save button should be enabled once required fields are filled");
    });

    await step("save T-03 and see the version badge", async () => {
      await page.locator('[data-testid="charter-save"]').click();
      await page.locator('[data-testid="charter-version-badge"]').waitFor();
      const badge = await page.locator('[data-testid="charter-version-badge"]').textContent();
      assert(badge?.includes("v1"), `expected version badge to show v1, got ${JSON.stringify(badge)}`);
    });

    await step("assert the solution-language flag renders in the prescore strip", async () => {
      const pill = page.locator('[data-testid="prescore-check-problem_statement_solution_language"]');
      await pill.waitFor();
      const status = await pill.getAttribute("data-status");
      assert(status === "flag", `expected prescore check status "flag", got ${JSON.stringify(status)}`);
      const text = await pill.textContent();
      assert(
        text?.toLowerCase().includes("solution language"),
        `expected the pill's label to mention solution language, got ${JSON.stringify(text)}`,
      );
    });

    await step("assert the solution-language flag renders on the field itself", async () => {
      // ProblemStatementSection's "What" field is flagged via
      // CharterForm's fieldFlag() mapping (charterChecks.ts), independent
      // of the prescore strip -- render the same information twice for
      // two different jobs (strip = overview, field = where to fix it).
      // The flag message div is a sibling of the input inside .sigma-field
      // (see design/components/Field.tsx), so one level up is enough.
      const whatField = page.locator('[data-testid="charter-problem-what"]').locator("..");
      await whatField.locator(".sigma-field__flag-message").waitFor();
      const flagText = await whatField.locator(".sigma-field__flag-message").textContent();
      assert(
        flagText?.toLowerCase().includes("solution") || flagText?.toLowerCase().includes("cause"),
        `expected the field-level flag to mention solution/cause language, got ${JSON.stringify(flagText)}`,
      );
    });
  } catch (err) {
    await finish(browser, false, err);
    return;
  }

  await finish(browser, true, null);
}

async function finish(browser, ok, err) {
  await browser.close();

  const failedSteps = steps.filter((s) => s.status === "FAIL");
  const overallOk = ok && failedSteps.length === 0 && pageErrors.length === 0;

  console.log("\n========== SMOKE TEST SUMMARY ==========");
  console.log(`Steps: ${steps.length} run, ${steps.filter((s) => s.status === "PASS").length} passed, ${failedSteps.length} failed`);
  console.log(`Page errors: ${pageErrors.length}`);
  console.log(`Console errors: ${consoleErrors.length}`);
  if (err) console.log(`Thrown error: ${err instanceof Error ? err.message : String(err)}`);
  if (pageErrors.length > 0) {
    console.log("Page error detail:");
    for (const e of pageErrors) console.log(`  - ${e}`);
  }
  console.log(overallOk ? "RESULT: PASS" : "RESULT: FAIL");
  console.log("=========================================");

  process.exit(overallOk ? 0 : 1);
}

main().catch((err) => {
  console.error("Unhandled error in smoke script:", err);
  process.exit(1);
});
