# M6 golden-scenario eval harness

PLAN §9's golden-scenario gate, automated: *"A scripted walkthrough
drives each scenario through every Tier-A tool in its declared scope;
outputs are frozen as goldens and diffed on every change."*

This directory holds two things with different jobs:

- `scenarios/` — the two held-out scenario **specs**: story, pre-collected
  data, and engine-verified ground truth. Read-only input, never shipped
  to users, never touched by the harness.
- `harness/` — the **driver** that reads those specs (plus the Coffee Bar
  demo in `demo/coffee-bar/`) and actually runs them against a live
  engine, and `goldens/` — the frozen output it produces.

## What the harness does

For each of the three scenarios (`coffee-bar`, `s1-helpdesk`,
`s2-library`) `evals/harness/run_goldens.py` drives every Tier-A tool in
that scenario's declared scope against a live engine, in DMAIC order:
create a fresh project, upload datasets, save each artifact (charter,
SIPOC, fishbone, control chart, ...), run the prescore/stats/gate calls a
real user's tools would trigger, and record every response.

- **`coffee-bar`** re-posts the shipped demo's own artifact JSONs
  (`demo/coffee-bar/**/*.json`) in dependency order — they're already
  valid inputs; the harness's job is to prove the *live* engine still
  reproduces the same computed numbers, not to re-author the demo.
- **`s1-helpdesk`** and **`s2-library`** are built from
  `evals/scenarios/*/spec.md`'s story and frontmatter `ground_truth` —
  every dataset value comes from the scenario's own CSVs, every derived
  number (charter baselines, thresholds, aggregates) is computed in
  Python from those same files, never hand-copied from the spec's prose,
  so a driver bug shows up as a numeric mismatch against the live engine
  rather than agreeing with itself.
- **`s2-library` carries PLAN §9's required named-exit trap**: T-12 round
  1 (`msa-round1.csv`) must come back `verdict: "fail"` with an `EXIT-02`
  payload attached — the driver asserts this explicitly and aborts loudly
  if the engine ever stops refusing it — then the run rewrites the
  operational definition, passes T-12 round 2, and only then opens the
  baseline. The refusal is captured verbatim in
  `evals/goldens/s2-library/T-12.round1.validate.json`.

## Freeze vs. replay

```
engine/.venv/bin/python evals/harness/run_goldens.py            # replay (default)
engine/.venv/bin/python evals/harness/run_goldens.py --freeze   # (re-)freeze
engine/.venv/bin/python evals/harness/run_goldens.py --scenario s2-library   # restrict to one (repeatable)
```

Requires a live engine at `http://127.0.0.1:8000` (override with
`--engine-url`); the harness runs *outside* the engine package (plain
Python + `httpx`, invoked via `engine/.venv/bin/python` since that's the
one interpreter already carrying `httpx` — the harness imports nothing
from `sigma_engine`).

- **Replay** (default, what CI runs): drives every scenario, diffs each
  step's normalized response against its frozen file in
  `evals/goldens/<scenario>/`, and exits 1 with a readable per-step
  unified diff if anything differs — a value changed, a golden file is
  missing, or a golden file on disk was never touched this run (a step
  got renamed or removed without a re-freeze). Exits 0 clean otherwise.
- **Freeze** writes (overwrites) the goldens instead of diffing. It also
  wipes the target scenario's golden directory first, so a renamed or
  deleted step can never leave a stale file behind for replay to
  (correctly) flag as orphaned on the *next* person's run.

Every response is **normalized** before it's written or compared
(`evals/harness/lib/normalize.py`): the engine is deterministic
everywhere except two server-generated ids — `dataset_id` and `image_id`
(both `uuid4().hex`, confirmed by reading `routes/datasets.py` and
`routes/floorplans.py`) — which are replaced with a stable placeholder,
by key name and (as defense in depth) by matching the bare 32-hex-char
shape those ids always take, wherever it shows up in the tree. Every
timestamp in this engine is caller-supplied, never `datetime.now()`
server-side, so the scenario drivers simply hardcode them — nothing else
needs normalizing. Goldens are canonical JSON: sorted keys, fixed indent,
one trailing newline, so two runs that compute the same thing always
produce byte-identical files.

## Re-freezing legitimately

A golden diff is a signal, not an obstacle. Before re-freezing:

1. **Understand *why* the numbers changed.** A real engine fix/regression
   in `engine/sigma_engine/` is the expected reason; if the diff doesn't
   trace to an intentional code change, it's a regression — fix the
   engine, don't launder it through a re-freeze.
2. **Re-freeze only the affected scenario(s)** with `--scenario`, review
   the diff in the golden files themselves (they're plain JSON — a normal
   `git diff` reads fine), then run a full replay to confirm it's clean.
3. **State the reason in the commit message.** The convention: a commit
   that touches `evals/goldens/` must say *what changed in the engine and
   why the new numbers are correct* (not just "update goldens") — e.g.
   `Fix Welch t df rounding; re-freeze s1-helpdesk T-17 (was truncating,
   now matches NIST §7.3.1)`. A golden-only commit with no such
   explanation should be treated as a red flag in review.

The two other artifacts below are regenerated (and, on a full run,
diffed) every invocation — never hand-edited, and never need a separate
freeze step of their own.

## `coverage.json` — collective in-scope coverage

Requirement: the three scenarios' declared in-scope tool sets must
collectively equal `docs/traceability-matrix.md` §1's Tier-A 25, with no
drift between the matrix, the specs, and the goldens. `run_goldens.py`
asserts this in code on every invocation (`lib/coverage.py`) and fails
loudly, before anything else runs, if it ever doesn't hold — a matrix
edit that adds/removes a Tier-A tool, or a spec edit that changes
`in_scope_tools`/`na_tools`, without updating the other side, is exactly
what this is for. `evals/goldens/coverage.json` is the resulting
coverage-by-scenario table (which scenario(s) cover which tool, and why a
tool is honestly N/A where it is) — always regenerated fresh from the
live matrix + specs, only ever written on a full (all-three-scenario)
run, since it's inherently a cross-scenario report.

## `golden-id-map.json` — golden-id reconciliation

`docs/traceability-matrix.md` cites golden ids throughout (`G-imr-01`,
`G-pchart-01`, `G-yield-01`, ...) as the promised proof for each BoK
row's coverage. `evals/goldens/golden-id-map.json` maps every one of
those ids (grepped out of the matrix, never hand-copied) to where it's
actually proven:

- **`unit-test`** — the literal id string appears in an
  `engine/tests/test_*.py` file (grepped, not a hardcoded guess).
- **`harness-step`** — one of this run's three scenario drivers exercises
  the tool surface that id belongs to (a hand-curated
  `(scenario, tool_id)` table in `lib/golden_id_map.py`, checked every
  run against the matrix's own id set so it can never silently go stale).
- **`uncovered`** — neither, reported honestly with a one-line reason.
  Ids that describe a case none of these three particular stories needs
  (unstable baseline, one-way ANOVA, the nonparametric fallbacks, the
  selector exits, one-proportion-vs-target, the PDCA quick path) carry
  pinned unit-test homes instead — named `test_G_<id>_...`, each with
  hand-checked reference values — plus a `design_note` stating why no
  harness step covers them. One id, `G-scatter-01`, has no engine-side
  computation to exercise at all (v1 scatter plots are visual-only); its
  entry carries an explicit documented status
  (`v1-scope-debt: no engine computation exists; scatter ships
  visual-only per matrix §5a A-2`) rather than fake coverage.

As of the current three-scenario freeze: **40 of 41 covered, 1
uncovered** — the one being `G-scatter-01`'s documented v1-scope debt
(see `evals/goldens/golden-id-map.json` for the full per-id breakdown
and reasons).

## Tests

`engine/tests/test_eval_harness.py` covers the harness's own machinery
(not the scenario content, which the live-engine replay already proves):
normalizer determinism, the manifest schema, the coverage-check's failure
mode, and the matrix/golden-id parsers against the real files.
