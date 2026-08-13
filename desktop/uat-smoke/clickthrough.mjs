/** THE COLD-START CLICK-THROUGH, DRIVEN.
 *
 * Shawn's Gate 1 checklist, performed by the harness against the production
 * bundle and a real engine: create project -> import ErrorLog_Sept.xlsx ->
 * Pareto -> download the chart picture -> one-page summary -> quit ->
 * relaunch -> the project is still there. Screenshots at every step.
 *
 * Usage:  node uat-smoke/clickthrough.mjs <enginePort>
 * The engine must already be running with SIGMA_PROJECTS_ROOT set; this
 * script kills nothing — the caller restarts the engine for the relaunch leg
 * by running with STAGE=relaunch after bouncing the engine process.
 */
import { openApp } from "./harness.mjs";
import { readFileSync } from "node:fs";

const ENGINE = Number(process.argv[2] || 8801);
const STAGE = process.env.STAGE || "first-run";
const OUT = `/tmp/uat/clickthrough-${STAGE}`;
const XLSX = new URL("../../docs/uat/method/data/ErrorLog_Sept.xlsx", import.meta.url).pathname;
const PROJECT = process.env.PROJECT_NAME || "Sept error log — cold start";

const app = await openApp({ enginePort: ENGINE, out: OUT, chunk: STAGE, sitePort: 4899 });
const { page } = app;
const fails = [];
const pass = (step, ok, note) => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${step}  ${note}`);
  if (!ok) fails.push(`${step}: ${note}`);
};

if (STAGE === "first-run") {
  // 1. Create a project
  await app.shot("01-front-door", "what a new user sees first");
  await page.getByTestId("create-project-name").fill(PROJECT);
  await page.getByTestId("create-project-submit").click();
  await page.getByTestId("phase-Define").waitFor({ timeout: 20000 });
  await app.shot("02-project-created", "project open, DMAIC phases visible");
  pass("create project", true, "phases rendered");

  // 2. Import the spreadsheet
  await page.getByTestId("nav-tool-T-11").click();
  await page.waitForTimeout(900);
  await page.getByTestId("dataimport-file-input").setInputFiles(XLSX);
  await page.waitForTimeout(3000);
  await app.shot("03-import-preview", "file parsed, preview on screen");
  await page.getByTestId("dataimport-save").click();
  await page.waitForTimeout(3000);
  const rowsBtn = await page.getByTestId("dataimport-view-rows-latest").count();
  pass("import ErrorLog_Sept.xlsx", rowsBtn > 0, rowsBtn > 0 ? "saved; rows view offered" : "no rows view after save");
  if (rowsBtn > 0) {
    await page.getByTestId("dataimport-view-rows-latest").click();
    await page.waitForTimeout(1800);
    await app.shot("04-own-rows", "the user's own rows, with totals");
  }

  // 3. Pareto chart
  await page.getByTestId("nav-tool-T-14").click();
  await page.waitForTimeout(1500);
  await page.getByTestId("chartset-dataset-select").selectOption({ index: 1 });
  await page.waitForTimeout(2000);
  if (await page.getByTestId("chartset-pareto-column").count()) {
    const sel = page.getByTestId("chartset-pareto-column");
    const labels = await sel.locator("option").allInnerTexts();
    const smart = labels.findIndex((l) => /wrong.part|error|reason|type|categor|cause|defect/i.test(l));
    if (smart >= 0) await sel.selectOption({ index: smart });
    else if (labels.length > 1) await sel.selectOption({ index: 1 });
    console.log(`   pareto column options: ${labels.join(" | ")}`);
    await page.waitForTimeout(2000);
  }
  const paretoUp = await page.getByTestId("chartset-pareto-panel").count();
  await app.shot("05-pareto", "the Pareto, drawn from the imported file");
  pass("Pareto renders", paretoUp > 0, paretoUp > 0 ? "panel on screen" : "no pareto panel");

  // 4. Download the chart as a picture
  const dlChart = page.waitForEvent("download", { timeout: 60000 });
  await page.getByTestId("chartset-pareto-download").click();
  const chartFile = await dlChart;
  const chartDest = `${OUT}/pareto.png`;
  await chartFile.saveAs(chartDest);
  const png = readFileSync(chartDest);
  const isPng = png.subarray(1, 4).toString() === "PNG";
  pass("chart downloads as picture", isPng && png.length > 10000,
    `${chartFile.suggestedFilename()} — ${png.length} bytes${isPng ? ", real PNG" : ", NOT a PNG"}`);

  // 5. One-page summary
  const dlSum = page.waitForEvent("download", { timeout: 60000 });
  await page.getByTestId("topbar-summary").click();
  const sumFile = await dlSum;
  const sumDest = `${OUT}/summary.pdf`;
  await sumFile.saveAs(sumDest);
  const pdf = readFileSync(sumDest);
  pass("one-page summary", pdf.subarray(0, 5).toString() === "%PDF-" && pdf.length > 20000,
    `${sumFile.suggestedFilename()} — ${pdf.length} bytes`);
  await app.shot("06-after-summary", "app state after producing the summary");
} else {
  // 6. Relaunch: fresh app + freshly restarted engine. The project must be
  // in the on-disk list, and must open.
  await app.shot("07-relaunch-front-door", "front door after quit and engine restart");
  const row = page.locator('[data-testid^="ondisk-project-"]', { hasText: PROJECT }).first();
  const listed = (await row.count()) > 0;
  pass("project survives relaunch", listed, listed ? "named project in the list" : "project missing from list");
  if (listed) {
    await row.click();
    await page.getByTestId("phase-Define").waitFor({ timeout: 20000 }).catch(() => {});
    const reopened = await page.getByTestId("phase-Define").count();
    await app.shot("08-reopened", "the surviving project, reopened");
    pass("project reopens", reopened > 0, reopened > 0 ? "phases visible again" : "did not reopen");
  }
}

const problems = await app.close();
if (problems?.length) console.log("HARNESS PROBLEMS:\n" + problems.join("\n"));
console.log(fails.length ? `\nRESULT: ${fails.length} FAILURE(S)` : "\nRESULT: ALL PASS");
process.exit(fails.length ? 1 : 0);
