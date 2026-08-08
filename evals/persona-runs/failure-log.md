# Task-level failure log — M6 simulated persona runs (S-1 + S-2)

> From SCRIPTED UNTRAINED-PERSONA RUNS simulated by an AI agent
> (2026-08-07 owner ruling; see README.md). Engine v0.1.0, run date
> 2026-08-08. Classification per PLAN §9: **usability** (a confusing
> screen) and **validity** (a wrong analysis) logged separately; stalls
> outside the suite's stated scope go here for a **scope ruling**.

## Legend

Severity: **low** (self-recoverable from what's on screen), **medium**
(recoverable but cost real time or needed off-screen knowledge),
**high** (could silently produce a wrong project). Every "screen text"
below is quoted from a live response or from the shipped UI content
files; every engine number is from the runs' evidence projects
(`persona-s1-corey`, `persona-s2-becca`).

## Entries

### FL-01 — COPQ Quantity/Rate carry no units
- **Scenario/phase/tool:** S-1, Define, T-02.
- **What happened:** Corey entered the contact COUNT (1,463) as
  quantity against the $34/hr rate; the engine computed a $49,742 row.
  Self-recovered via the computed Amount echo.
- **Class/severity:** usability / low.
- **Screen text involved:** field labels are bare "Quantity" and
  "Rate"; the Amount helper says only "Computed by the engine on save."
- **Fix direction:** per-category unit hints (hours × $/hour), or an
  inline "quantity × rate = amount" preview before save. Note: Becca
  (S-2) cleared the same field correctly — the trap is real but not
  universal.

### FL-02 — Sample-size helper example anchors the margin
- **Scenario/phase/tool:** S-1, Measure, T-11 sample-size panel.
- **What happened:** Corey copied the helper's example margin (±0.5,
  written for the Coffee Bar's minutes scale) onto an hours-scale
  project → n = 650 against an achievable ~130. Self-recovered by
  re-reading the same guidance ("precise enough to matter against an
  8.4 → 5.0 minute goal") and reasoning from his own goal gap.
- **Class/severity:** usability / low.
- **Screen text involved:** the margin guidance and the calculator's
  plain-English echo ("collect at least 650 data points").
- **Fix direction:** phrase the margin guidance relative to the user's
  charter gap (which the project already knows) instead of a
  fixed-scale example.

### FL-03 — Nothing on-screen catches a flattering clock-stop rule
- **Scenario/phase/tool:** S-1, Measure, T-11 operational definition.
- **What happened:** Corey's draft stop rule was the tech's close-click
  — reproducible (it passes the two-people test!) but flattering, since
  techs batch-close at day's end. Recovery came only from an in-story
  ask (Naomi) — logged per PLAN §9 as "what was asked."
- **Class/severity:** usability / **medium** — the failure mode the
  two-people question cannot see is a *biased but consistent* clock.
- **Screen text involved:** the op-def panel subtitle "Would two
  different people measuring this get the same number?" (necessary, not
  sufficient).
- **Fix direction:** add a bias prompt to the start/stop guidance
  ("does your stop moment flatter the process? who controls it?") —
  the import tab's bias self-check already asks exactly this shape of
  question for sampling.

### FL-04 — Transcribed tallies can't carry strata
- **Scenario/phase/tool:** S-1 + S-2, Measure, T-08 transcribe mode.
- **What happened:** both personas transcribed existing tallies as
  per-category counts; prescore flagged missing strata
  (S-1 `strata_declared`, S-2 `entries_carry_full_strata`) with no way
  to satisfy it inside transcribe mode. Both accepted the flag with
  reasoning.
- **Class/severity:** usability / low.
- **Screen text involved:** "no stratification fields declared —
  shift/station/operator splits won't be possible downstream."
- **Fix direction:** transcribe panel accepts counts per
  category-per-stratum (a small grid), or the flag detail explains the
  accepted-with-reasoning path.

### FL-05 — T-13 "Baseline" is continuous-only with no attribute signpost
- **Scenario/phase/tool:** S-2, Measure, T-13.
- **What happened:** the rail's one tool named "Baseline" cannot
  baseline an attribute project and never says so; Becca fed it daily
  counts and a percent "USL" and left more confused than she arrived.
  The real attribute baseline path (p-chart in T-21 + DPMO in T-10) is
  discoverable only by scanning a different phase's rail.
- **Class/severity:** usability / **medium** (a genuine stall; the
  scenario's own arc says "T-13's attribute path is T-21 + T-10" but
  the app never tells the user).
- **Screen text involved:** T-13's form (dataset / numeric column /
  USL / LSL); helper whenNotTo covers instability and shuffled data but
  not data type.
- **Fix direction:** T-13 reads the T-11 plan's declared `data_type`
  and, for attribute projects, shows a one-line router: "pass/fail data
  baselines on a p-chart — open T-21 (and T-10 for DPMO)."

### FL-06 — Meaningless capability numbers print for garbage inputs
- **Scenario/phase/tool:** S-2, Measure, T-13 (`/stats/baseline`).
- **What happened:** counts (9–29/day) against USL 1.9 returned mean
  17.2, **Ppk −0.878**, DPMO 995,780 — correct arithmetic on
  semantically wrong inputs. The honesty devices that exist DID fire
  (EXIT-04's "you don't have a baseline yet," Cpk suppressed,
  `performance_not_capability: true`), but a Ppk and a DPMO still
  render for a spec limit that sits below every observed value.
- **Class/severity:** usability / medium, with a validity note — an
  untrained reader can quote that Ppk.
- **Screen text involved:** "not stable — you don't have a baseline
  yet: only 15 points (< 20)…" plus the printed performance indices.
- **Fix direction:** a range sanity check — when a spec limit falls
  outside the data's observed range entirely (USL < min or LSL > max),
  say "check your units — every observed value is beyond this limit"
  before printing indices.

### FL-07 — No gate models "no T-12 has ever run" (the trap's soft link)
- **Scenario/phase/tool:** S-2, Measure, T-21/T-10/gates.
- **What happened:** Becca charted the bait at T-21 with no measurement
  check on file. Nothing consulted the T-12 verdict: the gate
  (`measure_capability_language_requires_msa_pass`) fires only on an
  EXISTING T-12 reading "fail," and T-21/T-10 don't look at all. The
  only refusal was the 20-point freeze floor ("got 15 point(s)"), which
  is about point count, not measurement trust. **A 20+-day pre-log
  would have frozen a broken baseline behind an all-green prescore
  strip.** gates.py's own comment records the decision: "a project that
  never ran T-12 is a softer, different concern … isn't modeled as its
  own gate this milestone."
- **Class/severity:** **out-of-scope → scope ruling requested** (it is
  a documented milestone decision, not an accident) — but flagged
  **high** visibility: it is the exact S-2-shaped hole, and rubric
  R-MEA-07's "the suite blocks the capability-language automatically"
  reads stronger than what ships.
- **Screen text involved:** the 422 floor text; T-21's six all-pass
  prescore checks on the bait chart.
- **Fix direction:** a soft gate (logged-override style) on
  freeze/baseline actions when the project has no T-12 on file:
  "you're about to trust numbers whose measurement was never checked —
  run T-12 or log why not."

### FL-08 — T-21's helper frames the tool as post-Improve only
- **Scenario/phase/tool:** S-2, Measure, T-21.
- **What happened:** the attribute baseline REQUIRES T-21 during
  Measure, but the helper's whenToUse says "After Improve implements
  the fix, to hold it," and the rail shelves T-21 under Control. Becca
  used it for a baseline anyway (correctly!) while the helper described
  a different job.
- **Class/severity:** usability / low (compounds FL-05).
- **Screen text involved:** T-21 whenToUse as quoted.
- **Fix direction:** one sentence in the helper acknowledging the
  baseline-freeze use for attribute projects, or FL-05's router making
  the cross-phase hop explicit.

### FL-09 — Post-Define sequence gates are still NOT_YET_BUILT stubs at M6
- **Scenario/phase/tool:** both runs, all phases past Define
  (`measure_to_analyze`, `analyze_to_improve`, `improve_to_control`,
  `control_to_wrap`).
- **What happened:** every one returns NOT_YET_BUILT with stub text
  naming milestones that have since shipped their tools ("Measure math
  guards (stability/capability) ship across M2," etc.). Neither persona
  was ever sequence-checked after Define; the protection that exists
  lives in per-tool validators and the one MSA hard gate.
- **Class/severity:** **scope ruling requested** / medium — either the
  guards were deliberately re-scoped out of v1 (then the stub text and
  PLAN §4.2's description should say so) or they were missed.
- **Screen text involved:** "not-yet-built: Measure math guards
  (stability/capability) ship across M2."
- **Fix direction:** ruling first; if in-scope, the M2-M4 rows exist to
  be filled; if not, re-word the stubs so they don't cite past
  milestones as future.

### FL-10 — The A3's graded blocks are invisible until post-save flags
- **Scenario/phase/tool:** both runs, Wrap, T-25 (plus S-1's T-22 OCAP
  coverage, same pattern).
- **What happened:** both personas filled the eight panels, saved, and
  only then learned (from three prescore flags each) that tollgates,
  lessons, and the realized-benefits block exist and are required for a
  passing wrap. Both fixed everything from the flag details alone —
  the details are excellent — but the discovery order is backwards.
- **Class/severity:** usability / low (the flags carry precise
  addresses; recovery was fast both times).
- **Screen text involved:** "phase(s) with an unanswered tollgate
  question: ['Define', 'Measure', …]"; "a lessons panel of only wins is
  not lessons"; "the realized-benefits panel is missing its COPQ re-run
  reference or stated window."
- **Fix direction:** show the empty required blocks in the form before
  first save (empty-state cards), not only as post-save flags.

### FL-11 — The stuck tree's baseline leaf is not data-type aware
- **Scenario/phase/tool:** S-2, Measure, Stuck button.
- **What happened:** the Measure tree that saved this run routes its
  "measurement checked? → yes" branch to T-13 for everyone — an
  attribute user who answers yes gets sent to the continuous form
  (FL-05's dead end) by the same tool that rescued them.
- **Class/severity:** usability / low (latent — Becca hit the T-12 leaf
  instead, which was correct).
- **Screen text involved:** leaf "Run the baseline — Stability then
  Capability (T-13)."
- **Fix direction:** leaf resolution consults the T-11 plan's
  `data_type` (the completion-aware substitution mechanism already
  reads project state, so the plumbing exists).

### FL-12 — S-2 golden↔spec COPQ discrepancy (found while validating this run)
- **Scenario/phase/tool:** S-2, Define, T-02 — in the FROZEN GOLDEN,
  not in this persona run.
- **What happened:** the S-2 golden's T-02 enters the search-time row
  as the raw 3-week sample (13.57 h), computing total **$1,017.62** —
  while the same golden's T-03 charter claims "COPQ calculator Q3 2026
  total ($2,195) × 4" and the spec's cost block expects ≈$2,195/quarter
  (search ≈$1,530.10, i.e. the sample scaled ×13/3). The golden's two
  artifacts contradict each other; the spec agrees with the charter,
  not the COPQ. (This run's persona scaled the sample and is internally
  consistent: engine total $2,193.34.)
- **Class/severity:** **out-of-scope for this run → flagged for the
  director** / medium — goldens are frozen and this task may not touch
  them, but a golden that disagrees with its own spec will fail
  somebody's diff eventually.
- **Screen text involved:** golden `T-02.validate.json` total
  1017.6200000000001 vs golden `T-03.validate.json` business_impact
  basis "$2,195 x 4".
- **Fix direction:** reconcile the golden driver's T-02 quantity
  (13.57 → ~58.79 scaled hours) or the spec/charter's $2,195 — one of
  them is the intended truth.

## Zero-padding honesty

- **Strict validity failures (a wrong number presented as right): zero
  observed.** Every engine statistic checked during both runs was
  correct for its inputs; the two validity-adjacent entries (FL-06,
  FL-07) are about wrong inputs being computable and about a missing
  guard, not about wrong math.
- **Hard stalls (unrecovered): zero.** Both personas finished all
  in-scope tools. This is worth stating with its caveat: both personas
  are scripted to be *careful*; FL-03 and FL-07 name the places where a
  careless real human would NOT have recovered, and those two entries —
  not the zero — are the finding.
- **Advisor surfaces: not exercised.** These runs deliberately used
  only the deterministic surfaces (helpers, prescore, gates, stuck
  tree, refusals); no entry here covers the AI advisor, so its absence
  from this log means untested, not clean.

## Totals

| Classification | Count | Entries |
|---|---|---|
| Usability | 8 | FL-01, FL-02, FL-03, FL-04, FL-05, FL-08, FL-10, FL-11 |
| Usability with a validity note | 1 | FL-06 |
| Out-of-scope → scope ruling requested | 3 | FL-07 (the trap's soft link), FL-09 (stub gates), FL-12 (golden↔spec) |
| Strict validity (wrong math/wrong verdict) | 0 | — |

By severity: high-visibility 1 (FL-07), medium 5 (FL-03, FL-05, FL-06,
FL-09, FL-12), low 6. Suite catches that worked as designed (not
failures, recorded in the transcripts): charter solution-language flag,
fishbone evidence 422 + missing-fix flag, EXIT-10 twice, EXIT-02 + hard
gate, signal-acknowledgment flag, T-22/T-25 completeness flags.
