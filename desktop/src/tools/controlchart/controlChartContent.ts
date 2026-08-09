import type { HelperFrameContent } from "../helperFrameTypes";

/** T-21 Control Chart helper content. "What good looks like" restates the
 * rubric items that grade this tool -- R-CTL-01 (chart selection and
 * construction) and R-CTL-02 (signal interpretation and response) -- one
 * source of truth, no parallel checklist (tier-a-done-means §2). */
export const controlChartHelperContent: HelperFrameContent = {
  toolId: "T-21",
  isPlaceholder: false,
  whatThisIs:
    "The alarm system for the improved process. A printed selector picks the chart family from the data " +
    "type -- continuous measurements get an I-MR chart; attribute data gets the defectives-or-defects " +
    "question first, because pass/fail UNITS fit a p chart and counts-per-unit are Poisson-family data the " +
    "p chart's math cannot carry (refused by name, EXIT-11; c/u charts ship v1.1). Limits are computed once " +
    "from a demonstrated-stable post-improvement window and then FROZEN: new points are judged against " +
    "them, they do not reshape them. That freeze is the whole alarm: a process drifting away from frozen " +
    "limits fires signals; limits recalculated on a whim follow the drift and erase the alarm system.",
  whenToUse:
    "After Improve implements the fix, to hold it -- and once before that, in Measure, run UNFROZEN: a " +
    "diagnostic chart with no frozen limits is the honest stability read on baseline data (the attribute " +
    "baseline runs its p chart exactly this way -- plotted, no freeze, no sustained-control claim); " +
    "freezing limits to monitor against stays a post-Improve act. At the Coffee Bar: daily peak " +
    "handoff-minutes values on " +
    "an I-MR chart, limits frozen from at least 20 post-change points that themselves show no rule-1/" +
    "rule-4 signal. The customer's 5.0-minute line stays a SPEC limit -- it never gets drawn as a control " +
    "limit. Control limits say what the process is doing; spec limits say what the customer needs; " +
    "\"out of control\" and \"out of spec\" are different sentences, and this chart only speaks the first.",
  whenNotTo:
    "The classic misuse is spec limits used as control limits -- every signal read is then wrong, and the " +
    "item invalidates. Close behind: rubber limits, recalculated on every update until a real shift the " +
    "chart had caught is refit into \"normal\" -- the quiet erase is the invalidating form. Defects-" +
    "counted-per-unit forced through the p route is EXIT-11's refusal, not a judgment call. And a chart " +
    "that is never armed protects nothing: a missing signal log because charting never ran grades as Fail, " +
    "not as a thin pass.",
  fieldGuidance: [
    {
      field: "Data shape",
      good: "The honest structure of the data: continuous for measured values (handoff minutes), attribute for pass/fail units.",
      bad: "Whatever keeps the familiar chart. (the selector is printed so the route can be checked, not vibes)",
    },
    {
      field: "Defectives or defects? (attribute only)",
      good: "Defectives when whole units pass or fail; defects declared as defects even though that routes to EXIT-11 -- counts per unit are not proportions.",
      bad: "Calling defect counts \"defectives\" to dodge the exit. (the p chart computes, and every limit on it is wrong)",
    },
    {
      field: "Metric monitored",
      good: "The primary CTQ -- handoff_minutes, the charter metric itself -- or a proxy with the link explained.",
      bad: "A convenient proxy with no stated link to the CTQ. (monitoring drift: the chart ends up guarding something nobody promised)",
    },
    {
      field: "Control chart data",
      good: "The post-improvement period in true time order, 20+ points, itself stable in the limit-setting window before you freeze.",
      bad: "Freezing from a short or still-shifting window. (bad limits preserved are bad alarms forever -- short of the floor, the chart runs diagnostically: plotted, no frozen limits, no \"sustained control\" claim)",
    },
    {
      field: "Freeze limits / Reason for recalculating",
      good: "Frozen once, recalculated only on a deliberate, logged decision -- e.g. a further proven process change moved the center for good, reason recorded.",
      bad: "Recalculating because recent points \"look different.\" (that difference is exactly what the frozen limits exist to catch)",
    },
    {
      field: "Start monitoring + cadence",
      good: "Armed as soon as limits freeze, with a cadence note that matches how the process runs -- daily peak entry at the Coffee Bar.",
      bad: "Configured but never armed. (never-armed is not a quiet success; it is the missing signal log the rubric fails)",
    },
    {
      field: "Signal acknowledgments + response note",
      good: "Every fired signal gets a read in your own words, in process terms -- \"8 points above center starting the week the backup grinder went in\" -- and the OCAP response recorded against it. A signal asks you to look at the process, not to twist a knob.",
      bad: "Adjusting the process on common-cause wiggle (tampering -- it adds variation), or the same signal firing repeatedly into silence.",
    },
  ],
  whatGoodLooksLike: [
    "The chart family matches the data type through the printed selector -- I-MR for continuous, p for " +
      "attribute with the denominator handled per subgroup -- and it monitors the primary CTQ, not an " +
      "unexplained proxy.",
    "Limits are computed by the tool from a post-improvement window that is itself demonstrated stable: " +
      "20+ points, no default-rule signal in the limit-setting window; short of that the chart runs " +
      "diagnostically and no sustained-control claim is made.",
    "Once established, limits are frozen -- recalculated only on a deliberate, logged decision, never " +
      "silently refit to recent data.",
    "Control limits and spec limits stay distinct in your own language -- \"out of control\" and \"out of " +
      "spec\" are different sentences.",
    "Every fired signal gets a recorded read in your own words -- special cause vs common cause, in " +
      "process terms -- and special-cause signals trigger the OCAP response path with the investigation " +
      "recorded. A read that correctly disagrees with a wrong signal explanation is a pass and files a " +
      "suite bug.",
    "No tampering: no adjustments on common-cause variation, no repeated signal left unacknowledged.",
    "Armed and quiet beats never armed: rules active, data flowing, nothing fired is a thin but real pass " +
      "-- monitoring that never ran is the Fail.",
  ],
  commonMistakes: [
    "Using spec limits as control limits -- every signal read is then wrong, and the item invalidates.",
    "Rubber limits: recalculating on every update until the shift the chart caught is refit away -- the " +
      "quiet erase of the alarm system.",
    "Tampering: adjusting the process on common-cause variation -- the classic over-reaction, and it adds " +
      "variation instead of removing it.",
    "Switching on all four zone rules \"to be thorough\" -- roughly a 4x false-alarm increase (in-control " +
      "ARL ~370 down to ~92), then a week chasing noise; rules 2-3 are opt-in with that cost stated.",
    "Reading \"in control\" as \"meeting spec\" -- a stable process can be stably too slow; the Coffee Bar " +
      "baseline was exactly that.",
    "Declaring the process \"in control\" in the wrap-up while sustained signals sit ignored -- a false " +
      "stability claim at the exact point the project exists to protect.",
  ],
  source:
    "Method source: NIST/SEMATECH e-Handbook §6.3.1 (what control charts are), §6.3.2/§6.3.3 (I-MR, p); " +
    "published constants tables; Western Electric rules with default = rule 1 + rule 4, zone rules 2-3 " +
    "opt-in with the false-alarm cost stated (traceability matrix VI.A.1, VI.A.3; VI.A.2 sampling-scheme " +
    "warning read from T-11). Matrix §4a: freeze floor >= 20 signal-free points; EXIT-11 for defects-per-" +
    "unit. Goldens G-imr-01, G-pchart-01, G-werules-01. Acceptance checklist: rubric R-CTL-01, R-CTL-02.",
};
