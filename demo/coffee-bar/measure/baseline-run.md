# Baseline run — the recorded engine verdict

Not an artifact: this is the recorded result of running the Measure sample
through the live engine's baseline orchestrator on 2026-08-04, after
`wait-times.csv` was saved as a project dataset and the T-12 measurement
check had passed (the engine consults the project's latest T-12 verdict
before it will speak capability language).

## The request

```
POST /stats/baseline
{
  "project_id": "coffee-bar",
  "dataset_id": "<wait-times.csv dataset id>",
  "column": "wait_minutes",
  "usl": 5.0,
  "operational_definition_ok": true
}
```

USL = 5.0 minutes is the customer's own walk-away line (VoC S4: "if it's more
than five minutes I just go to the vending machine"). There is no LSL — a
fast drink has no lower limit — so this is a one-sided study and the engine
reports no Cp/Pp. `operational_definition_ok` is checked on the strength of
the collection plan's confirmed two-people test.

## The engine's verdict (pasted from the response)

- `gate_ok: true`, `n: 120`, `measurement_check: null` (latest T-12 verdict:
  "acceptable" — capability language permitted), `exits: []`
- **Stability:** `stable: true` — `stability_note: "stable: 120 points, no
  default-rule signal"`. I-MR: xbar 8.4083, MRbar 1.1244, sigma_within
  0.9968, individuals limits 5.4180 / 11.3987, MR UCL 3.6733, **0 Western
  Electric signals** (rules 1+4, the frozen defaults; rules 2/3 not enabled).
- **Descriptive:** mean 8.4083, sd 1.0418, median 8.4, Q1 7.7, Q3 9.0,
  min 6.0, max 11.1.
- **Normality:** advisory `no_concern` — Anderson-Darling statistic 0.2126,
  `p_band: "p >= 0.15"`. No EXIT-05 supplement triggered.
- **Capability:** `one_sided: true`, `cp_index: null`, `pp_index: null`
  (one-sided — no Cp/Pp without both limits), **Cpk −1.1398** (within-sigma,
  reported because the process is stable), **Ppk −1.0905** (overall),
  `performance_not_capability: false`.
- **Sigma level:** `dpmo: 999465.4`, `sigma_level: -1.7716`,
  `convention: "with 1.5σ shift"` — the number never travels without its
  label. Observed beyond-USL in the sample itself: 120 of 120 orders
  (100%) exceeded 5.0 minutes; the model-implied expectation is the
  99.9% the DPMO states.
- **Dataset provenance echoed by the engine:** column `wait_minutes`,
  120 rows used, dataset sha256
  `6d31a43fbf305e84fad004cb20d0d06b02a395c3a59f9e6ba89aaf2ba1c72dc0` — re-hash
  the stored v1.csv to confirm this verdict came from this file.

(Each block above arrives wrapped in a provenance object — input hash, method
string, engine version 0.1.0, assumptions, warnings. The full response with
its 120-value input arrays is reproducible from the request; only the values
are transcribed here.)

## Teaching read

Stable but not capable — the two claims are different claims, and this
process earns exactly one of them: nothing special is happening morning to
morning (no signals, limits trustworthy at n=120), the process is simply
*designed* to run at 8.4 minutes against a 5.0-minute limit, so it reliably
makes people wait — every one of 120 sampled orders blew the customer's
five-minute line, and a negative Cpk says the center sits three
within-sigmas past the only spec limit. That is the Measure handoff to
Analyze: don't chase yesterday's bad morning (there wasn't one); find and
remove the common causes — the 4.5-minute cup queue and the grinder rework
the Pareto named — that this stable process is built out of.
