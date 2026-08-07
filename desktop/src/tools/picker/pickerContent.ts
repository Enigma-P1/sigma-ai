import type { HelperFrameContent } from "../helperFrameTypes";

/** Real helper content for T-01 (PLAN §4.1/§4.2 + matrix §4a, EXIT-01). One
 * of the two proof screens this milestone writes real content for. */
export const pickerHelperContent: HelperFrameContent = {
  toolId: "T-01",
  isPlaceholder: false,
  whatThisIs:
    "Before any DMAIC work starts, this checks whether the problem you have in mind is actually a workable first " +
    "project -- not whether it's important, but whether it's scoped, measurable, and has real support behind it.",
  whenToUse: "Always, first -- before Define work begins on a new problem.",
  whenNotTo:
    "Don't skip it because the problem feels obviously important. \"Important\" and \"a good first project\" are " +
    "different questions -- boiling the ocean is the failure mode this tool exists to catch before it costs you weeks.",
  fieldGuidance: [
    {
      field: "Scope narrow",
      good: "Only line-2 scrap, not the whole plant.",
      bad: "Improve manufacturing quality. (too broad to ever finish)",
    },
    {
      field: "Measurable outcome",
      good: "Scrap % is tracked daily in the QC log.",
      bad: "We'll know it when things feel better. (nothing to measure)",
    },
    {
      field: "Data obtainable",
      good: "QC log exports to CSV weekly.",
      bad: "Someone probably has that somewhere. (no real source named)",
    },
  ],
  whatGoodLooksLike: [
    "All five criteria answered honestly, each with a specific one-line reason -- not just checked to look ready.",
    "The route matches the answers: any \"No\" means this isn't a full-DMAIC project as scoped (matrix §4a, EXIT-01).",
    "A small, low-risk fix is routed to the PDCA quick path instead of forcing full DMAIC ceremony on it.",
  ],
  commonMistakes: [
    "Answering \"Yes\" across the board to get to the next screen, rather than describing what's actually true.",
    "Picking full-DMAIC out of habit when the problem is really small enough for the PDCA quick path.",
    "Leaving the detail field generic (\"it's fine\") instead of naming the actual evidence behind the answer.",
    "Scoping to \"the whole department\" because narrowing it feels like giving something up.",
  ],
};
