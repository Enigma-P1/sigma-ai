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

**Layer 1 — the tool suite.** A local desktop app — Python statistics engine
(FastAPI + scipy/statsmodels, unchanged in role) with a real web interface
(React + Konva canvas + Plotly.js), shipped as a single double-click
installer (Tauri with a packaged Python sidecar; no Python install on the
user's machine). Stack ruled by Shawn 2026-08-04 after the modern-UX
research (`docs/research/modern-ops-tools-and-ux-2026-08.md`): Streamlit's
interactivity ceiling would have capped exactly the tools the "slick, not
spreadsheet hell" bar cares about — the spaghetti tracer, drag-and-drop
process maps, the fishbone canvas. It contains every tool a Green Belt uses:
guided forms, decision trees, deterministic statistics, charts, and
field-by-field instructions. **Layer 1 is fully functional with no
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
| Intake | Project Picker | Before DMAIC starts: is this a good first project? Scoped narrow enough, measurable outcome, data obtainable, a process owner who cares, plausible business impact. Kills the "pet project / boil the ocean" failure the research ranks above statistics. Also routes small problems to the **PDCA quick path** — a lightweight plan-do-check-act track (charter-lite, one fix, one check) for wins that don't warrant full DMAIC rigor; practitioners abandon tools that force ceremony on small problems. |
| Define | COPQ / Benefit Calculator | Guided cost-of-poor-quality worksheet — scrap, rework, overtime, expediting, lost business — turning the problem into dollars, the language leadership hears. Feeds the charter's business-impact field; re-run at Wrap for realized benefits on the A3. |
| Define | Project Charter | Guided form: problem statement builder (what/where/when/magnitude — no causes, no solutions), SMART goal, scope in/out, team + process owner, timeline, business impact in dollars-or-hours terms, and a lightweight key-risks-&-mitigations block (risk, likelihood/impact, mitigation, owner — M0 matrix correction A-4; deep risk work stays FMEA's). Rule-based checks (regex/keyword heuristics + checklist confirmations) flag solution-shaped statements; the Layer-2 grader is the deeper check. |
| Define | SIPOC | Guided form + auto-rendered diagram |
| Define | VoC → CTQ Tree | Structured capture of customer statements → needs → measurable CTQs; tree diagram; explicit "is this what the *customer* critically needs, or what the process finds easy to measure?" check. (LLM theme extraction is a Layer-2 assist; manual entry always works.) |
| Measure | Process Map (swimlane) + Waste Walk | Interactive canvas map builder (drag-drop steps, auto-routing connectors, pan/zoom); each step tagged value-add / non-value-add / enabling; 8 wastes checklist per step. Steps carry data (times, defect points, stratification factors) that downstream tools reuse — one project data model, many views. A bottleneck readout names the constraint step — longest effective step time vs the pace demand requires (available time ÷ demand, two fields) — M0 correction A-7; full takt/line-balancing stays v1.1. |
| Measure | Spaghetti Diagram (interactive) | Promoted from paper-template to flagship visual tool: upload a floor-plan image (or a photo of the paper sketch), calibrate scale by drawing one known-length line, trace routes per operator/trip. Live metrics: distance per trip, trip count, path crossings, estimated walk time, distance × frequency = daily travel burden. **Heatmap toggle and before/after layout mode with delta metrics** — nothing in the free space offers either. Animated playback for demos. 2D canvas by design (the top-down plan view IS the recognizable artifact); an optional tilted 2.5D view is a possible later flourish, not v1. |
| Measure | Check Sheet / Tally | The field's second-most-used tool: define categories, tap to count failures as they happen (works on a phone at the line), timestamps and stratification captured automatically, feeds Pareto with zero re-entry. |
| Measure | Guided Time Study / Work Sampling | Phone-as-stopwatch observation: define the work elements, time repeated cycles or sample at intervals, get element times with spread, flag the outliers honestly. Warehouse-native; feeds baseline and the process map's step times. |
| Measure | Yield Calculator (FPY/RTY) | First-pass yield and rolled throughput yield from simple good/rework/scrap counts, alongside DPMO — the honest version of the number Excel habitually flatters. |
| Measure | Data Collection Plan | Operational definition builder ("two people would measure it the same way" check), data type identification, stratification factors (shift, machine, operator, day — captured as columns so later tools can use them), and **sample-size guidance as a first-class output** (n-for-a-stable-baseline rules of thumb + a calculator with plain-English framing, bias/convenience-sample warnings) |
| Measure | Measurement Check (MSA) | Real, narrow, and named honestly (M0 critic corrections): a resolution pre-check first (the gauge must read at least tenths of the span it judges, with ≥5 distinct values — a stopwatch in whole minutes fails a 3-minute process here, before any repeatability math), then a test/retest **repeatability%** verdict for continuous data — called repeatability, not "GRR" and not "%EV" (Belt-panel round 2: EV names a component of a full variance-decomposed study this narrow check is not), because a single-operator study cannot see reproducibility — defined in the matrix §4a, with its denominator named as which it is on the output; and a two-rater attribute agreement check reporting % agreement **plus kappa**, so chance agreement can't flatter a low-defect process. Three outcomes at frozen thresholds (matrix §4a): acceptable / marginal / **stop — fix your measurement first**. A failed check blocks capability-claim language downstream (results render as "unreliable — measurement system failed" until fixed). Full multi-operator Gage R&R stays v2; what ships is small but honest. |
| Measure | Baseline: Stability then Capability | Order enforced because the math requires it: spec limits + operational definition first, then an I-MR chart to assess stability, then capability. Stable → Cp/Cpk (within) and Pp/Ppk (overall), with the distinction explained; not stable → the tool says "you don't have a baseline yet — here's what the instability pattern suggests doing," and Pp/Ppk only, labeled as performance-not-capability. Normality assessed advisorily (visual + test + n-aware guidance, never a silent auto-gate); non-normal → percentile method with plain-English caveat. DPMO/sigma level with the 1.5σ shift convention named and toggleable. |
| Measure | Pareto / Histogram / Run Chart + Scatter / Box | Auto-annotated per the chart-modernization checklist (§4.5): plain-English verdict headline, vital-few bars highlighted to the 80% line, runs-rule signals colored with hover explanations. Scatter and box-and-whisker plots added per M0 matrix correction A-2 (ASQ III.D.4 is Create-level): scatter is visual-only in v1 — no fitted line, no r; EXIT-15 names the v1.1 deferral of quantified correlation/regression — and box plots are explicit in group displays here and in hypothesis-test output. |
| Analyze | Fishbone (6M) + 5 Whys | Structured capture with 6M categories; every candidate cause carries an evidence field — "what data supports this?" — unproven causes visibly flagged; verified-cause status feeds Improve |
| Analyze | FMEA (process) | Failure modes worksheet with industry-standard 1–10 severity/occurrence/detection anchor scales (generic wording, no licensed text), risk table sorted severity-first then RPN, with the known RPN limitation stated (equal RPNs are not equal risks; high severity never ignorable), action tracking. The "documenting failures" centerpiece. |
| Analyze | Hypothesis Testing (guided) | Rule-based selector, deliberately narrow: 2-sample t (Welch by default — no equal-variance assumption to trip on) / paired t / one-way ANOVA / chi-square or 2-proportion, with Mann-Whitney and Wilcoxon signed-rank as the stated nonparametric fallbacks — plus the one-sample-vs-target routes (1-sample t, 1-sample Wilcoxon, 1-proportion; M0 matrix correction A-1: "is my baseline/pilot different from the stated target?" is a routine GB question the tree previously couldn't route). Routes on the question and data structure first (what are you comparing? paired or independent? continuous or count?), assumptions second. Output always includes effect size + confidence interval + practical-vs-statistical significance in plain English, never a bare p-value. **The selector's unsupported-case list is enumerated, not vibes:** the M0 matrix's exit registry lists every route as supported / detected-and-exits (small n below stated floors, sparse cells, repeated measures, autocorrelated data, >1 factor, rates with exposure, multiple simultaneous comparisons, 3+ groups markedly non-normal [EXIT-14, Kruskal-Wallis territory — route ships v1.1, per A-3], continuous-x↔continuous-y questions [EXIT-15 → v1.1 regression]) — an inexperienced user can receive a result or a named exit, never a formally-computed-but-wrong answer for a case the tree knows it can't handle. ANOVA-significant gets a canned next step ("these groups differ overall; comparing specific pairs fairly needs a correction — guided pairwise comparisons ship in v1.1; here's the honest interim read"). The parametric→nonparametric switch is an n-and-shape rule shown to the user, never a silent normality pretest (the same conditional-testing mistake the Welch default avoids on variances); rank routes carry their own effect size + CI (rank-biserial, Hodges–Lehmann) and Mann-Whitney prints its equal-shape caveat (matrix §4a). |
| Improve | Solution Selection Matrix | Impact/effort grid + weighted-criteria matrix; solutions must link to verified causes or get flagged. Output is a **ranked fix list** — the queue the improvement loop works through. |
| Improve | Pilot Plan | A small study designer, not a form, teaching basic pilot discipline: **one change at a time**, what it's compared against (before-period or parallel comparison), who/what is included and how selected, success threshold and analysis plan declared **before** data collection, and a "what would prove this DIDN'T work" line. A confounder checklist in plain English (did anything else change? staffing, season, demand, measurement?) carries into the proof. |
| Improve | Before/After Proof + Remaining-Gap Check | Stats engine re-run on pilot data: side-by-side stability + capability, the appropriate Tier-A test, effect size + CI, and the pilot's pre-declared threshold checked. The confounder checklist answers print on the result — "improvement shown, but you reported a staffing change; this proof is weakened" is a possible verdict. Then the loop closes: the tool shows how much of the original gap this fix recovered and how much remains, and routes back to the next-ranked verified cause — "this fix got you 80% of the way; here's what's left and the next suspect" — until the goal is met or causes run out. |
| Control | Control Charts | v1 families: **I-MR** (continuous) and **p** (attribute) — the two a Green Belt actually reaches for — selector driven by data type; constants from published tables; Western Electric rules with **default = rule 1 + rule 4 only** (corrected at M0 critic review: running all four zone rules roughly quadruples false alarms — in-control ARL ~370 → ~92 — and I-MR charts over-signal on non-normal data; zone rules 2–3 are opt-in with that cost stated in the helper panel); limits frozen from baseline and recalculated only on deliberate, logged decision; reads the T-11 sampling-scheme field and warns on mixed-stream or too-sparse schemes before limits are trusted (matrix VI.A.2) |
| Control | Control Plan + Response Plan (OCAP) + Scheduled Check-ins | What's monitored, how often, by whom (a named owner is a required field — a control plan with no owner is flagged as theater), the exact out-of-control action path, and a training-&-handoff block (who gets trained on the new method, by whom, by when, verified how — M0 matrix correction A-5, ASQ VI.B.3: a fix nobody is trained on dies with the project). Plus the fix for the field's most-abandoned phase (Control = 6% of real tool usage): the app **schedules recurring check-ins** — "week 3: is the fix holding? enter this week's numbers" — with pass/fail against the control limits. Spreadsheets' real failure mode is that nobody chases the next step; this chases it. |
| Control | 5S Audit (scored) | Promoted from explain-only: a scored 5S checklist with photos and a trend line — the single most-digitized lean activity at SMB level, and a natural recurring companion to the control plan. |
| Control | Standard Work / SOP | The improved method written down so it survives the author |
| Wrap | A3 Final Report + Tollgate Checklists | A3 as a **guided narrative builder**, not field concatenation: the user writes the story panel-by-panel with each panel pre-seeded from its source artifact and editable; Layer 2 can draft narrative from artifacts, user approves. Includes realized-benefits panel. Tollgate checklists per phase. |

**The Improve phase is a one-change-at-a-time loop by design** (Shawn's
method, ruled 2026-08-04, superseding the same-day ruling that added a
multi-factor experiment tool to v1): rank the verified causes by likely
impact, fix the top one, prove it, check the remaining gap, take the next.
Cheap — every fix proves itself on real work, no test schedules.
Self-correcting — the gap tells you if your ranking was wrong. And every
step yields a clean before/after story. Changing several things at once —
throwing everything at the wall — is what the flow is built to prevent,
because you never learn what actually stuck. When someone genuinely needs a
combined test, the advisor helps think it through as advice; the
multi-factor Experiment Planner (full spec preserved under v1.1) ships only
if real use proves the need.

**Tier B — guided templates (forms + instruction, no stats):** Stakeholder
Analysis + Communication Plan; data-collection log sheets; kaizen/quick-win
tracker. (Spaghetti Diagram graduated to Tier A as the interactive flagship,
2026-08-04.)

**M0 matrix corrections (2026-08-07).** The traceability matrix
(`docs/traceability-matrix.md`) is now the authoritative tool inventory and
coverage record — **Tier-A count: 25** (§10's "~19" predated the seven
field-research additions). Per the §1 acceptance contract the matrix
corrected this section, all field/route-level, no new tools: **A-1**
one-sample-vs-target test routes (golden G-hyp-07); **A-2** scatter + box
plots in the v1 chart set; **A-3** EXIT-14 registered now, Kruskal-Wallis
route at v1.1; **A-4** charter key-risks block; **A-5** control-plan
training-&-handoff block; **A-7** (critic review, same day) bottleneck
readout on the process map. Plus one standing flag, **A-6**: v1 is honest
but incomplete on correlation/regression (scatter + named EXIT-15
deferral) — acceptable only while v1.1 stays "next release"; §9 golden
scenarios must not require regression to pass, and if v1.1 slips
materially the README's coverage language must say so. The matrix's §4a
**frozen exit trigger values** (added at the critic review) are part of
the coverage contract: exits fire at named numbers, frozen before any
demo data existed.

**v1.1 (next release, not v-someday):** X-bar/R, np, c, u chart families;
correlation + simple linear regression as a guided tool (with scatter
plots); Kruskal-Wallis and guided pairwise-comparison routes in the
hypothesis selector (M0 matrix correction A-3 / EXIT-13, EXIT-14);
8D corrective-action report as an export skin over existing project
data (the de facto framework in manufacturing/supplier contexts — same
fishbone/5-whys/pilot/control data, different paper); takt time + simple
line balancing; guided OEE calculator (manual Excel OEE runs 8–12 points
optimistic — an honest guided version has real value); the multi-factor
Experiment Planner if real use shows the need — spec already settled:
guided 2-level experiments up to 4 factors, full-factorial run table,
randomized order, main effects + two-factor interactions computed
deterministically, run-budget honesty check up front, Lenth's method for
unreplicated designs, limits gated by what the runs can prove (never belt
level — vault correction 2026-08-04-001); second demo project polish
beyond what §4.4 requires.

Deferred to v2 (specialist-tier — gated by method complexity, not belt
level): full multi-operator Gage R&R, DOE beyond the v1.1 planner spec
(fractional designs, response surface), Multi-Vari, VSM future-state,
EWMA/CUSUM, Monte Carlo, QFD, Taguchi, TRIZ. The coach can *explain* any of them; the suite only
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

- All charts Plotly.js in-app (interactive: hover context, signal
  explanations), rendered to static images for PDF export. **One design
  system across every tool** — one type scale, one muted-plus-accent
  palette, plain-English verdict headline above every chart, signals
  colored and noise muted, σ-zones as soft bands — so twenty tools read as
  one product, not twenty scripts (full checklist:
  `docs/research/modern-ops-tools-and-ux-2026-08.md` §F).
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
  any app screen is written. Coverage claims come from the matrix.
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
  from the BoK, then checked by reviewers who didn't write it. **Owner
  ruling 2026-08-07: no human certified-Belt reviewer will be sourced —
  "we are the creator and the reviewer on this one."** The independent
  check is a non-Claude external-model Belt review (GPT + Grok via the
  vault's second-opinion tool, charged as certified Belts), findings
  folded before the rubric locks. Honesty consequence: every claim about
  the rubric says "externally AI-reviewed" — nothing may state or imply a
  certified human reviewed it.
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

Local-first, not hosted (unchanged in principle from April; stack ruled
2026-08-04 after the modern-UX research): **a single double-click installer
per platform** — Tauri desktop shell + React/Konva/Plotly.js interface +
packaged Python sidecar (FastAPI, scipy/statsmodels) for all statistics. No
Python install on the user's machine, no `pip`, no `localhost` copy-paste.
No server, no accounts, no hosting costs; the user's data never leaves
their machine, which for real ops data is a feature, not a compromise.
This supersedes the April Streamlit decision — Streamlit's rerun-per-click
model and sandboxed components cap the interactive canvas tools (spaghetti
tracer, process map, fishbone) that the "slick" bar exists for.

Both reviewers flagged install friction as a plan-level risk — a student who
can't get past setup never reaches DMAIC, and the §9 test gets quietly
selection-biased toward people who can. So packaging is a **gated milestone-1
requirement, not a polish item**:

- **The packaging spike is the first build task of M1:** prove the
  Tauri + PyInstaller-sidecar pipeline produces working installers for
  Windows and Mac before any tool UI is built on it (known-good open
  templates exist for exactly this pattern).
- **The clean-machine test, at M1, with a precise pass/fail:** a stock
  Windows machine and a stock Mac, **no Python preinstalled**, fresh user
  account, normal internet access, a non-developer tester. Pass = within 15
  minutes the tester downloads, installs, and reaches the Project Picker
  with demo data open **and** a stats smoke check passes on that same
  machine (the engine runs one NIST-verified calculation — so "UI installs
  but the math engine doesn't" can't produce a false green). Fail → the
  approach changes **before** the remaining tools are built — fallback
  order: stlite+Electron (best install story in the Streamlit family,
  lower interactivity ceiling) → Streamlit + pip with launchers (the
  original April path). Either fallback is adopted only after a feasibility
  spike proves the scipy/statsmodels/PDF paths run on it.
- ReportLab over WeasyPrint (§4.5) removes the worst system-dependency risk
  up front; remaining Python deps (FastAPI, scipy, statsmodels, pydantic)
  all ship as ordinary wheels inside the sidecar.
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
   quietly thin under schedule pressure), and the **independent reviewer
   identified now**, not at M6 — the rubric locks only after their pass.
   *(Resolved by owner ruling 2026-08-07: the reviewer chair is the
   external-model Belt panel, §6 — no human Belt will be sourced.)* No
   app code before this exists.
1. **Skeleton + Define + the packaging gate.** The Tauri + Python-sidecar
   packaging spike FIRST (§7), then app shell (React + design system),
   FastAPI engine skeleton, project save/load (JSON folder + provenance
   objects), soft/hard gate state machine, Project Picker (+ PDCA quick
   path routing), Charter, COPQ calculator, SIPOC, VoC/CTQ, Coffee Bar demo
   data, PDF export for one artifact — and the **clean-machine install test
   (§7)**; packaging pivots now if it fails.
2. **Measure.** Stats engine (stability, capability, normality, DPMO/sigma,
   FPY/RTY), data import (CSV/Excel), interactive Process Map + Waste Walk,
   **Spaghetti Diagram (the canvas flagship)**, Check Sheet/Tally, Guided
   Time Study, Data Collection Plan (+ sample-size guidance), Measurement
   Check, Pareto/Histogram/Run charts. Deterministic tests for every
   formula against NIST reference values. **Milestone exit: fidelity review
   of Measure content + one untrained-user test of Define+Measure** —
   Measure is where untrained users actually die (operational definitions,
   data types, capability misuse), so it gets a user-shaped run before
   Analyze is built. *(Per the 2026-08-07 owner ruling: the tester is
   Shawn if he wants the run, else a scripted untrained-persona run,
   labeled as simulated — §9.)*
3. **Analyze.** Fishbone/5 Whys (canvas), FMEA, hypothesis selector + tests
   (with effect sizes/CIs), printed decision-tree flowcharts.
4. **Improve + Control.** Solution matrix (ranked fix list), pilot
   designer, before/after proof with remaining-gap loop, I-MR + p charts +
   constants + Western Electric rules, Control Plan/OCAP + scheduled
   check-ins, scored 5S audit, Standard Work, A3 narrative builder,
   tollgate checklists, Print Shop demo project completed across the
   attribute path.
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
  continuous-data/cycle-time). A scripted walkthrough drives each
  scenario through every Tier-A tool **in its declared scope** — each
  scenario spec names its in-scope tools and N/A set when it is authored
  (a project with no movement component honestly has no spaghetti
  diagram), and the scenario set collectively exercises all 25 (the
  inventory is the M0 matrix's tool list, `docs/traceability-matrix.md`
  §1 — one authoritative count, no drift between milestones, rubric, and
  goldens); outputs are frozen as goldens and diffed on every change.
  Rubric items resting on organizational facts a time-boxed scenario
  cannot supply (implementation beyond the pilot, an owner who accepted
  the role, post-improvement actuals) grade plan-and-record quality in
  eval mode, per rubric §10.7a — and each scenario spec supplies those
  facts as **scenario ground truth** (the named owner, the window, the
  after-data), so the items grade consistency with that truth, never
  invented fiction (Belt-panel constraint). The wall is machine-readable
  and one-directional: scenario specs carry `eval_mode:
  plan_quality_only`, and **real-project grading reverts to
  organizational reality** — implementation must be real, the owner must
  be real, actuals must be actuals (Belt-panel round 2).
- **The high-schooler test** *(amended by owner ruling 2026-08-07: no
  external humans will be sourced — the human bench is Shawn plus anyone
  he chooses to involve)*: each held-out scenario is run with only the
  suite, by (a) Shawn and/or humans he brings, and (b) scripted
  untrained-persona runs — an agent constrained to an untrained user's
  knowledge, choices logged — **always labeled as simulated, never
  presented as human results**. Task-level failure logging either way
  (where the run stalled, what was misread, what was asked). Scoring uses
  the shipped Green Belt rubric, applied by the external-model Belt panel
  (§6) plus the in-app grader, with disagreements arbitrated on the
  record. Pass bar: every phase scores "acceptable Green Belt
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
4. Everything else — local-first deployment, open source, portfolio-first,
   six anti-hallucination layers — carries forward intact. (The April
   Streamlit stack was later superseded 2026-08-04 by React + Tauri +
   Python sidecar, ruled after the modern-UX research; §3, §7.)

## 11. Open decisions for Shawn

**Ruled 2026-08-04:** license is **Apache 2.0**; the advisor's flagship
mode is remedy advice (§5.1) — tool use belongs to the product, AI is for
judgment on the problem. On experiments, two rulings same day, second
supersedes: Shawn first chose adding a multi-factor experiment tool to v1;
after seeing what the tool actually is, he ruled for **one change at a
time as the product's method** — the Improve loop (§4.1) — with the
Experiment Planner moved to v1.1, ships only if real use proves the need.
(The durable rule from the exchange stands regardless: features gate on
what the data can prove, never on belt level — vault 2026-08-04-001.)

**Ruled 2026-08-04 (post-research):** all seven field-research tool
additions are IN v1 (check sheet, COPQ calculator, FPY/RTY, scored 5S
audit, guided time study, scheduled control check-ins, PDCA quick path);
stack is **React + Konva + Plotly.js frontend, FastAPI/scipy Python
sidecar, Tauri single-installer** — superseding April's Streamlit
decision; spaghetti diagram promoted to Tier A interactive flagship, 2D
canvas (three.js ruled out by research as unrecognizable overkill; 2.5D
flourish possible later).

Still open, not blocking. Two worth a ruling when convenient:

1. **Name/positioning of the free packs.** The PDF template pack + prompt
   pack as a standalone free download is a distribution decision (great
   on-ramp, but it's also the part easiest to copy). Default: ship them
   openly — the app and the architecture are the moat, and this is a
   portfolio piece.
2. **Packaging fallback order** if the M1 spike or clean-machine test fails
   (§7): stlite+Electron first, Streamlit+pip second is the default — flip
   it if he has a preference.

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
