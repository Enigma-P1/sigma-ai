import type { HelperFrameContent } from "../helperFrameTypes";

/** T-10 Yield Calculator helper content. "What good looks like" restates
 * the rubric item that grades this tool -- R-MEA-09 (capability, yield,
 * and sigma reported honestly), the T-10 half -- one source of truth, no
 * parallel checklist (tier-a-done-means §2). */
export const yieldCalcHelperContent: HelperFrameContent = {
  toolId: "T-10",
  isPlaceholder: false,
  whatThisIs:
    "The counter for the hidden factory. Final yield asks \"did a good unit eventually come out?\" -- and " +
    "rework makes that number a flatterer, because a unit that failed, looped back, and shipped counts the " +
    "same as one built right. First-pass yield asks the harder question per step: how many came through " +
    "RIGHT THE FIRST TIME, no rework, no re-do. Rolled throughput yield (RTY) multiplies the steps' " +
    "first-pass yields into the odds one unit clears the WHOLE line untouched. The gap between final " +
    "yield and RTY is the rework you are paying for but not seeing. The DPMO block converts defect " +
    "counts into defects-per-million-opportunities and a sigma level -- every number engine-computed " +
    "from your counts, nothing hand-typed.",
  whenToUse:
    "Whenever the metric is counted, not measured -- defectives, remakes, errors per order -- and " +
    "whenever a multi-step process claims a healthy end-of-line yield. At the Coffee Bar: remakes ran " +
    "3.6 per 100 orders at baseline, so final yield looked near-perfect -- every customer eventually got " +
    "a drink -- while the grinder re-pull loop quietly re-made shots all morning. The re-pull is exactly " +
    "what first-pass counting catches and final yield hides. Yield here and the p-chart baseline (T-13/" +
    "T-21's attribute path) are the two halves of the attribute story the way Cpk and the I-MR chart are " +
    "for continuous data.",
  whenNotTo:
    "Not for measured quantities -- minutes, millimeters, dollars belong in T-13's continuous baseline, " +
    "where the actual distribution earns you far more information than collapsing it to pass/fail. Not " +
    "for guessing: every count here should trace to a real tally (T-08's check sheet is the natural " +
    "feeder), not a recalled impression. And RTY is not for parallel or branching flows -- the product-" +
    "of-FPYs math assumes every unit passes through every step in order, which is why the tool makes " +
    "you declare the steps are in series before it will roll them up.",
  fieldGuidance: [
    {
      field: "Step name",
      good: "The real work step as the process map names it -- \"pull shots\", \"steam milk\" -- so the weakest FPY points at a place someone can stand.",
      bad: "A department or a person. (yield problems live in steps; naming a team turns a count into an accusation)",
    },
    {
      field: "Units entering",
      good: "The count that actually arrived at this step in the window you tallied -- real lines rework and scrap between steps, so this is a counted number, not the previous step's output copied down.",
      bad: "An assumed carry-forward from the step before. (if you didn't count it, the FPY under it is decoration)",
    },
    {
      field: "First-pass-correct units",
      good: "Units right THE FIRST TIME -- no rework, no re-do, no touch-up. A re-pulled shot that ended in a shipped drink is not first-pass-correct.",
      bad: "Units that eventually shipped. (that is final yield wearing FPY's name -- the exact flattery this tool exists to remove, rubric R-MEA-09 #2)",
    },
    {
      field: "Are these steps in series?",
      good: "Answered honestly: yes only if every unit passes through every step in order. RTY is only computed under that declaration.",
      bad: "Yes because the rollup looks better with more steps. (parallel branches multiplied as if serial produce a fiction -- the tool refuses RTY rather than compute it wrong)",
    },
    {
      field: "Defects (DPMO block)",
      good: "Defect COUNT from a real tally over a stated window -- and one defective unit can carry several defects, which is why this is its own number.",
      bad: "A rate someone remembers, converted back into a count. (the tally is the evidence; memory is not a tally)",
    },
    {
      field: "Units (DPMO block)",
      good: "How many units were inspected in that same window -- the denominator the defects were actually found in.",
      bad: "Total production for the month when only Tuesday was inspected. (mismatch the windows and DPMO means nothing)",
    },
    {
      field: "Opportunities per unit",
      good: "1 unless you can name each distinct, checkable way a unit can be defective -- and the count stays the same for every unit and every future re-run.",
      bad: "A generous count because more opportunities means a smaller DPMO. (this is the classic sigma-flattering game, and the pre-score is built to catch it)",
    },
    {
      field: "What are the extra opportunities?",
      good: "The actual list, named: \"wrong drink, wrong size, wrong milk -- 3 checkable opportunities per order.\" If you can't list them, the count is 1.",
      bad: "\"Various\" or \"many\". (a placeholder word clears a form field but not the pre-score -- naming nothing while counting something is the tell)",
    },
    {
      field: "Apply the 1.5σ shift convention?",
      good: "Left on unless you are comparing against a source that reports unshifted sigma -- and either way the result carries its label, because a sigma level without its convention named is ambiguous by a whole 1.5σ.",
      bad: "Toggled to whichever setting produces the bigger number. (both conventions are legitimate; an unlabeled one is not -- rubric R-MEA-09 #4)",
    },
  ],
  whatGoodLooksLike: [
    "The right family for the data: counted defectives and remakes live here and on the p-chart path; " +
      "measured minutes and millimeters live in T-13's continuous baseline -- and your summary says which " +
      "family you're in and why.",
    "Rework is COUNTED: when rework exists anywhere in the process, RTY -- not the flattering final-yield " +
      "number -- is what your narrative quotes, and the gap between the two is named as the hidden factory " +
      "(rubric R-MEA-09 #2).",
    "Every count traces to a real tally over a stated window -- units entering, first-pass-correct, " +
      "defects, and inspected units all from the same collection the check sheet recorded.",
    "The sigma level is reported with its convention named -- \"4.0 with the 1.5σ shift applied\" -- exactly " +
      "as the tool prints it, never trimmed to a bare number in your own write-up (R-MEA-09 #4).",
    "Opportunities per unit is 1, or it is a short named list that would give the same count on any unit " +
      "on any day -- and the justification says what the list is.",
    "The yield number produced here is the same number, same units, same definition, that the charter's " +
      "metric and the baseline quote -- one number, one source (R-MEA-09 #5).",
  ],
  commonMistakes: [
    "Quoting final yield where first-pass yield is the question -- a unit that failed, was reworked, and " +
      "shipped is a cost, not a success, and final yield books it as a success.",
    "Copying each step's units-entering from the previous step's output instead of counting -- real lines " +
      "scrap and rework between steps, and an uncounted denominator makes the FPY under it fiction.",
    "Rolling parallel or branching steps into RTY as if they were serial -- the product-of-FPYs math " +
      "assumes every unit sees every step, and the declaration exists so that assumption is yours, not the tool's.",
    "Inflating opportunities per unit to shrink DPMO -- more \"opportunities\" flatter sigma without a " +
      "single unit improving; if you can't name each opportunity, the count is 1.",
    "Reporting sigma with no shift label -- 4.0 shifted and 4.0 unshifted are different claims by a factor " +
      "of ~30x in defect rate, and an unlabeled number lets the reader pick the wrong one.",
    "Building the yield story from remembered rates instead of tallies -- the check sheet feeds this tool; " +
      "impressions don't.",
  ],
  source:
    "Method source: standard FPY/RTY/DPU/DPMO definitions, cross-checked against DMAIC.io and Qualica " +
    "worksheet conventions (traceability matrix II.E.1; attribute capability path §3a 2.4.3 with T-13/" +
    "T-21); per-step FPY as the direct observed ratio (first-pass-correct / units entering, computed from " +
    "counts, not a modeled estimate -- rubric R-MEA-09 #2); sigma level via the published DPMO table rows " +
    "the engine's reference tests pin (6210 DPMO = 4.0 with the 1.5σ shift). Golden G-yield-01. Acceptance " +
    "checklist: rubric R-MEA-09.",
};
