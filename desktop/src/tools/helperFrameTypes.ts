/** The five-part helper frame content schema (PLAN §4.3), always the same
 * shape across every tool: what this is, when to (not) use it, per-field
 * guidance with a good/bad example, the acceptance checklist, and common
 * mistakes. Real content ships with each tool; everything not built yet
 * gets an honest, clearly-marked placeholder (M1 brief). */

export interface FieldGuidance {
  field: string;
  good: string;
  bad: string;
}

export interface HelperFrameContent {
  toolId: string;
  whatThisIs: string;
  whenToUse: string;
  whenNotTo: string;
  fieldGuidance: FieldGuidance[];
  whatGoodLooksLike: string[];
  commonMistakes: string[];
  /** Method-source citation (PLAN §6 / tier-a-done-means §1: every tool's
   * help panel cites its source) -- the traceability-matrix row's
   * method/formula source for this tool, plus its rubric item IDs. */
  source: string;
  /** True for every tool this milestone didn't write real content for. */
  isPlaceholder: boolean;
}

export function placeholderHelperContent(toolId: string, toolName: string): HelperFrameContent {
  return {
    toolId,
    whatThisIs: `PLACEHOLDER — "${toolName}" doesn't have a form in this milestone yet, so there's no real helper text to show.`,
    whenToUse: "PLACEHOLDER — ships with the tool.",
    whenNotTo: "PLACEHOLDER — ships with the tool.",
    fieldGuidance: [],
    whatGoodLooksLike: ["PLACEHOLDER — the rubric checklist for this tool ships with the tool."],
    commonMistakes: ["PLACEHOLDER — the common-mistakes list ships with the tool."],
    source: "PLACEHOLDER — the method-source citation ships with the tool.",
    isPlaceholder: true,
  };
}
