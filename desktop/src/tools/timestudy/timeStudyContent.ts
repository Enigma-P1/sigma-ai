import type { HelperFrameContent } from "../helperFrameTypes";

/** T-09 Guided Time Study / Work Sampling helper content. "What good
 * looks like" is drawn from rubric R-MEA-04 -- one source of truth, no
 * parallel checklist (tier-a-done-means §2). The outlier stance
 * (flag-and-explain, never delete) is this tool's core teaching point. */
export const timeStudyHelperContent: HelperFrameContent = {
  toolId: "T-09",
  isPlaceholder: false,
  whatThisIs:
    "A phone-as-stopwatch observation study: define the work elements first, then time repeated cycles, " +
    "splitting at each element boundary. The engine reports each element's time with its spread (mean, " +
    "median, SD, IQR) and flags outliers -- it never deletes them. An outlier is often the most informative " +
    "point you collected: the 14-minute order IS why customers walk away, not noise to trim.",
  whenToUse:
    "When the route needs timed observation: element times for the process map, or cycle data headed for the " +
    "baseline. At the Coffee Bar: order-to-handoff split into take order / pull shots / steam milk / " +
    "assemble & hand off, timed across 10+ real peak cycles. The optional work-sampling mode answers a " +
    "different question -- what share of time is working vs waiting vs moving -- by tapping what's happening " +
    "at set intervals.",
  whenNotTo:
    "Not a place for recalled or averaged guesses -- if you didn't observe it, don't type it. The classic " +
    "misuse is averaging away the outliers (or deleting the slow cycles) so the number looks tidy: the " +
    "summary then describes a process that doesn't exist, and whatever it says is a wrong number by " +
    "omission. Deleting an observation without a logged reason is this tool's fail line.",
  fieldGuidance: [
    {
      field: "Element name",
      good: "\"Steam milk\" -- one distinct chunk of work per element, defined before any timing starts.",
      bad: "\"Work.\" (one catch-all element is not a study -- and elements invented mid-study make earlier cycles incomparable with later ones)",
    },
    {
      field: "Start/stop trigger",
      good: "\"Starts when the pitcher touches the wand; ends when the pitcher is set down\" -- two people would split at the same instant.",
      bad: "No trigger stated. (cycle 9's split then lands somewhere different than cycle 2's, and the spread you compute is partly your own inconsistency)",
    },
    {
      field: "Stopwatch (Start / Split / Finish)",
      good: "Split at each element boundary as it happens; finish commits the cycle to the table below.",
      bad: "Reconstructing element times afterward from memory. (recalled times cluster and flatter -- the spread is the first casualty)",
    },
    {
      field: "Cycle time cell (seconds)",
      good: "A typed correction when a split was fumbled -- with a note on that cycle saying what was fixed and why.",
      bad: "Editing a real slow time down to look typical. (that's not a correction, it's fabrication)",
    },
    {
      field: "Cycle note",
      good: "\"Cycle 7: register crashed mid-order\" -- context recorded in the moment; this is also where a flagged outlier's explanation lives.",
      bad: "Blank notes on every flagged outlier. (an unexplained outlier leaves the reader guessing whether it was the process or the stopwatch)",
    },
    {
      field: "Delete cycle",
      good: "Only for a genuinely broken observation -- you stopped the watch late and know it -- and the record says so.",
      bad: "Deleting the slow cycles. (data integrity broken; the rubric treats every downstream summary as wrong by omission)",
    },
    {
      field: "Work sampling (Working / Waiting / Moving / Other)",
      good: "Tap what is happening at fixed intervals -- every 2 minutes through the peak, whatever it shows.",
      bad: "Tapping only when something interesting happens. (interval sampling only works if the intervals are honest -- selective taps bias every share)",
    },
    {
      field: "Send an element to baseline",
      good: "Export the handoff element's cycle times once the study is saved -- T-13 reads that same dataset, nothing re-typed.",
      bad: "Typing the times into a new file for the baseline. (a re-typed copy breaks the provenance chain the suite maintains for you)",
    },
  ],
  whatGoodLooksLike: [
    "Work elements are defined before timing starts -- an element list with start/stop triggers, not " +
      "categories invented mid-study.",
    "The tool's recommended cycle count is met, or the shortfall is named on the artifact (\"6 cycles; tool " +
      "recommends 10 -- treat spread as rough\").",
    "Element times are reported with their spread -- a single observation is never presented as \"the " +
      "time.\"",
    "Outliers are flagged and either explained or visibly retained -- never silently deleted. If a cycle " +
      "was removed, the record says why.",
    "The numbers quoted downstream are the engine's computed stats (mean, median, SD, IQR) -- nothing " +
      "re-derived by hand.",
  ],
  commonMistakes: [
    "Timing first, defining elements later -- the categories end up invented mid-study and the cycles " +
      "don't compare.",
    "Deleting or trimming outliers to tidy the spread -- the fail line of this tool, and it throws away " +
      "the most informative data you have.",
    "One or two cycles presented as \"the time\" with no spread and no caveat.",
    "Re-cutting elements mid-study without a restart note, so half the cycles measured one thing and half " +
      "another.",
    "Flagged outliers left unexplained and then quietly ignored in the summary narrative.",
  ],
  source:
    "Method source (traceability matrix III.D.3): standard time-study / work-sampling practice per the LSS " +
    "curriculum; element statistics (mean, median, SD, IQR) per NIST/SEMATECH §1.3.5, computed by the " +
    "engine, never on screen. Acceptance checklist: rubric R-MEA-04.",
};
