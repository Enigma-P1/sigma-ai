import type { HelperFrameContent } from "../helperFrameTypes";

/** T-20 Before/After Proof + Remaining-Gap Check helper content. "What
 * good looks like" restates the rubric items that grade this tool --
 * R-IMP-03 (before/after proof, anchor), R-IMP-04 (remaining-gap check +
 * loop, anchor), and R-IMP-05 (implementation + goal reconciliation) --
 * one source of truth, no parallel checklist (tier-a-done-means §2). */
export const proofHelperContent: HelperFrameContent = {
  toolId: "T-20",
  isPlaceholder: false,
  whatThisIs:
    "The stats engine re-run on the pilot's data, judged against the plan you declared in T-19 -- then the " +
    "loop's decision point. Before and after get side-by-side stability and capability, the routed test " +
    "with effect size and confidence interval, and the pre-declared threshold checked with the verdict " +
    "stated AS DECLARED: met, or not met. The verdict is what you declared, not what you wish. Then the " +
    "gap half closes the loop: original gap, how much this fix recovered, how much remains, and where to " +
    "go next. Most fixes recover part of the gap -- that is the method working, not failing.",
  whenToUse:
    "When the pilot has run its declared window and the after-period has enough data to say something. At " +
    "the Coffee Bar: before is the frozen baseline (n=120, mean 8.41 min against USL 5.0), after is the " +
    "pilot mornings, same handoff-minutes metric under the same operational definition (register timestamp " +
    "to name call, tenths of a minute) and the same passed measurement system. Say the after-period lands " +
    "at a 6.2-min mean against a declared 7.0 threshold: met -- and the gap panel still does the honest " +
    "arithmetic. Original gap 3.41 (8.41 baseline to the 5.0 goal), recovered 2.21 (64.8%), remaining 1.20 " +
    "-- goal not yet met, so the loop routes to the next verified cause: grinder rework, one change at a " +
    "time.",
  whenNotTo:
    "The classic misuse is moving the finish line: re-declaring the threshold to whatever the after-mean " +
    "hit, or narrating \"improved!\" past a verdict of not met. Both are invalidators -- a wrong number at " +
    "the exact point the project decides what to do next. Also never with a switched yardstick: a changed " +
    "metric, operational definition, or measurement system between before and after proves nothing by " +
    "construction, and the identity check fails the run. And don't skip the proof because the design can't " +
    "carry a test -- when floors are unreachable, the descriptive form IS the pass: magnitudes against the " +
    "declared threshold, \"observed improvement, not statistically tested,\" no inferential language.",
  fieldGuidance: [
    {
      field: "Pilot plan",
      good: "The saved T-19 this run proves -- its declared threshold, comparison, and confounder checklist ride in with it.",
      bad: "No pilot selected, threshold typed fresh here. (a threshold first written at proof time has no pre-declaration story at all)",
    },
    {
      field: "Metric / operational definition / measurement system",
      good: "The baseline's own three, unchanged: handoff_minutes, register-to-name-call in tenths, the T-12-passed camera-video method.",
      bad: "Any of the three switched between before and after. (a changed yardstick is a wrong number by construction -- a named invalidator)",
    },
    {
      field: "Before / After period",
      good: "Before: the baseline dataset itself. After: the whole declared pilot window, in true collection order.",
      bad: "After trimmed to the best week. (cherry-picking the window is the first thing a grader checks the dates for)",
    },
    {
      field: "Declared threshold + direction",
      good: "7.0, lower is better -- verbatim from the pilot plan, and the verdict banner renders met/not-met against exactly that.",
      bad: "\"Well, 7.3 is still better than 8.41.\" (true, and the verdict is still NOT MET -- say both honestly: improvement observed, threshold missed, loop continues)",
    },
    {
      field: "Confounder checklist (re-answered)",
      good: "Answered against what actually happened -- \"fall semester started, demand rose\" -- and the yes prints on the result: improvement shown, but this proof is weakened. A confessed confound weakens the claim honestly; that is the tool working.",
      bad: "A \"no\" the project record contradicts. (concealing a confound doesn't remove it -- it converts a weakened win into a false one)",
    },
    {
      field: "Guardrail metric (before/after)",
      good: "The charter's consequential metric -- say drink re-makes per 100 orders -- entered both sides, so a speed win that spikes re-makes reports as what it is: a tradeoff for the process owner to accept.",
      bad: "Guardrail left blank on a project whose charter names one. (a win that breaks something else is a tradeoff, not a win -- and concealing the loss is Fail-side)",
    },
    {
      field: "Charter baseline / goal",
      good: "8.41 and 5.0 -- the original gap (3.41) every loop iteration is measured against.",
      bad: "Re-typed \"improved\" numbers. (the gap arithmetic runs on computed values with provenance; a wrong remainder here is already an invalidator)",
    },
  ],
  whatGoodLooksLike: [
    "Same metric, same operational definition, same measurement system as the baseline -- the identity " +
      "check passes, and your own write-up never swaps yardsticks either.",
    "The engine re-ran on the pilot data: side-by-side stability, the routed test with effect size + CI " +
      "(or the descriptive form where the design can't carry a test), and the threshold verdict stated as " +
      "declared -- met, or not met.",
    "The re-answered confounder checklist prints on the result, and any reported confound tempers the " +
      "claim in your own words: \"improvement shown, but demand rose -- this proof is weakened.\"",
    "Guardrail metrics report alongside the primary; a primary win with a material guardrail loss is " +
      "stated as a tradeoff for the process owner to accept, never as a plain win.",
    "A threshold met on the mean with an unstable after-process is tempered: \"target hit on average; " +
      "process not yet stable -- monitoring extended.\"",
    "The gap arithmetic is done from computed numbers -- original gap, recovered, remaining -- and an " +
      "explicit routing decision is recorded: goal met, to Control; gap and verified causes remain, next-" +
      "ranked cause, one change at a time; causes exhausted with gap remaining, honest statement and route " +
      "(back to Analyze, or a human expert).",
    "Across loop iterations the cumulative claim is final state vs the original baseline; per-change " +
      "credits stay descriptive and are never summed into a stacked total when effects overlap.",
    "Improve closes with numbers against the charter goal -- met, partially met with the remainder stated, " +
      "or not met with the route taken -- the proven change implemented beyond the pilot, and Control set " +
      "to monitor the implemented state, not the pilot.",
  ],
  commonMistakes: [
    "Claiming improvement with the threshold unmet or the test unsupportive -- the verdict is what you " +
      "declared, not what you wish.",
    "Stripping a reported confound from the claim -- the weakened verdict travels with the number or the " +
      "number is a lie.",
    "Omitting a material guardrail worsening -- a win that breaks something else is a tradeoff, not a win.",
    "Reading a 64.8%-recovered result as failure and abandoning the loop -- partial recovery is the " +
      "expected shape; " +
      "the gap check exists to route you to the next cause, not to shame the fix.",
    "Declaring the goal met while the computed remainder says otherwise -- a wrong number at the loop's " +
      "decision point, enforced again at the phase gate.",
    "Proving the pilot and stopping -- implementation beyond pilot scope, documented, is what Control " +
      "inherits; a pilot-only improvement claimed as implemented fails the conclusion.",
  ],
  source:
    "Method source: gap analysis operationalized per traceability matrix IV.C.1 (golden G-proof-01; " +
    "NIST-reference tests on the engine's stats); the same stability/capability and test routes as T-13/" +
    "T-17, re-run by artifacts/proof.py with gap = |goal - baseline| directionally, recovered, remaining, " +
    "and routing computed with provenance -- never hand-typed. Improve-loop discipline per PLAN §4.1. " +
    "Acceptance checklist: rubric R-IMP-03 (anchor), R-IMP-04 (anchor), R-IMP-05; per rubric §8 an honest " +
    "\"not met\" with the route taken is pass-level work.",
};
