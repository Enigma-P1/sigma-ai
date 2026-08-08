import { parseNumberList, toFloatOrNull } from "./hypothesisParsing";
import { ensureMinGroups } from "./hypothesisFormState";
import type { ArraySourceValue, HypothesisFormState } from "./hypothesisFormState";

/** True when this array source has nothing usable yet -- paste text with
 * no parseable numbers, or a dataset pick that isn't finished (no column,
 * or a split column chosen with no split value yet). */
export function arraySourceIncomplete(s: ArraySourceValue): boolean {
  if (s.mode === "paste") return parseNumberList(s.pasteText).length === 0;
  if (!s.datasetId || !s.column) return true;
  return s.splitColumn !== "" && s.splitValue === "";
}

/** The exact fields Preview/Run's disabled state depends on, named in
 * plain English (Jordan usability fix: MissingHint reads this same list --
 * see msaLogic.ts's continuousMissingFields for the established pattern). */
export function missingFieldsForPreview(state: HypothesisFormState): string[] {
  const missing: string[] = [];
  if (state.questionText.trim() === "") missing.push("your question, in your own words");

  switch (state.comparisonType) {
    case "two_independent": {
      const [a, b] = state.groups;
      if (!a || arraySourceIncomplete(a)) missing.push(`${state.groups[0]?.label || "group A"} values`);
      if (!b || arraySourceIncomplete(b)) missing.push(`${state.groups[1]?.label || "group B"} values`);
      break;
    }
    case "multi_group": {
      const groups = ensureMinGroups(state.groups, 3);
      groups.forEach((g, i) => {
        if (arraySourceIncomplete(g)) missing.push(`${g.label || `group ${i + 1}`} values`);
      });
      break;
    }
    case "paired":
      if (arraySourceIncomplete(state.pairedBefore)) missing.push(`${state.pairedBefore.label || "before"} values`);
      if (arraySourceIncomplete(state.pairedAfter)) missing.push(`${state.pairedAfter.label || "after"} values`);
      break;
    case "one_sample_vs_target":
      if (arraySourceIncomplete(state.sample)) missing.push(`${state.sample.label || "sample"} values`);
      if (toFloatOrNull(state.targetText) == null) missing.push("target value");
      break;
    case "proportions":
      state.proportionGroups.forEach((g) => {
        if (toFloatOrNull(g.successesText) == null) missing.push(`${g.label} successes`);
        if (toFloatOrNull(g.nText) == null) missing.push(`${g.label} sample size (n)`);
      });
      if (state.proportionGroups.length === 1) {
        const t = toFloatOrNull(state.proportionTargetText);
        if (t == null || t < 0 || t > 1) missing.push("target proportion (0-1)");
      }
      break;
    case "association_categorical":
      for (const row of state.contingency.cells) {
        for (const cell of row) {
          if (toFloatOrNull(cell) == null) {
            missing.push("every cell in the counts table");
            break;
          }
        }
      }
      break;
    case "relationship_continuous":
      break; // always exits (EXIT-15) regardless of data -- nothing else required
  }
  return missing;
}

export function missingFieldsForReflection(reflection: string): string[] {
  return reflection.trim() === "" ? ["what this result means for your project"] : [];
}
