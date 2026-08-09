```yaml
scenario_id: S-2
persona: "Becca Lin — part-time circulation assistant, Ashford Public Library, Marion Street branch (fictional, invented for this run)"
simulated: true
label: "SCRIPTED UNTRAINED-PERSONA RUN, simulated by an AI agent per the 2026-08-07 owner ruling. Not a human result."
engine_version: "0.1.0"
date: "2026-08-08"
project_id: "persona-s2-becca"
engine_calls: 112
named_exit_required: "EXIT-02 (T-12 attribute measurement check round 1 must fail before any baseline)"
evidence: "engine project persona-s2-becca (artifact version history is the audit trail — including the bait chart at T-21 version 1)"
```

# S-2 persona run — Becca Lin (SIMULATED), with the trap sequence step by step

## The persona

Becca Lin, 24, part-time circulation assistant, "good with
spreadsheets," which at Marion Street makes her the software person.
High-school diploma plus two semesters of community college. No process
training, no statistics beyond a half-remembered class. Colette
(branch manager) asked her to run the improvement tool; Ruth
(circulation supervisor) runs the actual shelving operation and the
project. What Becca knows going in: the story facts (the daily "the
catalog says it's on the shelf" complaint, the three new pages, the
sorting room, Alan and Mira's closing log — fifteen tidy days showing
about 3.8% — and the fall reading-program surge), the data files as
they land on her in-story, and what the screens say. She has NOT been
told the log is broken. Nobody has.

Voice note: Becca likes visible progress — charts before paperwork —
which is exactly the instinct this scenario's trap is built to test.

## Define (compressed — the trap is the story here)

- **T-01 Picker:** five Yes answers, full-DMAIC (training, sorting, and
  audit practice all suspect — no single obvious fix). Prescore pass;
  both intake gates CLEAR (real).
- **T-02 COPQ:** three rows, all conversions done in the basis notes.
  The search-time row is a 3-week desk-log sample, so she scales it to
  the quarter and marks it estimate: 74 searches × 11 min = 814 min,
  ×13/3 → 58.79 h at $26. Replacements 21 × $19.40; holds 66 × 9 min =
  9.9 h at $26. Engine total (real): **$2,193.34** (rows $1,528.54 /
  $407.40 / $257.40). One real flag: `period_consistency` — her
  search row's period string ("Q3 2026 (3-week desk-log sample, scaled
  to the quarter)") differs from the others' plain "Q3 2026." She reads
  the detail, decides the difference IS the honesty (a scaled sample
  should say so), and leaves the flag standing with the basis note.
  (Note the contrast with Corey's run: the same unit-less Quantity
  field, but her sample-vs-period thinking made her do the arithmetic
  up front. Plausible variance, both logged.)
- **T-03 Charter v1:** written with the only number she has — the
  closers' log. Magnitude **3.8 percent** (period: closing log
  2026-08-10 → 08-26); goal "halve it: 3.8% → 1.9% by 2026-11-30";
  throughput and cancelled-holds guardrails; risks: new pages, fall
  returns surge. All six prescore checks pass (real) — **the suite has
  no way to know this baseline number is broken, and neither does
  Becca. Yet.**
- **T-04 SIPOC:** chute → check-in → sorting room → cart → shelf →
  audit. **T-05 VoC:** the daily complaint verbatim; binary CTQ C1 —
  found-where-the-catalog-points, pass/fail. Prescore pass; gate
  `define_to_measure` CLEAR (real).
- **T-06 Process map** (walked with Ruth): the step that jumps out is
  s3 — "Page sorts AND shelves at the shelf," an armload of books being
  interleaved into rows, fed by carts that leave the sorting room in
  rough order only. Defect points on s2/s3; wastes noted. All nine
  prescore checks pass (real).

## THE TRAP, step 1 — the bait goes in clean

Define is done and Becca wants her baseline chart. She has fifteen tidy
days of Alan and Mira's closing log — dates, items shelved, misshelves,
who logged. It looks perfect. She uploads `prelog-daily.csv` through
T-11's Import tab.

Engine preview (real): 15 rows, four columns, types inferred right
(`items_shelved` numeric, `misshelves_logged` numeric), quality scan
**completely clean** — 0 missing values, 0 non-numeric, 0 duplicates.
She confirms the types and saves; the dataset gets its SHA-256.

**What the screens said at this moment:** nothing warned her. The
import screen's job is schema and quality, and the bait is
schema-perfect — exactly as the scenario intends ("it would feed a
p-chart without a single schema complaint"). The one line that could
have snagged her sits in the import helper's what-good-looks-like list —
*"The operational definition passes the two-people test as written"* —
but it reads as paperwork this early, and she hasn't opened the
Collection Plan tab yet. The `logged_by` column scrolls past unread.

## THE TRAP, step 2 — the tool literally named "Baseline" (STALL 1)

The Measure rail lists **"T-13 Baseline: Stability then Capability."**
That is the word she wants, so that is where she goes. The form asks for
a dataset, a **numeric column**, and spec limits. Her data is pass/fail
books, but the closest numeric column is `misshelves_logged`, and the
closest thing she has to a "limit" is her charter target — so she picks
the column, types **1.9** in USL (her target percent), and ticks the
operational-definition checkbox to unlock the run button ("sure,
whatever that means" — the exact tick-to-unlock move the baseline
helper's field guidance calls out as the bad example).

Engine (real, HTTP 200): it RUNS. `gate_ok: true`. Descriptive mean
**17.2** (of daily counts), SD 5.81. Stability: *"**not stable — you
don't have a baseline yet**: only 15 points (< 20): limits cannot be
frozen (matrix §4a EXIT-04 companion floor)"*, `exits: ["EXIT-04"]`.
Capability: Cpk **null** (the EXIT-04 suppression), but **Ppk −0.878**
prints, labeled `performance_not_capability: true`, and the sigma block
prints **DPMO 995,780** — of daily misshelve counts against a "USL" of
1.9.

Becca's reaction, verbatim from her notes: "It says my average is 17.2.
17.2 what? My problem is a PERCENT. And it wants twenty of something I
have fifteen of." She closes the screen more confused than when she
opened it.

- Classification: **usability, medium** — T-13 is continuous-only with
  no signpost for attribute projects (failure log FL-05), and it
  computed performance/DPMO numbers against a semantically meaningless
  spec limit without any range sanity note (FL-06). The engine's math
  is correct for the inputs given, and its two honesty devices (the
  EXIT-04 "you don't have a baseline yet" line and the
  performance-not-capability label) both fired — but nothing told her
  the real problem: *wrong tool for her data type*.

## THE TRAP, step 3 — she finds the p-chart and tries to freeze the bait

Scanning the rail for anything chart-shaped, she spots **"T-21 Control
Charts (I-MR, p)"** down in the Control phase. The helper's opening
matches her data at last: *"attribute data gets the
defectives-or-defects question first, because pass/fail UNITS fit a p
chart."* Books pass or fail: defectives. She builds the chart from the
pre-log — 15 daily subgroups (n = items shelved, defectives = misshelves
logged) — and clicks freeze, because that is what the screen offers a
baseline-seeker.

Engine (real, **HTTP 422**): *"**EXIT-04 companion floor (matrix §4a):
freezing/recalculating limits needs >=20 points and no default-rule
(rule 1 or 4) signal in that exact window — got 15 point(s)** … The
chart runs diagnostically (no frozen limits, no stability claim) until
this window clears."*

She re-saves without the freeze. Engine (real): the **diagnostic bait
chart saves cleanly** — `frozen_at: null`, `p_baseline: null`, no
signal log — and the prescore strip shows **all six checks green**,
including `frozen_limits_present_before_signals: pass` with the detail
*"no frozen limits yet — chart runs diagnostically, no signal log (as
expected)."*

**Record, for the graders — what the screens did and did not do:** the
ONLY thing that refused the bait baseline was the 20-point freeze
floor. Nothing on T-21 — helper, prescore, or engine — mentions the
measurement check; T-21 and T-10 do not consult the T-12 verdict at
all, and the gate that does (`measure_capability_language_requires_
msa_pass`) only fires when a T-12 exists and reads "fail" — a project
that has never run T-12 sails through. gates.py documents that choice
in code comments ("a project that never ran T-12 is a softer, different
concern … isn't modeled as its own gate this milestone"). **Had the
closers' log carried 20+ days, this chart would have frozen a ~3.8%
baseline with a green prescore strip.** Failure log FL-07 — the run's
most important finding.

Becca's plan at this moment, quoted from her notes: "Fine. The log gets
five more days and then I freeze it." **The trap is still armed** — the
floor delayed her; it did not catch her.

## THE TRAP, step 4 — the Stuck button asks the one right question

Waiting five days with nothing to do, unsure whether waiting is even
right, she clicks **"I'm stuck."** The Measure-phase tree (a UI decision
tree, no engine call — quoted verbatim from the app's stuck-tree
content):

1. *"Do you already have a stable, engine-verified baseline number for
   this metric?"* — No (the freeze just refused her).
2. *"Have you collected real process data yet — a check sheet, time
   study, or an imported dataset?"* — Yes (the log is imported).
3. *"Has the measurement system itself been checked yet — test/retest
   repeatability or two-rater agreement (T-12)?"* — …two-rater
   agreement? There ARE two raters. Alan and Mira. Nobody has ever
   checked whether they agree. **No.**

The leaf: **"Check the measurement system — Measurement Check (T-12)"**
with the explanation: *"Real data is in hand, but a baseline built on
an unchecked gauge is a guess wearing a number's clothes. Confirm the
measurement first — the engine blocks capability language until this
passes."*

That sentence is what actually turns her around — not a gate, not a
refusal. She opens T-12, reads the helper's attribute path (*"for
pass/fail judgments, two raters judge the same items independently and
the engine reports % agreement plus kappa … kappa 0.75 or more
acceptable, 0.40 to under 0.75 marginal, under 0.40 fail"*), and the
helper's first common mistake reads like it was written about her
afternoon: *"Skipping the check because the numbers 'look fine.'"*

She takes it to Ruth, who stages the study properly (the helper's
field guidance drives the design she asks for): 50 flagged shelf
positions, 16 of them deliberately mis-placed by Ruth, numbered slips,
Alan walking at 4pm and Mira at 6pm, sheets sealed.

## THE TRAP springs — T-12 round 1: EXIT-02

Becca enters the 50 rows of pass/fail pairs, operator "Ruth Delgado
(ran the study)."

Engine (real): verdict **fail**. **% agreement 70.0, Cohen's kappa
0.3363** (p_observed 0.70, p_expected 0.548, n=50). The result panel's
own note explains the gap that would otherwise read as fine: *"%
agreement alone can flatter a low-defect process by chance — kappa
corrects for that. Both are reported, never one alone."* Seventy
percent SOUNDED okay to her; chance alone predicts ~55% here, so the
raters are barely better than coin-adjacent — and the verdict banner
says so in the fail wording: *"Fail — attribute agreement (kappa) is
outside the acceptable range. Stop and fix the measurement first."*

The EXIT-02 panel attaches (real payload, quoted): **"EXIT-02 — stop,
fix your measurement first"** / *"Stop — fix your measurement first.
Capability-claim language is blocked, and downstream results render as
'unreliable — measurement system failed' until this is fixed."* /
**Next step:** *"Rework the operational definition / gauge (T-11), then
re-run this check (T-12)."*

Gate check (real): `measure_capability_language_requires_msa_pass` →
**HARD_BLOCK** — *"Measurement check failed (EXIT-02): fix the
measurement system and get a passing T-12 re-run before capability
language is trusted."*

And now the pre-log makes terrible sense. Ruth reads the split items
off the study sheets: Alan passed 13 placements Mira failed —
transpositions, series-order oddities, books lying flat — his private
rule being "out of the bay is wrong, one slot over is fine, patrons
scan." Becca finally looks at the `logged_by` column she scrolled past
in step 1: Alan's closing days log ~3.0%, Mira's ~4.8%. **Two people,
two definitions, one spreadsheet.** The 3.8% was never a number about
the shelves — it was a number about who was closing.

**The run stops here.** No baseline, no more charting, the bait chart
abandoned in version 1. The charter's 3.8% is now known-contaminated
(reconciled properly once a real baseline exists — see below).

## Recovery — exactly what the exit told her to do

The EXIT-02 routing line is her literal to-do list: rework the
operational definition in T-11, then re-run T-12.

**T-11 (2026-08-28):** Ruth, Alan and Mira hammer out the four written
shelving-defect rules (the in-story definition fix — exact call-number
order with ANY out-of-order placement failing; juvenile series by the
posted series-title-then-volume scheme; oversize in the oversize section
WITH a dummy marker at the home slot; flat-on-top is not shelved).
Becca types them into the plan's what-is-measured and how fields — the
op-def panel's subtitle (*"Would two different people measuring this get
the same number?"*) finally has an answer she can defend, so the
two-people box gets checked honestly. Data type
`attribute_defective`; stratification by section; the sampling scheme
written down (subgroup = one day's audited books across the rotating
ranges); the pre-log demoted in the bias note to what it always was.
Sample-size panel (real): proportion, planning 5%, ±1.5 points, 95% →
**n = 811**; ~21 audit days at ~65/day ≈ 1,380 clears it. Prescore: all
six pass.

**T-12 round 2 (2026-08-29, real):** fresh 50-position planted set, same
raters, blind to round 1. Verdict **acceptable — kappa 0.8777, %
agreement 94.0**, `exit02: null`. The three remaining splits stay
splits, logged for the next definition review.

Gate re-check (real): **CLEAR**. The baseline window may open — and only
now.

## Measure — the honest baseline (higher than the bait)

Twenty-one audit days (2026-08-31 → 09-24) under the written rules.
Becca imports `baseline-audit.csv` (real preview: clean), sums the
(date, section) rows into daily subgroups per the plan's written
sampling scheme, and re-does the chart **as version 2 of the same T-21
artifact** — the bait chart stays in version 1 as the recorded dead end,
with the v2 note saying so.

Engine (real): freeze succeeds — **p̄ = 0.065265 (90 of 1,379), 21
subgroups, per-day limits, zero signals, frozen 2026-09-25**. The worst
day — 2026-09-10 at 11.7% (9 of 77) — sits inside its own UCL of 15.0%,
because every point carries its own limits when the audit n varies.
Stable at a bad level. All six prescore checks pass.

**6.5%, not 3.8%.** The broken gauge had been hiding roughly two-fifths
of the problem. Becca's note: "If we'd frozen the log, we'd have set out
to halve a number that was never true, hit '1.9%', and celebrated while
one book in fifteen stayed lost."

**T-10 Yield/DPMO (real):** one opportunity per book (her justification
field: the four rules are ways to fail ONE judgment, not four
opportunities — she'd noticed inflating opportunities would flatter the
number). **DPMO 65,265, sigma 3.01, "with 1.5σ shift" labeled**; FPY
93.47%; RTY null — `steps_in_series: false`, no serial claim. Prescore:
`opportunity_inflation_justified: pass`.

## Measure — check sheet, Pareto

**T-08:** the audit's per-book defect tags, transcribed by type through
the Transcribe panel (counts 44 / 29 / 10 / 7, source note required and
given). Prescore (real): three pass, one flag —
`entries_carry_full_strata`: her transcribed counts don't carry
per-entry section values (the strata field exists but rolled-up counts
can't fill it). She accepts it: the section split she needs lives in
the audit dataset itself. (Same transcribed-mode limitation as S-1 —
failure log FL-04.) Export to dataset (real).

**T-14 Pareto (real): "out-of-order within bay" 44 (48.9%) + "wrong
bay" 29 (cumulative 81.1%) are the flagged vital few**; series-by-author
10, oversize/flat 7. Her read: "It's ordering errors, overwhelmingly —
not lost-in-the-wrong-room errors. That points at wherever ordering
happens." (Which the map already answered: at the shelf, from
rough-sorted carts.)

## The charter reconciliation (logged edit, version 2)

The baseline helper's checklist demands it and her own numbers force
it: the charter says 3.8%, the engine says 6.5% — materially different.
Charter v2 (real save, new version on the same artifact): magnitude
**6.5% (90 of 1,379, audit window 8/31–9/24)**; goal restated as
halving the AUDITED rate (6.5% → ≤3.26%); and the pre-log kept in the
record as history with its caveat named — the notes field says exactly
why the number moved: *"the closers' log (3.8%) was counted under two
private definitions and hid roughly two-fifths of the problem."*
Prescore (real): all six checks pass.

The history is part of the story, labeled as such — not deleted. Both
charter versions live in the artifact's version list.

## Analyze — T-17 section screen, T-15 fishbone

**T-17 (screen, declared not-primary):** "Does the rate differ by
section?" Contingency 2×3 from the audit rows. Engine (real):
**chi-square 19.90, df 2, p = 4.8e-05, Cramér's V 0.120** (CI honestly
"not computed" with the reason printed), Cochran conditions clean.
Adult 19/553 (3.4%), juvenile 46/439 (**10.5%**), nonfiction 25/387
(6.5%). Her read: it rides where the sorting is hardest — juvenile's
long same-author runs and series conventions — a method-and-knowledge
shape, not a which-page-is-sloppy shape. (The audit can't attribute
marks to individual pages anyway; cart sign-outs don't survive to the
shelf — and the fishbone keeps that honesty.)

**T-15 fishbone (real, saved in one pass — she'd already learned the
evidence discipline the hard way at T-12):** verified — sorting happens
at the shelf (check sheet: the transposition-dominated Pareto), carts
leave in rough order (map walk: "order is created at the worst possible
place"), conventions unwritten until 8/28 (the definition fix itself is
the evidence, plus juvenile's 10.5%). Candidates with empty evidence
slots — lighting, cart overload. Ruled out with evidence retained —
rater drift (round 2 kappa 0.878; quarterly re-run planned) and shift
mix (rotation samples both shifts; the section split explains the
pattern). The Alan/Mira 3.0%-vs-4.8% gap goes in the notes as the
measurement lesson, explicitly not a people finding. Prescore (real):
all five pass — including *"5/6 branches carry a cause."*

## Improve — matrix, the second EXIT-10, primary test, proof

**T-18 (real):** weights declared before scores. Ranked: **1.
pre-sorted carts + posted standard (weighted 4.5)** — sorting moves to
a bench with both hands free and the standard on the wall, ~$60 in
dividers and flags, straight at the verified root; 2. retrain-everyone
(2.75) — "fades without a standard to train TO"; 3. double-check every
cart (2.0) — permanent labor at the symptom. `unlinked: []`.

**T-19:** her first draft adds *"also run the December series-convention
refresher during the same window — kill two birds."* Engine (real, HTTP
422): **EXIT-10, more than one change described for a single pilot** —
the same full refusal text Corey got, ending "Remove the extra entry
from `changes` (got 2)." The refresher goes back on the implementation
plan. Clean pilot saves (real, prescore all pass): one change,
threshold **settled-window rate ≤ 4.0%** declared 2026-09-25 (before
the 09-28 go-live), falsification line ("two settled weeks above 4.0%
and the carts go back"), confound declared with direction (fall
reading-program volume "can push the rate UP, it can't fake a win").

**T-17 primary (real):** two-proportion z, baseline 90/1,379 (6.53%) vs
settled weeks 19/753 (2.52%): **z = 4.011, p = 6.0e-05, risk
difference +4.00 points, CI [+2.18, +5.69]** (Newcombe method named),
floors printed and cleared.

**T-20 proof, full 24-day window (real):** daily audited rates weighted
by audit n. Verdict headline, quoted: *"**Threshold met, as declared**:
Audited misshelve rate (charter C1) = 0.025557 vs 0.04
(lower_is_better). Improvement shown, but a reported confounder
**weakens** this proof: season: Reading-program returns pushed volume up
through October — could only push the rate up, not fake the win.;
demand: Same volume effect."* Gap: recovered 0.0397 of the 0.0326
halving gap = **121.7%, remaining −0.0071, goal_met: true**, next-cause
pointer to the conventions/refresher. Guardrails: throughput 34.2 →
33.6 (`moved: "worse"`, but `material_worsening: false` — inside the
declared 10%), holds-cancelled 5.1 → 2.3 (improved). (The proof's
internal before/after check routed the daily rates to a Welch t —
t = 5.775, p = 2.4e-06 — while her declared primary z-test lives in
T-17; both real, both recorded.)

## Control — the chart's whole story on one artifact, 5S, the plan, the SOP

**T-21 v3 — extend, no re-freeze (real):** the 24 after-days appended
onto the frozen baseline limits. Engine: **exactly one signal — rule4,
indices 21–44, side "below"** — twenty-four consecutive points under
the old center. Prescore flags it by name:
`signal_acknowledgment_completeness` — *"1 of 1 fired signal(s) are not
yet acknowledged."*

**v4 — acknowledge (real):** her response note: "That run below the old
center IS the pre-sorted carts working… Keep the change; recalculating
limits is next, as its own logged step." All six checks pass.

**v5 — logged recalculation (real):** on the 24 post-window days alone,
reason recorded ("…moving the center to the new level so the chart can
catch backsliding from THERE"). Engine: **new p̄ 0.025557**, per-day
limits, recalculation_log now two entries (initial freeze + reasoned
recalc). All six checks pass. Version history v1→v5 IS the limits
story: bait (diagnostic, dead), audit freeze, signal, acknowledgment,
recalc.

**T-23 5S (real):** three scored rounds on the sorting room — 11 → 16 →
19 of 25, each round's lowest category carrying an action, schedule set.
One honest flag stands: `photos_present` (*"physical state should carry
the score"*) — photos are on the branch camera, not attached; she notes
it and leaves it. **T-22 (real):** four monitored items — the rate, the
throughput guardrail, the method itself (carts checked at the door),
**and the definition (quarterly kappa re-run)** — each with an OCAP
whose first steps check the METHOD before the people; the kappa OCAP's
escalation line: "Kappa under 0.40 — that's the EXIT-02 band again."
Training rows include the December refresher as scheduled-not-done.
Plan health (real): no ownerless items, not theater; Ruth accepted
2026-11-04. All eight prescore checks pass. **T-24 SOP (real):** the
sorting-room standard + the four rules, three steps marked
changed-from-prior. All four checks pass.

## Wrap — T-25 A3 (the measurement stop told as a finding)

Panels v1: the stop is the centerpiece — background carries the log's
~3.8% with its caveat; current-condition tells the round-1 fail, the
fix, round 2, and the baseline that came back HIGHER; lessons panel
says stopping "felt like losing two weeks" and was the only reason the
after-numbers mean anything.

Engine prescore on v1 (real): the same three flags Corey hit —
realized-benefits reference missing, all six phases' tollgates
unanswered, "0 lesson(s) recorded… a lessons panel of only wins is not
lessons." (Same discoverability gap, second persona — FL-10.)

The fixes (all real): a COPQ re-run (`bl-copq-after`) over the 4-week
after window — searches 31 × 11 min, one replacement, holds at
2.3/week → engine total **$202.96**, against her stated Q3-rate 4-week
equivalent $676.26; the realized-benefits block computes (real)
**realized-to-date $473.30, net of the $60 fix cost $413.30** — no
annual projection claimed. All 18 tollgate questions answered in her
own words (Measure-2's answer: "It FAILED first — kappa 0.336, EXIT-02,
hard stop… The stop is why the baseline is believable"); the Analyze-3
FMEA question answered honestly with the N/A reasoning (uniform
severity — every misshelve is the same findability failure). Lessons:
two went-wrong entries (the near-baselined broken log; 70% agreement
sounding fine until p_expected 0.548 was printed) and the $60-fix win.
Open items with owners: the after-Pareto's remaining within-bay errors
(December refresher, Ruth) and the quarterly kappa re-run (Ruth).
`project_status: closed` — close check (real): not blocked.

Engine (v2, real): **all six prescore checks pass.** Objectives verdict
(real): recovered 121.7%, remaining −0.0071, "Goal met — route to
Control."

## Did the SUITE force the honest path? (the question this run exists to answer)

The spec's honest outcome — EXIT-02 → definitions fixed → round 2 →
baseline on audit data — **happened, and the suite's own surfaces drove
every turn**. The chain, with the deciding screen text:

1. **The freeze floor** (engine 422): *"freezing/recalculating limits
   needs >=20 points … got 15"* — bought time; without it a frozen bait
   baseline exists by step 3.
2. **The Stuck button's Measure tree** (UI): *"Has the measurement
   system itself been checked yet — test/retest repeatability or
   two-rater agreement (T-12)?"* → *"a baseline built on an unchecked
   gauge is a guess wearing a number's clothes"* — the actual catch.
3. **T-12 + EXIT-02** (engine): kappa 0.3363 fail, *"Stop — fix your
   measurement first…"*, gate **HARD_BLOCK** — the stop with teeth,
   and a routing line that doubled as the recovery plan.

**But the honest answer to the spec's question is: forced only once she
got to T-12.** Steps 1–2 are soft. The floor is about point count, not
measurement trust — 20+ days of bait would freeze. The stuck tree only
speaks when clicked. T-21/T-10 never consult the T-12 verdict, and no
gate models "no T-12 has ever run" (a documented milestone decision in
gates.py). A hastier persona with a longer pre-log reaches Analyze on a
broken 3.8% baseline with every strip green. The suite caught THIS
runner by design-plus-one-click-of-luck; the failure log (FL-07) says
what would make the catch structural.

Also recorded honestly: the graders' trap criteria are all clean here —
no p-chart/capability/DPMO/test was built on `prelog-daily.csv` beyond
the unfrozen diagnostic view (retained in v1 as the recorded dead end),
no baseline opened before the passing T-12, no rater-averaging
workaround, no hand-edit of the round-1 verdict.

## Stalls and catches — the full list

| # | Where | What happened | Resolution | Class |
|---|---|---|---|---|
| 1 | T-13 | Attribute project fed counts + a percent "USL" into the continuous baseline; meaningless mean 17.2 / Ppk −0.878 printed | Recovered by rail scan to T-21 (no on-screen signpost) | usability, medium (FL-05, FL-06) |
| 2 | T-21 | Tried to freeze the bait; 422 floor refusal; diagnostic bait chart saved all-green | Floor delayed her; plan became "wait 5 more days" — trap still armed | validity-adjacent gap (FL-07) + usability (FL-08: T-21 helper frames post-Improve only) |
| 3 | Measure, adrift | "Wait for more log days" as the working plan | Stuck button → T-12 leaf — the decisive catch | suite catch (with FL-11: the tree's baseline leaf itself is not data-type aware) |
| 4 | T-12 round 1 | kappa 0.3363 FAIL, EXIT-02, gate HARD_BLOCK | Followed the exit's routing verbatim (T-11 rules → round 2 pass) | **named exit, honest path — the pass-bar beat** |
| 5 | T-02 | period_consistency flag on the scaled-sample row | Accepted with reasoning | flag accepted |
| 6 | T-08 | Transcribed counts can't carry per-entry strata | Accepted; splits live in the dataset | usability, low (FL-04) |
| 7 | T-19 | Bundled the December refresher | Engine 422 EXIT-10; split | suite catch |
| 8 | T-21 extend | rule4 signal unacknowledged | Prescore flag named it; acknowledged in her words | suite catch |
| 9 | T-23 | photos_present flag | Accepted (photos exist off-app) | flag accepted |
| 10 | T-25 | Tollgates/lessons/realized blocks invisible until flagged | All fixed in v2 per flag details | usability, low (FL-10) |

Hard stalls: **none**. Engine numbers wrong for their inputs: **none
observed** (the T-13 flail numbers were correct arithmetic on
semantically wrong inputs — that distinction is FL-06's whole point).

## Phase-by-phase honest outcome (facts for the graders)

- **Define:** charter v1 carried the only number that existed (the
  log's 3.8%) — later reconciled by logged edit, history retained;
  COPQ $2,193.34 engine-computed with the scaled sample marked
  estimate; binary CTQ; boundaries check-in-to-audited-shelf.
- **Measure (the pass-bar phase):** the trap was played straight and
  the run STOPPED at EXIT-02 — kappa 0.3363/70% (both printed, chance
  level 54.8% printed), gate HARD_BLOCK; recovery executed as ground
  truth defines it (written rules into T-11, round 2 kappa 0.8777
  acceptable); baseline only then, on audit data: p̄ 0.065265, 21
  subgroups, stable, frozen 2026-09-25; DPMO 65,265 / σ 3.01
  (convention labeled); vital few 81.1%. The bait was never frozen and
  never fed a downstream number.
- **Analyze:** chi-square screen (19.90, p=4.8e-05, V=0.120, juvenile
  10.5%) declared as a screen; verified causes with enforced evidence;
  rater drift and shift mix ruled out with evidence retained; the
  Alan/Mira gap kept as a measurement lesson, not a people finding.
- **Improve:** one change (EXIT-10 refused the bundle); threshold
  declared 9/25 before the 9/28 go-live; primary z = 4.011 (p =
  6.0e-05, risk difference +4.00 points CI [+2.18, +5.69]); proof
  verdict met-but-weakened with the confound's direction stated; gap
  121.7% recovered; guardrails inside their declared bands.
- **Control:** the limits history on one artifact — bait (diagnostic,
  v1), audit freeze (v2), the improvement arriving as an acknowledged
  rule-4 run on frozen limits (v3–v4), logged recalculation to p̄
  0.025557 (v5); the goal line never a control limit; 5S 11→16→19;
  the plan monitors the method and the definition (quarterly kappa);
  owner accepted 2026-11-04.
- **Wrap:** the A3 tells the stop as method; realized benefits from
  the COPQ re-run over the stated 4-week window ($473.30 realized,
  $413.30 net of the $60 fix, engine-computed); no annual claim; 18/18
  tollgates; two went-wrong lessons; open items owned; close taken,
  unblocked.
