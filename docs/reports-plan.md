# Plan: per-tool reports — documents, not transcripts

Status: reviewed by GPT-5.6 and Grok-4 (independent, plan-only, no access to
this reasoning). Their surviving findings are folded in below and marked
**[review]** where they changed the plan. Run record:
`Personal-AI/tools/second-opinion/runs/2026-08-10-*.md`.

## The problem

Sigma AI computes correct answers and shows them on screen. Almost none of it
can leave the app as something a person would show someone else.

- 1 of 23 tools exports (the T-03 charter).
- The whole-project export prints every field that was typed. 125 pages. It is
  a good audit trail and a useless report.

Minitab charges roughly $3k/seat/year and its actual unit of value is **one
analysis, one page**: a chart with the verdict on it and the caveats that
would invalidate it. That page is the product. The arithmetic is not — Excel
does arithmetic.

## Three document types, deliberately distinct

| Type | What it is | Who reads it | Count |
|---|---|---|---|
| **Tool report** | One tool, one page: the picture, the number, what it means, what would invalidate it | The person doing the work, and whoever they show it to | 23 |
| **A3** | The whole project on one sheet | A sponsor, in a ten-minute meeting | 1 |
| **Project record** | Every field as entered, in DMAIC order | Nobody — until someone challenges a number, and then it is the only thing that matters | 1 |

The project record already exists and **stays**. It is the receipts: when
someone asks where 8.4 came from, it shows that 52.5 was typed where 5.25 was
meant. That is a real job, already done, and it is not what a report is for.

## Every report has five zones

Consistency is the product. Read one report, you can read all of them.

1. **Header** — project, tool, date, version.
2. **The answer** — chart, table, or number. Most of the page.
3. **What it means** — one or two plain sentences.
4. **Report card** — what would invalidate this: assumptions checked, sample
   size, estimates flagged as estimates, confounders named. Verified: all 23
   tools already compute these (`PRESCORE_REGISTRY` covers 23/23, each result
   carrying a status and a plain-English detail). Today they appear only on
   screen.
5. **Provenance** — **[review, Grok]** dataset id and row count, date range,
   spec source, engine version, export timestamp, artifact version. The report
   must answer "where did 8.4 come from" *on its own*, without reaching for
   the 125-page record.

**Verdict and recommendation stay separate. [review, GPT]** "The means differ"
is a computed verdict. "Standardise the new method after checking week-2
stability" is advice. Printing them in one voice turns advice into a
computed fact — precisely the failure this product exists to prevent.

**One labelling vocabulary across all 23** — *estimate*, *pilot-only*,
*unstable process*, *measurement system not qualified* — used identically
everywhere. **[review, Grok]** A one-pager is exactly the format that mints
false confidence, and the labels are the guard.

**When MSA fails, the report says so in the reports downstream of it.
[review, GPT]** A Gage R&R percentage printed without "do not trust the
capability numbers that follow" is worse than not printing it.

## Chart capture — the one hard technical question

A PDF needs pictures. ReportLab cannot draw the app's charts.

**Chosen: capture on the client, stamped with provenance.**

The codebase makes capture unusually cheap, verified by reading it:

- Every Plotly chart renders through one component (`charts/PlotlyChart.tsx`
  via `ChartFrame`). `Plotly.toImage()` at that single choke point covers
  histogram, run chart, Pareto, scatter, box, I-MR, p-chart and the 5S trend —
  eight chart types, one change.
- The three hand-drawn canvases (fishbone, process map, spaghetti) are Konva
  `Stage`s, which already hold a `stageRef` and expose `.toDataURL()`.

**GPT argued against making browser pixels the source of document truth**, and
preferred a canonical chart spec rendered identically by UI and engine. That is
the right long-term answer and it is a second renderer's worth of work; it also
reintroduces the drift risk it aims to remove, because two renderers of one
spec still diverge. Partially accepted: client capture stays, but **every
captured image carries the artifact version and a hash of the data it was drawn
from, and the engine refuses to embed a capture whose hash does not match the
artifact it is exporting** — so a stale chart is a hard error, never a quiet
wrong number. **[review, GPT + Grok]**

Reports whose capture fails still render, with the chart area replaced by a
stated reason. A missing picture must not cost the page.

## Defined behaviour for thin and broken inputs [review, Grok]

Named now, not discovered later:

- **n below the tool's floor** — the report prints, the answer zone says why it
  is not computed, the report card says what n would be needed.
- **No spec limits** — capability is omitted, not defaulted; the histogram and
  stability verdict still print.
- **Never opened / nothing saved** — the button is disabled with the reason.
- **Data edited after export** — the provenance block's timestamp and hash make
  it detectable; the file name carries the date.
- **File naming** — `<project>-<tool>-<slug>-<YYYY-MM-DD>.pdf`, e.g.
  `coffee-bar-T13-capability-2026-08-10.pdf`.

## What each tool's report is

### Group A — the chart is the answer

1. **T-13 Baseline → Process Capability Report.** Histogram with spec limits,
   distribution curve, Cpk/Ppk, PPM out of spec, stability verdict. The Coffee
   Bar case prints "stable, Cpk −1.14" — predictable and predictably bad.
2. **T-12 MSA → Gage R&R Report.** Components of variation, %study variation,
   repeatability vs reproducibility, and whether the measurement system can see
   what you care about at all.
3. **T-21 Control Chart** — out-of-control points marked with the rule they
   broke, frozen limits and freeze date.
4. **T-17 Hypothesis → Summary / Diagnostic / Report Card**, modelled on
   Minitab's Assistant: plain answer, then assumption checks, then warnings.
5. **T-20 Before/After Proof** — both distributions, the gap arithmetic, and
   the confounders that weaken the claim printed alongside rather than omitted.

### Group B — a diagram is the deliverable

T-06 Process Map, T-15 Fishbone (with the verified / investigating / ruled-out
table and its evidence references resolved to readable text, not ids
**[review, GPT]**), T-07 Spaghetti, T-04 SIPOC, T-05 VoC→CTQ.

### Group C — a table is the deliverable

T-16 FMEA (RPN-ranked; **column priority and wrap rules defined, since the
on-screen version currently truncates every cell** — `docs/field-notes.md`),
T-22 Control Plan, T-18 Solution Matrix, T-08 Check Sheet, T-09 Time Study,
T-02 COPQ, T-23 5S, T-10 Yield.

### Group D — form-shaped

T-01 Picker, T-11 Collection Plan, T-19 Pilot Plan, T-24 Standard Work, T-03
Charter (built; keep).

### The capstone

**T-25 A3** — one landscape sheet, eight panels. The content exists: 5,609
characters across background (573), current condition (506), goal (360),
analysis (768), countermeasures (768), results (1,125), follow-up (811),
lessons (698). It is currently printed as a field list; it needs a layout.

**Per-panel character budgets, enforced. [review, both]** Results is already
1,125 characters and will not fit a panel at a readable size. The A3 is a
discipline, not a container: the tool should say when a panel is over budget,
the same way it flags a solution-shaped problem statement.

## Architecture

- `export/report_theme.py` — page furniture on top of the existing
  `pdf_theme.py`: title block, verdict banner, report-card box, provenance
  footer. One place, so 23 reports cannot become 23 looks.
- `export/reports/<tool>.py` — one module per report. Hand-laid, unlike the
  generic walker: a report is a designed page and that is the point.
- `POST /project/{id}/report/{tool_id}/pdf` — body carries captured images
  plus their hashes; response is the PDF.
- Desktop: **Download report** on each tool screen. **Export project** stays,
  serving the receipts. `project_pdf.py` is untouched — different job,
  different code.

## Phasing

- **Phase 1 — the spine, proven on two dissimilar reports. [review, GPT]**
  Chart capture at both choke points with hash stamping, the report theme, the
  five-zone frame, then **T-13 Capability** (proves images) *and* **T-16 FMEA**
  (proves pagination, column priority, legibility of dense tables). One chart
  report alone does not validate the hard cases. Plus the download button and a
  probe that clicks it and checks a real PDF lands.
- **Phase 2 — rest of Group A.** MSA, Control Chart, Hypothesis, Before/After.
- **Phase 3 — phase packs. [review, both]** Moved up from last. A Define or
  Measure pack, with cover and index, is how managers actually review work, and
  it tests ordering, naming and delivery earlier than Phase 5 would.
- **Phase 4 — the A3 one-pager**, with panel budgets.
- **Phase 5 — Groups B, C, D.**

## Acceptance — what proves this worked

Not "a PDF was produced." **[review, both]** A report passes when a person who
has never been trained in this can answer, from the page alone:

1. What happened?
2. How big is it?
3. Can I trust it?
4. What should I do next?

And the programme passes when a report is used in a real gate review without
the app open.

## Decisions on the open questions

Both reviewers converged on four of five.

1. **Formats — PDF first, PNG of the same one-pager second, no PPTX.** Minitab
   users live in slides, and a crisp PNG pastes without a layout fight. PPTX
   means masters, fonts and editable-but-broken charts: a separate product.
2. **A3 length — one page by default, with an explicitly labelled continuation
   when content cannot stay legible.** Never silently shrink type. A continuation
   is disclosed; an illegible page is a lie.
3. **Unit — per-tool is the primitive, phase packs immediately after.** Not
   either/or.
4. **Page size — support Letter and A4, defaulting from the OS locale, with
   separate templates rather than scaling A4 artwork.** The existing charter
   PDF is A4 only; US users expect Letter.
5. **Report card on page one.** A caveat that changes the interpretation cannot
   live on page two, because page one is what gets circulated. Detailed
   diagnostics may go to an appendix.

## Status — 2026-08-12

Every phase of this plan has shipped, in a different order than written.

| Phase | State |
|---|---|
| 1 — spine, Capability, FMEA | done |
| 2 — rest of Group A (MSA, Hypothesis, Control Chart, Before/After) | done |
| 3 — phase packs | done, **resequenced last** (see below) |
| 4 — A3 one-pager with panel budgets | done |
| 5 — Groups B, C, D | done |

**23 of 26 tools export a designed page.** The three that do not: T-13 and
T-14 are computed views with no saved artifact (T-13's capability report
ships separately, driven from a dataset), and T-03 keeps the hand-laid
charter PDF it already had.

**Phase 3 was moved from third to last, deliberately.** The plan's argument
for moving packs up was that they test ordering, naming and delivery early.
That is true and it was outweighed: a pack is mostly empty until its
phase's tools have reports, so a Define pack built at phase 3 would have
carried one report out of five tools and tested the cover rather than the
ordering. Built last, each pack indexes real verdicts.

### Open questions, resolved by building

**PNG of the same one-pager — declined for now, with a reason.** Decision 1
above chose "PDF first, PNG second". PNG is not being added: ReportLab
cannot rasterise, so this needs a native rasterizer (pypdfium2 or similar)
shipped inside the PyInstaller onefile — on an app whose packaged sidecar
failing to launch on installed Windows was a shipping incident
(`docs/field-notes.md`, v0.1.1). A convenience format does not justify
re-opening that risk. If slide users turn out to be the blocker in real
use, the cheaper move is exporting the CHART as PNG client-side, where the
image already exists (Plotly `toImage`, Konva `toDataURL`) and no engine
dependency changes.

**Letter/A4 as separate templates** (decision 4) is still open and still
worth doing.

## Deferred, named rather than dropped

Customer logo / project code / confidential marking; locale number and date
formats; tagged accessible PDFs (charts currently embed as raster images and
will not be screen-reader legible); PPTX.

## The gap this plan does not close

No untrained person has used any of this. Every quality claim here is "the
math is right" and "a model thought the page was good." The acceptance test
above is written to be run with a real person, and until it has been, the
reports are unproven regardless of how they look.
