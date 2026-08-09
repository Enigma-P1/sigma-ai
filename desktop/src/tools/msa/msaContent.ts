import type { HelperFrameContent } from "../helperFrameTypes";

/** T-12 Measurement Check helper content. "What good looks like" is drawn
 * from rubric R-MEA-07 (an anchor item -- the phase cannot pass without
 * it) -- one source of truth, no parallel checklist (tier-a-done-means
 * §2). The frozen verdict thresholds quoted below are the traceability
 * matrix §4a values; they change only by logged decision. */
export const msaHelperContent: HelperFrameContent = {
  toolId: "T-12",
  isPlaceholder: false,
  whatThisIs:
    "A check of the measurement itself, before you trust anything it measures. First a resolution pre-check: " +
    "can the gauge even see the process? The gauge's smallest step must be a tenth or less of the span it " +
    "judges, with at least 5 distinct values recorded -- a wall clock in whole minutes judging a process " +
    "that varies by 3 minutes fails here, before any math. Then the check itself: for continuous data, one " +
    "operator measures the same items twice and the engine reports repeatability% -- how much of the " +
    "tolerance (or the observed variation) is eaten by the gauge disagreeing with itself. Verdict bands, " +
    "frozen: 10% or less acceptable; over 10% up to 30% marginal; over 30% fail. For pass/fail judgments, " +
    "two raters judge the same items independently and the engine reports % agreement plus kappa -- kappa " +
    "0.75 or more acceptable, 0.40 to under 0.75 marginal, under 0.40 fail. Kappa matters because on a " +
    "low-defect process two raters agree most of the time by luck alone; % agreement is never shown by " +
    "itself.",
  whenToUse:
    "After the data collection plan names the gauge and before the baseline is trusted -- in Measure, every " +
    "time. At the Coffee Bar: ten orders spanning quick to slow, each timed twice with the same phone " +
    "stopwatch by the same person, before believing a single order-to-handoff number. Re-run it after any " +
    "fix to the gauge or the operational definition -- that re-run is how an EXIT-02 stop gets cleared.",
  whenNotTo:
    "Not when your question is bigger than this check. This is deliberately narrow: one operator, " +
    "repeatability only. It cannot see whether two different people would measure differently " +
    "(reproducibility), or whether the gauge reads consistently high (bias), or drifts (stability). Those " +
    "need studies this tool honestly doesn't run -- that's EXIT-03, named on this screen, and the route is a " +
    "quality engineer or a full study in v2, not improvising around it. The classic misuse is skipping the " +
    "check because the numbers \"look fine\": a noisy gauge inflates your spread invisibly, and that noise " +
    "becomes your baseline, your capability, and your fake improvement.",
  fieldGuidance: [
    {
      field: "Data type",
      good: "Continuous for measured numbers (order-to-handoff minutes); attribute for pass/fail judgments (drink made right / made wrong).",
      bad: "Attribute chosen for a time metric because tallying feels easier. (the check must match the data the baseline will actually use)",
    },
    {
      field: "Operator",
      good: "\"Marcus\" -- the same person who will time orders during real collection, named.",
      bad: "Whoever was free that afternoon. (a check run by someone who won't do the measuring checks the wrong system)",
    },
    {
      field: "Gauge / instrument",
      good: "\"Phone stopwatch (seconds)\" or \"POS timestamp clock\" -- the actual thing that will produce the data.",
      bad: "Left blank. (the record can't say what was checked, so a later reader can't tell whether the collection gauge was ever vetted)",
    },
    {
      field: "Gauge increment",
      good: "0.1 -- a stopwatch reading tenths of a minute, on a process whose orders span roughly 2 to 14 minutes: comfortably a tenth of the span.",
      bad: "1 (whole minutes) on a process that varies by about 3 minutes. (increment must be <= 1/10 of the span it judges -- this gauge fails the pre-check because it literally cannot see the differences that matter)",
    },
    {
      field: "USL / LSL (optional)",
      good: "Enter both only when both really exist -- the verdict is then judged against the tolerance width. The Coffee Bar has only an upper limit (5.0 min), so it leaves LSL empty and the engine names \"6 x study variation\" as the denominator instead.",
      bad: "Inventing a lower limit to get the tolerance denominator. (a made-up spec changes which band the verdict lands in -- that's denominator shopping)",
    },
    {
      field: "Items and repeat readings",
      good: "10+ orders spanning the range the process actually shows -- quick ones, slow ones, near-the-limit ones -- each measured twice, same operator, second reading blind to the first.",
      bad: "10 nearly identical easy items. (a range-less sample flatters repeatability% -- the check passes and tells you nothing about the measurements you'll actually make)",
    },
    {
      field: "Items and two-rater judgments (attribute path)",
      good: "10+ drinks judged pass/fail by rater A and rater B independently -- no peeking, no conferring, a mix of clearly-good, clearly-bad, and borderline items. And keep what agreement proves in bounds: it proves the two raters read the yardstick the same way, not that the yardstick is right -- validity takes an independent reference (see the mistake list).",
      bad: "Raters comparing answers as they go. (agreement between people who conferred is theater -- kappa can't rescue it)",
    },
  ],
  whatGoodLooksLike: [
    "The check matching the data type ran BEFORE the baseline was trusted -- resolution pre-check included, " +
      "repeatability% for continuous data, % agreement + kappa for judgment calls.",
    "The study's items follow the instruction: at least 10, spanning the range the process actually shows, " +
      "near-limit items included when specs exist.",
    "The verdict is obeyed: acceptable -> proceed; marginal -> proceed with the caveat carried into your own " +
      "narrative (not narrated as a clean pass); fail -> stop, fix the measurement, re-run the check, and " +
      "only then resume. Taking that stop is pass-level work, not failure.",
    "Your write-up carries the repeatability-only caveat in your own words: \"full gauge study not done -- a " +
      "full study could only read worse, not better.\" The 10/30 bands are borrowed from full-study " +
      "convention, so passing on repeatability alone is the lenient side, and saying so is part of the pass.",
    "A measurement question bigger than this check -- multiple operators, bias, linearity, drift -- takes " +
      "the named exit (EXIT-03) to a human expert, not a workaround.",
  ],
  commonMistakes: [
    "Skipping the check because the numbers \"look fine.\" Gauge noise is invisible in the numbers it " +
      "contaminates -- that's the whole problem.",
    "Reading agreement as validity. Two raters agreeing -- or one operator repeating -- proves the " +
      "yardstick reads consistently, not that it reads RIGHT: a consistently flattering clock (say, a " +
      "stop moment someone in the process controls) passes this check while measuring the wrong thing, " +
      "because both raters share its bias. The check for that is independent evidence: re-time a sample " +
      "against an independently-timed reference, or have someone outside the process hold the watch.",
    "Items that don't span the range: ten easy mid-range orders flatter the result and vet nothing.",
    "Narrating a marginal verdict as a clean pass -- the caveat must survive into your own words.",
    "Rater B seeing rater A's answers (or one person rating twice) in the attribute check.",
    "Pushing past a failed verdict by override or by prose. A failed check blocks capability language " +
      "downstream -- results render as \"unreliable -- measurement system failed\" until a passing re-run " +
      "-- because with a broken gauge, any capability number would describe the gauge's noise, not your " +
      "process. You'd be fixing, or celebrating, a fiction. The block is the suite protecting your project, " +
      "not punishing it.",
  ],
  source:
    "Method source (traceability matrix III.E + §4a frozen triggers): NIST/SEMATECH §2.4 (gauge studies) for " +
    "structure; verdict bands are generic industry threshold conventions -- repeatability% = 6 x s_repeat / " +
    "denominator x 100 with the denominator named on the output (tolerance width when both specs exist, else " +
    "6 x study variation); two-rater agreement reported as % agreement + Cohen's kappa. Called repeatability, " +
    "not \"GRR\" and not \"%EV\", because a single-operator check is not a full variance-decomposed study. " +
    "Acceptance checklist: rubric R-MEA-07; exits EXIT-02, EXIT-03.",
};
