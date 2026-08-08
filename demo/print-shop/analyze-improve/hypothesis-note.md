# Hypothesis runs — the shift screen and the before/after proof test

Both artifacts beside this note are engine echoes from
`POST /artifacts/T-17/validate`: routing and result are server-recomputed
from the stored question on every validate, which is what lets the
route-tamper prescore re-derive and match them. Two runs, two separately
pre-declared questions, each declared before its data was cut and each
answered by exactly one test (`comparisons_declared: 1`,
`tests_run_including_this_one: 1` on both — the multiplicity gate the
engine checks first, printed at the top of both decision paths). The
project's one **primary** comparison is the before/after test; the
chi-square is a stratification screen and says so
(`declared_primary: false`) — no shotgun p-values, no winner-narration.

## The chi-square screen (`hypothesis-shift.json`) — defect mix × shift

Declared at the 2026-07-27 huddle, before the shift split was tabulated: if
evening's defect mix differed from day's, the causes would be people-shaped
and the fix would have to split by shift. Input is the check sheet's own
4×2 table of failed-check marks (trim 38/29, paper 29/21, ink 6/7,
quantity 5/4 — day/evening), from the same to-dataset export the Pareto
ran on. The engine's verdict, pasted:

- Route: **`chi_square_independence`** — Cochran's rule checked before
  computing, as a printed node: "Does the table clear Cochran's rule?" →
  "88% of cells have expected>=5 (need >=80%); smallest expected cell=3.95
  (need >=1)" → **"cleared -- compute"**. The light cell (quantity ×
  evening, expected 3.95) is *within* the rule — 7 of 8 cells ≥ 5, none
  below 1 — and the engine said so rather than us deciding.
- Test: **χ² = 0.6069, df = 3, p = 0.8948** (α = 0.05), `significant:
  false`. Effect size: **Cramer's V = 0.0661** — "a negligible association"
  in the engine's own words.
- Plain-language block, non-significant form, verbatim in the echo: "no
  difference shown at this sample size. That is not proof there is no
  difference…" — the honest phrasing R-ANA-05 requires, printed by the
  engine so it cannot be paraphrased into "the shifts are identical."

The read: the defect mix is a **process** property, not a shift property —
consistent with the stable p-chart, and it routes the fix at the process
(pre-flight checklist, labeled trays) instead of at whoever works evenings.

## The pre-declared primary (`hypothesis-run.json`) — two-proportion z

The question was written into the huddle notes 2026-08-01, before any
post-change data existed: two full weeks after the change, is the
first-presentation defect rate lower than the baseline window's? The
comparison window (2026-08-10 → 08-22) deliberately excludes the six
bedding-in days after the 08-03 rollout and ends before the 08-31
term-start surge — the clean like-for-like cut; the proof artifact then
covers the full window with the surge declared. "Successes" is the
engine's word for the counted event; here the counted event is a rejected
order. The engine's verdict, pasted:

- Route: **`two_proportion_z`**, exit: none. The printed floor check, from
  the route echo: "baseline: n·p̂ = 135.00, n·(1−p̂) = 1431.00; post-change
  weeks 1–2: n·p̂ = 30.00, n·(1−p̂) = 854.00 (each needs ≥ 5)" — the
  proportion floors (matrix §4a EXIT-06) cleared six-fold on the smallest
  side. This is also where the sample-size teaching lands: the smaller
  group alone is 884 orders, seven times the coffee bar's entire n=120
  continuous baseline, because proportions are information-poor per row.
- Groups: baseline 135/1566 = **8.62%**; post-change weeks 1–2 30/884 =
  **3.39%**.
- Test: **z = 4.9576, p = 7.14e-07** (α = 0.05, two-sided),
  `significant: true`.
- Effect size: **risk difference +5.23 percentage points** (baseline minus
  post), 95% CI **[+3.32, +7.03] points** (Newcombe method 10, built from
  per-sample Wilson intervals — the engine names its CI method in the
  echo).
- Prescore: all five checks pass, including `route_tamper_check` (the
  stored route re-derives from the stored question) and
  `tests_run_vs_declared_primary`.

## Why these routes fit (in our own words, headlines covered)

Both questions are about counted pass/fail units, not measured amounts, so
neither goes anywhere near a t-test. The before/after question compares one
proportion against another from two independent windows — different orders,
different customers, no order in both — which is the two-proportion z's
exact shape: pooled-variance z on the difference, legitimate here because
both samples are far past the n·p̂ floors where the normal approximation
holds. What it can say: whether the drop from 8.6% to 3.4% is
distinguishable from chance, and how big the drop plausibly is (the CI).
What it cannot say: *why* the rate fell — attribution rides on the
monitoring chart's timing (the run below center starts on the change date)
and the confounder record, not on the z. The shift question is different in
kind — not "which proportion is bigger" but "are two categorical labelings
associated" — which is the chi-square of independence's exact shape, and
its honest gate is Cochran's rule on expected counts, checked by the engine
before any statistic was computed. Declaring the defect data as what it is
mattered both times: these are defectives (orders), so the proportions
family carries them; the same data declared as defect *counts* exits by
name — the route probe in `../print-shop-run.md` shows EXIT-11 firing on
the test selector exactly as it fired on the chart selector.

## What the results mean against the goal

The charter's gap is 4.3 percentage points (8.6% halved). The risk
difference says the first two settled weeks recovered **5.2 points, CI 3.3
to 7.0** — even the CI's pessimistic end recovers three-quarters of the
gap, and the point estimate clears it. Statistically detectable and
practically sufficient are different claims; here both hold, and the CI is
what licenses saying so (rubric R-ANA-05: the conclusion quotes effect size
and interval, not the p-value alone). What stays open after this test:
whether the rate *holds* — two clean weeks are evidence of a shift, not of
control, which is why the record continues through the full-window proof
(`proof.json`, surge declared, verdict weakened accordingly) and ends at a
recalculated, armed p-chart rather than at this p-value.
