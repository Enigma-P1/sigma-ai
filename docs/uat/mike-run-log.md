# RUN LOG — Mike Thompson's plan, driven for real

**Who:** Mike Thompson, warehouse ops supervisor, aftermarket auto-parts DC.
**App:** Sigma AI desktop bundle (`desktop/dist`) served at the packaged origin, engine on port 8802, fresh empty project store.
**Run directory:** `/tmp/uat/mike`
**Date of run:** 2026-08-12, 14:07–14:36 UTC.
**File used:** `/tmp/uat/desktop-files/ErrorLog_Sept.xlsx` — Mike's real file, unmodified. 71 spreadsheet rows = 1 header + 69 rows, of which row 25 is entirely blank and row 46 is the header line pasted a second time. Dates appear in two formats in one column (Excel date cells and text like `9/14`). 8 order numbers blank, 4 right-part cells blank, 7 part-number cells carry a trailing space.

**Outcome in one line:** 15 of 17 steps completed; 2 were impossible (steps 6 and 7); 62 screenshots, 17 videos, 3 files downloaded to disk. No browser console errors and no HTTP error responses were recorded in any chunk.

---

## Step 1 — Double-click the icon to open the app for the first time

- **Tried:** loaded the app cold against an empty project store.
- **Expected (Mike):** "some kind of welcome screen or empty workspace."
- **Actual:** a welcome screen headed **"Sigma AI"** with the line *"A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one."* Below it, a form headed **"Start a new project"** with two boxes (`Project name*`, `Project folder (ID)`), the line *"Default location: ~/.sigma-ai/projects/project"*, a **Create project** button, and a second block **"Open a project"** reading *"No recent projects yet on this machine."* and *"No projects in your projects folder yet."* Five interactive things on the whole screen; two of them (**Create project**, **Open**) were greyed out.
- **Shots:** `shots/01-open-and-create-01-cold-start.png`, `shots/01-open-and-create-02-cold-start-full.png`

## Step 2 — Look for a button that says "New Project" or "Create New", click it, type "Picking Errors Sept"

- **Tried:** enumerated every button label on the welcome screen, then clicked the closest match, then typed the name.
- **Expected (Mike):** a button with those words, then a name box.
- **Actual:** **there is no "New Project" button and no "Create New" button.** The only two buttons on the screen were `Create project` and `Open`. Clicking **Create project** straight away did nothing — it was disabled on arrival, the click never landed (Playwright: `element is not enabled`, timed out after 3 s), and the page text was byte-identical before and after. Typing `Picking Errors Sept` into the box under `Project name*` un-greyed it. The `Project folder (ID)` box auto-filled itself to `picking-errors-sept` as the name was typed.
- **Shots:** `shots/01-open-and-create-03-clicked-greyed-create.png` (the dead click), `shots/01-open-and-create-04-typed-project-name.png`

## Step 3 — Hit whatever saves or creates it, see what comes up next

- **Tried:** clicked **Create project**.
- **Expected (Mike):** "probably a blank table or dashboard."
- **Actual:** the project was created in ~1.6 s. What came up was neither a table nor a dashboard: a **DMAIC tool rail listing 26 tools** in seven phase groups (INTAKE, DEFINE, MEASURE, ANALYZE, IMPROVE, CONTROL, WRAP), each phase carrying a status line — five of them read *"Needs earlier steps (can override)"* — and each tool badged `Available`. The main pane opened on **T-01 Project Picker (+ PDCA quick path routing)**, a form of five Yes/No questions ("Is the scope narrow enough to actually finish?", "Is there a measurable outcome?", "Can you actually get the data?", "Does a process owner care about this?", "Is the business impact plausible?"), a `Route` choice of Full DMAIC / PDCA quick path / Not a good fit (EXIT-01), and a greyed-out **Save** under the line *"Missing: Is the scope narrow enough to actually finish? (answer), … a route"*. Sixty clickable things on screen. Six "Download the … pack (0)" buttons, all greyed out.
- **Shots:** `shots/01-open-and-create-05-after-create.png`, `shots/01-open-and-create-06-after-create-full.png`

## Step 4 — Find where to import data, pull in ErrorLog_Sept.xlsx

- **Tried:** looked over the project screen for an import; then opened all 26 tools in turn and checked each for a file box or import wording; then used the one that had it.
- **Expected (Mike):** an obvious Import button; the file loads.
- **Actual:** the project screen has **no import anywhere** — 0 file boxes, and no line of text on it contains "import", "upload", "Excel", "CSV" or "browse". Of the 26 tools, exactly **one** offers a data import: **T-11**, whose menu entry reads *"T-11 Data Collection Plan (+ sample-size guidance)"* — the word "import" does not appear in that name. Inside it, a tab strip reads `Import Data | Collection Plan | Sample Size`, and the Import Data tab says *"Data Collection Plan — import a dataset"* / *"Upload a CSV or XLSX file"*. (Two other tools have a file box, but not for a dataset: T-07 Spaghetti Diagram, whose box is labelled *"Upload a floor-plan image, or a photo of a paper sketch"*, and T-23 5S Audit, whose box carries no CSV/Excel wording anywhere near it.)
  The file picker accepts `.csv,.xlsx`. **Mike's messy file went in and was accepted** — no rejection, no crash — in ~2.7 s. It was then saved with the button **"Save dataset to project"**, which printed:
  > ✓ Saved: 69 rows as dataset 30adcea1
  > SHA-256 360f393ac516436f8beb97814559184a712971727edd8dc27c16694ef2708889 — the provenance anchor any baseline computed from this dataset links back to.
  The app read 69 rows from 71 spreadsheet rows: it silently dropped the blank row, and **kept the duplicated header line (row 46) as a data row**. Nothing on screen said either thing had happened.
  One friction point: leaving T-11 and coming back cleared the upload — the screen was back to *"Upload a CSV or XLSX file"* and the file had to be chosen again before it could be saved.
- **Shots:** `shots/02-find-import-01-project-home.png`, `shots/02-find-import-02-import-candidate-full.png`, `shots/03-import-excel-01-t11-landing.png`, `shots/03-import-excel-02-after-upload.png`, `shots/03-import-excel-03-after-upload-full.png`, `shots/04-save-and-type-rows-01-t11-on-return.png`, `shots/04-save-and-type-rows-02-after-save-dataset.png`, `shots/04-save-and-type-rows-03-after-save-dataset-full.png`

## Step 5 — If it asks what kind of data, pick "numbers and text" or the default

- **Tried:** looked for a data-type question after the upload.
- **Expected (Mike):** "a simple choice like numbers and text."
- **Actual:** it asked **per column, not per file**. A table appeared headed `Column | Inferred type | Confirmed type | Sample values`, under the line *"Column types are inferred automatically. Confirm or change them below, review the quality scan, then save."* Five dropdowns, each offering exactly two options — `numeric` and `text` — and **all five had pre-selected `text`**, including `Order #` and both part-number columns. Mike said he'd take the default, so nothing was changed. The sample values it printed for `Date` were `2026-09-01T00:00:00, 9/14, 9/27, 2026-09-11T00:00:00, 9/24` — both of his date formats side by side in the same column.
  Underneath, a quality scan fired:
  > ⚠ Quality scan found 59 issues across 69 rows
  > Order #: 8 missing values
  > Right Part: 4 missing values
  > Notes: 47 missing values
  > 69 total rows scanned
  It did not mention the duplicated header row or the trailing-space part numbers.
- **Shots:** `shots/03-import-excel-04-type-question.png`

## Step 6 — Type in the first few rows manually: date 9/3, order 48291, wrong part 44521, right part 44512

- **Tried:** looked for an add-row control on the data screen; clicked the first cell of the table and typed `9/3`; then swept all 26 tools for an add-row button or a typeable table cell; then went to the nearest data-entry screen and tried to put the values in.
- **Expected (Mike):** an editable table where I can add rows to my data.
- **Actual: IMPOSSIBLE.** The imported data cannot be edited or appended anywhere. The T-11 screen shows a 5-row column summary whose cells are plain text — clicking a cell and typing did nothing, and the typed text appeared nowhere. There is no add-row button on it. Data only ever enters through a CSV/XLSX file.
  Seventeen of the 26 tools do have `+ Add …` buttons, but every one adds a row to that tool's *own form* — `+ Add cost row`, `+ Add team member`, `+ Add milestone`, `+ Add supplier/input pair`, `+ Add cause to People`, `+ Add solution` — not to the dataset.
  The closest data-entry screen is **T-08 Check Sheet / Tally**, which has two modes, **Live tally** ("one tap per remake as it happens") and **Transcribe a paper tally**. Both take a **count per category**, not a record per error. Mike's two wrong part numbers went in as the two category labels (`44521`, `22187`) and a count of `1` was typed against the first. The transcribe screen's only other boxes are a `datetime-local` under *"When was this paper sheet's period -- not right now."* and a source-note box (`e.g. clipboard sheet dated 7/20, transcribed by Priya 7/22`). **There is no box for an order number and no box for a right/correct part on either mode** — the word "date" does not appear as a field label and "order number" appears nowhere. So 2 of Mike's 4 values had nowhere to go, and the two that fit went in as category names rather than as a row. That check sheet did save (`v1 saved`).
- **Shots:** `shots/04-save-and-type-rows-04-looking-for-add-row.png`, `shots/05-manual-rows-01-t11-saved-state-full.png`, `shots/05-manual-rows-02-t08-checksheet-full.png`, `shots/05-manual-rows-03-t08-added-category.png`, `shots/05-manual-rows-05-t08-after-attempt-full.png`, `shots/05b-manual-rows-tally-01-t08-two-parts.png`, `shots/05b-manual-rows-tally-02-t08-transcribe-full.png`, `shots/05b-manual-rows-tally-03-t08-transcribe-typed.png`, `shots/05b-manual-rows-tally-04-t08-after-save-full.png`

## Step 7 — Add another row right after: 9/3, order 48304, wrong 22187, right 22189

- **Tried:** same surfaces as step 6.
- **Expected (Mike):** a second row underneath the first.
- **Actual: IMPOSSIBLE — there is no row to add to.** Nothing in the app accepts a record shaped like (date, order number, wrong part, right part) typed by hand. That shape only enters through a file import. The second part number, `22187`, was placed as a second check-sheet category, which is the nearest thing the screen allows.
- **Shots:** `shots/05b-manual-rows-tally-01-t08-two-parts.png`

## Step 8 — Look for any button that says "Analyze" or "Find Patterns" and click it

- **Tried:** scanned every visible line and every clickable element for those words; clicked the word ANALYZE; clicked the app's own help button; then opened each of the three tools filed under ANALYZE.
- **Expected (Mike):** a button that analyses my data.
- **Actual: there is no "Analyze" button and no "Find Patterns" button.** The word "ANALYZE" appears exactly twice on screen: as a **phase heading** in the left rail (subtitle *"Find and verify root causes."*, status *"Needs earlier steps (can override)"*), and inside the greyed-out **"Download the Analyze pack (0)"**. The heading is not clickable — nothing on the page changed. The word "pattern" appears only inside help prose.
  Clicking the app's own **"I'm stuck — what do I use now?"** opened a pop-up headed *"What do I use now?"* which said:
  > An offline routing tree for the Intake phase — a couple of plain questions, no AI involved.
  > **No stuck-tree for Intake yet.** This phase's guided routing hasn't shipped yet. Use the DMAIC rail on the left to see what's available in Intake, or open a tool directly.
  Its only controls were `×` and `Start over`. The three tools under ANALYZE are **T-15 Fishbone (6M) + 5 Whys**, **T-16 FMEA (process)** and **T-17 Hypothesis Testing (guided selector)** — all three are forms to fill in by hand; none of them opened from, or referred to, the file that had been imported.
- **Shots:** `shots/06-analyze-button-01-home-hunting-analyze-full.png`, `shots/06-analyze-button-02-im-stuck-full.png`, `shots/07-analyze-tools-and-chart-01-analyze-T-15.png`, `shots/07-analyze-tools-and-chart-02-analyze-T-16.png`, `shots/07-analyze-tools-and-chart-03-analyze-T-17.png`

## Step 9 — If it shows a list or chart, check if it groups by part number or time

- **Tried:** opened **T-14 Pareto / Histogram / Run Chart** (the only tool whose name promises a chart), picked the dataset, then set the grouping column to `Wrong Part`, then to `Date`.
- **Expected (Mike):** a chart grouped by part number or by time.
- **Actual: yes, it groups by part number, and it produced a real answer.** The screen has a `Dataset` dropdown offering `ErrorLog_Sept.xlsx (69 rows)` and a `Category column` dropdown listing exactly Mike's five spreadsheet columns: `Date, Order #, Wrong Part, Right Part, Notes`. Grouped by **Wrong Part** it printed, with a green tick:
  > ✓ Vital few: 22187, 44521, 31104, 78802, 59310 account for 87.0% of 69
  > Bars sorted by count; the line is cumulative share. Vital-few bars are highlighted to the 80% line.
  Grouped by **Date** the same banner became a 39-item list, because Mike's two date formats are counted as different categories — `9/1` and `2026-09-01T00:00:00` sit in it as separate entries:
  > ✓ Vital few: 9/1, 9/10, 9/11, 9/14, 9/18, 9/19, 9/2, 9/20, 9/21, 9/24, 9/27, 9/28, 9/29, 9/5, 9/8, 9/9, 2026-09-01T00:00:00, 2026-09-02T00:00:00, … 2026-09-27T00:00:00, 9/12 account for 81.2% of 69
  **Time of day / shift is not available at all** — no line anywhere on the screen mentions shift, hour or time of day, Mike's spreadsheet has no such column, and the app does not derive one.
  Two of the five charts on the same screen never produced anything: **Histogram** and **Run Chart** both sat on *"Waiting on the engine's descriptive statistics…"* over empty −1…6 axes, and their `Column` dropdown was empty. Below them: *"Scatter needs at least two numeric columns; this dataset has 0."* and *"Box plot needs one numeric column and one text (grouping) column."* — because every column was typed `text` by the step-5 default.
- **Shots:** `shots/07-analyze-tools-and-chart-04-t14-landing-full.png`, `shots/07-analyze-tools-and-chart-05-t14-chosen-full.png`, `shots/07-analyze-tools-and-chart-06-t14-result-full.png`, `shots/08-pareto-and-filter-01-pareto-by-part.png`, `shots/08-pareto-and-filter-02-pareto-by-date.png`, `shots/10-reopen-and-target-04-pareto-onscreen.png`

## Step 10 — Try typing in a filter myself: "show me only errors on first shift"

- **Tried:** listed every typeable box on the data and chart screens; searched the whole screen text for "filter", "search", "query"; opened the Advisor panel; typed the phrase into the only free-text box that existed.
- **Expected (Mike):** a filter box that narrows the data.
- **Actual: there is no filter box and no search box.** The words "filter", "search" and "query" do not appear anywhere on the data or chart screens. The chart screen's only typeable boxes are `USL (optional)` and `LSL (optional)` (both numeric). The only free-text box in reach was inside the collapsed **Advisor** panel, placeholder **"Ask about this project…"**, next to a mode dropdown (`Ask a question / Review my artifact / Help me think / Explain this / Tollgate review / …`). Mike's exact words `show me only errors on first shift` were typed into it. **Nothing happened to the chart** — the vital-few line was unchanged. There is no Send or Ask button next to it; the only buttons are `Export for chatbot`, `Export tollgate` and `Set up the advisor`. Advisor settings confirms why: *"No key stored yet -- the advisor stays off until one is set."*
  The only narrowing control anywhere is the `Category column` dropdown, which regroups the whole dataset — it cannot show a subset.
- **Shots:** `shots/08-pareto-and-filter-03-advisor-open-full.png`, `shots/08-pareto-and-filter-04-typed-filter-phrase.png`

## Step 11 — Add a note like "bin A-14 keeps messing up" and attach it to a few rows

- **Tried:** looked for a note control on the chart screen; swept all 26 tools for a box labelled or placeheld "note"; typed the note into one.
- **Expected (Mike):** a note I can pin to specific rows of my data.
- **Actual: notes cannot be attached to rows.** The dataset is not editable, so there is nothing to attach to, and no screen offers a per-row note. Note boxes exist only as one free-text field per tool form. The complete list found: `T-01 Project Picker` (Notes — *"Optional free text."*), `T-02 COPQ` (`Basis note*`, placeholder `Q2 scrap log export`), `T-03 Project Charter` (Notes), `T-19 Pilot Plan` (`Honesty note`), `T-23 5S Audit` (five boxes placeheld `note`, one per S, plus `Cadence note`). Mike's note `bin A-14 keeps messing up` was typed into T-01's Notes box — where it belongs to that whole tool, not to any row — and **it could not be saved**: T-01's Save stays greyed out until all five intake questions and a route are answered.
- **Shots:** `shots/09-notes-and-export-01-chart-no-note.png`, `shots/09-notes-and-export-02-note-typed-full.png`

## Step 12 — Look around for an export or save button, save whatever view I end up with

- **Tried:** listed every export/download/save control on the chart screen, then clicked three of them and checked what landed on disk.
- **Expected (Mike):** a save/export that puts my view somewhere I can use it.
- **Actual: ten such controls, and three real files landed on disk.** Verified on disk:
  | Control clicked | File written | Size | Type |
  |---|---|---|---|
  | Download plot as a PNG | `files/newplot.png` | 34,916 bytes | PNG 644×340 |
  | Download the Measure pack (1) | `files/Picking-Errors-Sept-measure-pack.pdf` | 5,610 bytes | PDF 1.4, 2 pages |
  | Export project | `files/Picking-Errors-Sept-project-record.pdf` | 3,587 bytes | PDF 1.4, 2 pages |
  Five of the six phase-pack buttons were greyed out and read `(0)`: Define, Analyze, Improve, Control, Wrap. Only `Download the Measure pack (1)` was live, and only because the check sheet had been saved.
  **The downloaded PNG does not show what the on-screen banner says.** The Pareto's x-axis is a numeric scale reading `20k, 30k, 40k, 50k, 60k, 70k, 80k` — the part numbers are plotted as numbers rather than as named categories, so **no bar carries a label**, the bars are not in count order despite the caption *"Bars sorted by count"*, and the cumulative-% line zigzags up and down instead of rising. There is nothing in the picture that tells Mike which bar is part 22187.
- **Shots:** `shots/09-notes-and-export-03-after-exports-full.png`; the downloaded chart itself is `files/newplot.png`

## Step 13 — Check if the app remembers the data when I close and reopen

- **Tried:** closed the app window, opened a new one, read the first screen, opened the project by clicking its name, checked the import screen and the chart tool.
- **Expected (Mike):** my project and my data are still there.
- **Actual: yes.** The reopened first screen listed **"Picking Errors Sept — Measure · 1 tool saved"**, and clicking that name opened the project. T-11 still read *"ErrorLog_Sept.xlsx — 69 rows, saved 2026-08-12T14:14:07.896Z"*, and the chart tool's dataset dropdown still offered `ErrorLog_Sept.xlsx (69 rows)`. Rebuilding the chart gave the identical result: *"Vital few: 22187, 44521, 31104, 78802, 59310 account for 87.0% of 69"*.
  What did **not** survive is the chart view itself: the dataset and the category column had to be re-picked from the two dropdowns every single time the tool was opened — the app never reopened on the chart Mike had made.
- **Shots:** `shots/10-reopen-and-target-01-reopened-welcome-full.png`, `shots/10-reopen-and-target-02-reopened-project.png`, `shots/10-reopen-and-target-03-reopened-t11-full.png`

## Step 14 — If it asks for a "target" or "defect rate", type in 20

- **Tried:** swept every tool for a field labelled target / defect rate / goal / DPMO, then typed `20` into the one actually labelled `Target*`.
- **Expected (Mike):** type 20 and see what it does with it.
- **Actual: nothing in the app ever asked for a "defect rate"** — the phrase does not appear. The only field named `Target` sits on **T-03 Project Charter**, inside a SMART-goal block that also demands `Goal statement*`, `Metric name*`, `Baseline`, `Unit*` and `Target date*`, inside a form of 24 boxes. Typing `20` into `Target*` produced no calculation and no feedback. The banner above still read *"Missing: Project Picker (+ PDCA quick path routing). You can still work here, but proceeding needs a logged reason."*, the charter still said **"Not saved yet."**, and its **Save button stayed greyed out**, with the screen listing what was still missing:
  > Missing: problem statement: what, problem statement: where, problem statement: when, goal metric name, goal unit, goal target date, scope: in-scope, scope: out-of-scope, process owner name, process owner role, business impact unit, business impact basis
  (The other target-shaped fields in the app: `T-05 VoC → CTQ Tree` has a Higher/Lower/Target-is-best selector with a target box placeheld `<1%`; `T-20 Before/After Proof` has `Charter baseline value` and `Charter goal value`.)
- **Shots:** `shots/10-reopen-and-target-05-typed-20-full.png`, `shots/11-target-and-drilldown-01-charter-before-full.png`, `shots/11b-target-field-01-typed-20-target.png`, `shots/11b-target-field-02-typed-20-target-full.png`

## Step 15 — Click on a graph or summary and drill into just the brake pad errors

- **Tried:** clicked the tallest Pareto bar; hovered it; read the axis labels; searched the screen for any drill/subset wording and for the word "brake".
- **Expected (Mike):** click a bar, see only those errors.
- **Actual: clicking a bar does not drill in.** The only thing the click produced was a chart label reading **`(22.187k, 17)`** — the part number 22187 rendered as a number in thousands. The rest of the page was unchanged. The chart's only interactive controls are the plot toolbar: `Zoom, Pan, Box Select, Lasso Select, Zoom in, Zoom out, Autoscale, Reset axes, Download plot as a PNG`. There is no drill-down, no click-to-filter and no subset view anywhere. The bottom axis reads `20k 30k 40k 50k 60k 70k 80k`, so a bar cannot be identified from the chart itself.
  On brake pads specifically: **the word "brake" appears nowhere in the app**, and Mike's spreadsheet has no column saying which parts are brake pads — so there is no way to select them even in principle.
- **Shots:** `shots/11-target-and-drilldown-02-pareto-before-click.png`, `shots/11-target-and-drilldown-03-after-bar-click.png`, `shots/11-target-and-drilldown-04-bar-hover.png`, `shots/11b-target-field-03-bar-click-label.png`

## Step 16 — Look for an undo or delete project option

- **Tried:** swept the project screen, the Diagnostics screen, the Advisor settings screen and the projects list for undo/delete/remove/trash/archive/discard/revert; hovered the project card; right-clicked the project card.
- **Expected (Mike):** an undo button, or a way to delete the project.
- **Actual: neither exists.** Not one control anywhere in the app says **Undo**. Nothing offers to **Delete**, **Remove**, **Archive** or **Trash** a project. Hovering the project in the list revealed no extra control; right-clicking it produced no menu. The projects list has exactly six interactive things on it, one of which is the project itself.
  The only reset-shaped control seen in the whole run was **"Start over"** inside the "I'm stuck" pop-up, which restarts that pop-up's own questions. Diagnostics offers no destructive action (it shows *"Sidecar target: Tauri sidecar (127.0.0.1:8756)"*, *"✓ Online — engine_version 0.1.0"* and a NIST smoke check). Advisor settings has a Save but nothing that deletes.
- **Shots:** `shots/12-undo-delete-01-step16-project-screen.png`, `shots/12-undo-delete-02-step16-diagnostics-full.png`, `shots/12b-undo-delete-rest-01-advisor-settings-full.png`, `shots/13-final-reopen-01-reopened-cold-full.png`, `shots/13-final-reopen-02-hover-project-card.png`, `shots/13-final-reopen-03-rightclick-project-card.png`

## Step 17 — Close the whole thing and reopen, confirm my project is still there

- **Tried:** closed the app window entirely, opened it fresh, read the first screen, opened the project, checked the tool badges, the import screen and the chart.
- **Expected (Mike):** my project is still there.
- **Actual: yes, the project and the data are still there.** The first screen listed **"Picking Errors Sept / Measure · 1 tool saved"** under the heading **IN YOUR PROJECTS FOLDER**. (The block above it still read *"No recent projects yet on this machine."* — the recents list stayed empty across every reopen in this run, while the folder list was correct.) Opening it showed T-11 still listing *"ErrorLog_Sept.xlsx — 69 rows, saved 2026-08-12T14:14:07.896Z"*, the chart dropdown still offering `ErrorLog_Sept.xlsx (69 rows)`, and the rebuilt Pareto printing the identical *"Vital few: 22187, 44521, 31104, 78802, 59310 account for 87.0% of 69"*.
  Two things did not come back the same: **T-08 Check Sheet / Tally still showed the `Done` badge, but T-14 Pareto showed `Available`** — the badge it had before it was ever used — and the app reopened on T-01 Project Picker, not on the chart.
- **Shots:** `shots/13-final-reopen-01-reopened-cold-full.png`, `shots/13-final-reopen-04-reopened-project-final.png`, `shots/13-final-reopen-05-final-t11-full.png`, `shots/13-final-reopen-06-final-pareto.png`

---

# WHAT I COULD NOT DO

| Step | What it was | Why it was impossible |
|---|---|---|
| **6** | Type in the first rows manually — date 9/3, order 48291, wrong part 44521, right part 44512 | The imported dataset is read-only: no add-row control, and its table cells are plain text (clicked one and typed `9/3` — nothing was entered). Data enters only via a CSV/XLSX file. The nearest data-entry screen, T-08 Check Sheet / Tally, records **counts per category**, and has no field for a date, an order number, or a right/correct part — 2 of Mike's 4 values had nowhere to go. |
| **7** | Add a second row: 9/3, order 48304, wrong 22187, right 22189 | Same reason — there is no row to add to. Nothing in the app accepts a hand-typed record shaped (date, order number, wrong part, right part). |

Things inside completed steps that could not be done as Mike described them:

- **Step 2** — no "New Project"/"Create New" button exists; the equivalent is a form already on the welcome screen whose **Create project** button is greyed out until a name is typed, and clicking it before that does nothing at all.
- **Step 8** — no "Analyze" or "Find Patterns" button exists anywhere; ANALYZE is only a phase heading, and it is not clickable.
- **Step 10** — no filter box, no search box, no way to narrow to a subset; typing Mike's sentence into the only free-text box ("Ask about this project…") changed nothing, and the advisor behind it is off with no API key.
- **Step 11** — a note cannot be attached to rows; note boxes belong to whole tool forms. The note typed into T-01 could not even be saved (Save greyed out pending five unanswered questions).
- **Step 14** — nothing asked for a "defect rate"; the one `Target` box is buried in a 24-field charter that would not save.
- **Step 15** — no drill-down of any kind; and "brake pads" is not a concept the app or the spreadsheet has.
- **Step 16** — no undo and no delete-project anywhere.

**Nothing in this run had to be found by reading the source code.** Every feature reported above was located by dumping the visible page text and reading it, exactly as Mike would. There is no `COULD NOT FIND ON SCREEN` entry — the features Mike went looking for and did not find (New Project, Analyze, Find Patterns, a filter, a per-row note, undo, delete project) are not hidden; on the evidence of the screen they do not exist.

---

# THINGS THE SCREEN SAID

**On first opening**
> Sigma AI
> A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one.
> Default location: ~/.sigma-ai/projects/project
> No recent projects yet on this machine.
> No projects in your projects folder yet.

**After the file went in** (T-11 Import Data)
> Column types are inferred automatically. Confirm or change them below, review the quality scan, then save.
> Date — inferred `text` — sample values: `2026-09-01T00:00:00, 9/14, 9/27, 2026-09-11T00:00:00, 9/24`
> ⚠ **Quality scan found 59 issues across 69 rows**
> Order #: 8 missing values
> Right Part: 4 missing values
> Notes: 47 missing values
> 69 total rows scanned

**After saving the dataset**
> ✓ Saved: 69 rows as dataset 30adcea1
> SHA-256 360f393ac516436f8beb97814559184a712971727edd8dc27c16694ef2708889 — the provenance anchor any baseline computed from this dataset links back to.
> Previously imported into this project: ErrorLog_Sept.xlsx — 69 rows, saved 2026-08-12T14:14:07.896Z

**The number Mike will ask about** (T-14 Pareto, grouped by Wrong Part)
> ✓ **Vital few: 22187, 44521, 31104, 78802, 59310 account for 87.0% of 69**
> Bars sorted by count; the line is cumulative share. Vital-few bars are highlighted to the 80% line.

The same banner grouped by Date, with his two date formats counted separately:
> ✓ Vital few: 9/1, 9/10, 9/11, 9/14, 9/18, 9/19, 9/2, 9/20, 9/21, 9/24, 9/27, 9/28, 9/29, 9/5, 9/8, 9/9, 2026-09-01T00:00:00, 2026-09-02T00:00:00, … 2026-09-27T00:00:00, 9/12 **account for 81.2% of 69**

Clicking the tallest bar produced only:
> (22.187k, 17)

**Charts that never drew**
> Waiting on the engine's descriptive statistics… *(Histogram)*
> Waiting on the engine's descriptive statistics… *(Run Chart)*
> Scatter needs at least two numeric columns; this dataset has 0.
> Box plot needs one numeric column and one text (grouping) column.

**Gates and warnings that sat above every Measure/Analyze tool**
> ⚠ Measure: Needs earlier steps (can override)
> Missing: Project Charter, SIPOC, VoC → CTQ Tree. You can still work here, but proceeding needs a logged reason.
> **Override & proceed**

**When Mike asked the app for help**
> What do I use now?
> An offline routing tree for the Intake phase — a couple of plain questions, no AI involved.
> **No stuck-tree for Intake yet.** This phase's guided routing hasn't shipped yet. Use the DMAIC rail on the left to see what's available in Intake, or open a tool directly.

**The charter, after typing 20 into Target**
> Not saved yet.
> Missing: problem statement: what, problem statement: where, problem statement: when, goal metric name, goal unit, goal target date, scope: in-scope, scope: out-of-scope, process owner name, process owner role, business impact unit, business impact basis

**Advisor settings** (why the "Ask about this project…" box did nothing)
> The Layer 2 advisor is optional. Layer 1 (every tool, all math, every chart) works fully without any of this.
> No key stored yet -- the advisor stays off until one is set.
> Your API key is stored in plain text in settings.json on this machine -- it is not encrypted.

**Diagnostics**
> Sidecar target: Tauri sidecar (127.0.0.1:8756)
> ✓ Online — engine_version 0.1.0
> NIST smoke check — Dataset: NIST StRD "Lew" (n = 200) — Mean −177.435 / −177.435, Std dev 277.33216804431606 / 277.332168044316
> ✓ NIST smoke check PASSED

**On reopening**
> Picking Errors Sept — Measure · 1 tool saved

---

## Where the evidence is

- `transcript-01-open-and-create.md` … `transcript-13-final-reopen.md` — 16 chunk transcripts, written as the run happened
- `shots/` — 62 captioned screenshots
- `video/` — 17 webm recordings, one per chunk (four are named for chunks whose script crashed partway: `05b-first-attempt-crashed`, `06-analyze-button`, `12-undo-delete`, `12b-undo-delete-rest` — in each case the driving script hit a selector problem, not the app; the steps were then redone in a follow-up chunk)
- `files/` — the three files the app actually wrote to disk
- `scripts/` — the step scripts that were run

No browser console errors, no uncaught page errors and no HTTP responses of 400 or above were recorded in any chunk of this run.
