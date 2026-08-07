---
type: knowledge
status: draft
tags: [m0, traceability, bok]
date: 2026-08-07
---

# Green Belt BoK Traceability Matrix — Milestone 0

**Status:** DRAFT — locks only after independent certified-Belt review of the rubric (PLAN §8, milestone 0).
**Date:** 2026-08-07

**Pinned references** (pins name outline versions, not licensed text — no ASQ/IASSC/PeopleCert copyrighted prose is reproduced here; topic names and original wording only):

1. **ASQ Certified Six Sigma Green Belt Body of Knowledge, 2022 edition** — six sections: I. Overview: Six Sigma and the Organization; II. Define; III. Measure; IV. Analyze; V. Improve; VI. Control. Outline taken from ASQ's official 2014→2022 BoK Map PDF (`asq.org/cert/resource/pdf/certification/2022-SSGB-BoK-Map.pdf`), **fetched and extracted live 2026-08-07** — every topic code and name below is verified against that document.
2. **IASSC/PeopleCert Lean Six Sigma Green Belt Body of Knowledge** — five phases (D-M-A-I-C) with subtopics. Outline **fetched live 2026-08-07** from both `iassc.org/body-of-knowledge/green-belt-body-of-knowledge/` and the PeopleCert syllabus PDF at the v1.1 URL (`peoplecert.org/.../lsspeoplecertgbsyllabusenv11.pdf`); the two topic lists are identical. One discrepancy to record: the PDF served at the v1.1 URL self-identifies internally as "Version 1.0, June 2021" — the pin is the topic outline (verified), and the version-stamp mismatch goes to the M2 fidelity review.

**Authority statement (PLAN §1, the acceptance contract):** the quality bar — Green Belt-grade work on everything the suite covers — is fixed and never softens. The coverage list is what flexes, and only visibly: this matrix names exactly which BoK items v1 covers, which are explain-only, and which exit to a human expert. The rubric grades against this declared scope. **If this matrix shows a genuinely-required Green Belt capability missing from the tool list, the tool list grows — the matrix corrects the plan, not the other way around.** Coverage claims in any README or marketing come from this matrix; the gaps are named, never asserted away. §5a below applies that clause: five corrections to PLAN §4.1 are proposed there, and rows they affect are marked `†`.

**How to read the coverage column:** a `T-nn` ID means a shipping v1 tool does the work; `explain-only` means the suite teaches the topic (helper text, decision-tree annotations, advisor) but generates no artifact for it; `EXIT-nn` means the suite recognizes the case and routes it honestly (§4); `v1.1` / `v2` means a named, scheduled tool covers it in that release; `out-of-scope` means beyond Green Belt product scope with the exit named. `†` = coverage contingent on a §5a plan correction.

## 1. Authoritative tool inventory

This table is **the single authoritative tool count** PLAN §9 refers to ("the inventory is the M0 matrix's tool list — one authoritative count, no drift between milestones, rubric, and goldens"). Tool list taken verbatim from PLAN §4.1: Tier A table, Tier B line, v1.1 list, v2 list. **Tier A count: 25.** (PLAN §10's "~19" predates the seven field-research additions ruled in on 2026-08-04; per the acceptance contract, this table is the number.)

| ID | Tool | Phase | Tier |
|---|---|---|---|
| T-01 | Project Picker (+ PDCA quick path routing) | Intake | A |
| T-02 | COPQ / Benefit Calculator | Define | A |
| T-03 | Project Charter | Define | A |
| T-04 | SIPOC | Define | A |
| T-05 | VoC → CTQ Tree | Define | A |
| T-06 | Process Map (swimlane) + Waste Walk | Measure | A |
| T-07 | Spaghetti Diagram (interactive) | Measure | A |
| T-08 | Check Sheet / Tally | Measure | A |
| T-09 | Guided Time Study / Work Sampling | Measure | A |
| T-10 | Yield Calculator (FPY/RTY + DPMO) | Measure | A |
| T-11 | Data Collection Plan (+ sample-size guidance) | Measure | A |
| T-12 | Measurement Check (narrow MSA) | Measure | A |
| T-13 | Baseline: Stability then Capability | Measure | A |
| T-14 | Pareto / Histogram / Run Chart | Measure | A |
| T-15 | Fishbone (6M) + 5 Whys | Analyze | A |
| T-16 | FMEA (process) | Analyze | A |
| T-17 | Hypothesis Testing (guided selector) | Analyze | A |
| T-18 | Solution Selection Matrix | Improve | A |
| T-19 | Pilot Plan | Improve | A |
| T-20 | Before/After Proof + Remaining-Gap Check | Improve | A |
| T-21 | Control Charts (I-MR, p) | Control | A |
| T-22 | Control Plan + Response Plan (OCAP) + Scheduled Check-ins | Control | A |
| T-23 | 5S Audit (scored) | Control | A |
| T-24 | Standard Work / SOP | Control | A |
| T-25 | A3 Final Report + Tollgate Checklists | Wrap | A |
| T-26 | Stakeholder Analysis + Communication Plan | Define | B |
| T-27 | Data-collection log sheets | Measure | B |
| T-28 | Kaizen / quick-win tracker | Improve | B |
| T-29 | Chart families: X-bar/R, np, c, u | Control | v1.1 |
| T-30 | Correlation + Simple Linear Regression (guided, with scatter plots) | Analyze | v1.1 |
| T-31 | 8D corrective-action report (export skin over project data) | Wrap | v1.1 |
| T-32 | Takt Time + Simple Line Balancing | Measure/Improve | v1.1 |
| T-33 | Guided OEE Calculator | Measure | v1.1 |
| T-34 | Multi-factor Experiment Planner (ships only if real use proves need) | Improve | v1.1 |
| T-35 | Full multi-operator Gage R&R | Measure | v2 |
| T-36 | DOE beyond the planner spec (fractional designs, response surface) | Improve | v2 |
| T-37 | Multi-Vari | Analyze | v2 |
| T-38 | VSM future-state | Measure | v2 |
| T-39 | EWMA / CUSUM charts | Control | v2 |
| T-40 | Monte Carlo | Analyze | v2 |
| T-41 | QFD | Define | v2 |
| T-42 | Taguchi | Improve | v2 |
| T-43 | TRIZ | Improve | v2 |

Notes: (1) PLAN §4.1's v1.1 list also includes "second demo project polish" — content, not a tool; excluded from the inventory. (2) Tier B = guided templates, real forms with instruction panels, no statistical claims, labeled as such in-app. (3) §5a proposes growing T-03, T-14, T-17, T-22 by specific form fields/routes — field-level growth, no new tool IDs.

**Golden coverage rule (PLAN §9):** every Tier-A tool carries ≥1 golden test; computational tools (T-10, T-12, T-13, T-14, T-17, T-20, T-21) additionally carry NIST-reference unit tests. Golden IDs proposed in the matrix below; the eval harness will be authored against them.

**Rubric ID plan:** R-\<PHASE\>-NN, PHASE ∈ {ORG, DEF, MEA, ANA, IMP, CTL, WRAP}. This matrix proposes 39 rubric items (R-DEF-01..08, R-MEA-01..11, R-ANA-01..06, R-IMP-01..05, R-CTL-01..06, R-WRAP-01..03); the rubric document will be authored to honor these IDs. **R-ORG-\* is deliberately empty in v1:** Overview-section knowledge is graded where it lands in project artifacts (FMEA → R-ANA-03, spaghetti → R-MEA-03, SMART goals → R-DEF-03), not as standalone knowledge checks — the suite grades project work, not exam recall.

## 2. Coverage matrix — ASQ CSSGB 2022

One row per 2022 BoK subtopic (leaf item), using ASQ's own numbering — 66 rows total (8 + 23 + 13 + 6 + 6 + 10). Subtopic names are ASQ's published topic titles; parenthetical detail paraphrases the subtext in original wording. "Std LSS curriculum" in the source column means non-quantitative content taught the same way in any Green Belt course, written originally for this suite. "NIST/SEMATECH" = the NIST/SEMATECH e-Handbook of Statistical Methods; section numbers are given where confident, chapter level otherwise.

### 2.I — Overview: Six Sigma and the Organization

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| I.A.1 Value of six sigma | explain-only (onboarding + helper text) | Std LSS curriculum | — | — |
| I.A.2 Organizational goals and six sigma projects (SMART goals) | T-01, T-03 (goal linkage in picker; SMART goal builder in charter) | Std LSS curriculum; SMART criteria | R-DEF-01, R-DEF-03 | G-picker-01, G-charter-01 |
| I.A.3 Organizational drivers and metrics (KPIs) | explain-only (T-01/T-02 helper frames business drivers) | Std LSS curriculum | — | — |
| I.B.1 Lean concepts (TOC, value chain, flow, takt, JIT, Gemba, spaghetti diagrams, perfection) | T-07 (spaghetti — done, not just defined); T-32 (v1.1 takt); rest explain-only | Elementary geometry (scale calibration, distance × frequency); Std LSS curriculum | R-MEA-03 | G-spaghetti-01 |
| I.B.2 Value-stream mapping (VA/waste identification) | T-06 (functional coverage: VA/NVA/enabling tagging + times + waste walk); formal VSM notation explain-only; future-state = T-38 (v2). See §5b | Std LSS curriculum (VA/NVA classification, 8 wastes) | R-MEA-01, R-MEA-02 | G-procmap-01 |
| I.C.1 Road maps for DFSS (DMADV, IDOV) | explain-only (out of a DMAIC project's path) | Std LSS curriculum | — | — |
| I.C.2 Basic FMEA (scale criteria, RPN) | T-16 | Industry-standard 1–10 anchor structure, original generic wording; RPN = S×O×D with stated limitation | R-ANA-03 | G-fmea-01 |
| I.C.3 Design FMEA and process FMEA (distinguish) | explain-only (T-16 helper text; the suite ships process FMEA) | Std LSS curriculum | — | — |

### 2.II — Define

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| II.A.1 Project selection | T-01 | Field-research intake criteria + std LSS curriculum | R-DEF-01 | G-picker-01 |
| II.A.2 Process elements (components, boundaries, cross-functional) | T-04, T-06 | Std LSS curriculum | R-DEF-06, R-MEA-01 | G-sipoc-01 |
| II.A.3 Benchmarking (competitive, collaborative, best practices) | explain-only. See §5b | Std LSS curriculum | — | — |
| II.A.4 Process inputs and outputs (SIPOC model) | T-04 | Std LSS curriculum | R-DEF-06 | G-sipoc-01 |
| II.A.5 Owners and stakeholders | T-03 (team + process owner required fields); T-26 (Tier B deep-dive) | Std LSS curriculum | R-DEF-04 | G-charter-01 |
| II.B.1 Customer identification (internal/external) | T-05 | Std LSS curriculum | R-DEF-07 | G-ctq-01 |
| II.B.2 Customer data (surveys, focus groups, interviews, observation) | T-05 (statement capture + bias checks); collection-method mechanics explain-only | Std LSS curriculum | R-DEF-07 | G-ctq-01 |
| II.B.3 Customer requirements (QFD, CTX, CTQ tree, Kano) | T-05 (CTQ tree — the doing path); QFD = T-41 (v2); Kano/CTX explain-only | Std LSS curriculum | R-DEF-07 | G-ctq-01 |
| II.C.1 Project methodology (agile, top-down) | explain-only. See §5b | Std LSS curriculum | — | — |
| II.C.2 Project charter (problem statement w/ baseline + goals) | T-03 | Std LSS curriculum; rule-based solution-language checks | R-DEF-02, R-DEF-03 | G-charter-01 |
| II.C.3 Project scope (process maps, Pareto to bound scope) | T-03 (scope in/out) + T-14 (Pareto as scoping evidence) | Std LSS curriculum | R-DEF-04 | G-charter-01 |
| II.C.4 Project metrics (primary + consequential) | T-03 | Std LSS curriculum | R-DEF-03 | G-charter-01 |
| II.C.5 Project planning tools (WBS, Gantt, CPM, PERT, tollgate reviews) | T-25 (tollgate reviews — done); T-03 (timeline field); WBS/Gantt/CPM/PERT explain-only. See §5b | Std LSS curriculum / std PM practice | R-DEF-08 | G-tollgate-01 |
| II.C.6 Project documentation (data, presentation tools, phase reviews) | T-25 + project-folder/provenance architecture (PLAN §4.5) | Std LSS curriculum | R-WRAP-01 | G-a3-01 |
| II.C.7 Project risk analysis and management (feasibility, impact, RPN, continuity) | T-03 † (charter risk block — §5a A-4) + T-16 (RPN mechanics) | Std LSS curriculum; RPN per FMEA anchors | R-DEF-04 | G-charter-01 |
| II.C.8 Project closure (objectives vs charter, lessons learned) | T-25 (closure + lessons panel) | Std LSS curriculum | R-WRAP-03 | G-a3-01 |
| II.D Management and planning tools (affinity, interrelationship digraph, tree diagram, prioritization matrix, matrix diagram, PDPC, activity network, SWOT) | explain-only; two live as forms: T-05 is a tree diagram, T-18 is a prioritization/weighted matrix. See §5b | Std LSS curriculum | — | — |
| II.E.1 Process performance (DPU, RTY, COPQ, DPMO, sigma levels, capability indices) | T-02 (COPQ), T-10 (DPU/FPY/RTY/DPMO), T-13 (indices, sigma level) | Standard FPY/RTY/DPU/DPMO definitions (cross-checked vs DMAIC.io + Qualica templates); NIST/SEMATECH §6.1.6 for indices; NIST ref test | R-DEF-05, R-MEA-09 | G-copq-01, G-yield-01, G-baseline-01 |
| II.E.2 Communication (top-down, bottom-up, horizontal) | explain-only; T-26 (Tier B comm plan form). See §5b | Std LSS curriculum | — | — |
| II.F.1 Team stages and dynamics (forming–adjourning; negative dynamics) | explain-only. See §5b | Std LSS curriculum (Tuckman stages) | — | — |
| II.F.2 Team roles and responsibilities (RACI, belts, champion, sponsor, owner) | T-26 (Tier B RACI-style grid); role definitions explain-only | Std LSS curriculum | — | — |
| II.F.3 Team tools and decision-making (brainstorming, NGT, multivoting) | explain-only; Layer-2 "Help me think" runs the brainstorm, T-15/T-18 capture output | Std LSS curriculum | — | — |
| II.F.4 Team communication (progress, reviews, stakeholders) | T-26 (Tier B communication plan); T-25 (phase reviews) | Std LSS curriculum | — | — |

### 2.III — Measure

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| III.A Process analysis and documentation (maps, procedures, work instructions, flowcharts) | T-06 (as-is map); T-24 (procedures/work instructions on the improved state) | Std LSS curriculum | R-MEA-01 | G-procmap-01 |
| III.B.1 Basic probability concepts (independence, mutual exclusivity, multiplication, permutations/combinations) | explain-only (taught where it bites: sample-size and distribution helper text). See §5b | Standard probability theory | — | — |
| III.B.2 Central limit theorem (CIs, hypothesis tests, control charts) | explain-only (T-11 sample-size helper; T-17/T-21 helper) | Standard statistical theory | — | — |
| III.C Statistical distributions (normal, binomial, Poisson, chi-square, t, F) | explain-only user-facing; engine-internal to T-13/T-17/T-21 computations | NIST/SEMATECH §1.3.6 (probability distributions) | — | — |
| III.D.1 Types of data and measurement scales (continuous/discrete; nominal/ordinal/interval/ratio) | T-11 (data-type identification is a first-class field, drives every downstream route) | Std LSS curriculum / standard measurement theory | R-MEA-05 | G-dcp-01 |
| III.D.2 Sampling and data collection plans/methods (random, stratified; check sheets, coding, quality checks) | T-08 (check sheet), T-11 (plan + stratification + quality checks), T-27 (Tier B log sheets) | Std LSS curriculum; sample-size rules of thumb w/ plain-English framing | R-MEA-05, R-MEA-06 | G-checksheet-01, G-dcp-01 |
| III.D.3 Descriptive statistics (central tendency, dispersion, frequency distributions) | T-13/T-14 (computed + displayed on every baseline chart); T-09 (element-time spread) | NIST/SEMATECH §1.3.5 (quantitative techniques); NIST ref test | R-MEA-10 | G-hist-01 |
| III.D.4 Graphical methods (scatter, normal probability plot, histogram, stem-and-leaf, box-and-whisker) | T-14 (histogram, run) + T-13 (normal probability plot) + box/scatter † (§5a A-2); stem-and-leaf explain-only | NIST/SEMATECH §1.3.3 (graphical techniques) | R-MEA-10 | G-hist-01, G-run-01 |
| III.E Measurement system analysis (GR&R, correlation, bias, linearity, percent agreement, P/T) | T-12 (narrow: test/retest %GRR-style verdict + two-rater attribute agreement); full multi-operator GR&R = T-35 (v2); bias/linearity explain-only + EXIT-03 | NIST/SEMATECH §2.4 (gauge R&R studies); NIST ref test | R-MEA-07 | G-msa-01, G-msa-02 (fail path) |
| III.F.1 Process performance vs. process specifications (natural limits vs spec limits) | T-13 (spec limits + operational definition enforced first) | NIST/SEMATECH §6.1.6 | R-MEA-08 | G-baseline-01 |
| III.F.2 Process capability studies (characteristics, specs, tolerances; verify stability and normality) | T-13 (order-enforced: stability → then capability; normality advisory) + EXIT-04, EXIT-05 | NIST/SEMATECH §6.1.6; normality per §1.3.5 (Anderson-Darling + visual) | R-MEA-08 | G-baseline-01, G-baseline-02 (unstable path) |
| III.F.3 Cp, Cpk / Pp, Ppk indices (relationship; Cpm; sigma level) | T-13 (Cp/Cpk within vs Pp/Ppk overall, distinction explained); Cpm explain-only | NIST/SEMATECH §6.1.6; NIST ref test | R-MEA-09 | G-baseline-01, G-baseline-03 (non-normal path) |
| III.F.4 Short-term vs. long-term capability and sigma shift | T-13 (1.5σ shift convention named + toggleable) | Std LSS convention, stated explicitly (PLAN §6) | R-MEA-09 | G-baseline-01 |

### 2.IV — Analyze

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| IV.A.1 Multi-vari studies (positional, cyclical, temporal) | explain-only; formal tool = T-37 (v2); stratified views via T-08/T-11 tags + T-14 give the working GB equivalent. See §5b | Std LSS curriculum | — | — |
| IV.A.2 Correlation and linear regression (correlation ≠ causation; coefficient, significance, prediction) | T-30 (v1.1 — guided, with scatter); v1: scatter plot † (§5a A-2) + EXIT-15 named deferral; correlation-vs-causation explain-only in v1 | NIST/SEMATECH ch. 7; scipy/statsmodels; NIST ref test (at v1.1) | R-ANA-05 (interpretation discipline) | G-hyp-06 (selector routes/exits); T-30 goldens at v1.1 |
| IV.B.1 Hypothesis testing basics (statistical vs practical significance, sample size, power, Type I/II) | T-17 (selector output: effect size + CI + practical-vs-statistical, always); T-11 (sample-size calculator); power explain-only advisory + EXIT-06 (n floors) | NIST/SEMATECH ch. 7; std statistical definitions | R-ANA-04, R-ANA-05 | G-hyp-06 |
| IV.B.2 Tests for means, variances, and proportions (paired t, F, ANOVA, chi-square) | T-17: Welch 2-sample t, paired t, one-way ANOVA, chi-square, 2-proportion; Mann-Whitney + Wilcoxon signed-rank fallbacks; 1-sample routes † (§5a A-1); variance tests (F) explain-only (see §5b) + EXIT-13 on ANOVA-significant | NIST/SEMATECH §7.3 (two-process comparisons), §7.4 (multi-process/ANOVA); scipy; NIST ref tests | R-ANA-04, R-ANA-05 | G-hyp-01 (Welch t), G-hyp-02 (ANOVA), G-hyp-03 (chi-sq), G-hyp-04 (proportions), G-hyp-05 (nonparametric fallbacks) |
| IV.C.1 Gap analysis (current vs future state with predefined metrics) | T-20 (remaining-gap check — gap analysis operationalized) + T-02 (gap in dollars) | Std LSS curriculum; arithmetic on computed baselines | R-IMP-04 | G-proof-01 |
| IV.C.2 Root cause analysis (cause/effect diagrams, relational matrices, 5 Whys, fault tree) | T-15 (fishbone + 5 Whys + evidence fields); fault tree + relational matrices explain-only | Std LSS curriculum (Ishikawa 6M) | R-ANA-01, R-ANA-02 | G-fishbone-01 |

### 2.V — Improve

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| V.A.1 DOE basic terms (factors, levels, responses, blocks, randomization, replication…) | explain-only in v1 (helper text draws the line from the pilot — a one-factor experiment — to DOE vocabulary); T-34 (v1.1, conditional). See §5b | Std experimental-design vocabulary | — | — |
| V.A.2 DOE graphs and plots (main effects, interactions) | explain-only in v1; T-34 computes them at v1.1 | Std experimental-design methods | — | — |
| V.B Implementation planning (proof of concept, try-storming, simulations, pilot tests) | T-19 (pilot designer — the doing core) + T-18 (ranked implementation queue); try-storming/simulation explain-only | Std LSS curriculum; pilot discipline per PLAN §4.1 (one change, pre-declared threshold, falsification line, confounder checklist) | R-IMP-01, R-IMP-02 | G-pilot-01, G-solmatrix-01 |
| V.C.1 Waste elimination (pull, kanban, 5S, standard work, poka-yoke) | T-23 (5S — scored audit), T-24 (standard work); pull/kanban/poka-yoke explain-only + Layer-2 remedy advisor proposes them | Std lean practice, original wording | R-CTL-04, R-CTL-05 | G-5s-01, G-stdwork-01 |
| V.C.2 Cycle-time reduction (continuous flow, setup reduction, SMED) | explain-only as remedies (Layer-2 remedy advisor); T-06/T-09 quantify cycle time; T-32 (v1.1 takt/line balancing) | Std lean practice | — | — |
| V.C.3 Kaizen and kaizen blitz | T-28 (Tier B quick-win tracker) + T-01 (PDCA quick path for small problems) | Std lean practice | R-DEF-01 (routing) | G-picker-02 (PDCA route) |

### 2.VI — Control

| BoK item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| VI.A.1 SPC basics (objectives; common vs special cause; chart deduction) | T-21 (verdict headlines name the signal and its meaning) | NIST/SEMATECH §6.3.1 (what are control charts); Western Electric rules | R-CTL-01, R-CTL-02 | G-imr-01, G-werules-01 |
| VI.A.2 Rational subgrouping | explain-only in v1 (bites at X-bar/R, which is T-29 v1.1; I-MR needs only honest time-ordering — EXIT-09 guards the autocorrelation trap). See §5b | Std SPC practice | — | — |
| VI.A.3 Control charts (X̄-R, X̄-s, ImR/XmR, median, p, np, c, u) | T-21 (I-MR, p — the two a GB reaches for); T-29 (v1.1: X̄-R, np, c, u); X̄-s + median explain-only; selector by data type is a printed decision tree | Standard published constant tables (d2, A2, D3, D4…); NIST/SEMATECH §6.3.2 (variables), §6.3.3 (attributes); NIST ref tests | R-CTL-01 | G-imr-01, G-pchart-01 |
| VI.B.1 Control plan (develop, implement, document, monitor) | T-22 (named owner required; monitoring cadence; scheduled check-ins chase the follow-through) | Std LSS curriculum | R-CTL-03, R-CTL-04 | G-ctrlplan-01 |
| VI.B.2 Document control | explain-only + embodied in architecture (artifact versioning, provenance objects — PLAN §4.5; T-24 SOP carries version/owner fields). See §5b | Std quality-system practice | — | — |
| VI.B.3 Training plans (implement and sustain improvements) | T-22 † (training & handoff block — §5a A-5); T-24 (the training artifact itself) | Std LSS curriculum | R-CTL-04 | G-ctrlplan-01 |
| VI.B.4 Audits (first-, second-, third-party) | explain-only (taxonomy); T-23 is a live first-party audit instance. See §5b | Std quality-system practice | — | — |
| VI.B.5 Plan-do-check-act (PDCA) | T-01 (PDCA quick path — the steps applied, not just defined) | Std LSS curriculum (Deming/Shewhart cycle) | R-DEF-01 (routing) | G-picker-02 |
| VI.C.1 Total productive maintenance (TPM; predictive maintenance) | explain-only (remedy advisor can propose). See §5b | Std lean practice | — | — |
| VI.C.2 Visual factory (Andon, Jidoka) | explain-only; T-23 photos/trend + posted control charts are the practical variants. See §5b | Std lean practice | — | — |

## 3. IASSC delta rows

The IASSC/PeopleCert GB syllabus (5 phases, 47 subtopics) was swept in full against §2. Most IASSC subtopics land on an existing ASQ row (e.g., IASSC 1.2.3 COPQ → ASQ II.E.1; 2.1.1 Fishbone → IV.C.2; 2.3.x MSA → III.E; 5.2.2 I-MR → VI.A.3; 5.3.2/5.3.3 control/response plan → VI.B.1) and are not duplicated here. The 15 rows below are the IASSC topics **not** already dispositioned by an ASQ row.

| IASSC item | Coverage | Method/formula source | Rubric | Golden |
|---|---|---|---|---|
| 1.1.4 The problem-solving strategy Y = f(x) | explain-only — the suite's charter → CTQ → metric → baseline → test thread **is** Y = f(x); helper text names it | Std LSS curriculum | — | — |
| 1.1.5 Voice of the Customer, Business and Employee (VoB/VoE beyond ASQ's VOC) | explain-only (T-05 helper distinguishes the three voices; VOC itself → ASQ II.B rows) | Std LSS curriculum | — | — |
| 2.1.3 X-Y diagram (cause-and-effect matrix) | explain-only — function absorbed: T-15 evidence fields + T-20 ranked-cause loop do the cause-prioritization job. See §5b | Std LSS curriculum | — | — |
| 2.4.3 Attribute & discrete capability | T-10 (DPMO/sigma from defect counts) + T-13/T-21 (p-chart baseline path — the Print Shop demo thread) | Standard binomial/DPMO methods (cross-checked vs DMAIC.io/Qualica); NIST ref test | R-MEA-09 | G-yield-01, G-pchart-01 |
| 3.4.1 one-sample t-test (the 1-sample half; 2-sample → ASQ IV.B.2) | T-17 † (one-sample-vs-target route — §5a A-1) | NIST/SEMATECH §7.2 (single-process comparisons); scipy; NIST ref test | R-ANA-04 | G-hyp-07 † |
| 3.4.2 one-sample variance test | explain-only — spread changes are shown by I-MR + capability comparison; formal variance tests rare in GB projects. See §5b | Std statistical methods | — | — |
| 3.5.2 Kruskal-Wallis | EXIT-14 in v1 (named, honest); recommend T-17 route at v1.1 (§5a A-3) | Std nonparametric methods; scipy (at v1.1) | R-ANA-04 (exit correctness) | G-hyp-06 (exit case) |
| 3.5.3 Mood's median | explain-only — Mann-Whitney fallback + EXIT-14 cover the GB need. See §5b | Std nonparametric methods | — | — |
| 3.5.4 Friedman | explain-only + EXIT-08 (repeated measures is a named exit). See §5b | Std nonparametric methods | — | — |
| 3.5.5 one-sample sign test | explain-only — Wilcoxon signed-rank is the shipped fallback. See §5b | Std nonparametric methods | — | — |
| 3.5.6 one-sample Wilcoxon | T-17 † (ships as the nonparametric fallback of the one-sample-vs-target route — §5a A-1) | Std nonparametric methods; scipy | R-ANA-04 | G-hyp-07 † |
| 3.5.7 one-sample proportion (2-sample → ASQ IV.B.2) | T-17 † (proportion-vs-target route — §5a A-1) | Standard exact/normal-approx binomial test; scipy; NIST ref test | R-ANA-04 | G-hyp-07 † |
| 4.2 Multiple regression analysis (4.2.1 non-linear, 4.2.2 multiple linear, 4.2.3 CI/PI, 4.2.4 residuals) | out-of-scope for v1 tools (Black Belt-tier modeling); EXIT-10 (>1 factor) + EXIT-15 route it by name; advisor can explain | Std regression methods (v2 territory) | — | — |
| 4.2.5 Data transformation, Box-Cox | explain-only — the suite's non-normal path is percentile capability with a plain-English caveat (EXIT-05), not transformation. See §5b | Std statistical methods | — | — |
| 5.2.8 CuSum + 5.2.9 EWMA charts | out-of-scope v1 → T-39 (v2); explain-only meanwhile (I-MR + Western Electric rules are the GB reach) | Std SPC methods (v2) | — | — |

## 4. Named-exit registry

Every honesty exit the suite must recognize, in flow order. Exits are gated by method limits, never by belt level (vault correction 2026-08-04-001). "This needs an experienced human" is a first-class output, not a failure state (PLAN §1). EXIT-01..05 are flow/quality gates; EXIT-06..15 are hypothesis-selector cases — the selector's enumerated unsupported-case list per PLAN §4.1, plus two cases this BoK sweep surfaced (EXIT-14, EXIT-15). Each exit path is itself golden-tested (an exit case appears in G-picker-02, G-msa-02, G-baseline-02, G-hyp-06) and one held-out eval scenario deliberately requires recognizing an exit (PLAN §9).

| EXIT | Trigger condition | What the suite says/does | Routes to |
|---|---|---|---|
| EXIT-01 | Intake: problem too broad / outcome not measurable / no obtainable data / no process owner | Picker names the failed criterion; "not a viable first GB project as scoped" | Rescope guidance; small problem → PDCA quick path (T-01); organizational/political problem → sponsor or human expert |
| EXIT-02 | Measurement check fails (repeatability or attribute agreement below floor) | "Stop — fix your measurement first." Capability-claim language blocked; downstream results labeled "unreliable — measurement system failed" until fixed | T-11 (operational definition rework) → re-run T-12 |
| EXIT-03 | Measurement question exceeds the narrow check (multi-operator GR&R, bias/linearity/stability study needed) | Names the needed study and states the tool doesn't run it (v2 scope: T-35) | Human quality engineer / certified Belt; v2 |
| EXIT-04 | Baseline process not stable (I-MR signals) | "You don't have a baseline yet"; instability-pattern guidance; Pp/Ppk only, labeled performance-not-capability; no Cp/Cpk claim | Find/remove special causes, re-run T-13; persistent instability → human expert |
| EXIT-05 | Non-normal data at capability (caveat path, not a stop) | Percentile-method capability with plain-English caveat; caveat prints on all exports; advisory normality read (visual + test + n-aware), never a silent auto-gate | Stays in T-13; advisor explains implications |
| EXIT-06 | Sample size below the stated floor for the routed test | Named refusal with the floor and the n still needed — no underpowered p-value theater | T-11 sample-size calculator → collect more data |
| EXIT-07 | Sparse cells (chi-square expected counts below floor) | "This table is too sparse for a trustworthy chi-square" | Collect more data or honestly merge categories; else human expert |
| EXIT-08 | Repeated measures (>2 related measurements per unit) | Beyond the paired case the tree carries; named as repeated-measures territory | Human expert / Black Belt; advisor explains study structure |
| EXIT-09 | Autocorrelated data (time-dependence violates test and I-MR assumptions) | Names the autocorrelation problem and why the standard result would mislead | Time-ordered analysis guidance; human expert |
| EXIT-10 | More than one factor changed / multi-factor question | The Improve loop's one-change-at-a-time discipline invoked; combined tests named as experiment territory | Advisor "help me think"; T-34 Experiment Planner (v1.1); human expert for real multi-factor designs |
| EXIT-11 | Rates with exposure (events per opportunity-window, Poisson-type) | Named as rate data the v1 battery doesn't test | u-chart family (T-29, v1.1) for monitoring; human expert for rate comparisons |
| EXIT-12 | Multiple simultaneous comparisons requested | Multiplicity warning — shotgun p-values refused; "declare one primary comparison" | One pre-declared primary comparison, or human expert |
| EXIT-13 | ANOVA significant → which pairs differ? | Canned honest interim: "these groups differ overall; fair pairwise comparison needs a correction — guided pairwise ships in v1.1" | Interim read now; T-17 pairwise route (v1.1) |
| EXIT-14 | 3+ groups with markedly non-normal / ordinal data (Kruskal-Wallis territory) — *surfaced by IASSC 3.5.2* | Named: "the shipped tests don't cover this case honestly"; shows medians + distribution display, no formal verdict | Kruskal-Wallis route recommended for T-17 at v1.1 (§5a A-3); human expert meanwhile |
| EXIT-15 | Continuous-x ↔ continuous-y relationship question (correlation/regression) — *surfaced by ASQ IV.A.2 / IASSC 4.1* | v1 shows the scatter plot († §5a A-2) and names the deferral: "quantified correlation/regression ships in v1.1" | T-30 (v1.1); advisor explains correlation ≠ causation meanwhile |

## 5. Gap analysis

### 5a. Real-project capabilities not covered by the current tool list

Per the acceptance contract, these correct PLAN §4.1. All five corrections are **field/route-level growth inside existing tools** — no new tool IDs, no Tier-A count change. Rows marked `†` in §2–§3 depend on them.

**A-1. One-sample tests against a target.** IASSC 3.4.1/3.5.6/3.5.7 require 1-sample t, 1-sample Wilcoxon, and 1-sample proportion; ASQ IV.B.2 "tests for means…and proportions" implies the one-sample case too. A real GB project routinely asks "is my baseline (or my pilot result) different from the stated target?" — the selector currently has no route for it and would either misroute or exit on a case it should handle. **Recommendation: grow T-17** with three thin routes — one-sample t vs target, Wilcoxon signed-rank vs target (its nonparametric fallback), one-proportion vs target. Same engine, same decision tree, same output contract (effect size + CI + plain English). New golden: G-hyp-07.

**A-2. Scatter and box plots in v1.** ASQ III.D.4 is Create-level: the student must *construct* scatter diagrams and box-and-whisker plots. v1 currently has neither as a first-class chart (scatter arrives with T-30 in v1.1; box plots are implicit in T-17's group displays). **Recommendation: grow T-14's chart set** with scatter (visual only — no fitted line, no r; EXIT-15 names the inference deferral) and make the box plot explicit in T-14/T-17 group displays. Cheap (Plotly built-ins), closes the only Create-level graphical gap.

**A-3. Non-normal 3+ group comparison (Kruskal-Wallis).** IASSC 3.5.2. The selector's enumerated exits didn't include this case — a user with three shifts of skewed cycle-time data would hit a formally-computed-but-fragile ANOVA. **Recommendation:** register EXIT-14 now (done, §4) so v1 detects and exits by name; add the Kruskal-Wallis route to T-17 in v1.1 (scipy carries it; the cost is the decision-tree branch and a golden, not math).

**A-4. Project risk on the charter.** ASQ II.C.7 (risk analysis and management) has no v1 home — the charter spec has no risk field, and FMEA covers process failure modes, not project risks. A real GB project states its risks at Define. **Recommendation: grow T-03** with a lightweight "key risks & mitigations" block (risk, likelihood/impact rating, mitigation, owner) graded under R-DEF-04. Deep risk work stays T-16.

**A-5. Training & handoff in the control plan.** ASQ VI.B.3 (training plans — new in the 2022 BoK) is a real sustainment requirement: a fix that nobody is trained on dies with the project. T-24 produces the training artifact (the SOP) but nothing plans who gets trained, by whom, verified how. **Recommendation: grow T-22** with a "training & handoff" block (who, on what, by when, verified how), graded under R-CTL-04 and checked by the scheduled check-ins.

**A-6. Correlation/regression timing — flag, not a change.** ASQ IV.A.2 is Evaluate-level and genuinely used in GB projects (continuous x vs continuous y). T-30 already covers it **in v1.1**; with A-2's scatter plot and EXIT-15's named deferral, v1 is honest but not complete on this item. This is acceptable **only because** PLAN calls v1.1 "next release, not v-someday." Two conditions attach: the golden eval scenarios (PLAN §9) must not require regression to pass, and if v1.1 slips materially, this row becomes a real coverage gap and the README's coverage language must say so.

### 5b. Exam-knowledge topics where explain-only is honestly sufficient

One line each on why explain-only honestly satisfies the item — these are things a Green Belt must *know*, not things a GB project *produces*:

- **I.A.1, I.A.3** (value of six sigma; drivers/metrics) — orientation knowledge; no project artifact exists to generate.
- **I.C.1** (DFSS road maps) — DMADV/IDOV are design-methodology selection, outside a DMAIC project's path.
- **I.C.3** (design vs process FMEA) — definitional distinction; the suite ships the process FMEA a GB project uses.
- **II.A.3** (benchmarking) — taxonomy knowledge; real competitive benchmarking needs external data no first project has.
- **II.C.1** (agile/top-down methodology) — definitional exam content.
- **II.C.5** (WBS/Gantt/CPM/PERT) — generic PM tooling; charter timeline + tollgates carry what a GB project needs, and PM suites exist elsewhere.
- **II.D** (management & planning tools) — workshop facilitation aids; the two used in anger exist as forms (T-05 tree, T-18 prioritization matrix).
- **II.E.2, II.F.1–II.F.3** (communication techniques; team dynamics/tools) — human-process knowledge the advisor coaches; nothing to compute or template beyond T-26.
- **III.B.1, III.B.2, III.C** (probability, CLT, distributions) — foundational math taught where it bites (sample size, normality, chart choice); engine-internal otherwise.
- **IV.A.1** (multi-vari) — BB-leaning formal charts; stratified Pareto/box views over T-08/T-11 tags cover the GB need; T-37 at v2.
- **IV.B.2-variance / IASSC 3.4.2** (F-test, 1-sample variance) — Welch-by-default removes the classic F-pretest misuse; spread changes are visible in I-MR + capability comparison.
- **V.A.1, V.A.2** (DOE terms/plots) — the product's method is one-change-at-a-time (Shawn's ruling 2026-08-04); the pilot teaches one-factor discipline, T-34 arrives if use proves need.
- **VI.A.2** (rational subgrouping) — bites at X̄-R (v1.1); I-MR needs only honest time-ordering, and EXIT-09 guards the trap.
- **VI.B.2** (document control) — embodied in versioning + provenance architecture rather than taught as a form.
- **VI.B.4** (audit types) — taxonomy; T-23 is a live audit the user actually runs.
- **VI.C.1, VI.C.2** (TPM, visual factory) — remedy-level lean knowledge the advisor proposes where relevant.
- **IASSC 1.1.4, 1.1.5** (Y=f(x); VoB/VoE) — framing concepts the suite's own thread demonstrates.
- **IASSC 2.1.3** (X-Y diagram) — its cause-prioritization function is absorbed by T-15 evidence fields + T-20's ranked-cause loop.
- **IASSC 3.5.3–3.5.5** (Mood's, Friedman, sign test) — nonparametric alternates; the shipped fallbacks + EXIT-08/EXIT-14 cover the decisions a GB faces.
- **IASSC 4.2.5** (Box-Cox) — the suite deliberately prefers percentile capability with a caveat over transformation an untrained user can't defend.

## 6. Coverage summary

Counting rule: each row is classified by its primary disposition (a row led by a tool ID counts as tool-covered even where named sub-parts are explain-only — the sub-part disposition is stated in the row).

| Category | Count |
|---|---|
| Total BoK items (rows) | **81** — 66 ASQ 2022 + 15 IASSC delta |
| Covered by a shipping v1 tool | **47** (43 ASQ + 4 delta; 5 of these carry `†` — contingent on §5a corrections A-1/A-4/A-5) |
| Explain-only (justified in §5b) | **30** (22 ASQ + 8 delta) |
| v1.1-primary (named, scheduled) | **1** (ASQ IV.A.2 — see A-6 conditions) |
| Named-exit-primary | **1** (IASSC 3.5.2 → EXIT-14) |
| Out-of-scope v1 (v2 tier, exits named) | **2** (IASSC 4.2 multiple regression; 5.2.8/5.2.9 CuSum/EWMA) |
| Named exits registered | **15** (13 from PLAN §4.1's enumerations; EXIT-14, EXIT-15 surfaced by this sweep) |
| **Tier-A tool count (THE §9 number)** | **25** (Tier B: 3, v1.1: 6, v2: 9 — inventory total 43) |
| Proposed rubric items | 39 (R-DEF 8, R-MEA 11, R-ANA 6, R-IMP 5, R-CTL 6, R-WRAP 3; R-ORG reserved empty) |
| Goldens proposed | ≥1 per Tier-A tool; NIST-reference unit tests on T-10, T-12, T-13, T-14, T-17, T-20, T-21 |
| Items awaiting outline verification | **0** — both outlines fetched live 2026-08-07 (ASQ BoK-map PDF; IASSC via iassc.org + PeopleCert PDF). One admin item for the M2 fidelity review: the PeopleCert v1.1-URL PDF self-stamps "Version 1.0, June 2021" (topic list identical to iassc.org) |

**Plan corrections this matrix makes (per the §1 authority statement):** A-1 (one-sample test routes in T-17), A-2 (scatter + box plots in v1 chart set), A-3 (EXIT-14 now, Kruskal-Wallis at v1.1), A-4 (charter risk block), A-5 (control-plan training & handoff block) — plus the A-6 flag on v1.1 regression timing and the Tier-A count fixed at 25. PLAN §4.1 should be updated to reference this matrix; the rubric and golden documents are authored against the IDs proposed here.
