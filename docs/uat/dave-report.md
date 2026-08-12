# Dave Mercer — evening ops supervisor, food-service warehouse

Written in persona, from this tester's own screenshots and run log — 20 planned steps, driven for real on 2026-08-12. Not edited. See `README.md` for the method and the triage.

---

## openai · `gpt-5.6-luna`
*tokens: 81177 in / 9126 out*

# What I thought after actually trying it

I went into this with a very specific job in mind: take a messy but real-looking set of picking complaints, get it into the software without typing 487 rows, see whether the errors cluster by aisle, picker, error type, or item pair, write down some possible causes, and come out with something I could show my warehouse manager.

The first part was straightforward. The middle part was partly useful. The last part — getting a saved, manager-ready answer out of it — did not happen.

The application did not crash, throw browser errors, or lose the project completely. It did save the uploaded dataset and the fishbone causes. That is worth saying. But it also made me work around its structure almost immediately, and the two things I most needed to keep — the charter and the chart setup — were not still there when I reopened the project.

## Opening it and starting the project

The first screen was clean and easy enough to understand at a basic level. It said **“Sigma AI”**, and underneath:

> “A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one.”

There were two cards: **“Start a new project”** and **“Open a project.”** The first one had **“Project name*,” “Project folder (ID),”** and **“Create project.”** The second said:

> “No recent projects yet on this machine.”

and

> “IN YOUR PROJECTS FOLDER — No projects in your projects folder yet.”

That is all visible in `01-first-open-01-cold-start.png` and `01-first-open-02-cold-start-full.png`.

The basic layout was not a problem. I could see where to start, and there was no example project cluttering things up. I specifically did not want to be forced into some coffee shop example, and it did not do that.

The problem was the opening sentence. I do not know what **“Green Belt”** means in practical terms, and I do not know what **“DMAIC”** means without having somebody explain it. The screen also used **“Project folder (ID)”**, which sounds like a technical field, not something I would expect to fill in as an operations supervisor. It was pre-filled with `project`, along with:

> “Default location: ~/.sigma-ai/projects/project”

I understand now that it is just the project’s folder name, but the screen did not say that in plain English. I would rather see “Project file name” or “Project ID — leave this alone unless you need a different folder.”

I clicked **Create project** before entering a name and it was disabled, as shown in `02-create-project-01-before-typing.png`. That behavior was fine. It was obvious enough that the missing required project name was the reason.

I typed exactly:

> `June 2026 warehouse picking errors`

The folder ID changed itself to:

> `june-2026-warehouse-picking-errors`

That was good. I did not have to figure out how to make a folder-safe name. I clicked Create project, waited about three seconds, and landed in **“T-01 Project Picker (+ PDCA quick path routing)”**. The full page is in `02-create-project-03-after-create.png` and `02-create-project-04-after-create-full.png`.

This was not the blank project screen I expected. It immediately wanted five Yes/No answers:

- “Is the scope narrow enough to actually finish?”
- “Is there a measurable outcome?”
- “Can you actually get the data?”
- “Does a process owner care about this?”
- “Is the business impact plausible?”

Each one also had a box saying:

> “One line: what makes this true?”

Then it wanted a required route: **Full DMAIC**, **PDCA quick path**, or **Not a good fit (EXIT-01)**.

I can see what the software is trying to do. It is trying to stop somebody from starting an enormous, vague project and calling it improvement. That part is sensible. The explanations on the right were also much better than the label at the top. For example, under the data question it said:

> “Name the real source — a log, a system export, a form.”

That is clear. It also gave examples of a good named owner and a rough business impact. I understood the questions once I read the long help panel.

But this is too much ceremony before I can even write down what the problem is. I was sitting there with a project title, but no place to enter the actual problem or the numbers. The first thing I had to do was answer a project-screening questionnaire built around a method I had never heard of in detail.

The button at the bottom, **“I'm stuck — what do I use now?”**, did not help. It opened a panel saying:

> “An offline routing tree for the Intake phase — a couple of plain questions, no AI involved.”

Then:

> “No stuck-tree for Intake yet — This phase's guided routing hasn't shipped yet.”

That is not useful help. If the help button says the routing tree has not shipped, then it is basically admitting the help button does not work yet. The software did at least tell me honestly what was happening. I will give it that.

## Trying to enter the problem and goal

There was no problem box on the screen I landed on. I had to read the left-hand rail and guess that **T-03 Project Charter** was where the problem belonged. The rail described it as:

> “Problem, goal, scope, and who it matters to.”

That was enough to find it, but I should not have had to hunt for it. `03b-problem-goal-01-charter-problem-section.png` shows the charter screen.

The charter did not have one plain problem statement field. Under **“Problem statement”** it had four separate required fields:

- **What\***
- **Where\***
- **When\***
- **Magnitude\***

The note underneath said:

> “What's wrong, where, when, and how much -- no causes, no solutions.”

That explanation is actually good. I understand why those pieces might matter. But it did not match what I had been asked to do. I had a plain English problem statement ready:

> “Restaurant and school orders are receiving wrong items after picking. We had 487 reported errors on 38,600 order lines in June 2026, costing about $6,800 in credits and redeliveries.”

There was no obvious place for that whole sentence. I put it into **What\***, exactly as written. It accepted it character for character, which was good, but it was clearly not the right shape for the field. I still had to separately fill in where, when, magnitude, scope, owner, team, and so on.

The screenshot `03b-problem-goal-02-typed-problem-into-what.png` makes the problem clear: a long paragraph is sitting in a field whose purpose is supposed to be just “What.” The field is not even wide enough to show the whole sentence without scrolling sideways.

For the goal, I typed exactly:

> “Reduce reported wrong-item errors from 1.26% of order lines to below 0.5% by September 30, 2026.”

The goal box accepted the sentence exactly. That part worked. It also gave me separate fields for **Metric name**, **Baseline**, **Target**, **Unit**, and **Target date**, which is the right idea. The screenshot `03b-problem-goal-03-typed-goal.png` shows that setup.

The problem was that the separate fields were not optional. The **Target** field was pre-filled with `0`, while the others were blank. I understand that the software wants a structured metric, but it did not use the sentence I had already entered to fill anything in. It made me enter the same meaning again in a different format.

When I tried to save, the button stayed grey. There was no tooltip explaining what I needed to do. The yellow message at the bottom said:

> “Missing: problem statement: where, problem statement: when, goal metric name, goal unit, goal target date, scope: in-scope, scope: out-of-scope, process owner name, process owner role, business impact unit, business impact basis”

That is a lot of missing fields for somebody who only wanted to write down the problem and goal. The full screen after typing is in `03b-problem-goal-04-charter-filled-full.png`, and the disabled Save button is in `03b-problem-goal-05-save-disabled.png`.

This is where the software started working against me. It did not just say “you need a few more details.” It dumped a list of internal field names at me:

- “business impact unit”
- “business impact basis”
- “scope: in-scope”
- “process owner role”

I know what most of those mean after reading the help text. A normal supervisor should not have to decode them from a disabled Save button.

The charter help itself was one of the better parts of the application. It gave examples like:

> “Line 2 scrap rate averaged 6.2% in Q2, costing ~$40k.”

and explained that the magnitude needs a number, a unit, and a period. It also said:

> “A real, named person -- not a placeholder like TBD or management.”

That is plain enough and operationally sensible. The trouble is that the help is long, and the actual form does not make a reasonable first pass possible. I could have filled every field if I had spent another half hour inventing a team list, process owner role, milestones, guardrail metrics, and business-impact basis. But that was not the job I was trying to do in this test.

I eventually left the charter unsaved and moved on. That mattered later: when I reopened the project, all the text I had typed into the charter was gone. More on that below.

## Finding the data import

I was worried this would be the deal breaker because I have 487 complaint rows and will not manually type them into a tool. The application did have a CSV/XLSX import, but it was not where I expected it.

It was inside **T-11 Data Collection Plan (+ sample-size guidance)**, under a tab called **Import Data**. `05-import-csv-01-import-tab.png` shows the screen before uploading. It said:

> “Data Collection Plan — import a dataset”

and:

> “Upload a CSV or XLSX file”

with:

> “Column types are inferred automatically. Confirm or change them below, review the quality scan, then save.”

Once I found it, the actual file upload worked. I gave it `june_picking_errors_test.csv`, containing the ten sample rows with the messy dates and inconsistent picker names untouched. It processed the file in about four seconds.

That is an important positive. I did not have to clean up the dates before the software would accept the file. It did not demand that I rename all the employees first. It did not reject the blank aisle. For a real warehouse spreadsheet, that is much better than software that refuses to do anything until every cell is perfect.

It correctly read the first row as column headings and displayed the twelve columns with inferred types and sample values. It inferred:

- Complaint date: text
- Delivery date: text
- Order number: numeric
- Customer: text
- Picker: text
- Aisle: numeric
- Item ordered: text
- Item shipped: text
- Error type: text
- Quantity: numeric
- Credit amount: numeric
- Notes: text

The import screen is shown in `05-import-csv-03-after-upload.png` and `05-import-csv-04-after-upload-full.png`.

The app did not offer a paste box or an editable table. I looked for somewhere to paste the ten rows directly and found nothing. The only option was the file picker. That is not a serious problem for my actual 487-row file because I already have a spreadsheet, but it would be useful for testing or quickly adding a few records.

The type choices were also very limited. Every column dropdown offered only:

- **numeric**
- **text**

There was no “category,” “group,” or anything similar. I changed Aisle from numeric to text because I wanted it treated as a grouping field. That worked as a workaround, but it is not obvious that changing a numeric-looking aisle to text is the right thing to do.

The quality scan was probably the clearest part of this screen. It said:

> “Quality scan found 1 issue across 10 rows”

and:

> “Aisle: 1 missing value”

and:

> “10 total rows scanned”

That is shown in `06-types-preview-02-quality-scan.png`.

It did not complain about the mixed date formats because it treated both date columns as text. For my immediate purpose, that was fine. It also did not silently change anything, which is good. The help text explicitly said:

> “This is not a data-cleaning tool: the scan finds problems, it never silently fixes them”

That is a fair warning. I would rather know that the software left my data alone than have it quietly change dates or employee names.

The app then saved the upload and gave it a dataset ID:

> “✓ Saved: 10 rows as dataset 04727612”

It also displayed a long SHA-256 value and called it:

> “the provenance anchor any baseline computed from this dataset links back to.”

The saved result is in `06-types-preview-04-dataset-saved.png` and `06-types-preview-05-dataset-saved-full.png`.

I do not know what a **provenance anchor** is. I understand the general idea that the software is tying later results to the exact file used, but the screen could say that instead. The SHA-256 number is not useful to me unless somebody later asks whether the file changed. I would rather see “This keeps a fingerprint of the uploaded file so later charts can be tied back to it.” The current wording sounds like something from a software audit.

The import did not show the actual ten records. It only showed five sample values per column. It confirmed ten rows and one missing aisle, but it did not show:

- a table of the ten complaints,
- a distinct order-number count,
- the total credit amount,
- any row-level preview.

I knew the credit amounts totaled $671.15 from the file, but the application never displayed `$671.15`, so I could not verify whether it had added the money correctly. That is a missed opportunity. A simple summary line saying “10 rows, 10 order numbers, 1 missing aisle, $671.15 credit total” would have made this screen much more useful.

## Trying to find patterns in aisles, pickers, error types, and items

The chart tool was **T-14 Pareto / Histogram / Run Chart**, which I found from the left rail. It actually draws several charts at once: histogram, run chart, Pareto, scatter, and box plot. The tool screen is shown in `08-pareto-aisle-01-dataset-picked.png`.

The first thing it did when I selected the dataset was draw a histogram of **Order number**, with:

> “n=10 · mean 105516.70 Order number · sd 642.91 Order number · median 105287.00 Order number”

I understand `n=10` means ten records. I do not understand `sd` without looking it up. The chart also automatically chose Complaint date for the first Pareto, producing a time axis with labels like:

> “23:59:59.9996Jun 3, 2026”

That is just broken-looking from my point of view. The date values were imported as text, and the chart tried to plot them in a way that produced meaningless timestamp labels. It did not explain why it chose Complaint date, and it did not ask me what I wanted to look at first.

For the aisle analysis, I selected **Aisle** as the Category column. The app said:

> “No small subset dominates — 6 categories are roughly even (9 total)”

The actual bars were 2, 2, 2, 1, 1, 1, which matches the ten sample rows after excluding the blank aisle. The problem is that the chart did not print the aisle values under the bars. It only showed a number line with 5, 10, 15, and 20. The screenshot `09-group-by-02-pareto-aisle.png` shows what I mean.

I could see six bars, but I could not reliably tell which bar represented aisle 3, 7, 12, 14, 19, or 22. So the software technically plotted the data, but it did not answer my question. I wanted to be able to say, “Aisles 3, 7, and 12 are at the top.” Instead I got a chart where I had to guess from the bar positions.

Also, the app silently left the blank aisle out of the chart. It said there were nine total records in the Pareto, but it did not clearly say, “One row has a blank Aisle and was excluded.” I noticed the mismatch because I knew there were ten rows. Any chart that drops records needs to say so plainly.

There was no separate measure choice. I wanted “count of complaints,” and the chart did count rows, but the application did not ask me that. It just assumed the Pareto should count records. That is fine for this particular chart, but it leaves me wondering whether another chart might be summing quantity or credit amount without my noticing.

The picker chart was more revealing, although it also exposed the data-cleaning problem. It showed:

- JM: 3
- AB: 2
- TK: 2
- J Morales: 1
- J. Morales: 1
- RL: 1

The headline said:

> “Vital few: JM, AB, TK, J Morales account for 80.0% of 10”

That is not a useful statement about picker performance because **JM, J Morales, and J. Morales are the same person** in my source data. The chart is treating them as three people. It even calls “J Morales” one of the “vital few,” while leaving “J. Morales” as a separate person. The screenshot `09-group-by-04-pareto-picker.png` shows the separate bars.

This was exactly the sort of problem I wanted to test. Unfortunately, there was no way to combine, rename, merge, recode, or edit category values. I searched the screen for those options and found nothing. The application did not warn me that inconsistent names could make a picker comparison misleading.

That is a serious issue for real use. If I put the full June file in as-is, I could easily get a chart implying that one employee has fewer complaints than another simply because his name was entered with initials on some rows and a full name on others. I already know the labor report has its own name inconsistencies. I need the software to help me clean that up or at least make the limitation impossible to miss.

The error-type chart was straightforward. It showed:

- wrong item: 6
- mispick: 2
- substitution: 2

The headline said:

> “Vital few: wrong item, mispick account for 80.0% of 10”

That is technically what the file says, and the separate bars were useful. But again, it gave no warning that “wrong item,” “mispick,” and “substitution” may overlap or be different ways people describe the same thing. In my operation they are not consistently defined. The application simply treated them as three categories. The screenshot is `09-group-by-05-pareto-errortype.png`.

That means I got a count of labels, not necessarily a count of consistently defined error types. I would need to clean the source spreadsheet first.

The item analysis was the closest thing to a useful answer. I could not group by the combination of Item ordered and Item shipped. The Pareto only accepted one category column. There was no pair option, crosstab, combination field, or second text grouping.

I ran one chart by **Item ordered** and another by **Item shipped**. The ordered chart showed the ketchup and chicken items at count 2, and the shipped chart showed the corresponding wrong items at count 2. Those are in `10-item-pairs-01-pareto-item-ordered.png` and `10-item-pairs-02-pareto-item-shipped.png`.

I could infer that:

- Ketchup packets 4 oz → Ketchup packets 6 oz happened twice.
- Frozen chicken tenders 10 lb → Frozen chicken patties 10 lb happened twice.

But I had to match the two separate charts by eye. That is not good enough for 487 complaints with many similar products. The whole point of the item-pair question is that the ordered item and shipped item belong together on the same row. The software has both columns and still cannot analyze them together.

The chart screen also used phrases I would not normally use:

- “No small subset dominates”
- “Vital few”
- “cumulative share”
- “80% line”
- “Histogram”
- “Run Chart”
- “Box Plot”
- “Scatter”
- “USL”
- “LSL”

Some of those were explained in the help panel. For example, it explained that a Pareto is used to find which few categories carry most of the pain. That was helpful. But the headline still sounds like software talking to itself. I would understand “No aisle accounts for most reported errors” more quickly than “No small subset dominates.”

The app also displayed:

> “EXIT-15: correlation and regression (a fitted line, an r value) are not computed in this version — deferred to v1.1. This plot is for visual inspection only.”

I appreciate that it did not pretend to calculate a correlation it did not have. That is a good limitation to state. But **EXIT-15** is another internal code that means nothing to me. It should say “This version does not calculate correlation or regression. The scatter plot is only for visual inspection.”

## Entering possible causes

The fishbone was under **T-15 Fishbone (6M) + 5 Whys**. That was easy enough to locate once I understood the rail. The screen said:

> “Click a branch to add a candidate cause. Every cause needs an evidence pointer before it can be marked verified -- team consensus alone is not evidence.”

That is one of the strongest parts of the application. I agree completely that a group sitting around and agreeing that “people need to pay more attention” is not proof. The warning that causes are only candidates until tied to evidence is useful.

It did require an **Effect statement\*** before it would save. My original problem text was not carried over from the unsaved charter, so I had to type it again. The effect statement was supposed to be:

> “The baselined problem -- the measured gap, not a convenient symptom of it.”

That is a fair rule, although I could not give it a baselined gap because I had only imported ten complaint rows, not the full 38,600 order-line denominator. I used the problem sentence anyway.

The fishbone required every cause to be put under one of six branches:

- People
- Method
- Machine
- Material
- Measurement
- Environment

I put the six proposed causes where they seemed to fit:

- **Environment:** Similar-looking cases stored beside each other
- **Method:** Old paper pick tickets are hard to read
- **Method:** No scan confirmation before loading
- **People:** New employees are not familiar with look-alike items
- **Environment:** Product slots are not clearly labeled
- **People:** Picker is rushed near the end of the shift

The application saved all six. That was good. It preserved the wording and showed **“no evidence yet”** beside every cause. The saved fishbone is shown in `13-causes-04-causes-saved.png`.

It also gave me a warning:

> “No verified causes yet — Attach evidence and mark a cause verified once the data ties it to the baseline gap.”

That is fair. I was not expecting ten sample rows to prove a root cause.

The problem was step 16. I wanted to mark three causes high priority and three medium priority. The fishbone had no high/medium/low priority control. The only status choices were:

- Candidate
- Investigating
- Verified
- Ruled out

Those are not priority ratings. They describe how much evidence there is. I understand the distinction, and in fact I prefer not mixing priority and proof together, but the application gave me no alternative way to record which causes I wanted to investigate first.

The nearby FMEA tool had severity, occurrence, detection, and RPN ratings from 1 to 10. It explained:

> “Rate severity, occurrence, and detection against the 1-10 anchor scales below -- a rating should match its anchor's wording, not a gut feel.”

That is too much machinery for the simple question I was trying to answer, and it was not connected to the fishbone causes. I could have made six process failure rows from scratch, but that would be a different exercise.

One thing I liked about the fishbone was that it did not let me mark **“No scan confirmation before loading”** as verified just because it sounded plausible. The screen also warned that a cause should be a condition or mechanism, not an absent solution:

> “A condition or mechanism ('labels applied before ink dries'), not an absent solution ('no barcode scanner').”

That wording is a little too academic, but the underlying point is good. “No scan confirmation” is really a missing control, not necessarily the cause of every wrong item. The tool was right not to present it as proven.

After saving, it showed:

> “2 checks worth a second look”

and listed checks including:

- “At least 4 of the 6 branches explored”
- “At least 6 causes on the board”
- “No cause reads as an absent solution”
- “Every verified cause has evidence”
- “Ruled-out causes kept on the board”

That gave me a useful reminder that I had only made a list of suspects. It did not give me a cause answer, which is appropriate based on the data I provided.

## Trying to make a report

This is where the application fell down for my actual job.

The obvious summary tool was **T-25 A3 Final Report + Tollgate Checklists**. It described itself as:

> “One argument, panel by panel -- problem, baseline, causes, countermeasures, proof, control. Not a field dump.”

That sounds exactly like what I wanted. But every panel was empty. It said:

> “Not seeded yet”

and:

> “Re-seed from its source artifact, or write the narrative by hand.”

The Save button was greyed out, and the missing message said:

> “Missing: narrative or a seed for: background, current_condition, goal, analysis, countermeasures, results, follow_up_control, lessons”

The screen did not show any of my numbers:

- 487 reported errors: not shown
- 38,600 order lines: not shown
- $6,800: not shown
- 10 imported rows: not shown
- Aisle: not shown
- wrong item: not shown

The A3 screen is in `14-report-02-t25.png` and `14-report-03-t25-full.png`.

I could have manually copied all of that into the A3 panels, but then the software would just be a blank form I was filling out myself. It did not pull the saved dataset into the report, did not pull the chart analysis into the report, and did not pull the fishbone into the analysis panel.

It also did not show a manager-ready dashboard anywhere else. The project rail had a lot of tools, but not one page that gave me:

- the problem,
- the target,
- the number of records,
- the main patterns,
- the possible causes,
- and the next action.

That is the page I needed.

## Exporting something

The application did create PDFs. I tried the top-bar **Export project**, the Analyze pack, and the fishbone report. The files saved were:

- `June-2026-warehouse-picking-errors-project-record.pdf`
- `June-2026-warehouse-picking-errors-analyze-pack.pdf`
- `June-2026-warehouse-picking-errors-T-15-report.pdf`

The export screenshots are `15-export-01-before-export.png`, `15-export-02-after-export-click.png`, and `15-export-03-after-pack.png`.

It never asked me to name the file `June picking error review`. It named everything automatically. I do not care deeply about the exact filename, but I do care that I could not choose a name I could recognize and email to my manager.

More importantly, the project record PDF had:

> “TOOLS SAVED: 1”

and:

> “PHASES COVERED: Analyze”

It contained the fishbone causes, but not the imported dataset, not the charts, and not the analysis I had just done. The Analyze pack included the fishbone and said:

> “Chart not captured — open this tool's screen, then export again.”

That is a pretty serious failure in an export process. If I am exporting a project report, I should not have to reopen a chart and export again just so the chart can be captured.

The chart screen itself had no **Download report** button at all, as shown in `16-export2-addrow-01-t14-no-export.png`. The charter had an **Export PDF** button, but it was disabled because the charter was never saved, as shown in `16-export2-addrow-02-charter-export.png`.

Every exported page also had this stamp:

> “Working document — not certification evidence and not validation for regulated processes.”

I cannot tell whether that warning is required for some intended use of the application. From my side, it makes the report feel like a draft even when the information is correct. I would not want that warning on a simple warehouse manager review unless there were a way to turn it off for ordinary internal use.

## Adding one more complaint and reopening

I could not add the extra June 30 complaint by hand. The data screen had no table of the ten rows and no controls named:

- add row,
- new row,
- append,
- add record,
- edit row,
- table editor.

The only input that accepted anything was the file picker. The screen is shown in `17-addrow-reopen-01-data-screen.png` and `16-export2-addrow-03-back-at-data.png`.

The only hand-entry tool I found was T-08 **Check Sheet / Tally**, shown in `17-addrow-reopen-02-t08-tally.png`. That tool lets you set categories and tap tally marks. It is not a twelve-column complaint table. I could not use it to add the new complaint with its order number, picker, aisle, ordered item, shipped item, credit amount, and notes.

So if one more complaint comes in tomorrow, I have to edit the CSV outside the software and upload the whole thing again. That is not the end of the world, but it is clumsy and it means I cannot quickly update a chart while sitting in a meeting.

The project itself did reopen. That part worked. After clicking **← Projects**, the start screen listed:

> “June 2026 warehouse picking errors”

with the project path. The reopened project is shown in `17-addrow-reopen-03-back-at-start.png`, and the project screen is in `17-addrow-reopen-05-reopened.png`.

The imported dataset was still there:

> “june_picking_errors_test.csv — 10 rows, saved 2026-08-12T14:16:48.574Z”

The six fishbone causes were still there too. That is a real positive. Saved artifacts did survive closing and reopening.

The charter did not survive because it had never been saved. The problem paragraph and goal sentence were gone, as shown in `17-addrow-reopen-08-reopen-charter.png`. I understand that I had not completed all the required fields, but the application should either preserve a draft or warn me very clearly before I leave that the text will be lost. The top bar kept saying:

> “No changes yet”

even after I typed a problem and goal. That wording was misleading. There were changes on the screen; they simply were not saved.

The chart setup also did not survive. When I reopened T-14, the Dataset field was empty again, as shown in `17-addrow-reopen-09-reopen-charts.png`. I had to choose the file and choose Aisle again. The app saved the dataset, but it did not save the analysis view.

## Did I get closer to the actual warehouse problem?

A little, but not enough.

From the ten rows, I could see that the same kinds of look-alike items showed up repeatedly:

- ketchup packets, 4 oz ordered versus 6 oz shipped,
- chicken tenders versus chicken patties,
- soups,
- tortillas,
- similar-looking cases.

The item charts also showed repeated counts for the ketchup and chicken products, even though I had to compare separate ordered and shipped charts to see it. The error-type chart showed six rows labeled “wrong item,” two “mispick,” and two “substitution.” The fishbone let me record plausible causes without pretending they were proven.

Those are useful observations. If I were standing in the warehouse Monday morning, I would be justified in checking the storage locations and labels for those look-alike products. I could also ask the inventory clerk to standardize the picker names and error-type labels before we make claims about individual performance.

But I could not honestly tell my manager:

- which aisles account for the most errors,
- which picker has the highest error rate,
- which item pairs are the biggest repeat problem,
- whether those patterns hold across all 487 complaints,
- or what the error rate is by person after accounting for the number of lines picked.

The software never used the separate labor report, so it could not calculate picker error rates. It counted complaints by name only. That would be dangerous to show as a performance comparison.

It also did not use the 38,600 order-line denominator. The imported test file had ten complaints, but the application never calculated the 10-row complaint rate or connected the test data to the real June rate of 1.26%. I still had no baseline chart I could show.

The fishbone causes were useful as a list of things to investigate, but none had evidence attached. The software was right about that. I did not learn that a scan check, storage layout, labels, paper tickets, or new hires caused the problem. I only learned that the application would let me write those suspicions down.

## What was genuinely good

There were some solid pieces.

The project creation was quick. Typing the project name automatically created a usable folder ID. No example project was forced on me.

The CSV import worked with the messy sample data. It accepted mixed date formats, different picker-name styles, and one missing aisle. It did not silently clean the file. It showed the exact quality finding:

> “Aisle: 1 missing value”

and confirmed:

> “10 total rows scanned.”

That is better than many systems that either reject messy data or quietly make changes.

The app also kept a saved dataset tied to the uploaded file. The message:

> “Saved: 10 rows as dataset 04727612”

and the file fingerprint show that the software is trying to keep results traceable to a particular upload. I do not need the SHA-256 terminology in front of me, but keeping track of the source file is a good idea.

The Pareto tool did count categories correctly for the sample. The picker problem was caused by bad names in the source, not by the chart miscounting them. The error-type counts were also displayed clearly enough once I got to the chart.

The fishbone was better than a blank “root cause” text box. It forced causes into branches, kept them marked as candidates, and did not let me call anything verified without evidence. The line:

> “No verified causes yet — Attach evidence and mark a cause verified once the data ties it to the baseline gap.”

is exactly the kind of restraint I want in a tool. I do not want software giving me a fake answer based on ten complaints.

The application also behaved consistently in the run. The log reports no page errors, console errors, or server errors. The delays were a few seconds, but nothing crashed. The project, dataset, and fishbone did come back after reopening.

## Would I open it again?

I would open it again to use the CSV import and maybe the fishbone.

I would not put my full June data into it yet if I expected to use the results for a manager discussion. I would first clean the picker names and error types outside the app, because I cannot fix those categories inside it. I would also have to create an item-pair column outside the app, something like:

`Ketchup packets 4 oz -> Ketchup packets 6 oz`

Then I could import that new column and group by it. That is a workaround, not a good workflow.

I would not tell another supervisor, “This will give you a useful report,” because it did not give me one. I might tell somebody, “This has a decent structured fishbone and it can import a CSV,” but I would warn them that the charts are hard to read, categories cannot be cleaned up, and the report does not pull the work together.

I would not spend an afternoon completing all the DMAIC fields unless I knew the save problem had been fixed. Losing the charter text after reopening is the kind of thing that makes people stop trusting a tool.

## The changes that matter most to me

If I could get four things changed before using this for real, I would want them in this order.

### 1. Make the data usable without leaving the application

This is the biggest one.

I need to be able to:

- view the actual imported rows,
- add or edit one row,
- standardize values such as `JM`, `J Morales`, and `J. Morales`,
- combine or rename categories,
- create a combined field from two columns, especially Item ordered plus Item shipped,
- see counts and sums such as total credit amount.

For my job, the most important missing feature is the item-pair grouping. The application already has both columns. It should let me choose **Ordered item + Shipped item** as a pair and show:

> `Ketchup packets 4 oz → Ketchup packets 6 oz: 2 complaints`

The picker cleanup is just as important. If it cannot automatically tell that those three names are probably the same person, it should at least let me select the three values and rename them to one standard value.

Without that, the charts can produce a clean-looking answer that is wrong for operational reasons.

### 2. Give me a plain summary page that actually uses the saved work

The A3 report needs to pull from the project instead of opening as eight empty boxes.

After importing the dataset and running a chart, I should be able to open one page and see:

- the problem statement,
- the June baseline,
- 487 reported errors,
- 38,600 order lines,
- the 1.26% rate,
- the target of below 0.5%,
- the number of imported complaint rows,
- top aisles,
- top picker names after cleanup,
- top item pairs,
- error-type counts,
- possible causes,
- and an obvious note saying what needs to be checked next.

I do not need a fancy dashboard. I need one page I can put on a desk and talk through in ten minutes.

The current A3 says:

> “Not seeded yet — Re-seed from its source artifact, or write the narrative by hand.”

That means the software has not done the basic job of connecting its own tools. If I have already typed the data and made the charts, I should not have to type all the same facts into another screen.

### 3. Make saving and drafts safe

The charter should either save a draft automatically or make the loss impossible to miss.

It is not acceptable that I type a problem statement and goal, navigate away, and later find both gone. The top bar saying **“No changes yet”** after I typed them made it worse. I need one of these:

- automatic draft saving,
- a working Save draft button,
- or a warning saying, “You have unsaved text. Leaving now will discard it.”

The same applies to chart selections. If I choose a dataset and group by Aisle, that view should be stored in the project or there should be a clear **Save analysis** button. Having to reselect the dataset and category every time is wasted time.

### 4. Replace the method language with plain workplace language, or explain it where it appears

I do not need the application to remove all its structure, but it needs to stop making me translate its vocabulary.

Words that lost me or were not explained where I first saw them included:

- Green Belt
- DMAIC
- PDCA quick path
- EXIT-01
- SIPOC
- VoC → CTQ Tree
- COPQ
- MSA
- Gage R&R
- FPY/RTY/DPMO
- RPN
- 6M
- A3
- tollgate
- guardrail metric
- stratification factor
- provenance anchor
- SHA-256

The long **“How this tool works”** panels did explain some of them eventually, and I appreciated the examples. But a supervisor should not have to open a training essay to understand why a button is disabled. “Missing: process owner name, role, and business impact basis” is clearer than a list of internal validation terms, but even that should be paired with a direct link or short instruction.

I would also change the chart wording. Instead of:

> “No small subset dominates”

say:

> “No single aisle accounts for most complaints.”

Instead of:

> “Vital few: JM, AB, TK, J Morales account for 80.0% of 10”

say:

> “These names account for 8 of 10 complaints. Check for duplicate employee names before comparing people.”

That last sentence would have caught the exact problem I found.

So, bluntly: I did not waste the entire afternoon. The import worked, the quality scan was useful, the fishbone was sensible, and the software did not pretend ten rows proved a root cause. But I did not get a reliable answer to my warehouse problem, and I did not get a report I could show my manager. Right now I would use it as a rough worksheet alongside Excel, not as the place where I would keep the actual improvement project.

