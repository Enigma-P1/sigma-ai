---
type: knowledge
status: draft
tags: [m0, rubric, green-belt]
date: 2026-08-07
---

# Green Belt Project Rubric — Milestone 0

**Status:** DRAFT — locks only after review by an independent certified Belt who did not author it (PLAN §6/§9 author/checker split; the reviewer is being sourced now, per PLAN §8 milestone 0). Until that pass, every criterion here is a proposal.
**Date:** 2026-08-07

**What this is.** The single grading authority for Sigma AI ("Green Belt in a Box"). It defines, for every phase of a DMAIC project run with the suite, what acceptable Green Belt work looks like — concretely enough that a grader can point at the artifact and decide. It grades **project work, not exam recall**: there are no R-ORG items, deliberately (matrix §1). Overview-section knowledge is graded where it lands in artifacts — FMEA knowledge in R-ANA-03, spaghetti/lean in R-MEA-03, SMART goals in R-DEF-03 — never as standalone knowledge checks.

**Three consumers, one document:**

1. **The human grader** — the independent certified Belt in the PLAN §9 evals scores real student projects item by item with this rubric.
2. **The in-app "what good looks like" panels** (PLAN §4.3) — each tool's acceptance checklist is drawn from that tool's items here. One source of truth; no parallel checklist (tier-a-done-means §2).
3. **The AI advisor's "Review my artifact" mode** (PLAN §5.1) — grades against these same items, with the rule-checkable subset pre-scored deterministically in code before the model sees anything. Each item below states honestly which of its criteria code can decide and which need judgment.

**Item IDs** are the 39 proposed by the traceability matrix (`docs/traceability-matrix.md` §1): R-DEF-01..08, R-MEA-01..11, R-ANA-01..06, R-IMP-01..05, R-CTL-01..06, R-WRAP-01..03. Every ID is defined below; none added, none dropped. Tool references (T-nn) and exit references (EXIT-nn) are the matrix's inventory and exit registry.

**The bar.** A competent **first project by an untrained-but-guided person** — Green Belt grade, not Black Belt polish. Every criterion must be passable by the PLAN §9 high-schooler using only what the suite teaches; anything demanding judgment the suite doesn't teach is a miscalibrated criterion, and §10 lists the places where that tension is real. The scale is defined once in §1 and used by every item.

## 1. The grading scale

Every item scores one of three grades. The grader writes one line of justification for every grade below Pass.

- **Pass** — the item's criteria are met as written. Competent first-project Green Belt work; thin is allowed, dishonest is not.
- **Needs work** — a shortfall a rework pass would fix, and which does **not** change what the phase concluded.
- **Fail** — the item's failure line is crossed, or an artifact the project's route required was never produced.

**Phase pass bar ("acceptable Green Belt work," PLAN §9):** every applicable item in the phase at Pass, **or** at Needs-work with a recorded justification and no invalidation of the phase conclusion.

**"Invalidate" means, concretely** — a Needs-work or Fail invalidates the phase conclusion when it makes the conclusion untrue, not merely thin:

- a **wrong number** — a stated value that differs from its computed source, or arithmetic that doesn't check;
- an **unverified cause treated as verified** — an assumption carried downstream wearing a verification badge;
- a **capability claim on an unstable process**, or any capability-language after a failed measurement check;
- a **proof claimed when its pre-declared threshold was not met**, or with a reported confound stripped from the claim.

A **thin-but-honest field is not invalidating**: an estimate labeled estimate, a small sample with the shortfall named, a lessons panel that admits a dead end. Honesty about a limit is Pass-side behavior (see §8); concealing the limit is the failure.

**Two bug taxonomies, per PLAN §9.** Usability failures — the student stalled, misread a screen, asked what to do — are logged against the **suite**. Validity failures — wrong method, wrong claim, wrong number — are graded against the **artifact**. This rubric grades the artifact axis only. When the suite's guidance *caused* a validity failure, log both: the item still fails (the claim is still wrong), and the root cause goes to the suite's bug log so the fix lands in the product, not on the student.

**Applicability.** The graded set is the artifacts the project's route actually required — the guided DMAIC flow plus the picker's routing decide which tools were in play. A tool the route required but the student skipped scores **Fail** on its item. A tool the route never called for (e.g. a spaghetti diagram on a project with no movement component, a 5S audit with no workplace-organization component) is **N/A — recorded with the reason, excluded from the phase roll-up**. N/A is a grader decision with a written reason, never a silent omission.

**Item frame.** Each item states: **Grades** (which artifacts/tools, by matrix T-nn ID) · **Pass means** (numbered, checkable criteria) · **Needs work when** (the most common shortfalls) · **Fail / invalidates when** (the line that voids the conclusion, where one exists) · **Pre-scored in code** (the deterministic subset — schema presence, regex/keyword heuristics, computed-value matches, gate states) vs **Judgment-only** (what only a grader or the advisor can weigh). The pre-score split is deliberately honest: over-claiming what code can check would corrupt the advisor's pre-score design (PLAN §5.1).

## 2. Define

#### R-DEF-01 — Project selection and routing

**Grades:** Project Picker output, including the PDCA quick-path routing (T-01). Exit: EXIT-01.

**Pass means:**
1. All five intake criteria are answered with project-specific content: scope narrow enough, measurable outcome, obtainable data, a named process owner who cares, plausible business impact.
2. The routing matches the answers — full DMAIC for a problem that warrants the rigor, the PDCA quick path for a small single-fix problem, and EXIT-01 (rescope or route out) when a criterion fails.
3. The outcome measure named at intake is the metric the charter and baseline actually carry — or a logged re-charter explains the change.

**Needs work when:** criteria are answered in generic phrases ("we'll get data somehow"); impact is asserted with no basis; the route is right but the reasoning is thin.

**Fail / invalidates when:** an EXIT-01 condition is present — no measurable outcome, no obtainable data, or no process owner — and full DMAIC is launched anyway without rescoping. Everything downstream is built on an unmeasurable or unowned problem.

**Pre-scored in code:** five intake fields non-empty (schema); recorded route consistent with the picker's rule tree (gate state); intake outcome measure matches the charter's primary metric ID. **Judgment-only:** whether the answers are true of the real situation; whether the impact claim is plausible.

#### R-DEF-02 — Problem statement quality

**Grades:** Project Charter problem statement (T-03).

**Pass means:**
1. States what, where, when, and magnitude — and the magnitude is a number with units and a time period ("Line 2 scrap averaged 6.2% in Q2, ~$40k"), not an adjective.
2. Contains no cause language and no solution language — nothing that presumes why it happens or prescribes a fix ("operators need retraining" is a solution, not a problem).
3. The stated magnitude is traceable to data the project holds (records, check sheet, export) — a labeled estimate is acceptable; a guess presented as measurement is not.
4. A reader outside the team could tell, from the statement alone, what hurts and by how much.

**Needs work when:** magnitude present but its source unstated; the "when" missing; hedges ("roughly," "seems") used without naming the underlying data gap.

**Fail / invalidates when:** a solution or cause is embedded in the statement, or the stated magnitude is contradicted by the project's own baseline data with no reconciliation (see R-MEA-11) — a wrong number at the root of the project.

**Pre-scored in code:** what/where/when/magnitude fields non-empty; number + unit + period pattern present in the magnitude; the T-03 solution/cause keyword heuristics (PLAN §4.1) clean; magnitude-vs-computed-baseline consistency flag once T-13 runs. **Judgment-only:** whether the statement describes the real problem; cause-smuggling too subtle for the keyword rules.

#### R-DEF-03 — Goal and metrics

**Grades:** Charter SMART goal, primary and consequential metrics (T-03; BoK I.A.2, II.C.2, II.C.4).

**Pass means:**
1. The goal is SMART in substance: a target value for a named metric with a date, sized against the problem's magnitude ("reduce line-2 scrap from 6.2% to 3% by Nov 30") — improvement-sized, not perfection-sized.
2. The primary metric is operationally defined (or points at the Data Collection Plan's definition) and is the same measure the baseline will compute.
3. At least one consequential (guardrail) metric is named — what must not get worse while the primary improves — and it is checked again at the proof.
4. The goal connects to the business driver named at intake, in the student's words.

**Needs work when:** target without a date; guardrail named but never revisited; the goal restates the problem instead of naming a target state.

**Fail / invalidates when:** the goal's metric is not the metric the baseline measures, with no logged re-charter — the project proves something it never promised. A goal that is itself a solution ("install the new labeler by Q3") also fails.

**Pre-scored in code:** metric/target/date fields present and typed; primary-metric ID identical to the baseline tool's metric ID; consequential-metric field non-empty and referenced by the T-20 proof; solution-language heuristic on the goal text. **Judgment-only:** target realism; driver linkage quality.

#### R-DEF-04 — Scope, team, and project risk

**Grades:** Charter scope in/out, team + process owner, and the key-risks block (T-03, incl. matrix correction A-4); Pareto as scoping evidence where used (T-14); Tier-B stakeholder deep-dive not graded (T-26). BoK II.A.5, II.C.3, II.C.7.

**Pass means:**
1. Scope-in and scope-out are both non-empty and specific — a named process segment, line, or product family, not "the warehouse."
2. Where the scope was narrowed from a bigger problem, the narrowing cites evidence (e.g. a Pareto showing the chosen category dominates), not preference.
3. The team is listed with a named process owner — the person who runs the process, not a placeholder or a title-only sponsor.
4. The risk block holds at least one real project risk with a likelihood/impact rating, a mitigation, and an owner. (Project risks — data access, resource loss, seasonality — not process failure modes; those are FMEA's job, T-16.)

**Needs work when:** scope-out is empty (everything is implicitly in); risks are generic ("lack of time") with no mitigation an owner could act on; the owner named is not the person who can accept the control plan later.

**Fail / invalidates when:** no process owner exists at all — nobody can own the control plan, so the project cannot finish honestly.

**Pre-scored in code:** in/out/team/owner fields non-empty; risk entries schema-complete (rating + mitigation + owner); owner-name blocklist ("TBD," "team," "management"); cross-artifact check that the charter owner appears on the control plan (T-22). **Judgment-only:** specificity of scope; whether the owner is real and appropriate; whether cited scoping evidence supports the cut.

#### R-DEF-05 — Business impact quantified (COPQ)

**Grades:** COPQ / Benefit Calculator worksheet and the charter's business-impact field (T-02, T-03). BoK II.E.1 (COPQ half; yield/indices grade under R-MEA-09).

**Pass means:**
1. COPQ is built from named cost buckets (scrap, rework, overtime, expediting, lost business...) each as quantity × rate computed by the tool — no hand-typed totals anywhere.
2. Inputs are project-real: taken from records where records exist, and labeled **estimate** where they don't.
3. The charter's business-impact field equals the calculator's output — one number, one source.
4. Any annualization or extrapolation states its basis ("Q2 actuals × 4").

**Needs work when:** a single lump-sum bucket does all the work; estimates and record-based figures are indistinguishable; buckets mix time periods without conversion.

**Fail / invalidates when:** the arithmetic is wrong, or the charter carries a different number than the calculator computed — a wrong number in the money story the sponsor will quote.

**Pre-scored in code:** computed total exists as a provenance object; charter field equals calculator output; every bucket has quantity and rate; estimate flags present; period-consistency check. **Judgment-only:** whether the buckets and rates are plausible for this operation.

#### R-DEF-06 — SIPOC

**Grades:** SIPOC form + rendered diagram (T-04). BoK II.A.2, II.A.4.

**Pass means:**
1. All five columns are populated, and the process column is 4–7 high-level steps whose start and end boundaries match the charter scope.
2. Outputs are paired to the customers who actually receive them, and inputs to their suppliers — not free-floating lists.
3. The CTQ-bearing output appears — the thing the customer cares about is on the map, so the CTQ tree (T-05) has something to hang from.

**Needs work when:** process steps drop to task-level detail (that belongs in the T-06 map); customers list only the internal next step when an end customer plainly exists.

**Fail / invalidates when:** the SIPOC's boundaries contradict the charter scope — the team has mapped a different process than the one chartered, and every downstream artifact inherits the mismatch.

**Pre-scored in code:** five columns non-empty; process step count in range (4–9); start/end boundary fields soft-matched against charter scope text; output referenced by the CTQ tree (link check). **Judgment-only:** right altitude; whether the supplier/input and output/customer pairings are correct.

#### R-DEF-07 — Voice of the customer → CTQ tree

**Grades:** VoC capture + CTQ tree (T-05). BoK II.B.1–II.B.3.

**Pass means:**
1. At least one real customer is identified by role (internal or external) — "everyone" is nobody.
2. Customer statements are captured close to verbatim, each with its source noted (interview, complaint log, direct observation).
3. The tree walks statement → need → measurable CTQ, and every CTQ carries a measure and a direction or target.
4. The tool's check — "is this what the *customer* critically needs, or what the process finds easy to measure?" — is answered per CTQ, in the student's words.
5. The primary CTQ is the charter's primary metric, or the mismatch is explained on the artifact.

**Needs work when:** statements arrive pre-digested into needs (no verbatims to audit); a CTQ is measurable but its link to the need is a stretch; one customer voice stands in for two that plainly differ.

**Fail / invalidates when:** a CTQ appears with no customer statement behind it and is treated downstream as "the customer requirement" — the project optimizes an invented voice.

**Pre-scored in code:** ≥1 customer with role field; ≥1 statement with source field; tree completeness (every CTQ resolves to a parent need and statement); measure + direction fields present; check answered (checklist state); CTQ ↔ charter-metric link or explanation field. **Judgment-only:** whether the CTQs honestly reflect the captured voice (see §10 — the suite teaches this with one check question; grade against that, not against market-research craft).

#### R-DEF-08 — Plan and tollgate discipline

**Grades:** Charter timeline field (T-03) + tollgate checklists at each phase exit (T-25). BoK II.C.5. Graded across the whole project — evidence accrues at every gate.

**Pass means:**
1. The charter timeline names phase-level milestones with dates, consistent with the goal date — a plan, not a wish.
2. The Define tollgate checklist is completed before Measure work begins — or the soft gate is overridden with a logged, non-boilerplate reason (PLAN §4.2 allows iteration; it requires honesty about it).
3. The same discipline holds at every later phase exit: checklist completed, or override logged with a reason.

**Needs work when:** dates are already blown with no revision on record; overrides become routine with copy-paste reasons.

**Fail / invalidates when:** — (no invalidation line of its own; tollgate-skipping does its damage through the phase items it lets through). Persistent gate evasion caps this item at Needs-work and belongs in the grader's notes.

**Pre-scored in code:** timeline fields present; tollgate checklist completion states; override log entries non-empty — this item is almost entirely gate-state readable. **Judgment-only:** date realism; whether override reasons are reasons.

## 3. Measure

#### R-MEA-01 — As-is process map

**Grades:** Swimlane process map (T-06). BoK I.B.2, II.A.2, III.A.

**Pass means:**
1. The map shows the **as-is** process — walked or observed, not the procedure as written or the improved state as hoped. Tell: it contains the inconvenient parts (workarounds, waits, informal handoffs).
2. Start and end match the SIPOC boundaries; lanes are the roles/functions that actually touch the work.
3. Decision points and rework loops that exist in reality appear on the map — a defect problem mapped with zero rework loops is suspect on its face.
4. Steps carry the data downstream tools reuse (times and/or defect points on the relevant steps) — one project data model, many views.

**Needs work when:** happy path only; altitude jumps (three giant boxes, then twelve micro-steps); lanes drawn by department when the handoffs that matter happen between roles.

**Fail / invalidates when:** the map documents the intended procedure rather than observed reality — Analyze would then target a fiction, and every cause found on the map is a cause in a document, not in the process.

**Pre-scored in code:** ≥2 lanes; boundary match to SIPOC; step-data presence (times/defect flags on at least some steps); advisory flag when a defect-metric project has no rework loop. **Judgment-only:** whether the map reflects the real, observed process — the one thing no schema can see.

#### R-MEA-02 — Value analysis and waste walk

**Grades:** VA/NVA/enabling tags + 8-wastes walk on the map (T-06). BoK I.B.2.

**Pass means:**
1. Every step is tagged value-add / non-value-add / enabling, with the value test applied honestly (customer would pay for it; it changes the thing; done right the first time).
2. The waste walk produces concrete observations tied to locations on the map ("operator waits ~4 min at step 6 for QC sign-off") — not a recited list of the 8 wastes.
3. The tags roll up to a number — NVA time or NVA step share — that the Improve phase can attack.

**Needs work when:** everything is tagged VA or enabling (the test wasn't really applied); wastes are named but attached to nothing.

**Fail / invalidates when:** — (no invalidation line; a weak waste walk thins Analyze but fakes no number).

**Pre-scored in code:** tag present on 100% of steps; waste entries linked to step IDs; NVA rollup computed by the tool. **Judgment-only:** tag honesty; whether observations are observations.

#### R-MEA-03 — Spaghetti diagram

**Grades:** Interactive spaghetti diagram (T-07). BoK I.B.1. **Applicability:** graded only when the problem has a movement/layout component; otherwise N/A with reason.

**Pass means:**
1. The floor plan is calibrated by a drawn known-length line, and that real length is stated.
2. Routes are traced per operator or trip type from an actual observation — trips counted, not imagined.
3. The computed metrics are read and used: distance per trip, trip count, and daily travel burden (distance × frequency) quoted where the burden matters.
4. The observation window is stated: when, how long, which shift.

**Needs work when:** one trip is traced and presented as typical; the calibration length is guessed; the heatmap/before-after features substitute for stating what was actually observed.

**Fail / invalidates when:** a fabricated frequency — a travel-burden number not grounded in observation — is used downstream as baseline evidence. That is a wrong number wearing a diagram.

**Pre-scored in code:** calibration state set with stated length; ≥1 route with trip count > 0; computed metrics present (provenance objects); observation-window fields non-empty. **Judgment-only:** whether the tracing reflects observed movement and the window is representative.

#### R-MEA-04 — Time study / work sampling

**Grades:** Guided time study / work sampling (T-09). Supports BoK III.D.3 (element-time spread). **Applicability:** graded when the route required timed observation; otherwise N/A with reason. *(ID inferred — see §10.)*

**Pass means:**
1. Work elements are defined **before** timing starts — an element list with start/stop triggers, not categories invented mid-study.
2. The tool's recommended cycle count is observed, or the shortfall is named on the artifact ("6 cycles; tool recommends 10 — treat spread as rough").
3. Element times are reported with their spread — a single observation is never presented as "the time."
4. Outliers are flagged and either explained or visibly retained — never silently deleted.

**Needs work when:** elements are re-cut mid-study without a restart note; single-digit cycles carry no caveat; the flagged outliers are ignored in the summary.

**Fail / invalidates when:** observations are deleted without a logged reason — data integrity broken; whatever the summary says is a wrong number by omission.

**Pre-scored in code:** element list timestamps precede first timing; cycle count vs the tool's recommendation; spread computed and present; outlier flags present; deletion requires a logged reason (schema). **Judgment-only:** element granularity sanity; quality of outlier explanations.

#### R-MEA-05 — Data collection plan

**Grades:** Data Collection Plan incl. operational definition, data-type identification, sample-size guidance (T-11). BoK III.D.1, III.D.2.

**Pass means:**
1. The operational definition passes the two-people test as written: unit, boundaries, the exact moment of measurement, and the instrument/gauge named — two people following it would record the same value.
2. The data type is identified correctly (continuous vs attribute/count) — this single field drives every downstream chart and test route.
3. Stratification factors (shift, machine, operator, day...) are chosen for suspected sources of difference and captured **as columns**, so later tools can split on them.
4. The sample-size guidance was consulted: planned n stated with the rule-of-thumb or calculator rationale attached.
5. Who collects, where, when, and how is stated — including a bias check (is this a convenience sample? says so if so).

**Needs work when:** the definition names the metric but not the measurement moment; factors are listed in the plan but never appear in the data; planned n is a bare number with no rationale.

**Fail / invalidates when:** the data type is wrong — continuous treated as attribute or the reverse — because every downstream route (chart family, test family, capability path) is then wrong by inheritance.

**Pre-scored in code:** all plan fields non-empty; declared data type consistent with the collected dataset's actual columns (type sniffing); planned-n and rationale fields present; stratification columns exist in the data. **Judgment-only:** whether the definition is truly unambiguous (the two-people test itself); whether the chosen factors are the sensible suspects.

#### R-MEA-06 — Data collection execution

**Grades:** Check Sheet / Tally output or imported dataset (T-08; Tier-B log sheets T-27 feed it). BoK III.D.2.

**Pass means:**
1. Data was collected per the plan: same operational definition, strata recorded on the rows, timestamps present.
2. Achieved n is stated against planned n — and a shortfall is named, not smoothed over.
3. The collection artifact **is** the dataset the baseline runs on — no re-typed intermediate copy between tally and analysis.
4. Basic data-quality checks are visibly done: missing values, impossible values, duplicates found and addressed with a note.

**Needs work when:** some rows lack the planned strata; achieved n is given without its period; quality-check findings are fixed without saying what was fixed.

**Fail / invalidates when:** the dataset was edited without a trail — values changed or rows dropped silently. Untraceable data can support no conclusion.

**Pre-scored in code:** timestamps present; achieved n computed vs plan with shortfall flag; missing/impossible/duplicate scans run and results stored; provenance hash links collection artifact → baseline input (no re-typing possible without breaking the hash). **Judgment-only:** whether collection circumstances match the plan (the convenience-sample smell no scan detects).

#### R-MEA-07 — Measurement system check

**Grades:** Narrow MSA — test/retest repeatability (continuous) or two-rater attribute agreement (pass/fail) (T-12). BoK III.E. Exits: EXIT-02, EXIT-03.

**Pass means:**
1. The check matching the data type was run **before** the baseline was trusted: test/retest for continuous data, two-rater agreement for judgment calls.
2. The verdict is obeyed: acceptable → proceed; marginal → proceed with the caveat carried into the narrative; **fail → stop, fix the measurement (EXIT-02), re-run the check** — and only then resume. Taking that stop is Pass-level work (§8).
3. If the measurement question exceeds the narrow check the suite ships — multi-operator variation, bias, linearity — the named exit is taken (EXIT-03: human quality engineer / v2 T-35), not improvised around.

**Needs work when:** the check ran on samples that don't span the working range; a marginal verdict is carried but narrated as a clean pass.

**Fail / invalidates when:** baseline or capability claims are made after a failed check with no fix — the suite blocks the capability-language automatically; pushing past it by override or by narrative is a first-order validity failure. All downstream numbers are unreliable, and this rubric treats them so.

**Pre-scored in code:** check-ran gate state precedes baseline trust; verdict recorded; downstream capability-language block consistent with verdict; re-run present after a failed first check. **Judgment-only:** whether the check's samples spanned the range; narrative honesty about a marginal result. (§10: grade against the narrow check the suite teaches — a reviewer instinct to demand full Gage R&R here is out of declared scope.)

#### R-MEA-08 — Stability before capability

**Grades:** Baseline tool's enforced order — spec limits + operational definition, then stability (I-MR, or p-chart on the attribute path), then capability (T-13). BoK III.F.1, III.F.2. Exit: EXIT-04.

**Pass means:**
1. Spec limits are entered before capability, with a **source**: customer requirement, standard, or a stated internal target — never reverse-engineered from the data to flatter the result.
2. The stability read is correct: signals identified, and the stable/not-stable call matches what the chart shows.
3. Not stable → EXIT-04 honored: "you don't have a baseline yet"; special causes investigated; **Pp/Ppk only, labeled performance-not-capability; no Cp/Cpk claim anywhere** — including in the student's own prose.
4. The data enters in true collection order — stability analysis on shuffled data is meaningless.

**Needs work when:** the spec-limit source is unstated; signals are noted but nobody investigated before moving on.

**Fail / invalidates when:** capability (Cp/Cpk) is claimed on an unstable process — the defining invalidator of this rubric — or spec limits were set from the data to make the process look capable. Both make the baseline a fiction.

**Pre-scored in code:** spec-limit fields + source field present; stability verdict computed; language-gate state (Cp/Cpk suppressed while unstable — tool-enforced, pre-score verifies no override slipped through prose); time-order flag on the dataset. **Judgment-only:** legitimacy of the spec-limit source; quality of the special-cause investigation.

#### R-MEA-09 — Capability, yield, and sigma reported honestly

**Grades:** Capability indices + sigma level (T-13), FPY/RTY/DPMO (T-10). BoK II.E.1, III.F.3, III.F.4; IASSC 2.4.3. Exit: EXIT-05.

**Pass means:**
1. The right family for the data: continuous → Cp/Cpk and/or Pp/Ppk with the within-vs-overall distinction stated in the student's own summary; attribute → FPY/RTY/DPMO with the p-chart baseline path.
2. Yield is computed from good/rework/scrap counts with **rework counted** — RTY, not the flattering final-yield number, is what the narrative quotes when rework exists.
3. Non-normal data → the percentile-method caveat (EXIT-05) stays attached in the student's narrative, not just on the auto-printed export.
4. Sigma level is reported with the 1.5σ shift convention named, as the tool prints it.
5. The baseline number produced here is the charter metric's number — same units, same definition.

**Needs work when:** Cp is quoted without Cpk (centering ignored) in the summary; RTY is computed but FPY is what the story tells; the caveat survives on the PDF but vanishes from the prose.

**Fail / invalidates when:** any reported number differs from its computed source — an index recomputed outside the tool, a transcription "rounded" into a better story. (Capability claimed past a failed gate already invalidates under R-MEA-07/08; this item catches the reporting side.)

**Pre-scored in code:** family route matches declared data type; indices/yields exist as provenance objects; narrative-vs-computed number-match scan; caveat string present in export; shift-convention toggle state recorded; baseline-metric ID equals charter-metric ID. **Judgment-only:** which number the story leads with — honesty of emphasis.

#### R-MEA-10 — Descriptive and graphical reads

**Grades:** Pareto / histogram / run chart (+ box/scatter per matrix correction A-2) (T-14); descriptive statistics displayed with them (T-13). BoK III.D.3, III.D.4.

**Pass means:**
1. The charts the data shape calls for exist: histogram for shape, run chart for time behavior, Pareto where categorical defect data exists, box/scatter where the tool offers them.
2. Each chart is read correctly **in the student's own words** — the vital few named from the Pareto (or its absence admitted when the bars are flat), shape and spread described from the histogram, drift/shift/runs noted from the run chart, consistent with the tool's verdict headline.
3. Center and spread are quoted as the computed mean/median and SD/IQR — never re-derived by hand.

**Needs work when:** charts exist but the narrative never touches them; a flat Pareto is narrated as if a vital few existed.

**Fail / invalidates when:** — (a chart read backwards fails the conclusion it feeds — usually R-MEA-08 or R-MEA-11 — rather than this item alone).

**Pre-scored in code:** chart artifacts exist per data shape; verdict headlines generated; narrative-number match against computed statistics. **Judgment-only:** the correctness of the student's own reads.

#### R-MEA-11 — Baseline statement and charter reconciliation

**Grades:** The Measure-exit baseline statement (T-13 outputs + charter T-03, tollgate T-25). *(ID inferred — see §10.)*

**Pass means:**
1. One baseline sentence exists and is complete: metric, value, period, n, stability status, and the capability-**or**-performance label — every element matching computed results.
2. It is reconciled with the charter's claimed magnitude: confirmed, or the charter revised by logged edit ("charter said 6.2%; measured 9.1%; charter updated") — never both numbers left standing in conflict.
3. The goal is re-checked against the measured baseline and restated in its terms if needed.

**Needs work when:** the baseline sentence lacks period or n; the reconciliation happened but the goal went stale.

**Fail / invalidates when:** charter magnitude and measured baseline contradict each other with no reconciliation — the project now carries two versions of the truth, and one of them is a wrong number.

**Pre-scored in code:** baseline-summary fields present and value-matched to provenance objects; charter-vs-baseline delta flag raised and cleared; charter version log shows a revision when the delta is material. **Judgment-only:** whether the reconciliation reasoning is sound.

## 4. Analyze

#### R-ANA-01 — Cause exploration (fishbone + 5 Whys)

**Grades:** Fishbone (6M) + 5 Whys chains (T-15). BoK IV.C.2.

**Pass means:**
1. The fishbone's effect is the baselined problem — the measured gap, not a convenient symptom of it.
2. At least four of the 6M categories carry project-specific candidate causes; causes are phrased as conditions or mechanisms ("labels applied before ink dries"), not absent solutions ("no barcode scanner" is a solution wearing a cause costume).
3. 5 Whys runs on the leading candidates: each chain at least three levels deep or ending at a named actionable cause, with each "why" actually explaining the level above it.
4. Breadth before depth: more than one branch is explored — the diagram is not a single pre-decided path with decoration.

**Needs work when:** categories are filled with textbook generics ("training," "communication"); why-chains jump tracks ("why late? → because morale").

**Fail / invalidates when:** — (exploration quality bites through R-ANA-02 and R-ANA-06, where a bad cause becomes a claimed one).

**Pre-scored in code:** effect field matches the baseline problem ID; category-coverage count; cause count; absent-solution keyword heuristic ("no X," "lack of X"); why-chain depth from schema. **Judgment-only:** logical connection of chains; project-specificity of causes.

#### R-ANA-02 — Evidence discipline on causes

**Grades:** Evidence fields + verified/unproven status on every cause (T-15); verification tests where used (T-17, T-14 stratified views). BoK IV.C.2. This is the item the Improve phase stands on.

**Pass means:**
1. Every cause carried forward as **verified** has a non-empty evidence field citing data or direct observation — a stratified Pareto, a hypothesis-test result, a check-sheet split, a documented gemba observation. "Team consensus" alone verifies nothing.
2. Causes claiming a measured difference cite the test or chart that shows it (T-17 output or a stratified view) — not an eyeballed pair of averages.
3. The evidence pertains to *that* cause — the cited artifact addresses the cause's mechanism, not just the general problem.
4. Unverified candidates stay visibly flagged unproven and are not used by Improve.

**Needs work when:** evidence fields restate the cause in different words; one strong verification is used to wave through neighboring causes; observation evidence has no date/place.

**Fail / invalidates when:** an unverified cause is treated as verified — one of this rubric's named invalidators. Improve then builds on an assumption wearing a verification badge, and the phase conclusion is void.

**Pre-scored in code:** evidence field non-empty for every status=verified cause (the matrix's own example check); status flags present; solution matrix references only status=verified causes (link check); evidence cites a resolvable artifact ID. **Judgment-only:** pertinence and sufficiency of the evidence — see §10: the grader holds to "data or observation a reasonable person would accept as showing the cause operates," not statistical proof for every cause.

#### R-ANA-03 — Process FMEA

**Grades:** Process FMEA worksheet (T-16). BoK I.C.2.

**Pass means:**
1. Failure modes are specific failures of specific process steps (drawn from the T-06 map), each with its effect and cause — "process fails" is not a mode.
2. Severity/occurrence/detection are rated against the 1–10 anchor scales — spot-checked, a rating matches its anchor's wording, not gut feel.
3. The table is worked severity-first, then RPN, and the student's action list reflects the stated RPN limitation: equal RPNs are not equal risks, and high severity is never ignorable.
4. Top items carry actions with owners.

**Needs work when:** detection ratings are all the same middle number (anchor not consulted); actions exist without owners; modes sit at whole-process altitude.

**Fail / invalidates when:** a severity-9/10 mode is visible and unaddressed while low-severity high-RPN items get the attention — the exact misuse the tool warns about, and the FMEA's protective purpose is voided. (Does not by itself invalidate the Analyze conclusion; it fails this item.)

**Pre-scored in code:** mode/effect/cause/S/O/D/action schema completeness; ratings in 1–10; severity-first sort tool-enforced; high-severity-without-action flag; action-owner fields. **Judgment-only:** mode specificity; anchor consistency spot-check.

#### R-ANA-04 — Right test, right route

**Grades:** Hypothesis-test selector routing and its printed decision path (T-17, incl. matrix correction A-1 one-sample routes). BoK IV.B.1, IV.B.2; IASSC 3.4.1, 3.5.2, 3.5.6, 3.5.7. Exits: EXIT-06..14.

**Pass means:**
1. The comparison question is stated first, in plain words — what vs what, paired or independent, continuous or count, against-a-target or between-groups — and the selector's routed test matches that structure. (The tool routes by rule — Welch default, nonparametric fallbacks — so the student's job is answering the routing questions truthfully.)
2. The printed decision path is retained with the artifact, and the student's narrative doesn't contradict the route it shows.
3. When the data trips a floor or an unsupported case, the named exit is taken: small n (EXIT-06), sparse cells (EXIT-07), repeated measures (EXIT-08), autocorrelation (EXIT-09), multiple simultaneous comparisons (EXIT-12), ANOVA-significant pairwise (EXIT-13), non-normal 3+ groups (EXIT-14). **Recognizing the exit is a Pass** (§8).
4. One pre-declared primary comparison — no shotgun p-values (EXIT-12's discipline, visible in the artifact).

**Needs work when:** the question is written after the result (test-shopping smell); several tests were run and only the significant one is narrated.

**Fail / invalidates when:** a route is forced past a triggered exit — an n-floor overridden, a sparse chi-square computed elsewhere and pasted in — the phase conclusion then rests on a test the method itself says is untrustworthy.

**Pre-scored in code:** routing inputs recorded; route equals rule-tree output (true by construction — verified for tampering); exit gate states; n and expected-cell floors; count of tests run vs declared primary. **Judgment-only:** whether the stated question is the real question.

#### R-ANA-05 — Interpretation discipline

**Grades:** The student's conclusions drawn from T-17 output (which always carries effect size + CI + plain English); scatter reads (T-14, correction A-2). BoK IV.A.2, IV.B.1. Exit: EXIT-15.

**Pass means:**
1. Conclusions quote effect size and confidence interval, not just p — and state practical significance against the goal ("2.1 min faster, CI 0.8–3.4; the goal needs 3.0 — real but not sufficient alone").
2. Non-significant is never narrated as "no difference" — the honest form is "no difference shown at this sample size."
3. Claims stay inside what was tested: a difference between shifts is not proof of the mechanism the student suspects behind the shifts.
4. Association language is disciplined: correlation ≠ causation observed; scatter-plot reads stay visual and qualitative in v1, with quantified correlation/regression deferred by name (EXIT-15 → T-30 at v1.1).

**Needs work when:** p-value theater ("highly significant!" over a trivial effect); the CI is printed by the tool but never enters the student's reasoning.

**Fail / invalidates when:** the practical conclusion contradicts the computed result — claiming a cause difference the test didn't show, or dismissing one it did — a wrong claim over a right number.

**Pre-scored in code:** effect size/CI present (tool-emitted, always); narrative-number match; "no difference" phrase heuristic on non-significant results (advisory flag); EXIT-15 state on any correlation question. **Judgment-only:** the quality of practical-vs-statistical reasoning — this item is mostly judgment, and is where the advisor earns its keep.

#### R-ANA-06 — Analyze conclusion: verified causes ranked against the gap

**Grades:** The Analyze-exit ranked cause list — T-15 verified statuses ordered for the Improve loop (feeds T-18; tollgate T-25). *(ID inferred — see §10.)*

**Pass means:**
1. A closing list of verified causes exists, each with its evidence pointer, **ranked by likely impact on the baseline gap** with the ranking rationale stated (Pareto share, effect size, frequency — whatever the evidence supports). This ranking is what the Improve loop consumes first.
2. The list is honest about coverage: it plausibly accounts for the gap the goal must close, **or the shortfall is named** ("verified causes explain perhaps half; remaining drivers unknown").
3. Nothing unverified rides in the ranked list.

**Needs work when:** the ranking has no stated rationale; a single verified cause is carried as if it explains everything, without saying so.

**Fail / invalidates when:** the ranked list contains causes whose status is not verified — the same invalidator as R-ANA-02, caught here at the phase gate.

**Pre-scored in code:** ranked list exists; every entry status=verified (link check); rationale fields non-empty; evidence pointers resolve. **Judgment-only:** plausibility of the impact ranking and of the gap accounting.

## 5. Improve

#### R-IMP-01 — Solution selection

**Grades:** Solution Selection Matrix — impact/effort + weighted criteria, ranked fix list (T-18). BoK V.B.

**Pass means:**
1. At least two candidate solutions were considered for the top-ranked verified cause — the matrix is a comparison, not a rubber stamp for a pre-decided fix.
2. Every solution links to a verified cause; the tool flags unlinked solutions, and none survive to the ranked list unresolved.
3. Criteria and weights were set before scoring (impact/effort at minimum), and the scoring arithmetic is the tool's.
4. The output is a ranked fix list, and the #1 pick is the top scorer — or the deviation carries a logged reason.

**Needs work when:** effort/impact ratings have no stated basis; the weights are unusual and unexplained (the shape of a post-hoc rescue); remedy-advisor suggestions were pasted in without the user's own pruning.

**Fail / invalidates when:** a solution unlinked to any verified cause is piloted anyway — the solution-first project this whole flow exists to prevent, and the Improve logic is void.

**Pre-scored in code:** solution count ≥2; cause-link on every solution with status=verified; weight/score fields with tool-computed ranking; weight timestamps precede score timestamps; pick equals top rank or override-with-reason logged. **Judgment-only:** honesty of the scoring; sanity of the criteria.

#### R-IMP-02 — Pilot design

**Grades:** Pilot Plan — the small-study designer (T-19). BoK V.B. Exit: EXIT-10. This item enforces the product's method: **one change at a time** (PLAN §4.1).

**Pass means:**
1. **One change per pilot**, stated in one sentence. Multiple candidate fixes become sequential pilots through the loop — or, when a genuinely combined question exists, the named exit (EXIT-10: advisor / v1.1 Experiment Planner / human expert), never a bundle claimed as attributable.
2. The comparison is defined before running: baseline period or parallel comparison, stated, with who/what is included and how selected.
3. Success threshold **and** analysis plan are declared before data collection — timestamps prove it.
4. The falsification line is filled in and substantive: "what would prove this DIDN'T work."
5. The confounder checklist (staffing, season, demand, measurement changed?) is answered up front, to be re-answered at proof.

**Needs work when:** the pilot is too small or short to assess the declared threshold and doesn't say so; pilot units are chosen by convenience without stating it.

**Fail / invalidates when:** the threshold is set or changed after seeing results — pre-declaration is the entire point; or more than one change runs as one pilot and the result is claimed as attributable to a specific fix.

**Pre-scored in code:** single-change field (plus a flag when the solution matrix maps >1 solution into one pilot); threshold/analysis-plan timestamps precede first pilot-data timestamps; falsification field non-empty; checklist answered; comparison-definition fields present. **Judgment-only:** adequacy of the comparison design; scope sanity; whether the falsification line has teeth. (§10: unit-selection bias is graded at "stated honestly," not at sampling-theory rigor.)

#### R-IMP-03 — Before/after proof

**Grades:** Before/After Proof — the stats-engine re-run on pilot data (T-20, proof half). *(ID inferred — see §10.)*

**Pass means:**
1. The proof runs the **same metric, same operational definition, same measurement system** as the baseline — a changed yardstick proves nothing.
2. The engine re-ran on the pilot data: side-by-side stability, the appropriate Tier-A test with effect size + CI, and the pre-declared threshold checked — with the verdict stated **as declared**: met, or not met.
3. The confounder checklist is re-answered and its answers print on the result; any reported confound tempers the claim in the student's own words ("improvement shown, but staffing changed — this proof is weakened").
4. The after-period has enough run to say something — the tool's floors honored, EXIT-06 taken if not.

**Needs work when:** the after-window looks cherry-picked (best week) and isn't justified; a confounder answered "no" that the project record contradicts.

**Fail / invalidates when:** improvement is claimed with the threshold unmet or the test unsupportive; a reported confound is stripped from the claim; or the metric/definition switched between before and after — a wrong number by construction. All three are named invalidators (§1).

**Pre-scored in code:** metric/definition/measurement-system IDs match before↔after; threshold-met computed against the declared value; confounder answers present and printed in the export; test result + effect size as provenance objects. **Judgment-only:** cherry-picking detection; plausibility of confounder answers.

#### R-IMP-04 — Remaining-gap check and the improvement loop

**Grades:** Remaining-gap check + loop routing (T-20, gap half). BoK IV.C.1 — gap analysis operationalized. The loop discipline (PLAN §4.1): rank → fix one → prove → check gap → next.

**Pass means:**
1. The gap arithmetic is done from computed numbers: original gap, amount recovered by this fix, remainder — "this fix got you 80%; here's what's left."
2. An explicit routing decision is recorded: goal met → Control; gap remains and verified causes remain → next-ranked cause, one change at a time; causes exhausted with gap remaining → honest statement and route (back to Analyze, or exit to a human expert).
3. Every loop iteration repeats the R-IMP-02/R-IMP-03 discipline — graded on the repeat artifacts when iterations exist.

**Needs work when:** the remainder is computed but no routing decision follows; a second pilot starts while the first is unproven (loop discipline slipping).

**Fail / invalidates when:** the narrative declares the goal met while the computed remainder says otherwise — a wrong number at the loop's decision point.

**Pre-scored in code:** gap fields computed (provenance); routing decision recorded; iteration linkage (pilot N+1 references the next-ranked verified cause); concurrent-unproven-pilot flag. **Judgment-only:** the routing reasoning.

#### R-IMP-05 — Improve conclusion: implementation and goal reconciliation

**Grades:** The Improve-exit state — implementation beyond pilot, reconciled against the charter goal (T-20 outputs + charter T-03; feeds T-22/T-24; tollgate T-25). *(ID inferred — see §10.)*

**Pass means:**
1. The proven change is implemented beyond the pilot scope, with what-changed documented — the material the SOP (T-24) and control plan (T-22) will carry.
2. Improve closes with numbers against the charter goal: met / partially met with the remainder stated / not met with the honest route taken. Partial success stated as partial is Pass-side; see §8.
3. What Control will monitor is the implemented state — pilot-only improvements are not claimed as implemented.

**Needs work when:** implementation is asserted with no artifact trail; the guardrail (consequential) metric from R-DEF-03 is never re-checked.

**Fail / invalidates when:** the goal is claimed met against the computed remainder — same line as R-IMP-04, enforced at the phase gate.

**Pre-scored in code:** implementation fields/dates present; goal-vs-result delta computed and consistent with the claimed status; links to SOP and control plan resolve; guardrail-metric recheck present. **Judgment-only:** whether implementation is real beyond the record.

## 6. Control

#### R-CTL-01 — Control chart selection and construction

**Grades:** Control charts — I-MR (continuous) or p (attribute) via the printed selector (T-21). BoK VI.A.1, VI.A.3.

**Pass means:**
1. The chart family matches the data type through the printed selector — I-MR for continuous, p for attribute with the denominator handled per subgroup — and the chart monitors the primary CTQ/metric, not a convenient proxy (or the proxy is explained).
2. Limits are computed by the tool from the post-improvement baseline period and then **frozen** — recalculated only on a deliberate, logged decision, never silently refit to recent data.
3. The tool's minimum-points advisory is honored before the limits are treated as meaningful.
4. Control limits and spec limits are kept distinct in the student's own language — "out of control" and "out of spec" are different sentences.

**Needs work when:** limits are recalculated on every update (rubber limits); the monitored metric drifted from the CTQ without a stated link.

**Fail / invalidates when:** spec limits are used as control limits (every signal read is then wrong), or limits are quietly recalculated in a way that erases a shift the chart had caught.

**Pre-scored in code:** selector route recorded and matches data type; limit-freeze state + recalculation log; point count vs advisory floor; monitored-metric ID link to CTQ. **Judgment-only:** proxy appropriateness; spec-vs-control conflation in the narrative.

#### R-CTL-02 — Signal interpretation and response

**Grades:** Western Electric rule signals (conservative default, rules 1–4) and what the student did about them (T-21). BoK VI.A.1.

**Pass means:**
1. Every fired signal gets a recorded read in the student's words — special cause vs common cause — consistent with the chart's own explanation of the rule that fired.
2. Special-cause signals trigger the response path (OCAP, R-CTL-04): investigation/containment recorded against the signal.
3. No tampering: no adjustments made on common-cause variation (the classic over-reaction), and no repeated signal left unacknowledged.

**Needs work when:** signals are acknowledged but the investigation notes are empty; every signal is reflexively blamed on the same cause ("operator error") without evidence.

**Fail / invalidates when:** sustained special-cause signals are ignored while the wrap-up declares the process "in control" — a false stability claim at the exact point the project exists to protect.

**Pre-scored in code:** signal events + acknowledgment states; OCAP-invocation records linked to signals; adjustment log cross-checked against signal states (tampering flag); unacknowledged-repeat-signal flag. **Judgment-only:** correctness of each read; quality of the response. (§10: within a short eval window signals may simply never fire — then this item grades the recorded discipline and mechanics, and thin evidence is not a Fail.)

#### R-CTL-03 — Control plan core

**Grades:** Control Plan — what's monitored, how, how often, by whom (T-22). BoK VI.B.1.

**Pass means:**
1. Every monitored item names: the characteristic, how it's measured (linked to its operational definition), where, how often, and **who** — a named person who has accepted the role, not "the team." The tool requires the owner; the grader checks the person is real (appears on the charter team or a handoff note).
2. The monitoring frequency has a reason — tied to how fast the process could drift or how much volume flows — not a default left standing.
3. The plan covers what Improve changed **plus** the primary CTQ — the fix is monitored, not just the outcome.

**Needs work when:** an owner is named with no evidence of handoff; frequency is defaulted with no rationale; the guardrail metric is missing from the plan.

**Fail / invalidates when:** no named owner — the tool flags an ownerless plan as theater, and this rubric agrees: an unowned control plan is no control plan, and the project's sustainment claim is void.

**Pre-scored in code:** owner field non-empty and person-shaped (blocklist: "TBD," "team," role-only strings); frequency + method fields present; links to operational definition and to the changed process steps resolve; CTQ coverage check. **Judgment-only:** owner realness; frequency reasoning; coverage sufficiency.

#### R-CTL-04 — Sustainment: response plan, training, check-ins

**Grades:** OCAP (response plan), training & handoff block (matrix correction A-5), scheduled check-ins (T-22); the SOP as the training artifact (T-24). BoK VI.B.1, VI.B.3.

**Pass means:**
1. **OCAP:** for each monitored item, the exact out-of-control action path — who acts first, what containment looks like, when and to whom it escalates — specific enough to follow at 2 a.m. without the author.
2. **Training & handoff:** who gets trained, on what (the T-24 SOP, which exists and is referenced), by whom, by when, verified how (sign-off or observed demonstration) — a fix nobody is trained on dies with the project.
3. **Check-ins:** the scheduled check-ins are accepted, and every check-in due within the grading window is answered with numbers against the limits.

**Needs work when:** the OCAP says "investigate and fix"; training is listed without a verification method; check-ins are scheduled but the due ones sit unanswered.

**Fail / invalidates when:** the primary CTQ has no response path at all — a signal would fire into silence, and the claim "the improvement is protected" is void.

**Pre-scored in code:** OCAP fields per monitored item; training block schema-complete (who/what/when/verified-how); SOP link resolves; check-in schedule exists with due-vs-answered states. **Judgment-only:** followability of the OCAP; whether the verification method would actually verify.

#### R-CTL-05 — 5S audit

**Grades:** Scored 5S audit with photos and trend (T-23). BoK V.C.1. **Applicability:** graded when the project has a workplace-organization component; otherwise N/A with reason.

**Pass means:**
1. A baseline audit is scored against the checklist, with photos wherever physical state carries the score.
2. Scores track the checklist's anchors — spot-checked against the photos, a 4 looks like the checklist's 4, and the scores are not uniform by reflex.
3. Recurrence is real: a schedule exists (or the trend already has ≥2 points), and the lowest-scoring category carries an action.

**Needs work when:** one audit, no recurrence; all categories scored identical; actions listed with no owner or date.

**Fail / invalidates when:** — (5S theater degrades sustainment but fakes no project number; it caps at Needs-work and belongs in the grader's notes).

**Pre-scored in code:** audit completeness; scores in range with uniformity flag; photo attachments present; schedule or ≥2 trend points; action recorded on the minimum category. **Judgment-only:** score honesty against the photos.

#### R-CTL-06 — Standard work / SOP

**Grades:** Standard Work / SOP — the improved method written down (T-24). BoK V.C.1, and the training artifact for VI.B.3. *(ID inferred — see §10.)*

**Pass means:**
1. The **improved** method is written as steps a qualified-but-new person could follow: each step an action with its standard ("what right looks like"), and the points that changed from the old method highlighted.
2. Version, owner, and date fields are set; if an older instruction existed, the SOP names what it supersedes.
3. The SOP matches the process map's improved state and is the document the training block (R-CTL-04) points at — one method, one source.

**Needs work when:** the SOP describes the old process with a patch note; steps are written as policy ("ensure quality") instead of actions; the changed steps aren't marked.

**Fail / invalidates when:** the SOP contradicts the implemented change — the method being trained is not the method that was proven, and the sustainment story is void.

**Pre-scored in code:** step schema (action + standard fields); version/owner/date present; supersedes field when a prior doc exists; links from training block and control plan resolve; changed-step markers present. **Judgment-only:** followability — could the grader do the job from it — and consistency with what was actually implemented.

## 7. Wrap

#### R-WRAP-01 — A3 final report

**Grades:** A3 guided narrative + the project record it rolls up (T-25). BoK II.C.6.

**Pass means:**
1. The A3 reads as one argument — problem → baseline → causes → countermeasures → proof → control — with every panel consistent with its source artifact: numbers identical, claims not upgraded in transit (the proof panel keeps the confound the T-20 result printed; the baseline panel keeps the performance-not-capability label).
2. It works as narrative for a sponsor who saw none of the working artifacts — panels are prose telling the story, not field dumps.
3. Every quantitative claim on the A3 traces to a provenance object carried in the export.

**Needs work when:** panels are concatenated fields; the story skips the failed first pilot that the record shows; jargon appears the sponsor can't parse.

**Fail / invalidates when:** any A3 number differs from its computed source, or a claim is upgraded in transit — "proved" where the proof said "weakened," "capable" where the baseline said "performance." The deliverable is where honesty pays or dies.

**Pre-scored in code:** panel-vs-source number-match scan; provenance completeness on the export; caveat/confound strings carried into panel text (presence check). **Judgment-only:** narrative quality; sponsor-readability; upgrade-in-transit phrasings the string checks miss.

#### R-WRAP-02 — Realized benefits, honestly stated

**Grades:** COPQ re-run at Wrap + realized-benefits panel (T-02, T-25; drawing on T-20/T-13 numbers). *(ID inferred — see §10.)*

**Pass means:**
1. The COPQ is re-run with post-improvement actuals over a **stated window**; realized-to-date is separated from annualized projection, each labeled as what it is. (A student project may have weeks of after-data, not quarters — realized-to-date with the window named is the passing form.)
2. The benefit arithmetic ties to the measured improvement — the delta the proof showed — not to the goal, and not to the original COPQ hope.
3. Costs of the fix are netted, or at least named beside the benefit.

**Needs work when:** a projection is presented without its basis; soft benefits ride inside the dollar figure unlabeled.

**Fail / invalidates when:** benefits are claimed from the original COPQ as if realized — claiming the whole gap when the proof recovered 60% of it. A wrong number in the sentence leadership will repeat.

**Pre-scored in code:** wrap-COPQ present with window fields; realized vs projected labels; benefit ↔ proof-delta arithmetic consistency; fix-cost fields present. **Judgment-only:** netting completeness; plausibility of the projection basis.

#### R-WRAP-03 — Closure and lessons

**Grades:** Closure + lessons panel, open-item handoff, project record (T-25). BoK II.C.8.

**Pass means:**
1. Objectives-vs-charter reconciliation in numbers — goal, achieved, remainder — consistent with the Improve conclusion (R-IMP-05).
2. Lessons learned with substance: at least two, including at least one thing that went wrong or a dead end. A lessons panel containing only wins is not lessons — and this suite's brief is documenting the failures too.
3. Open items are handed off with owners: the remaining gap, pending check-ins, candidate causes left unverified on the table.
4. The project record is complete and versioned — the folder holds every artifact the A3 cites, loadable.

**Needs work when:** lessons are generic ("communicate more"); open items have no owners; the record is missing an artifact the A3 references.

**Fail / invalidates when:** — (closure thinness fakes no result; contradictions with the record grade under R-WRAP-01/02).

**Pre-scored in code:** reconciliation fields computed and consistent with R-IMP-05 status; lessons count ≥2 non-empty; open-item owner fields; every A3-cited artifact ID resolves in the project folder. **Judgment-only:** substance of the lessons.

## 8. Honesty-exit grading

The suite's exit registry (matrix §4, EXIT-01..15) names every case the tools detect but decline to compute — gated by method limits, never by belt level. The grading rule, stated once for every grader and both AI consumers:

**Recognizing and taking a named exit is PASS-level Green Belt behavior — never a deduction.** "This needs an experienced human" is a first-class output (PLAN §1). A student who hits a failed measurement check and stops to fix it (EXIT-02), who reports Pp/Ppk-performance-only on an unstable process (EXIT-04), who declines an underpowered test and goes to collect more data (EXIT-06), or who names a question as Kruskal-Wallis territory the suite doesn't carry (EXIT-14) has done **better** Green Belt work than one who produced a number there. One PLAN §9 eval scenario deliberately requires an exit; on that scenario the exit **is** the pass, and graders must not mark the analysis "incomplete" for ending at the honest boundary.

Three conditions make an exit a Pass rather than an abandonment:

1. **Named** — the artifact shows the exit language: which limit was hit (EXIT-nn), why the standard result would mislead.
2. **Routed** — the registry's route is taken or recorded: rescope (EXIT-01), fix-and-re-run (EXIT-02, EXIT-04), collect more (EXIT-06, EXIT-07), human expert / scheduled release (EXIT-03, EXIT-08..15).
3. **Honored downstream** — no later artifact quietly claims what the exit declined to compute.

**The failure is pushing past.** The invalidating push-pasts, by ID: capability-language after a failed measurement check (EXIT-02 ignored → R-MEA-07 Fail); a Cp/Cpk claim on an unstable process (EXIT-04 ignored → R-MEA-08 Fail); an underpowered or sparse test presented as a result (EXIT-06/EXIT-07 ignored → R-ANA-04 Fail); a multi-change pilot claimed as attributable (EXIT-10 ignored → R-IMP-02 Fail); shotgun p-values with the winner narrated (EXIT-12 ignored → R-ANA-04 Fail). A silent stall at a limit — no name, no route — is not an exit; it grades as the missing artifact it leaves behind.

**Pre-scored in code:** exit-state records (which EXIT fired, acknowledged or overridden) are gate states — fully deterministic, and the first thing the advisor's pre-score reports. **Judgment-only:** whether the routing reasoning holds, and whether downstream prose honored the exit.

## 9. Phase roll-up — the grader's scoresheet

One line per item. Grade ∈ {Pass, Needs work, Fail, N/A + reason}; one written line of justification for anything below Pass. Phase verdict = "acceptable Green Belt work" per §1.

| ID | Item | Grades (tools) | Grade | Notes |
|---|---|---|---|---|
| R-DEF-01 | Project selection and routing | T-01 | | |
| R-DEF-02 | Problem statement quality | T-03 | | |
| R-DEF-03 | Goal and metrics | T-03 | | |
| R-DEF-04 | Scope, team, and project risk | T-03, T-14, T-16 | | |
| R-DEF-05 | Business impact quantified (COPQ) | T-02, T-03 | | |
| R-DEF-06 | SIPOC | T-04 | | |
| R-DEF-07 | VoC → CTQ tree | T-05 | | |
| R-DEF-08 | Plan and tollgate discipline | T-03, T-25 | | |
| **Define verdict** | | | | |
| R-MEA-01 | As-is process map | T-06 | | |
| R-MEA-02 | Value analysis and waste walk | T-06 | | |
| R-MEA-03 | Spaghetti diagram | T-07 | | |
| R-MEA-04 | Time study / work sampling | T-09 | | |
| R-MEA-05 | Data collection plan | T-11 | | |
| R-MEA-06 | Data collection execution | T-08, T-27 | | |
| R-MEA-07 | Measurement system check | T-12 | | |
| R-MEA-08 | Stability before capability | T-13 | | |
| R-MEA-09 | Capability, yield, sigma honest | T-13, T-10 | | |
| R-MEA-10 | Descriptive and graphical reads | T-14, T-13 | | |
| R-MEA-11 | Baseline statement + reconciliation | T-13, T-03 | | |
| **Measure verdict** | | | | |
| R-ANA-01 | Cause exploration | T-15 | | |
| R-ANA-02 | Evidence discipline on causes | T-15, T-17, T-14 | | |
| R-ANA-03 | Process FMEA | T-16 | | |
| R-ANA-04 | Right test, right route | T-17 | | |
| R-ANA-05 | Interpretation discipline | T-17, T-14 | | |
| R-ANA-06 | Verified causes ranked vs gap | T-15 → T-18 | | |
| **Analyze verdict** | | | | |
| R-IMP-01 | Solution selection | T-18 | | |
| R-IMP-02 | Pilot design | T-19 | | |
| R-IMP-03 | Before/after proof | T-20 | | |
| R-IMP-04 | Remaining-gap check + loop | T-20 | | |
| R-IMP-05 | Implementation + goal reconciliation | T-20, T-03 | | |
| **Improve verdict** | | | | |
| R-CTL-01 | Chart selection and construction | T-21 | | |
| R-CTL-02 | Signal interpretation and response | T-21 | | |
| R-CTL-03 | Control plan core | T-22 | | |
| R-CTL-04 | Response plan, training, check-ins | T-22, T-24 | | |
| R-CTL-05 | 5S audit | T-23 | | |
| R-CTL-06 | Standard work / SOP | T-24 | | |
| **Control verdict** | | | | |
| R-WRAP-01 | A3 final report | T-25 | | |
| R-WRAP-02 | Realized benefits, honestly stated | T-02, T-25 | | |
| R-WRAP-03 | Closure and lessons | T-25 | | |
| **Wrap verdict** | | | | |

**Count check:** 8 + 11 + 6 + 5 + 6 + 3 = **39 items** — exactly the matrix's proposed set; R-ORG deliberately empty (project work, not exam recall).

**Pre-score coverage, for the PLAN §5.1 wiring** (counted over the 143 numbered pass-criteria above): **61** criteria are fully decidable in code (schema presence, ID/number matches, timestamps, gate states), **71** carry a deterministic component (presence/consistency checked in code, quality judged by grader/advisor), **11** are pure judgment. So the deterministic pre-score can *decide* roughly four in ten criteria and *pre-check* another five in ten — the advisor and the human grader are structurally necessary for the rest. Over-claiming this split would corrupt the pre-score design; these counts are the honest ones.

## 10. Open items for the independent Belt reviewer

Flagged per the calibration rule (§1): where "high-schooler passable" and "Green Belt grade" pull apart, the tension is named here rather than silently resolved. The reviewer rules on each.

1. **Seven IDs are defined by inference.** The matrix proposes 39 IDs but its rows cite only 32; R-MEA-04, R-MEA-11, R-ANA-06, R-IMP-03, R-IMP-05, R-CTL-06, R-WRAP-02 appear in no row. Three are near-certain from tool/golden wiring — R-MEA-04 (T-09 is the only Tier-A Measure tool otherwise without a rubric home), R-IMP-03 (T-20's proof half; G-proof-01), R-CTL-06 (T-24; G-stdwork-01) — since tier-a-done-means §2 requires every Tier-A tool to have rubric items. The other four (the three phase-conclusion items and R-WRAP-02 realized benefits) are this author's design. Confirm they match matrix intent; if the matrix author meant something else, the matrix's next revision should cite these IDs explicitly either way.
2. **R-ANA-02 evidence sufficiency.** The suite teaches: non-empty evidence field, T-17 for measured comparisons, stratified views. It does not teach how *much* evidence verifies a cause. The criterion holds at "data or observation a reasonable person would accept"; a reviewer instinct to demand statistical verification for every cause would exceed what the suite teaches and break high-schooler passability. Confirm the calibration.
3. **R-DEF-07 critical-to-customer vs easy-to-measure.** Real VoC judgment carried by a single check question. Grading holds to "the check is answered thoughtfully" — confirm that is Green Belt enough.
4. **R-MEA-07 scope.** The grader must hold to the narrow MSA the suite ships (test/retest + two-rater agreement), with EXIT-03 covering everything beyond. A certified reviewer's instinct to expect fuller MSA is out of declared scope by design.
5. **R-IMP-02 pilot-unit selection.** Unbiased selection is design judgment the suite teaches only via prompts and the confounder checklist; the bar is "selection stated honestly," not sampling-theory rigor.
6. **R-CTL-02 grading window.** In a short eval, signals may never fire; the item then grades recorded discipline and mechanics only. Confirm thin-evidence-≠-fail.
7. **R-WRAP-02 timeline.** Student projects rarely have quarters of after-data; realized-to-date with the window named, projection labeled projection, is the passing form.
8. **Pre-score honesty.** Each item's "Pre-scored in code" line is a commitment the M1–M5 builds must implement (tier-a-done-means §2 requires the checks unit-tested). If any listed check proves infeasible, the item text changes by logged edit — the pre-score claims must never exceed what code actually checks.

On the reviewer's pass, status moves from DRAFT to locked, and this section's resolved items move into the item texts.
