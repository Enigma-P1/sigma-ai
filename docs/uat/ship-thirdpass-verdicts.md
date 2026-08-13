# Third pass and confirmation — 2026-08-13

**Intent:** Gate 0 of `docs/RELEASE-v0.2.md`, judged twice on the same day it
was built. The third pass put three summary pages in front of both reviewers —
A = the worked example, B = the data-first messy import with the
fingerprint-checked Pareto on it, C = an empty project — all produced by
clicking the app's own "One-page summary" button (`desktop/tools/
summary-exhibits.mjs`, evidence in `gate0/`). The confirmation pass re-judged
A after the two copy defects the third pass named were fixed engine-side
(`5c9b445`). Full transcripts with token counts:
`Personal-AI/tools/second-opinion/runs/2026-08-13-third-pass-*.md` and
`…-gate-0-confirmation-*.md`.

## Verdicts

| Round | GPT (`gpt-5.6-luna`) | Grok (`grok-4.6`) |
|---|---|---|
| Third pass (build `3dd8175`) | **Gate 0 PASS**, two non-blocking polish notes | **NOT-READY** — B passes, C correct, A fails on two lines of copy |
| Confirmation (build `5c9b445`) | **Met.** | **Met.** |

## Third pass — what held, what failed

Everything the second pass demanded of the page held on first contact:

- **B is a manager artifact.** Grok: *"B is now a manager artifact for the
  data-first path."* GPT: *"clearly states the 69-row source, selected field,
  ranking, percentage, and next action; the Pareto is present and tied to the
  imported data."*
- The fingerprint-checked Pareto is *"the right object"*; counts *"now name
  what they count"*; body English clean, ids and hashes footer-only; the
  11/5-verified/6-unproven frame is *"the right frame"*; the next step *"has
  an ask, an owner, a date, and is labelled advice."*
- **The check-sheet-beats-selection design rule survived review.** Grok:
  *"Design rule: keep it. A's table and no picture is correct. Do not add a
  chart to the check-sheet case; that is not a v0.3 item."*
- C *"is appropriately honest and actionable"* and *"would not embarrass"*.

What failed — A only, two lines of copy:

1. The where-fragment glued after a full stop: *"…peak-end overtime. at
   Campus coffee bar, front counter…"* — *"two fields concatenated, then
   clipped. Lowercase at after a full stop is the give-away."*
2. Cause bullets dying mid-clause (*"a cup…", "every…", "and…"*) — *"do not
   print three unfinished thoughts and call it the brief."*

Grok's stated pass condition: *"Gate 0 passes when A's problem line is one
readable statement (integrate or drop the where-fragment; no '. at …') and
each fishbone line you choose to show is a complete clause. That is copy
logic, not another rebuild."*

Carried as follow-ups, per both reviewers non-blocking: an import-quality
one-liner on the summary when the scan found findings the user has not
acted on (GPT's suggestion, Grok: *"nicer; not dress-down material"*), and
the worked example's doubled source filename
(`coffee-check-sheet-check-sheet.csv`).

## The fix, and the confirmation

Commit `5c9b445` ("Complete statements, or nothing") implemented the pass
condition as engine-side copy logic — sentence-aware fitting for the charter
narrative (whole sentences kept, the rest dropped cleanly, never a fragment),
clause-complete-or-dropped cause bullets with the pointer's count carrying
what was dropped, and the `". at "` join replaced by a composition that
respects whether the charter's `what` already ends a sentence. Seven tests
pin it, including literal never-again assertions on `". at "` and mid-clause
ellipses. Full gate green: 1771 engine tests, 267 golden steps 0 diffs, tsc,
bundle, five probes, exhibits regenerated through the real button.

Both reviewers, on the regenerated page, in full:

> **GPT:** Met. The problem line is complete, and the shown fishbone cause is
> a complete clause; no ". at …" join or mid-clause truncation remains.

> **Grok:** Met. The two Gate 0 defects are gone: the problem line is one
> finished sentence (where-fragment dropped, no `. at`), and the only shown
> fishbone cause is a complete clause, with the remainder carried by the
> `+4` pointer.

**Gate 0 is closed.** Do-not-block list unchanged through both rounds;
nothing new blocks v0.2 beyond the standing gates — installers + cold-start
smoke (Gate 1, Shawn), fresh-eyes UAT on the release candidate (Gate 2,
personas C and D are written and deliberately unburned in `method/`).

## Evidence in `gate0/`

| File | What it is |
|---|---|
| `coffee-bar-example-summary.pdf` | A on `5c9b445` — the page both models judged "Met" |
| `wrong-part-summary.pdf` | B — fresh project, ErrorLog_Sept.xlsx imported and charted, nothing else; the fingerprint-checked Pareto on the page |
| `fresh-empty-summary.pdf` | C — nothing saved; every gap named |
