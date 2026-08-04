# Sigma AI — Green Belt in a Box: v1 Build Plan

> Status: DRAFT — under external review (GPT + Grok loop, per Shawn's 2026-08-04 brief).
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
Belt would be asked to do," so the April "9 tight tools" scope expands to the
tools those bodies of knowledge actually expect a Green Belt to execute —
19 tools, organized as a guided DMAIC flow with a tollgate at each phase exit.

| Phase | Tool | How it works |
|---|---|---|
| Define | Project Charter | Guided form: problem statement builder (what/where/when/magnitude — no causes, no solutions), goal (SMART), scope in/out, team, timeline. Validation rejects solution-shaped problem statements. |
| Define | SIPOC | Guided form + auto-rendered diagram |
| Define | VoC → CTQ Tree | Structured capture of customer statements → needs → measurable CTQs; tree diagram. (LLM theme extraction is a Layer-2 assist; manual entry always works.) |
| Define | Stakeholder Analysis + Communication Plan | Power/interest grid + who-hears-what-when table |
| Measure | Process Map (swimlane) + Waste Walk | Step-by-step map builder; each step tagged value-add / non-value-add / enabling; the 8 wastes checklist applied per step |
| Measure | Data Collection Plan | Operational definition builder ("two people would measure it the same way" check), sampling plan guidance, data type identification (continuous vs attribute — drives everything downstream) |
| Measure | Measurement System Check (MSA-lite) | Green-Belt-level gage sense check: repeatability/reproducibility walkthrough with pass/caution/fail guidance; full Gage R&R deferred to v2 |
| Measure | Baseline Capability | Cp/Cpk/Pp/Ppk, DPMO, sigma level — scipy, deterministic; normality checked (Shapiro-Wilk) and non-normal paths handled honestly (percentile method + plain-English caveat, not silent wrong math) |
| Measure | Pareto / Histogram / Run Chart | matplotlib; auto-annotated (80/20 line, distribution shape notes, run-chart trend/shift rules per standard runs tests) |
| Analyze | Fishbone (6M) + 5 Whys | Structured capture with the 6M categories; each candidate cause carries an evidence field — "what data supports this?" — and unproven causes are visibly flagged |
| Analyze | FMEA (process FMEA) | Full RPN worksheet with standard 1–10 severity/occurrence/detection anchor scales (AIAG-style wording), sorted risk table, action tracking. This is the "documenting failures" centerpiece. |
| Analyze | Hypothesis Testing (guided) | Rule-based test selector — data type, group count, normality, variance equality → t-test / paired t / ANOVA / chi-square / Mann-Whitney / correlation+simple regression. The user answers plain-English questions; the decision tree picks the test and shows its reasoning. p-values explained in plain English with practical-vs-statistical-significance guidance. |
| Improve | Solution Selection Matrix | Impact/effort grid + weighted criteria (Pugh-style) matrix; ties solutions back to verified root causes — a solution with no linked verified cause gets flagged |
| Improve | Pilot Plan | Small-scale test design: what/where/how long/success threshold declared **before** the pilot runs |
| Improve | Before/After Proof | Same stats engine re-run on pilot data; side-by-side capability + the appropriate hypothesis test on before-vs-after; verdict in plain English |
| Control | Control Charts | I-MR, X-bar/R, p, np, c, u — selector driven by data type and subgroup structure; standard control chart constants from published tables; Western Electric zone rules for out-of-control signals |
| Control | Control Plan + Response Plan (OCAP) | What's monitored, how often, by whom, and the exact out-of-control action path |
| Control | Standard Work / SOP | The improved method written down so it survives the author |
| Wrap | A3 Final Report + Tollgate Checklists | One-page A3 rolled up from every prior artifact + per-phase tollgate checklist (the questions a Champion asks before letting you pass) |

Deferred to v2 (unchanged reasoning — these are Black-Belt-tier or
specialist): full Gage R&R, DOE, Multi-Vari, VSM future-state, EWMA/CUSUM,
Monte Carlo, QFD, Taguchi, TRIZ. The coach can *explain* any of them; the
suite only *generates* what it can generate correctly.

### 4.2 The Tool Picker — "what do I use now?"

The single biggest confusion for an untrained user is not any one tool — it's
knowing which tool the moment calls for. Three mechanisms:

1. **The DMAIC spine.** The app is a guided flow, not a toolbox menu. You are
   always *in* a phase, the phase shows which tools are done/available/locked,
   and phase gates enforce order (no control chart without baseline data, no
   charter sign-off without a problem statement — hard guards in the state
   machine, per the April architecture).
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

The suite ships with one complete, realistic demo project — "The Coffee Bar"
(order-to-handoff time at a busy campus coffee bar) — with real-shaped
datasets. Every tool's screen can toggle "show me the example": the same tool,
filled in for the demo project, at the same point in the flow. The user sees a
finished Green Belt project end-to-end before and while doing their own.

One project, not many: the point is continuity — the student watches the
charter's problem statement become the CTQ, the CTQ become the metric, the
metric become the baseline, the baseline become the hypothesis test, the fix
become the control chart. That thread *is* the method.

### 4.5 Charts and outputs

- All charts matplotlib/plotly, embedded in the app and in exports.
- Every artifact exports to PDF (WeasyPrint) individually and rolls up into
  the A3 final report — the deliverables a sponsor actually sees.
- Every artifact also saves as structured JSON (the Pydantic schema is the
  source of truth), which is what the AI advisor and the prompt pack consume.
- The whole project saves as one folder — portable, versionable, emailable.

## 5. Layer 2: the AI Black Belt advisor

### 5.1 In-app advisor modes

The advisor is context-aware: every call carries the current phase, the
current artifact's JSON, and the computed stats as **facts in the prompt** —
the model explains and critiques; it never calculates. Four modes:

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

### 5.2 The portable prompt pack (works without the app)

A `prompts/` directory of copy-paste expert prompts — one per tool plus one
per tollgate — for users running Layer 2 through any chatbot (Claude, ChatGPT,
Gemini, whatever they have). Each prompt embeds: the expert role frame, the
tool's rubric, instructions to demand the user's actual artifact/data before
answering, and explicit guardrails ("do not invent numbers; if the data isn't
provided, ask for it"). The app's export screen produces a paste-ready block:
prompt + artifact JSON + computed stats in one copy action.

This makes Part 2 real for a student with zero setup — and it's honest about
what it is: same method, weaker guarantees than in-app (no schema
enforcement), which the pack's README says plainly.

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
6. Validator pass — a second cheap-model call flags any artifact claim not
   traceable to inputs; user sees flags before saving.

## 6. Fidelity to established Lean Six Sigma

"100% based on established rules and process" is a buildable requirement, not
a vibe:

- **Method scope** anchors to the ASQ CSSGB Body of Knowledge and IASSC
  Green Belt syllabus — nothing invented, nothing renamed.
- **Formulas** (capability indices, control limits, test statistics) follow
  the NIST/SEMATECH e-Handbook of Statistical Methods; control chart
  constants (A2, D3, D4, d2…) from the standard published tables; runs rules
  per Western Electric.
- **FMEA scales** use standard 1–10 anchor wording (AIAG-style).
- **Sigma level / DPMO** conversion stated with the 1.5σ shift convention
  named explicitly (and toggleable), because hiding conventions is how tools
  teach wrong ideas.
- Every tool's help panel cites its source ("this decision tree follows the
  standard test-selection logic taught in ASQ GB prep").
- **Review gate for content:** the teaching text and rubrics get a dedicated
  fidelity review pass against the BoK references before v1 ships (part of
  §9, and a natural place for the GPT/Grok outside check).

## 7. Deployment and distribution

Unchanged from April: **local install, not hosted.** Python + Streamlit,
`pip install sigma-ai` then `sigma-ai` (a console entry point that launches
Streamlit — one command, not two). No server, no accounts, no hosting costs;
the user's data never leaves their machine, which for real ops data is a
feature, not a compromise.

Friction reducers for the "hand it to a student" bar:

- A plain-English install page: one path for Windows, one for Mac, each ~5
  steps with screenshots, assuming nothing (including "install Python" via
  the official installer).
- Windows `run-sigma.bat` / Mac `run-sigma.command` double-click launchers in
  the release download.
- The prompt pack and the PDF template pack are downloadable **on their own**
  from the repo — someone who never installs Python still gets a usable
  paper/chatbot version of the suite. The app is the full product; the packs
  are the zero-install on-ramp.
- Investigated for v1.1, not gating v1: stlite (Streamlit compiled to run
  fully in-browser) — would make "downloadable" mean "open an HTML file."
  Promising but adds packaging risk; decision deferred until v1 works.

API key for Layer 2: first-run settings screen with a plain-English "get a
key" walkthrough; the app is fully usable while the field is empty.

## 8. Build sequence

Six milestones, each independently shippable and committed as it lands:

1. **Skeleton + Define.** App shell, project save/load (JSON folder), phase
   state machine, Charter + SIPOC + VoC/CTQ + Stakeholder tools, the Coffee
   Bar demo project data, PDF export for one artifact.
2. **Measure.** Stats engine (capability, normality, DPMO/sigma), data import
   (CSV/Excel), Process Map + Waste Walk, Data Collection Plan, MSA-lite,
   Pareto/Histogram/Run charts. Deterministic tests for every formula against
   NIST reference values.
3. **Analyze.** Fishbone/5 Whys, FMEA, hypothesis test selector + tests, the
   printed decision-tree flowcharts.
4. **Improve + Control.** Solution matrix, pilot plan, before/after proof,
   control charts + constants tables + Western Electric rules, Control
   Plan/OCAP, Standard Work, A3 roll-up, tollgate checklists.
5. **Layer 2.** Advisor (4 modes), validator pass, prompt pack, paste-ready
   export.
6. **Polish + proof.** Install guides, launchers, demo video, the
   high-schooler golden-scenario evals (§9), fidelity review pass, README and
   architecture writeup.

Milestones 1–4 produce a complete, AI-free Green Belt suite — worth shipping
even if Layer 2 slipped. It won't slip, but the ordering means the floor is
never at risk.

## 9. Success criteria and evals

Deterministic gates first, judgment gates second:

- **Stats correctness:** every computed statistic tested against
  NIST/SEMATECH reference datasets and published worked examples (control
  chart constants, capability indices, test statistics). These are unit
  tests; they run in CI; they are the final authority on the math.
- **Golden scenarios:** three complete projects with datasets (the Coffee
  Bar demo plus two held-out scenarios — one attribute-data/defects, one
  continuous-data/cycle-time). A scripted walkthrough drives each through all
  19 tools; the outputs are frozen as goldens and diffed on every change.
- **The high-schooler test, literally:** at least two real untrained testers
  (Shawn can source; a teenager and a non-ops adult) each run a held-out
  scenario using only the suite. A Green Belt rubric (shipped with the
  product, same one the AI grader uses) scores their output. Pass bar:
  every phase scores "acceptable Green Belt work" or better. Where they
  stall or misread instructions is a v1 bug, not user error.
- **Advisor evals:** a frozen set of artifact-review and tollgate calls with
  known-defective artifacts (a solution-shaped problem statement, a fishbone
  with zero evidence, a capability run on non-normal data) — the advisor
  must catch the planted defects. Run per release like the vault's goldens.

## 10. Changes from the 2026-04-22 locked scope

Named explicitly so nothing changes silently:

1. **Tool count: 9 → 19.** The April scope chose "tight over broad" so the
   anti-hallucination architecture would headline. The new brief — "all the
   things a green belt would be asked to do" — makes Green Belt BoK coverage
   the requirement, and 9 tools don't cover it (no FMEA, no control charts,
   no process map meant "documenting process and failures" was literally
   impossible). The architecture still headlines; it now governs more tools.
   The added tools are mostly templates and rule-driven charts — the cheap
   kind — not new stats surface.
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

None blocking the build. Two worth a ruling when convenient:

1. **Name/positioning of the free packs.** The PDF template pack + prompt
   pack as a standalone free download is a distribution decision (great
   on-ramp, but it's also the part easiest to copy). Default: ship them
   openly — the app and the architecture are the moat, and this is a
   portfolio piece.
2. **v1.1 packaging bet.** stlite in-browser vs. a proper installer vs.
   leave as pip. Decide after v1 real-user testing shows where install
   friction actually bites.
