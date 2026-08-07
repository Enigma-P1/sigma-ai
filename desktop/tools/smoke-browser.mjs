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

// Strips everything but digits/./- so "6,000" or "Total: 9,600" reads as a
// plain number, regardless of the browser's thousands-separator locale.
function numeric(text) {
  if (text == null) return NaN;
  return Number(text.replace(/[^\d.-]/g, ""));
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

    await step("assert the Export PDF button is enabled now that a version is saved", async () => {
      // Button-state only -- actually triggering the download goes through
      // a Tauri save dialog in the packaged app, which isn't reachable
      // from a plain Chromium/Playwright session (M1 export brief).
      const exportBtn = page.locator('[data-testid="charter-export-pdf"]');
      await exportBtn.waitFor();
      assert(await exportBtn.isEnabled(), "Export PDF button should be enabled once a charter version is saved");
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

    // ---- Define-completion additions (M1 build-out): T-02/T-04/T-05 real
    // forms, plus the gate override feedback loop (gates.py's
    // _covering_override). The override is exercised BEFORE T-05 is saved
    // on purpose: define_to_measure requires T-03+T-04+T-05, and by the
    // time all three exist the gate is plain CLEAR with nothing left to
    // override -- checking it here, with T-05 still missing, is the only
    // point in this flow with a real soft block to clear. ----

    await step("open T-02 COPQ and fill two cost rows", async () => {
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

      assert(await page.locator('[data-testid="copq-save"]').isEnabled(), "COPQ save button should be enabled once both rows are filled");
    });

    await step("save T-02 and see the server-computed total render", async () => {
      await page.locator('[data-testid="copq-save"]').click();
      await page.locator('[data-testid="copq-version-badge"]').waitFor();
      // The version badge renders as soon as the save POST resolves, but
      // useCopqForm's reload-after-save GET (what actually populates the
      // engine-computed amounts/total) is a separate awaited step just
      // after -- wait for that render to land before reading values.
      await page.waitForFunction(() => document.querySelector('[data-testid="copq-row-0-amount"]')?.value !== "not yet computed");

      const row0Amount = await page.locator('[data-testid="copq-row-0-amount"]').inputValue();
      const row1Amount = await page.locator('[data-testid="copq-row-1-amount"]').inputValue();
      assert(numeric(row0Amount) === 6000, `expected row 0's engine-computed amount to be 6000 (500 x 12), got ${JSON.stringify(row0Amount)}`);
      assert(numeric(row1Amount) === 3600, `expected row 1's engine-computed amount to be 3600 (80 x 45), got ${JSON.stringify(row1Amount)}`);

      const totalHeadline = await page.locator('[data-testid="copq-total"] .sigma-verdict__headline').textContent();
      assert(numeric(totalHeadline) === 9600, `expected the server-computed total to read 9600 (6000 + 3600), got ${JSON.stringify(totalHeadline)}`);
      const totalDetail = await page.locator('[data-testid="copq-total"] .sigma-verdict__detail').textContent();
      assert(
        totalDetail?.toLowerCase().includes("computed by the engine"),
        `expected the total panel to say it's engine-computed, got ${JSON.stringify(totalDetail)}`,
      );
    });

    await step("open T-04 SIPOC and fill five clean process steps", async () => {
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

      assert(await page.locator('[data-testid="sipoc-save"]').isEnabled(), "SIPOC save button should be enabled once all five columns are filled");
    });

    await step("save T-04 and assert the step-count prescore reads clean", async () => {
      await page.locator('[data-testid="sipoc-save"]').click();
      await page.locator('[data-testid="sipoc-version-badge"]').waitFor();

      const pill = page.locator('[data-testid="prescore-check-step_count_range"]');
      await pill.waitFor();
      const status = await pill.getAttribute("data-status");
      assert(status === "pass", `expected 5 steps to read a clean (pass) step-count range, got ${JSON.stringify(status)}`);
    });

    await step("switch to Measure and confirm the Define exit gate soft-blocks (T-05 still missing)", async () => {
      await page.locator('[data-testid="nav-tool-T-06"]').click();
      await page.locator('[data-testid="gate-override-open"]').waitFor();
    });

    await step("log a soft-block override with a reason and confirm the gate renders cleared-with-note", async () => {
      const overrideReason = "Charter, COPQ, and SIPOC are done; unblocking Measure prep while VoC/CTQ is finished.";
      await page.locator('[data-testid="gate-override-open"]').click();
      await page.locator('[data-testid="gate-override-reason"]').fill(overrideReason);
      await page.locator('[data-testid="gate-override-submit"]').click();

      const clearedNote = page.locator(".sigma-verdict", { hasText: "cleared, override logged" });
      await clearedNote.waitFor();
      const bannerText = await clearedNote.textContent();
      assert(
        bannerText?.includes(overrideReason),
        `expected the cleared-with-note banner to include the logged override reason, got ${JSON.stringify(bannerText)}`,
      );
    });

    await step("open T-05 VoC -> CTQ and build one statement -> need -> CTQ", async () => {
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

      assert(await page.locator('[data-testid="voc-ctq-save"]').isEnabled(), "VoC/CTQ save button should be enabled once the tree is complete");
    });

    await step("save T-05 and assert tree-completeness prescore passes", async () => {
      await page.locator('[data-testid="voc-ctq-save"]').click();
      await page.locator('[data-testid="voc-ctq-version-badge"]').waitFor();

      const pill = page.locator('[data-testid="prescore-check-tree_completeness"]');
      await pill.waitFor();
      const status = await pill.getAttribute("data-status");
      assert(status === "pass", `expected the VoC/CTQ tree to read complete (pass), got ${JSON.stringify(status)}`);
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
