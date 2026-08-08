import type { HelperFrameContent } from "../helperFrameTypes";

/** T-14 Pareto / Histogram / Run Chart + Scatter / Box helper content.
 * "What good looks like" is drawn from rubric R-MEA-10 (descriptive and
 * graphical reads) -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). Scatter is visual-only in v1 by design (matrix
 * correction A-2; EXIT-15 names the deferral). */
export const chartSetHelperContent: HelperFrameContent = {
  toolId: "T-14",
  isPlaceholder: false,
  whatThisIs:
    "Five ways of looking at a saved dataset, each answering a different question: histogram -- what shape " +
    "and spread? run chart -- what happened over time? Pareto -- which few categories carry most of the " +
    "pain? box plot -- how do groups compare? scatter -- do two measures move together? The verdict " +
    "headlines are the engine's; the graded work is your read of each chart in your own words.",
  whenToUse:
    "As soon as a dataset exists, and alongside the baseline. At the Coffee Bar: a histogram of " +
    "handoff_minutes with the 5.0 USL drawn on it, a run chart across the collection mornings, and a Pareto " +
    "of remake reasons straight from the check-sheet export -- three views, three different facts about the " +
    "same problem.",
  whenNotTo:
    "The classic misuse is measuring what's easy instead of what the customer feels: a wall of charts about " +
    "espresso temperature and bean weight when the CTQ is handoff time. A beautiful chart of a convenient " +
    "metric is not evidence about the customer's metric. Second misuse, specific to scatter: reading a " +
    "correlation coefficient off it. v1 draws the picture only -- no fitted line, no r -- because quantified " +
    "correlation/regression is EXIT-15 territory (ships v1.1); describe the pattern you see, don't invent " +
    "the number.",
  fieldGuidance: [
    {
      field: "Dataset",
      good: "The saved import or check-sheet/time-study export -- the same fingerprinted dataset the baseline reads.",
      bad: "A freshly re-typed file \"just for the charts.\" (charts and baseline must describe the same data, or the story splits)",
    },
    {
      field: "Histogram -- column + USL/LSL",
      good: "handoff_minutes with USL 5.0 drawn on it: the shape, the spread, and how much of the process sits past the customer's limit, in one look.",
      bad: "Decorative limits typed from memory that match nothing in the charter. (a wrong line teaches a wrong conclusion)",
    },
    {
      field: "Run chart -- column",
      good: "handoff_minutes in collection order -- the view that shows drift, shifts, and runs the histogram flattens away.",
      bad: "Data that was sorted or alphabetized upstream. (order is the whole point of this chart; destroyed order makes the time story meaningless)",
    },
    {
      field: "Pareto -- category column",
      good: "remake_reason from the check-sheet export -- the vital few named to the 80% line (\"wrong milk + misheard order = 78% of remakes\").",
      bad: "Narrating a vital few when the bars are nearly flat. (a flat Pareto is a real finding -- it says stratify differently or fix broadly -- and pretending otherwise misdirects Analyze)",
    },
    {
      field: "Scatter -- X and Y columns",
      good: "orders_in_queue vs handoff_minutes, read as a pattern in plain words: \"handoff time climbs as the queue grows.\"",
      bad: "\"Strong correlation, r about 0.8.\" (v1 computes no r on purpose -- EXIT-15; a claimed coefficient is an invented number)",
    },
    {
      field: "Box plot -- value column + group by",
      good: "handoff_minutes grouped by register vs mobile -- compare medians, boxes (IQR), and whiskers to see if one stream runs slower or wilder.",
      bad: "Reading a 3-orders-per-group comparison as decisive. (tiny groups make wide, unstable boxes -- say the n before saying the difference)",
    },
  ],
  whatGoodLooksLike: [
    "The charts the data shape calls for exist: histogram for shape, run chart for time behavior, Pareto " +
      "where categorical defect data exists, box and scatter where the tool offers them.",
    "Each chart is read correctly in your own words, graded against the data pattern itself: the vital few " +
      "named from the Pareto (or their absence admitted when the bars are flat), shape and spread described " +
      "from the histogram, drift/shift/runs noted from the run chart.",
    "A read that correctly disagrees with a wrong verdict headline is a pass -- and a suite bug to report. " +
      "Agreeing with the headline earns nothing by itself; the grade is on your read.",
    "Center and spread are quoted as the computed mean/median and SD/IQR -- never re-derived by hand.",
  ],
  commonMistakes: [
    "Charts exist but the narrative never touches them -- unread charts are decoration, not analysis.",
    "A flat Pareto narrated as if a vital few existed, because the method says there should be one.",
    "Reading a trend into a run chart's ordinary wiggle -- or missing a real shift because no one looked.",
    "Quoting a correlation number from the scatter (v1 draws the pattern only -- EXIT-15 names why).",
    "Charting the easy metric instead of the customer's metric, and calling the wall of charts evidence.",
  ],
  source:
    "Method source (traceability matrix III.D.3, III.D.4): NIST/SEMATECH §1.3.3 (graphical techniques) and " +
    "§1.3.5 (descriptive statistics, engine-computed); Pareto per standard LSS practice with the vital-few " +
    "read to the 80% line; scatter + box added per matrix correction A-2, scatter visual-only with EXIT-15 " +
    "named. Acceptance checklist: rubric R-MEA-10.",
};
