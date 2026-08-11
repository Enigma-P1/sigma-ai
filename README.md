# Sigma AI — Green Belt in a Box

A downloadable Lean Six Sigma tool suite that a smart, motivated person with
zero LSS training can use to run a real improvement project — documenting the
process, the failures, the data, and the fixes — at the quality level expected
of a certified Green Belt. Plus an AI Black Belt advisor to consult at every
step, and a portable prompt pack for people who would rather use their own
chatbot.

Two honesty clauses, stated up front because the rest of this README depends
on them:

- The suite teaches and enforces Green Belt **method**. It does not confer
  certification and never claims to. Its outputs are working documents — not
  certification evidence, and not validation for regulated processes.
- When a project runs past what the suite can honestly compute or verify — a
  measurement system that fails, a case the statistics genuinely can't
  handle — the suite says so by name and routes to a human expert instead of
  faking an answer. "This needs an experienced human" is a first-class
  output, not a failure state.

Coverage is declared, not asserted: the locked
[traceability matrix](docs/traceability-matrix.md) maps every ASQ CSSGB 2022 /
IASSC Green Belt body-of-knowledge item to the tool that covers it, an
explain-only entry, or a named exit — and the gaps are named there, never
papered over.

## The two layers

**Layer 1 — the tool suite.** A local desktop app: a Python statistics engine
(FastAPI + SciPy) behind a React interface, shipped as a double-click
installer with the engine packaged inside (no Python install on your
machine). Layer 1 is **fully functional with no AI and no internet** — every
form, chart, decision tree, instruction panel, and a complete worked example
work offline, and your data never leaves your machine.

**Layer 2 — the AI Black Belt advisor.** An optional expert layer, powered by
the Claude API with your own key: review my artifact, help me think, explain
this result, run my tollgate review, and — the flagship — what do I do about
this proven cause? The advisor explains and critiques; it never computes.
Numbers come from the engine, always. No key? The
[prompt pack](prompts/README.md) is the same method as copy-paste prompts for
any chatbot, with its weaker guarantees stated plainly.

## What's in the box

- **25 Tier-A tools spanning the full DMAIC arc** — built to the frozen
  [Tier-A definition of done](docs/tier-a-done-means.md): five-part helper
  frame, rubric-wired acceptance checklist, NIST-anchored math with frozen
  golden outputs, visible decision trees on every routed tool, provenance on
  every computed result. By phase:
  - *Intake:* Project Picker (with a PDCA quick path for small problems)
  - *Define:* COPQ Calculator, Project Charter, SIPOC, VoC → CTQ Tree
  - *Measure:* Process Map + Waste Walk, interactive Spaghetti Diagram, Check
    Sheet/Tally, Guided Time Study, Yield Calculator (FPY/RTY + DPMO), Data
    Collection Plan (+ sample-size guidance), Measurement Check (narrow MSA),
    Baseline (stability then capability), Pareto/Histogram/Run charts
  - *Analyze:* Fishbone (6M) + 5 Whys, FMEA, guided Hypothesis Testing
  - *Improve:* Solution Selection Matrix, Pilot Plan, Before/After Proof +
    Remaining-Gap Check
  - *Control:* Control Charts (I-MR, p), Control Plan + OCAP + scheduled
    check-ins, scored 5S Audit, Standard Work/SOP
  - *Wrap:* A3 Final Report + tollgate checklists
  - Plus three Tier-B guided templates (stakeholder analysis + comms plan,
    log sheets, kaizen tracker) — real forms, no statistical claims, labeled
    as such.
- **Two complete worked demo projects** threading every tool:
  [the Coffee Bar](demo/coffee-bar/README.md) (continuous data — I-MR,
  capability, Welch t) and [the Print Shop](demo/print-shop/README.md)
  (attribute data — p-chart, kappa, two-proportion z). Each ships one
  deliberately flawed artifact with its correction, because seeing the
  mistake is half the teaching.
- **The portable prompt pack** ([prompts/](prompts/README.md)) — 31
  copy-paste expert prompts (one per tool, one per tollgate) for any chatbot.
- **The eval stack** ([evals/](evals/README.md)) — golden scenarios, advisor
  evals, and simulated persona runs. Numbers below.

## The honesty architecture

The differentiator is not the tool count — it is that the suite cannot
flatter you. Six anti-hallucination layers, all shipped and testable:

1. **Schema-constrained artifacts** — every artifact is a Pydantic model;
   invalid work does not save.
2. **Numbers come from code, never a model** — SciPy computes; every computed
   result is stored as an immutable provenance object (input-data hash,
   method id, engine version, assumptions checked, warnings). The schema
   forbids an LLM creating or mutating any quantitative field.
3. **Rule-based routing** — decision trees pick tests and charts and are
   printed on screen; a case the tree can't handle gets a **named exit**
   (EXIT-01…EXIT-15, trigger values frozen in the matrix before any demo data
   existed), never a computed-anyway answer.
4. **Grounded fields** — claims must cite user input or computed results;
   fishbone causes can't be marked verified without evidence, control plans
   without named owners are flagged as theater.
5. **Phase gates** — hard math guards in the state machine (no capability
   claim without stability plus a passed measurement check), soft sequence
   gates with logged overrides.
6. **Validator pass** — a second, cheap-model call that flags free-text
   claims it can't trace to data. Stated for what it is: a heuristic
   reviewer; the guarantees live in layers 1–5, which are deterministic.

A deterministic **pre-score** (the rule-checkable subset of the grading
rubric) runs in code on every save — the advisor grades on top of the
checklist, never instead of it.

## Quickstart

**Installers (Windows + Mac).** Download the Windows `.msi`/`.exe` (NSIS) or
the Mac `.dmg` from the repo's **[Releases](../../releases)** page — one clean
download page, no login-gated artifact hunting. Tagging a version (`vX.Y.Z`)
builds the installers and publishes them there
([release workflow](.github/workflows/release.yml); the same installers are
also built on every push to `main` via the [build workflow](.github/workflows/build.yml)).
Step-by-step guides, including the unsigned-app warnings you will see and how
to get past them: [Windows install guide](docs/install-windows.md) ·
[Mac install guide](docs/install-mac.md).

**Installed it — now what?** Two ways in, depending on whether you want to
watch or to type:

- **Watch first, type nothing.** [`examples/`](examples/) has a finished
  Coffee Bar project — all 25 tools filled in, both datasets embedded, charts
  and stats computed. Unzip it into your projects folder and open it by ID.
  Fastest way to see what the output actually looks like.
- **Type it yourself.** [Test drive](docs/test-drive.md) is a 20-minute
  script with real copy-paste answers that produce that same project, so the
  numbers tie out across tools and the honesty checks behave as they would on
  a live project.

**Run from source (developers).** Requires Python 3.11+ and Node 22+. Use two
terminals — the engine keeps running in the first while you work in the second.

macOS / Linux:

```bash
# Terminal 1 — engine (FastAPI + SciPy) on port 8000
cd engine
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m uvicorn sigma_engine.main:app --port 8000

# Terminal 2 — desktop UI (Vite dev server on port 1420, proxies to the engine)
cd desktop
npm install
npm run dev
```

Windows (PowerShell) — the venv lives in `.venv\Scripts\`, not `.venv/bin/`, and
PowerShell has no `&&`, so run these one line at a time:

```powershell
# Terminal 1 — engine
cd engine
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python -m uvicorn sigma_engine.main:app --port 8000

# Terminal 2 — desktop UI
cd desktop
npm install
npm run dev
```

Open http://localhost:1420. For the full Tauri desktop shell instead of a
browser tab, build the sidecar first, then run Tauri dev (needs a Rust
toolchain): `scripts/build-sidecar.sh` from the repo root, then
`cd desktop && npm run tauri dev`.

**Run the proof yourself** (macOS / Linux paths; on Windows use
`.venv\Scripts\python`):

```bash
scripts/local-gate.sh        # everything CI's Linux job checks, one command
scripts/local-gate.sh --fast # same, minus the browser probes (~2 min faster)
```

That runs the 1552 NIST-anchored engine tests, the 267-step golden replay,
the frontend typecheck and production bundle, and five browser probes
against the packaged-app origin condition — starting and tearing down the
engines it needs. The only things it cannot prove are the Windows and macOS
installer builds, which need those platforms. Run the pieces directly if
you prefer:

```bash
cd engine && .venv/bin/python -m pytest          # 1552 tests, NIST-anchored
.venv/bin/python ../evals/harness/run_goldens.py # 267-step golden replay
                                                 # (needs the engine running on port 8000)
```

## The proof — evals and reviews

Deterministic gates first, judgment second, and every claim labeled:

- **1552 engine tests** run in CI on every push: every computed statistic is
  unit-tested against NIST/SEMATECH reference values or published worked
  examples (control-chart constants, capability indices, test statistics,
  kappa, sigma tables). These tests are the final authority on the math.
- **A 267-step golden-scenario replay** runs in CI against a live engine:
  three complete projects (the Coffee Bar demo plus two held-out scenarios —
  a help desk and a library, one continuous, one attribute) driven through
  every Tier-A tool in their declared scope, every response diffed against
  frozen goldens. The three scenarios collectively exercise all 25 tools —
  asserted in code on every run. One scenario deliberately requires a named
  exit: its measurement check must fail with EXIT-02, and the harness aborts
  if the engine ever stops refusing it. Honesty paths are regression-tested,
  not just the happy path.
- **Advisor evals** ([evals/advisor-evals/](evals/advisor-evals/README.md)):
  six frozen defective-artifact fixtures — crude defects and subtle
  Green-Belt-fail patterns — with a grading harness whose mechanics are
  proven offline against canned responses. Honest status: **no live
  model run has been executed yet** (no API key has been configured in the
  build environment); the first `--live` run is a pre-release checklist item.
- **Simulated persona runs** ([evals/persona-runs/](evals/persona-runs/README.md)):
  both held-out scenarios were driven end-to-end by scripted untrained
  personas — fictional characters constrained to a smart high-school
  graduate's knowledge, played by an AI agent against the live engine (217
  real engine calls, refusals and recoveries logged, plus a consolidated
  failure log). These are **always labeled simulated and are never presented
  as human results**.
- **Review provenance:** the grading rubric and traceability matrix were
  locked after a three-round **externally AI-reviewed** Belt-panel review
  (GPT + Grok, charged as certified Belts). No human certified Belt has
  reviewed this project, and no claim here implies otherwise.

## The advisor and your data

Layer 1 sends nothing anywhere — no server, no account, no telemetry;
projects are plain JSON folders on your disk. Layer 2 talks to the Claude API
with a key you supply, and the settings screen states exactly what it sends.
That statement, verbatim (from
[`desktop/src/advisor/privacyStatement.ts`](desktop/src/advisor/privacyStatement.ts)):

> The advisor (Layer 2) sends nothing until you actually use it. When you ask
> it something, the current artifact goes in full, along with its computed
> results and pre-score findings; most modes also send short, code-generated
> summaries of your project's other saved artifacts, so the advisor can
> reference them or ask to see one in full. "Check my claims" additionally
> sends a summary of every dataset you've imported into this project,
> including up to 3 sample values per column. Don't put customer names or
> other sensitive identifiers in artifact text or imported datasets. Your API
> key is stored in plain text in settings.json on this machine -- it is not
> encrypted.

## Documentation

- [Demo walkthrough](docs/demo-walkthrough.md) — a 12-stop guided tour of the
  Coffee Bar project, with screenshots.
- [Test drive](docs/test-drive.md) — 20 minutes, copy-paste answers, every
  tool exercised. [`examples/`](examples/) is the same project pre-filled if
  you'd rather not type.
- [Field notes](docs/field-notes.md) — rough edges found using shipped
  builds: what was observed, why, and what a fix costs.
- [Architecture](docs/architecture.md) — the two-layer design, the honesty
  machinery, and where each piece lives in the code.
- [Install guides](docs/install-windows.md) — [Windows](docs/install-windows.md),
  [Mac](docs/install-mac.md).
- [Traceability matrix](docs/traceability-matrix.md) — BoK topic → tool →
  source → rubric → golden; the authoritative coverage record.
- [Green Belt rubric](docs/green-belt-rubric.md) — the grading authority
  (externally AI-reviewed; see its header for the full review record).
- [Tier-A "done means"](docs/tier-a-done-means.md) — the frozen definition of
  done that kept polish from thinning.
- [Build plan](PLAN.md) — the reviewed v1 plan this repo was built against.
- Market context: [free/OSS landscape](docs/research/free-and-oss-landscape-2026-08.md)
  and [modern ops-tool UX research](docs/research/modern-ops-tools-and-ux-2026-08.md).

## Status and roadmap — honestly

**v1 is feature-complete against the locked matrix.** All 25 Tier-A tools,
both demos, the advisor (five modes + validator), the prompt pack, and the
eval stack are built; CI is green on tests, golden replay, and both platform
installers.

Named limits of v1, none of them hidden in-app:

- **Correlation/regression is honest but incomplete:** scatter plots are
  visual-only (no fitted line, no r), and quantified correlation/regression
  is EXIT-15 — the tool names the deferral and routes you rather than
  computing something it can't defend.
- **v1.1 (next release, not v-someday), per the matrix:** X-bar/R, np, c, u
  chart families; guided correlation + simple linear regression (the scatter
  computation EXIT-15 defers); Kruskal-Wallis and guided pairwise-comparison
  routes in the hypothesis selector; 8D report export; takt time + line
  balancing; guided OEE; the multi-factor Experiment Planner (DOE) if real
  use proves the need.
- **The advisor has not been fired live:** everything deterministic about it
  is tested (context assembly, budget, structured-output parsing, injection
  delimiters — with a mocked API), but the live advisor-eval run and a
  real-key end-to-end check are open items pending an API key.
- **The clean-machine install test** (stock Windows/Mac, no Python, 15
  minutes to the Project Picker) is defined in [PLAN.md](PLAN.md) §7 and not
  yet run on physical hardware; CI smoke-tests the built sidecar on real
  Windows and macOS runners in its place.

**License:** Apache 2.0, per the build plan's ruling (PLAN §7). Full text in
[LICENSE](LICENSE).
