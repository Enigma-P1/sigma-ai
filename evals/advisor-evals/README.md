# M6 advisor evals

PLAN §9's "Advisor evals" paragraph, verbatim:

> Advisor evals: a frozen set of artifact-review and tollgate calls with
> known-defective artifacts — crude defects (solution-shaped problem
> statement, fishbone with zero evidence) and subtle Green-Belt-fail
> patterns (capability claimed on an unstable process, before/after "proof"
> with a reported confound, control plan with no owner) — the advisor must
> catch them. Run per release like the vault's goldens, with model/version
> pinned per run so results are comparable.

This is a different shape of eval than `evals/harness/` (the golden
scenarios). That harness diffs deterministic engine math against frozen
numbers — the engine is a pure function of its inputs, so a byte-for-byte
diff is the right test. The advisor is not deterministic: it is a live
Claude API call, and grading it means judging whether the model's *prose
and structured verdicts* caught a planted defect, not whether a number
matches. This unit is built around that difference.

## Status: no live run exists yet

**No live run has ever been executed against these fixtures.** There is no
Anthropic API key configured anywhere this unit has been built or tested.
`--live` refuses cleanly and exits non-zero the moment it detects that
(`POST /advisor/status` reports `configured: false`) — it never silently
skips fixtures or fabricates a result. The first live run happens when an
Anthropic API key is configured on the engine (`PUT /advisor/settings` or
the `ANTHROPIC_API_KEY` environment variable) and someone runs:

```
engine/.venv/bin/python evals/advisor-evals/run_advisor_evals.py --live
```

Until that happens, do not read anything under `runs/` as advisor
performance data — the only file there right now (`runs/*-mock.json`) is a
mechanics self-check, not a judgment eval. See "What this ships instead"
below for what *is* proven today.

## The two layers

Every fixture is graded on two independent things, and the fixture set is
built to keep them visibly separate:

1. **Deterministic layer** — what the engine's own schema and rule-based
   pre-score already guarantee, with no model call at all. Recorded in each
   fixture's `*.expect.json` under `deterministic_layer`: whether the
   artifact validates (it always does — see "Why every fixture validates"),
   and the *exact* live pre-score output. This is proven today, on every
   test run, with no API key.
2. **Advisor layer** — judgment only a model call can supply: reading a
   narrative claim against the artifact's own computed facts, grading a
   rubric item that needs plain-English reasoning, playing the Champion at
   a tollgate. This is what `--live` exercises, and what has never run yet.

The point of building the fixtures this way is to make the boundary
between the two layers legible per defect, not just in the abstract: each
`*.expect.json`'s `deterministic_layer.notes` states plainly what code
already catches about that specific artifact and what it structurally
cannot — see each fixture's file for the details; the short version, per
fixture, is in the table below.

## Why every fixture validates (schema-legal by construction)

The advisor only ever sees artifacts a Green Belt student could actually
save in the app — which means every fixture must pass its own schema's
`POST /artifacts/{tool}/validate` (200, `schema_blocks: false` in every
`*.expect.json`). Where the "purest" version of a named defect is
schema-blocked outright (a fishbone cause marked `verified` with no
evidence literally cannot be constructed — `artifacts/fishbone.py`'s
`Cause._evidence_required_when_verified`), that half of the defect is a
**schema test** (see `engine/tests/test_artifacts_fishbone.py`), not an
advisor eval — PLAN §4.2's own hard/soft split says so. The fixture instead
takes the *strongest schema-legal form* of the same defect (candidate
status, no evidence object, but the free text itself asserts proof) and
`schema_note` in that fixture's `*.expect.json` says exactly what was
blocked and why the fixture takes the shape it does.

## The six fixtures

| fixture_id | tool | mode | defect | what code already catches |
|---|---|---|---|---|
| `crude-charter-solution-shaped` | T-03 Charter | review | problem statement embeds the fix; goal is written as the fix | prescore's two solution-language keyword checks fire (`because`, `install`) — the model still has to say the goal/problem need rewriting, not just that a keyword matched |
| `crude-fishbone-zero-evidence` | T-15 Fishbone | review | six causes narrate "proven"/"confirmed" in free text while every status stays `candidate`, no evidence | **nothing** — all 5 prescore checks pass; none of them read cause text against cause status |
| `subtle-capability-on-unstable` | T-20 Proof | validate | `notes` claims a specific before-window Cpk while `before_baseline.stable=false` and `capability.cpk_index=null` (the engine's own gate) | **nothing in prescore**, and `facts_block` for this artifact is empty (confirmed by calling `render_facts_block` directly — see the fixture's notes) — the gate is real and lives in the delimited draft JSON, not in any trusted/flagged tier |
| `subtle-proof-confounded` | T-20 Proof | review | `notes` claims the improvement is "fully attributable" while `confounders.staffing.changed=true` and the engine's own `verdict.headline` already states the confound weakens the proof | prescore's `confounder_echo_present` correctly confirms the ENGINE is honest with itself — it has no way to see, and never compares against, the free-text `notes` |
| `subtle-controlplan-no-owner` | T-22 Control Plan | review | one item is blank-owner, one is `"the team"`/not accepted, one is `"TBD"`/**accepted=true** | blank owner hard-flags; not-accepted soft-flags; the `"TBD"` + accepted=true item passes **both** checks cleanly — it is deterministically indistinguishable from a real accepted owner |
| `tollgate-premature-improve` | T-20 Proof (T-19 never saved) | tollgate (Improve) | a full-rollout claim in `notes` with no Pilot Plan ever saved to the project | **nothing** — `improve_to_control` is still a `kind="stub"` gate (`gates.py`, confirmed live: `POST /gates/check` returns `NOT_YET_BUILT` regardless of project state) and the tollgate context selector silently skips any phase tool with no saved artifact |

Every claim in that table is a live-recorded fact, not an assertion — see
each fixture's `deterministic_layer` for the exact recorded output, and
`engine/tests/test_advisor_evals_fixtures.py` for the test that re-derives
`prescore_flags` fresh on every run and fails loudly if it ever drifts.

## Running it

```
# No key needed, no engine needed -- pure grading-logic self-check:
engine/.venv/bin/python evals/advisor-evals/run_advisor_evals.py --mock

# Needs a live engine at http://127.0.0.1:8000 (override with --engine-url)
# and a configured Anthropic key -- refuses cleanly otherwise:
engine/.venv/bin/python evals/advisor-evals/run_advisor_evals.py --live
```

- **`--mock`**: loads two canned model responses per fixture from
  `fixtures/mock-responses/<fixture_id>.{pass,fail}.json` — one shaped the
  way a response that *caught* the defect would look, one shaped the way a
  response that *missed* it would look — and runs both through the exact
  grading function `--live` uses (`grade_response`). Prints a full
  pass/fail matrix and exits non-zero if the grader ever misclassifies one
  of the twelve (a bug in the grader itself, not a real eval result). No
  network call happens in this mode at all.
- **`--live`**: `POST /advisor/status` first; if the advisor isn't
  configured, refuses with a clear message and exits non-zero *before*
  touching any fixture. Otherwise, per fixture: creates a scratch project
  (`advisor-eval-<fixture_id>`), saves whichever prerequisite artifact the
  fixture needs, calls the real `POST /advisor/ask` (review/tollgate) or
  `POST /advisor/validate` route, and grades the real response. A
  mechanically complete run (every fixture produced a graded result) exits
  0 *regardless of individual pass/fail* — an advisor **missing** a defect
  is exactly the signal this suite exists to surface for review, not a
  runner crash. Only a refusal or a hard setup error (engine unreachable,
  a fixture failing to save) exits non-zero.

Both modes write `runs/<YYYY-MM-DD>-<mode>.json` (UTC date), the pin header
(`engine_version`, `anthropic_sdk_version`, `advisor_model`) plus one row
per fixture (or per canned response, in mock mode).

### The mock-transport proof (a different, deeper check)

`--mock`'s job is to prove the *runner's own grading logic* is sound,
offline. A separate, stronger proof — that a fixture flows correctly
through the actual advisor pipeline (context assembly, token budget,
structured-output parsing and retry, route dispatch) — lives in
`engine/tests/test_advisor_evals_fixtures.py`, using the same technique
`test_routes_advisor.py` already established: `respx` intercepts only the
real `https://api.anthropic.com/v1/messages` endpoint and returns one of
this suite's own canned responses as the model's fenced-JSON text, while
everything else (`TestClient(app)`, real project store, real
`sigma_engine.advisor.*` code) runs for real. One such test exists per
structured mode this fixture set uses (review, tollgate, validate), plus
one proving a malformed model reply still degrades to
`unstructured_fallback` rather than a 500 — the ordinary contract every
other advisor caller in this engine already gets, unmodified here.

## Commit convention — live runs are appended per release

`runs/` accumulates one dated file per invocation; nothing in it is ever
edited by hand or silently overwritten across different days. When a real
release runs `--live`:

1. The resulting `runs/<date>-live.json` is committed alongside that
   release — never squashed into a previous run, never regenerated to
   "fix" an old result. A regression is a real regression; re-running until
   the number looks better defeats the point (the same discipline
   `evals/harness/README.md` states for golden re-freezes).
2. Commit message states the pin (`advisor_model` + `anthropic_sdk_version`
   + `engine_version`) and the headline pass/fail count, so a reviewer can
   compare two releases' runs without opening either file
   (e.g. `Advisor evals 2026-09-01: claude-sonnet-5 / anthropic 0.121.0 /
   engine 0.2.0 -- 5/6 caught, T-20 confound miss under review`).
3. **Comparability is pin-gated, not date-gated**: two runs are only a fair
   comparison if `pins` match (same model, same SDK version, same engine
   version). A run on a different model/engine is a different experiment,
   not a regression — say so if you're citing one against another.
4. A fixture that starts failing across two same-pin runs is a real advisor
   regression, worth its own investigation before the next release — the
   same bar `evals/harness/`'s replay-diff holds engine math to.

## Extending this set

A new fixture needs: a schema-legal `<id>.json` body (validated live before
it ships — see "Why every fixture validates"), a `<id>.expect.json`
sidecar with `deterministic_layer` recorded from an actual live
validate+prescore run (never hand-typed), a `grading` block (one or more
declarative checks — see `run_advisor_evals.py`'s `_CHECK_HANDLERS` for the
supported types, plus a `text_fallback_keywords` list for the
unstructured-output path), and two canned responses under
`fixtures/mock-responses/` proving the grading rule actually discriminates.
`engine/tests/test_advisor_evals_fixtures.py` parametrizes over every file
in `fixtures/*.expect.json` automatically — a new fixture is picked up with
no test-file edit needed.
