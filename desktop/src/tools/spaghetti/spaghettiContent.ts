import type { HelperFrameContent } from "../helperFrameTypes";

/** T-07 Spaghetti Diagram helper content. "What good looks like" is drawn
 * from rubric R-MEA-03 -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). Applicability note: R-MEA-03 grades this tool
 * only when the problem has a movement/layout component. */
export const spaghettiHelperContent: HelperFrameContent = {
  toolId: "T-07",
  isPlaceholder: false,
  whatThisIs:
    "A trace of the actual walking: upload the floor plan, draw one line of known real length to calibrate " +
    "the scale, then trace each trip you observe. The engine turns your traced lines into numbers -- distance " +
    "per trip, walk time, crossings, and daily travel burden (distance x how often the trip happens). The " +
    "numbers are trustworthy because they are geometry on the lines you drew, at the scale you calibrated: " +
    "nothing on this screen is eyeballed or hand-computed, so they are exactly as good as your calibration " +
    "and your trip counts -- which is why both come from measurement, not memory.",
  whenToUse:
    "When the problem has a movement or layout component -- people walking to fetch, deliver, or restock. At " +
    "the Coffee Bar: the barista's trips from the espresso station to the backroom fridge during the peak. " +
    "Trace what you watch happen, then use the current/proposed modes to test a layout change with delta " +
    "metrics instead of opinions.",
  whenNotTo:
    "If nobody moves, skip it and record why -- a project with no movement component honestly has no " +
    "spaghetti diagram (it grades N/A, not missing). The classic misuse is tracing trips from imagination at " +
    "a desk: a travel-burden number with an invented frequency is a wrong number wearing a diagram, and the " +
    "rubric fails it the moment it's used as baseline evidence.",
  fieldGuidance: [
    {
      field: "Upload a floor plan",
      good: "The bar's floor plan, or a photo of a paper sketch -- anything with at least one feature whose real length you know (the 6 m front counter).",
      bad: "A tight crop with nothing measurable in it. (with no known length in the image, calibration is a guess and every distance inherits it)",
    },
    {
      field: "Calibration -- real length + unit",
      good: "Draw the line along the front counter and enter 6 meters, from the tape measure. The longer the known line, the smaller any pixel error matters.",
      bad: "\"Roughly 2 meters,\" guessed. (calibration is the exchange rate for every number this tool prints -- a guessed rate makes all of them guesses)",
    },
    {
      field: "Layout mode (Current / Proposed)",
      good: "Current for everything you observe today; Proposed only for the redesigned routes you want the delta table to compare.",
      bad: "Tracing the hoped-for improved path into Current. (that quietly builds the fiction the as-is rule exists to prevent)",
    },
    {
      field: "Operator",
      good: "\"Marcus -- bar barista,\" one entry per person or role whose movement you trace.",
      bad: "Leaving \"Operator 1\" placeholder names in place. (the prescore flags them -- a trace nobody can attribute is a trace nobody can re-check)",
    },
    {
      field: "Trip label",
      good: "\"Espresso station to backroom fridge (milk restock)\" -- names both ends and the purpose.",
      bad: "\"Trip 3.\" (when the burden table says trip 3 dominates, nobody will know what to fix)",
    },
    {
      field: "Frequency (trips/day)",
      good: "12 -- counted: 4 restock trips in the 3-hour June 12 watch, scaled to the day and said so.",
      bad: "A number that makes the burden look impressive. (frequency multiplies straight into the daily burden -- an invented frequency is the fail line of this tool)",
    },
    {
      field: "Walk speed override (units/min)",
      good: "Left blank -- the engine uses its cited default (84 m/min). Override only with a pace you actually timed.",
      bad: "A hand-picked slow speed to inflate the minutes. (the distance is measured; don't launder opinion in through the speed)",
    },
    {
      field: "Observation window -- when / duration / shift",
      good: "\"June 12 2026\" / \"3 hours (7:00-10:00 peak)\" / \"morning\" -- so a reader can judge whether the window was representative.",
      bad: "Left empty. (one unstated afternoon of tracing can misrepresent a morning-peak problem completely)",
    },
    {
      field: "Heatmap toggle",
      good: "Use it to spot the hot corridor when you present -- line width scales with frequency, display only.",
      bad: "Citing \"the heatmap\" as evidence. (the evidence is the routes list's computed numbers; the heatmap just makes them visible)",
    },
  ],
  whatGoodLooksLike: [
    "The floor plan is calibrated by a drawn known-length line, and that real length is stated (\"the 6 m " +
      "front counter\") -- not guessed.",
    "Routes are traced per operator or trip type from an actual observation -- trips counted, not imagined.",
    "The computed metrics are read and used: distance per trip, trip count, and daily travel burden " +
      "(distance x frequency) quoted where the burden matters to the story.",
    "The observation window is stated: when, how long, which shift.",
    "Every number quoted comes from the engine's metrics on the traced routes -- no hand-measured or " +
      "eyeballed distances anywhere.",
  ],
  commonMistakes: [
    "Tracing one trip and presenting it as typical -- one observation is an anecdote, not a burden.",
    "A guessed calibration length, or a tiny calibration line so every pixel of error scales up.",
    "Frequencies invented at a desk instead of counted at the process.",
    "No observation window stated, so nobody can tell a peak trace from a quiet-afternoon trace.",
    "Letting the heatmap and before/after flash substitute for saying what was actually observed, when, " +
      "and how often.",
  ],
  source:
    "Method source (traceability matrix I.B.1): standard lean spaghetti-diagram practice; the math is " +
    "elementary geometry -- scale calibration from one known length, path length, distance x frequency -- " +
    "computed by the engine with provenance, walk time from a cited default speed (84 m/min, about 1.4 m/s) " +
    "unless you override it with a measured pace. Acceptance checklist: rubric R-MEA-03.",
};
