import type { HelperFrameContent } from "../helperFrameTypes";

/** T-02 COPQ / Benefit Calculator helper content. "What good looks like" is
 * drawn from rubric R-DEF-05 -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). Re-run at Wrap for realized benefits (R-WRAP-02). */
export const copqHelperContent: HelperFrameContent = {
  toolId: "T-02",
  isPlaceholder: false,
  whatThisIs:
    "A guided cost-of-poor-quality worksheet: name each cost bucket the problem creates -- scrap, rework, " +
    "overtime, expediting, lost business -- and the tool computes every row (quantity x rate) and the total. " +
    "It turns the problem into dollars, the language leadership hears.",
  whenToUse:
    "Right after (or alongside) the charter, to put a computed number behind its business-impact field. " +
    "Re-run it at project wrap with post-fix numbers to report realized benefits with the same honesty.",
  whenNotTo:
    "Not a tool for inflating a business case. The classic misuse is one giant lump-sum bucket with a " +
    "hand-picked number in it -- the whole point is buckets small enough that each quantity and each rate " +
    "can be checked against a record or an admitted estimate.",
  fieldGuidance: [
    {
      field: "Category",
      good: "One row per named bucket: scrap, rework, overtime, expediting, lost business -- \"custom\" only for a cost that fits none.",
      bad: "Everything in one \"custom: general losses\" row. (a single lump sum can't be checked, so it can't be believed)",
    },
    {
      field: "Custom label",
      good: "\"Comped drinks (long-wait apologies)\" -- specific enough that a stranger knows what was counted.",
      bad: "\"Misc\" or \"other costs.\" (if you can't name it, you can't source it)",
    },
    {
      field: "Quantity",
      good: "500 units scrapped in Q2, from the scrap-log export -- a count with a source behind it.",
      bad: "A round number typed in to make the total look right. (a guess wearing a count's clothes)",
    },
    {
      field: "Rate",
      good: "$12 per unit -- material plus labor, per the cost sheet.",
      bad: "A rate that includes costs already counted in another row. (double-counting inflates the story)",
    },
    {
      field: "Amount",
      good: "Left alone: the engine computes quantity x rate on save.",
      bad: "There is nothing to type here, and that is the point -- no hand-typed totals anywhere (R-DEF-05).",
    },
    {
      field: "Period",
      good: "\"Q2 2026\" on every row -- one period, so the total means one thing.",
      bad: "\"Q2 2026\" on one row and \"per month\" on the next. (summing mixed periods produces a meaningless number)",
    },
    {
      field: "Basis note",
      good: "\"Q2 scrap log export\" or \"estimate: interviews with 3 operators\" -- where this number comes from.",
      bad: "\"Records.\" (a source with no name -- nobody can re-check the number later)",
    },
    {
      field: "This is an estimate, not a record",
      good: "Toggled on for any row with no record behind it, so estimates read differently from measured data.",
      bad: "Left off on a guessed number. (a guess presented as measurement is the failure the rubric names)",
    },
  ],
  whatGoodLooksLike: [
    "COPQ is built from named cost buckets -- scrap, rework, overtime, expediting, lost business -- each as " +
      "quantity x rate computed by the tool. No hand-typed totals anywhere.",
    "Inputs are project-real: taken from records where records exist, and labeled estimate where they don't.",
    "The charter's business-impact field equals this calculator's output -- one number, one source.",
    "Any annualization or extrapolation states its basis (\"Q2 actuals x 4\").",
    "All rows share one time period, or were converted to one before entry -- mixed periods are a prescore flag.",
  ],
  commonMistakes: [
    "A single lump-sum bucket doing all the work instead of named categories.",
    "Estimates indistinguishable from record-based figures -- the estimate flag exists so a sponsor can " +
      "weigh them differently.",
    "Rows mixing quarterly and monthly figures in one total without converting first.",
    "Double-counting: the same cost appearing in two buckets (scrapped units also counted as rework labor).",
    "Carrying a different number into the charter than the calculator computed -- the wrong-number failure " +
      "R-DEF-05 fails outright.",
  ],
  source:
    "Method source (traceability matrix II.E.1, COPQ half): standard LSS cost-of-poor-quality categories; " +
    "row arithmetic (quantity x rate, summed) is computed by the engine with provenance and cross-checked " +
    "against open implementations (DMAIC.io, Qualica templates). Acceptance checklist: rubric R-DEF-05.",
};
