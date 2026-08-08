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

export function continuousCanSave(items: ContinuousItemValue[], gaugeIncrementText: string, operator: string): boolean {
  const increment = Number(gaugeIncrementText);
  return (
    items.length > 0 &&
    operator.trim() !== "" &&
    Number.isFinite(increment) &&
    increment > 0 &&
    items.every((it) => it.item_id.trim() !== "" && it.readings.some((r) => parseReading(r) != null))
  );
}

export function attributeCanSave(items: AttributeItemValue[], operator: string): boolean {
  return items.length > 0 && operator.trim() !== "" && items.every((it) => it.item_id.trim() !== "");
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
  "multi-operator reproducibility — do different people get different readings on the same items?",
  "gauge bias — is the gauge systematically off from a known reference/standard?",
  "linearity — does bias change across the measurement range?",
  "gauge stability over time — does repeatability drift across weeks or months?",
];

export const EXIT03_ROUTES_TO =
  "A human quality engineer or certified Belt for a full Gage R&R study (multi-operator GR&R ships in v2, T-35).";
