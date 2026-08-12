# What to build next, and why

Written off the 2026-08-12 supervisor UAT (`README.md`). Every item here
traces to something a real user tried and could not do, in their words. It is
ordered by what they said mattered, not by what is easy.

## Where this stands — 2026-08-12

All three decisions were answered on the day: keep the DMAIC gate but give
data a front door; make saves work; version dataset edits rather than mutate
them. Phases 1–3 are built and the Phase 4 exit criterion has been measured.

**The count.** `method/scorecard.mjs` re-runs every step the two supervisors
recorded as impossible or partial, in the real app, and reports what moved.
Run it against a fresh engine after any further work.

| | 2026-08-12 baseline | After this work |
|---|---|---|
| Impossible for Dave | 4 | 1 |
| Impossible for Mike | 2 | 0 |
| Partial | 2 | 1 |
| Something to show a manager | neither had one | one-page summary, from whatever exists |

Eight of the ten blocked items now work: the charter survives walking away;
the rows and the $671.15 total are on screen; `JM` / `J. Morales` /
`J Morales` merge into one person; the ordered-and-shipped item pair groups
as one column; a row can be added by hand; the chart screen filters to a
subset and remembers its selections; the one-page summary exists; and a
project can be deleted.

**What did not move, and why:**

- **Dave 7 — paste ten rows straight into a table.** Partly. A row can now be
  typed one at a time and a file still imports, but there is no paste target.
- **Dave 16 — rate the six causes high / medium / low.** Not done. The
  fishbone still offers only Candidate / Investigating / Verified / Ruled
  out, which is about proof rather than priority. Adding a priority field is
  a real design question — it risks becoming a second, softer ranking beside
  the FMEA's — and it did not seem right to answer it by reflex.
- **Undo.** Delete exists; undo does not, anywhere.

Landed:

| | What | Commit |
|---|---|---|
| ✅ | Pareto axis, vital-few headline, silent row drops, dead "waiting" panels, top-bar save label | `c9ce4dc` |
| ✅ | Intake stuck-tree — the data-first front door | `aa9bd6b` |
| ✅ | Drafts store (engine) | `5f5f8a1` |
| ✅ | Dataset derivations (engine) — row edits, recode, derived column, each a new version with lineage | `6575feb` |
| ✅ | 1.1 rows view with per-column totals and a caveat on which totals mean anything | `ae61819` |
| ✅ | Project/artifact ids contained to the projects folder (not in the original plan) | `23c3736` |
| ✅ | 1.5 quality scan (engine) — repeated header, near-duplicates, mixed date formats | `9724c23` |
| ✅ | Drafts wired into T-03 / T-25 / T-16 — "make saves work", delivered | `4e0636c` |
| ✅ | Plain-English first screen, 28-entry glossary, delete-a-project (engine) | `67e4cd5` |
| ✅ | 1.2–1.5 client, 2.1, 2.3, 2.4, 2.5, delete UI, quadrant-label fix | `b069e83` |

## The diagnosis

Both testers wanted the same four things in this order: **load my messy file →
show me where the pain concentrates → let me fix the obvious junk in it → give
me one page I can print and take to my manager.**

Sigma AI can nearly do all four. It has a real import, a correct Pareto, an
honest quality scan, a fishbone that refuses to fake a conclusion, and a report
layer that produces designed PDFs. What it does not have is a **path** through
those four things. The pieces sit in 26 tools named for a methodology neither
tester had heard of, gated on each other, and nothing carries from one to the
next. So both of them got one useful number and a pile of empty forms.

That is the thing to fix. Not 30 complaints — one missing spine.

The clearest evidence: **the app never once showed either of them their own
rows.** It read their file, hashed it, tallied it, charted it, and refused to
display it. Everything downstream of that follows.

## Three decisions that are yours, not mine

These are real tensions in the product, not oversights. I have a
recommendation on each, but they change what Sigma AI *is*, so they are
yours.

**1. Does the DMAIC frame have to come first?**
Both testers landed on T-01's five-question screening gate before they could
write down their problem. It is defensible — it stops vague projects. But it
means the first thing a supervisor meets is a quiz about a method they do not
know, and Mike's summary was blunt: *"I do not need a DMAIC gatekeeper to look
at my error log; I just need the chart."*
*Recommendation:* keep the gate, but let "import a file and chart it" be a
front door that does not pass through it. The gate then earns its place when
someone wants to call the work a project, which is when it actually matters.

**2. Should a partial charter be savable?**
Dave typed the two sentences he came to write and lost both, because Save sits
behind eleven other required fields. The gating is deliberate — a charter with
no owner and no baseline is not a charter.
*Recommendation:* split "saved" from "complete". Let anything save as a draft;
keep the completeness bar exactly where it is for tollgates, packs and the
`Done` badge. Nobody should ever lose typing.

**3. Is editing a dataset in-app compatible with the provenance anchor?**
The SHA-256 anchor is load-bearing — it is what lets a baseline point at
exactly the bytes it was computed from. Letting a user edit rows appears to
break that.
*Recommendation:* it does not, if an edit produces a **new dataset version**
with its own hash and a recorded parent, rather than mutating in place. Then
"which file was this computed from" stays answerable, and the edit history is
itself provenance. This is more work than a mutable table and it is the only
version worth building.

---

## Phase 1 — Make the data layer real

Both testers ranked this first, independently. Dave: *"This is the biggest
one."* Mike: *"My log is never clean on the first try; fixing it in the same
place I analyze it would save real time on the floor."*

| # | What | Why it matters | Size |
|---|---|---|---|
| 1.1 | **A rows view.** The imported dataset, in a table, paged. | The app has never shown a user their own data. Dave could not check whether $671.15 of credits imported correctly because no total and no rows were ever displayed. | S |
| 1.2 | **Edit a cell, add a row, delete a row** — each producing a new dataset version with its own hash and a parent pointer. | Both testers' step 6-7 / step 19 failed here. Mike's file is *never* clean on arrival; going back to Excel to fix one typo and re-importing is the workflow that makes people stop. | L |
| 1.3 | **A recode map** — select several spellings of a value, map them to one, keep the mapping visible and exportable. | Dave's Pareto named `JM` and `J Morales` as two separate members of the vital few. They are one man. As a comparison between people that chart is not merely imprecise, it is wrong, and it looks clean. | M |
| 1.4 | **A derived column** — combine two columns into one. | Solves the item-pair question (`Ketchup 4 oz → Ketchup 6 oz`) without building a crosstab, and it is the general answer to "group by two things". Dave's whole reason for coming. | M |
| 1.5 | **Quality-scan additions**: a repeated header row, values that differ only in punctuation/case/whitespace, and more than one date format in one column. | All three were in the test files, all three passed the scan silently. The repeated header is visible as the stray `Wrong Part` bar in `pareto-after.png` — it became a category. | M |

1.5 is the highest value per hour on this list: it is the scan telling a user
what 1.3 and 1.4 are for, at the moment they can act on it.

## Phase 2 — Make the first hour end in something

| # | What | Why it matters | Size |
|---|---|---|---|
| 2.1 | **Chart view persists** — dataset and column choice saved with the project. | Both had to re-pick the dataset and the grouping every single time they opened the tool. Dave: *"Nothing in the app stores 'the chart I made'."* | S |
| 2.2 | **Export from the chart screen.** | The chart tool is the one screen with no report button, and it produced the only useful output either of them got. Both had to reach for the browser's own PNG download. | S |
| 2.3 | **Seed the A3 from what is saved.** | Dave opened it after saving a dataset, six causes and several charts and found eight empty panels reading "Not seeded yet". *"If I have already typed the data and made the charts, I should not have to type all the same facts into another screen."* | M |
| 2.4 | **A one-page project summary** — problem, target, rows imported, top categories, causes, next action — from whatever exists, with the gaps named. | This is the artifact both came for and neither got. Dave: *"I need one page I can put on a desk and talk through in ten minutes."* | M |
| 2.5 | **Filter/subset on the chart screen** (column = value). | Mike typed *"show me only errors on first shift"* into the only text box he could find. Half his errors are shift-specific; without a subset the vital-few list is half an answer. | M |

## Phase 3 — Say what things mean where they appear

Cheap, and it is the difference between "this is not for me" and "I can read
this".

| # | What | Size |
|---|---|---|
| 3.1 | Chart headlines in workplace language: *"No single aisle accounts for most complaints"* rather than *"No small subset dominates"*. Dave wrote the replacement wording himself. | S |
| 3.2 | The `Missing:` strip should name fields the way the form labels them, not the way the schema does — `business impact basis`, `problem statement: where` are internal names shown to a user. | S |
| 3.3 | First-use glossary for the terms that arrive before any explanation: Green Belt, DMAIC, PDCA quick path, EXIT-nn, provenance anchor, SHA-256, SIPOC, VoC→CTQ, COPQ, MSA, Gage R&R, RPN, 6M, A3, tollgate, guardrail metric, stratification factor. | M |
| 3.4 | The "I'm stuck" panel on Intake currently answers *"This phase's guided routing hasn't shipped yet"* — on the screen a brand-new user lands on. Either ship the Intake tree or have the button not offer itself there. | S |
| 3.5 | Warn when a Pareto compares people and the category values look like variants of each other. Dave: *"That last sentence would have caught the exact problem I found."* | S |

## Phase 4 — Stop losing work

| # | What | Size |
|---|---|---|
| 4.1 | Draft persistence on every form, or an explicit "you have unsaved text" warning on leaving. Dave lost a problem statement and a goal and only found out on reopen. | M |
| 4.2 | Real dirty state in the top bar. It now says "Nothing saved yet" (truthful) instead of "No changes yet" (a claim it could not make), but it still cannot say "unsaved changes" because nothing reports edits upward. | M |
| 4.3 | Let exports be named. Nothing either tester downloaded could be called what they wanted to call it. Minor, and it came up in both runs. | S |

## Deliberately not proposing

- **Rewriting the vital-few/flat rule.** Mike's 40-of-53 "vital few" looks
  absurd because his dates were two formats, not because the rule is wrong.
  Fix the data (1.5), then look again. Changing a frozen statistical
  convention on one UAT's evidence would need its own decision and a golden
  refreeze.
- **Dropping the gates.** They were right both times. The fishbone refusing to
  mark a cause verified without evidence is the single most-praised behaviour
  in both reports. Dave: *"That is exactly the kind of restraint I want."*
- **Auto-cleaning imported data.** The app says *"This is not a data-cleaning
  tool: the scan finds problems, it never silently fixes them"*, and Dave
  specifically approved of that. Phase 1 gives the user tools to clean it
  themselves, visibly. It does not clean anything behind their back.

## How we will know it worked

The test is reproducible. `method/` holds the harness, the driver rules, both
personas' plans verbatim, and the two data files. Re-run the same 37 steps
after each phase and count.

Baseline, 2026-08-12:

| | Dave | Mike |
|---|---|---|
| Completed as written | 14 / 20 | 15 / 17 |
| Impossible | 4 | 2 |
| Partly | 2 | — |
| Would open it again tomorrow | no | "only T-14, if someone else imported the file" |
| Had something to show a manager | no | one Pareto |

Phase 1 should move Dave's steps 7, 12, 14 and 19 and Mike's 6 and 7 from
impossible to done. Phase 2 should change both answers in the last two rows.
Those are the numbers to beat.
