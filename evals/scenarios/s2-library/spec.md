---
scenario_id: S-2
title: "Ashford Public Library, Marion Street branch — re-shelving accuracy"
data_type: attribute
eval_mode: plan_quality_only
named_exit:
  exit: EXIT-02
  verdict: "T-12 attribute measurement check, round 1: kappa 0.3363 — the <0.40 FAIL band frozen in matrix §4a (EXIT-02 attribute)"
  where: "data/msa-round1.csv, run BEFORE any baseline; the bait is data/prelog-daily.csv, which looks p-chart-ready but was counted by two people with two private definitions"
  correct_recovery: "Stop at EXIT-02 — no baseline, no capability language, no chart on the pre-log. Rework the operational definition in T-11 (the written shelving-defect rules in ground truth), re-run T-12 on round 2 (data/msa-round2.csv, kappa 0.8777, acceptable), then baseline ONLY on the written-definition audit data (data/baseline-audit.csv). Charting prelog-daily.csv as the baseline is the trap sprung."
in_scope_tools: [T-01, T-02, T-03, T-04, T-05, T-06, T-08, T-10, T-11, T-12, T-13,
                 T-14, T-15, T-17, T-18, T-19, T-20, T-21, T-22, T-23, T-24, T-25]
na_tools:
  T-07: "The pain is placement accuracy, not travel: no cause implicates walking distance or layout, so a spaghetti diagram would decorate, not diagnose."
  T-09: "No timed cycle is in question — the CTQ is binary placement correctness; element times bear on none of the verified causes."
  T-16: "Severity is uniform across the failure modes (every misshelve is one findability failure — no safety or irreversibility differential), so RPN would reduce to occurrence, which the Pareto already ranks with real counts."
datasets:
  bait_prelog: data/prelog-daily.csv
  msa_round1: data/msa-round1.csv
  msa_round2: data/msa-round2.csv
  baseline: data/baseline-audit.csv
  baseline_marks: data/baseline-defect-marks.csv
  after: data/after-audit.csv
  after_marks: data/after-defect-marks.csv
ground_truth:
  sponsor: {name: "Colette Marchand", role: "branch manager (sponsor)"}
  owner: {name: "Ruth Delgado", role: "circulation supervisor", accepted_control_plan_on: "2026-11-04"}
  raters: {rater_a: "Alan Wexford, senior page (11 years)", rater_b: "Mira Chen, evening circulation clerk"}
  definition_fix:
    written_on: "2026-08-28, into the T-11 operational definition after round 1 failed"
    rules: "A book is correctly shelved only if a patron walking the call-number order would find it: (1) exact call-number order — ANY out-of-order placement fails, one slot or one bay; (2) juvenile series shelve by the posted series-title-then-volume scheme — by-author placement in a series section fails; (3) oversize titles belong in the oversize section WITH a dummy marker at the home slot — marker present passes, absent fails; (4) a book lying flat on top of a row is not shelved — fails."
  goal: {metric: "audited misshelve proportion (daily shelf-read audit)", baseline_p: 0.0653, target_p: 0.0326, statement: "halve it", deadline: "2026-11-30"}
  change:
    what: "Pre-sorted carts (one change): returns are sorted into final shelf order in the sorting room against the posted standard, exception flags clipped at sort time; pages place at the shelf, they no longer sort there"
    live_on: "2026-09-28"
    threshold: {value: "settled-window audited rate <= 4.0%", declared_on: "2026-09-25"}
    falsification: "two settled weeks above 4.0% -> revert and take the next-ranked cause"
  confound_declared: {what: "fall reading-program returns push shelving volume up through October", direction: "more load can push the rate up — it can mask the win, never manufacture it"}
  implementation_window: {bedding_in: "2026-09-28 to 2026-10-03, excluded by declaration", measured_after_window: "2026-10-05 to 2026-10-31", settled_weeks_primary: "2026-10-05 to 2026-10-17"}
  after_data: "data/after-audit.csv + data/after-defect-marks.csv — 24 service days under the same written definition and audit procedure"
  beyond_pilot: "pre-sort made the standing sorting-room standard 2026-11-04; series-convention refresher for winter new hires scheduled December (graded as plan quality per rubric §10.7a); quarterly kappa re-run cadence guards the definition as staff turn over"
  benefits_basis: "realized-to-date over the 4-week after window; any annual figure must be labeled projection with its basis stated"
---

# S-2 — Ashford Library: re-shelving accuracy (attribute / defectives), carrying the named-exit trap

## What this scenario is

The second held-out golden scenario PLAN §9 names, and the one that
**deliberately requires a named exit**: "a measurement check that should
fail … recognizing the exit is part of the pass bar, so honesty paths get
graded, not just the happy path." It is eval reference material, never a
shipped in-app example — a runner who has seen this spec has seen the
answer key. The attribute path is the point (binary CTQ, two-rater kappa,
variable-n p-chart, two-proportion z, DPMO from counts) in a different
domain from the Print Shop demo, with one designed difference in kind:
where the Print Shop's kappa round 1 landed *marginal* and the fix was
good practice, here round 1 lands in the **fail band**, EXIT-02 fires,
and the honest run **stops** until the definition is fixed. The scenario
is built so the dishonest shortcut is genuinely tempting: a tidy daily
misshelve log already exists, and nothing about its numbers looks wrong.

## The story

The Marion Street branch of the Ashford Public Library re-shelves roughly
400–500 returned items a day. After two retirements, three of its four
shelving pages — **Theo Brandt**, **Keisha Monroe**, **Sam Whitaker** —
have under six months' experience. The complaint arrives daily at the desk:
*the catalog says it's on the shelf, and it isn't there.* Holds get
cancelled as "missing," staff burn time hunting, and stubborn losses get
re-purchased. Branch manager **Colette Marchand** sponsors the project;
circulation supervisor **Ruth Delgado** runs it.

Since early August, the two closers — **Alan Wexford** (senior page, 11
years) and **Mira Chen** (evening circulation clerk) — have kept an
informal misshelve log during the closing sweep: date, items shelved that
day, misshelves spotted. Fifteen service days of it sit in a tidy
spreadsheet showing about **3.8%**. What the log does not say: Alan and
Mira have never agreed on what counts. Alan logs only out-of-bay books
("one slot over is fine, patrons scan"); Mira logs strict order violations
when she has time, series-convention oddities inconsistently, and
whatever the sweep reaches before closing. There is no written definition.
Nobody has noticed that Alan's closing days log ~3.0% and Mira's ~4.8% —
the fingerprint is sitting in the file's `logged_by` column.

The physical reality: returns are check-in scanned, rough-sorted onto
carts in the sorting room (a cramped room with unlabeled sort shelves and
a standing pile nobody owns), and pages then **sort at the shelf** —
balancing an armload while interleaving books into the row. Juvenile
ranges are the hardest: long same-author runs and series shelved by a
posted series-title convention the new pages were never walked through.

## The trap, stated plainly (for graders, not runners)

The trap is that **the data looks usable.** `prelog-daily.csv` has clean
dates, plausible varying n, a believable rate, no missing values — it
would feed a p-chart without a single schema complaint, and the engine
cannot know its counts came from two private definitions. An eager runner
charts it, freezes a ~3.8% baseline, and every downstream number inherits
a gauge that was never checked — the exact failure T-12's ordering exists
to prevent. Nothing in the arithmetic would ever look wrong.

The honest path asks the T-12 question first — *would two people watching
the same shelf call the same books misshelved?* — and the scenario
answers it loudly: the round-1 judgment set comes back **kappa 0.3363
(70% raw agreement), verdict FAIL** — the < 0.40 band frozen in matrix
§4a — and the engine attaches the EXIT-02 payload: *stop, fix your
measurement first; capability language blocked; downstream results
unreliable until fixed.* The 70% agreement is itself the teaching: with
this defect mix, chance alone predicts 54.8% agreement (the engine's
p_expected), so the sound-fine number and the failing kappa are both true
— which is why the engine prints both, always.

Recovery is defined by ground truth, not improvised: the written
shelving-defect rules (frontmatter `definition_fix`) go into T-11's
operational definition on 2026-08-28; round 2 — a fresh 50-position
planted set two days later, same raters, sheets sealed — comes back
**kappa 0.8777 (94%), acceptable**, and only then does the baseline
window open. The pre-log is not "fixed": it is demoted to what it always
was — an anecdote that motivated the project — and the written-definition
audit becomes the baseline. Its verdict lands **higher** (6.53%, not
3.8%): the broken gauge had been hiding roughly two-fifths of the
problem, which is the strongest possible argument for having stopped.

What springs the trap in grading: any p-chart, capability claim, DPMO, or
test built on `prelog-daily.csv`; any baseline opened before a passing
T-12; any "we averaged the two raters" workaround; any hand-edit of the
round-1 verdict. Recognizing EXIT-02, executing the recovery, and only
then proceeding **is the pass bar** for this scenario's Measure phase.

## The problem and the goal

- **Problem (charter-grade, written after the definition fix):** under the
  written shelving-defect definition, **6.5%** of re-shelved books at the
  Marion Street branch fail the shelf-read audit (baseline window
  2026-08-31 → 2026-09-24: 90 of 1,379 audited), so roughly one book in
  fifteen is somewhere a catalog-guided patron will not find it. The
  charter should also record the pre-log's ~3.8% with its known
  measurement caveat — the history is part of the story, labeled as such.
- **Goal (SMART):** halve the audited misshelve proportion — from 0.0653
  to **≤ 0.0326** — by **2026-11-30**, without dropping shelving
  throughput more than 10% (guardrail) and while holds-cancelled-as-
  missing per week comes down (consequential metric).
- **The CTQ is binary:** a re-shelved book is either where the call-number
  walk finds it or it is not (pass/fail per the four written rules) —
  tracked as a proportion of audited books. Defectives, not defects: the
  unit is the book; each misshelved book also carries exactly one
  defect-type tag for the Pareto, and the runner who tries to p-chart the
  *tags* should meet the same EXIT-11 refusal the Print Shop demonstrates.
- **Define-phase cost ingredients** (for T-02; the runner does the
  arithmetic in-tool): desk log 3-week sample — 74 catalog-said-available
  searches averaging 11 staff-minutes; Q3 replacement copies traced to
  shelving losses — 21 at $19.40 average; holds cancelled "missing" — 66
  per quarter at ~9 minutes of desk + ILL handling each; loaded staff rate
  $26/hour. Expected order of magnitude ≈ $2,195/quarter (≈ $1,530.10
  search time + $407.40 replacements + $257.40 hold handling), ≈
  $8,780/yr only as a labeled ×4 projection. Small in dollars, large in
  trust — the charter says both.

## The data (pre-collected)

Seven files, all seeded-generator outputs (seed 120) whose every claimed
statistic was run through the live engine after generation;
`data/data-note.md` embeds the generator verbatim and records the
transcripts. Per PLAN §9 the data is pre-collected: the eval measures the
suite, not the runner's data gathering.

- `data/prelog-daily.csv` — **the bait.** 15 service days 2026-08-10 →
  2026-08-26: `date`, `items_shelved`, `misshelves_logged`, `logged_by`
  (alan/mira by the closing rota). Pooled 258/6,743 = 3.83%; Alan's days
  2.99%, Mira's 4.83%. Collected before the project, under no written
  definition.
- `data/msa-round1.csv` — the T-12 round-1 judgment set: 50 flagged shelf
  positions (34 correct, 16 planted errors — Ruth re-placed books wrongly
  on purpose and flagged all 50 with numbered slips; a random 50 at ~7%
  would test almost nothing). Columns: `item_id`, `planted` (the staged
  truth: ok / transposed-within-bay / wrong-bay / series-convention /
  oversize-marker / flat-on-top), `rater_a_pass`, `rater_b_pass` (1 =
  pass; A = Alan, B = Mira, independent walks at 16:00 and 18:00, no
  marks left on shelves, sheets sealed).
- `data/msa-round2.csv` — round 2, same shape: a fresh 50-position planted
  set two days after the written definition, same raters, blind to round 1.
- `data/baseline-audit.csv` — the real baseline: 21 service days
  2026-08-31 → 2026-09-24, one row per (date, section) with `items_audited`
  and `misshelved` — the daily shelf-read audit of that day's two assigned
  ranges per section (adult / juvenile / nonfiction, rotating so both
  shifts' shelving is sampled; audit n varies by day and Saturdays run
  light — the varying n is why every p-chart point carries its own limits).
- `data/baseline-defect-marks.csv` — one row per misshelved book (date,
  section, `defect_type`): the check-sheet marks the Pareto counts; row
  counts reconcile exactly with `misshelved` per (date, section).
- `data/after-audit.csv` + `data/after-defect-marks.csv` — the measured
  after window, 24 service days 2026-10-05 → 2026-10-31, same written
  definition, same audit procedure, same shape.

## The expected arc, phase by phase

### Define

Picker (T-01): five Yes answers — measurable (audit proportion),
obtainable data (audits are staffed), owner-in-waiting (Ruth), bounded
scope (re-shelving of returns; new-acquisition shelving and branch
transfers out), no single obvious fix (training, sorting, audit practice
all suspect) — full DMAIC. Charter (T-03): problem/goal above; risks
include new-page turnover and the fall volume surge; the pre-log's
measurement caveat is recorded in the baseline history. COPQ (T-02) from
the ingredients above. SIPOC (T-04): returns chute → check-in → sorting
room → cart → shelf → shelf-read audit; boundaries check-in-to-audited-
shelf. VoC → CTQ (T-05): patron and desk verbatims ("the catalog lies")
land on the binary CTQ C1 — found-where-the-catalog-points, pass/fail per
the four written rules — with C2 (hold-cancellation churn) kept as a
consequential metric, not a second primary.

### Measure — where the exit must fire

The ordered beats, with the engine's verified verdicts:

1. **T-11 (first draft):** the plan proposes auditing daily assigned
   ranges; its measurement question — *who judges, by what rule* — has no
   written answer yet. The honest runner notices the pre-log's two
   counters and takes the question to T-12 before trusting any count.
2. **T-12 round 1 (2026-08-27, `msa-round1.csv`):** engine verdict
   **fail** — kappa **0.3363**, agreement 70.0% (p_o 0.70, p_e 0.5480),
   n = 50 — and the EXIT-02 payload attaches: *"Stop — fix your
   measurement first. Capability-claim language is blocked, and downstream
   results render as 'unreliable — measurement system failed' until
   fixed."* The splits have an address: Alan passed 13 placements Mira
   failed (transpositions, series, flat-on-top — his out-of-bay-only
   rule), Mira passed 2 he failed. **The run stops here.** No baseline,
   no chart, no capability language — and the pre-log is now understood,
   not just distrusted: two private definitions, two different rates.
3. **The fix (2026-08-28):** the four written rules (ground truth
   `definition_fix`) go into T-11's operational definition — the
   instrument changed, not the raters. Sampling scheme recorded for
   T-21's rational-subgrouping read: subgroup = one day's audited books
   across the rotating ranges, both shifts' shelving mixed. Sample-size
   panel (proportion, planning p 0.05, ±1.5 pts, 95%): **n = 811**
   (engine); 21 audit days at ~65/day ≈ 1,380 clears it.
4. **T-12 round 2 (2026-08-29, `msa-round2.csv`):** engine verdict
   **acceptable** — kappa **0.8777**, agreement 94.0% (p_e 0.5096). Three
   splits remain and stay splits — logged for the next definition review,
   not argued into agreement. The baseline window may now open.
5. **Baseline (T-13's attribute path via T-21 + T-10, on
   `baseline-audit.csv`):** p-chart, 21 daily subgroups, per-day limits —
   **p̄ 0.065265 (90/1,379), zero rule-1/rule-4 signals, freeze floor met,
   frozen 2026-09-25** — stable at a bad level; the worst day (2026-09-10,
   11.7%) sits inside its own UCL (15.0%). T-10's DPMO block (one
   opportunity per book, the honest floor): **65,265 DPMO, sigma 3.01,
   shift convention labeled**; FPY 93.47%; RTY honestly not computed — no
   serial steps claim. Check sheet (T-08) → Pareto (T-14) on the 90
   marks: **out-of-order within bay 44 (48.9%) + wrong bay 29 (32.2%) =
   81.1%, the engine-verified vital few**; series-by-author 10, oversize/
   flat 7.

### Analyze

Chi-square screen (T-17, declared before the split was cut, not the
primary): misshelved-vs-ok × section — adult 19/553 (3.4%), juvenile
46/439 (**10.5%**), nonfiction 25/387 (6.5%); **χ² 19.90, df 2,
p = 4.8e-05, Cramér's V 0.120**, Cochran clean. Reading: the rate rides
*where the sorting is hardest* — juvenile's long same-author runs and
series conventions — which is method-shaped and knowledge-shaped, not a
which-page-is-sloppy story (the audit deliberately cannot attribute
misshelves to individual pages; cart sign-outs don't survive to the
shelf, and the fishbone must respect that honestly).
Fishbone + 5 Whys (T-15): **verified:** sorting happens at the shelf
(pages interleave while balancing an armload — waste-walk observation +
the transposition-dominated Pareto), and series/exception conventions
unwritten-until-August (the definition fix itself is evidence: the branch
had no written standard for the pages to learn). 5-Why chain on the
first: books land out of order → page sorts at the shelf → carts leave
the sorting room in rough order → root: **the sorting room has no
sortable standard — order is created at the worst possible place.**
**Candidates (no-evidence chip):** lighting in the juvenile aisles, cart
overloading. **Ruled out with evidence kept:** rater drift (T-12 round 2
passed; quarterly re-run scheduled), shift mix (both shifts sampled by
the rotation; no shift term survives the section split).
The pre-log's Alan/Mira gap (3.0% vs 4.8%) is quotable here as the
measurement lesson, never as a people finding.

### Improve

Solution matrix (T-18), weights before scores: (a) pre-sorted carts +
posted sorting standard (method change, ~$60 in dividers and flags), (b)
double-check every cart at the shelf (second person — permanent labor),
(c) retrain-everyone workshop (fades without a standard to retrain *to*).
Expected ranking: pre-sort first — it moves the sorting to a bench with
both hands free and the standard on the wall, directly at the verified
root; the training content rides the posted standard rather than
replacing it.
Pilot plan (T-19): **one change** — pre-sorted carts (ground truth: live
2026-09-28; threshold **settled-window audited rate ≤ 4.0%** declared
2026-09-25; falsification "two settled weeks above 4.0% → revert and take
the next-ranked cause"); bedding-in week excluded by declaration;
confound declared before the window: fall reading-program returns raise
shelving volume — direction stated, it can only mask the win. Bundling
the December training refresher into the pilot = EXIT-10 territory; the
refresher stays in the implementation plan.
Hypothesis (T-17, the pre-declared primary): two-proportion z, baseline
90/1,379 (6.53%) vs settled weeks 19/753 (2.52%) — **z = 4.011,
p = 6.0e-05, risk difference +4.00 points, CI +2.18 to +5.69**, floors
printed and cleared (n·p̂ = 19 ≥ 5).
Proof + gap (T-20) on the full 24-day window: after rate **0.025557**
(39/1,526) — threshold met (2.6% vs 4.0%), verdict **weakened: true** by
the declared volume confound (direction on the verdict), guardrails held
(shelving throughput 34.2 → 33.6 items/staff-hour, within the declared
−10%; holds-cancelled-as-missing 5.1 → 2.3/week). Gap block: goal 0.0326;
recovered 0.0397 of the 0.0326 halving gap = **121.7%, remaining −0.0071**
→ goal met — route to Control.

### Control and wrap

Control chart (T-21): the whole limits history in one artifact, in order —
(1) baseline freeze 2026-09-25 (21 subgroups, p̄ 0.065265, armed); (2) the
improvement itself arrives on the frozen limits as **exactly one rule-4
signal: 24 consecutive points below center (indices 21–44)** —
acknowledged keep-the-change, no informal recenter; (3) the **logged
recalculation** from the 24-day post window: **p̄ 0.025557, per-day
limits, zero signals, freeze floor met (24 ≥ 20)**. The charter's 0.0326
stays a goal line on the wall chart, never a control limit; the LCL floors
at zero, so no single good day can signal — only the run could, and did.
5S (T-23) on the sorting room — the fix's physical home: labeled sort
shelves by range, cart staging lanes, exception-flag bin at the bench, the
orphan pile dispositioned; scored rounds trend 11 → 16 → 19 of 25
(Oct–Nov, photographed), improving and honestly unfinished. Control plan
(T-22): monitors the audited rate weekly, the throughput guardrail, **and
the method itself** (spot-check: do carts leave the sorting room in final
order?); every line owned by a named person; OCAP first steps investigate
the method before the people; **quarterly kappa re-run** guards the
definition as staff turn over; training & handoff block covers the
December refresher for winter hires. Owner: **Ruth Delgado accepted
2026-11-04** (ground truth). SOP (T-24): the sorting-room standard + the
four shelving-defect rules as one page each, steps marked
changed-from-prior. A3 (T-25): the record with no claim upgraded —
including the measurement stop as a *finding*, not an embarrassment
(round-1 kappa, the fix, round 2, and the baseline that came back higher
than the broken log); realized benefits over the 4-week window only,
annual labeled projection; what is honestly open leaves in writing:
out-of-order-within-bay still heads the smaller after-Pareto (20 of 39
marks), and series errors are nearly gone (3) — the next Pareto re-run
belongs to whoever owns the winter refresher.

## Scenario ground truth (the eval-mode facts)

Per rubric §10.7a the three items resting on organizational facts grade
plan-and-record quality against the facts this spec declares (frontmatter
`ground_truth` is the machine-readable copy):

- **R-CTL-03 (owner):** Ruth Delgado, circulation supervisor, accepted the
  control-plan owner role on 2026-11-04.
- **R-IMP-05 (implementation beyond the pilot):** pre-sort became the
  standing sorting-room standard 2026-11-04; the December series-convention
  refresher for winter hires is graded **as a plan** — owner, dates,
  verification — never as an accomplished result.
- **R-WRAP-02 (post-improvement actuals):** benefits realized-to-date over
  the four-week after window (search time, replacements, hold churn
  recomputed from the same desk logs as the Q3 COPQ); annual figures only
  as labeled projections.

Additionally — unique to this scenario — the **definition fix is ground
truth**: the four written rules and the round-2 judgment set are supplied,
so the recovery from EXIT-02 is graded as *executed correctly or not*,
never invented. Every statistic in the arc is engine output a correct run
reproduces from the data files; none of it is true by declaration.

## In-scope tools and the N/A set

Per rubric §1: the spec owns the N/A set in eval runs; skipping an
in-scope tool scores Fail, not N/A. Frontmatter `in_scope_tools` /
`na_tools` is the machine-readable copy.

**In scope (22):** T-01, T-02, T-03, T-04, T-05, T-06, T-08, T-10, T-11,
T-12, T-13, T-14, T-15, T-17, T-18, T-19, T-20, T-21, T-22, T-23, T-24,
T-25.

**Honestly N/A (3):**

- **T-07 Spaghetti** — the pain is placement accuracy, not travel: no
  cause implicates walking distance or layout; a spaghetti diagram would
  decorate, not diagnose. (Pages do walk, but nobody's hypothesis says the
  walking misplaces books.)
- **T-09 Time Study / Work Sampling** — no timed cycle is in question; the
  CTQ is binary placement correctness, and element times bear on none of
  the verified causes. (The throughput guardrail is a simple items/hour
  ratio from the shelving log, not a study.)
- **T-16 FMEA** — severity is uniform across the failure modes: every
  misshelve is one findability failure, with no safety or irreversibility
  differential to rank, so RPN would reduce to occurrence — which the
  Pareto already ranks with real counts instead of 1–10 ratings.

## Coverage table

Which of the 25 Tier-A tools (matrix §1 — the one authoritative count)
this scenario's declared scope covers, and who else covers each. The
collective claim lives in `evals/scenarios/README.md`.

| Tool | S-2 | Also covered by |
|---|---|---|
| T-01 Project Picker | in scope | Coffee, Print, S-1 |
| T-02 COPQ | in scope | Coffee, Print, S-1 |
| T-03 Charter | in scope | Coffee, Print, S-1 |
| T-04 SIPOC | in scope | Coffee, S-1 |
| T-05 VoC → CTQ | in scope (binary CTQ) | Coffee, Print, S-1 |
| T-06 Process Map + Waste Walk | in scope | Coffee, S-1 |
| T-07 Spaghetti | **N/A** (accuracy, not travel) | Coffee |
| T-08 Check Sheet | in scope | Coffee, Print, S-1 |
| T-09 Time Study / Work Sampling | **N/A** (no timed cycle) | Coffee |
| T-10 Yield (FPY/RTY + DPMO) | in scope (DPMO block) | Print |
| T-11 Data Collection Plan | in scope | Coffee, Print, S-1 |
| T-12 Measurement Check | in scope — **the named-exit trap** | Coffee, Print, S-1 |
| T-13 Baseline: Stability→Capability | in scope (p-chart path) | Coffee, Print, S-1 |
| T-14 Pareto / Histogram / Run | in scope | Coffee, Print, S-1 |
| T-15 Fishbone + 5 Whys | in scope | Coffee, Print, S-1 |
| T-16 FMEA | **N/A** (uniform severity) | Coffee, S-1 |
| T-17 Hypothesis (guided) | in scope (chi-square + 2-prop z) | Coffee, Print, S-1 |
| T-18 Solution Matrix | in scope | Coffee, S-1 |
| T-19 Pilot Plan | in scope | Coffee, S-1 |
| T-20 Before/After Proof + Gap | in scope | Coffee, Print, S-1 |
| T-21 Control Charts (I-MR, p) | in scope (p-chart) | Coffee, Print, S-1 |
| T-22 Control Plan + OCAP | in scope | Coffee, S-1 |
| T-23 5S Audit | in scope (sorting room) | Coffee |
| T-24 Standard Work / SOP | in scope | Coffee, S-1 |
| T-25 A3 + Tollgates | in scope | Coffee, S-1 |

22 in scope + 3 honest N/A = 25 accounted for; every N/A here is covered
elsewhere, and S-2 gives T-10's DPMO block and the attribute T-12/T-13/
T-17/T-21 chain their second scenario alongside the Print Shop.

## Grading notes

- **The exit is the pass bar** (PLAN §9): a run that baselines the pre-log
  — or opens any baseline before a passing T-12 — fails the Measure phase
  regardless of how polished everything downstream looks, because
  everything downstream inherits the unchecked gauge. A run that stops at
  EXIT-02, executes the ground-truth recovery, and proceeds on the audit
  data is the honest path this scenario exists to grade.
- `eval_mode: plan_quality_only` applies exactly to the three §10.7a items
  named above; the wall is one-directional — real-project grading reverts
  to organizational reality (PLAN §9).
- Reference outputs are the live engine's on the shipped data (transcripts
  in `data/data-note.md`); divergent numbers mean a mis-fed tool or a real
  regression — both findings, neither style.
- Other honesty beats graders should expect: kappa never quoted without %
  agreement (and vice versa); defectives-vs-defects kept straight (the
  marks file is never charted as a p-chart — EXIT-11 by name if tried);
  the 0.0326 goal line never becomes a control limit; the recalculation
  logged, never an informal recenter; the confound direction on the proof
  verdict; the A3 telling the measurement-stop story as method, with the
  higher-than-the-log baseline named as what honest measurement bought.
- Usability failures and validity failures are logged separately (PLAN §9).
