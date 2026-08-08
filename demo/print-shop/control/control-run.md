# Control run — the recorded engine verdicts, freeze to recalculation

Not an artifact: the recorded engine runs of the monitoring story, project
`print-shop-demo`, continuing `../print-shop-run.md`. One chart artifact
(`print-pchart`) carries the whole arc as saved versions — the frozen
baseline (`../measure/baseline-pchart.json`), the monitoring close-out
with the improvement signal acknowledged (quoted below, echo in the
project store), the recalculated post-change chart (shipped as
`control-chart.json`, its latest re-validated echo). That shape is the
point: control limits lived one freeze and one *logged* recalculation,
and every intermediate state is a version, not an overwrite.

## Monitoring against the frozen baseline (v2 of `print-pchart`)

The chart was armed the day it froze (2026-07-23), and dailies kept landing
on it: 60 subgroups by the 2026-09-07 close-out save — the 21 frozen
baseline days plus 39 monitored days — every one judged against the FROZEN
limits (the baseline fields ride through the v2 save byte-identical; the
engine only recomputes limits on an explicit freeze or a logged
recalculation). What the frozen limits said, from the v2 echo:

- The nine pre-change days (07-23 → 08-01) fired nothing — including a
  12.7% day and a 15.9% day, both inside their own limits. Ugly-looking
  and common-cause are different claims; nobody re-cut a blade over a
  Saturday spike, and the chart is what licensed the restraint.
- From **2026-08-03 — the change date, exactly** — every daily point sits
  below the frozen center. The engine's signal, verbatim: **rule4, indices
  30–59, side below — "30 consecutive points fall below the center line
  (indices 30-59)"**. Index 30 is 2026-08-03.
- Prescore on v2: all five checks pass — `never_armed` pass-as-armed,
  `signal_acknowledgment_completeness` "every fired signal is
  acknowledged."

## The signal, acknowledged — and what was deliberately NOT done

A rule-4 run below center is a special cause, and special causes get
investigated even when they point the right way. The acknowledgment on the
signal (key `rule4:30:59:below`, 2026-08-12 — the morning after the run's
eighth point) records the investigation in process terms: the run begins
the day the prepress pre-flight checklist and labeled paper trays went into
effect, the change is deployed and holding on both shifts, no other process
change in the window. And it records the discipline: **keep the change; do
NOT re-center the chart informally** — new limits come only through the
logged recalculation path, from a ≥ 20-subgroup clean post-change window.
The improvement arriving as an alarm on the old chart is the freeze doing
its one job: drift — in either direction — now has something fixed to
drift away from.

## The recalculation (v3 — `control-chart.json`)

`POST /artifacts/T-21/validate` with a non-empty `recalculate_reason`, then
saved v3. The reason is the log entry — it names the verified change, the
investigated signal, the evidence (z = 4.96, p = 7.1e-7; gap block goal
met), and the window choice (2026-08-10 → 09-05, bedding-in week excluded
so the limits describe the settled process). The engine's recalculated
baseline, pasted:

- **center p̄ = 0.037891** — 69 defective orders over 1,821, 24 daily
  subgroups, engine-verified signal-free before it would freeze (the same
  ≥ 20-and-quiet floor as the first freeze)
- per-point limits again, n 58–91: UCL 0.1131 on the lightest day, 0.0979
  on the heaviest; LCL floored at 0 on every point
- **recalculation log, two entries**: `initial freeze, 2026-07-23` and the
  full logged reason, `recalculate, 2026-09-07` — the chart's whole limit
  history in one field
- signals against the new limits: **0**; armed stays true, same daily
  cadence — the term-start surge week (81–91 orders/day) is *inside* the
  window and inside the limits: load went up, the rate held
- the charter's 0.043 stays a **goal line on the wall chart, never a
  control limit** — the cadence note says so in as many words, and no rule
  reads against it. The chart says what the process is doing (0.0379,
  stable); the goal says what the charter promised (met, remaining −0.005);
  the two sentences stay different on purpose.
- Prescore: all five checks pass.

## The proof beside it (`../analyze-improve/proof.json`)

`POST /artifacts/T-20/validate`, saved the same afternoon (16:30, after
the recalculation proved the after-window stable). Before = the 21 baseline
daily proportions, after = the 24 post-change dailies **with weights** —
each day's order count beside its proportion, so the proof's after-mean is
the pooled rate 69/1821, not an unweighted mean of daily proportions that
would let a 58-order Saturday count exactly as much as a 90-order Monday.
The engine's verdict, pasted:

- **Threshold met, as declared**: after-mean **0.037891** vs the 0.05
  declared 2026-08-01 in the rollout memo — `met`/`not_met` are the only
  values the field can hold, and it renders as declared. That 0.037891 is
  the same pooled number the recalculated chart above froze as its center
  p̄ — chart and proof now quote one post-window rate, which is exactly
  what pooling by subgroup size is for.
- **`weakened: true`, on purpose**: season (fall term began 08-31) and
  demand (final six days averaged 84 orders/day against 73 for the first
  eighteen, ~15% more load) are answered `changed`, with the direction
  stated — more load pushes the rate *up*, so the confound can mask the
  win, not manufacture it. The headline carries both notes verbatim.
- Supporting test on the dailies: Welch t = 6.583, p = 2.02e-07, d = 1.997
  (CI 1.28–2.71) — the primary inference remains the pooled two-proportion
  z (`hypothesis-run.json`); both agree.
- Guardrails: median turnaround 1.9 → 1.8 days (`improved`, −5.3%); press
  overtime 6.5 → 5.9 h/wk (`improved`, −9.2%). No tradeoff sentence.
- **The gap block**: measured baseline 0.086207, goal 0.043, original gap
  0.043207; recovered **0.048316 (111.8%)**, remaining **−0.005109**,
  `goal_met: true`. Loop verdict, verbatim: *"Goal met — route to
  Control."*
- The continuous-baseline blocks inside the proof report their gate
  honestly as not-run ("at least one spec limit (USL or LSL) is
  required…") — a deliberate scope call, stated in the artifact's notes:
  spec-limit capability on daily proportions is the continuous path's
  language; this thread's stability read is the frozen p-chart and its
  capability language is T-10's DPMO/sigma (matrix 2.4.3).
- Prescore: all five checks pass (`threshold_as_declared`,
  `confounder_echo_present` with the weakened sentence confirmed in the
  headline, `gap_arithmetic_consistency` re-derived, two guardrails
  reported, metric identity single-copy).

## Cross-checks and close of record

`POST /prescore/cross/print-shop-demo` (dataset `3122dfa3…`, column
`reject_any`), both project-level reconciliations pass, pasted:

- charter business impact vs COPQ engine total: 23,720.6 vs 5,930.15
  annualized to 23,720.6 — **relative difference 0.0%**
- charter goal vs measured baseline: 0.043 against the engine-computed
  column mean 0.086207 — "a genuine improvement over the measured
  baseline"

(The check-sheet burst heuristic returns nothing to flag: every entry is
honest `transcribed` mode, which that check excludes by design.) The
record closes with the chart armed on recalculated limits, the goal line
still a goal line, and the open items named in the README — ink and
quantity, never targeted by this fix, now carry 28 of the post window's
69 marks (~41%, up from 16% of 139 at baseline): the natural head of a
future Pareto re-run, on a much smaller total.

## Teaching read

The attribute control story is the continuous one with the units changed
and one twist worth staring at. Same discipline: freeze from a verified
window, judge new points against frozen limits, recalculate only on a
logged reason — the chart's alarm value comes entirely from what it
refuses to forget. The twist is the LCL: at these subgroup sizes a
p-chart's lower limit floors at zero, so no single good day can ever
signal — only a *run* can prove improvement (rule 4 did, thirty days
long), and only recalculated limits can make the new level the thing
future drift is measured against. Which closes the loop the flawed draft
opened: the p-chart could carry this story precisely because the units
were pass/fail orders all the way down — the one thing the engine refused
to compromise on.
