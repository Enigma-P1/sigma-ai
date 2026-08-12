# Uncertified-supervisor UAT — 2026-08-12

Two people who have never used Sigma AI, have no Six Sigma certification, and
have a real operational problem, tried to use it for that problem. Both runs
happened for real, in a browser, against a live engine, on their own data.

## Why this exists

Every test before this one measured whether the app did what the app intends.
This one measured whether it does what a warehouse supervisor came to it for.
Those turn out to be different questions, and the gap between them is where
every finding in here lives.

## Method

Three phases, and the separation between them is what makes the result worth
anything:

1. **They invented their own scenario.** Two external models, held in persona
   as uncertified ops supervisors, each wrote down who they are, the problem
   that actually annoys them, the data they realistically have, what would make
   them keep the software or close it forever, and a numbered plan of what they
   would try in their first hour — before seeing a single screen.
2. **Someone drove that plan for real.** One driver per persona, working under
   written rules: do exactly what they said, in order, in their words; never
   use knowledge of the codebase to find a feature (find it by reading the
   screen, as they would); record facts not verdicts; treat an impossible step
   as a result, not a blocker. Screenshots at every step, video per chunk, and
   a tried/expected/actual line for every numbered step.
3. **They wrote the review from their own run.** Each model got its own
   screenshots and its own transcript back — never the other's — and wrote the
   feedback in persona.

Isolation was real: separate engines on separate ports, separate empty project
stores, no worked example (one of them explicitly said he did not want one),
the production bundle served from its own origin with the Tauri globals
injected — the packaged-app condition, not the dev server.

## The two testers

**Dave Mercer** — evening ops supervisor, 90,000 sq ft food-service warehouse,
18 reports on his shift. Wrong items picked onto restaurant orders: 487 errors
on 38,600 order lines in June, ~$6,800 in credits and redeliveries, 54 hours of
rework. His data is a spreadsheet the inventory clerk maintains: three date
formats, one picker recorded as `JM`, `J. Morales` and `J Morales`, a blank
aisle. Twenty steps, exact about the words and numbers he would type.

**Mike Thompson** — warehouse ops supervisor, aftermarket auto parts, 12
pickers. Wrong part in the box, 15–20 times a week, 68 logged last month,
overtime creeping up. His data is "a half-assed Excel file the lead updates
when he feels like it" — 69 rows, two date formats in one column, missing order
numbers, blank cells, trailing-space part numbers, one blank row, and the
header line pasted a second time in the middle. Seventeen steps, deliberately
vague where a real person would be vague.

## What is in this directory

| File | What it is |
|---|---|
| `dave-run-log.md` | Every step of Dave's run: tried, expected, actual, screenshots |
| `dave-report.md` | Dave's own write-up, from his screenshots |
| `mike-run-log.md` | Every step of Mike's run |
| `mike-report.md` | Mike's own write-up, from his screenshots |
| `pareto-before.png` | The Pareto Mike would have taken to a meeting |
| `pareto-after.png` | The same chart, same data, after the axis fix |

Screenshots and video (135 images, 36 recordings) were captured for both runs
and are not in the repo — they are the raw material the reports were written
from, not the deliverable.

## What they independently agreed on

Neither tester saw the other's run. These landed in both:

- **The Pareto was unreadable when the categories were numbers.** Dave's aisle
  numbers printed on an axis labelled 5/10/15/20; Mike's part numbers on one
  labelled 20k–80k. Neither could tell which bar was which. **Fixed.**
- **The app never showed them their own rows.** Both tried to add or correct a
  record by hand; neither could. Data enters only through a file.
- **Nothing carried between tools.** The charter did not seed the fishbone, the
  fishbone did not seed the A3, the chart did not reach any export.
- **They got exactly one thing they could act on** — a ranked list of the worst
  categories — and both said so plainly, unprompted. Everything else in their
  hour produced nothing they could take to a manager.

## Triage

### Fixed in this pass

| Finding | Where | Fix |
|---|---|---|
| Pareto axis goes numeric when categories look like numbers: bars out of count order, no labels, cumulative line zigzags | `charts/Pareto.tsx` | `xaxis: { type: "category" }` |
| A "vital few" of 21 names in one sentence, with nothing saying the few was not few | `charts/Pareto.tsx` | Name the first five, count the rest, and lead with `40 of 53 categories` |
| Pareto silently drops rows with a blank category — "9 total" over a 10-row dataset | `tools/chartset/ParetoPanel.tsx` | Say how many rows are missing that column and are not counted |
| Histogram and Run Chart sit on "Waiting on the engine's descriptive statistics…" forever when the dataset has no numeric column | `tools/chartset/{Histogram,RunChart}Panel.tsx` | Say the dataset has no numeric column, as Scatter and Box already did |
| Top bar said "No changes yet" while a user was typing a charter that was then lost | `app/TopBar.tsx` | `idle` only knows that nothing was saved — say that |

### Real, not fixed here

Each of these is a design decision, not a defect to patch quietly:

- **A dataset cannot be viewed, edited or appended.** Both testers hit it, both
  ranked it first. Mike: "My log is never clean on the first try; fixing it in
  the same place I analyze it would save real time on the floor."
- **Category values cannot be merged or renamed.** Dave's Pareto named `JM` and
  `J Morales` as two separate members of the vital few — the same man. As a
  comparison between people, that chart is wrong in a way that would matter.
- **No two-column grouping.** The app has `Item ordered` and `Item shipped` on
  the same row and cannot pair them, which is the whole question Dave came with.
- **The A3 opens empty even when the work exists.** "Not seeded yet" on every
  panel after a dataset, six causes and several charts had been saved.
- **A duplicated header row imports as data** and the quality scan does not
  mention it. Visible as the `Wrong Part` bar in `pareto-after.png`.
- **No filter or subset anywhere**, and no drill-down from a bar.
- **The charter is all-or-nothing.** Eleven required fields between a
  supervisor and saving the two sentences he came to write, and the text is
  gone when he leaves.
- **"I'm stuck" says the Intake routing has not shipped** — on the screen a
  brand-new user lands on.
- **Jargon on first contact.** Green Belt, DMAIC, EXIT-01, provenance anchor,
  SHA-256, all before anything has been explained.

### Where a tester was mistaken

Kept for honesty, since the reports are verbatim:

- Mike wrote "the on-screen version was fine; the downloaded picture is not."
  The on-screen chart had the same numeric axis — his own run log records the
  axis reading 20k–80k on screen. Same defect, one surface.

## What was good, in their words

Worth recording, because it is the part that survived contact:

- The messy file went in untouched and produced a real answer. Mike: "The
  Pareto told me five part numbers make up 87% of the 69 logged errors. I can
  take that list to the shift lead Monday morning."
- The quality scan reported without silently fixing. Dave: "I would rather know
  that the software left my data alone than have it quietly change dates or
  employee names."
- The fishbone refused to let a plausible cause be marked verified. Dave: "That
  is exactly the kind of restraint I want in a tool. I do not want software
  giving me a fake answer based on ten complaints."
- Projects and saved artifacts survived close-and-reopen in both runs.
- No crash, no page error, no console error, no HTTP error in either run.
