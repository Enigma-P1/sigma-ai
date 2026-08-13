# Changelog

## v0.2.0 — unreleased

Everything below traces to two operations supervisors with no Six Sigma
training using the app on their own messy spreadsheets, and saying what
happened. Their verbatim reports, the run logs, and the method that
produced them are in [`docs/uat/`](docs/uat/) — including the parts that
did not go well.

### The thing that was most wrong

**The app never showed you your own rows.** It read your file, hashed it,
tallied it, charted it, and refused to display it. One tester could not
check whether his file's credit amounts had imported correctly, because no
rows and no total were ever on screen. There is now a paged rows view with
per-column totals — and a note saying which totals mean anything, because
summing an order-number column produces a real number that is not a fact.

### You can fix your own data now

- **Recode** several spellings of a value into one. One tester's Pareto
  named `JM` and `J Morales` as two separate members of the "vital few".
  They were the same man, and the chart looked clean.
- **Edit a cell, add a row, delete rows.** Both testers tried to correct
  one record and could not; the only route was rebuilding the file in
  Excel and re-importing.
- **Derive a column** by joining two others, which answers "which item got
  swapped for which" without a crosstab.
- Every one of these creates a **new dataset version** with its own
  fingerprint and a link to its parent. Nothing is edited in place, so a
  chart you made last week still resolves to the exact bytes it was
  computed from.

### The quality scan catches what silently broke both runs

A header row pasted into the middle of a spreadsheet (it was importing as
data and becoming a category), values that differ only in case,
punctuation or spacing, and more than one date format in a single column.
Each finding points at the tool that fixes it. It reports; it never
silently changes your data.

### Charts

- The Pareto axis is **categorical**. Part numbers and aisle numbers used
  to plot on a numeric scale — no bar carried a label and the cumulative
  line zigzagged. The chart a supervisor would email was unreadable.
- **Download this chart as a picture**, with a real filename.
- **Filter** to a subset — one shift, one picker — with the row count
  always on screen, because a chart quietly drawn over part of the data is
  a claim waiting to be misquoted.
- The screen **remembers** your dataset and column choices.
- Headlines name your own column: *"Aisle: 3 of 6 carry 80% of 9 rows"*
  rather than *"No small subset dominates"*.
- Histogram and run chart now say a dataset has no numeric column instead
  of waiting forever on statistics that were never requested.

### Your typing survives

Drafts autosave on the charter, the A3 and the FMEA, and come back after
you navigate away or close the app. One tester typed the two sentences he
came to write, clicked away, and lost both — Save sat behind eleven other
required fields he had not filled in. **Drafts are not artifacts**: they
never count towards a tool being done, so "saved" still means what it
meant.

### Plain English

- The first screen no longer opens with *"A guided Green Belt DMAIC
  flow."* Neither tester knew what either term meant.
- **A glossary** of 28 terms, reachable from every screen, written for a
  supervisor rather than a Black Belt.
- A **data-first path**: import a file and chart it without passing
  through the project-screening questions.
- The Intake help button no longer answers that the help has not shipped.

### Housekeeping

- **Delete a project**, behind a typed confirmation that distinguishes it
  from the "forget" control it sits beside.
- A **one-page project summary** built from whatever the project actually
  has, naming the gaps rather than dropping the sections it cannot fill.

### Security

- **A website you had open could previously drive the engine** while the
  app was running — reading your project list, or deleting a project.
  Requests now have to come from the app itself. See
  [`SECURITY.md`](SECURITY.md).
- Project, dataset and image identifiers can no longer be crafted to write
  outside your projects folder.
- The threat model is written down, including what it does **not** defend
  against and the fact that the optional advisor key is stored in plain
  text.

### Fixed

- A Solution Matrix report printed raw internal values for three of its
  four quadrants.
- A Pareto silently dropped rows with a blank category, so a 10-row
  dataset reported "9 total" with no explanation.
- The quality scan reported "clean" for files whose only problems were the
  three findings added in this release.

## v0.1.1

Packaged sidecar launch fix for installed Windows builds.

## v0.1.0

First public build.
