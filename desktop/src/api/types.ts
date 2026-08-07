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
  /** The gate's missing-tool-ids set at override time (gates.py's
   * OverrideLogEntry.missing) -- what a later /gates/check compares
   * against to tell a still-covering override from a stale one. */
  missing: string[];
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
  /** True when a SOFT_BLOCK cleared because the project's override log
   * already carries a reason logged against exactly this missing set
   * (gates.py's check() / _covering_override). Never true for HARD_BLOCK. */
  overridden: boolean;
  override_reason?: string | null;
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

// ---- Provenance (provenance.py) ----

export interface ProvenanceRecord {
  input_hash: string;
  method: string;
  engine_version: string;
  assumptions_checked: string[];
  warnings: string[];
}

export interface Computed<T> {
  value: T;
  provenance: ProvenanceRecord;
}

// ---- T-02 COPQ / Benefit Calculator (artifacts/copq.py) ----

export const COPQ_CATEGORIES = ["scrap", "rework", "overtime", "expediting", "lost_business", "custom"] as const;
export type CopqCategory = (typeof COPQ_CATEGORIES)[number];

export interface CopqRow {
  category: CopqCategory;
  custom_label?: string | null;
  quantity: number;
  rate: number;
  period: string;
  basis: string;
  is_estimate: boolean;
  /** computed_field on the engine (CopqRow.amount) -- present on rows the
   * engine has echoed back (validate/load), absent on a row the user is
   * still filling in that hasn't round-tripped yet. */
  amount?: number;
}

export interface CopqArtifact extends ArtifactBase {
  tool_id: "T-02";
  rows: CopqRow[];
  total: Computed<number>;
}

// ---- T-04 SIPOC (artifacts/sipoc.py) ----

export interface SupplierInputPair {
  supplier: string;
  input: string;
}

export interface ProcessStep {
  step_number: number;
  description: string;
}

export interface OutputCustomerPair {
  output: string;
  customer: string;
}

export interface SipocArtifact extends ArtifactBase {
  tool_id: "T-04";
  supplier_input_pairs: SupplierInputPair[];
  process_steps: ProcessStep[];
  output_customer_pairs: OutputCustomerPair[];
  scope_start: string;
  scope_end: string;
}

// ---- T-05 VoC -> CTQ Tree (artifacts/voc_ctq.py) ----

export type CtqDirection = "higher_is_better" | "lower_is_better" | "target_is_best";
export const CTQ_DIRECTIONS: CtqDirection[] = ["higher_is_better", "lower_is_better", "target_is_best"];

export type VocStatementSource = "interview" | "complaint_log" | "survey" | "direct_observation" | "other";
export const VOC_STATEMENT_SOURCES: VocStatementSource[] = [
  "interview",
  "complaint_log",
  "survey",
  "direct_observation",
  "other",
];

export interface VocCustomer {
  role: string;
  is_internal: boolean;
}

export interface VocStatement {
  statement_id: string;
  customer_role: string;
  text: string;
  source: VocStatementSource;
  source_detail: string;
}

export interface CustomerNeed {
  need_id: string;
  statement_ids: string[];
  text: string;
}

export interface Ctq {
  ctq_id: string;
  need_id: string;
  measure: string;
  direction: CtqDirection;
  target?: string | null;
  critical_vs_easy_check: string;
}

export interface VocCtqArtifact extends ArtifactBase {
  tool_id: "T-05";
  customers: VocCustomer[];
  statements: VocStatement[];
  needs: CustomerNeed[];
  ctqs: Ctq[];
  primary_ctq_id: string;
  charter_metric_link: string;
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
