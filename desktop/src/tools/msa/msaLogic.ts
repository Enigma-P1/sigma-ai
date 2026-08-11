import type { AttributeJudgmentRow, ContinuousItemRow, MsaArtifact, MsaVerdict } from "../../api/types";
import type { VerdictTone } from "../../design/components";

/** Fixed at the matrix §4a floor (>=2 repeat readings per item) -- a
 * simple two-column grid rather than a configurable repeat count, kept
 * deliberately narrow for v1 (the engine model itself supports more). */
export const MSA_REPEATS_PER_ITEM = 2;

export interface ContinuousItemValue {
  item_id: string;
  /** One string per repeat slot; "" = missing/invalid repeat (excluded
   * server-side from s_repeat and logged, never treated as zero). */
  readings: string[];
}

export interface AttributeItemValue {
  item_id: string;
  rater_a: boolean;
  rater_b: boolean;
}

export function emptyContinuousItem(index: number): ContinuousItemValue {
  return { item_id: `item-${index + 1}`, readings: Array(MSA_REPEATS_PER_ITEM).fill("") };
}

export function emptyAttributeItem(index: number): AttributeItemValue {
  return { item_id: `item-${index + 1}`, rater_a: false, rater_b: false };
}

export function parseReading(text: string): number | null {
  if (text.trim() === "") return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : null;
}

export function continuousItemsToBody(items: ContinuousItemValue[]): ContinuousItemRow[] {
  return items.map((it) => ({ item_id: it.item_id.trim(), readings: it.readings.map(parseReading) }));
}

export function attributeItemsToBody(items: AttributeItemValue[]): AttributeJudgmentRow[] {
  return items.map((it) => ({ item_id: it.item_id.trim(), rater_a: it.rater_a, rater_b: it.rater_b }));
}

export function continuousItemsFromArtifact(artifact: MsaArtifact): ContinuousItemValue[] {
  return artifact.continuous_items.map((r) => ({
    item_id: r.item_id,
    readings: r.readings.map((v) => (v == null ? "" : String(v))),
  }));
}

export function attributeItemsFromArtifact(artifact: MsaArtifact): AttributeItemValue[] {
  return artifact.attribute_items.map((r) => ({ item_id: r.item_id, rater_a: r.rater_a, rater_b: r.rater_b }));
}

/** The exact fields the Run/Save button's disabled state depends on, named
 * in plain English -- continuousCanSave below and the rendered
 * "Missing: ..." hint both read from this one list (Jordan usability fix). */
export function continuousMissingFields(items: ContinuousItemValue[], gaugeIncrementText: string, operator: string): string[] {
  const missing: string[] = [];
  if (operator.trim() === "") missing.push("operator");
  const increment = Number(gaugeIncrementText);
  if (!(Number.isFinite(increment) && increment > 0)) missing.push("gauge increment (> 0)");
  if (items.length === 0) missing.push("at least one item");
  else if (!items.every((it) => it.item_id.trim() !== "")) missing.push("every item's id");
  else if (!items.every((it) => it.readings.some((r) => parseReading(r) != null))) missing.push("at least one reading per item");
  return missing;
}

export function continuousCanSave(items: ContinuousItemValue[], gaugeIncrementText: string, operator: string): boolean {
  return continuousMissingFields(items, gaugeIncrementText, operator).length === 0;
}

export function attributeMissingFields(items: AttributeItemValue[], operator: string): string[] {
  const missing: string[] = [];
  if (operator.trim() === "") missing.push("operator");
  if (items.length === 0) missing.push("at least one item");
  else if (!items.every((it) => it.item_id.trim() !== "")) missing.push("every item's id");
  return missing;
}

export function attributeCanSave(items: AttributeItemValue[], operator: string): boolean {
  return attributeMissingFields(items, operator).length === 0;
}

export function toneForVerdict(verdict: MsaVerdict): VerdictTone {
  switch (verdict) {
    case "acceptable":
      return "pass";
    case "marginal":
      return "flag";
    case "fail":
      return "fail";
  }
}

export function verdictHeadline(verdict: MsaVerdict, dataType: "continuous" | "attribute"): string {
  const noun = dataType === "continuous" ? "repeatability%" : "attribute agreement (kappa)";
  switch (verdict) {
    case "acceptable":
      return `Acceptable — ${noun} is within the frozen band.`;
    case "marginal":
      return `Marginal — ${noun} is inside the lenient-but-usable band.`;
    case "fail":
      return `Fail — ${noun} is outside the acceptable range. Stop and fix the measurement first.`;
  }
}

export function fmtPercent(n: number, digits = 2): string {
  return `${n.toFixed(digits)}%`;
}

export function fmt(n: number, digits = 3): string {
  return n.toFixed(digits);
}

export const EXIT03_EXAMPLES: string[] = [
  "gauge bias — is the gauge systematically off from a known reference/standard?",
  "linearity — does bias change across the measurement range?",
  "gauge stability over time — does repeatability drift across weeks or months?",
];

/** Multi-operator reproducibility used to head the list above with "ships
 * in v2" beside it. T-35 now runs that study, so it is no longer an exit
 * -- it is a screen in this app, and the route says which one. Bias,
 * linearity and stability are still genuinely out of scope. */
export const EXIT03_ROUTES_TO =
  "For multi-operator reproducibility, run T-35 (Gage R&R, full crossed study) — it is in this app, in Measure. " +
  "For bias, linearity or stability over time, a human quality engineer or certified Belt: this suite does not " +
  "run those studies.";
