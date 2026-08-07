import type { HelperFrameContent } from "../helperFrameTypes";

/** Real helper content for T-02 (PLAN §4.1's COPQ row + rubric R-DEF-05). */
export const copqHelperContent: HelperFrameContent = {
  toolId: "T-02",
  isPlaceholder: false,
  whatThisIs:
    "A guided cost-of-poor-quality worksheet -- scrap, rework, overtime, expediting, lost business -- that turns " +
    "the problem into dollars, the language leadership actually hears. The tool computes every row and the total; " +
    "you never type a total by hand.",
  whenToUse: "Right after (or alongside) the charter, to put a real number behind the business-impact field.",
  whenNotTo:
    "Don't force a single lump-sum guess into one bucket because breaking it out feels like extra work -- a wrong " +
    "number in the money story the sponsor will quote is exactly what this tool exists to prevent (rubric R-DEF-05).",
  fieldGuidance: [
    {
      field: "Quantity and rate",
      good: "500 units x $12/unit scrap, from the Q2 scrap log export.",
      bad: "A single $40,000 guess with nothing behind it.",
    },
    {
      field: "Basis note",
      good: "Q2 scrap log export -- a real record, or an estimate from a named source.",
      bad: "(left blank) -- nobody can tell later whether this was a record or a guess.",
    },
    {
      field: "Estimate flag",
      good: "Toggled Yes for a bucket with no record behind it yet, so it reads differently from measured data.",
      bad: "Left off on a guessed number, so it looks as solid as the rows that came from real records.",
    },
    {
      field: "Period",
      good: "Every row says \"Q2 2026\" -- one period, so the total means one thing.",
      bad: "Mixing \"Q2 2026\" and \"per month\" rows into one total without converting first.",
    },
  ],
  whatGoodLooksLike: [
    "Each bucket is quantity x rate, computed by the tool -- no hand-typed totals anywhere.",
    "Rows taken from real records read differently from rows marked as estimates.",
    "The charter's business-impact field ends up equal to this calculator's total -- one number, one source.",
    "All rows share one time period, or state how they were converted to a common one.",
  ],
  commonMistakes: [
    "One giant bucket instead of named categories (scrap/rework/overtime/expediting/lost business).",
    "A hand-typed total that quietly drifts from what the rows actually add up to.",
    "Estimates presented with the same confidence as record-based figures.",
    "Rows mixing quarterly and monthly figures without converting to a common period first.",
  ],
};
