# S-1 data — four pre-collected scenario inputs, engine-verified

The S-1 eval scenario's complete data package: the 20-day baseline window,
the 20-day measured after window, the T-12 test/retest pairs, and the
check-sheet delay marks. These are **eval scenario inputs** (PLAN §9:
datasets are pre-collected and realistic — the eval measures the suite,
not data gathering), not artifacts: an eval run feeds them into the tools
and must reproduce the engine verdicts recorded below.

## The files

- `tickets-baseline.csv` — 127 rows, every 2nd routine (P3) ticket over 20
  business days 2026-07-06 → 2026-07-31, in true time order. Columns:
  `ticket_id`, `date`, `request_type`, `channel`, `tech`,
  `resolution_hours` (business hours 8:00–17:00 Mon–Fri, tenths, ticket
  created → requester-confirmed resolution — the operational definition
  chosen because techs batch-close at day's end).
- `tickets-after.csv` — 124 rows, same columns and definition, the measured
  after window 2026-09-14 → 2026-10-09 (dispatch rule live 2026-09-07;
  bedding-in week excluded by declaration).
- `msa-repeats.csv` — 12 baseline tickets spanning the observed range
  (every 12th order statistic), each re-extracted blind from the event log
  five days after the first pass, same person, same procedure. Six of the
  twelve second passes differ from the first — the study has something to
  measure.
- `delay-tallies.csv` — one mark per baseline ticket over the 8.0-hour
  promise (all 127), tagged with the largest wait segment in its event
  log: the T-08 → T-14 chain's raw input.

## The numbers, and the checks made

- Baseline: n = 127, **mean 26.714**, sd 6.172, median 26.6, min 10.6, max
  42.9 — consistent with the charter's ~26-hour June magnitude and its 6.5
  planning SD. After: n = 124, **mean 7.217**, sd 2.080, min 2.7, max 13.8.
- **Stability engine-verified on both windows, not assumed** — zero
  Western Electric rule-1/rule-4 signals either side (the frozen
  defaults); details in the transcript below. No hand adjustment was
  needed after engine verification.
- Normality advisory both windows: `no_concern` (baseline A-D 0.291,
  after 0.318, both p ≥ 0.15) — S-1 deliberately stays off the EXIT-05
  path; the non-normal caveat path is not this scenario's lesson.
- Strata are real, not decoration: access grants run ~7.4 h longer
  (approval wait), email arrivals ~2.4 h longer (manual triage), and the
  engine's Welch run below verifies the access split a runner should find.
- Import quality scan on save: 0 missing values, 0 non-numeric values in
  `resolution_hours`, 0 duplicate rows, both CSVs.
- The 12 `msa-repeats.csv` first readings match the baseline CSV's
  recorded values for the same `ticket_id`s, by construction — same
  extraction, same file.
- Delay-tally cross-check: 127 marks = 127 baseline rows over 8.0 h (every
  sampled ticket blew the promise; the tally is a census of them).

## Engine verification transcript (2026-08-08, engine 0.1.0)

Every claimed statistic below is pasted from live-engine responses at
`http://127.0.0.1:8000`; the requests are reproducible from the CSVs.

**`POST /stats/baseline`** (baseline column, `usl: 8.0`, no LSL,
`operational_definition_ok: true`):
`stable: true` — "stable: 127 points, no default-rule signal". I-MR: x̄
26.7142, MR-bar 7.3302, σ-within 6.4984, individuals limits 7.2191 /
46.2093, **0 signals**. Descriptive: mean 26.7142, sd 6.1717, median 26.6,
Q1 22.3, Q3 30.95. Normality `no_concern` (A-D 0.2914, p ≥ 0.15).
Capability `one_sided: true`: **Cpk −0.9599**, Ppk −1.0108, no Cp/Pp
(one spec limit). Sigma block: DPMO 998,786.4, sigma level −1.5323,
`convention: "with 1.5σ shift"`. Observed: 127 of 127 over 8.0. `exits: []`.

**`POST /stats/baseline`** (after column, same specs): `stable: true` —
124 points, 0 signals; x̄ 7.2169, σ-within 2.2033, limits 0.6069 /
13.8270; mean 7.2169, sd 2.0797; normality `no_concern` (A-D 0.3176);
**Cpk 0.1185**, Ppk 0.1255; DPMO 353,259.8, sigma 1.8765 (shift
labeled). Observed: 44 of 124 (35.5%) over 8.0.

**`POST /artifacts/T-12/validate`** (continuous, `gauge_increment: 0.1`,
`usl: 8.0`, the 12 re-extraction pairs): resolution pre-check **passed**
(increment = 0.30% of the 32.9-h observed span, 18 distinct values);
**repeatability 1.6562%** (s_repeat 0.1354, denominator
`study_variation` = 49.0524, 12 items used, none excluded); verdict
**acceptable**, repeatability-only caveat attached by the engine.

**`POST /stats/pareto`** (127 delay marks): sat unassigned 68 (53.54%) →
cum 53.54%; waiting on manager approval 34 (26.77%) → **cum 80.31%,
vital-few count 2**; requester reply 11; reassigned 8; license/stock 6;
`flat: false`.

**`POST /stats/hypothesis/run`** (two_independent, declared primary —
access grants vs other routine): route `welch_two_sample_t`; access n = 51,
mean 31.1157, sd 4.9851; rest n = 76, mean 23.7605, sd 5.0407; **t =
8.1145, df 108.19, p = 8.33e-13**, Cohen's d (Welch form) **1.4672**, CI
1.0692 to 1.8653. Not refused; floors cleared.

**`POST /stats/hypothesis/run`** (two_independent — baseline vs after,
the proof's test): **t = 33.6963, df 154.86, p = 3.45e-73, d = 4.2338**
(CI 3.7884 to 4.6792).

**`POST /stats/sample-size`** (mean calculator, planning_sd 6.5, margin
1.25, 95%): **n = 104** (n_exact 103.87, z 1.95996). Achieved n = 127.

Derived arithmetic the tools recompute in-run (stated for the record):
goal 8.0, gap 26.7142 − 8.0 = 18.7142; recovered 26.7142 − 7.2169 =
19.4973 = **104.2%**, remaining **−0.78**.

## Reproducibility

This is eval fixture data: it was generated by the seeded script below,
engineered to tell the scenario's true story — a stable process built to
run at ~26.7 business hours against an 8-hour promise, delay marks
concentrating on batch triage + approval waits, then a deliberate
2026-09-07 dispatch-rule change that recovers the gap without fully fixing
the access tail — with realistic request-type/channel/tech strata. The
script searches seeds from 0 and keeps the first sample passing every
acceptance check: window sizes in band, baseline mean 26.0–26.8 with sd
5.6–6.8, no I-MR rule-1/rule-4 signal on either window (the engine's
frozen defaults, same d2 = 1.128 arithmetic), Anderson-Darling p ≥ 0.06
both windows, baseline one-sided Cpk in −1.15..−0.85 and after Cpk in
0.08..0.24 (mean 6.9–7.3), the access-vs-rest Welch split real (p < 1e-3,
gap 4.0–7.5 h), T-12 pairs in the acceptable band with visible
disagreement, and the delay tallies in strict Pareto order crossing 80%
exactly at the second category (the engine's vital-few convention).
**Seed 32** is the first acceptable seed and produced all four files. The
binding verdicts remain the live engine's, which every number above was
run through after generation. Run with `engine/.venv/bin/python` (scipy
for the normality/Welch pre-checks).

```python
#!/usr/bin/env python3
"""Generate evals/scenarios/s1-helpdesk/data/ -- the S-1 held-out eval
scenario's pre-collected inputs: a 20-day baseline window of routine-ticket
resolution times (business hours), a 20-day post-change window, the T-12
test/retest re-extraction pairs, and the delay-reason tally marks. One
seeded simulation, engineered to tell the scenario's true story -- a stable
process built to resolve routine tickets in ~26 business hours against an
8-business-hour promise, whose delay marks concentrate on batch triage +
approval waits, then a deliberate 2026-09-07 dispatch-rule change that
recovers the gap -- with the binding verdicts always the live engine's.
The script searches seeds from 0 and keeps the first sample passing every
acceptance check below (all mirroring the engine's own frozen rules: I-MR
rule 1 + rule 4 with d2 = 1.128, the 80% Pareto vital-few convention,
Anderson-Darling normality as the EXIT-05 advisory input, Welch floors).
Run with engine/.venv/bin/python (scipy for the normality/Welch pre-checks).
"""
import csv
import math
import statistics
import random
import sys

from scipy import stats as scistats

# --- calendar: Mon-Fri service days ------------------------------------------
def business_days(start_iso, n_days):
    import datetime as dt
    d = dt.date.fromisoformat(start_iso)
    out = []
    while len(out) < n_days:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out

BASELINE_DATES = business_days("2026-07-06", 20)  # -> 2026-07-31
AFTER_DATES = business_days("2026-09-14", 20)     # -> 2026-10-09

# --- process model (resolution time in BUSINESS hours, 8h business day) ------
TYPES = ["password_reset", "software_install", "access_grant"]
TYPE_W = [0.28, 0.42, 0.30]
CHANNELS = ["portal", "email"]
CHANNEL_W = [0.62, 0.38]
TECHS = ["B.O.", "L.F.", "M.D."]  # Ben Okafor, Lena Fischer, Marco Diaz
TECH_W = [0.38, 0.34, 0.28]

# Baseline: the morning triage batch dominates everyone's clock; access
# grants add the manager-approval wait on top.
BASE = {"mean": 24.1, "noise_sd": 5.3, "day_sd": 0.7, "clip": (9.0, 44.0),
        "type_eff": {"password_reset": -1.6, "software_install": 0.3, "access_grant": 5.6},
        "chan_eff": {"portal": 0.0, "email": 2.4},
        "tech_eff": {"B.O.": -0.3, "L.F.": 0.1, "M.D.": 0.3}}
# After (assign-on-arrival dispatch rule, live 2026-09-07): the batch wait
# is gone for every ticket, and the approval request now goes out the same
# hour the ticket lands, so the access gap shrinks without a second change.
AFTER = {"mean": 6.3, "noise_sd": 1.9, "day_sd": 0.25, "clip": (2.0, 14.5),
         "type_eff": {"password_reset": -0.9, "software_install": 0.2, "access_grant": 2.3},
         "chan_eff": {"portal": 0.0, "email": 0.6},
         "tech_eff": {"B.O.": -0.1, "L.F.": 0.0, "M.D.": 0.1}}

USL = 8.0        # the service-catalog promise: one business day
D2_N2 = 1.128    # engine's I-MR d2 constant (stats/constants.py)

# Delay-reason model for the check-sheet marks: one primary reason per
# baseline ticket that blew the 8-hour promise, tagged by the largest wait
# segment in its event log. Access grants mostly tag the approver wait;
# everything else mostly tags the unassigned queue.
REASONS = ["sat unassigned in triage queue > 4h", "waiting on manager approval",
           "waiting on requester reply", "reassigned between techs", "license/stock wait"]
def reason_weights(ticket_type):
    if ticket_type == "access_grant":
        return [0.28, 0.60, 0.05, 0.04, 0.03]
    return [0.74, 0.02, 0.12, 0.08, 0.04]


def simulate_window(rng, dates, model, prefix):
    rows = []
    for date in dates:
        day_shift = rng.gauss(0.0, model["day_sd"])
        n_today = rng.choices([5, 6, 7, 8], weights=[0.2, 0.35, 0.3, 0.15])[0]
        for i in range(n_today):
            ttype = rng.choices(TYPES, weights=TYPE_W)[0]
            chan = rng.choices(CHANNELS, weights=CHANNEL_W)[0]
            tech = rng.choices(TECHS, weights=TECH_W)[0]
            mu = (model["mean"] + day_shift + model["type_eff"][ttype]
                  + model["chan_eff"][chan] + model["tech_eff"][tech])
            x = rng.gauss(mu, model["noise_sd"])
            lo, hi = model["clip"]
            while not (lo <= x <= hi):
                x = rng.gauss(mu, model["noise_sd"])
            tid = f"{prefix}-{date[5:7]}{date[8:10]}-{i + 1:02d}"
            rows.append([tid, date, ttype, chan, tech, round(x, 1)])
    return rows


def simulate(seed):
    rng = random.Random(seed)
    base_rows = simulate_window(rng, BASELINE_DATES, BASE, "HD")
    after_rows = simulate_window(rng, AFTER_DATES, AFTER, "HD")
    # T-12 re-extraction pairs: 12 baseline tickets picked to span the
    # observed range (every 12th order statistic), second blind extraction
    # differing only by occasional event-row / business-hours slips.
    by_val = sorted(base_rows, key=lambda r: r[5])
    idx = [round(j * (len(by_val) - 1) / 11) for j in range(12)]
    msa_rows = []
    for j in idx:
        first = by_val[j][5]
        d = rng.choices([0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.6],
                        weights=[0.35, 0.15, 0.15, 0.10, 0.10, 0.05, 0.05, 0.05])[0]
        msa_rows.append([by_val[j][0], first, round(first + d, 1)])
    # Delay-reason tally: one mark per baseline ticket over the 8.0h promise.
    tally_rows = [[r[0], r[1], rng.choices(REASONS, weights=reason_weights(r[2]))[0]]
                  for r in base_rows if r[5] > USL]
    return base_rows, after_rows, msa_rows, tally_rows


# --- engine-rule mirrors (binding verdicts stay the live engine's) -----------
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


def cpk_upper_only(values):
    xbar = statistics.fmean(values)
    mrs = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    sigma_within = (sum(mrs) / len(mrs)) / D2_N2
    return (USL - xbar) / (3 * sigma_within)


def acceptable(base_rows, after_rows, msa_rows, tally_rows):
    bv = [r[5] for r in base_rows]
    av = [r[5] for r in after_rows]
    # window sizes in the brief's bands
    if not (126 <= len(bv) <= 140 and 108 <= len(av) <= 126):
        return False
    # baseline: story magnitude, stable, normal-enough, Cpk in band
    if not (26.0 <= statistics.fmean(bv) <= 26.8 and 5.6 <= statistics.stdev(bv) <= 6.8):
        return False
    if not imr_rule1_rule4_clean(bv):
        return False
    if scistats.anderson(bv, dist="norm", method="interpolate").pvalue < 0.06:
        return False
    if not (-1.15 <= cpk_upper_only(bv) <= -0.85):
        return False
    # after: goal met on the mean, still not capable, stable, normal-enough
    if not (6.9 <= statistics.fmean(av) <= 7.3 and statistics.stdev(av) <= 2.6):
        return False
    if not imr_rule1_rule4_clean(av):
        return False
    if scistats.anderson(av, dist="norm", method="interpolate").pvalue < 0.06:
        return False
    if not (0.08 <= cpk_upper_only(av) <= 0.24):
        return False
    # Analyze's declared primary: access grants vs the rest (Welch, floors >= 8)
    acc = [r[5] for r in base_rows if r[2] == "access_grant"]
    rest = [r[5] for r in base_rows if r[2] != "access_grant"]
    if len(acc) < 30 or len(rest) < 70:
        return False
    t, p = scistats.ttest_ind(acc, rest, equal_var=False)
    if not (p < 1e-3 and 4.0 <= statistics.fmean(acc) - statistics.fmean(rest) <= 7.5):
        return False
    # T-12 pairs: acceptable band with visible (nonzero) disagreement
    diffs = [b - a for _, a, b in msa_rows]
    s_repeat = math.sqrt(sum(d * d / 2 for d in diffs) / len(diffs))
    s_study = statistics.stdev([a for _, a, _ in msa_rows] + [b for _, _, b in msa_rows])
    if not (0.005 < (s_repeat / s_study) * 100.0 <= 5.0):
        return False
    # tally Pareto: strict order, vital few = top two crossing 80% (engine
    # convention: categories up to and including the one crossing >= 80%)
    counts = [sum(1 for r in tally_rows if r[2] == c) for c in REASONS]
    order = sorted(counts, reverse=True)
    if counts != order or len(set(counts)) < 5:
        return False
    total = sum(counts)
    if not (counts[0] / total < 0.80 <= (counts[0] + counts[1]) / total):
        return False
    if counts[4] < 3:  # tail still visible, not a rounding ghost
        return False
    return True


def main(out_dir):
    for seed in range(5000):
        base_rows, after_rows, msa_rows, tally_rows = simulate(seed)
        if acceptable(base_rows, after_rows, msa_rows, tally_rows):
            break
    else:
        sys.exit("no acceptable seed found in range(5000)")

    with open(f"{out_dir}/tickets-baseline.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "date", "request_type", "channel", "tech", "resolution_hours"])
        w.writerows(base_rows)
    with open(f"{out_dir}/tickets-after.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "date", "request_type", "channel", "tech", "resolution_hours"])
        w.writerows(after_rows)
    with open(f"{out_dir}/msa-repeats.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "first_extract_hours", "second_extract_hours"])
        w.writerows(msa_rows)
    with open(f"{out_dir}/delay-tallies.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticket_id", "date", "primary_delay_reason"])
        w.writerows(tally_rows)

    bv = [r[5] for r in base_rows]
    av = [r[5] for r in after_rows]
    counts = {c: sum(1 for r in tally_rows if r[2] == c) for c in REASONS}
    print(f"seed={seed}")
    print(f"  baseline: n={len(bv)} mean={statistics.fmean(bv):.3f} sd={statistics.stdev(bv):.3f} "
          f"min={min(bv)} max={max(bv)} cpk~{cpk_upper_only(bv):.3f}")
    print(f"  after:    n={len(av)} mean={statistics.fmean(av):.3f} sd={statistics.stdev(av):.3f} "
          f"min={min(av)} max={max(av)} cpk~{cpk_upper_only(av):.3f}")
    print(f"  tallies ({sum(counts.values())}): {counts}")
    acc = [r[5] for r in base_rows if r[2] == "access_grant"]
    rest = [r[5] for r in base_rows if r[2] != "access_grant"]
    print(f"  access n={len(acc)} mean={statistics.fmean(acc):.2f} vs rest n={len(rest)} mean={statistics.fmean(rest):.2f}")
    diffs = [b - a for _, a, b in msa_rows]
    print(f"  msa nonzero-diff items={sum(1 for d in diffs if abs(d) > 1e-9)}/12")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
```
