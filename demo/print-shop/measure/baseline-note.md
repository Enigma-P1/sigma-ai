# Baseline — the attribute path's stability-then-capability read

Not an artifact: the recorded result of running the Measure baseline through
the live engine on 2026-07-23, after `orders.csv` was saved as a project
dataset and the T-12 check had passed. The routing itself is the first
teaching point: T-13's `/stats/baseline` orchestrator is the continuous
path — I-MR stability, then Cp/Cpk — and daily defective proportions are
not continuous measurements, so this thread never calls it. The attribute
baseline is the matrix's own 2.4.3 route: **stability from the p-chart
branch of T-21** (frozen from the baseline window, exactly as the coffee
bar's I-MR read came from `/stats/baseline`'s stability half), **capability
language from T-10's DPMO/sigma block** (defect counts against named
opportunities), with no Cpk anywhere — a proportion has no spec-limit
z-score to build one from, and the suite does not improvise one.

## The frozen baseline p-chart (engine echo: `baseline-pchart.json`)

`POST /artifacts/T-21/validate` with `freeze_requested: true`, then saved v1;
the selector answered on the record — attribute data, **defectives** (whole
orders pass or fail; the reject log's per-check marks are defects and are
charted nowhere here). The engine's frozen baseline, pasted:

- **center p̄ = 0.086207** — 135 defective orders over 1,566 (21 daily
  subgroups, 2026-06-29 → 2026-07-22)
- limits are per-point because n varies 58–90 by day: UCL runs 0.1750 (the
  n=90 day) to 0.1968 (the n=58 Saturday), **LCL floored at 0 on every
  point** — at p̄ 8.6% and these subgroup sizes, three binomial sigmas
  reach below zero, so no day can signal "too good" on rule 1; only a run
  can say that (rule 4 later does exactly this, on this same chart)
- **signals: 0** — no point beyond its own limits, no run of 8; the worst
  day (2026-07-13, 12.79%) sits inside its own 17.70% UCL
- freeze floor: 21 subgroups ≥ 20, no default-rule signal in the window —
  both engine-checked before it would freeze; `meets_freeze_floor: true`
- recalculation log: one entry — `initial freeze, 2026-07-23T17:30:00Z`;
  armed at freeze, daily close-out cadence
- source provenance: dataset `3122dfa39994454090c24e7a857d18f6`, column
  `reject_any`, the engine's own `source_dataset_hash` stamped on the
  frozen window

Prescore: all five checks pass (`family_matches_data`,
`frozen_limits_present_before_signals`, `never_armed` pass-as-armed,
`signal_acknowledgment_completeness` with no signals yet,
`recalculation_log_has_reasons`).

## Yield and sigma (engine echo: `yield-calc.json`)

The T-10 steps table counts what the QC desk cannot see: per-step
first-pass-correct from the job travelers, same 21-day window, where a
re-plated file or a re-run press pass counts against first-pass even though
the shop caught it and the customer never did. The engine's computed steps,
pasted (`defects_at_step`, `dpu_at_step`, `fpy_at_step` are all derived —
first_pass_correct is the one raw input):

- order entry: 1566 in, 1517 first-pass — DPU 0.0313, FPY 0.9692
- prepress: 1566 in, 1492 first-pass — DPU 0.0473, FPY 0.9538
- print: 1566 in, 1484 first-pass — DPU 0.0524, FPY 0.9490
- trim/finish: 1566 in, 1503 first-pass — DPU 0.0402, FPY 0.9606
- **RTY = 0.8427** (product of the four FPYs, computed only under the
  explicit `steps_in_series: true` declaration)

Three yields, three different sentences, all true at once: final yield —
did a good order eventually go out? — is ~99.8% (all but three cancelled
reprints eventually shipped right), and it is the number that kept this
problem invisible for a year. First-presentation yield is 91.38%
(1 − 0.0862): what the customer experiences. **RTY is 84.27%**: the odds an
order clears all four steps untouched — the gap between 84 and 99.8 is the
hidden factory, roughly one order in six getting quietly re-worked
somewhere. The narrative quotes RTY, not final yield, because rework exists
(rubric R-MEA-09 #2).

The DPMO block converts the escape counts to capability language: 139
failed-check marks over 1,566 orders × 4 opportunities — **DPMO 22,190.29,
sigma 3.5105, convention printed: "with 1.5σ shift"** — the number never
travels without its label. `opportunities_per_unit: 4` carries its
justification verbatim: the four named checks, one opportunity each, fixed
for every order and every re-run. (The first draft claimed 8 justified as
"various"; the prescore hard-flagged it by name and the corrected block is
what shipped — the draft and flag are quoted in `../print-shop-run.md`.)

## The Pareto (engine echo: `pareto.json`)

The check sheet exported through `to-dataset` (dataset
`c33da44e761b4bf39eecf65a232f8cb7`, one row per tally mark, zero re-typing)
and its category column fed `POST /stats/pareto`. The engine's ranking,
pasted:

- **Trim misalignment: 67 marks, 48.20%** — cumulative 48.20%, vital few
- **Wrong paper stock: 50 marks, 35.97%** — cumulative **84.17%**, vital few
- Ink smudge / banding: 13 marks, 9.35% — cumulative 93.53%
- Wrong quantity: 9 marks, 6.47% — cumulative 100%
- `vital_few_count: 2`, `flat: false` — two of four categories carry the
  80% line, an engine-verified vital few, not an eyeball claim

That ranking is the Analyze hand-off: trim and wrong paper are where the
fix aims (prepress pre-flight checklist for what reaches the cutter,
labeled trays for what reaches the press), and the chi-square screen
(`../analyze-improve/hypothesis-shift.json`) says the mix is the same on
both shifts — a process property, not a people property.

## Teaching read

Stable at a bad level — the coffee bar's sentence, in attribute form. Zero
signals on 21 subgroups means no day was special: nobody's bad Tuesday, no
rogue shift, nothing to hunt. The process is simply built to reject about
one order in twelve, and the chart's quiet is the proof that chasing
yesterday's spike (2026-07-13's 12.8% was still common cause) would have
been tampering. So Measure hands Analyze a different question than "what
went wrong last week": which common causes put 84% of the failed-check
marks on two of the four checks — and the answer has to move p̄, the center
line, not any single day. The DPMO/sigma pair (22,190 / 3.51 with the
shift convention named) is the same fact in capability units: this is what
the process is designed to produce, until the process itself is changed.
