import type {
  PilotChange,
  PilotComparisonDesign,
  PilotConfounderChecklist,
  PilotDirection,
  PilotInclusion,
  PilotPlanArtifact,
  PilotStatus,
} from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as solutionMatrixLogic.ts's genId. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export const PRIMARY_CHANGE_ID = "the-one-change";

export interface PilotPlanState {
  primaryChangeText: string;
  linkedSolutionId: string | null;
  linkedCauseIds: string[];
  /** Extra `changes` entries beyond the primary -- normally empty. The
   * desktop's own "+ add another change" affordance appends here so the
   * engine's EXIT-10 refusal (artifacts/pilot_plan.py) can be demonstrated
   * and then undone, exactly like a real drafting mistake would be. */
  extraChanges: PilotChange[];
  comparisonDesign: PilotComparisonDesign;
  inclusion: PilotInclusion;
  metricRef: string;
  direction: PilotDirection;
  thresholdValue: number;
  expectedRoute: string;
  rationale: string;
  falsificationLine: string;
  confounderChecklist: PilotConfounderChecklist;
  status: PilotStatus;
}

export function emptyConfounderChecklist(): PilotConfounderChecklist {
  const blank = { changed: false, note: "" };
  return { staffing: { ...blank }, season: { ...blank }, demand: { ...blank }, measurement: { ...blank }, other: { ...blank } };
}

export function emptyPilotPlanState(): PilotPlanState {
  return {
    primaryChangeText: "",
    linkedSolutionId: null,
    linkedCauseIds: [],
    extraChanges: [],
    comparisonDesign: { kind: "before_period", description: "" },
    inclusion: { who_or_what: "", how_selected: "", honesty_note: "" },
    metricRef: "",
    direction: "lower_is_better",
    thresholdValue: 0,
    expectedRoute: "welch_two_sample_t",
    rationale: "",
    falsificationLine: "",
    confounderChecklist: emptyConfounderChecklist(),
    status: "designed",
  };
}

export function changesFromState(state: PilotPlanState): PilotChange[] {
  return [{ change_id: PRIMARY_CHANGE_ID, text: state.primaryChangeText }, ...state.extraChanges];
}

export function pilotPlanMissingFields(state: PilotPlanState): string[] {
  const missing: string[] = [];
  if (!state.primaryChangeText.trim()) missing.push("the one change");
  if (!state.comparisonDesign.description.trim()) missing.push("comparison description");
  if (!state.inclusion.who_or_what.trim()) missing.push("who/what is included");
  if (!state.inclusion.how_selected.trim()) missing.push("how it was selected");
  if (!state.metricRef.trim()) missing.push("success threshold metric");
  if (!state.expectedRoute.trim()) missing.push("expected analysis route");
  if (!state.rationale.trim()) missing.push("analysis-plan rationale");
  if (!state.falsificationLine.trim()) missing.push("falsification line");
  return missing;
}

export function canSavePilotPlan(state: PilotPlanState): boolean {
  return pilotPlanMissingFields(state).length === 0;
}

/** `success_threshold.declared_at` is stamped fresh at every save -- the
 * pre-declaration record (rubric R-IMP-02 #3), same "always regenerated,
 * never loaded back as user input" contract every timestamp in this app's
 * build*Body helpers already follows for created_at/updated_at. */
export function buildPilotPlanBody(input: { artifactId: string; schemaVersion: number; state: PilotPlanState }): Record<string, unknown> {
  const now = new Date().toISOString();
  const { state } = input;
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-19",
    created_at: now, updated_at: now,
    the_one_change: { statement: state.primaryChangeText, linked_solution_id: state.linkedSolutionId, linked_cause_ids: state.linkedCauseIds },
    changes: changesFromState(state),
    comparison_design: state.comparisonDesign,
    inclusion: state.inclusion,
    success_threshold: { metric_ref: state.metricRef, direction: state.direction, value: state.thresholdValue, declared_at: now },
    analysis_plan: { expected_route: state.expectedRoute, rationale: state.rationale },
    falsification_line: state.falsificationLine,
    confounder_checklist: state.confounderChecklist,
    status: state.status,
  };
}

export function pilotPlanStateFromArtifact(artifact: PilotPlanArtifact): PilotPlanState {
  return {
    primaryChangeText: artifact.the_one_change.statement,
    linkedSolutionId: artifact.the_one_change.linked_solution_id ?? null,
    linkedCauseIds: artifact.the_one_change.linked_cause_ids,
    extraChanges: artifact.changes.filter((c) => c.change_id !== PRIMARY_CHANGE_ID),
    comparisonDesign: artifact.comparison_design,
    inclusion: artifact.inclusion,
    metricRef: artifact.success_threshold.metric_ref,
    direction: artifact.success_threshold.direction,
    thresholdValue: artifact.success_threshold.value,
    expectedRoute: artifact.analysis_plan.expected_route,
    rationale: artifact.analysis_plan.rationale,
    falsificationLine: artifact.falsification_line,
    confounderChecklist: artifact.confounder_checklist,
    status: artifact.status,
  };
}
