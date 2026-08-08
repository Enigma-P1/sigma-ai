# after-round2.csv — the round-2 pilot-window sample

120 order-to-handoff times in minutes (tenths), collected under the round-2
change (grinder dial-in + standby swap, pilot `pilot-plan-round2.json`) on
top of the implemented round-1 method, same T-11 rule as every prior window:
every 4th espresso order, weekday 7:00–10:00 peak, 10 weekday mornings
2026-09-08 → 2026-09-21 (Labor Day 2026-09-07 excluded), 12 orders per
morning. Same columns, strata, operational definition, and measurement
system as `measure/wait-times.csv`. This window runs in fall semester —
order counts ~15% above the summer baseline — which the pilot plan declared
as a live season/demand confound up front and the round-2 proof carries on
its verdict.

## The numbers, and the checks made

- n = 120, **mean 4.899**, sd 0.658, min 3.4, max 6.6 — against the round-1
  window's 6.198/0.866, the pilot's pre-declared 5.5 threshold, and the
  charter's 5.0 goal.
- Rows in true time order, as the I-MR chart and the T-20 run require.
- **Stability engine-verified**: saved as project dataset
  `314125ca183d4f89a9442a2f2408f485` (sha256
  `96d34e2bce8654cce7fc212caf5417b33a15eee2d8f90c12e0344f6f3b89b66e`) and
  run through the live `POST /stats/baseline` (USL 5.0, no LSL) on
  2026-09-21: `stable: true` — "stable: 120 points, no default-rule
  signal" — I-MR limits 3.029 / 4.899 / 6.770, MR UCL 2.298, zero
  rule-1/rule-4 signals. This clean 120-point window is what T-21 freezes
  its control limits from the next morning (the ≥20-point signal-free
  freeze floor, cleared six times over).
- Normality advisory: `no_concern` (Anderson-Darling statistic 0.3591,
  p ≥ 0.15).
- **Capability, reported because the window is stable: Cpk 0.054** (Ppk
  0.051), dpmo 439,120 — the engine's model puts ~43.9% of orders past the
  5.0-minute line at this center and spread, and the sample agrees in kind:
  46 of these 120 orders (38%) ran over 5.0 minutes.
- Import quality scan on save: 0 missing, 0 non-numeric, 0 duplicates.

## The honest read: center vs spread

This is the file where the project's two promises come apart, on purpose.
The **mean** promise is met: 4.899 against the 5.0 goal, under semester
load, with the re-pull stalls gone (the grinder card logged zero under-queue
re-dials all window). The **every-order** promise is not: a process
centered 0.10 under the limit with 0.62 minutes of within-sigma wobble puts
a bit under half its orders over the line — Cpk 0.054 is the number that
says "the center cleared the bar; the spread still straddles it." Both
claims are true at once, and the round-2 proof, the control chart's notes,
and the A3's close all say them together rather than letting the mean speak
alone. That is the stable-but-not-yet-capable teaching moment the T-21
helper names — met here at close instead of at baseline.

## Reproducibility

Demo data from the seeded script below, same acceptance-search shape as the
other two generators: seeds from 0, first pass wins. Acceptance checks —
mean 4.895–4.905, sd 0.62–0.68, range inside 3.3–6.9, 46–56 of 120 values
over 5.0 (so the capability story stays honest in the sample, not just the
model), Anderson-Darling p ≥ 0.06, no I-MR rule-1/rule-4 signal (d2 =
1.128). **Seed 5** is the first acceptable seed and produced this file. The
binding verdicts are the live engine's (`/stats/baseline` above, the T-20
proof, and the T-21 freeze). Run with `engine/.venv/bin/python`.

```python
#!/usr/bin/env python3
"""Generate demo/coffee-bar/improve/after-round2.csv -- 120 order-to-handoff
times (minutes, tenths) over the 10 weekday pilot mornings 2026-09-08 to
2026-09-21 (Labor Day excluded), under the round-2 change (backup grinder +
dose dial-in) on top of the implemented round-1 method, mean ~= 4.90,
STABLE under the engine's default I-MR rules and clean of rule-1/rule-4
signals so the same window can freeze the T-21 control limits (>=20-point
floor comfortably cleared at n=120). Same acceptance-search shape as the
baseline generator; binding verdict is the live engine's /stats/baseline.
Run with engine/.venv/bin/python (scipy for the normality pre-check)."""
import csv
import random
import statistics
import sys

from scipy import stats as scistats

DATES = ["2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11", "2026-09-14",
         "2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18", "2026-09-21"]
ORDERS_PER_DAY = 12  # every 4th espresso order of ~55 semester-peak orders
DRINKS = ["latte", "cappuccino", "americano", "mocha"]
DRINK_WEIGHTS = [0.40, 0.25, 0.20, 0.15]
DRINK_EFFECT = {"latte": -0.03, "cappuccino": 0.04, "americano": -0.25, "mocha": 0.18}
BARISTAS = ["Marcus", "Riley"]
BARISTA_WEIGHTS = [0.6, 0.4]
BARISTA_EFFECT = {"Marcus": -0.05, "Riley": 0.08}
DAYPART_EFFECT = {"early": -0.12, "late": 0.12}
BASE_MEAN = 4.92          # intercept; weighted strata effects net ~-0.02
NOISE_SD = 0.63
DAY_SD = 0.08
CLIP_LO, CLIP_HI = 3.3, 6.9
D2_N2 = 1.128


def simulate(seed):
    rng = random.Random(seed)
    rows = []
    for date in DATES:
        day_shift = rng.gauss(0.0, DAY_SD)
        for i in range(ORDERS_PER_DAY):
            daypart = "early" if i < 6 else "late"
            drink = rng.choices(DRINKS, weights=DRINK_WEIGHTS)[0]
            barista = rng.choices(BARISTAS, weights=BARISTA_WEIGHTS)[0]
            mu = (BASE_MEAN + day_shift + DAYPART_EFFECT[daypart]
                  + DRINK_EFFECT[drink] + BARISTA_EFFECT[barista])
            x = rng.gauss(mu, NOISE_SD)
            while not (CLIP_LO <= x <= CLIP_HI):
                x = rng.gauss(mu, NOISE_SD)
            order_id = f"POS-{date[5:7]}{date[8:10]}-{i + 1:02d}"
            rows.append([order_id, date, daypart, drink, barista, round(x, 1)])
    return rows


def imr_rule1_rule4_clean(values):
    xbar = statistics.fmean(values)
    mrs = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    sigma = (sum(mrs) / len(mrs)) / D2_N2
    ucl, lcl = xbar + 3 * sigma, xbar - 3 * sigma
    if any(v > ucl or v < lcl for v in values):
        return False
    run_side, run_len = 0, 0
    for v in values:
        side = 1 if v > xbar else (-1 if v < xbar else 0)
        run_len = run_len + 1 if side == run_side and side != 0 else (1 if side else 0)
        run_side = side
        if run_len >= 8:
            return False
    return True


def acceptable(values):
    mean = statistics.fmean(values)
    sd = statistics.stdev(values)
    over5 = sum(1 for v in values if v > 5.0)
    ad_p = scistats.anderson(values, dist="norm", method="interpolate").pvalue
    return (4.895 <= mean <= 4.905 and 0.62 <= sd <= 0.68
            and min(values) >= CLIP_LO and max(values) <= CLIP_HI
            and 46 <= over5 <= 56 and ad_p >= 0.06
            and imr_rule1_rule4_clean(values))


def main(out_path):
    for seed in range(20000):
        rows = simulate(seed)
        values = [r[5] for r in rows]
        if acceptable(values):
            break
    else:
        sys.exit("no acceptable seed found in range(20000)")
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "date", "daypart", "drink_type", "barista", "wait_minutes"])
        w.writerows(rows)
    mean, sd = statistics.fmean(values), statistics.stdev(values)
    over5 = sum(1 for v in values if v > 5.0)
    print(f"seed={seed} n={len(values)} mean={mean:.4f} sd={sd:.4f} "
          f"min={min(values)} max={max(values)} over5={over5}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "after-round2.csv")
```
