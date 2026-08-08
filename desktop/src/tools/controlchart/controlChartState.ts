import { emptyArraySource } from "../hypothesis/hypothesisFormState";
import type { ArraySourceValue } from "../hypothesis/hypothesisFormState";
import type { ControlChartArtifact, DataShape, DefectivesOrDefects, PSubgroup } from "../../api/types";

export const ARTIFACT_ID = "control-chart";
export const SCHEMA_VERSION = 1;

export interface AckState {
  acknowledged: boolean;
  response_note: string;
}

export interface ControlChartState {
  dataShape: DataShape;
  defectivesOrDefects: DefectivesOrDefects | "";
  metricRef: string;
  imrSource: ArraySourceValue;
  pSubgroupsPasteText: string; // one "label,n,defective_count" per line -- the p-chart's own paste format
  /** Western Electric zone rules 2/3, opt-in (M4 addition, matrix VI.A.1)
   * -- I-MR only; the engine rejects either true on a p-chart. Applies to
   * the live MONITORING read, not the frozen limits (control_chart.py's
   * module docstring). */
  rule2Enabled: boolean;
  rule3Enabled: boolean;
  freezeRequested: boolean;
  recalculateReason: string;
  monitoringStarted: boolean;
  cadenceNote: string;
  acknowledgments: Record<string, AckState>;
}

export function emptyControlChartState(): ControlChartState {
  return {
    dataShape: "continuous", defectivesOrDefects: "", metricRef: "",
    imrSource: emptyArraySource("Control chart data"), pSubgroupsPasteText: "",
    rule2Enabled: false, rule3Enabled: false,
    freezeRequested: false, recalculateReason: "", monitoringStarted: false, cadenceNote: "",
    acknowledgments: {},
  };
}

export function controlChartStateFromArtifact(a: ControlChartArtifact): ControlChartState {
  return {
    dataShape: a.selector.data_shape, defectivesOrDefects: a.selector.defectives_or_defects ?? "",
    metricRef: a.metric_ref,
    imrSource: a.chart_type === "imr" && a.imr_values
      ? { ...emptyArraySource("Control chart data"), mode: "paste", pasteText: a.imr_values.join(", ") }
      : emptyArraySource("Control chart data"),
    pSubgroupsPasteText: a.chart_type === "p" && a.p_subgroups ? subgroupsToText(a.p_subgroups) : "",
    rule2Enabled: a.rule2_enabled, rule3Enabled: a.rule3_enabled,
    freezeRequested: false, recalculateReason: "",
    monitoringStarted: a.armed.monitoring_started, cadenceNote: a.armed.cadence_note,
    acknowledgments: Object.fromEntries(Object.entries(a.acknowledgments).map(([k, v]) => [k, { acknowledged: v.acknowledged, response_note: v.response_note }])),
  };
}

export function subgroupsToText(subgroups: PSubgroup[]): string {
  return subgroups.map((s) => `${s.label},${s.n},${s.defective_count}`).join("\n");
}

/** Parses the p-chart's own "label,n,defective_count" paste format --
 * one subgroup per line, blank lines and unparsable rows dropped rather
 * than silently defaulting to zero. */
export function parseSubgroupsText(text: string): PSubgroup[] {
  const subgroups: PSubgroup[] = [];
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const parts = trimmed.split(",").map((p) => p.trim());
    if (parts.length !== 3) continue;
    const [label, nText, defectiveText] = parts;
    const n = Number(nText);
    const defective_count = Number(defectiveText);
    if (!label || !Number.isFinite(n) || !Number.isFinite(defective_count)) continue;
    subgroups.push({ label, n, defective_count });
  }
  return subgroups;
}

export function missingFields(state: ControlChartState, resolvedImrCount: number, resolvedSubgroups: PSubgroup[]): string[] {
  const missing: string[] = [];
  if (!state.metricRef.trim()) missing.push("what metric this chart monitors");
  if (state.dataShape === "attribute" && !state.defectivesOrDefects) missing.push("defectives-or-defects answer");
  if (state.dataShape === "continuous" && resolvedImrCount < 2) missing.push("at least 2 data points");
  // "defects" is refused by EXIT-11 regardless of data (matrix VI.A.3) --
  // subgroup data is only required on the "defectives" path, so the save
  // button stays enabled to let the refusal itself surface immediately.
  if (state.dataShape === "attribute" && state.defectivesOrDefects === "defectives" && resolvedSubgroups.length < 1) missing.push("at least 1 subgroup");
  return missing;
}
