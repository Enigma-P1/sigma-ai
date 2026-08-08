# Print Shop run — the recorded engine session

Not an artifact: the recorded result of running the Print Shop thread
through the live engine, the coffee bar's `baseline-run.md` /
`improve-run.md` convention applied to the whole attribute thread. Project
`print-shop-demo` (`POST /project/create`, 2026-06-23). Every artifact in
this demo was POSTed to the running engine and accepted; every computed
number in every note is pasted from an engine response; the two refusals
(a prescore hard_flag and a 422) were run on purpose and are quoted below
verbatim. Where a phase has its own note, this transcript stays brief and
points at it.

Datasets: `orders.csv` saved 2026-07-22 as
`3122dfa39994454090c24e7a857d18f6` (sha256 `b6b0559d…154d9f`, 1,566 rows;
import quality scan: 0 missing, 0 non-numeric, 0 duplicate rows). The
check-sheet export (below) is `c33da44e761b4bf39eecf65a232f8cb7` (sha256
`8eb697fe…740b00`), produced by the engine's own `to-dataset` action, not
by re-typing.

## Define — four saves, clean prescores

`picker.json`, `charter.json`, `voc-ctq.json`, `copq.json` each through
`POST /artifacts/{tool}/validate`, saved v1, prescored clean:

- **T-01**: five criteria Yes with project-specific detail, route
  `full-DMAIC` — `routing_consistency` pass (the schema itself would have
  rejected a No with that route).
- **T-03**: all six prescore checks pass first try — no solution language
  in problem or goal, magnitude number+unit+period (8.6 / % of orders
  rejected at first presentation / Q2 2026), owner named (Tessa Nguyen),
  two guardrail metrics, three risk rows including the term-start surge
  and the rater-drift risk the kappa rounds answer. The metric fields
  carry proportions (0.086 → 0.043) so every downstream tool shares one
  unit.
- **T-05**: `tree_completeness` pass — five sourced statements, three
  needs, two CTQs; C1 is the binary first-presentation CTQ (pass/fail per
  order, tracked as the rejected proportion), primary, linked to the
  charter metric verbatim; C2 (turnaround) is explicitly demoted to
  guardrail.
- **T-02**: engine-computed row amounts — 468 × $3.30 = $1,544.40 reprint
  materials; 164 h × $21 = $3,444.00 press/operator time (`is_estimate:
  true`, basis names the 40-traveler sample); 27 × $18.50 = $499.50 rush
  courier; 61 × $7.25 = $442.25 credits — **engine total $5,930.15 for
  Q2**, ×4 = $23,720.60/yr on the charter, basis stated.

## The sample-size run — proportions change the arithmetic

`POST /stats/sample-size` (proportion calculator, planning p 0.09 from the
Q2 reject log, margin ±1.5 points, 95%): **n = 1399** (n_exact 1398.29,
z 1.96). Set that against the coffee bar's recorded mean-calculator run
(n = 117 at its precision): a defect rate needs roughly ten times the
data for a usable estimate, because each pass/fail row carries one bit.
That number is why the plan is a census — every order, 21 service days,
~1,550 expected — rather than a sample, and why `collection-plan.json`
restates it in its own `sample_size_rationale` with the 20-subgroup
freeze floor alongside.

## Measure — kappa twice, census, tally, export

- **T-12 v1** (2026-06-25): kappa **0.6067**, % agreement 86.0 —
  **marginal**, the engine's frozen 0.40–0.75 band. **T-12 v2**
  (2026-06-27, same artifact re-run after the definition fix): kappa
  **0.8645**, % agreement 96.0 — **acceptable**. Both echoes ship
  (`measure/msa-round1.json`, `msa-round2.json`); the arc — and why the
  fix went into the operational definition, not into a conversation — is
  `measure/msa-note.md`. Prescores pass on both, including
  result-matches-recompute.
- **T-11** saved after round 2, `two_people_confirmed` checked on the
  kappa pass; all six prescore checks pass (`data_type_declared`:
  `attribute_defective` — the three-way declaration that keeps count data
  from ever being silently routed down the proportions path).
- The 21-day census ran 2026-06-29 → 07-22: **1,566 orders, 135 rejected
  (p̂ 0.0862), 139 failed-check marks** (`measure/orders-note.md` for the
  data, generation, and seed).
- **T-08** saved 2026-07-22: 80 transcribed entries (per day, shift,
  check), counts summing to the 139 marks; all four prescore checks pass.
  `to-dataset` (2026-07-23) materialized one row per mark; the category
  column through `POST /stats/pareto`: **trim 67 (48.20%) + wrong paper
  50 (cumulative 84.17%) = the engine-verified vital few**
  (`vital_few_count: 2`, `flat: false`); ink 13, quantity 9 the tail.
  Echo: `measure/pareto.json`.

## The opportunity-inflation beat — hard_flag, quoted, corrected

The first draft of the T-10 DPMO block claimed
`opportunities_per_unit: 8` with justification `"various"`. The schema
accepted it — "various" is non-empty — which is exactly why the prescore
exists. `POST /prescore/T-10` on the draft, the flag verbatim:

> `opportunity_inflation_justified` — **hard_flag** —
> "opportunities_per_unit=8.0 > 1 with no real justification (placeholder:
> 'various') -- name what the extra opportunities actually are, or sigma
> is being flattered by inflated opportunity counting (rubric R-MEA-09)"

The draft's own numbers show what the game buys: 8 opportunities read DPMO
11,095 / sigma 3.79 — a **0.28-sigma compliment** the process never
earned, purchased entirely by the denominator. Corrected block: 4
opportunities, justification naming the four checks verbatim; `POST
/artifacts/T-10/validate` + save v1 (`measure/yield-calc.json`), prescore
all-pass including `opportunity_inflation_justified` **pass** with the
named list echoed. Engine results: per-step FPY 0.9692 / 0.9538 / 0.9490 /
0.9606, **RTY 0.8427** (serial declaration explicit), **DPMO 22,190.29,
sigma 3.5105 "with 1.5σ shift"** — read against first-presentation yield
91.38% and final yield ~99.8% in `measure/baseline-note.md`.

## The baseline freeze, and Analyze's two questions

- **T-21 v1** (2026-07-23): `freeze_requested: true` → the engine checked
  the floor (21 subgroups ≥ 20, zero rule-1/rule-4 signals) and froze —
  **p̄ 0.086207**, per-day limits (UCL 0.1750–0.1968 by n, LCL floored at
  0 everywhere), armed at freeze. Echo: `measure/baseline-pchart.json`;
  the stability-then-capability read: `measure/baseline-note.md`.
- **T-17 #1, the shift screen** (2026-07-27, `declared_primary: false`,
  1/1): chi-square independence on the check sheet's 4×2 table — Cochran
  checked in the printed path (7/8 cells expected ≥ 5, min 3.95, none
  < 1), **χ² 0.6069, df 3, p 0.8948, Cramer's V 0.066** — no association
  shown; the mix is a process property. Echo:
  `analyze-improve/hypothesis-shift.json`.
- **T-17 #2, the pre-declared primary** (question written 2026-08-01, run
  2026-08-24): two-proportion z, baseline 135/1566 (8.62%) vs post-change
  weeks 1–2 30/884 (3.39%) — floors printed and cleared (n·p̂ 135 and 30
  vs 5), **z 4.9576, p 7.14e-07, risk difference +5.23 points, CI [+3.32,
  +7.03]** (Newcombe). Echo: `analyze-improve/hypothesis-run.json`; both
  reads: `analyze-improve/hypothesis-note.md`. Prescores: all five checks
  pass on both runs.

## The EXIT-11 pair — chart refused, route refused

Run on purpose, 2026-09-06, so the record shows the engine saying no by
name. The draft chart (`analyze-improve/chart-flawed.json`) plots daily
failed-check **marks** through the p route and answers the selector's
printed question honestly; `POST /artifacts/T-21/validate` came back
**HTTP 422**:

> Value error, EXIT-11: This is counts-per-unit/area (defects), not
> pass/fail units (defectives) -- a p-chart is barred for it by name
> (defectives != defects, matrix VI.A.3 / §4a). Routes to: c/u chart
> family (T-29, v1.1) for monitoring; DPMO/yield (T-10) remains available
> as a descriptive summary.

The same framing through the test selector's routing-only endpoint
(`POST /stats/hypothesis/route`, `declared_data_type: "count_rate"`)
stopped at the same name: decision path ends "EXIT-11 — no v1 route
carries count/rate data honestly", `route: null`. One rule, both doors;
`analyze-improve/teaching-note.md` is the full write-up, including the
139-marks-on-135-orders fact that makes counts ≠ units concrete.

## Improve → Control — proof, monitoring close-out, recalculation

The change itself — prepress pre-flight checklist + labeled paper trays,
in effect 2026-08-03 — ships as prose (README), per the demo scope rule:
no pilot-plan artifact on this thread, so the rollout memo (2026-08-01,
threshold 0.05 declared before the window, falsification line included)
is echoed by reference where T-20 needs it. The engine runs, in order on
2026-09-07:

- **T-21 v2** (09:30): monitoring close-out, 60 subgroups against the
  frozen limits — quiet pre-change days (a 12.7% and a 15.9% day inside
  limits), then the engine's **rule4 signal, indices 30–59 below center**
  (index 30 = the change date), acknowledged 2026-08-12 with the
  keep-the-change / no-informal-recenter note. Prescore all-pass,
  including signal-acknowledgment completeness.
- **T-21 v3** (16:00): logged `recalculate_reason`, new freeze from the
  24-day post window — **p̄ 0.037891, 0 signals, log now two entries**.
  Echo: `control/control-chart.json`.
- **T-20** (16:30): threshold **met as declared** (0.036823 vs 0.05);
  **weakened: true** — season and demand (the ~15% final-week surge)
  carried on the verdict with direction stated; guardrails both improved
  (turnaround −5.3%, overtime −9.2%); gap block: recovered **0.049384 of
  the 0.043207 gap (114.3%), remaining −0.006177, goal_met: true — "Goal
  met — route to Control."** Echo: `analyze-improve/proof.json`; the
  full read: `control/control-run.md`. Prescore: five for five.

## The stored record

Project `print-shop-demo` closes the session holding: picker v1, charter
v1, voc-ctq v1, copq v1, collection-plan v1, **msa v1+v2** (the
marginal→fix→re-run arc as versions), check-sheet v1, yield v1,
**pchart v1+v2+v3** (freeze →
monitored signal → logged recalculation as versions), hypothesis-shift v1,
hypothesis-beforeafter v1, proof v1 — plus the two datasets and the one
draft that never saved because the engine refused it. Cross-checks
(`POST /prescore/cross/print-shop-demo`, dataset column `reject_any`):
charter impact vs COPQ total **0.0% apart**; goal vs engine-computed
measured baseline "a genuine improvement." Every shipped JSON is the
engine's own echo; the demo's prose quotes engine numbers and nothing
else.
