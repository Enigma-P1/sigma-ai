"""Rubric item lookup for the "review" advisor mode (M5 unit 2 brief, PLAN
§5.1 mode 1): grades the current artifact against "the same rubric items
the tool's helper panel restates."

Two tables, both DERIVED FROM THE LOCKED docs/green-belt-rubric.md
(status: LOCKED 2026-08-07 -- see that file's own header) -- this module
never reads docs/ at runtime (the desktop app is shipped via PyInstaller
with `datas=[]`, engine/sigma_engine.spec -- nothing under docs/ is bundled
into a built app, so a runtime read would work in dev and silently break
once packaged). Instead, like every other frozen-external-source constant
in this engine (stats/constants.py's numbers cited to
docs/traceability-matrix.md, artifacts/fmea.py's SEVERITY_ANCHORS), the
rubric text below is TRANSCRIBED once, with the source cited, and changes
only when the locked rubric changes (which itself only happens through the
rubric's own §10 item-8 logged-edit path) -- if that ever happens, this
file's transcription must be re-synced by hand as part of that same edit.

1. TOOL_RUBRIC_ITEMS: tool_id -> the rubric item IDs that tool's helper
   panel cites. No machine-readable mapping exists between the desktop's
   *Content.ts helper-panel files and this Python engine (they're a
   different language, and the citation lives inside each file's free-text
   `source` field, e.g. copqContent.ts: "Acceptance checklist: rubric
   R-DEF-05."). Built here by hand by reading every desktop/src/tools/*/
   *Content.ts `source` field's "Acceptance checklist: rubric ..." citation
   (and, for T-08/T-11 and T-17, an earlier sentence in the same field) --
   the exact table below is that citation set, tool by tool. Order matches
   docs/green-belt-rubric.md's own DMAIC section order.

2. RUBRIC_ITEM_TEXT: rubric item ID -> title + "Grades" + the "Pass means"
   numbered criteria, extracted VERBATIM from docs/green-belt-rubric.md
   (all 39 items, R-DEF-01..R-WRAP-03) by a one-time script matching this
   module's docstring claim -- not hand-retyped, to rule out transcription
   error over 39 items' worth of text. "Needs work when" / "Fail /
   invalidates when" / "Pre-scored in code" / "Judgment-only" are
   deliberately NOT carried here: review mode's output contract is a
   two-valued verdict (pass | needs_work, routes/advisor.py's
   ReviewResponse) matching the rubric's own "Pass means" criteria
   directly, and the fail-line/pre-score-split text is about how the
   *human* grader and the deterministic pre-score work, not what the
   advisor needs to hold an artifact up against.

render_rubric_items_block() is the one function modes.py's review context
selector calls -- everything above is data, not consumed directly.
"""

from __future__ import annotations

from pydantic import BaseModel

# ---- 1. tool_id -> rubric item IDs (module docstring) ----

TOOL_RUBRIC_ITEMS: dict[str, tuple[str, ...]] = {
    "T-01": ("R-DEF-01",),
    "T-02": ("R-DEF-05",),
    "T-03": ("R-DEF-02", "R-DEF-03", "R-DEF-04", "R-DEF-05", "R-DEF-08"),
    "T-04": ("R-DEF-06",),
    "T-05": ("R-DEF-07",),
    "T-06": ("R-MEA-01", "R-MEA-02"),
    "T-07": ("R-MEA-03",),
    "T-08": ("R-MEA-06", "R-MEA-05"),  # checkSheetContent.ts: "R-MEA-06, plus the stratification-as-columns requirement of R-MEA-05"
    "T-09": ("R-MEA-04",),
    "T-10": ("R-MEA-09",),
    "T-11": ("R-MEA-05", "R-MEA-06"),
    "T-12": ("R-MEA-07",),
    # T-13/T-14 (baseline, chart set) are stats-computed views with no
    # ARTIFACT_REGISTRY entry (routes/stats.py) -- no artifact_id ever
    # exists for them, so "review" mode (which grades a specific saved
    # artifact_id) cannot be invoked against them from the desktop. Their
    # rubric item IDs are still recorded here for completeness/consistency
    # with the desktop's own baselineContent.ts/chartSetContent.ts
    # citations, in case a future unit adds a review-able artifact for
    # either (render_rubric_items_block degrades honestly either way --
    # see its docstring).
    "T-13": ("R-MEA-08", "R-MEA-09", "R-MEA-11"),
    "T-14": ("R-MEA-10",),
    "T-15": ("R-ANA-01", "R-ANA-02", "R-ANA-06"),
    "T-16": ("R-ANA-03",),
    "T-17": ("R-ANA-04", "R-ANA-05"),
    "T-18": ("R-IMP-01",),
    "T-19": ("R-IMP-02",),
    "T-20": ("R-IMP-03", "R-IMP-04", "R-IMP-05"),
    "T-21": ("R-CTL-01", "R-CTL-02"),
    "T-22": ("R-CTL-03", "R-CTL-04"),
    "T-23": ("R-CTL-05",),
    "T-24": ("R-CTL-06",),
    "T-25": ("R-WRAP-01", "R-WRAP-02", "R-WRAP-03"),
}


class RubricItemText(BaseModel):
    item_id: str
    title: str
    grades: str  # the doc's own "Grades:" line -- which artifact(s)/tool(s) this item is about
    pass_means: tuple[str, ...]  # the doc's numbered "Pass means" criteria, verbatim


# ---- 2. rubric item ID -> its text (module docstring) ----

RUBRIC_ITEM_TEXT: dict[str, RubricItemText] = {
    "R-DEF-01": RubricItemText(
        item_id="R-DEF-01",
        title="Project selection and routing",
        grades="Project Picker output, including the PDCA quick-path routing (T-01). Exit: EXIT-01.",
        pass_means=(
            "All five intake criteria are answered with project-specific content: scope narrow enough, measurable outcome, obtainable data, a named process owner who cares, plausible business impact.",
            "The routing matches the answers — full DMAIC for a problem that warrants the rigor, the PDCA quick path for a small single-fix problem, and EXIT-01 (rescope or route out) when a criterion fails.",
            "The outcome measure named at intake is the metric the charter and baseline actually carry — or a logged re-charter explains the change.",
        ),
    ),
    "R-DEF-02": RubricItemText(
        item_id="R-DEF-02",
        title="Problem statement quality",
        grades="Project Charter problem statement (T-03).",
        pass_means=(
            "States what, where, when, and magnitude — and the magnitude is a number with units and a time period (\"Line 2 scrap averaged 6.2% in Q2, ~$40k\"), not an adjective.",
            "Contains no cause language and no solution language — nothing that presumes why it happens or prescribes a fix (\"operators need retraining\" is a solution, not a problem).",
            "The stated magnitude is traceable to data the project holds (records, check sheet, export) — a labeled estimate is acceptable; a guess presented as measurement is not.",
            "A reader outside the team could tell, from the statement alone, what hurts and by how much.",
        ),
    ),
    "R-DEF-03": RubricItemText(
        item_id="R-DEF-03",
        title="Goal and metrics",
        grades="Charter SMART goal, primary and consequential metrics (T-03; BoK I.A.2, II.C.2, II.C.4).",
        pass_means=(
            "The goal is SMART in substance: a target value for a named metric with a date, sized against the problem's magnitude (\"reduce line-2 scrap from 6.2% to 3% by Nov 30\") — improvement-sized, not perfection-sized.",
            "The primary metric is operationally defined (or points at the Data Collection Plan's definition) and is the same measure the baseline will compute.",
            "At least one consequential (guardrail) metric is named — what must not get worse while the primary improves — and it is checked again at the proof.",
            "The goal connects to the business driver named at intake, in the student's words.",
        ),
    ),
    "R-DEF-04": RubricItemText(
        item_id="R-DEF-04",
        title="Scope, team, and project risk",
        grades="Charter scope in/out, team + process owner, and the key-risks block (T-03, incl. matrix correction A-4); Pareto as scoping evidence where used (T-14); Tier-B stakeholder deep-dive not graded (T-26). BoK II.A.5, II.C.3, II.C.7.",
        pass_means=(
            "Scope-in and scope-out are both non-empty and specific — a named process segment, line, or product family, not \"the warehouse.\"",
            "Where the scope was narrowed from a bigger problem, the narrowing cites evidence (e.g. a Pareto showing the chosen category dominates), not preference.",
            "The team is listed with a named process owner — the person who runs the process, not a placeholder or a title-only sponsor.",
            "The risk block holds at least one real project risk with a likelihood/impact rating, a mitigation, and an owner. (Project risks — data access, resource loss, seasonality — not process failure modes; those are FMEA's job, T-16.)",
        ),
    ),
    "R-DEF-05": RubricItemText(
        item_id="R-DEF-05",
        title="Business impact quantified (COPQ)",
        grades="COPQ / Benefit Calculator worksheet and the charter's business-impact field (T-02, T-03). BoK II.E.1 (COPQ half; yield/indices grade under R-MEA-09).",
        pass_means=(
            "COPQ is built from named cost buckets (scrap, rework, overtime, expediting, lost business...) each as quantity × rate computed by the tool — no hand-typed totals anywhere.",
            "Inputs are project-real: taken from records where records exist, and labeled estimate where they don't.",
            "The charter's business-impact field equals the calculator's output — one number, one source.",
            "Any annualization or extrapolation states its basis (\"Q2 actuals × 4\").",
        ),
    ),
    "R-DEF-06": RubricItemText(
        item_id="R-DEF-06",
        title="SIPOC",
        grades="SIPOC form + rendered diagram (T-04). BoK II.A.2, II.A.4.",
        pass_means=(
            "All five columns are populated, and the process column is 4–7 high-level steps (one declared range — Belt-panel round 2 caught the 4–7-vs-4–9 mismatch; the code check flags 8–9 as Needs-work-side, everything outside 4–9 hard-flags) whose start and end boundaries match the charter scope.",
            "Outputs are paired to the customers who actually receive them, and inputs to their suppliers — not free-floating lists.",
            "The CTQ-bearing output appears — the thing the customer cares about is on the map, so the CTQ tree (T-05) has something to hang from.",
        ),
    ),
    "R-DEF-07": RubricItemText(
        item_id="R-DEF-07",
        title="Voice of the customer → CTQ tree",
        grades="VoC capture + CTQ tree (T-05). BoK II.B.1–II.B.3.",
        pass_means=(
            "At least one real customer is identified by role (internal or external) — \"everyone\" is nobody.",
            "Customer statements are captured close to verbatim, each with its source noted (interview, complaint log, direct observation).",
            "The tree walks statement → need → measurable CTQ, and every CTQ carries a measure and a direction or target.",
            "The tool's check — \"is this what the *customer* critically needs, or what the process finds easy to measure?\" — is answered per CTQ, in the student's words.",
            "The primary CTQ is the charter's primary metric, or the mismatch is explained on the artifact.",
        ),
    ),
    "R-DEF-08": RubricItemText(
        item_id="R-DEF-08",
        title="Plan and tollgate discipline",
        grades="Charter timeline field (T-03) + tollgate checklists at each phase exit (T-25). BoK II.C.5. Graded across the whole project — evidence accrues at every gate.",
        pass_means=(
            "The charter timeline names phase-level milestones with dates, consistent with the goal date — a plan, not a wish.",
            "The Define tollgate checklist is completed before Measure work begins — or the soft gate is overridden with a logged, non-boilerplate reason (PLAN §4.2 allows iteration; it requires honesty about it).",
            "The same discipline holds at every later phase exit: checklist completed, or override logged with a reason.",
        ),
    ),
    "R-MEA-01": RubricItemText(
        item_id="R-MEA-01",
        title="As-is process map",
        grades="Swimlane process map (T-06). BoK I.B.2, II.A.2, III.A.",
        pass_means=(
            "The map shows the as-is process — walked or observed, not the procedure as written or the improved state as hoped. Tell: it contains the inconvenient parts (workarounds, waits, informal handoffs).",
            "Start and end match the SIPOC boundaries; lanes are the roles/functions that actually touch the work.",
            "Decision points and rework loops that exist in reality appear on the map — a defect problem mapped with zero rework loops is suspect on its face.",
            "Steps carry the data downstream tools reuse (times and/or defect points on the relevant steps) — one project data model, many views.",
        ),
    ),
    "R-MEA-02": RubricItemText(
        item_id="R-MEA-02",
        title="Value analysis and waste walk",
        grades="VA/NVA/enabling tags + 8-wastes walk on the map (T-06). BoK I.B.2.",
        pass_means=(
            "Every step is tagged value-add / non-value-add / enabling, with the value test applied honestly (customer would pay for it; it changes the thing; done right the first time).",
            "The waste walk produces concrete observations tied to locations on the map (\"operator waits ~4 min at step 6 for QC sign-off\") — not a recited list of the 8 wastes.",
            "The tags roll up to a number — NVA time or NVA step share — that the Improve phase can attack.",
        ),
    ),
    "R-MEA-03": RubricItemText(
        item_id="R-MEA-03",
        title="Spaghetti diagram",
        grades="Interactive spaghetti diagram (T-07). BoK I.B.1. **Applicability:** graded only when the problem has a movement/layout component; otherwise N/A with reason.",
        pass_means=(
            "The floor plan is calibrated by a drawn known-length line, and that real length is stated.",
            "Routes are traced per operator or trip type from an actual observation — trips counted, not imagined.",
            "The computed metrics are read and used: distance per trip, trip count, and daily travel burden (distance × frequency) quoted where the burden matters.",
            "The observation window is stated: when, how long, which shift.",
        ),
    ),
    "R-MEA-04": RubricItemText(
        item_id="R-MEA-04",
        title="Time study / work sampling",
        grades="Guided time study / work sampling (T-09). Supports BoK III.D.3 (element-time spread). **Applicability:** graded when the route required timed observation; otherwise N/A with reason.",
        pass_means=(
            "Work elements are defined before timing starts — an element list with start/stop triggers, not categories invented mid-study.",
            "The tool's recommended cycle count is observed, or the shortfall is named on the artifact (\"6 cycles; tool recommends 10 — treat spread as rough\").",
            "Element times are reported with their spread — a single observation is never presented as \"the time.\"",
            "Outliers are flagged and either explained or visibly retained — never silently deleted.",
        ),
    ),
    "R-MEA-05": RubricItemText(
        item_id="R-MEA-05",
        title="Data collection plan",
        grades="Data Collection Plan incl. operational definition, data-type identification, sample-size guidance (T-11). BoK III.D.1, III.D.2.",
        pass_means=(
            "The operational definition passes the two-people test as written: unit, boundaries, the exact moment of measurement, and the instrument/gauge named — two people following it would record the same value.",
            "The data type is identified correctly (continuous vs attribute/count) — this single field drives every downstream chart and test route.",
            "Stratification factors (shift, machine, operator, day...) are chosen for suspected sources of difference and captured as columns, so later tools can split on them.",
            "The sample-size guidance was consulted: planned n stated with the rule-of-thumb or calculator rationale attached.",
            "Who collects, where, when, and how is stated — including a bias check (is this a convenience sample? says so if so).",
        ),
    ),
    "R-MEA-06": RubricItemText(
        item_id="R-MEA-06",
        title="Data collection execution",
        grades="Check Sheet / Tally output or imported dataset (T-08; Tier-B log sheets T-27 feed it). BoK III.D.2.",
        pass_means=(
            "Data was collected per the plan: same operational definition, strata recorded on the rows, timestamps present.",
            "Achieved n is stated against planned n — and a shortfall is named, not smoothed over.",
            "The collection artifact is the dataset the baseline runs on — no re-typed intermediate copy between tally and analysis.",
            "Basic data-quality checks are visibly done: missing values, impossible values, duplicates found and addressed with a note.",
        ),
    ),
    "R-MEA-07": RubricItemText(
        item_id="R-MEA-07",
        title="Measurement system check",
        grades="Narrow MSA — test/retest repeatability (continuous) or two-rater attribute agreement (pass/fail) (T-12). BoK III.E. Exits: EXIT-02, EXIT-03.",
        pass_means=(
            "The check matching the data type was run before the baseline was trusted: test/retest repeatability for continuous data (reported as repeatability% — renamed from %EV at Belt-panel round 2; defined in matrix §4a — with its denominator named as which one it is — tolerance when specs exist, else study variation, matching the tool's rule; an unnamed denominator lets the flatter number get shopped), two-rater agreement with kappa for judgment calls — including the resolution pre-check the tool runs first (the gauge reads fine enough to see the process; a stopwatch in whole minutes on a 3-minute process fails here, before any repeatability math). The student's narrative carries the tool's repeatability-only caveat (\"full gauge study not done — a full study could only read worse, not better\"): the 10/30 bands are borrowed from full-study convention, so passing them on repeatability alone is the lenient side, and saying so is part of the pass (Belt-panel review). The check's samples follow the tool's instruction: ≥10 items spanning the range the process actually shows, near-limit items included when specs exist.",
            "The verdict is obeyed: acceptable → proceed; marginal → proceed with the caveat carried into the narrative; fail → stop, fix the measurement (EXIT-02), re-run the check — and only then resume. Taking that stop is Pass-level work (§8). Verdict thresholds are the matrix §4 frozen trigger values.",
            "If the measurement question exceeds the narrow check the suite ships — multi-operator variation, bias, linearity — the named exit is taken (EXIT-03: human quality engineer / v2 T-35), not improvised around.",
        ),
    ),
    "R-MEA-08": RubricItemText(
        item_id="R-MEA-08",
        title="Stability before capability",
        grades="Baseline tool's enforced order — spec limits + operational definition, then stability (I-MR, or p-chart on the attribute path), then capability (T-13). BoK III.F.1, III.F.2. Exit: EXIT-04.",
        pass_means=(
            "Spec limits are entered before capability, with a source: customer requirement, standard, or a stated internal target — never reverse-engineered from the data to flatter the result.",
            "The stability read is correct: signals identified, and the stable/not-stable call matches what the chart shows.",
            "Not stable → EXIT-04 honored: \"you don't have a baseline yet\"; special causes investigated; Pp/Ppk only, labeled performance-not-capability; no Cp/Cpk claim anywhere — including in the student's own prose.",
            "The data enters in true collection order — stability analysis on shuffled data is meaningless.",
        ),
    ),
    "R-MEA-09": RubricItemText(
        item_id="R-MEA-09",
        title="Capability, yield, and sigma reported honestly",
        grades="Capability indices + sigma level (T-13), FPY/RTY/DPMO (T-10). BoK II.E.1, III.F.3, III.F.4; IASSC 2.4.3. Exit: EXIT-05.",
        pass_means=(
            "The right family for the data: continuous → Cp/Cpk and/or Pp/Ppk with the within-vs-overall distinction stated in the student's own summary; attribute → FPY/RTY/DPMO with the p-chart baseline path.",
            "Yield is computed from good/rework/scrap counts with rework counted — RTY, not the flattering final-yield number, is what the narrative quotes when rework exists.",
            "Non-normal data → the percentile-method caveat (EXIT-05) stays attached in the student's narrative, not just on the auto-printed export.",
            "Sigma level is reported with the 1.5σ shift convention named, as the tool prints it.",
            "The baseline number produced here is the charter metric's number — same units, same definition.",
        ),
    ),
    "R-MEA-10": RubricItemText(
        item_id="R-MEA-10",
        title="Descriptive and graphical reads",
        grades="Pareto / histogram / run chart (+ box/scatter per matrix correction A-2) (T-14); descriptive statistics displayed with them (T-13). BoK III.D.3, III.D.4.",
        pass_means=(
            "The charts the data shape calls for exist: histogram for shape, run chart for time behavior, Pareto where categorical defect data exists, box/scatter where the tool offers them.",
            "Each chart is read correctly in the student's own words, graded against the data pattern itself — the vital few named from the Pareto (or its absence admitted when the bars are flat), shape and spread described from the histogram, drift/shift/runs noted from the run chart. A read that correctly disagrees with a wrong verdict headline is a Pass — and files a suite bug; agreement with the headline earns nothing by itself.",
            "Center and spread are quoted as the computed mean/median and SD/IQR — never re-derived by hand.",
        ),
    ),
    "R-MEA-11": RubricItemText(
        item_id="R-MEA-11",
        title="Baseline statement and charter reconciliation",
        grades="The Measure-exit baseline statement (T-13 outputs + charter T-03, tollgate T-25).",
        pass_means=(
            "One baseline sentence exists and is complete: metric, value, period, n, stability status, and the capability-or-performance label — every element matching computed results.",
            "It is reconciled with the charter's claimed magnitude: confirmed, or the charter revised by logged edit (\"charter said 6.2%; measured 9.1%; charter updated\") — never both numbers left standing in conflict. Material has a frozen default (Belt-panel round 2 — an undefined threshold leaves the gate to grader mood): relative delta > 10%, or any delta that changes goal feasibility or direction. A material magnitude change refreshes the money too: the COPQ/business-impact figure recomputes from the measured baseline (Belt-panel review — otherwise the dollar story stays fiction while the metric story gets fixed).",
            "The goal is re-checked against the measured baseline and restated in its terms if needed.",
        ),
    ),
    "R-ANA-01": RubricItemText(
        item_id="R-ANA-01",
        title="Cause exploration (fishbone + 5 Whys)",
        grades="Fishbone (6M) + 5 Whys chains (T-15). BoK IV.C.2.",
        pass_means=(
            "The fishbone's effect is the baselined problem — the measured gap, not a convenient symptom of it.",
            "At least four of the 6M categories carry project-specific candidate causes; causes are phrased as conditions or mechanisms (\"labels applied before ink dries\"), not absent solutions (\"no barcode scanner\" is a solution wearing a cause costume).",
            "5 Whys runs on the leading candidates: each chain at least three levels deep or ending at a named actionable cause, with each \"why\" actually explaining the level above it.",
            "Breadth before depth: more than one branch is explored — the diagram is not a single pre-decided path with decoration.",
        ),
    ),
    "R-ANA-02": RubricItemText(
        item_id="R-ANA-02",
        title="Evidence discipline on causes",
        grades="Evidence fields + verified/unproven status on every cause (T-15); verification tests where used (T-17, T-14 stratified views). BoK IV.C.2. This is the item the Improve phase stands on.",
        pass_means=(
            "Every cause carries a three-state status — candidate → supported → confirmed for action (Belt-panel round 2; \"verified\" in this rubric = confirmed for action): *candidate* = proposed, evidence field empty; *supported* = evidence attached showing the condition exists (a dated gemba observation, a check-sheet split); *confirmed for action* = the evidence ties the cause to the CTQ gap — a stratified Pareto or view showing the gap concentrates where the cause operates, or a test result. Stratified descriptive evidence and dated observation count; formal tests are required only when the cause claims a measured difference. \"Team consensus\" alone moves nothing past candidate. Two calibration exemplars: *bare Pass* — \"batch delays concentrate on shift B (check-sheet split, 31 of 42 delays, weeks 2–4); B uses the old fixture\" = confirmed for action. *Fail* — \"operators agree the fixture is the problem\" carried as verified = an assumption wearing a badge.",
            "Causes claiming a measured difference cite the test or chart that shows it (T-17 output or a stratified view) — not an eyeballed pair of averages.",
            "The evidence pertains to *that* cause — the cited artifact addresses the cause's mechanism, not just the general problem.",
            "Unverified candidates stay visibly flagged unproven and are not used by Improve.",
        ),
    ),
    "R-ANA-03": RubricItemText(
        item_id="R-ANA-03",
        title="Process FMEA",
        grades="Process FMEA worksheet (T-16). BoK I.C.2.",
        pass_means=(
            "Failure modes are specific failures of specific process steps (drawn from the T-06 map), each with its effect and cause — \"process fails\" is not a mode.",
            "Severity/occurrence/detection are rated against the 1–10 anchor scales — spot-checked, a rating matches its anchor's wording, not gut feel.",
            "Prioritization is severity-sensitive in substance — the action list reflects the stated RPN limitation (equal RPNs are not equal risks, high severity never ignorable) whatever sort order the worksheet displays; severity-first is the tool's default view, not a graded requirement (Belt-panel round 2).",
            "Top items carry actions with owners.",
        ),
    ),
    "R-ANA-04": RubricItemText(
        item_id="R-ANA-04",
        title="Right test, right route",
        grades="Hypothesis-test selector routing and its printed decision path (T-17, incl. matrix correction A-1 one-sample routes). BoK IV.B.1, IV.B.2; IASSC 3.4.1, 3.5.2, 3.5.6, 3.5.7. Exits: EXIT-06..14.",
        pass_means=(
            "The comparison question is stated first, in plain words — what vs what, paired or independent, continuous or count, against-a-target or between-groups — and it is the real question the project needs answered (traceable to a verified cause or the goal), not a question retrofitted to a route.",
            "The student explains in their own words why the routed test fits that structure — what is being compared, why paired/independent, what the test can and cannot say — and the narrative doesn't contradict the printed decision path retained with the artifact. Restating the tool's output is not an explanation; the explanation must survive with the tool's headline covered up.",
            "When the data trips a floor or an unsupported case, the named exit is taken: small n (EXIT-06), sparse cells (EXIT-07), repeated measures (EXIT-08), autocorrelation (EXIT-09), rates with exposure (EXIT-11), multiple simultaneous comparisons (EXIT-12), ANOVA-significant pairwise (EXIT-13), non-normal 3+ groups (EXIT-14). Recognizing the exit is a Pass (§8).",
            "One pre-declared primary comparison — no shotgun p-values (EXIT-12's discipline, visible in the artifact).",
        ),
    ),
    "R-ANA-05": RubricItemText(
        item_id="R-ANA-05",
        title="Interpretation discipline",
        grades="The student's conclusions drawn from T-17 output (which always carries effect size + CI + plain English); scatter reads (T-14, correction A-2). BoK IV.A.2, IV.B.1. Exit: EXIT-15.",
        pass_means=(
            "Conclusions quote effect size and confidence interval, not just p — and state practical significance against the goal (\"2.1 min faster, CI 0.8–3.4; the goal needs 3.0 — real but not sufficient alone\").",
            "Non-significant is never narrated as \"no difference\" — the honest form is \"no difference shown at this sample size.\"",
            "Claims stay inside what was tested: a difference between shifts is not proof of the mechanism the student suspects behind the shifts.",
            "Association language is disciplined: correlation ≠ causation observed; scatter-plot reads stay visual and qualitative in v1, with quantified correlation/regression deferred by name (EXIT-15 → T-30 at v1.1).",
        ),
    ),
    "R-ANA-06": RubricItemText(
        item_id="R-ANA-06",
        title="Analyze conclusion: verified causes ranked against the gap",
        grades="The Analyze-exit ranked cause list — T-15 verified statuses ordered for the Improve loop (feeds T-18; tollgate T-25).",
        pass_means=(
            "A closing list of verified causes exists, each with its evidence pointer, ranked by likely impact on the baseline gap with the ranking rationale stated (Pareto share, effect size, frequency — whatever the evidence supports). This ranking is what the Improve loop consumes first.",
            "The list is honest about coverage: it plausibly accounts for the gap the goal must close, or the shortfall is named (\"verified causes explain perhaps half; remaining drivers unknown\"). When the verified set plausibly explains little or none of the gap, naming it is necessary but not sufficient to proceed: the route is back to Analyze for more cause work, or the named human-expert exit — Improve does not launch on unverified guesses (Belt-panel review).",
            "Nothing unverified rides in the ranked list.",
        ),
    ),
    "R-IMP-01": RubricItemText(
        item_id="R-IMP-01",
        title="Solution selection",
        grades="Solution Selection Matrix — impact/effort + weighted criteria, ranked fix list (T-18). BoK V.B.",
        pass_means=(
            "At least two candidate solutions were considered for the top-ranked verified cause — the matrix is a comparison, not a rubber stamp for a pre-decided fix.",
            "Every solution links to a verified cause; the tool flags unlinked solutions, and none survive to the ranked list unresolved.",
            "Criteria and weights were set before scoring (impact/effort at minimum), and the scoring arithmetic is the tool's.",
            "The output is a ranked fix list, and the #1 pick is the top scorer — or the deviation carries a logged reason.",
        ),
    ),
    "R-IMP-02": RubricItemText(
        item_id="R-IMP-02",
        title="Pilot design",
        grades="Pilot Plan — the small-study designer (T-19). BoK V.B. Exit: EXIT-10. This item enforces the product's method: **one change at a time** (PLAN §4.1).",
        pass_means=(
            "One change per pilot, stated in one sentence. Multiple candidate fixes become sequential pilots through the loop — or, when a genuinely combined question exists, the named exit (EXIT-10: advisor / v1.1 Experiment Planner / human expert), never a bundle claimed as attributable. One honest carve-out (Belt-panel round 2): a declared inseparable package — components that cannot be deployed apart — may run as one pilot when it is declared as the package up front, attribution goes to the package only, the components are listed, and no component-level claim is ever made. An undeclared bundle, or component credit claimed from a package pilot, stays EXIT-10's failure.",
            "The comparison is defined before running: baseline period or parallel comparison, stated, with who/what is included and how selected.",
            "Success threshold and analysis plan are declared before data collection — record-entry timestamps support the claim (they show entry order, not observation order; see the pre-score note below).",
            "The falsification line is filled in and substantive: \"what would prove this DIDN'T work.\"",
            "The confounder checklist (staffing, season, demand, measurement changed?) is answered up front, to be re-answered at proof.",
        ),
    ),
    "R-IMP-03": RubricItemText(
        item_id="R-IMP-03",
        title="Before/after proof",
        grades="Before/After Proof — the stats-engine re-run on pilot data (T-20, proof half).",
        pass_means=(
            "The proof runs the same metric, same operational definition, same measurement system as the baseline — a changed yardstick proves nothing.",
            "The engine re-ran on the pilot data: side-by-side stability, the appropriate Tier-A test with effect size + CI (or the criterion-4 descriptive form where the design can't carry a test), and the pre-declared threshold checked — with the verdict stated as declared: met, or not met. Across loop iterations, the cumulative claim is final-state vs original baseline; per-change credits stay descriptive and are never summed into a stacked total when effects overlap (Belt-panel round 2).",
            "The confounder checklist is re-answered and its answers print on the result; any reported confound tempers the claim in the student's own words (\"improvement shown, but staffing changed — this proof is weakened\").",
            "The after-period has enough run to say something — the tool's floors honored; when the design honestly cannot support an inferential test (floor unreachable, no comparison window), the descriptive-proof form is the pass: before/after magnitudes shown against the pre-declared threshold, evidence strength stated plainly (\"observed improvement, not statistically tested\"), no inferential language (Belt-panel round 2 — a student is never forced into a nominal test the data can't carry).",
            "The charter's consequential (guardrail) metrics report alongside the primary: a primary win with a material guardrail loss cannot be claimed as plain \"improvement proven\" — the honest form is a stated tradeoff for the process owner to accept, and concealing the loss is Fail-side (Belt-panel review).",
            "A threshold met on the mean with an unstable after-process is not narrated as a clean win — the honest form tempers (\"target hit on average; process not yet stable — loop continues / monitoring extended\") (Belt-panel round 2).",
        ),
    ),
    "R-IMP-04": RubricItemText(
        item_id="R-IMP-04",
        title="Remaining-gap check and the improvement loop",
        grades="Remaining-gap check + loop routing (T-20, gap half). BoK IV.C.1 — gap analysis operationalized. The loop discipline (PLAN §4.1): rank → fix one → prove → check gap → next.",
        pass_means=(
            "The gap arithmetic is done from computed numbers: original gap, amount recovered by this fix, remainder — \"this fix got you 80%; here's what's left.\"",
            "An explicit routing decision is recorded: goal met → Control; gap remains and verified causes remain → next-ranked cause, one change at a time; causes exhausted with gap remaining → honest statement and route (back to Analyze, or exit to a human expert).",
            "Every loop iteration repeats the R-IMP-02/R-IMP-03 discipline — graded on the repeat artifacts when iterations exist.",
        ),
    ),
    "R-IMP-05": RubricItemText(
        item_id="R-IMP-05",
        title="Improve conclusion: implementation and goal reconciliation",
        grades="The Improve-exit state — implementation beyond pilot, reconciled against the charter goal (T-20 outputs + charter T-03; feeds T-22/T-24; tollgate T-25).",
        pass_means=(
            "The proven change is implemented beyond the pilot scope, with what-changed documented — the material the SOP (T-24) and control plan (T-22) will carry.",
            "Improve closes with numbers against the charter goal: met / partially met with the remainder stated / not met with the honest route taken. Partial success stated as partial is Pass-side; see §8.",
            "What Control will monitor is the implemented state — pilot-only improvements are not claimed as implemented.",
        ),
    ),
    "R-CTL-01": RubricItemText(
        item_id="R-CTL-01",
        title="Control chart selection and construction",
        grades="Control charts — I-MR (continuous) or p (attribute) via the printed selector (T-21). BoK VI.A.1, VI.A.3.",
        pass_means=(
            "The chart family matches the data type through the printed selector — I-MR for continuous, p for attribute with the denominator handled per subgroup — and the chart monitors the primary CTQ/metric, not a convenient proxy (or the proxy is explained).",
            "Limits are computed by the tool from a post-improvement period that is itself demonstrated stable (Belt-panel round 2 — freezing limits from an unstable window preserves bad limits): the tool's frozen floor is ≥ 20 points with no default-rule signal in the limit-setting window; short of that, the chart runs diagnostically — plotted, no frozen limits, no \"sustained control\" claim.",
            "Once established, limits are frozen — recalculated only on a deliberate, logged decision, never silently refit to recent data.",
            "Control limits and spec limits are kept distinct in the student's own language — \"out of control\" and \"out of spec\" are different sentences.",
        ),
    ),
    "R-CTL-02": RubricItemText(
        item_id="R-CTL-02",
        title="Signal interpretation and response",
        grades="Western Electric rule signals (default: rules 1 + 4, the low-false-alarm pair; zone rules 2–3 opt-in — see matrix VI.A.1) and what the student did about them (T-21). BoK VI.A.1.",
        pass_means=(
            "Every fired signal gets a recorded read in the student's words — special cause vs common cause — graded against what the data pattern shows, in process terms (\"8 points above center starting when the new fixture arrived\"), not by echoing the chart's explanation text. A read that correctly disagrees with a wrong signal explanation is a Pass and files a suite bug.",
            "Special-cause signals trigger the response path (OCAP, R-CTL-04): investigation/containment recorded against the signal.",
            "No tampering: no adjustments made on common-cause variation (the classic over-reaction), and no repeated signal left unacknowledged.",
        ),
    ),
    "R-CTL-03": RubricItemText(
        item_id="R-CTL-03",
        title="Control plan core",
        grades="Control Plan — what's monitored, how, how often, by whom (T-22). BoK VI.B.1.",
        pass_means=(
            "Every monitored item names: the characteristic, how it's measured (linked to its operational definition), where, how often, and who — a named person who has accepted the role, not \"the team.\" The tool requires the owner; the grader checks the person is real (appears on the charter team or a handoff note).",
            "The monitoring frequency has a reason — tied to how fast the process could drift or how much volume flows — not a default left standing.",
            "The plan covers what Improve changed plus the primary CTQ — the fix is monitored, not just the outcome.",
        ),
    ),
    "R-CTL-04": RubricItemText(
        item_id="R-CTL-04",
        title="Sustainment: response plan, training, check-ins",
        grades="OCAP (response plan), training & handoff block (matrix correction A-5), scheduled check-ins (T-22); the SOP as the training artifact (T-24). BoK VI.B.1, VI.B.3.",
        pass_means=(
            "OCAP: for each monitored item, the out-of-control action path carries four concrete elements — the actionable first response, the containment step, the escalation trigger and recipient, and the acting owner (Belt-panel round 2 recalibration: a first-project Green Belt writes an actionable path; fully executable emergency procedure depth belongs to the operational owner's SOP).",
            "Training & handoff: who gets trained, on what (the T-24 SOP, which exists and is referenced), by whom, by when, verified how (sign-off or observed demonstration) — a fix nobody is trained on dies with the project.",
            "Check-ins: the scheduled check-ins are accepted, and every check-in due within the grading window is answered with numbers against the limits.",
        ),
    ),
    "R-CTL-05": RubricItemText(
        item_id="R-CTL-05",
        title="5S audit",
        grades="Scored 5S audit with photos and trend (T-23). BoK V.C.1. **Applicability:** graded when the project has a workplace-organization component; otherwise N/A with reason.",
        pass_means=(
            "A baseline audit is scored against the checklist, with photos wherever physical state carries the score.",
            "Scores track the checklist's anchors — spot-checked against the photos, a 4 looks like the checklist's 4, and the scores are not uniform by reflex.",
            "Recurrence is real: a schedule exists (or the trend already has ≥2 points), and the lowest-scoring category carries an action.",
        ),
    ),
    "R-CTL-06": RubricItemText(
        item_id="R-CTL-06",
        title="Standard work / SOP",
        grades="Standard Work / SOP — the improved method written down (T-24). BoK V.C.1, and the training artifact for VI.B.3.",
        pass_means=(
            "The improved method is written as steps a qualified-but-new person could follow: each step an action with its standard (\"what right looks like\"), and the points that changed from the old method highlighted.",
            "Version, owner, and date fields are set; if an older instruction existed, the SOP names what it supersedes.",
            "The SOP matches the process map's improved state and is the document the training block (R-CTL-04) points at — one method, one source.",
        ),
    ),
    "R-WRAP-01": RubricItemText(
        item_id="R-WRAP-01",
        title="A3 final report",
        grades="A3 guided narrative + the project record it rolls up (T-25). BoK II.C.6.",
        pass_means=(
            "The A3 reads as one argument — problem → baseline → causes → countermeasures → proof → control — with every panel consistent with its source artifact: numbers identical, claims not upgraded in transit (the proof panel keeps the confound the T-20 result printed; the baseline panel keeps the performance-not-capability label).",
            "It works as narrative for a sponsor who saw none of the working artifacts — panels are prose telling the story, not field dumps.",
            "Every quantitative claim on the A3 traces to a provenance object carried in the export.",
        ),
    ),
    "R-WRAP-02": RubricItemText(
        item_id="R-WRAP-02",
        title="Realized benefits, honestly stated",
        grades="COPQ re-run at Wrap + realized-benefits panel (T-02, T-25; drawing on T-20/T-13 numbers).",
        pass_means=(
            "The COPQ is re-run with post-improvement actuals over a stated window; realized-to-date is separated from annualized projection, each labeled as what it is. (A student project may have weeks of after-data, not quarters — realized-to-date with the window named is the passing form.)",
            "The benefit arithmetic ties to the measured improvement — the delta the proof showed — not to the goal, and not to the original COPQ hope.",
            "Costs of the fix are netted, or at least named beside the benefit.",
        ),
    ),
    "R-WRAP-03": RubricItemText(
        item_id="R-WRAP-03",
        title="Closure and lessons",
        grades="Closure + lessons panel, open-item handoff, project record (T-25). BoK II.C.8.",
        pass_means=(
            "Objectives-vs-charter reconciliation in numbers — goal, achieved, remainder — consistent with the Improve conclusion (R-IMP-05).",
            "Lessons learned with substance: at least two, including at least one thing that went wrong or a dead end. A lessons panel containing only wins is not lessons — and this suite's brief is documenting the failures too.",
            "Open items are handed off with owners: the remaining gap, pending check-ins, candidate causes left unverified on the table.",
            "The project record is complete and versioned — the folder holds every artifact the A3 cites, loadable.",
        ),
    ),
}


def render_rubric_items_block(tool_id: str) -> str:
    """The text `modes.py`'s review context selector folds into
    `extra_block` -- engine-authored (never wrapped untrusted; see
    context.py's wrap_untrusted docstring for what that tag means and why
    this content doesn't need it). Degrades honestly rather than raising
    for a tool_id with no rubric mapping (a future/placeholder tool, or
    T-13/T-14's no-artifact case) -- the addendum text (modes.py) already
    tells the model what an empty rubric context means; this function's
    job is just never to crash the review call over it."""
    item_ids = TOOL_RUBRIC_ITEMS.get(tool_id, ())
    if not item_ids:
        return f"No rubric items are mapped to tool {tool_id!r}."

    sections = [f"Rubric items for {tool_id} (docs/green-belt-rubric.md, LOCKED 2026-08-07):"]
    for item_id in item_ids:
        item = RUBRIC_ITEM_TEXT.get(item_id)
        if item is None:
            continue  # defensive only -- every TOOL_RUBRIC_ITEMS id has a matching entry, see test_advisor_rubric_items.py
        sections.append(f"\n{item.item_id} — {item.title}\nGrades: {item.grades}\nPass means:")
        sections.extend(f"  {i}. {text}" for i, text in enumerate(item.pass_means, start=1))
    return "\n".join(sections)
