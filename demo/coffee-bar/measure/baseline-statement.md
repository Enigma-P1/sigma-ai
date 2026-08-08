# Baseline statement — R-MEA-11 (Measure-exit anchor)

## The one-sentence baseline

Average order-to-handoff time (C1), weekday 7:00–10:00 peak, Q2 2026 (10
mornings, 2026-07-20 to 2026-07-31): **mean 8.41 min**, n = 120, **stable**
(0 Western Electric rule-1/rule-4 signals at n=120), **capability claim**
— Cpk **−1.14** vs USL 5.0 min (Cpk, not just Pp/Ppk, licensed because the
process is stable).

## Charter reconciliation

| | Value | Source |
|---|---|---|
| Charter claimed | 8.4 min | `define/charter.json`, Q2 2026, n = 412 |
| Measured baseline | 8.408 min | `measure/baseline-run.md`, live engine, n = 120 |
| Delta | 0.008 min (~0.1% relative) | well under the 10% materiality line |
| Verdict | **Non-material** | charter stands unrevised, no logged edit |
| Goal | **Unchanged** | 8.4 → 5.0 min by 2026-10-31 still fits the measured number |

## Read

The charter's Define-phase magnitude and Measure's independently-computed
baseline agree to within a tenth of a minute, so the number this project
was chartered against needs no revision. What the baseline adds is
stability: the process is not having occasional bad mornings, it is
reliably centered three within-sigmas past the only spec limit — Analyze's
job is common causes built into a stable process, not a special cause that
was never there.
