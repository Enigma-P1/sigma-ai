/** TypeScript mirrors of the engine's Pydantic models (engine/sigma_engine/
 * artifacts/*.py, project_store.py, gates.py, prescore/common.py). Field
 * names and shapes are kept in lockstep with the Python source by hand —
 * there is no schema-generation step in this milestone, so a field rename
 * on either side needs a matching edit here.
 */

// ---- Shared artifact envelope (artifacts/base.py) ----

export interface ArtifactBase {
  schema_version: number;
  artifact_id: string;
  tool_id: string;
  created_at: string;
  updated_at: string;
  notes?: string | null;
}

// ---- Project (project_store.py) ----

export interface ArtifactIndexEntry {
  tool_id: string;
  latest_version: number;
}

export interface ProjectMetadata {
  schema_version: number;
  project_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  artifact_index: Record<string, ArtifactIndexEntry>;
}

export interface OverrideLogEntry {
  gate_id: string;
  reason: string;
  timestamp: string;
}

// ---- Prescore (prescore/common.py) ----

export type PrescoreStatus = "pass" | "flag" | "hard_flag";

export interface PrescoreResult {
  check_id: string;
  tool_id: string;
  status: PrescoreStatus;
  detail: string;
}

// ---- Gates (gates.py) ----

export type GateStatus = "CLEAR" | "SOFT_BLOCK" | "HARD_BLOCK" | "NOT_YET_BUILT";

export interface GateResult {
  status: GateStatus;
  missing: string[];
  reason?: string | null;
}

export type Phase = "Intake" | "Define" | "Measure" | "Analyze" | "Improve" | "Control" | "Wrap";

// ---- T-01 Project Picker (artifacts/picker.py) ----

export type PickerRoute = "full-DMAIC" | "PDCA" | "EXIT-01";

export interface IntakeCriterion {
  answer: boolean;
  detail: string;
}

/** Fixed order matching PickerArtifact.criteria_answers() in picker.py —
 * the frozen routing rule depends on this exact order. */
export const PICKER_CRITERIA_KEYS = [
  "scope_narrow",
  "measurable_outcome",
  "data_obtainable",
  "process_owner_engaged",
  "business_impact_plausible",
] as const;

export type PickerCriterionKey = (typeof PICKER_CRITERIA_KEYS)[number];

export interface PickerArtifact extends ArtifactBase {
  tool_id: "T-01";
  scope_narrow: IntakeCriterion;
  measurable_outcome: IntakeCriterion;
  data_obtainable: IntakeCriterion;
  process_owner_engaged: IntakeCriterion;
  business_impact_plausible: IntakeCriterion;
  route: PickerRoute;
}

// ---- T-03 Project Charter (artifacts/charter.py) ----

export interface Magnitude {
  number: number;
  unit: string;
  period: string;
}

export interface ProblemStatement {
  what: string;
  where: string;
  when: string;
  magnitude: Magnitude;
}

export interface SmartGoal {
  statement: string;
  metric_name: string;
  baseline_value?: number | null;
  target_value: number;
  unit: string;
  target_date: string;
  consequential_metrics: string[];
}

export interface ScopeBlock {
  in_scope: string;
  out_scope: string;
}

export interface TeamMember {
  name: string;
  role: string;
}

export interface TimelineMilestone {
  name: string;
  date: string;
}

export interface BusinessImpact {
  amount: number;
  unit: string;
  basis: string;
}

export type RiskLevel = "low" | "medium" | "high";

export interface RiskRow {
  risk: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  mitigation: string;
  owner: string;
}

export interface CharterArtifact extends ArtifactBase {
  tool_id: "T-03";
  problem_statement: ProblemStatement;
  goal: SmartGoal;
  scope: ScopeBlock;
  team: TeamMember[];
  process_owner: TeamMember;
  timeline: TimelineMilestone[];
  business_impact: BusinessImpact;
  risks: RiskRow[];
}

// ---- Diagnostics (main.py) ----

export interface HealthResponse {
  status: string;
  engine_version: string;
}

export interface SmokeResponse {
  dataset: string;
  n: number;
  mean: number;
  stdev: number;
  certified_mean: number;
  certified_stdev: number;
  match: boolean;
}
