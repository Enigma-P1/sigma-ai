# Sigma AI — Green Belt in a Box: v1 Build Plan

> Status: APPROVED FOR BUILD — external review converged at round 3 of 4:
> GPT SOUND, Grok SOUND ("good to build"). Review history in §12.
> Supersedes the tool-scope portion of the 2026-04-22 scoping in the vault
> (`Personal-AI/context/projects/sigma-ai.md`); carries its architecture forward.

## 1. Mission and the acceptance bar

Build a downloadable Lean Six Sigma tool suite that a smart, motivated person
with **zero LSS training** can pick up and use to run a real improvement
project — documenting the process, the failures, the data, and the fixes — at
the quality level expected of a certified Green Belt. Plus an AI Black Belt
advisor they can consult at every step.

**The acceptance bar (the "high-schooler test"):** hand the suite to a smart
high school student with a real problem (a slow coffee line, a defect-prone
print job) and a spreadsheet of data. Following only what the suite tells
them, they produce a project — charter, process map, baseline, root-cause
analysis, tested improvement, control plan, final report — that a certified
Black Belt grading against a Green Belt rubric would pass. This is not a
metaphor; it is the shipping gate (see §9).

**The acceptance contract, stated once so scope and claim can't drift
apart:** the quality bar — Green Belt-grade work on everything the suite
covers — is fixed and never softens. The *coverage list* is what flexes,
and only visibly: milestone 0's traceability matrix (§6) names exactly
which BoK items v1 covers, which are explain-only, and which exit to a
human expert; the rubric grades against that declared scope; and if the
matrix shows a genuinely-required Green Belt capability missing from the
tool list, the tool list grows — the matrix corrects the plan, not the
other way around. Marketing language follows the matrix ("covers the
Green Belt core; the gaps are named"), never "full coverage" by assertion.

Two honesty clauses on that claim: the suite teaches and enforces Green Belt
**method**; it does not confer certification and will never claim to (the
README and app say so plainly). And when a project runs past what the suite
can honestly compute or verify — an unstable process that won't stabilize, a
measurement system that fails, an analysis needing methods the tool doesn't
carry — the suite's job is to say so by name and route to a human expert,
not to fake an answer. "This needs an experienced human" is a first-class
output, not a failure state. (Exits are gated by method limits, never by
belt level — vault correction 2026-08-04-001: the belt difference is
experience interpreting output, not access to tools.) The README also
carries one policy sentence: outputs are working documents, not
certification evidence and not validation for regulated processes.

What separates a Black Belt is judgment built from experience. The suite
cannot ship experience, so it ships the next best thing: an AI advisor
grounded in established LSS method that answers "is this right?", "what am I
missing?", and "what would you do?" at every tool and every phase gate.

## 2. Who it's for

Primary users: people who need to run improvement projects and have no belt —
SMB ops practitioners, team leads, students, anyone with a process and a
problem. The high schooler is the **usability bar**, not the market: if the
suite works for them, it works for the untrained ops manager who is the real
audience (unchanged from the April scoping — Minitab's own mid-market reviews
say licenses go unused because "too complex"; that is the gap).

Secondary audience: evaluators. This is a public portfolio piece — engineers
will read the code, execs will read the README and watch the demo. Portfolio
deliverables (README, demo video, plain-English architecture writeup) remain
first-class, unchanged from April.

## 3. Product shape — two layers

**Layer 1 — the tool suite.** A local app (Python/Streamlit) containing every
tool a Green Belt uses: guided forms, decision trees, deterministic statistics,
charts, and field-by-field instructions. **Layer 1 is fully functional with no
AI and no internet.** A student with no API key still gets the complete suite:
every template, every chart, every decision tree, every instruction, and a
complete worked example. This matters because the deterministic core is what
makes the output trustworthy — the AI is a coach on top, never the engine.

**Layer 2 — the AI Black Belt advisor.** An expert layer the user can consult
from anywhere in the app: review my artifact, help me brainstorm, explain this
result, run my tollgate review. Powered by the Claude API with the
anti-hallucination architecture from the April scoping (numbers come from
code, never the model). For users who can't or won't set up an API key, the
suite ships a **portable prompt pack** — expert-grade prompts they paste into
any chatbot along with their exported artifact (§5.2).

The two layers are separable on purpose: Layer 1 is the product's floor and
its credibility; Layer 2 is what closes the gap between "filled in the
template" and "understood what the template was telling them."

## 4. Layer 1: the tool suite (works with zero AI)

### 4.1 Tool set — full Green Belt coverage, by DMAIC phase

Scope anchor: the ASQ Certified Six Sigma Green Belt Body of Knowledge and the
IASSC Lean Six Sigma Green Belt syllabus. The brief is "all the things a Green
Belt would be asked to do." Coverage is proven, not asserted: **milestone 0
produces a traceability matrix** — BoK topic → tool → formula/source → rubric
item → golden test — and the tool list below is corrected against it before
build (§6, §8).

The suite is tiered, because the shipping gate is a *completed project*, not
a toolbox screenshot. **Tier A is the vertical spine** — built to full polish
(instructions, rubric, decision trees, golden outputs, advisor prompts) and
sufficient to pass §9 end-to-end. **Tier B tools are guided templates** —
real forms with real instruction panels, but no statistical claims — clearly
labeled as such in-app.

**Tier A — the spine (guided DMAIC flow, tollgate at each phase exit):**

| Phase | Tool | How it works |
|---|---|---|
| Intake | Project Picker | Before DMAIC starts: is this a good first project? Scoped narrow enough, measurable outcome, data obtainable, a process owner who cares, plausible business impact. Kills the "pet project / boil the ocean" failure the research ranks above statistics. |
| Define | Project Charter | Guided form: problem statement builder (what/where/when/magnitude — no causes, no solutions), SMART goal, scope in/out, team + process owner, timeline, business impact in dollars-or-hours terms. Rule-based checks (regex/keyword heuristics + checklist confirmations) flag solution-shaped statements; the Layer-2 grader is the deeper check. |
| Define | SIPOC | Guided form + auto-rendered diagram |
| Define | VoC → CTQ Tree | Structured capture of customer statements → needs → measurable CTQs; tree diagram; explicit "is this what the *customer* critically needs, or what the process finds easy to measure?" check. (LLM theme extraction is a Layer-2 assist; manual entry always works.) |
| Measure | Process Map (swimlane) + Waste Walk | Step-by-step map builder; each step tagged value-add / non-value-add / enabling; 8 wastes checklist per step |
| Measure | Data Collection Plan | Operational definition builder ("two people would measure it the same way" check), data type identification, stratification factors (shift, machine, operator, day — captured as columns so later tools can use them), and **sample-size guidance as a first-class output** (n-for-a-stable-baseline rules of thumb + a calculator with plain-English framing, bias/convenience-sample warnings) |
| Measure | Measurement Check (MSA) | Real, narrow: test/retest repeatability study for continuous data (%GRR-style verdict from a simplified Gage study) and a two-rater attribute agreement check for pass/fail judgments. Three outcomes: acceptable / marginal / **stop — fix your measurement first**. A failed check blocks capability-claim language downstream (results render as "unreliable — measurement system failed" until fixed). Full multi-operator Gage R&R stays v2; what ships is small but honest. |
| Measure | Baseline: Stability then Capability | Order enforced because the math requires it: spec limits + operational definition first, then an I-MR chart to assess stability, then capability. Stable → Cp/Cpk (within) and Pp/Ppk (overall), with the distinction explained; not stable → the tool says "you don't have a baseline yet — here's what the instability pattern suggests doing," and Pp/Ppk only, labeled as performance-not-capability. Normality assessed advisorily (visual + test + n-aware guidance, never a silent auto-gate); non-normal → percentile method with plain-English caveat. DPMO/sigma level with the 1.5σ shift convention named and toggleable. |
| Measure | Pareto / Histogram / Run Chart | matplotlib; auto-annotated (80/20 line, distribution shape notes, standard runs rules for trends/shifts) |
| Analyze | Fishbone (6M) + 5 Whys | Structured capture with 6M categories; every candidate cause carries an evidence field — "what data supports this?" — unproven causes visibly flagged; verified-cause status feeds Improve |
| Analyze | FMEA (process) | Failure modes worksheet with industry-standard 1–10 severity/occurrence/detection anchor scales (generic wording, no licensed text), risk table sorted severity-first then RPN, with the known RPN limitation stated (equal RPNs are not equal risks; high severity never ignorable), action tracking. The "documenting failures" centerpiece. |
| Analyze | Hypothesis Testing (guided) | Rule-based selector, deliberately narrow: 2-sample t (Welch by default — no equal-variance assumption to trip on) / paired t / one-way ANOVA / chi-square or 2-proportion, with Mann-Whitney and Wilcoxon signed-rank as the stated nonparametric fallbacks. Routes on the question and data structure first (what are you comparing? paired or independent? continuous or count?), assumptions second. Output always includes effect size + confidence interval + practical-vs-statistical significance in plain English, never a bare p-value. **The selector's unsupported-case list is enumerated, not vibes:** the M0 matrix lists every route as supported / detected-and-exits (small n below stated floors, sparse cells, repeated measures, autocorrelated data, >1 factor, rates with exposure, multiple simultaneous comparisons) — an inexperienced user can receive a result or a named exit, never a formally-computed-but-wrong answer for a case the tree knows it can't handle. ANOVA-significant gets a canned next step ("these groups differ overall; comparing specific pairs fairly needs a correction — guided pairwise comparisons ship in v1.1; here's the honest interim read"). |
| Improve | Solution Selection Matrix | Impact/effort grid + weighted-criteria matrix; solutions must link to verified causes or get flagged |
| Improve | Pilot Plan | A small study designer, not a form, teaching **basic Green Belt pilot discipline** (this is GB material, not deferred DOE): what changes and what it's compared against (before-period or parallel comparison), who/what is included and how selected, run order randomized where feasible, success threshold and analysis plan declared **before** data collection, and a "what would prove this DIDN'T work" line. A confounder checklist in plain English (did anything else change? staffing, season, demand, measurement?) carries into the proof. Multi-factor questions route to the Experiment Planner; designs beyond it (response surface, hard-to-change factors, power analysis) = named specialist exits. |
| Improve | Before/After Proof | Stats engine re-run on pilot data: side-by-side stability + capability, the appropriate Tier-A test, effect size + CI, and the pilot's pre-declared threshold checked. The confounder checklist answers print on the result — "improvement shown, but you reported a staffing change; this proof is weakened" is a possible verdict. |
| Improve | Experiment Planner (designed experiments) | **Added by Shawn's ruling 2026-08-04; scope re-based per his correction (vault 2026-08-04-001):** limits are set by what the runs can honestly prove — never by belt level. Certification syllabi park experiment design in Black Belt training, but that's a curriculum split, not a capability line; beltless practitioners run multi-factor tests constantly. The tool: guided 2-level experiments up to 4 factors — pick factors and levels in plain English, the tool builds the full-factorial run table, randomizes run order, and computes main effects **and two-factor interactions** deterministically ("speed only hurts when temperature is high" is exactly the real-world case). Honesty rails scale with the design, up front: a run-budget check before you start ("with 8 runs and no repeats, you can detect big effects only — here's what 16 buys you"), replication encouraged and accounted for, and significance for unreplicated designs judged by the standard published method (Lenth), with weak conclusions labeled weak. Named specialist exits only for genuinely specialist territory: >4 factors, fine-tuning optimal settings (response surface), hard-to-change factors. The advisor helps plan and interpret; the tool computes. |
| Control | Control Charts | v1 families: **I-MR** (continuous) and **p** (attribute) — the two a Green Belt actually reaches for — selector driven by data type; constants from published tables; Western Electric rules with a conservative default subset (rules 1–4) to limit false alarms; limits frozen from baseline and recalculated only on deliberate, logged decision |
| Control | Control Plan + Response Plan (OCAP) | What's monitored, how often, by whom (a named owner is a required field — a control plan with no owner is flagged as theater), and the exact out-of-control action path |
| Control | Standard Work / SOP | The improved method written down so it survives the author |
| Wrap | A3 Final Report + Tollgate Checklists | A3 as a **guided narrative builder**, not field concatenation: the user writes the story panel-by-panel with each panel pre-seeded from its source artifact and editable; Layer 2 can draft narrative from artifacts, user approves. Includes realized-benefits panel. Tollgate checklists per phase. |

**Tier B — guided templates (forms + instruction, no stats):** Stakeholder
Analysis + Communication Plan; data-collection log sheets; kaizen/quick-win
tracker.

**v1.1 (next release, not v-someday):** X-bar/R, np, c, u chart families;
correlation + simple linear regression as a guided tool; second demo project
polish beyond what §4.4 requires.

Deferred to v2 (specialist-tier — gated by method complexity, not belt
level): full multi-operator Gage R&R, DOE beyond the 2-level/4-factor
planner (fractional designs, response surface), Multi-Vari, VSM
future-state, EWMA/CUSUM, Monte Carlo, QFD, Taguchi, TRIZ. The coach can *explain* any of them; the suite only
*generates* what it can generate correctly.

### 4.2 The Tool Picker — "what do I use now?"

The single biggest confusion for an untrained user is not any one tool — it's
knowing which tool the moment calls for. Three mechanisms:

1. **The DMAIC spine.** The app is a guided flow, not a toolbox menu. You are
   always *in* a phase; the phase shows which tools are done, available, or
   not-yet-recommended. Gates are two kinds, deliberately different:
   **math guards are hard** (no capability without spec limits; no
   capability *claim* without a stability check and a passed measurement
   check — because the number would be wrong, not just premature) while
   **sequence gates are soft**: a gate warning lists what's missing, and the
   user can proceed with a required, logged override reason. Real projects
   iterate — re-charter after Measure, re-baseline after a failed
   measurement check — and the flow supports going back without corrupting
   the record (artifacts version on edit; §4.5). Hard locks everywhere
   would teach a false, linear cartoon of DMAIC.
2. **Decision trees, visible.** Every routing decision (which hypothesis test,
   which control chart, continuous vs attribute path) is a printed flowchart
   the user can see, not hidden logic. The suite makes the choice by rule and
   shows the path it took. These flowcharts are themselves standard LSS
   content — the same trees in any Green Belt course.
3. **"I'm stuck" button.** Answer 2–3 plain-English questions ("do you have
   data yet?", "are you trying to find causes or prove one?") → the picker
   routes you and explains why. Works offline via the decision tree; Layer 2
   makes it conversational.

### 4.3 The instruction layer — what to input where

Every tool screen has the same five-part frame, always visible:

- **What this is** — two sentences, plain English, no jargon unbunked.
- **When to use it / when not to** — including the classic misuse.
- **Exactly what goes in each field** — per-field helper text with a good and
  a bad example ("Problem statement: 'Line 2 scrap rate averaged 6.2% in
  Q2, costing ~$40k' ✓ — 'Operators need retraining' ✗ that's a solution").
- **What good looks like** — the acceptance checklist for this artifact,
  drawn from the same rubric the AI grader uses (§5.1).
- **Common mistakes** — the 3–5 errors every instructor sees.

This is the "green belt course compressed into helper text" — the user learns
the method *by doing the project*, not by reading a manual first.

### 4.4 The worked example — one project threaded through everything

The suite ships with **two** complete, realistic demo projects, because the
continuous and attribute data paths genuinely differ and one example would
teach students to copy the demo's shape instead of their own:

- **The Coffee Bar** — order-to-handoff time (continuous data, I-MR,
  capability, t-test) — the primary threaded example.
- **The Print Shop** — defective orders (attribute data, p-chart,
  proportions test, Pareto by defect type) — filled in for every tool whose
  attribute path differs.

Every tool's screen can toggle "show me the example": the same tool, filled
in, at the same point in the flow. The point is continuity — the student
watches the charter's problem statement become the CTQ, the CTQ become the
metric, the metric become the baseline, the baseline become the hypothesis
test, the fix become the control chart. That thread *is* the method. Each
demo also includes one deliberately flawed artifact with its correction
("here's the solution-shaped problem statement we fixed, and why") — seeing
the mistake is half the teaching.

### 4.5 Charts and outputs

- All charts matplotlib/plotly, embedded in the app and in exports.
- Every artifact exports to PDF individually and rolls up into the A3 final
  report — the deliverables a sponsor actually sees. PDF engine:
  **ReportLab, not WeasyPrint** — pure Python, no system dependencies
  (WeasyPrint's Pango/GTK requirement on Windows would sink the §7
  clean-machine install bar on its own).
- Every artifact saves as structured JSON (the Pydantic schema is the source
  of truth), which is what the AI advisor and the prompt pack consume.
- **Computed results are provenance objects**: every statistic is stored
  immutable with input-data hash, method identifier, software version,
  assumptions checked, and warnings attached. Exports carry them, so an
  independent reviewer can reproduce any number. The LLM cannot create or
  mutate quantitative fields — schema-enforced, not policy-hoped.
- Artifacts version on edit; the whole project saves as one folder —
  portable, versionable, emailable.

## 5. Layer 2: the AI Black Belt advisor

### 5.1 In-app advisor modes

**The advisor's center of gravity is advice on the problem and its
remedies — not tool operation** (Shawn, 2026-08-04). Tool use lives in the
product: forms, decision trees, and computation are Layer 1's job, and the
suite should never need AI to be usable. What the advisor uniquely adds is
the thing templates can't: Black Belt-grade judgment on *your* situation.
The reason its answers are sharp instead of generic-chatbot noise is
structural — the app assembles the framework-shaped context (charter,
verified causes with their evidence, computed baselines, constraints) and
asks the expert question *for* the user, so they never have to figure out
what to ask or sort through pages of filler.

The advisor is context-aware: every call carries the current phase, the
current artifact's JSON, and the computed stats as **facts in the prompt** —
the model explains and critiques; it never calculates. Five modes:

1. **Review my artifact.** Grades the artifact against the same published
   rubric shown in the tool's "what good looks like" panel. Output is
   structured: pass/needs-work per criterion, with the specific fix. This is
   the experience-substitute — the red pen a Black Belt mentor would apply.
2. **Help me think.** Socratic brainstorm for the divergent tools (fishbone
   causes, 5-why chains, VoC themes, solution ideas). The model proposes, the
   user prunes; nothing enters the artifact without the user accepting it,
   and accepted causes still carry the "what data supports this?" field.
3. **Explain this.** Any computed result (Cpk 0.7, p = 0.03, an
   out-of-control signal) explained in plain English: what it means, what it
   doesn't mean, what a Green Belt would do next.
4. **Tollgate review.** Before a phase gate, the AI plays the Champion: asks
   the standard tollgate questions for that phase against the actual
   artifacts, and gives a go / go-with-actions / no-go recommendation with
   reasons. The user can always override — it's an advisor, not a lock.
5. **What do I do about this? (the remedy advisor — the flagship mode.)**
   Once causes are verified, the app sends the full evidence picture —
   problem, process, verified causes and their supporting data, constraints
   the user has stated (budget, headcount, what can't change) — and the
   advisor returns ranked candidate remedies with plain-English reasoning:
   why each fits the verified cause, what it costs, what could go wrong,
   what to pilot first and how to know it worked. Output feeds directly
   into the Solution Selection Matrix and Pilot Plan. This is where the
   "Black Belt in your pocket" promise actually lives — the experience gap
   between belts is mostly *knowing what to do about a proven cause*, and
   this mode is aimed at exactly that gap.

Mechanics that keep the advisor honest and affordable:

- **Deterministic pre-score first.** Before any tollgate or review call, the
  rule-based rubric checks run in code and their results go into the prompt.
  The model's job is judgment on top of the checklist, not rediscovering it —
  which also keeps context small.
- **Context budget.** Tollgate reviews get artifact summaries plus the
  pre-score, not the full project dump; any artifact the model wants in full
  it asks for by ID. Provisional ceiling: ~30k tokens in / ~4k out per
  tollgate review (roughly a few cents per call at current pricing);
  measured and tuned in M5, but the architecture is designed to that budget
  from the start.
- **Injection defense.** User-entered fields and imported file content are
  data, never instructions: delimited and tagged in prompts, and the advisor's
  system prompt treats artifact content as untrusted quoted material.
- **Privacy, stated plainly.** Layer 1 sends nothing anywhere. Layer 2 sends
  the current artifact + computed stats to the Claude API — the settings
  screen says exactly that, and the docs advise not putting customer names or
  sensitive identifiers in artifact text (with a field-level "keep this
  local" flag on free-text notes as a v1.1 candidate).

### 5.2 The portable prompt pack (works without the app)

A `prompts/` directory of copy-paste expert prompts — one per tool plus one
per tollgate — for users running Layer 2 through any chatbot (Claude, ChatGPT,
Gemini, whatever they have). Each prompt embeds: the expert role frame, the
tool's rubric, instructions to demand the user's actual artifact/data before
answering, and explicit guardrails ("do not invent numbers; if the data isn't
provided, ask for it"). The app's export screen produces a paste-ready block:
prompt + artifact JSON + computed stats in one copy action.

This gives a student with zero setup a usable version of Part 2 — and it's
honest about what it is: same method, weaker guarantees than in-app (no
schema enforcement, no grounding checks). The pack's README and every
prompt's footer say so plainly, including the one rule that prevents
split-brain projects: **numbers that come back from a chatbot are not
authoritative — the app's computed results are the record.**

### 5.3 Anti-hallucination architecture (carried forward)

The six layers from the April scoping, unchanged — they are the differentiator
and the research (documented LLM-as-statistician failure modes) still stands:

1. Schema-constrained output — every artifact is a Pydantic model; the LLM
   returns conforming JSON or the call retries.
2. Numbers come from code, never the LLM — scipy/statsmodels compute;
   results pass into prompts as facts.
3. Rule-based tool selection — decision trees pick tests/charts; the LLM
   explains the choice, never makes it.
4. Grounded fields only — claims must cite user input or computed results;
   unfilled fields prompt the user, never get invented.
5. Phase gates — hard guards in the state machine, not hopeful prompting.
6. Validator pass — a second cheap-model call reads each artifact against
   source data and flags claims it can't trace to inputs; user sees flags
   before saving. Stated for what it is: a **heuristic reviewer** that
   catches some errors, not a guarantee — the guarantees live in layers 1–5
   and the provenance objects (§4.5), which are deterministic.

## 6. Fidelity to established Lean Six Sigma

"100% based on established rules and process" is a buildable requirement, not
a vibe — and it's proven by traceability, not citation-dropping:

- **The traceability matrix is milestone 0** and a repo artifact: every ASQ
  CSSGB / IASSC Green Belt knowledge item mapped to → the tool that covers it
  (or an explicit "explain-only" / "out of v1 scope" entry) → the
  formula/method source → the rubric item that grades it → the golden test
  that locks it. Tool scope in §4.1 gets corrected against this matrix before
  any Streamlit page is written. Coverage claims come from the matrix.
- **Formulas** (capability indices, control limits, test statistics) follow
  the NIST/SEMATECH e-Handbook of Statistical Methods; control chart
  constants (A2, D3, D4, d2…) from the standard published tables; runs rules
  per Western Electric.
- **FMEA scales** use industry-standard 1–10 anchor structure with original
  generic wording — no AIAG or ASQ licensed text reproduced, no implied
  endorsement (this is a public repo; trademark and licensing hygiene from
  day one).
- **Sigma level / DPMO** conversion stated with the 1.5σ shift convention
  named explicitly (and toggleable), because hiding conventions is how tools
  teach wrong ideas.
- Every tool's help panel cites its source.
- **The Green Belt rubric has an independent author-checker split:** built
  from the BoK, then reviewed by a certified Belt who didn't write it
  (Shawn sources; §9). A self-graded rubric would make the whole eval
  circular.
- **Review gate for content:** teaching text and rubrics get a fidelity
  review pass against the BoK references at the end of the Measure milestone
  and again before v1 ships — not only at the end (§8).

## 7. Deployment and distribution

**License: Apache 2.0** (Shawn's ruling 2026-08-04) — permissive like MIT
with explicit patent language; friendly to every evaluator audience and
deliberately unlike nearest-neighbor DMAIC.io's AGPL. This is a free
showpiece by design: the README says so, with an honest comparison table
against the free alternatives (stats toolboxes, template packs, chatbot
coaches — see `docs/research/free-and-oss-landscape-2026-08.md`).

Unchanged from April: **local install, not hosted.** Python + Streamlit,
`pip install sigma-ai` then `sigma-ai` (a console entry point that launches
Streamlit — one command, not two). No server, no accounts, no hosting costs;
the user's data never leaves their machine, which for real ops data is a
feature, not a compromise.

Both reviewers flagged install friction as a plan-level risk — a student who
can't get past setup never reaches DMAIC, and the §9 test gets quietly
selection-biased toward people who can. So packaging is a **gated milestone-1
requirement, not a polish item**:

- **The clean-machine test, at M1, with a precise pass/fail:** a stock
  Windows machine and a stock Mac, **no Python preinstalled**, fresh user
  account, normal internet access, a written install guide, a non-developer
  tester. Pass = within 15 minutes the tester reaches the Project Picker
  with demo data open **and** a stats smoke check passes on that same
  machine (the engine runs one NIST-verified calculation — so "UI installs
  but the math engine doesn't" can't produce a false green). Fail → the
  packaging approach changes **before** the remaining tools are built —
  fallback order: bundled-Python installer (Briefcase/PyInstaller-style) →
  stlite (Streamlit fully in-browser). Either fallback is adopted only
  after a feasibility spike proves the scipy/statsmodels/PDF paths actually
  run on it — no betting the stats engine on an untested runtime.
- ReportLab over WeasyPrint (§4.5) removes the worst system-dependency risk
  up front; remaining deps (Streamlit, scipy, matplotlib, pydantic) all ship
  as ordinary wheels.
- Windows `run-sigma.bat` / Mac `run-sigma.command` double-click launchers in
  the release download; install guide with screenshots assuming nothing.
- The prompt pack and the PDF template pack are downloadable **on their own**
  from the repo — someone who never installs anything still gets a usable
  paper/chatbot version of the suite. The app is the full product; the packs
  are the zero-install on-ramp.

API key for Layer 2: first-run settings screen with a plain-English "get a
key" walkthrough; the app is fully usable while the field is empty.

## 8. Build sequence

Seven milestones, each independently shippable and committed as it lands.
Testing and fidelity checks ride along per milestone — they are not a final
phase (both reviewers called back-loaded proof the plan's structural risk):

0. **Traceability matrix + rubric.** The BoK→tool→source→rubric→golden
   matrix (§6) against **pinned editions** of the ASQ CSSGB BoK and IASSC
   syllabus (editions named in the matrix header), the Green Belt grading
   rubric drafted, tool list corrected against the matrix, the "Tier A done
   means" checklist frozen (helper frame + rubric items + ≥1 golden +
   decision tree if routed + export/provenance — so "full polish" can't
   quietly thin under schedule pressure), and the **independent Belt
   reviewer identified now**, not at M6 — the rubric locks only after
   their pass. No app code before this exists.
1. **Skeleton + Define + the packaging gate.** App shell, project save/load
   (JSON folder + provenance objects), soft/hard gate state machine, Project
   Picker, Charter, SIPOC, VoC/CTQ, Coffee Bar demo data, PDF export for one
   artifact — and the **clean-machine install test (§7)**; packaging pivots
   now if it fails.
2. **Measure.** Stats engine (stability, capability, normality, DPMO/sigma),
   data import (CSV/Excel), Process Map + Waste Walk, Data Collection Plan
   (+ sample-size guidance), Measurement Check, Pareto/Histogram/Run charts.
   Deterministic tests for every formula against NIST reference values.
   **Milestone exit: fidelity review of Measure content + one live
   untrained-user test of Define+Measure** — Measure is where untrained
   users actually die (operational definitions, data types, capability
   misuse), so it gets a real user before Analyze is built.
3. **Analyze.** Fishbone/5 Whys, FMEA, hypothesis selector + tests (with
   effect sizes/CIs), printed decision-tree flowcharts.
4. **Improve + Control.** Solution matrix, pilot designer, Simple
   Experiment Planner (DOE-lite), before/after proof, I-MR + p charts +
   constants + Western Electric rules, Control Plan/OCAP, Standard Work,
   A3 narrative builder, tollgate checklists, Print Shop demo project
   completed across the attribute path.
5. **Layer 2.** Advisor (5 modes, remedy advisor as the flagship +
   pre-score wiring + context budget), validator pass, prompt pack,
   paste-ready export.
6. **Proof + polish.** Full high-schooler golden-scenario evals (§9),
   independent Belt review of rubric + outputs, final fidelity pass, install
   guides, demo video, README and architecture writeup.

Milestones 0–4 produce a complete, AI-free Green Belt suite — worth shipping
even if Layer 2 slipped. The ordering means the floor is never at risk.

## 9. Success criteria and evals

Deterministic gates first, judgment gates second:

- **Stats correctness:** every computed statistic tested against
  NIST/SEMATECH reference datasets and published worked examples (control
  chart constants, capability indices, test statistics). These are unit
  tests; they run in CI; they are the final authority on the math. As a
  cheap extra cross-check, spot-verify outputs against DMAIC.io and the
  Qualica Excel templates (independent open implementations of the same
  formulas).
- **Golden scenarios:** three complete projects with datasets (the Coffee
  Bar demo plus two held-out scenarios — one attribute-data/defects, one
  continuous-data/cycle-time). A scripted walkthrough drives each through all
  every Tier-A tool (the inventory is the M0 matrix's tool list — one
  authoritative count, no drift between milestones, rubric, and goldens);
  outputs are frozen as goldens and diffed on every change.
- **The high-schooler test, literally:** untrained testers (target 3–5;
  minimum two — a teenager and a non-ops adult; Shawn sources) each run a
  held-out scenario using only the suite, with task-level failure logging
  (where they stalled, what they misread, what they asked). Scoring uses
  the shipped Green Belt rubric, applied by a certified Belt who did not
  author the content. Pass bar: every phase scores "acceptable Green Belt
  work" or better, with **usability failures and validity failures logged
  separately** — a confusing screen and a wrong analysis are different bugs.
  Scenario datasets are pre-collected and realistic (the test measures the
  suite, not the tester's ability to gather data); a stall inside the
  suite's guidance is a v1 bug, a stall outside its stated scope goes to the
  failure log for a scope ruling. Two additions so the test measures the
  actual §1 claim, not just scenario-following: **at least one tester runs a
  real problem of their own with their own data** (graded on method quality
  given their data, since the data can't be controlled), and **one held-out
  scenario deliberately requires a named exit** (a measurement check that
  should fail, or a question needing a Black Belt) — recognizing the exit
  is part of the pass bar, so honesty paths get graded, not just the happy
  path.
- **Advisor evals:** a frozen set of artifact-review and tollgate calls with
  known-defective artifacts — crude defects (solution-shaped problem
  statement, fishbone with zero evidence) *and* subtle Green-Belt-fail
  patterns (capability claimed on an unstable process, before/after "proof"
  with a reported confound, control plan with no owner) — the advisor must
  catch them. Run per release like the vault's goldens, with model/version
  pinned per run so results are comparable.

## 10. Changes from the 2026-04-22 locked scope

Named explicitly so nothing changes silently:

1. **Tool count: 9 → a tiered ~19.** The April scope chose "tight over
   broad" so the anti-hallucination architecture would headline. The new
   brief — "all the things a green belt would be asked to do" — makes Green
   Belt BoK coverage the requirement, and 9 tools don't cover it (no FMEA,
   no control charts, no process map meant "documenting process and
   failures" was literally impossible). The tiering (§4.1) keeps the April
   instinct honest: the spine gets full depth, templates are labeled
   templates, and coverage is proven by the milestone-0 matrix rather than
   claimed.
2. **Audience bar restated:** "smart high schooler" replaces "SMB non-belt"
   as the usability bar (the market is unchanged). This hardens the
   instruction layer (§4.3) and the worked example (§4.4) from nice-to-have
   to load-bearing.
3. **Part 2 formalized:** the AI coach was already in scope; the four
   advisor modes, tollgate reviewer, and the portable prompt pack are new
   commitments.
4. Everything else — local Streamlit deployment, stack, open source,
   portfolio-first, six anti-hallucination layers — carries forward intact.

## 11. Open decisions for Shawn

**Ruled 2026-08-04:** Simple Experiment Planner (DOE-lite) is IN v1 (Shawn
chose the tool over advice-only — resolving the GPT disagreement); license
is **Apache 2.0**; the advisor's flagship mode is remedy advice (§5.1) —
tool use belongs to the product, AI is for judgment on the problem.

Still open, not blocking. Two worth a ruling when convenient:

1. **Name/positioning of the free packs.** The PDF template pack + prompt
   pack as a standalone free download is a distribution decision (great
   on-ramp, but it's also the part easiest to copy). Default: ship them
   openly — the app and the architecture are the moat, and this is a
   portfolio piece.
2. **Packaging fallback order** if the M1 clean-machine test fails (§7):
   bundled installer first, stlite second is the default — flip it if he
   has a preference.

## 12. External review log

**Round 1 (2026-08-04) — GPT `gpt-5.6-luna`: FLAWED. Grok `grok-4.5`:
SOUND-WITH-FIXES.** Full transcripts:
`Personal-AI/tools/second-opinion/runs/2026-08-04-v1-build-plan-*.md`.

Accepted and folded in: stability-before-capability with Cp/Cpk vs Pp/Ppk
enforced (§4.1); real narrow MSA with a blocking "fix your measurement"
outcome (§4.1); soft sequence gates with logged overrides, hard gates only
where math breaks (§4.2); tiered tool set with a polished vertical spine
(§4.1); traceability matrix + rubric as milestone 0 (§6, §8); untrained-user
test and fidelity review pulled into the Measure milestone (§8); sample-size
guidance first-class (§4.1); narrowed hypothesis battery with effect
sizes/CIs and named "needs a Black Belt" exits (§4.1); pilot as study
designer with confounder checklist carried into the proof (§4.1); control
charts narrowed to I-MR + p with conservative rules and frozen limits
(§4.1); A3 as guided narrative builder (§4.1); second (attribute) demo
project + flawed-example teaching (§4.4); provenance objects and
LLM-can't-touch-numbers enforcement (§4.5); validator restated as heuristic
(§5.3); advisor pre-score, context budget, injection defense, privacy
statement (§5.1); prompt-pack authority banner (§5.2); RPN limitations
stated, licensed-text hygiene (§4.1, §6); no-certification-claim wording
(§1); project intake tool (§4.1); packaging as gated M1 test, ReportLab
swap (§7); rubric author/checker split and separated usability-vs-validity
failure logging (§9).

Pushed back, with reasons: GPT's fuller experimental-design and advanced
stats demands (randomization/blocking, count-data models, multiple
comparisons, equivalence testing) are Black-Belt scope; the suite's answer
is honest named exits and limitation flags, not more statistics an
untrained user can't wield (§1, §4.1). Grok's "make zero-install the v1
default" is handled as the M1 packaging gate rather than a pre-commitment —
same risk, addressed earlier, without betting the stack on stlite untested.

**Round 2 (2026-08-04) — GPT: FLAWED (narrowed to five points). Grok:
SOUND ("good to build"; both §12 pushbacks upheld).** Transcripts:
`runs/2026-08-04-round-2-*.md`.

Accepted and folded in: the acceptance contract — fixed quality bar,
matrix-governed coverage list, matrix corrects the plan (§1); **basic pilot
discipline reclassified as Green Belt scope** and built into the Pilot
designer (run order, selection, comparison definition, falsification line) —
GPT was right that wholesale DOE deferral swept in things a GB does do,
and Grok concurred (§4.1); enumerated unsupported-case detection for the
test selector with Welch default and Wilcoxon fallback (§4.1); ANOVA
next-step guidance (§4.1); tool-count ambiguity removed — the M0 matrix
inventory is the one authoritative list (§9); bring-your-own-problem
tester + a should-exit scenario in the eval (§9); precise install
pass/fail (no Python preinstalled, fresh account, 15 min, stats smoke
check) + fallback feasibility spikes (§7); pinned BoK editions, Belt
reviewer identified at M0, "Tier A done means" checklist frozen at M0
(§8); provisional advisor token budget (§5.1); non-certification /
non-regulated-use policy sentence (§1).

Remaining GPT items not adopted as written: demands to resolve
matrix-level coverage questions (exact BoK edition contents, whether the
rubric requires X-bar/R or regression) inside this plan document — that
resolution is exactly what milestone 0 exists to produce, and the
acceptance contract now states which way conflicts resolve. Data-import
validation detail (missing values, units, duplicates) is implementation
detail scheduled under M2's Data Collection Plan and import work.

**Round 3 (2026-08-04) — GPT: SOUND ("prior plan-level gaps are
addressed; remaining concerns are execution questions explicitly assigned
to milestones and gates"). Grok: SOUND ("good to build; remaining
concerns are milestone-scoped implementation work or resource deps, not
plan holes").** Both reviewers in agreement — the loop closes at round 3
of the 4 allowed. Transcripts: `runs/2026-08-04-round-3-*.md` (note: the
saved round-3 file holds the Grok retry; GPT's round-3 verdict is quoted
here from the live run — its first attempt saved then was overwritten by
the Grok network-retry using the same filename).
