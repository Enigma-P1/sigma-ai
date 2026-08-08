import type { ChangeLogEntry, SopStep, StandardWorkArtifact } from "../../api/types";

let counter = 0;
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export interface StandardWorkState {
  title: string;
  version: number;
  owner: string;
  effectiveDate: string;
  supersedes: string | null;
  seededFromProcessMapId: string | null;
  linkedControlPlanId: string | null;
  steps: SopStep[];
  changeLog: ChangeLogEntry[];
}

export function emptyStep(order: number): SopStep {
  return { step_id: genId("step"), order, action: "", standard: "", changed_from_prior: false, source_step_ref: null, note: "" };
}

export function emptyState(): StandardWorkState {
  return {
    title: "", version: 1, owner: "", effectiveDate: new Date().toISOString().slice(0, 10),
    supersedes: null, seededFromProcessMapId: null, linkedControlPlanId: null, steps: [emptyStep(1)], changeLog: [],
  };
}

export function stateFromArtifact(a: StandardWorkArtifact): StandardWorkState {
  return {
    title: a.title, version: a.version, owner: a.owner, effectiveDate: a.effective_date, supersedes: a.supersedes ?? null,
    seededFromProcessMapId: a.seeded_from_process_map_id ?? null, linkedControlPlanId: a.linked_control_plan_id ?? null,
    steps: a.steps, changeLog: a.change_log,
  };
}

export function missingFields(state: StandardWorkState): string[] {
  const missing: string[] = [];
  if (!state.title.trim()) missing.push("title");
  if (!state.owner.trim()) missing.push("owner");
  if (state.steps.length === 0) missing.push("at least one step");
  if (!state.steps.every((s) => s.action.trim() && s.standard.trim())) missing.push("every step's action and standard");
  return missing;
}

export function canSave(state: StandardWorkState): boolean {
  return missingFields(state).length === 0;
}

export function buildBody(input: { artifactId: string; schemaVersion: number; state: StandardWorkState }): Record<string, unknown> {
  const now = new Date().toISOString();
  const { state } = input;
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-24", created_at: now, updated_at: now,
    title: state.title, version: state.version, owner: state.owner, effective_date: state.effectiveDate,
    supersedes: state.supersedes, seeded_from_process_map_id: state.seededFromProcessMapId,
    linked_control_plan_id: state.linkedControlPlanId, steps: state.steps, change_log: state.changeLog,
  };
}
