# Hypothesis run — early vs late morning, the recorded engine verdict

The artifact next to this note (`hypothesis-run.json`) is the engine's own
echo from `POST /artifacts/T-17/validate` — routing and result are
server-computed from the stored question, never hand-typed, which is what
lets the route-tamper prescore re-derive and match them. This note records
how the run was made and what the numbers honestly mean.

## The question, stated before the data was touched

**"Are early-morning (07:00–08:30) and late-morning (08:30–10:00)
espresso-order wait times different?"** This is the one pre-declared primary
comparison for Analyze (`declared_primary: true`, comparisons declared 1,
tests run 1). It is the real project question the daypart stratification
column was captured for: if late mornings were much slower, staffing shape
(the fishbone's People candidate) would be a live driver; if not, the causes
operate all morning and the espresso-capacity story carries the weight.

## The split, documented

Raw values are `wait_minutes` from `measure/wait-times.csv` (the saved
baseline dataset), split by its `daypart` stratification column exactly as
recorded at collection: **early = 60 rows, late = 60 rows** (6 + 6 per
morning, 10 mornings, every 4th espresso order). Two independent groups —
different orders, different customers, nobody measured twice — declared
continuous, collected in time order (so the engine checked autocorrelation),
no shape concern declared.

## The engine's verdict (pasted from the response)

- Route: **`welch_two_sample_t`**, exit: none, 9 decision-path nodes. The
  path's checks along the way: one pre-declared primary comparison —
  continue; not count/rate data — continue; at most paired — continue;
  autocorrelation per group `early: r1=0.100, threshold=2/sqrt(n)=0.258` and
  `late: r1=-0.013` — "no material autocorrelation signal -- continue";
  n=60 ≥ 15 per group — "use the parametric default (Welch t)"; EXIT-06
  floor n≥8 per sample — "floor cleared -- compute".
- Groups: early (07:00-08:30) n=60, mean **8.1817**, sd 1.0963; late
  (08:30-10:00) n=60, mean **8.635**, sd 0.9395.
- Test: t = **−2.432152809782416**, df = 115.2963149150924,
  **p = 0.01654731610630722** (α = 0.05, two-sided), `significant: true`.
- Effect size: **Cohen's d (Welch/unequal-variance form) = −0.44404831907246695**,
  95% CI **[−0.8062701964450925, −0.08182644169984149]** (Hedges & Olkin
  (1985) large-sample approximate SE — not an exact noncentral-t CI).
- Assumptions checked: "n >= 8 per sample cleared (matrix §4a EXIT-06);
  groups independent". Warnings: none.
- Plain-language block, verbatim: "p = 0.0165, below the alpha=0.05
  threshold: if there were truly no difference, a result at least this far
  from 'no difference' would turn up by chance alone only about 1.7% of the
  time. That makes the difference statistically detectable here -- it does
  not mean the null hypothesis is false with that probability, and it says
  nothing yet about whether the difference is big enough to matter."

## Why Welch's t fits (in our own words, headline covered)

Two separate sets of orders measured once each — independent, not paired,
and a measured amount of time, not a count. Comparing two independent means
is t-test territory; Welch's form is the engine's default because it does
not assume the two groups share a variance (early's sd 1.10 vs late's 0.94
— close, but nothing needs to ride on that). What the test can say: whether
the early/late difference in mean wait is distinguishable from chance at
this sample size, and how big it plausibly is. What it cannot say: *why*
the dayparts differ — a daypart difference is not proof of any particular
mechanism behind the dayparts.

## What the result means against the goal

Late mornings run **0.45 minutes slower** than early (8.64 vs 8.18) — real
(p = 0.0165) but **small** (d = −0.44; the CI runs from a medium effect to a
negligible one). The gap the goal must close is **3.4 minutes** (baseline
8.41 against the 5.0 promise), and even the *early* window averages 8.18 —
3.2 minutes past the customer's line. So the daypart split is ruled **in**
as a real but minor load effect, and ruled **out** as a main driver: no
schedule shuffle between dayparts can recover more than a fraction of a
minute when both windows blow the promise by three. That is exactly the
fishbone's espresso-capacity story — the verified causes (drink-queue
pileup ahead of the single station, grinder rework) operate all morning —
and it is why the People-branch staffing cause stays *investigating*, not
verified: this run is its evidence-so-far, and the evidence says "not the
driver."
