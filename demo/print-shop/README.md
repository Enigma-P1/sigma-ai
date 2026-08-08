# Print Shop demo — the attribute data path

This is the suite's second reference thread (PLAN §4.4): a campus print
shop where ~8.6% of orders failed the customer's first look — wrong paper
stock, crooked trim, ink smudge, wrong quantity — carried through the
tools whose **attribute** path genuinely differs from the continuous one
the Coffee Bar already demonstrates: binary CTQ, proportions sample-size
arithmetic, two-rater kappa instead of test/retest repeatability, a
variable-n p-chart baseline instead of I-MR, FPY/RTY/DPMO instead of
Cp/Cpk, a two-proportion z instead of Welch's t, and a frozen-then-
recalculated p-chart holding the gain. **The scope rule, applied**: this
is deliberately not a second 25-tool thread. Process map, spaghetti, time
study, fishbone, FMEA, solution matrix, pilot plan, control plan, 5S,
standard work, and A3 behave identically on attribute data and are not
duplicated here — the Coffee Bar is their reference; this README carries
the Analyze/Improve narrative they would hold, in prose, so the
before/after still has its story. Everything that did ship was POSTed to
the live engine and accepted; every computed number is the engine's
(`print-shop-run.md` is the session transcript, and the two refusals in
it — a prescore hard_flag and a 422 — were run on purpose).

`define/` routes and frames the defect-rate problem. The picker's five
Yes answers send it to full DMAIC — no single obvious fix when intake,
prepress, press, and finishing all feed the reprint shelf. The VoC tree
lands on the thread's defining object, a **binary CTQ**: an order either
survives its first presentation or it does not (C1, pass/fail against
four named checks, tracked as the rejected proportion; turnaround is
kept, demoted to guardrail, as C2). The charter carries that CTQ as a
proportion metric — baseline 0.086 from the Q2 reject log, target 0.043
by 2026-09-30, halve it — with the term-start surge and rater-drift named
as risks, and the COPQ worksheet prices the reprint economy ($1,544.40
materials + $3,444.00 press/operator time + $499.50 rush courier +
$442.25 credits = **$5,930.15 for Q2, engine-computed**; ×4 =
$23,720.60/yr on the charter, basis stated, 0.0% apart from the COPQ
total on the project cross-check).

`measure/` is where the attribute path earns its keep. The sample-size
panel's proportion calculator returns **n = 1399** where the coffee bar's
mean calculator needed 117 — so the plan is a census: every order, both
shifts, 21 service days (1,566 achieved). Before the window opened, the
measurement check ran as **two-rater kappa** — round 1 landed marginal
(κ 0.6067, 86% agreement: "smudge" and "at-2mm trim" were being judged
from memory, not from a definition), the definitions were tightened into
the collection plan (arm's-length rule, exactly-2mm-passes rule), and
round 2 passed (κ 0.8645, 96%) — both rounds shipped as versions of one
artifact: verdict obeyed, definition fixed, check re-run, the measurement
discipline the continuous MSA teaches, in attribute form (`msa-note.md`). The baseline is the p-chart path (matrix
2.4.3): daily subgroups with n varying 58–90, per-day limits, **p̄
0.086207 frozen from 21 signal-free subgroups** — stable at a bad level,
in proportions — with capability language from T-10: per-step first-pass
counts off the job travelers roll to **RTY 84.27%** against the 91.38%
the customer sees and the ~99.8% final yield that hid the problem
(reprints are the hidden factory), and the DPMO block reads **22,190
DPMO / sigma 3.51, shift convention named**, its four opportunities
justified verbatim as the four checks. The check sheet tallies the 139
failed-check marks by type and shift; through `to-dataset` and the
engine Pareto, **trim misalignment (48.2%) + wrong paper stock (84.2%
cumulative) are the verified vital few** (`baseline-note.md`).

`analyze-improve/` holds the tests, the proof, and this thread's
flawed-then-fixed pair. The chi-square screen (declared before the split
was cut; Cochran's rule engine-checked, one light cell within the rule)
reads χ² 0.61, p 0.895, Cramer's V 0.066 — the defect mix is the same on
both shifts, so the causes are process-shaped, not people-shaped. **What
the fishbone and pilot would hold** (prose here, per the scope rule, and
their method is the Coffee Bar's): the fishbone's verified causes would
sit under Methods and Materials — trim failures trace to jobs reaching
the cutter without a signed-off imposition (fold/bleed set per operator
habit), wrong-stock failures to unlabeled tray loads between jobs — with
the Pareto shares (48.2% / 36.0%) and the traveler rework counts as
their evidence pointers, one 5-Why running proof-approval → imposition →
no written pre-flight; ink and quantity would stay honest candidates in
the tail. The pilot plan would declare **one change**: a prepress
pre-flight checklist (imposition, bleed, stock SKU confirmed against the
ticket) **with labeled paper trays as its materials half**, threshold
0.05 declared 2026-08-01, falsification line "two settled weeks not
below 5% → revert and take the next cause." That named fix went live
2026-08-03; the record of it is the engine's. The pre-declared primary
test — **two-proportion z**, baseline 135/1566 (8.62%) vs settled weeks
one–two 30/884 (3.39%), floors printed and cleared — reads **z 4.96,
p 7.1e-07, risk difference +5.23 points, CI +3.32 to +7.03**
(`hypothesis-note.md`). The proof on the full 24-day window lands
**threshold met as declared** (0.0368 vs 0.05) and **weakened: true** —
the term-start surge is on the verdict with its direction stated (more
load pushes the rate up; it can mask the win, not manufacture it) — with
both guardrails improved and the gap block closing the loop: **recovered
114.3% of the halving gap, remaining −0.006, "Goal met — route to
Control."** The pair: `chart-flawed.json` charts defect *marks* through
the p route and the engine refuses with **EXIT-11 by name** (422 quoted
in `teaching-note.md`, the same guard shown firing on the test
selector); the corrected chart, on defective *orders*, is the control
phase's.

`control/` closes the way an attribute thread should: on the chart, with
the limits' whole history in one logged field. One artifact, three
versions — the 2026-07-23 baseline freeze (armed that day), the
monitoring close-out where the improvement itself arrives as a **rule-4
signal on the old limits** (thirty consecutive days below center,
starting exactly on the change date; acknowledged with
keep-the-change / no-informal-recenter), and the **logged recalculation**
from the 24-day post-change window: **p̄ 0.037891, per-day limits, zero
signals, armed**, the term-start surge week inside the window and inside
the limits — load went up, the rate held. The charter's 0.043 stays a
goal line on the wall chart and never becomes a control limit; the LCL
floors at zero (no single good day can signal — only the run could, and
did). What is honestly open leaves in writing: ink smudge and wrong
quantity were never targeted by this fix and now carry ~41% of a much
smaller total (28 of the post window's 69 marks, vs 16% of 139 at
baseline) — the head of the next Pareto re-run; and the kappa re-run
cadence guards the definition as staff turn over (`control-run.md`).

The record, by file: `print-shop-run.md` (the engine session, refusals
quoted verbatim) · `define/` picker, charter, voc-ctq, copq ·
`measure/` orders.csv + orders-note (seed 90, generator embedded),
collection-plan, msa-round1/2 + msa-note, check-sheet, pareto,
yield-calc, baseline-pchart + baseline-note · `analyze-improve/`
hypothesis-shift, hypothesis-run + hypothesis-note, proof,
chart-flawed + teaching-note · `control/` control-chart + control-run.
JSON files are engine echoes (computed blocks server-stamped, versioned
in project `print-shop-demo`); the notes quote engine numbers and
nothing else. Staff names (Tessa Nguyen, Omar Haddad, Jordan Pike,
Elaine Foster) are fictional, as is the shop.
