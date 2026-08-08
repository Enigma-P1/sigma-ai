import { emptyArraySource } from "../hypothesis/hypothesisFormState";
import type { ArraySourceValue } from "../hypothesis/hypothesisFormState";
import { emptyConfounderChecklist } from "../pilotplan/pilotPlanLogic";
import type { NextCauseRef, PilotConfounderChecklist, PilotDeclaredPackage, PilotDirection, ProofArtifact } from "../../api/types";

export const ARTIFACT_ID = "proof";
export const SCHEMA_VERSION = 1;

export interface ProofState {
  pilotRef: string;
  metricRef: string;
  operationalDefinitionRef: string;
  measurementSystemRef: string;
  uslText: string;
  lslText: string;
  before: ArraySourceValue;
  after: ArraySourceValue;
  thresholdValue: string;
  thresholdDirection: PilotDirection;
  confounders: PilotConfounderChecklist;
  guardrailMetricRef: string;
  guardrailDirection: PilotDirection;
  guardrailBeforeText: string;
  guardrailAfterText: string;
  charterRef: string;
  charterBaselineText: string;
  charterGoalText: string;
  charterGoalDirection: PilotDirection;
  nextCauseRef: NextCauseRef | null;
  /** Echoed from the linked T-19 pilot's own declared_package, when it
   * declared one (rubric R-IMP-02's carve-out) -- read-only here, never
   * hand-edited: usePilotPlanForm.ts's pilot-loading effect is the only
   * writer, same "echoed by ref" contract as nextCauseRef/confounders. */
  declaredPackage: PilotDeclaredPackage | null;
}

export function emptyProofState(): ProofState {
  return {
    pilotRef: "", metricRef: "", operationalDefinitionRef: "", measurementSystemRef: "",
    uslText: "", lslText: "",
    before: emptyArraySource("Before"), after: emptyArraySource("After"),
    thresholdValue: "", thresholdDirection: "lower_is_better",
    confounders: emptyConfounderChecklist(),
    guardrailMetricRef: "", guardrailDirection: "higher_is_better", guardrailBeforeText: "", guardrailAfterText: "",
    charterRef: "", charterBaselineText: "", charterGoalText: "", charterGoalDirection: "lower_is_better",
    nextCauseRef: null,
    declaredPackage: null,
  };
}

export function proofStateFromArtifact(a: ProofArtifact): ProofState {
  return {
    pilotRef: a.pilot_ref, metricRef: a.metric_ref,
    operationalDefinitionRef: a.operational_definition_ref, measurementSystemRef: a.measurement_system_ref,
    uslText: a.usl != null ? String(a.usl) : "", lslText: a.lsl != null ? String(a.lsl) : "",
    before: { ...emptyArraySource("Before"), mode: "paste", pasteText: a.before.values.join(", ") },
    after: { ...emptyArraySource("After"), mode: "paste", pasteText: a.after.values.join(", ") },
    thresholdValue: String(a.declared_threshold.value), thresholdDirection: a.declared_threshold.direction,
    confounders: a.confounders,
    guardrailMetricRef: a.guardrails[0]?.metric_ref ?? "", guardrailDirection: a.guardrails[0]?.direction ?? "higher_is_better",
    guardrailBeforeText: a.guardrails[0] ? String(a.guardrails[0].before_value) : "",
    guardrailAfterText: a.guardrails[0] ? String(a.guardrails[0].after_value) : "",
    charterRef: a.charter_ref, charterBaselineText: String(a.charter_baseline_value),
    charterGoalText: String(a.charter_goal_value), charterGoalDirection: a.charter_goal_direction,
    nextCauseRef: a.next_cause_ref ?? null,
    declaredPackage: a.declared_package ?? null,
  };
}

export function missingFields(state: ProofState, beforeCount: number, afterCount: number): string[] {
  const missing: string[] = [];
  if (!state.pilotRef.trim()) missing.push("pilot plan reference");
  if (!state.metricRef.trim()) missing.push("metric monitored");
  if (!state.operationalDefinitionRef.trim()) missing.push("operational definition reference");
  if (!state.measurementSystemRef.trim()) missing.push("measurement system reference");
  if (beforeCount < 2) missing.push("at least 2 before-period values");
  if (afterCount < 2) missing.push("at least 2 after-period values");
  if (!state.thresholdValue.trim()) missing.push("the declared threshold value");
  if (!state.charterRef.trim()) missing.push("charter reference");
  if (!state.charterBaselineText.trim() || !state.charterGoalText.trim()) missing.push("charter baseline and goal values");
  return missing;
}
