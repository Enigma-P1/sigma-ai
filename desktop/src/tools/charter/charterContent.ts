import type { HelperFrameContent } from "../helperFrameTypes";

/** Real helper content for T-03 (PLAN §4.3's own worked example + the
 * prescore rubric in prescore/charter.py). The second of the two proof
 * screens this milestone writes real content for. */
export const charterHelperContent: HelperFrameContent = {
  toolId: "T-03",
  isPlaceholder: false,
  whatThisIs:
    "The charter turns a picked project into a written commitment: what the problem is, how you'll know it's fixed, " +
    "who's on the hook, and what's in and out of scope. It's the document everything downstream points back to.",
  whenToUse: "Right after the Project Picker clears -- before any process mapping or data collection.",
  whenNotTo:
    "Don't write it as a to-do list of fixes. A charter describes the problem and the goal, not the solution -- if " +
    "you already know exactly what to change, you probably haven't looked hard enough yet.",
  fieldGuidance: [
    {
      field: "Problem statement",
      good: "Line 2 scrap rate averaged 6.2% in Q2, costing ~$40k.",
      bad: "Operators need retraining. (that's a solution, not a problem statement)",
    },
    {
      field: "SMART goal",
      good: "Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026.",
      bad: "Improve scrap rate. (no baseline, no target, no date)",
    },
    {
      field: "Process owner",
      good: "Maria Ortiz, Line-2 supervisor.",
      bad: "TBD / Management / the team. (nobody is actually on the hook)",
    },
    {
      field: "Consequential metrics",
      good: "Line-2 throughput. (so a scrap fix that tanks output gets caught)",
      bad: "(left blank -- a fix could quietly break something else and nobody would notice)",
    },
  ],
  whatGoodLooksLike: [
    "The problem statement and goal describe what's wrong and by how much -- no causes, no solutions, no blame.",
    "The magnitude has a number, a unit, and a period, so anyone can tell whether it's actually improving.",
    "The process owner is a real, named person -- not a placeholder like \"TBD\" or \"management.\"",
    "At least one consequential (guardrail) metric is named, so an improvement can't quietly break something else.",
    "The key-risks block has at least one real risk with a likelihood, impact, mitigation, and owner.",
  ],
  commonMistakes: [
    "Writing the problem statement as a solution (\"train the operators\") instead of an observed fact.",
    "A goal with no baseline or date, so nobody can tell later whether it worked.",
    "A placeholder owner name because the real owner hasn't been asked yet.",
    "Scope in/out left vague, so the project quietly grows during Measure.",
    "An empty risk block, or risks copied in without a named owner or mitigation.",
  ],
};
