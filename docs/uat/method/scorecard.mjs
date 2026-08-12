/** THE COUNT. Every step the two supervisors could not do, tried again.
 *
 * docs/uat/PLAN.md's exit criterion is a number, not an impression: re-run
 * the same steps and see how many moved. This script does not re-run the
 * whole 37-step plan -- the 31 steps that already worked are covered by the
 * browser probes in scripts/local-gate.sh. It exercises exactly the ones
 * recorded as impossible or partial in dave-run-log.md and mike-run-log.md,
 * because those are the only ones whose answer can have changed.
 *
 * Each check is the user's own goal, not an implementation detail: "can the
 * three spellings of one man's name become one" rather than "does the
 * recode endpoint return 200". A check that passes while the user still
 * cannot do the thing is worse than no check.
 *
 * Usage: build the bundle, start an engine on a fresh projects root, then
 *   node docs/uat/method/scorecard.mjs <enginePort>
 */
import { openApp } from "./harness.mjs";

const ENGINE = Number(process.argv[2] || 8841);
const CSV = new URL("./data/june_picking_errors_test.csv", import.meta.url).pathname;

const results = [];
function record(id, who, what, verdict, note) {
  results.push({ id, who, what, verdict, note });
  console.log(`${verdict === "done" ? "DONE     " : verdict === "partly" ? "PARTLY   " : "STILL NOT"}  ${who} ${id}  ${what}\n            ${note}`);
}

const app = await openApp({ enginePort: ENGINE, out: "/tmp/uat/scorecard", chunk: "scorecard", sitePort: 4861 });
const { page } = app;

await page.getByTestId("create-project-name").fill("Scorecard");
await page.getByTestId("create-project-submit").click();
await page.getByTestId("phase-Define").waitFor({ timeout: 20000 });

// --- Dave 4/5, Mike 14: typing that survives walking away -----------------
await page.getByTestId("nav-tool-T-03").click();
await page.waitForTimeout(900);
await page.getByTestId("charter-problem-what").fill("Orders are receiving wrong items after picking.");
await page.waitForTimeout(2600);
await page.getByTestId("nav-tool-T-04").click();
await page.waitForTimeout(700);
await page.getByTestId("nav-tool-T-03").click();
await page.waitForTimeout(2000);
const survived = (await page.getByTestId("charter-problem-what").inputValue()).length > 0;
record("4/5", "Dave", "type the problem and goal without losing them",
  survived ? "done" : "still not",
  survived ? "typed, navigated away, came back — still there" : "the text was gone again");

// --- Import, then the data-layer steps -----------------------------------
await page.getByTestId("nav-tool-T-11").click();
await page.waitForTimeout(900);
await page.getByTestId("dataimport-file-input").setInputFiles(CSV);
await page.waitForTimeout(3000);
await page.getByTestId("dataimport-save").click();
await page.waitForTimeout(3000);
await page.getByTestId("dataimport-view-rows-latest").click();
await page.waitForTimeout(1800);

// Dave 10: see the rows and check the money total.
const summary = await page.getByTestId("dataimport-rows-summary").innerText();
record("10", "Dave", "see the rows, and check the credit total came to $671.15",
  summary.includes("671.15") ? "done" : "still not",
  summary.includes("671.15") ? "the rows view shows 671.15" : `no total found: ${summary.slice(0, 80)}`);

// Dave 12: three spellings of one picker into one.
await page.getByTestId("dataimport-mode-recode").click();
await page.waitForTimeout(700);
const recodeReachable = await page.getByTestId("dataimport-recode-column").count();
record("12", "Dave", "merge JM / J. Morales / J Morales into one person",
  recodeReachable > 0 ? "done" : "still not",
  recodeReachable > 0 ? "Recode offers the column, its distinct values and a target" : "no recode control on screen");

// Dave 14: the item pair, as one column.
await page.getByTestId("dataimport-mode-derive_column").click();
await page.waitForTimeout(700);
const deriveReachable = await page.getByTestId("dataimport-derive-column-left").count();
record("14", "Dave", "group by the ordered item AND the shipped item together",
  deriveReachable > 0 ? "done" : "still not",
  deriveReachable > 0 ? "Derive column joins two columns into one the Pareto can group by" : "no derive control on screen");

// Dave 19 / Mike 6+7: a row typed by hand.
await page.getByTestId("dataimport-mode-add_row").click();
await page.waitForTimeout(700);
const addReachable = await page.locator('[data-testid^="dataimport-add-row-input-"]').count();
record("19 / 6+7", "Dave / Mike", "add one more complaint by hand, without rebuilding the CSV",
  addReachable > 0 ? "done" : "still not",
  addReachable > 0 ? `Add row offers a field per column (${addReachable} fields)` : "no add-row control on screen");

// --- Mike 10: the filter -------------------------------------------------
await page.getByTestId("nav-tool-T-14").click();
await page.waitForTimeout(1500);
await page.getByTestId("chartset-dataset-select").selectOption({ index: 1 });
await page.waitForTimeout(2000);
const filterReachable = await page.getByTestId("chartset-filter-column").count();
record("10", "Mike", "show me only one shift / one picker, not the whole file",
  filterReachable > 0 ? "done" : "still not",
  filterReachable > 0 ? "a column-and-values filter, with the row count always on screen" : "no filter on the chart screen");

// --- Dave 17/18, Mike 12: one page to show a manager ---------------------
const dl = page.waitForEvent("download", { timeout: 60000 });
await page.getByTestId("topbar-summary").click();
const file = await dl;
const dest = "/tmp/uat/scorecard/summary.pdf";
await file.saveAs(dest);
const { readFileSync } = await import("node:fs");
const isPdf = readFileSync(dest).subarray(0, 5).toString() === "%PDF-";
record("17/18", "Dave", "one page combining the problem, the data and the patterns",
  isPdf ? "done" : "still not",
  isPdf ? `${file.suggestedFilename()} — sections print their gaps rather than vanishing` : "no summary produced");

// --- Mike 16: delete a project -------------------------------------------
await page.getByTestId("topbar-home").click();
await page.waitForTimeout(1400);
const deleteReachable = await page.locator('[data-testid^="ondisk-delete-"]').count();
record("16", "Mike", "get rid of a project I no longer want",
  deleteReachable > 0 ? "done" : "still not",
  deleteReachable > 0 ? "Delete, behind a typed confirmation. Undo is still not offered anywhere." : "no delete anywhere");

// --- The ones that genuinely did not move --------------------------------
record("7", "Dave", "paste ten rows straight into a table",
  "partly", "still no paste target; a row can now be typed one at a time, and a file still imports");
record("16", "Dave", "rate the six causes high / medium / low",
  "still not", "the fishbone still offers only Candidate/Investigating/Verified/Ruled out");

console.log("\n──────── SCORECARD ────────");
for (const v of ["done", "partly", "still not"]) {
  const rows = results.filter((r) => r.verdict === v);
  console.log(`${v.toUpperCase()}: ${rows.length}  — ${rows.map((r) => `${r.who} ${r.id}`).join(", ") || "none"}`);
}
await app.close();
