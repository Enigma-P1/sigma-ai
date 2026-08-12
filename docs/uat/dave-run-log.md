# RUN LOG — Dave Mercer's plan, driven against Sigma AI

Run directory: `/tmp/uat/dave`
Engine: `127.0.0.1:8801`, fresh empty project store (`/tmp/uat/roots/dave` was empty at start — no example project existed).
Bundle served: `/home/user/sigma-ai/desktop/dist` (production build), Tauri conditions injected by `/tmp/uat/harness.mjs`.
Date on the machine during the run: 2026-08-12. Window 1440x950.
Project created: **June 2026 warehouse picking errors** (folder id `june-2026-warehouse-picking-errors`).
File used wherever the plan called for a file: `/tmp/uat/desktop-files/june_picking_errors_test.csv` (Dave's ten June rows, messy dates and inconsistent picker names untouched).

73 screenshots in `shots/`, 19 videos in `video/`, 3 downloaded files in `files/`, one transcript per chunk (`transcript-*.md`).
The browser reported **no** page errors, console errors or HTTP 4xx/5xx responses in any chunk.

---

## Step 1 — Open the app for the first time and see what the starting screen says

**Tried:** opened the app cold, took the screen before touching anything, dumped every visible word.
**Expected (Dave):** a welcome screen, a "new project" option, or some example project; screenshots of the whole first screen including words I don't understand.
**Actual:** A single screen headed **"Sigma AI"** with the line **"A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one."** Two cards: **"Start a new project"** (Project name*, Project folder (ID) pre-filled with `project`, small print "Default location: ~/.sigma-ai/projects/project", a pale **Create project** button) and **"Open a project"** ("No recent projects yet on this machine.", "IN YOUR PROJECTS FOLDER — No projects in your projects folder yet.", "Or open by project ID", an **Open** button). No example project anywhere. Unexplained words on this screen: *Green Belt*, *DMAIC*, *Project folder (ID)*.
**Shots:** `01-first-open-01-cold-start.png`, `01-first-open-02-cold-start-full.png`

## Step 2 — Look for a button that sounds like New Project / Create Project / Start

**Tried:** read the screen for such a button; tried the button before typing anything.
**Expected:** see one and select it; expect it to ask for a project name or problem description.
**Actual:** Found **"Create project"** inside the "Start a new project" card. It asks for a project name right there — no wizard, no problem-description box. Before a name is typed the button is greyed and the browser reports it as **disabled (cannot be clicked)**. The only other clickable things on the whole screen were the two text boxes and **Open**.
**Shots:** `02-create-project-01-before-typing.png`

## Step 3 — Type exactly `June 2026 warehouse picking errors`

**Tried:** typed the name character for character into "Project name*", then clicked Create project.
**Expected:** creates a blank project or takes me to the next setup screen; no example project forced on me.
**Actual:** "Project folder (ID)" auto-changed from `project` to `june-2026-warehouse-picking-errors`. Create project became clickable; the screen changed in **≈3.1 seconds**. It landed on a tool called **"T-01 Project Picker (+ PDCA quick path routing)"**, headed **"Is this a good first project?"** — five required Yes/No questions ("Is the scope narrow enough to actually finish?", "Is there a measurable outcome?", "Can you actually get the data?", "Does a process owner care about this?", "Is the business impact plausible?"), each with a one-line "what makes this true?" box, then a required **Route** (Full DMAIC / PDCA quick path / Not a good fit (EXIT-01)), Notes, and Save. Down the left is a rail of 26 numbered tools (T-01 … T-25, T-35) grouped INTAKE / DEFINE / MEASURE / ANALYZE / IMPROVE / CONTROL. No example project was offered or forced.
**Shots:** `02-create-project-02-typed-name.png`, `02-create-project-03-after-create.png`, `02-create-project-04-after-create-full.png`

## Step 4 — Type the problem statement exactly as written

**Tried:** looked for a problem box on the screen the app opened on (T-01) — none. Read the left rail: under **DEFINE** it says "Problem, goal, scope, and who it matters to."; opened **T-03 Project Charter**. Typed the 182-character paragraph.
**Expected:** the app saves that text without making me translate it into technical language.
**Actual:** There is **no single problem-statement box**. The charter has a heading "Problem statement" with the note *"What's wrong, where, when, and how much -- no causes, no solutions."* and under it **four separate required boxes: What\*, Where\*, When\*, Magnitude\***, the last captioned "Number + unit + period, so anyone can tell if it's improving." The paragraph was typed into **What\*** and held character for character, no truncation. The other three stayed empty and required. A yellow banner sat above the charter: **"Define: Needs earlier steps (can override) — Missing: Project Picker (+ PDCA quick path routing). You can still work here, but proceeding needs a logged reason."** with an **Override & proceed** button. The card also said **"Not saved yet."** and the window header kept saying **"No changes yet"** the whole time I typed.
**Shots:** `03b-problem-goal-01-charter-problem-section.png`, `03b-problem-goal-02-typed-problem-into-what.png`, `03-problem-goal-04-no-problem-field.png`

## Step 5 — Type the goal sentence exactly

**Tried:** typed the 96-character goal sentence into the box labelled **Goal statement\***.
**Expected:** either accepts the sentence, or shows separate fields for current number, target number and date.
**Actual:** It does both. The sentence was accepted exactly as typed into a textarea whose placeholder reads *"Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026."* Beside it are separate boxes: **Metric name\*** (text, empty), **Baseline** (number, empty), **Target\*** (number, **pre-filled with 0**), **Unit\*** (text, empty, placeholder "%"), **Target date\*** (a date picker, empty). Nothing was saved: see step 20 — this text was gone afterwards.
**Shots:** `03b-problem-goal-03-typed-goal.png`, `03b-problem-goal-04-charter-filled-full.png`, `03b-problem-goal-05-save-disabled.png`

**What happened when I tried to keep it:** the **Save** button at the bottom of the charter was greyed out and did not respond to a click (no tooltip). Under it, in a yellow strip: **"Missing: problem statement: where, problem statement: when, goal metric name, goal unit, goal target date, scope: in-scope, scope: out-of-scope, process owner name, process owner role, business impact unit, business impact basis"**. Fifteen boxes on that screen carry a red asterisk: What, Where, When, Magnitude, Goal statement, Metric name, Target, Unit, Target date, In scope, Out of scope, Process owner, Team, Timeline, Business impact. The screen's own guidance also says a process owner must be "A real, named person -- not a placeholder like TBD or management."

## Step 6 — Find somewhere to bring in a spreadsheet

**Tried:** read the top bar (only "← Projects", "Export project", "Advisor settings", "Diagnostics"); clicked the button at the bottom of the rail that says **"I'm stuck — what do I use now?"**; then opened the four tools whose names sound like data (T-08, T-11, T-13, T-14) and read each screen.
**Expected:** some way to import a spreadsheet rather than type every complaint; if CSV only, use the ten-row test file.
**Actual:** "I'm stuck" opened a panel that said: **"An offline routing tree for the Intake phase — a couple of plain questions, no AI involved."** then **"No stuck-tree for Intake yet — This phase's guided routing hasn't shipped yet. Use the DMAIC rail on the left to see what's available in Intake, or open a tool directly."** Import turned out to live inside **T-11 "Data Collection Plan (+ sample-size guidance)"**, on a tab called **Import Data**, headed **"Data Collection Plan — import a dataset"**, **"Upload a CSV or XLSX file"**, **"Column types are inferred automatically. Confirm or change them below, review the quality scan, then save."** It is the only file-upload box in the app: T-08 had none, T-13 had none, T-14 had none. Handing over `june_picking_errors_test.csv` produced a result in **≈4.0 seconds**.
**Shots:** `04-find-import-01-im-stuck.png`, `04-find-import-02-t-08-check-sheet.png`, `04-find-import-03-t-11-data-collection-plan.png`, `04-find-import-04-t-13-baseline.png`, `04-find-import-05-t-14-pareto.png`, `05-import-csv-01-import-tab.png`, `05-import-csv-03-after-upload.png`

## Step 7 — Paste the ten rows with the column names into a table

**Tried:** looked on the import screen for anywhere to paste rows.
**Expected:** it spots the first row as headings and shows the ten complaints as records; if it minds the mixed dates, show the exact error and whether it offers to fix or ignore.
**Actual:** **Not offered.** The import screen has exactly one control — a file box — and no textarea; the words *paste*, *type in*, *enter rows* and *table editor* appear nowhere on it. So the file was used instead. From the file, the app did read the first row as headings: all twelve column names appear as rows in a table headed **Column | Inferred type | Confirmed type | Sample values**, each with five sample values. It never showed the ten complaints as records.
**Shots:** `05-import-csv-01-import-tab.png`, `05-import-csv-04-after-upload-full.png`

## Step 8 — Retype the dates as `2026-06-03` … `2026-06-29` if it demands a clean date format

**Tried:** read the quality scan and the whole screen for any date complaint.
**Expected:** app accepts the tidied dates and either accepts blank aisle and different picker names or tells me which fields are mandatory.
**Actual:** **Never needed.** The app made no date complaint at all: `Complaint date` and `Delivery date` were both typed as **text**, and the word "date" does not appear in the quality scan. The scan said, in full: **"Quality scan found 1 issue across 10 rows — Aisle: 1 missing value — 10 total rows scanned"**. It did not tell me any field was mandatory, and it offered no fix/ignore choice. (The screen's own guidance elsewhere says: *"This is not a data-cleaning tool: the scan finds problems, it never silently fixes them"*.) The messy dates, the blank aisle and the three spellings of one picker's name all went in untouched.
**Shots:** `06-types-preview-02-quality-scan.png`

## Step 9 — Mark Aisle, Picker, Error type as groups; Quantity and Credit amount as numbers

**Tried:** opened the per-column type drop-downs and set them to Dave's settings.
**Expected:** the app detects it automatically or offers a simple choice; use those exact settings.
**Actual:** There is **no "category" or "group" setting** — the words *category*, *group*, *nominal*, *discrete* appear nowhere on the screen. Every column's drop-down offers exactly two words: **numeric** and **text**. What it decided on its own: Complaint date=text, Delivery date=text, Order number=**numeric**, Customer=text, Picker=text, Aisle=**numeric**, Item ordered=text, Item shipped=text, Error type=text, Quantity=numeric, Credit amount=numeric, Notes=text. Picker, Error type, Quantity and Credit amount matched what Dave wanted with no action. **Aisle** came in as a number, so it was changed to **text** — the only non-number choice on offer. (Order number stayed numeric, which is what the app chose.)
**Shots:** `06-types-preview-01-uploaded-again.png`, `06-types-preview-03-aisle-to-text.png`

## Step 10 — Find a preview / summary / basic table of the imported data

**Tried:** read the whole import screen, then pressed **Save dataset to project** and read it again.
**Expected:** 10 records, 10 order numbers, 1 blank aisle, credit amounts totalling $671.15.
**Actual:** Confirmed by the app: **"10 total rows scanned"**, **"Quality scan found 1 issue across 10 rows — Aisle: 1 missing value"**, and after saving **"✓ Saved: 10 rows as dataset 04727612"** with **"SHA-256 9d2c5177e5afe041940402d70bc611bd6bf8e81d2d76abdc20aa83196c9c0428 — the provenance anchor any baseline computed from this dataset links back to."** and a line **"Previously imported into this project: june_picking_errors_test.csv — 10 rows, saved 2026-08-12T14:16:48.574Z"**. Not shown anywhere: a list of the ten records, a count of distinct order numbers, and any money total — the figure **671.15 does not appear on any screen** (the ten Credit amount values in the file do add to $671.15, but the app never displays a total, so there was nothing to check it against). The only view of the data is five sample values per column. Save took **≈4.1 s**.
**Shots:** `06-types-preview-04-dataset-saved.png`, `06-types-preview-05-dataset-saved-full.png`

## Step 11 — Simplest analysis grouping records by Aisle, counting complaints

**Tried:** opened **T-14 Pareto / Histogram / Run Chart**, chose the dataset, set **Category column = Aisle**.
**Expected:** aisle 12 and aisle 7 near the top in this small sample.
**Actual:** Choosing the dataset (`june_picking_errors_test.csv (10 rows)`) made the screen draw five charts at once, headed **"Pareto / Histogram / Run Chart + Scatter / Box"**. Before I chose anything it had already drawn a **Histogram of "Order number"** — *"n=10 · mean 105516.70 Order number · sd 642.91 Order number · median 105287.00 Order number"* — a **Run Chart of Order number**, and a **Pareto grouped by "Complaint date"** whose verdict read *"No small subset dominates — 10 categories are roughly even (10 total)"* with a time axis printed as *"23:59:59.9996Jun 3, 2026 / 23:59:59.9998 / 00:00:00Jun 4, 2026"*.
It **never asked what to measure** — there is no count/sum/measure choice anywhere on the screen; the Pareto counts rows.
With Category column = Aisle the verdict was: **"No small subset dominates — 6 categories are roughly even (9 total)"**. Nine, not ten — the row with the blank aisle is not in the chart and no message says it was dropped. Six bars at heights 2, 2, 2, 1, 1, 1, but **no aisle number is printed under any bar**: the x-axis is a number line labelled 5, 10, 15, 20, so which bar is which aisle cannot be read off the chart. (In the file itself, aisles 3, 7 and 12 each have two complaints and 14, 19, 22 one each — but that is from the spreadsheet, not from anything the screen showed.) Dave's expectation that "aisle 12 and aisle 7 show up near the top" is therefore neither confirmed nor denied by what the app displayed.
**Shots:** `08-pareto-aisle-01-dataset-picked.png`, `09-group-by-01-pareto-default.png`, `09-group-by-02-pareto-aisle.png`, `09-group-by-03-pareto-aisle-full.png`

## Step 12 — Repeat by Picker; check whether JM / J. Morales / J Morales are three people; combine them

**Tried:** set Category column = Picker; then searched the screen for any way to combine or rename categories.
**Expected:** probably three separate people because the data is messy; combine all three as `J. Morales` and see if the chart changes.
**Actual:** Six labelled bars: **JM (3), AB (2), TK (2), J Morales (1), J. Morales (1), RL (1)** — one man appears as three separate people. The app's own headline reads: **"Vital few: JM, AB, TK, J Morales account for 80.0% of 10"**, i.e. two spellings of the same man are named as two of the four "vital few". **The combining could not be done**: the words *combine*, *merge*, *rename*, *recode*, *group values* and *edit categories* appear nowhere on the screen, and there is no click target on a bar or a label.
**Shots:** `09-group-by-04-pareto-picker.png`

## Step 13 — Group by Error type, leaving the three labels separate

**Tried:** set Category column = Error type.
**Expected:** see `wrong item`, `mispick`, `substitution` separately; see whether the software warns that these are inconsistent labels.
**Actual:** Three labelled bars, read off the chart: **wrong item 6, mispick 2, substitution 2**, y-axis 0–6. Verdict: **"Vital few: wrong item, mispick account for 80.0% of 10"**. **No warning of any kind** that the three labels may mean the same thing — the words *inconsistent*, *similar*, *synonym*, *duplicate label* appear nowhere. They are treated as three plain categories.
**Shots:** `09-group-by-05-pareto-errortype.png`

## Step 14 — Group by Item ordered AND Item shipped to find repeated item pairs

**Tried:** looked for a second grouping box, a crosstab or a pair option; then ran the two columns as two separate charts.
**Expected:** the pair `Ketchup packets 4 oz → Ketchup packets 6 oz` twice, and `Frozen chicken tenders 10 lb → Frozen chicken patties 10 lb` twice.
**Actual:** **Not possible.** The Pareto takes exactly one "Category column"; the words *pair*, *crosstab*, *two columns* and *combination* appear nowhere on the screen. Every drop-down on the chart screen: Dataset; Column (histogram) = [Order number | Quantity | Credit amount]; Column (run chart) = same three; Category column (Pareto) = the nine text columns; Scatter X and Y = the same three numbers only; Box plot = "Value column (numeric)" + "Group by (text)" — a two-column control, but the value side refuses text, so two text columns cannot be paired.
Run separately: by **Item ordered** — *"Vital few: Frozen chicken tenders 10 lb, Ketchup packets 4 oz, Low sodium soup, 12-inch flour tortillas, 5 oz burger patties account for 80.0% of 10"*; by **Item shipped** — *"Vital few: Frozen chicken patties 10 lb, Ketchup packets 6 oz, Regular soup, 10-inch flour tortillas, 4 oz burger patties account for 80.0% of 10"*. Each chart shows the ketchup line and the chicken line at 2, but the ordered→shipped pairing has to be matched up by eye across two charts.
**Shots:** `10-item-pairs-01-pareto-item-ordered.png`, `10-item-pairs-02-pareto-item-shipped.png`

## Step 15 — Enter the six possible causes exactly

**Tried:** opened **T-15 Fishbone (6M) + 5 Whys** under ANALYZE ("Find and verify root causes."), typed all six causes, saved.
**Expected:** lets me save them as a list or arrange them somehow; not expecting it to prove which one is true from ten rows.
**Actual:** It is not a plain list. The screen says **"Click a branch to add a candidate cause. Every cause needs an evidence pointer before it can be marked verified -- team consensus alone is not evidence. A candidate with no evidence yet carries a visible flag until it does."** Two things the plan did not anticipate:
1. A required **Effect statement\*** ("The baselined problem -- the measured gap, not a convenient symptom of it.") blocks Save — with it empty the button was greyed and the strip read **"Missing: the effect statement"**, then **"Missing: the effect statement, every cause's text"**. Dave's own problem sentence from step 4 was typed in there (it had to be retyped; nothing carried over from the charter).
2. Every cause must be filed under one of six headings — **People, Method, Machine, Material, Measurement, Environment**. The plan gives six causes with no headings, so each went under the heading its wording matches, recorded here: "Similar-looking cases stored beside each other" → **Environment**; "Old paper pick tickets are hard to read" → **Method**; "No scan confirmation before loading" → **Method**; "New employees are not familiar with look-alike items" → **People**; "Product slots are not clearly labeled" → **Environment**; "Picker is rushed near the end of the shift" → **People**.
All six were typed word for word and **Save worked** (≈3.1 s). Afterwards: **"Verified causes -- the Improve feed … No verified causes yet — Attach evidence and mark a cause verified once the data ties it to the baseline gap."**, a **Save new version** button, and **"! 2 checks worth a second look"** over a checklist: "At least 4 of the 6 branches explored / At least 6 causes on the board / No cause reads as an absent solution / Every verified cause has evidence / Ruled-out causes kept on the board". Each cause carries the flag **"no evidence yet"**.
**Shots:** `11-fishbone-survey-01-t15.png`, `12-fishbone-probe-01-one-cause-added.png`, `13-causes-01-effect-typed.png`, `13-causes-02-six-causes.png`, `13-causes-03-six-causes-full.png`, `13-causes-04-causes-saved.png`

## Step 16 — Mark three causes high and three medium

**Tried:** looked for a rating or priority control on the fishbone, and at the other ANALYZE tool.
**Expected:** a simple high/medium/low choice, then a ranked list or some visual showing the choices.
**Actual:** **The app never asked**, and offers no high/medium/low anywhere — those three words do not appear together on the screen. The only per-cause setting is **Status: Candidate / Investigating / Verified / Ruled out**, which is about how much is proven, not priority. The nearest rating machinery in the app is the neighbouring **T-16 FMEA (process)**: *"One row per specific failure of a specific process step. Rate severity, occurrence, and detection against the 1-10 anchor scales below -- a rating should match its anchor's wording, not a gut feel."* with a table Step | Failure mode | Effect | Cause | S | O | D | RPN | Action | Owner | Due | Status and a sort choice "Severity first / By RPN" — 1-to-10 numbers on process failure modes, not high/medium/low on the six causes, and nothing carries the six causes into it. So the three-high/three-medium marking was not done.
**Shots:** `13-causes-05-status-choice.png`, `14-report-01-t16-fmea.png`

## Step 17 — Find a report / dashboard / summary combining problem, goal, data and charts

**Tried:** read the rail and top bar for report-like things, then opened **T-25 A3 Final Report + Tollgate Checklists** under WRAP.
**Expected:** shows the number of records and at least one useful pattern; if only percentages, find out whether raw counts can be shown too.
**Actual:** The A3 page is the summary page: **"One argument, panel by panel -- problem, baseline, causes, countermeasures, proof, control. Not a field dump."** with eight panel tabs (Background, Current Condition, Goal / Target, Analysis, Countermeasures, Results / Realized Benefits, Follow-up / Control, Lessons Learned). Every panel was empty: **"Seeds from T-03 — ! Not seeded yet — Re-seed from its source artifact, or write the narrative by hand."** Its **Download the A3** button was greyed out, its Save was greyed out, and the strip read **"Missing: narrative or a seed for: background, current_condition, goal, analysis, countermeasures, results, follow_up_control, lessons"**. None of Dave's figures were on it: 487 — not on screen; 38,600 — not on screen; 6,800 — not on screen; "10 rows" — not on screen; Aisle — not on screen; "wrong item" — not on screen. (The words "picking" and "Picker" do appear on that screen, but only in the project title in the header and the tool rail.) Across the eleven screens reached in this run (start screen, T-01, T-03, T-08, T-11, T-13, T-14, T-15, T-16, T-25 and the "I'm stuck" panel), no screen showed the problem, the goal, the data and a chart together; the tool the app itself presents as that summary, T-25, was empty. Fifteen further tools in the rail were not opened.
**Shots:** `14-report-02-t25.png`, `14-report-03-t25-full.png`

## Step 18 — Export or save the result as PDF, image or spreadsheet, named `June picking error review`

**Tried:** every download the app offers: top-bar **Export project**; **Download the <phase> pack**; each tool's **Download report**; the charter's **Export PDF**; the A3's **Download the A3**.
**Expected:** something I could print or email to my warehouse manager without the manager needing the application.
**Actual:** Three files landed on disk (verified on disk, sizes below). **At no point was I asked what to call anything** — the app names the file itself — so nothing is called "June picking error review". Every export offered on the screens reached produced a PDF; no image or spreadsheet option appeared anywhere.
- **Export project** → `June-2026-warehouse-picking-errors-project-record.pdf`, 5,752 bytes, 3 pages. Titled "Full project record — every saved tool, in DMAIC order". It says **TOOLS SAVED: 1**, **PHASES COVERED: Analyze**, and contains only the fishbone: the six causes with branch/id/status, the effect statement, and "Verified causes COUNT 0". The imported dataset is not in it. The charts are not in it. Every page is stamped **"Working document — not certification evidence and not validation for regulated processes."**
- **Download the Analyze pack (1)** → `June-2026-warehouse-picking-errors-analyze-pack.pdf`, 6,475 bytes, 3 pages. Contains "T-15 Fishbone + 5 Whys — 6 cause(s) on the diagram, none verified yet — all still suspects", "T-16 FMEA — not done in this project", "T-17 Hypothesis Test — not done in this project", the six causes grouped by branch, and the line **"Chart not captured — open this tool's screen, then export again."**
- **T-15 Download report** → `June-2026-warehouse-picking-errors-T-15-report.pdf`, 130,337 bytes.
- **T-14 charts:** the words "Download report" appear **0 times** on the chart screen — the Pareto/histogram/run chart have no export of their own, and no chart image appeared in any of the three PDFs.
- **T-03 charter "Export PDF":** greyed out (the charter had never been saveable).
- **Download the Define / Measure / Improve / Control / Wrap pack:** all greyed out, each showing "(0)". Only "Download the Analyze pack (1)" was live.
**Shots:** `15-export-01-before-export.png`, `15-export-02-after-export-click.png`, `15-export-03-after-pack.png`, `16-export2-addrow-01-t14-no-export.png`, `16-export2-addrow-02-charter-export.png`

## Step 19 — Go back to the data table and add one more row by hand

**Tried:** returned to T-11 → Import Data and looked for a table and an add-row control; then checked the only other hand-entry screen, T-08.
**Expected:** add `2026-06-30, …, 106901, Green Valley Hospital, J. Morales, 12, Ketchup packets 4 oz, Ketchup packets 6 oz, wrong item, 1, 43.20, customer called again` and watch the charts or totals update.
**Actual:** **Not possible.** There is no table of the ten rows anywhere in the app and no way to type one in: *add row*, *new row*, *append*, *add record*, *edit row*, *table editor* appear nowhere on the screen. The only box on the data screen that accepts typing is the file picker. The screen's controls are: Override & proceed, Import Data, Collection Plan, Sample Size, Download report, + Add stratification factor, Save, Calculate. It does show **"Previously imported into this project: june_picking_errors_test.csv — 10 rows, saved 2026-08-12T14:16:48.574Z"**. The nearest hand-entry screen is **T-08 Check Sheet / Tally** (+ Add category, + Add stratification field, Live tally, Transcribe a paper tally, "Category 1 0", Save, Send to Pareto), which counts tally marks against categories and does not hold rows with twelve columns. To add that one complaint, a new CSV would have to be built outside the app and imported again.
**Shots:** `17-addrow-reopen-01-data-screen.png`, `16-export2-addrow-03-back-at-data.png`, `16-export2-addrow-04-back-at-data-full.png`, `17-addrow-reopen-02-t08-tally.png`

## Step 20 — Close the project, reopen it, and check the rows and charts are still there

**Tried:** clicked **← Projects**, read the start screen, clicked the project by name, then walked back through the data, the fishbone, the charter and the charts.
**Expected:** reopen "June 2026 warehouse picking errors" and still see the imported rows and whatever charts I made.
**Actual:** Closing is the **← Projects** link. The start screen now lists **"June 2026 warehouse picking errors"** with its path `/tmp/uat/roots/dave/june-2026-warehouse-picking-errors` and an **×** beside it, and the line "IN YOUR PROJECTS FOLDER — Everything on this machine is already listed above." Clicking the name reopened it in **≈4.1 s**. There was no separate save or backup action anywhere in the app; saving is per-tool.
- **Imported rows: kept.** "june_picking_errors_test.csv — 10 rows, saved 2026-08-12T14:16:48.574Z".
- **The six causes: kept**, all still on the fishbone.
- **The charter: lost.** The problem paragraph in What\* and the goal sentence in Goal statement\* were gone, the boxes empty — that screen never let me press Save.
- **The chart: not kept as a chart.** The Dataset drop-down on T-14 was empty again; the file has to be re-chosen and Category column re-set to Aisle to redraw it. Nothing in the app stores "the chart I made".
**Shots:** `17-addrow-reopen-03-back-at-start.png`, `17-addrow-reopen-04-back-at-start-full.png`, `17-addrow-reopen-05-reopened.png`, `17-addrow-reopen-06-reopen-data.png`, `17-addrow-reopen-07-reopen-fishbone.png`, `17-addrow-reopen-08-reopen-charter.png`, `17-addrow-reopen-09-reopen-charts.png`

---

# WHAT I COULD NOT DO

All 20 steps were attempted and reached an outcome. Six could not be carried out as the plan described them:

1. **Step 4 (partly) — no plain problem-statement box.** The charter breaks the problem into four required boxes (What / Where / When / Magnitude). The paragraph was typed into What\* and accepted, but it could not be stored: **Save stayed greyed out** behind eleven other missing values, and the text was gone at step 20.
2. **Step 7 — pasting rows into a table.** Not offered anywhere. The import screen accepts a file and nothing else.
3. **Step 12 (partly) — combining `JM`, `J. Morales`, `J Morales`.** No merge, rename or recode control exists on any screen reached. The three spellings stay three people, and the app's "vital few" headline names two of them.
4. **Step 14 — grouping by the item pair.** The Pareto accepts exactly one category column; there is no crosstab or second grouping. Two separate charts were run instead.
5. **Step 16 — rating the causes high/medium/low.** The app never asks, and offers no such rating. The only per-cause choice is Status (Candidate / Investigating / Verified / Ruled out).
6. **Step 19 — adding one row by hand.** No data table and no add-row control exists; the only route back into the data is uploading another file.

Also short of the plan's expectation, though the step itself completed:
- **Step 10** — the app confirms 10 rows and 1 missing aisle, but shows no record list, no distinct order-number count and **no money total**, so $671.15 could not be checked against anything.
- **Step 17** — the summary page exists but was empty; none of Dave's numbers appeared on it.
- **Step 18** — files exported, but the naming is automatic (nothing could be called "June picking error review"), the format is PDF only, and **no chart image is in any of them** ("Chart not captured — open this tool's screen, then export again").

**COULD NOT FIND ON SCREEN:** nothing. Every feature used in this run was found by reading the screen — the import under T-11's "Import Data" tab, the charts under T-14, the causes under T-15, the summary under T-25, the exports in the top bar and the rail. No feature was located by reading the source. The features the plan asked for and that were not found (paste-a-table, category merge, item-pair grouping, cause rating, add-a-row) were not found in the source either — they were simply not on any screen reached.

---

# THINGS THE SCREEN SAID

Wording, errors and numbers likely to be asked about, quoted exactly.

**On the first screen**
- "A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one."
- "Default location: ~/.sigma-ai/projects/project"

**Blocking messages**
- Charter Save, greyed: "Missing: problem statement: where, problem statement: when, goal metric name, goal unit, goal target date, scope: in-scope, scope: out-of-scope, process owner name, process owner role, business impact unit, business impact basis"
- On every tool outside Intake: "Define: Needs earlier steps (can override) — Missing: Project Picker (+ PDCA quick path routing). You can still work here, but proceeding needs a logged reason." / "Measure: Needs earlier steps (can override) — Missing: Project Charter, SIPOC, VoC → CTQ Tree."
- Fishbone Save, greyed: "Missing: the effect statement, every cause's text"
- A3 Save, greyed: "Missing: narrative or a seed for: background, current_condition, goal, analysis, countermeasures, results, follow_up_control, lessons"
- Help panel: "No stuck-tree for Intake yet — This phase's guided routing hasn't shipped yet."

**About the data**
- "Column types are inferred automatically. Confirm or change them below, review the quality scan, then save."
- "Quality scan found 1 issue across 10 rows" / "Aisle: 1 missing value" / "10 total rows scanned"
- "✓ Saved: 10 rows as dataset 04727612"
- "SHA-256 9d2c5177e5afe041940402d70bc611bd6bf8e81d2d76abdc20aa83196c9c0428 — the provenance anchor any baseline computed from this dataset links back to."
- "Previously imported into this project: june_picking_errors_test.csv — 10 rows, saved 2026-08-12T14:16:48.574Z"
- "This is not a data-cleaning tool: the scan finds problems, it never silently fixes them"

**Chart headlines (the app's own words)**
- Grouped by Complaint date (drawn before anything was chosen): "No small subset dominates — 10 categories are roughly even (10 total)"
- Grouped by **Aisle**: "No small subset dominates — 6 categories are roughly even (9 total)"  ← nine of the ten rows; the blank-aisle row is absent with no message
- Grouped by **Picker**: "Vital few: JM, AB, TK, J Morales account for 80.0% of 10"  ← "JM" and "J Morales" are the same man
- Grouped by **Error type**: "Vital few: wrong item, mispick account for 80.0% of 10"
- Grouped by **Item ordered**: "Vital few: Frozen chicken tenders 10 lb, Ketchup packets 4 oz, Low sodium soup, 12-inch flour tortillas, 5 oz burger patties account for 80.0% of 10"
- Grouped by **Item shipped**: "Vital few: Frozen chicken patties 10 lb, Ketchup packets 6 oz, Regular soup, 10-inch flour tortillas, 4 oz burger patties account for 80.0% of 10"
- Auto-drawn on opening: "n=10 · mean 105516.70 Order number · sd 642.91 Order number · median 105287.00 Order number"
- "Bars sorted by count; the line is cumulative share. Vital-few bars are highlighted to the 80% line."
- "EXIT-15: correlation and regression (a fitted line, an r value) are not computed in this version — deferred to v1.1. This plot is for visual inspection only."

**About causes**
- "Every cause needs an evidence pointer before it can be marked verified -- team consensus alone is not evidence."
- "A condition or mechanism ('labels applied before ink dries'), not an absent solution ('no barcode scanner')."
- "No verified causes yet — Attach evidence and mark a cause verified once the data ties it to the baseline gap."
- "! 2 checks worth a second look"
- In the exported pack: "A fishbone is a list of suspects, not a list of causes. … Nothing here is verified yet, so all 6 entries are still suspects. Fixing one now is a guess with a diagram behind it." and "3 branch(es) empty: Machine, Material, Measurement."

**In the exported PDFs**
- "Working document — not certification evidence and not validation for regulated processes." (every page)
- "Full project record — every saved tool, in DMAIC order" / "TOOLS SAVED 1" / "PHASES COVERED Analyze"
- "Chart not captured — open this tool's screen, then export again."

**Unexplained words met along the way** (no definition offered on the screen where they appear): Green Belt, DMAIC, PDCA quick path, EXIT-01, EXIT-15, SIPOC, VoC → CTQ Tree, COPQ, MSA, Gage R&R, FPY/RTY/DPMO, RPN, 6M, A3, tollgate, guardrail metric, stratification factor, provenance anchor, SHA-256.
