import { ARTIFACT_ID, SCHEMA_VERSION } from "./controlChartState";
import type { ControlChartState } from "./controlChartState";
import type { ControlChartArtifact, PSubgroup } from "../../api/types";

/** Assembles the full T-21 save body. Frozen-state fields (imr_baseline/
 * p_baseline/frozen_at/...) are carried forward verbatim from the last
 * loaded server artifact whenever this save isn't itself a freeze/
 * recalculate action -- "frozen means frozen" (control_chart.py's module
 * docstring): only the engine ever overwrites them, and only on an
 * explicit action, never as a side effect of e.g. toggling armed state. */
export function buildControlChartBody(
  state: ControlChartState,
  resolvedImrValues: number[] | null,
  resolvedSubgroups: PSubgroup[] | null,
  serverArtifact: ControlChartArtifact | null,
  nowIso: string,
  action: { freeze?: boolean; recalculateReason?: string },
): Record<string, unknown> {
  const trimmedReason = action.recalculateReason?.trim() ?? "";
  const attempting = Boolean(action.freeze) || trimmedReason !== "";
  const chartType = state.dataShape === "continuous" ? "imr" : "p";

  return {
    schema_version: SCHEMA_VERSION, artifact_id: ARTIFACT_ID, tool_id: "T-21",
    created_at: serverArtifact?.created_at ?? nowIso, updated_at: nowIso,
    chart_type: chartType,
    metric_ref: state.metricRef.trim(),
    selector: {
      data_shape: state.dataShape,
      defectives_or_defects: state.dataShape === "attribute" ? state.defectivesOrDefects || null : null,
    },
    source: state.dataShape === "continuous" && state.imrSource.mode === "dataset"
      ? { kind: "dataset", dataset_id: state.imrSource.datasetId || null, column: state.imrSource.column || null }
      : { kind: "manual" },
    imr_values: chartType === "imr" ? resolvedImrValues : null,
    p_subgroups: chartType === "p" ? resolvedSubgroups : null,
    // I-MR only (control_chart.py rejects either true on a p-chart) --
    // chartType === "p" forces both false regardless of stale state, the
    // same defensive move the data payload fields above already make.
    rule2_enabled: chartType === "imr" && state.rule2Enabled,
    rule3_enabled: chartType === "imr" && state.rule3Enabled,
    freeze_requested: Boolean(action.freeze),
    recalculate_reason: trimmedReason || null,
    action_at: attempting ? nowIso : null,
    frozen_at: serverArtifact?.frozen_at ?? null,
    source_dataset_hash: serverArtifact?.source_dataset_hash ?? null,
    frozen_window_values: serverArtifact?.frozen_window_values ?? null,
    frozen_window_subgroups: serverArtifact?.frozen_window_subgroups ?? null,
    imr_baseline: serverArtifact?.imr_baseline ?? null,
    p_baseline: serverArtifact?.p_baseline ?? null,
    recalculation_log: serverArtifact?.recalculation_log ?? [],
    armed: { monitoring_started: state.monitoringStarted, cadence_note: state.cadenceNote },
    acknowledgments: Object.fromEntries(
      Object.entries(state.acknowledgments).map(([key, ack]) => [
        key, { acknowledged: ack.acknowledged, response_note: ack.response_note, at: ack.acknowledged ? nowIso : null },
      ]),
    ),
  };
}

export function signalKey(ruleId: string, startIndex: number, endIndex: number, side: string): string {
  return `${ruleId}:${startIndex}:${endIndex}:${side}`;
}
