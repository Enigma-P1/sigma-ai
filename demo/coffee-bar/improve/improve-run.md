# Improve run — the recorded engine verdicts

Not an artifact: this is the recorded result of running the Improve phase
through the live engine, `baseline-run.md`'s convention continued. Every
artifact in this folder was POSTed to the running engine and accepted (200),
every computed number below is pasted from an engine response, and the
artifacts that carry computed blocks (`solution-matrix.json`,
`proof-round1.json`, `proof-round2.json`) are the engine's own echoes —
scores, rankings, test statistics, gap arithmetic, and verdicts are
server-computed on validate, which is what lets the prescore tamper checks
re-derive and match them, the same property `analyze/hypothesis-run.json`
ships with.

## Setup: the project the runs live in

Project `coffee-bar-demo-ic` (`POST /project/create`), seeded with the
Define/Measure/Analyze demo artifacts as prerequisites — charter, COPQ,
SIPOC, VoC/CTQ, collection plan, check sheet, time study, process map, MSA,
fishbone, FMEA, daypart hypothesis run — each saved v1 through
`POST /project/{id}/artifacts/{tool}`. `wait-times.csv` saved as project
dataset `9b1b8c167bbf45079f5c6de910dd31f0`; the engine's stored sha256
(`6d31a43f…c72dc0`) matches the hash `baseline-run.md` recorded in August,
so the before-window is bit-identical to the file the baseline verdict came
from. Re-running `POST /stats/baseline` on that dataset (USL 5.0,
operational definition confirmed) reproduced the anchor exactly: mean
8.4083, sd 1.0418, stable (0 signals at n=120), Cpk −1.1398, measurement
check consulted (T-12 verdict "acceptable" — capability language
permitted). The project-level cross-checks
(`POST /prescore/cross/coffee-bar-demo-ic`) all pass: charter business
impact reconciles with the COPQ engine total (16084 vs 16084, 0.0% off),
and the 5.0 goal is a genuine improvement over the measured baseline.

## T-18 — the ranked fix list

`POST /artifacts/T-18/validate`, then saved v1. The matrix carries three
candidates, every one linked to a verified T-15 cause, with criteria and
weights declared (09:40) before any score was entered (11:10) — the
timestamps are in the artifact. The engine's ranking, pasted:

- **rank 1: sol-batch-steam** — weighted total 4.25, quadrant `quick_win`
  (impact 4 / effort 2), linked to c-batch-locked + c-queue
- **rank 2: sol-grinder-backup** — 3.5, `quick_win` (3/2), linked to
  c-grinder
- **rank 3: sol-second-head** — 3.0, `major_project` (5/5), linked to
  c-one-head + c-station-serial — the highest impact rating on the board
  and last anyway, because a ~$12k machine loses to a $40 method change on
  cost, effort, and speed; ranked and kept as the escalation, not picked

`unlinked: []` — nothing on the board is a guess wearing a plan's clothes.
Prescore (`POST /prescore/T-18`): `unlinked_solution_flags` pass,
`ranked_list_exists` pass (#1 is the batch-steam method change),
`quadrant_vs_rank_consistency` pass (stored scores re-derive from the
stored inputs).

## T-19 round 1 — the EXIT-10 refusal, then the clean plan

Before the clean save, the refusal — run on purpose so the record shows the
engine saying no by name. A draft of the round-1 plan with the grinder
change added as a second `changes[]` entry went to
`POST /artifacts/T-19/validate` and came back **HTTP 422**:

> EXIT-10: more than one change described for a single pilot (matrix §4a
> trigger: "pilot plan declares more than one change"). The Improve loop is
> one-change-at-a-time by design (PLAN §4.1, rubric R-IMP-02 #1): run the
> extra change as its own sequential pilot once this one is proven, declare
> a genuinely inseparable PACKAGE explicitly if the components truly cannot
> deploy apart (R-IMP-02's carve-out — attribution then goes to the package
> only, never a component), or route to the advisor / v1.1 Experiment
> Planner / a human expert for a real multi-factor question. Remove the
> extra entry from `changes` (got 2) before saving.

The grinder change went back to the queue as round 2, and the one-change
plan (`pilot-plan-round1.json`) validated and saved v1: threshold 7.0
declared 2026-08-07T15:45Z (three days before the first pilot morning),
falsification line with teeth ("not below 7.0 over the full 10 mornings →
revert, take the next-ranked fix"), comparison named exactly (the frozen
n=120 baseline), inclusion honest about convenience (one site, the crew we
have, window placed to end before semester). Prescore: all three checks
pass — `threshold_before_data_advisory` (entry order only, the honest
caveat printed), `falsification_substance_heuristic`,
`checklist_completeness` (all five confounder notes filled).

## The round-1 window, verified before the proof

`after-round1.csv` saved as dataset `7fd6229c7d514253bdb67f950003e68a`,
then `POST /stats/baseline` (USL 5.0): **mean 6.1983, sd 0.8660, stable
true** — "stable: 120 points, no default-rule signal" — I-MR limits
3.559 / 6.198 / 8.838, normality `no_concern` (AD 0.4443, p ≥ 0.15), Cpk
−0.454. Generation, seed (36), and acceptance checks are in
`after-round1-note.md`; the engine's verdict is the binding one.

## T-20 round 1 — proof, gap, and the loop firing

`POST /artifacts/T-20/validate`, saved v1 (`proof-round1.json` is the
echo). The request carries the same metric/operational-definition/
measurement-system refs as the baseline — one copy each, so a switched
yardstick cannot happen — before = the baseline dataset's 120 values,
after = the full pilot window, threshold echoed verbatim from the plan.
The engine's verdict, pasted:

- **Route:** `welch_two_sample_t`. **t = 17.8706**, df = 230.31,
  **p = 2.15e-45**, `significant: true`; **Cohen's d = 2.31**, 95% CI
  [1.98, 2.63] — a very large, unambiguous shift.
- **Side-by-side stability:** before stable (Cpk −1.1398), after stable
  (Cpk −0.4540) — the improvement did not buy stability at the price of a
  drifting process, and the after-window is still not capable.
- **Threshold, as declared:** "Threshold met, as declared:
  handoff_minutes … = 6.19833 vs 7 (lower_is_better)." `weakened: false`
  — all five confounders re-answered "no" against recorded actuals
  (counts 44–52/peak, mean 47.6, vs 48 at baseline; same crew; same
  instrument).
- **Guardrails:** remake rate 3.6 → 3.4 per 100 (`improved`, −5.6%);
  labor hours 8.65 → 8.40 (`improved`, −2.9%). No material worsening —
  no tradeoff sentence.
- **The gap block, the loop's decision point:** original gap **3.4083**
  (measured baseline 8.4083 against the 5.0 goal), recovered **2.2100**
  (**64.8%**), remaining **1.1983**, `goal_met: false`. Loop verdict,
  verbatim: *"Gap remains (1.19833, 65% of the original gap recovered) —
  route to the next-ranked verified cause: 'Sour or channelled shots get
  dumped and re-pulled at the grinder-dose step, restarting the drink and
  stalling every cup behind it' (via solution 'Backup grinder + dose
  dial-in routine', rank #2), one change at a time."*

The decision recorded is **loop**, not close — 64.8% recovered is the
method working, and the remainder routes to the #2 ranked fix. Prescore:
all five checks pass, including `gap_arithmetic_consistency` (stored gap
re-derives from the stored inputs) and `confounder_echo_present`.
Implementation beyond the pilot followed the proof: batch-steam +
sequencing became the standard on every morning from 2026-08-24, the
documented state round 2 measures from.

## T-19 round 2 — the next-ranked fix, one change again

`pilot-plan-round2.json` validated and saved v1, designed 2026-09-03 with
the threshold (5.5, lower is better) declared at 15:00 — five days before
the first pilot morning. One change, declared as one dosing method whose
parts cannot deploy apart (the mid-peak swap needs the standby unit; the
unit is pointless without the dial-in routine) — attribution to the method
as a whole, never a component, the R-IMP-02 package reading stated up
front. The comparison window is the round-1 pilot window — the implemented
current state — so the test isolates what this change adds; the cumulative
goal check stays with the original baseline in the proof's gap block. The
honest part of this plan is the confounder checklist: **season and demand
are declared "yes" before the pilot runs** — fall semester began
2026-08-31, order counts already ~53–57/peak — with the direction stated
(more load lengthens queues; the confound can mask a win, not manufacture
one). Prescore: all three checks pass.

## The round-2 window, and the capability run

`after-round2.csv` saved as dataset `314125ca183d4f89a9442a2f2408f485`,
then `POST /stats/baseline` — the same route the Measure baseline used,
same USL 5.0, run on 2026-09-21. The engine's verdict, pasted:

- `stable: true` — "stable: 120 points, no default-rule signal"; I-MR
  3.0285 / 4.8992 / 6.7698, MR UCL 2.2979, zero rule-1/rule-4 signals.
- Descriptive: mean **4.8992**, sd 0.6582, median 4.9, min 3.4, max 6.6.
- Normality `no_concern` (AD 0.3591, p ≥ 0.15).
- **Capability: Cpk 0.0539, Ppk 0.0511, dpmo 439,120** — the model puts
  **43.9%** of orders past the 5.0-minute line at this center and spread;
  in the sample itself, 46 of 120 (38%) ran over.

That is the number the close does not hide: the mean is under the goal and
nearly half of individual orders still are not. Seed (5) and acceptance
checks in `after-round2-note.md`.

## T-20 round 2 — goal met on the mean, said honestly

`POST /artifacts/T-20/validate`, saved v1 (`proof-round2.json` is the
echo). Before = the round-1 window (the implemented state), after = the
full round-2 window, threshold 5.5 echoed from the plan. The engine's
verdict, pasted:

- **Route:** `welch_two_sample_t`. **t = 13.0841**, df = 222.08,
  **p = 2.23e-29**, `significant: true`; **d = 1.69**, 95% CI [1.39,
  1.98] — the grinder change's own effect, 6.198 → 4.899, isolated from
  round 1 by the choice of before-window.
- **Threshold, as declared:** met — "handoff_minutes … = 4.89917 vs 5.5
  (lower_is_better)."
- **The confound prints on the verdict**, exactly as R-IMP-03 #3 wants:
  `weakened: true`, and the headline carries both declared confounders in
  full — season ("fall semester began 2026-08-31 … the charter's named
  risk, carried on the verdict") and demand ("counts ran 53–58 per peak,
  mean 55.4, vs 48 at baseline … biases against the pilot; it weakens the
  claim without being able to manufacture it"). Improvement shown, proof
  weakened, direction stated — all three travel together.
- **Guardrails, cumulative vs the charter baselines:** remake rate 3.6 →
  2.3 per 100 (`improved`, −36.1% — the grinder fix cuts remakes
  directly); labor hours 8.65 → 8.10 (`improved`, −6.4%). No tradeoff.
- **Stability of the after-window:** stable — no met-but-unstable
  tempering needed; the same window freezes the control chart next
  morning.
- **The gap block:** original gap **3.4083**, recovered **3.5092**
  (**103.0%**), remaining **−0.1008**, `goal_met: true`. Loop verdict,
  verbatim: *"Goal met — route to Control."* `next_cause_ref` is null
  because the loop is done routing: what remains is not a ranked cause,
  it is spread — and that goes to Control and the A3's open items, in
  writing, with the Cpk 0.054 capability run above quoted wherever the
  win is claimed.

Prescore: all five checks pass (`confounder_echo_present` confirms the
weakened sentence is in the headline; `gap_arithmetic_consistency`
re-derives the remainder). Improve closes with numbers against the
charter goal: **met on the mean (4.899 vs 5.0, remaining −0.10), under
semester load, with both guardrails improved and the every-order promise
explicitly not yet met** — and the implemented state (both methods, all
mornings, from 2026-09-22) is what Control monitors.

## Teaching read

The Improve phase is one loop run twice, and the loop's discipline did the
work. Rank the verified causes; fix the top one — and only it, with the
engine refusing the bundle by name when we tried; declare the finish line
before the data exists; let the engine judge the result against exactly
that line; then let the remaining-gap arithmetic decide what happens next.
Round 1 recovered 64.8% and the gap check said *loop*, not *celebrate* and
not *despair* — partial recovery is the expected shape of a single fix.
Round 2 closed the remainder and the same arithmetic said *Control*. Two
things kept the record honest at the moment it was most tempting to round
up: the semester confound rode into the round-2 verdict instead of being
managed out of it, and the capability run was made and quoted at the point
of maximum good news — mean promise met, every-order promise not, Cpk
0.054. The next phase inherits both sentences, not just the happy one.
