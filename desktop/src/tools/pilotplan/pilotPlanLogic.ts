import type {
  PilotChange,
  PilotComparisonDesign,
  PilotConfounderChecklist,
  PilotDeclaredPackage,
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
export const MIN_PACKAGE_COMPONENTS = 2;

export interface PilotPlanState {
  primaryChangeText: string;
  linkedSolutionId: string | null;
  linkedCauseIds: string[];
  /** Extra `changes` entries beyond the primary -- normally empty. The
   * desktop's own "+ add another change" affordance appends here so the
   * engine's EXIT-10 refusal (artifacts/pilot_plan.py) can be demonstrated
   * and then undone, exactly like a real drafting mistake would be. Not
   * used when declaredPackage is set -- changesFromState derives `changes`
   * from the package's own components list instead (below). */
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
  /** Rubric R-IMP-02 #1's "one honest carve-out" (M4 addition) -- null is
   * the ordinary single-change pilot. When set, `changes` is derived 1:1
   * from `components` (changesFromState below), never hand-typed
   * separately -- the two views can't silently diverge because there's
   * only one place components get typed. */
  declaredPackage: PilotDeclaredPackage | null;
  status: PilotStatus;
}

export function emptyConfounderChecklist(): PilotConfounderChecklist {
  const blank = { changed: false, note: "" };
  return { staffing: { ...blank }, season: { ...blank }, demand: { ...blank }, measurement: { ...blank }, other: { ...blank } };
}

export function emptyDeclaredPackage(): PilotDeclaredPackage {
  return { rationale: "", components: ["", ""] }; // starts at 2 -- the rubric's own carve-out names components, plural
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
    declaredPackage: null,
    status: "designed",
  };
}

/** With no declared package: primary + any demo extra changes (unchanged
 * pre-M4 behavior -- the EXIT-10 refusal path). With one: exactly one
 * `changes` entry per listed component, 1:1, so the count the engine
 * checks against declared_package.components can never mismatch from
 * anything typed in this app (artifacts/pilot_plan.py's own count check
 * becomes unreachable through this UI, not just satisfied by luck). */
export function changesFromState(state: PilotPlanState): PilotChange[] {
  if (state.declaredPackage) {
    return state.declaredPackage.components.map((text, i) => ({ change_id: `pkg-component-${i + 1}`, text }));
  }
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
  if (state.declaredPackage) {
    if (!state.declaredPackage.rationale.trim()) missing.push("declared-package rationale");
    // Schema minimum is 1 non-blank component (a 1-component "package" is
    // legal but prescore-flagged, artifacts/pilot_plan.py's DeclaredPackage
    // docstring) -- this only blocks Save on what the engine would also
    // reject outright: zero components, or a blank one.
    if (state.declaredPackage.components.length === 0 || state.declaredPackage.components.some((c) => !c.trim())) {
      missing.push("declared-package components");
    }
  }
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
    declared_package: state.declaredPackage,
    status: state.status,
  };
}

export function pilotPlanStateFromArtifact(artifact: PilotPlanArtifact): PilotPlanState {
  const declaredPackage = artifact.declared_package ?? null;
  return {
    primaryChangeText: artifact.the_one_change.statement,
    linkedSolutionId: artifact.the_one_change.linked_solution_id ?? null,
    linkedCauseIds: artifact.the_one_change.linked_cause_ids,
    // declared_package's changes are entirely derived from its components
    // (changesFromState) -- nothing to load back as "extra" changes.
    extraChanges: declaredPackage ? [] : artifact.changes.filter((c) => c.change_id !== PRIMARY_CHANGE_ID),
    comparisonDesign: artifact.comparison_design,
    inclusion: artifact.inclusion,
    metricRef: artifact.success_threshold.metric_ref,
    direction: artifact.success_threshold.direction,
    thresholdValue: artifact.success_threshold.value,
    expectedRoute: artifact.analysis_plan.expected_route,
    rationale: artifact.analysis_plan.rationale,
    falsificationLine: artifact.falsification_line,
    confounderChecklist: artifact.confounder_checklist,
    declaredPackage: declaredPackage ? { rationale: declaredPackage.rationale, components: [...declaredPackage.components] } : null,
    status: artifact.status,
  };
}
