# S-2 data — seven pre-collected scenario inputs, engine-verified (trap included)

The S-2 eval scenario's complete data package: the bait log, the two-rater
judgment sets that make the EXIT-02 trap real, the written-definition
baseline audit with its defect marks, and the post-change window. These
are **eval scenario inputs** (PLAN §9: pre-collected and realistic), not
artifacts: an eval run feeds them into the tools and must reproduce the
engine verdicts recorded below — including the one that says *stop*.

## The files

- `prelog-daily.csv` — **the bait**: 15 service days (2026-08-10 →
  2026-08-26) of the closers' informal misshelve log. Schema-clean,
  plausible, chartable — and counted by two people under two private
  definitions, which no engine check can see. The `logged_by` column is
  the discoverable tell.
- `msa-round1.csv` — T-12 round 1: 50 flagged shelf positions (34 staged
  correct, 16 planted errors), judged pass/fail independently by Alan
  Wexford (rater A) and Mira Chen (rater B). `planted` records the staged
  truth per position; only the two rater columns feed the T-12 artifact
  (1 = pass, matching the engine's `rater_a`/`rater_b` booleans).
- `msa-round2.csv` — T-12 round 2, same shape: a fresh 50-position planted
  set two days after the written definition, same raters, round-1 sheets
  sealed. Round-2 planted categories reflect the written rules
  (`series-by-author`, `oversize-no-marker` are definite fails under them).
- `baseline-audit.csv` — 63 rows: 21 service days × 3 sections (adult /
  juvenile / nonfiction), `items_audited` and `misshelved` per cell, under
  the written definition, 2026-08-31 → 2026-09-24. Daily p-chart
  subgroups are the per-date sums; per-section columns feed the chi-square
  screen and stratified views.
- `baseline-defect-marks.csv` — 90 rows, one per misshelved book (date,
  section, `defect_type`): the check-sheet marks behind the Pareto.
- `after-audit.csv` — 72 rows: 24 service days × 3 sections, 2026-10-05 →
  2026-10-31, same definition and procedure (pre-sorted carts live
  2026-09-28; bedding-in week excluded by declaration).
- `after-defect-marks.csv` — 39 rows, same shape as the baseline marks.

## The numbers, and the checks made

- **The trap bands are engine-landed, not approximate**: round 1 kappa
  0.3363 sits in the frozen fail band (< 0.40) with a
  deliberately fine-looking 70% raw agreement; round 2 kappa 0.8777 sits
  in the acceptable band (≥ 0.75) with three honest residual splits. Both
  split directions exist in round 1 (13 A-pass/B-fail, 2 B-pass/A-fail) —
  a genuine two-definition disagreement, not one blind rater.
- Bait vs truth: pre-log pooled 258/6,743 = **3.83%** (Alan's closing days
  2.99%, Mira's 4.83%); written-definition baseline **6.53%** — the broken
  gauge hid roughly two-fifths of the problem. The two numbers disagree by
  design; only one of them has a measurement system behind it.
- Baseline: 21 daily subgroups, n varying 44–77 (Saturdays light), 90
  misshelved of 1,379 audited — **stable in proportions** (zero
  rule-1/rule-4 signals, engine-frozen). After: 24 subgroups, 39/1,526 =
  **2.56%**, own limits clean, freeze floor met.
- Marks reconcile exactly: 90 baseline mark rows = the audit file's
  misshelved sum, per (date, section); 39 after marks likewise. Strict
  Pareto order with the vital few crossing 80% at the second category
  (engine convention).
- Section structure is real: juvenile 10.5% vs adult 3.4% at baseline —
  the chi-square screen is significant and Cochran-clean (all expected
  counts ≥ 5).
- Import quality scan on save: 0 missing values, 0 non-numeric values, 0
  duplicate rows, all seven files.
- Every post-window day sits below the frozen baseline center, so the
  improvement reads on the old limits as **exactly one maximal rule-4
  run** — engine-confirmed below.

## Engine verification transcript (2026-08-08, engine 0.1.0)

Every claimed number below is pasted from live-engine responses at
`http://127.0.0.1:8000`; requests are reproducible from the CSVs.

**`POST /artifacts/T-12/validate`** (attribute, round 1 judgments):
verdict **fail** — kappa **0.336283**, % agreement **70.0** (p_observed
0.70, p_expected 0.5480), n = 50 — with the EXIT-02 payload attached by
the engine: "Stop — fix your measurement first. Capability-claim language
is blocked, and downstream results render as 'unreliable — measurement
system failed' until this is fixed." (routes to: rework the operational
definition in T-11, then re-run T-12.)

**`POST /artifacts/T-12/validate`** (attribute, round 2 judgments):
verdict **acceptable** — kappa **0.877651**, % agreement **94.0**
(p_expected 0.5096), n = 50. No exit payload.

**`POST /artifacts/T-21/validate`** (chart_type p, defectives selector,
21 daily baseline subgroups, `freeze_requested: true`): frozen — k = 21,
total n = 1,379, defectives 90, **p̄ 0.065265**, per-day limits, **zero
signals**, freeze floor met. Worst day 2026-09-10: p 0.1169 inside its
own UCL 0.1497.

**`POST /artifacts/T-21/validate`** (the frozen echo re-validated with
the 24 post-window days appended, no re-freeze): **exactly one signal** —
`rule4`, "24 consecutive points fall below the center line (indices
21–44)", side below — the improvement arriving on the old limits, and
nothing else firing.

**`POST /artifacts/T-21/validate`** (post window alone, own limits,
freeze requested): k = 24, total n = 1,526, defectives 39, **p̄
0.025557**, zero signals, freeze floor met (24 ≥ 20).

**`POST /artifacts/T-10/validate`** (DPMO block: 90 defects, 1,379 units,
1 opportunity/unit — the honest floor): **DPMO 65,264.7, sigma level
3.0120, convention "with 1.5σ shift"**; single-step FPY 0.9347; RTY null
(`steps_in_series: false` — no serial-steps claim).

**`POST /stats/pareto`** (90 baseline marks): out-of-order within bay 44
(48.89%) → cum 48.89%; wrong bay 29 (32.22%) → **cum 81.11%, vital-few
count 2**; series shelved by author 10 (11.11%); oversize/flat exception
7 (7.78%); `flat: false`. After marks (39): 20 / 11 / 5 / 3 — series
errors nearly gone, within-bay transpositions still the (much smaller)
head.

**`POST /stats/hypothesis/run`** (association_categorical, the declared
non-primary screen — misshelved-vs-ok × section, table [[19, 46, 25],
[534, 393, 362]]): `chi_square_independence`, **χ² 19.9002, df 2,
p = 4.77e-05, Cramér's V 0.1201**; not refused (Cochran clean). Rates:
adult 19/553 = 3.44%, juvenile 46/439 = 10.48%, nonfiction 25/387 = 6.46%.

**`POST /stats/hypothesis/run`** (proportions, the pre-declared primary —
baseline 90/1,379 vs settled weeks 19/753): `two_proportion_z`, **z =
4.0112, p = 6.04e-05, risk difference +0.0400 (CI +0.0218 to +0.0569)**;
floors cleared.

**`POST /stats/sample-size`** (proportion calculator, planning_p 0.05,
margin 0.015, 95%): **n = 811** (n_exact 810.97). Achieved baseline
n = 1,379.

Derived arithmetic the tools recompute in-run: goal 0.0326325 (half of
p̄); gap 0.0326325; recovered 0.065265 − 0.025557 = 0.039708 = **121.7%**,
remaining **−0.0071**. Settled-weeks slice: 19/753 = 2.52%.

## Reproducibility

This is eval fixture data: it was generated by the seeded script below,
engineered to tell the scenario's true story — two counters with two
private definitions producing a plausible ~3.8% log while the
written-definition truth is ~6.5% and stable, a round-1 judgment set that
genuinely fails kappa and a round-2 set that genuinely passes, then a
deliberate 2026-09-28 pre-sort change that cuts the rate to ~2.6% — with
realistic section structure and Saturday-light audit volumes. The script
searches seeds from 0 and keeps the first passing every acceptance check:
round-1 kappa in 0.25–0.372 with 70–78% agreement and both split
directions present, round-2 kappa in 0.78–0.92 with ≥ 90% agreement and
≥ 1 residual split, bait rate 3.0–4.2% with the Alan-under-Mira
fingerprint visible, baseline p̄ 6.2–7.4% with no rule-1/rule-4 signal
(the engine's frozen p-chart defaults mirrored, per-day limits included),
marks in strict Pareto order crossing 80% at the second category, a
Cochran-clean significant section chi-square with juvenile ≥ 1.7× adult,
a post window at 2.4–3.4% that is clean on its own limits with every day
below the frozen baseline center (so the improvement fires as one
maximal rule-4 run), and a settled-weeks two-proportion z at p < 1e-3
with its floors cleared. **Seed 120** is the first acceptable seed and
produced all seven files. The binding verdicts remain the live engine's,
which every number above was run through after generation. Run with
`engine/.venv/bin/python` (scipy for the chi-square/z pre-checks).

```python
#!/usr/bin/env python3
"""Generate evals/scenarios/s2-library/data/ -- the S-2 held-out eval
scenario's pre-collected inputs: the bait (an unpedigreed daily misshelve
log that LOOKS p-chart-ready), the two-rater judgment sets that make the
named-exit trap real (round 1 must FAIL the engine's kappa check, round 2
-- after the written definition -- must pass), the post-definition 21-day
baseline audit, its defect-type marks, and the 24-day post-change window.
One seeded simulation, engineered to tell the scenario's true story: two
counters with two private definitions produce a plausible-looking ~3.6%
log while the written-definition rate is ~6.8%, stable; the pre-sorted-
carts change then cuts the rate to ~2.9%. The binding verdicts are always
the live engine's (T-12 kappa bands, T-21 p-chart rules, Pareto, chi-
square, two-proportion floors) -- the script only mirrors them to search
seeds. Run with engine/.venv/bin/python (scipy for chi-square/z pre-checks).
"""
import csv
import math
import random
import sys

from scipy import stats as scistats

# --- calendar: Mon-Sat service days ------------------------------------------
def service_days(start_iso, n_days):
    import datetime as dt
    d = dt.date.fromisoformat(start_iso)
    out = []
    while len(out) < n_days:
        if d.weekday() != 6:  # closed Sundays
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out

PRELOG_DATES = service_days("2026-08-10", 15)    # -> 2026-08-26 (the bait log)
BASELINE_DATES = service_days("2026-08-31", 21)  # -> 2026-09-24 (written-definition audit)
POST_DATES = service_days("2026-10-05", 24)      # -> 2026-10-31 (pre-sorted carts live 2026-09-28; week 1 declared bedding-in)

# --- T-12 judgment-set model -------------------------------------------------
# Planted 50-position audit sets (category, count). Round 1 runs against two
# PRIVATE definitions; round 2 against the written one. rater A = Alan
# Wexford (fails out-of-bay placements only), rater B = Mira Chen (strict on
# exact order, inconsistent on conventions). Probabilities = P(rater FAILS
# the item) per category.
ROUND1_MIX = [("ok", 26), ("transposed-within-bay", 8), ("wrong-bay", 7),
              ("series-convention", 4), ("oversize-marker", 3), ("flat-on-top", 2)]
R1_P_FAIL = {  # (alan, mira)
    "ok": (0.02, 0.08),
    "transposed-within-bay": (0.05, 0.80),
    "wrong-bay": (0.97, 0.97),
    "series-convention": (0.05, 0.50),
    "oversize-marker": (0.05, 0.25),
    "flat-on-top": (0.10, 0.80),
}
ROUND2_MIX = [("ok", 30), ("transposed-within-bay", 9), ("wrong-bay", 5),
              ("series-by-author", 3), ("oversize-no-marker", 2), ("flat-on-top", 1)]
R2_TRUE_FAIL = {"ok": False, "transposed-within-bay": True, "wrong-bay": True,
                "series-by-author": True, "oversize-no-marker": True, "flat-on-top": True}
R2_ERR = 0.05  # per-rater slip rate against the written definition

# --- process model -----------------------------------------------------------
SECTIONS = ["adult", "juvenile", "nonfiction"]
AUDIT_N = {"adult": 27, "juvenile": 21, "nonfiction": 19}  # per-day audited, +/- noise
SAT_FACTOR = 0.78                                          # lighter Saturday audits
BASE_RATE = {"adult": 0.048, "juvenile": 0.102, "nonfiction": 0.057}
# The one change (carts leave the sorting room in final shelf order, posted
# standard + exception flags): retention multiplier per defect type.
TYPES = ["out-of-order within bay", "wrong bay", "series shelved by author", "oversize/flat exception"]
TYPE_MIX = {  # per section: P(type | misshelved)
    "adult":      [0.62, 0.29, 0.00, 0.09],
    "juvenile":   [0.48, 0.21, 0.26, 0.05],
    "nonfiction": [0.60, 0.31, 0.00, 0.09],
}
RETENTION = {"out-of-order within bay": 0.30, "wrong bay": 0.45,
             "series shelved by author": 0.35, "oversize/flat exception": 0.60}
# The bait log: whole-day shelving volume with two private definitions --
# Alan's out-of-bay-only rule sees less than half of the true rate; Mira
# catches more, inconsistently. logged_by alternates with the closing rota.
SHELVED_PER_DAY = (380, 520)
PRELOG_CATCH = {"alan": 0.42, "mira": 0.70}  # share of true misshelves each counter logs
TRUE_RATE_PRELOG = 0.066


def judgment_set(rng, mix, p_fail, prefix):
    rows, i = [], 0
    order = [c for c, n in mix for _ in range(n)]
    rng.shuffle(order)
    for cat in order:
        i += 1
        pa, pb = p_fail[cat]
        a_fail = rng.random() < pa
        b_fail = rng.random() < pb
        rows.append([f"{prefix}-{i:02d}", cat, int(not a_fail), int(not b_fail)])
    return rows


def judgment_set_written(rng, mix, prefix):
    rows, i = [], 0
    order = [c for c, n in mix for _ in range(n)]
    rng.shuffle(order)
    for cat in order:
        i += 1
        true_fail = R2_TRUE_FAIL[cat]
        a_fail = true_fail if rng.random() > R2_ERR else not true_fail
        b_fail = true_fail if rng.random() > R2_ERR else not true_fail
        rows.append([f"{prefix}-{i:02d}", cat, int(not a_fail), int(not b_fail)])
    return rows


def kappa(rows):
    n = len(rows)
    agree = sum(1 for r in rows if r[2] == r[3]) / n
    a_pass = sum(r[2] for r in rows) / n
    b_pass = sum(r[3] for r in rows) / n
    p_e = a_pass * b_pass + (1 - a_pass) * (1 - b_pass)
    return agree, (agree - p_e) / (1 - p_e)


def day_audit_n(rng, date, section):
    import datetime as dt
    base = AUDIT_N[section]
    if dt.date.fromisoformat(date).weekday() == 5:
        base *= SAT_FACTOR
    return max(10, round(rng.gauss(base, 2.5)))


def simulate_audits(rng, dates, rate_fn):
    """-> per-(date, section) rows [date, section, audited, misshelved, marks]"""
    out = []
    for date in dates:
        for sec in SECTIONS:
            n = day_audit_n(rng, date, sec)
            p = rate_fn(sec)
            mis = sum(1 for _ in range(n) if rng.random() < p)
            marks = [rng.choices(TYPES, weights=TYPE_MIX[sec])[0] for _ in range(mis)]
            out.append([date, sec, n, mis, marks])
    return out


def post_rate(sec):
    return BASE_RATE[sec] * sum(w * RETENTION[t] for t, w in zip(TYPES, TYPE_MIX[sec]))


def simulate(seed):
    rng = random.Random(seed)
    r1 = judgment_set(rng, ROUND1_MIX, R1_P_FAIL, "SR1")
    r2 = judgment_set_written(rng, ROUND2_MIX, "SR2")
    prelog = []
    rota = ["alan", "mira", "alan", "mira", "alan", "mira"]  # Mon..Sat closers
    import datetime as dt
    for date in PRELOG_DATES:
        who = rota[dt.date.fromisoformat(date).weekday()]
        shelved = rng.randint(*SHELVED_PER_DAY)
        true_mis = sum(1 for _ in range(shelved) if rng.random() < TRUE_RATE_PRELOG)
        logged = sum(1 for _ in range(true_mis) if rng.random() < PRELOG_CATCH[who])
        prelog.append([date, shelved, logged, who])
    baseline = simulate_audits(rng, BASELINE_DATES, lambda s: BASE_RATE[s])
    post = simulate_audits(rng, POST_DATES, post_rate)
    return r1, r2, prelog, baseline, post


# --- engine-rule mirrors (binding verdicts stay the live engine's) -----------
def p_chart_clean(subs, pbar=None):
    """Mirror stats/p_chart.py rule 1 (per-point limits) + rule 4 (8 same side)."""
    if pbar is None:
        pbar = sum(d for _, d in subs) / sum(n for n, _ in subs)
    for n, d in subs:
        sp = 3 * math.sqrt(pbar * (1 - pbar) / n)
        if d / n > min(pbar + sp, 1.0) or d / n < max(pbar - sp, 0.0):
            return False
    side, run = 0, 0
    for n, d in subs:
        s = 1 if d / n > pbar else (-1 if d / n < pbar else 0)
        run = run + 1 if (s == side and s != 0) else (1 if s else 0)
        side = s
        if run >= 8:
            return False
    return True


def daily(subrows):
    days = {}
    for date, _sec, n, mis, _marks in subrows:
        days.setdefault(date, [0, 0])
        days[date][0] += n
        days[date][1] += mis
    return [(v[0], v[1]) for _, v in sorted(days.items())]


def acceptable(r1, r2, prelog, baseline, post):
    # -- the trap: round 1 in the FAIL band, agreement still plausible-looking
    ag1, k1 = kappa(r1)
    if not (0.25 <= k1 <= 0.372 and 0.70 <= ag1 <= 0.78):
        return False
    # both split directions present (a real disagreement, not one blind rater)
    if not (sum(1 for r in r1 if r[2] == 1 and r[3] == 0) >= 8
            and sum(1 for r in r1 if r[2] == 0 and r[3] == 1) >= 1):
        return False
    # -- round 2 comfortably acceptable but honest (>=1 residual split)
    ag2, k2 = kappa(r2)
    if not (0.78 <= k2 <= 0.92 and ag2 >= 0.90):
        return False
    if sum(1 for r in r2 if r[2] != r[3]) < 1:
        return False
    # -- bait log: plausible, materially under the written-definition truth,
    #    with the two-counter fingerprint visible (alan days < mira days)
    p_pre = sum(r[2] for r in prelog) / sum(r[1] for r in prelog)
    if not (0.030 <= p_pre <= 0.042):
        return False
    alan = [r for r in prelog if r[3] == "alan"]
    mira = [r for r in prelog if r[3] == "mira"]
    if not (sum(r[2] for r in alan) / sum(r[1] for r in alan) + 0.012
            < sum(r[2] for r in mira) / sum(r[1] for r in mira)):
        return False
    # -- baseline: story magnitude, stable in proportions, chartable
    subs = daily(baseline)
    N = sum(n for n, _ in subs)
    D = sum(d for _, d in subs)
    if not (0.062 <= D / N <= 0.074 and N >= 1250):
        return False
    if not p_chart_clean(subs):
        return False
    # -- defect-type Pareto: strict order, vital few = top two crossing 80%
    marks = [m for row in baseline for m in row[4]]
    counts = [marks.count(t) for t in TYPES]
    if sorted(counts, reverse=True) != counts or len(set(counts)) < 4:
        return False
    tot = sum(counts)
    if not (counts[0] / tot < 0.80 <= (counts[0] + counts[1]) / tot):
        return False
    if counts[3] < 4:
        return False
    # -- chi-square screen: misshelved-vs-ok x section, Cochran-clean and
    #    significant, juvenile visibly worse (the mix is method-shaped where
    #    conventions bite)
    by_sec = {s: [0, 0] for s in SECTIONS}
    for _date, sec, n, mis, _m in baseline:
        by_sec[sec][0] += n
        by_sec[sec][1] += mis
    table = [[by_sec[s][1] for s in SECTIONS], [by_sec[s][0] - by_sec[s][1] for s in SECTIONS]]
    exp = scistats.contingency.expected_freq(table)
    if min(e for row in exp for e in row) < 5:
        return False
    chi2, pval, dof, _ = scistats.chi2_contingency(table, correction=False)
    if pval > 0.01:
        return False
    if not (by_sec["juvenile"][1] / by_sec["juvenile"][0]
            >= 1.7 * by_sec["adult"][1] / by_sec["adult"][0]):
        return False
    # -- post window: on story, own-limits clean (24 >= 20 freeze floor),
    #    every day below the baseline center (the improvement reads as one
    #    long rule-4 run on the old limits)
    psubs = daily(post)
    Np = sum(n for n, _ in psubs)
    Dp = sum(d for _, d in psubs)
    if not (0.024 <= Dp / Np <= 0.034):
        return False
    if not p_chart_clean(psubs):
        return False
    if not all(d / n < D / N for n, d in psubs):
        return False
    # -- pre-declared primary (first 12 settled days vs baseline): floors + z
    N2 = sum(n for n, _ in psubs[:12])
    D2 = sum(d for _, d in psubs[:12])
    if D2 < 15:
        return False
    pp = (D + D2) / (N + N2)
    z = (D / N - D2 / N2) / math.sqrt(pp * (1 - pp) * (1 / N + 1 / N2))
    if 2 * (1 - scistats.norm.cdf(abs(z))) > 1e-3:
        return False
    return True


def main(out_dir):
    for seed in range(20000):
        r1, r2, prelog, baseline, post = simulate(seed)
        if acceptable(r1, r2, prelog, baseline, post):
            break
    else:
        sys.exit("no acceptable seed found in range(20000)")

    with open(f"{out_dir}/msa-round1.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "planted", "rater_a_pass", "rater_b_pass"])
        w.writerows(r1)
    with open(f"{out_dir}/msa-round2.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "planted", "rater_a_pass", "rater_b_pass"])
        w.writerows(r2)
    with open(f"{out_dir}/prelog-daily.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "items_shelved", "misshelves_logged", "logged_by"])
        w.writerows(prelog)
    for name, subrows in (("baseline-audit.csv", baseline), ("after-audit.csv", post)):
        with open(f"{out_dir}/{name}", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "section", "items_audited", "misshelved"])
            w.writerows([[d, s, n, m] for d, s, n, m, _ in subrows])
    for name, subrows in (("baseline-defect-marks.csv", baseline), ("after-defect-marks.csv", post)):
        with open(f"{out_dir}/{name}", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "section", "defect_type"])
            w.writerows([[d, s, m] for d, s, _n, _mis, marks in subrows for m in marks])

    ag1, k1 = kappa(r1)
    ag2, k2 = kappa(r2)
    subs, psubs = daily(baseline), daily(post)
    N, D = sum(n for n, _ in subs), sum(d for _, d in subs)
    Np, Dp = sum(n for n, _ in psubs), sum(d for _, d in psubs)
    marks = [m for row in baseline for m in row[4]]
    print(f"seed={seed}")
    print(f"  round1: agreement={ag1:.3f} kappa={k1:.4f}   round2: agreement={ag2:.3f} kappa={k2:.4f}")
    print(f"  prelog: p={sum(r[2] for r in prelog)/sum(r[1] for r in prelog):.4f}")
    print(f"  baseline: N={N} D={D} pbar={D/N:.5f}   post: N={Np} D={Dp} p={Dp/Np:.5f}")
    print(f"  marks: {[(t, marks.count(t)) for t in TYPES]}")
    N2 = sum(n for n, _ in psubs[:12]); D2 = sum(d for _, d in psubs[:12])
    print(f"  settled 12 days: N={N2} D={D2} p={D2/N2:.5f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
```
