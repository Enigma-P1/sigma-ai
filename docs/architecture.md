# Sigma AI — architecture

The design writeup PLAN.md §8 (milestone 6) promises: how the suite is
built, why it is built that way, and where each honesty mechanism lives in
the code. Written for a technical reader evaluating the design; every file
path below is real and checkable.

## The two-layer shape

The product is a local desktop app in two strictly separated layers:

- **Layer 1** — a deterministic tool suite: a Python statistics engine
  (FastAPI + Pydantic + SciPy) and a React/Tauri desktop interface. Fully
  functional with no AI and no internet. This layer is the product's floor
  and its credibility: every number a user ever sees is computed here.
- **Layer 2** — an AI advisor (Claude API) that reviews, explains, and
  advises *about* Layer 1's artifacts. It is strictly optional, degrades to
  a clean disabled state with no key, and is structurally prevented from
  producing numbers (§ six layers, below).

The separation is the architecture's one big decision, and everything else
follows from it: the model explains and critiques; the engine computes and
refuses. A documented LLM failure mode — the confident wrong statistic — is
handled by never asking the model for a statistic.

## The engine (`engine/sigma_engine/`)

A FastAPI app (`main.py`), bound to `127.0.0.1` only, serving ~12 routers
(`routes/`). Ships as a PyInstaller sidecar in the packaged app (port 8756)
or via uvicorn in development (port 8000). The parts that matter:

- **Artifacts are Pydantic models with a recompute pattern**
  (`artifacts/*.py`, one module per tool). Every computed field (a COPQ
  total, an MSA verdict, a proof's gap arithmetic) is *unconditionally
  recomputed inside model validation* from the artifact's input fields —
  whatever a caller submits for those fields is thrown away and rebuilt. The
  save route (`routes/artifacts.py`) persists `model_dump()` of the
  validated model, so what is on disk is always the engine's own arithmetic,
  never the client's.
- **Provenance objects** (`provenance.py`). Every computed result is a
  frozen `Computed[T]` wrapper: value plus a `ProvenanceRecord` — SHA-256
  input hash, method identifier, engine version, assumptions checked,
  warnings. Frozen models close the mutation path; the one honest limit
  (Python has no private constructors, and loading saved JSON needs the
  public one) is documented in the module docstring rather than hidden.
- **Statistics** (`stats/`): I-MR and p-chart math, capability, normality,
  sigma/DPMO conversion, the hypothesis selector and runners (parametric,
  nonparametric, categorical), MSA, Pareto, sample size. Constants come from
  published tables (`stats/constants.py`); formula implementations cite
  their NIST/SEMATECH section at the definition site; NIST reference
  datasets ship in-repo (`nist_lew.py`, `nist_lottery.py`, `nist_mavro.py`)
  and anchor the unit tests (`engine/tests/`, 1552 tests).
- **Gates** (`gates.py`) — a small state machine with two deliberately
  different kinds. Soft sequence gates (`define_to_measure`, …) warn, list
  what's missing, and clear via a *logged* override whose recorded
  missing-set must still match (`_covering_override` — a stale override
  clears nothing). Hard gates refuse outright: `intake_picker_not_exit01`
  and `measure_capability_language_requires_msa_pass`, the rule that blocks
  capability language until a measurement check passes.
- **Prescore** (`prescore/`, one module per tool + `cross_checks.py`) — the
  deterministic, rule-checkable subset of the grading rubric, run on every
  save and returned as pass/flag/hard-flag per check. This is what makes the
  advisor cheap and honest: code rediscovers nothing at model time.
- **Storage** (`project_store.py`): one folder per project, one JSON file
  per artifact *version* (every save is a new version), an append-only
  override log, atomic tempfile-rename writes. Projects are portable by
  copying a folder.
- **Exports** (`export/`): PDF via ReportLab (pure Python — chosen over
  WeasyPrint specifically to avoid native Pango/GTK dependencies that would
  sink a clean-machine install).

## The desktop (`desktop/src/`)

React 19 + TypeScript in a Tauri v2 shell; Konva for the two canvas tools
(process map, spaghetti tracer, fishbone), Plotly for charts, hand-rolled
hash routing (four top-level routes, no router library).

- **A single fetch path.** Every engine call goes through `api/client.ts`;
  `api/runtime.ts` resolves the base URL exactly once — the Tauri sidecar
  (`127.0.0.1:8756`) inside the packaged app, or a same-origin `/engine-api`
  proxy under the Vite dev server (`vite.config.ts`), which exists because
  the engine deliberately sends no CORS headers. No component talks to the
  network on its own.
- **The helper-frame teaching system** (`tools/HelperFrame.tsx`). Every tool
  screen renders the same five-part frame — what this is / when to use it
  and when not to / per-field guidance with one good and one bad example /
  what good looks like / common mistakes — from per-tool content modules
  (`tools/*/…Content.ts`). The "what good looks like" checklist is *drawn
  from the same rubric items the grader and advisor use* (`tools/rubricCite.ts`),
  so the teaching text and the grading text cannot drift apart.
- **Verdicts over widgets.** Computed results render as plain-English
  verdict banners (`design/components/VerdictBanner.tsx`) with the number
  underneath — "stable: 120 points, no default-rule signal" first, the
  control limits second. The prescore strip (`tools/PrescoreStrip.tsx`)
  renders every rule-based check with its status; field-level flags repeat
  the same information on the field where the fix belongs.
- **Workspace shell** (`app/`): DMAIC rail with per-phase gate status, gate
  banners with the logged-override flow, the "I'm stuck" button
  (`app/stuckTree.ts` — the offline decision tree), and a save-state
  context so the top bar always tells the truth about unsaved work.

## Packaging (`.github/workflows/build.yml`)

One installer per platform, no Python on the user's machine:

- `scripts/build-sidecar.sh` runs **PyInstaller in onefile mode** over the
  engine and renames the single self-contained executable to Tauri's
  expected `sigma-engine-<target-triple>` form in
  `desktop/src-tauri/binaries/`. That one file is the whole artifact: Tauri
  ships it via `externalBin`, and its bootloader unpacks the interpreter and
  scipy's native libs to a temp dir at launch. Onefile is used precisely
  because there is then no sibling support directory to go missing — the
  earlier onedir build shipped a `_internal/` folder that the exe resolved
  relative to its own path, that path broke inside the installed MSI and
  inside the `.app` (PYI-9202, hit as a real CI failure), and the sidecar
  never started for the first installed user.
- **Windows:** `tauri build` produces `.msi` and NSIS `.exe` bundles. CI
  does not take the staging on faith: the workflow launches the *staged*
  sidecar on the real Windows runner and asserts `/health` and the NIST
  `/smoke` check (`match: true`) before packaging.
- **macOS:** the Mac job builds the `.app` only, smoke-tests the sidecar at
  `Contents/MacOS/sigma-engine` on the real runner, and only then seals the
  `.dmg` with `hdiutil` — because a dmg is a sealed image you cannot patch
  afterwards. With onefile there is no `_internal` relocation step; that
  fixup existed for the onedir layout and was removed with it.
- The **sidecar's lifetime is bounded by the app's**, not by a kill signal.
  Tauri's `CommandChild::kill()` can only SIGKILL the PyInstaller
  bootloader, which forks the real Python process as a *grandchild* of the
  app and cannot forward that signal — so the engine used to survive the
  app, keep holding `127.0.0.1:8756`, and answer the next launch's
  readiness poll from a stale build. The app therefore starts the sidecar
  with `--shutdown-on-stdin-eof` and holds the write end of its stdin pipe;
  the OS closes that pipe when the app process dies for any reason,
  including a crash, and the engine stops itself
  (`sigma_engine.main._exit_when_stdin_closes`,
  `engine/tests/test_sidecar_lifecycle.py`).
- The engine test job (pytest + the golden-scenario replay against a live
  ephemeral engine) gates both installer jobs. Before paying for an
  installer build, run the **real built app** locally — see
  [`docs/local-app-testing.md`](local-app-testing.md), which drives
  `desktop/src-tauri/target/release/desktop` under Xvfb and proves the
  webview actually reaches the engine cross-origin.

## The advisor (`engine/sigma_engine/advisor/`)

Layer 2 lives server-side in the engine (the desktop only renders it), so
its guarantees are enforced where the artifacts and computed results live.

- **Context assembly** (`context.py`): every call carries the current
  artifact in full, its computed results extracted as plain facts, and its
  prescore findings; most modes add short code-generated summaries of the
  project's other artifacts (tollgate/remedy narrow to their own phase).
  The model's job is judgment on top of the deterministic checklist.
- **Untrusted delimiters**: all user-entered text is wrapped in one fixed
  delimiter (`wrap_untrusted()` → `<artifact_content … trust="untrusted">`),
  tag literals inside it are defanged, and the system prompt instructs the
  model to treat delimited content as quoted material, never instructions.
  The advisor red-team tests (`engine/tests/test_advisor_red_team.py`)
  exercise this.
- **Budget** (`context.py`): a hard input budget of 30k tokens and 4096 out
  (PLAN §5.1's ceiling, enforced in code, not hoped for). Trimming is tiered
  by priority and *never silent* — anything dropped is recorded in the
  response's `budget_report.dropped`.
- **Structured outputs** (`structured.py`): review/tollgate/validate modes
  demand schema-conforming JSON, with one retry and then an explicit
  `unstructured_fallback` — a malformed model reply degrades, it never 500s.
- **Five modes** (`modes.py`): review my artifact (graded against the same
  rubric items the prescore checks), help me think, explain this result,
  tollgate review, and the remedy advisor. The model pins default to
  `claude-sonnet-5` (`client.py`, env-overridable).
- **The validator** (`validator.py`) is the sixth anti-hallucination layer:
  a second, cheap-tier call (default `claude-haiku-4-5-20251001`) that reads
  a draft's free-text claims against the artifact's own computed facts and
  the project's dataset summaries, and flags what it cannot trace. Its
  response carries a permanent disclaimer naming it a heuristic reviewer.
- **Settings** (`settings_store.py`): key stored in `settings.json` beside
  the projects root, plain text (stated in the UI's privacy statement, which
  is a single shared constant — `desktop/src/advisor/privacyStatement.ts` —
  so the two surfaces that show it can never diverge). Unconfigured, every
  advisor route returns a clean typed "not configured" response.

## The eval stack (`evals/`)

Three different proofs for three different failure modes:

- **Golden-scenario replay** (`evals/harness/`, output in `evals/goldens/`):
  a scripted driver runs three complete projects — the Coffee Bar demo
  re-posted from its shipped JSONs, plus two held-out scenarios built from
  spec files — against a live engine, in DMAIC order, and diffs every
  normalized response against frozen goldens (267 steps across the three).
  Runs in CI on every push; freezing is a deliberate local act with a
  stated-reason commit convention. A coverage check asserts in code that the
  three scenarios' declared scopes collectively equal the matrix's 25 Tier-A
  tools, and `golden-id-map.json` reconciles every golden id the matrix
  cites to a unit test or harness step (40 of 41 covered; the one uncovered
  id is scatter's documented visual-only scope debt). The s2-library
  scenario carries PLAN §9's required named-exit trap: its measurement check
  must fail with EXIT-02, and the harness aborts if the engine ever accepts
  it.
- **Advisor evals** (`evals/advisor-evals/`): six schema-legal
  known-defective fixtures with per-fixture records of what the
  deterministic layer already catches versus what only model judgment can.
  The grading harness is proven offline (`--mock` against canned pass/fail
  responses; the fixture pipeline is separately integration-tested with a
  mocked Anthropic transport). No live run has been executed yet — the runs
  directory says so instead of pretending.
- **Simulated persona runs** (`evals/persona-runs/`): both held-out
  scenarios driven end-to-end by scripted untrained personas against the
  live engine — always labeled simulated, never presented as human results —
  with a consolidated usability/validity failure log that fed real M6 fixes
  (e.g. the baseline screen's attribute-data routing notice).

## The six anti-hallucination layers, mapped to code

The April scoping's six layers are the product's differentiator; here is
where each one actually lives:

| # | Layer | Implemented by |
|---|---|---|
| 1 | Schema-constrained artifacts — invalid work cannot save | `engine/sigma_engine/artifacts/*.py` (Pydantic models, one per tool); `routes/artifacts.py` returns 422 with field-level detail |
| 2 | Numbers from code, never the model — with provenance | `stats/*` computes; `provenance.py`'s frozen `Computed[T]` + `ProvenanceRecord` stamp every result; the artifact recompute pattern discards client-supplied computed fields; computed stats enter prompts as extracted facts (`advisor/context.py`) |
| 3 | Rule-based tool selection, visible, with named exits | `stats/hypothesis_selector.py` (test routing), `artifacts/control_chart.py` (chart family + freeze rules), `artifacts/picker.py` (intake); trees rendered in-app (`desktop/src/tools/hypothesis/DecisionTree.tsx`); exits EXIT-01…15 fire at the matrix §4a frozen trigger values as 422 refusals or verdict payloads, never computed-anyway answers |
| 4 | Grounded fields only | `artifacts/fishbone.py` (a cause cannot be `verified` without evidence — schema-enforced), prescore checks like the charter's solution-language flags (`prescore/charter.py`) and the control plan's named-owner/placeholder-owner checks (`prescore/control_plan.py`) |
| 5 | Phase gates in a state machine, not prompting | `gates.py`: soft gates with logged, missing-set-matched overrides; hard gates `intake_picker_not_exit01` and `measure_capability_language_requires_msa_pass`; unit-tested in `engine/tests/test_gates.py` and replayed in the goldens |
| 6 | Validator pass — a heuristic second reader, labeled as such | `advisor/validator.py` (`run_validator`), cheap-tier model, permanent disclaimer; its honest scope (catches some errors, guarantees live in layers 1–5) is stated in code and in every response |

Two cross-cutting facts make the table more than a checklist. First, layers
1–5 are deterministic and run with no API key — they are tested by the 1552
unit tests and the 267-step golden replay, so the honesty machinery is
regression-locked in CI. Second, the advisor consumes the layers rather
than bypassing them: the prescore runs before any model call, computed
values arrive as facts, and the model is never the source of a number that
reaches an artifact.
