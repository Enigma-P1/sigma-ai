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

// ---- T-06 Process Map (swimlane) + Waste Walk (artifacts/process_map.py) ----

export type StepType = "value_add" | "non_value_add" | "enabling";
export const STEP_TYPES: StepType[] = ["value_add", "non_value_add", "enabling"];

// The 8 canonical lean wastes (DOWNTIME) -- matrix §3a 1.4.4: "T-06 waste
// walk uses the 8-waste superset."
export type WasteId =
  | "defects"
  | "overproduction"
  | "waiting"
  | "non_utilized_talent"
  | "transportation"
  | "inventory"
  | "motion"
  | "extra_processing";

export const WASTE_IDS: WasteId[] = [
  "defects",
  "overproduction",
  "waiting",
  "non_utilized_talent",
  "transportation",
  "inventory",
  "motion",
  "extra_processing",
];

export interface ProcessMapLane {
  lane_id: string;
  name: string;
  owner: string;
}

export interface WasteEntry {
  waste_id: WasteId;
  note: string;
}

export interface ProcessMapStep {
  step_id: string;
  lane_id: string;
  name: string;
  order: number;
  step_type: StepType;
  reason: string;
  time_minutes?: number | null;
  defect_point: boolean;
  strata: string[];
  wastes: WasteEntry[];
}

export interface ProcessMapConnector {
  from_step: string;
  to_step: string;
  label?: string | null;
}

export interface StepPosition {
  x: number;
  y: number;
}

export interface DemandBlock {
  available_time_minutes?: number | null;
  demand_units?: number | null;
}

/** The longest-timed step of ANY step_type, waits included -- needs no
 * demand block (fidelity fix: a wait can be the longest step without ever
 * being the constraint -- see ConstraintStepResult below). */
export interface LongestStepResult {
  step_id: string;
  step_name: string;
  step_type: StepType;
  time_minutes: number;
}

/** A-7's constraint readout, restricted to PROCESSING steps (step_type
 * value_add or enabling) -- a pure-wait non_value_add step can queue up
 * behind the constraint, but it can never be named here. meets_pace is
 * judged on this step alone. */
export interface ConstraintStepResult {
  step_id: string;
  step_name: string;
  time_minutes: number;
  pace_minutes_per_unit: number;
  meets_pace: boolean;
}

export interface ProcessMapArtifact extends ArtifactBase {
  tool_id: "T-06";
  lanes: ProcessMapLane[];
  steps: ProcessMapStep[];
  connectors: ProcessMapConnector[];
  demand?: DemandBlock | null;
  /** Keyed by step_id -- opaque display data, round-tripped, never
   * interpreted by the engine (M2 brief). */
  layout: Record<string, StepPosition>;
  /** Server-computed, never hand-typed -- present once the engine has
   * echoed the artifact back (validate/save/load). Null means "nothing to
   * name yet" (no step has a time) -- needs no demand block. */
  longest_step?: Computed<LongestStepResult> | null;
  /** Server-computed (matrix §5a A-7), never hand-typed -- present once the
   * engine has echoed the artifact back. Null means "nothing to name yet"
   * (demand incomplete, or no PROCESSING step has a time), not an error. */
  constraint_step?: Computed<ConstraintStepResult> | null;
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

// ---- Datasets (engine/sigma_engine/datasets.py) — T-11 import half ----

export type ColumnType = "numeric" | "text";

export interface ColumnInfo {
  name: string;
  inferred_type: ColumnType;
  /** Effective type: a caller's confirmed override if given, else
   * inferred_type — "inferred but user-confirmable" (M2 brief). */
  type: ColumnType;
  sample_values: string[];
}

export interface QualityScanResult {
  row_count: number;
  missing_values: Record<string, number>;
  non_numeric_in_numeric_columns: Record<string, number>;
  duplicate_row_count: number;
}

/** Returned by the preview route — never persisted. */
export interface DatasetPreview {
  source_filename: string;
  row_count: number;
  columns: ColumnInfo[];
  quality: QualityScanResult;
  sample_rows: Record<string, string>[];
}

/** The persisted record (meta.json). */
export interface DatasetMeta {
  schema_version: number;
  dataset_id: string;
  project_id: string;
  source_filename: string;
  created_at: string;
  sha256: string;
  row_count: number;
  columns: ColumnInfo[];
  quality: QualityScanResult;
  /** Provenance the other direction (T-08/T-09's zero-re-entry contract,
   * rubric R-MEA-06 #3): which in-app artifact this dataset was
   * materialized from. null for an ordinary CSV/XLSX upload. */
  source_artifact_id?: string | null;
  source_tool_id?: string | null;
}

export interface DatasetDetail {
  meta: DatasetMeta;
  rows: Record<string, string>[];
}

// ---- Stats: descriptive + baseline (engine/sigma_engine/stats/*.py) — T-13 ----
// Mirrored field-for-field from the Pydantic models routes/stats.py
// serializes — T-13 renders BaselineResult faithfully and computes
// nothing itself, so these shapes are load-bearing, not decorative.

export interface DescriptiveStats {
  n: number;
  mean: number;
  sd: number;
  median: number;
  q1: number;
  q3: number;
  iqr: number;
  min: number;
  max: number;
}

export type ImrSignalSide = "above" | "below";

export interface ImrSignal {
  rule_id: string;
  start_index: number;
  end_index: number;
  side: ImrSignalSide;
  description: string;
}

export interface ImrChartResult {
  n: number;
  xbar: number;
  mr_bar: number;
  sigma_within: number;
  i_ucl: number;
  i_cl: number;
  i_lcl: number;
  mr_ucl: number;
  mr_cl: number;
  mr_lcl: number;
  signals: ImrSignal[];
  rule2_enabled: boolean;
  rule3_enabled: boolean;
}

export interface CapabilityResult {
  n: number;
  mean: number;
  sigma_within: number;
  sigma_overall: number;
  usl: number | null;
  lsl: number | null;
  one_sided: boolean;
  /** null whenever the process is not stable (EXIT-04) — render the
   * EXIT-04 explanation in that case, never a blank (M2 brief). */
  cp_index: number | null;
  cpk_index: number | null;
  pp_index: number | null;
  ppk_index: number;
  performance_not_capability: boolean;
}

export type NormalityAdvisory = "no_concern" | "concern" | "too_few_to_judge";

export interface NormalityResult {
  n: number;
  statistic: number | null;
  approx_pvalue: number | null;
  p_band: string;
  advisory: NormalityAdvisory;
}

export interface PercentileCapabilityResult {
  n: number;
  p_low: number;
  p_median: number;
  p_high: number;
  pp_percentile: number | null;
  ppk_percentile: number;
  label: string;
}

export interface ObservedYieldResult {
  n: number;
  in_spec_fraction: number;
  dpmo: number;
}

export type SigmaConvention = "with 1.5σ shift" | "without shift";

export interface SigmaLevelResult {
  dpmo: number;
  /** Python's float can hold `inf` (an extremely capable process against
   * very wide spec limits pushes the underlying z-score there); pydantic
   * serializes a non-finite float as JSON `null` by default, so this is
   * genuinely nullable on the wire even though the engine's own type
   * annotation reads as a plain float — confirmed empirically against
   * the route, not assumed. Render an honest "not finite at this scale"
   * message rather than crashing .toFixed() on null. */
  sigma_level: number | null;
  convention: SigmaConvention;
}

export interface BaselineResult {
  gate_ok: boolean;
  gate_message: string | null;
  n: number | null;
  /** "failed" whenever the project's latest T-12 (Measurement Check)
   * verdict reads "fail" (matrix §4a EXIT-02) -- capability/percentile_
   * capability/observed_yield/sigma are all null whenever this is set
   * (stats/baseline.py suppresses them server-side, not just a label). */
  measurement_check: "failed" | null;
  descriptive: Computed<DescriptiveStats> | null;
  stability: Computed<ImrChartResult> | null;
  stable: boolean | null;
  stability_note: string | null;
  capability: Computed<CapabilityResult> | null;
  normality: Computed<NormalityResult> | null;
  percentile_capability: Computed<PercentileCapabilityResult> | null;
  observed_yield: Computed<ObservedYieldResult> | null;
  sigma: Computed<SigmaLevelResult> | null;
  exits: string[];
}

/** R-MEA-06's dataset -> BaselineResult hash chain, echoed back only when
 * the baseline route was fed a dataset_id (routes/stats.py). */
export interface DatasetProvenance {
  dataset_id: string;
  dataset_sha256: string;
  column: string;
  row_count_used: number;
}

export interface BaselineResponse extends BaselineResult {
  dataset_provenance?: DatasetProvenance;
}

// ---- Stats: Pareto (engine/sigma_engine/stats/pareto.py) — T-14 ----

export interface ParetoCategory {
  category: string;
  count: number;
  share: number;
  cumulative_share: number;
  vital_few: boolean;
}

export interface ParetoResult {
  total: number;
  categories: ParetoCategory[];
  vital_few_count: number;
  /** No small subset of categories dominates — the honest "flat-bars"
   * case (research §F), not a forced vital-few claim. */
  flat: boolean;
}

// ---- Stats: MSA (engine/sigma_engine/stats/msa.py) — T-12 -----------------

export type MsaVerdict = "acceptable" | "marginal" | "fail";
export type MsaDataType = "continuous" | "attribute";
export type MsaSpanBasis = "tolerance" | "observed_spread";
export type MsaDenominator = "tolerance" | "study_variation";

export interface ResolutionCheckResult {
  gauge_increment: number;
  span: number;
  span_basis: MsaSpanBasis;
  increment_to_span_ratio: number | null;
  distinct_value_count: number;
  passed: boolean;
  reasons: string[];
}

export interface RepeatabilityResult {
  s_repeat: number;
  denominator_value: number;
  denominator: MsaDenominator;
  repeatability_percent: number;
  verdict: MsaVerdict;
  items_used: number;
  items_excluded: string[];
  exclusion_reasons: string[];
}

export interface AttributeAgreementResult {
  n: number;
  percent_agreement: number;
  kappa: number;
  p_observed: number;
  p_expected: number;
  verdict: MsaVerdict;
}

export interface Exit02Payload {
  exit_id: "EXIT-02";
  message: string;
  routes_to: string;
}

export interface Exit03Payload {
  exit_id: "EXIT-03";
  message: string;
  out_of_scope_examples: string[];
  routes_to: string;
}

export interface MsaResult {
  data_type: MsaDataType;
  verdict: MsaVerdict;
  resolution_check: ResolutionCheckResult | null;
  repeatability: Computed<RepeatabilityResult> | null;
  attribute_agreement: Computed<AttributeAgreementResult> | null;
  caveat: string | null;
  exit02: Exit02Payload | null;
}

// ---- T-12 Measurement Check artifact (artifacts/msa.py) -------------------

export interface ContinuousItemRow {
  item_id: string;
  /** A `null` slot is a missing/invalid repeat -- excluded from s_repeat
   * server-side and logged, never treated as zero. */
  readings: (number | null)[];
}

export interface AttributeJudgmentRow {
  item_id: string;
  rater_a: boolean;
  rater_b: boolean;
}

export interface MsaArtifact extends ArtifactBase {
  tool_id: "T-12";
  data_type: MsaDataType;
  operator: string;
  gauge_name?: string | null;
  gauge_increment?: number | null;
  usl?: number | null;
  lsl?: number | null;
  continuous_items: ContinuousItemRow[];
  attribute_items: AttributeJudgmentRow[];
  /** Server-computed, never hand-typed -- present once the engine has
   * echoed the artifact back (validate/save/load), absent on a fresh
   * client-side draft that hasn't round-tripped yet. */
  result?: MsaResult | null;
}

// ---- Stats: sample-size guidance (stats/sample_size.py) — T-11 ------------

export interface RuleOfThumbResult {
  context: "imr_baseline";
  minimum_n: number;
  recommended_n: number;
  rationale: string;
}

export interface MeanSampleSizeResult {
  n: number;
  n_exact: number;
  z: number;
  confidence_level: number;
  planning_sd: number;
  margin_of_error: number;
  plain_english: string;
}

export interface ProportionSampleSizeResult {
  n: number;
  n_exact: number;
  z: number;
  confidence_level: number;
  planning_p: number;
  margin_of_error: number;
  plain_english: string;
}

export interface SampleSizeResponse {
  rule_of_thumb: RuleOfThumbResult;
  calculator: Computed<MeanSampleSizeResult> | Computed<ProportionSampleSizeResult> | null;
  warnings: string[];
}

// ---- T-07 Spaghetti Diagram (artifacts/spaghetti.py) ----

export type SpaghettiUnit = "meters" | "feet";
export type LayoutMode = "current" | "proposed";
export const LAYOUT_MODES: LayoutMode[] = ["current", "proposed"];

export interface FloorPlanRef {
  image_id: string;
  source_filename: string;
  sha256: string;
  width_px: number;
  height_px: number;
}

export interface CalibrationPoint {
  x: number;
  y: number;
}

export interface Calibration {
  point_a: CalibrationPoint;
  point_b: CalibrationPoint;
  real_length: number;
  unit: SpaghettiUnit;
}

export interface Operator {
  operator_id: string;
  name: string;
  color_index: number;
}

export interface RoutePoint {
  x: number;
  y: number;
}

export interface SpaghettiRoute {
  route_id: string;
  operator_id: string;
  trip_label: string;
  frequency_per_day: number;
  points: RoutePoint[];
  layout_mode: LayoutMode;
}

export interface ObservationWindow {
  when: string;
  duration: string;
  shift: string;
}

export interface RouteMetrics {
  route_id: string;
  operator_id: string;
  trip_label: string;
  layout_mode: LayoutMode;
  unit: SpaghettiUnit;
  distance_per_trip: number;
  walk_time_minutes_per_trip: number;
  frequency_per_day: number;
  daily_distance: number;
  daily_walk_time_minutes: number;
}

export interface OperatorTotal {
  operator_id: string;
  operator_name: string;
  layout_mode: LayoutMode;
  daily_trip_count: number;
  total_daily_distance: number;
  total_daily_walk_time_minutes: number;
}

export interface PathCrossing {
  route_id_a: string;
  route_id_b: string;
  crossing_count: number;
}

/** One row of the current-vs-proposed table: either one operator (`scope`
 * = that operator's operator_id) or the "overall" rollup. */
export interface DeltaRow {
  scope: string;
  scope_label: string;
  current_daily_distance: number | null;
  proposed_daily_distance: number | null;
  distance_delta: number | null;
  distance_delta_pct: number | null;
  current_daily_walk_time_minutes: number | null;
  proposed_daily_walk_time_minutes: number | null;
  walk_time_delta_minutes: number | null;
  walk_time_delta_pct: number | null;
}

export interface SpaghettiMetrics {
  unit: SpaghettiUnit;
  pixels_per_unit: number;
  walk_speed_units_per_minute: number;
  routes: RouteMetrics[];
  operator_totals: OperatorTotal[];
  total_daily_distance_all: number;
  total_daily_walk_time_minutes_all: number;
  crossings: PathCrossing[];
  total_crossing_count: number;
  /** Null until both layout modes have >=1 route -- an honest "nothing to
   * compare yet," not a table of zeros. */
  delta: DeltaRow[] | null;
}

export interface SpaghettiArtifact extends ArtifactBase {
  tool_id: "T-07";
  floor_plan: FloorPlanRef;
  calibration?: Calibration | null;
  operators: Operator[];
  routes: SpaghettiRoute[];
  walk_speed_override_per_minute?: number | null;
  observation_window: ObservationWindow;
  /** Server-computed (T-06 longest_step/constraint_step's pattern), never
   * hand-typed. Null only when there's no calibration yet to scale by. */
  metrics?: Computed<SpaghettiMetrics> | null;
}

// ---- Floor-plan image storage (floorplan_images.py) — T-07 upload ----

export interface FloorPlanImageMeta {
  schema_version: number;
  image_id: string;
  project_id: string;
  source_filename: string;
  created_at: string;
  sha256: string;
  content_type: "image/png" | "image/jpeg";
  width_px: number;
  height_px: number;
}

export interface FloorPlanDetail {
  meta: FloorPlanImageMeta;
  content_base64: string;
}

// ---- Soft delete (artifacts/base.py DeletionInfo) -- shared by T-08's
// entries and T-09's cycles: rubric R-MEA-04's "deletions carry a logged
// reason," generalized to T-08 too. The row stays in the array; `deleted`
// is what marks it excluded from computed stats/exports. ----

export interface DeletionInfo {
  reason: string;
  at: string;
}

// ---- T-08 Check Sheet / Tally (artifacts/check_sheet.py) ----

export interface CheckSheetCategory {
  category_id: string;
  label: string;
}

export interface StrataFieldDef {
  key: string;
  label: string;
}

export type EntryMode = "tap" | "transcribed";

export interface CheckSheetEntry {
  entry_id: string;
  category_id: string;
  timestamp: string;
  strata: Record<string, string>;
  note: string;
  /** "tap" (default): one live tap, one entry. "transcribed": reading a
   * paper tally after the fact -- `note` doubles as the required source
   * note and `count` carries how many marks this one entry represents.
   * The cross-artifact burst-entry check only ever looks at "tap" entries
   * (engine/sigma_engine/prescore/cross_checks.py), so an honest
   * transcription session is never mistaken for a suspicious burst. */
  entry_mode?: EntryMode;
  /** How many tally marks this entry represents -- always 1 on the tap
   * path; a transcribed entry carries the paper tally's count. */
  count?: number;
  deleted?: DeletionInfo | null;
}

export interface CheckSheetArtifact extends ArtifactBase {
  tool_id: "T-08";
  categories: CheckSheetCategory[];
  strata_fields: StrataFieldDef[];
  entries: CheckSheetEntry[];
}

// ---- T-09 Guided Time Study / Work Sampling (artifacts/time_study.py) ----

export interface WorkElement {
  element_id: string;
  name: string;
  description: string;
}

export interface ElementTime {
  element_id: string;
  seconds: number;
}

export interface TimeStudyCycle {
  cycle_number: number;
  element_times: ElementTime[];
  observer_note: string;
  deleted?: DeletionInfo | null;
}

export type WorkSamplingCategory = "working" | "waiting" | "moving" | "other";
export const WORK_SAMPLING_CATEGORIES: WorkSamplingCategory[] = ["working", "waiting", "moving", "other"];

export interface IntervalObservation {
  observation_id: string;
  timestamp: string;
  category: WorkSamplingCategory;
  note: string;
}

export interface WorkSamplingShare {
  category: WorkSamplingCategory;
  count: number;
  share: number;
}

export interface WorkSamplingSummary {
  total_observations: number;
  shares: WorkSamplingShare[];
}

export type OutlierDirection = "low" | "high";

export interface OutlierFlag {
  cycle_number: number;
  seconds: number;
  direction: OutlierDirection;
  fence_value: number;
  reason: string;
}

export interface ElementStats {
  element_id: string;
  element_name: string;
  n: number;
  /** null below n=2 -- sample SD needs at least 2 observations. */
  descriptive: DescriptiveStats | null;
  outliers: OutlierFlag[];
  below_recommended_cycles: boolean;
  cycle_count_note: string;
}

export interface TimeStudyArtifact extends ArtifactBase {
  tool_id: "T-09";
  elements: WorkElement[];
  cycles: TimeStudyCycle[];
  interval_observations: IntervalObservation[];
  /** Server-computed, never hand-typed -- present once the engine has
   * echoed the artifact back (validate/save/load). */
  element_stats?: Computed<ElementStats[]> | null;
  /** null when there are no interval observations yet. */
  work_sampling_summary?: Computed<WorkSamplingSummary> | null;
}

// ---- T-10 Yield Calculator (artifacts/yield_calc.py) ----

export interface YieldStep {
  name: string;
  units_in: number;
  /** The one input convention this tool uses -- defective_units_at_step is
   * always derived server-side (units_in - first_pass_correct), never a
   * second raw input. */
  first_pass_correct: number;
  /** computed_field on the engine -- present once a save/validate has
   * echoed the step back, absent on a step the user is still filling in
   * that hasn't round-tripped yet (CopqRow.amount's same "engine-sourced,
   * never a client stand-in presented as authoritative" precedent).
   * Named defective_units_at_step, not "defects_at_step": this tool's raw
   * input is defect-free UNITS, so the derived count is defective UNITS
   * too (never a defect count, which can exceed 1 per unit -- matrix
   * VI.A.3's EXIT-11 distinction). */
  defective_units_at_step?: number;
  /** Direct observed ratio (first_pass_correct / units_in), not a modeled
   * estimate -- rubric R-MEA-09 #2 "computed from good/rework/scrap
   * counts." */
  fpy_at_step?: number;
}

export interface DpmoBlock {
  defects: number;
  units: number;
  opportunities_per_unit: number;
  /** Required non-empty the moment opportunities_per_unit > 1 (engine-
   * enforced, artifacts/yield_calc.py) -- the opportunity-inflation
   * honesty guard, rubric R-MEA-09. */
  opportunity_justification: string;
  apply_sigma_shift: boolean;
}

export interface YieldCalcArtifact extends ArtifactBase {
  tool_id: "T-10";
  steps: YieldStep[];
  /** Required, no default on the engine side -- RTY is only computed/
   * claimed when this is explicitly true. */
  steps_in_series: boolean;
  dpmo_block?: DpmoBlock | null;
  /** Server-computed, never hand-typed -- present once round-tripped;
   * null whenever steps_in_series is false (RTY is only computed/claimed
   * under the explicit serial assumption). */
  rty_result?: Computed<number> | null;
  /** null whenever dpmo_block is absent -- the DPMO/sigma calculation is
   * independent of the steps table. Reuses the same SigmaLevelResult
   * shape as T-13's baseline.sigma (always the same shift-convention
   * label, never a second convention invented for this tool). */
  dpmo_result?: Computed<SigmaLevelResult> | null;
}

// ---- T-11 Data Collection Plan (artifacts/data_collection_plan.py) -------
// The PLAN half of T-11 -- the import half is DatasetMeta/DatasetPreview
// above, the sample-size half is SampleSizeResponse. No computed fields:
// a plan is written down, not derived (rubric R-MEA-05).

export type DataCollectionDataType = "continuous" | "attribute_defective" | "attribute_count";

export const DATA_COLLECTION_DATA_TYPES: { value: DataCollectionDataType; label: string }[] = [
  { value: "continuous", label: "Continuous -- a measured amount (time, weight, length...)" },
  { value: "attribute_defective", label: "Attribute -- defective (pass/fail per unit)" },
  { value: "attribute_count", label: "Attribute -- defect count (defects per unit or area)" },
];

export interface OperationalDefinition {
  what_measured: string;
  how_instrument: string;
  precision_unit: string;
  starts_when: string;
  stops_when: string;
  two_people_confirmed: boolean;
}

export interface StratificationFactor {
  name: string;
  values_expected: string[];
}

export interface CollectionLogistics {
  who_collects: string;
  where_collected: string;
  when_how_often: string;
  planned_n: number | null;
  sample_size_rationale: string;
}

export interface DataCollectionPlanArtifact extends ArtifactBase {
  tool_id: "T-11";
  metric_name: string;
  charter_metric_id?: string | null;
  operational_definition: OperationalDefinition;
  data_type: DataCollectionDataType | null;
  stratification_factors: StratificationFactor[];
  no_stratification_reason: string;
  logistics: CollectionLogistics;
  bias_note: string;
}

// ---- Stats: Hypothesis Testing (engine/sigma_engine/stats/hypothesis_*.py) — T-17 ----
// Mirrored field-for-field from hypothesis_common.py / hypothesis_selector.py --
// the printed decision tree and the result numbers are both rendered
// straight off these shapes, nothing recomputed client-side (build brief).

export type HypComparisonType =
  | "two_independent"
  | "paired"
  | "multi_group"
  | "one_sample_vs_target"
  | "proportions"
  | "association_categorical"
  | "relationship_continuous";

export const HYP_COMPARISON_TYPES: { value: HypComparisonType; label: string }[] = [
  { value: "two_independent", label: "Two groups (independent)" },
  { value: "paired", label: "Before/after pairs (same units, measured twice)" },
  { value: "multi_group", label: "Three or more groups" },
  { value: "one_sample_vs_target", label: "One group vs. a target value" },
  { value: "proportions", label: "Two proportions (pass/fail rates)" },
  { value: "association_categorical", label: "Counts in categories (association)" },
  { value: "relationship_continuous", label: "Two continuous variables (relationship)" },
];

export type HypDeclaredDataType = "continuous" | "ordinal" | "nominal_categorical" | "count_rate";
export type HypQuestionIntent = "omnibus_any_group_differs" | "which_groups_differ";
export type HypRouteName =
  | "welch_two_sample_t"
  | "paired_t"
  | "one_sample_t"
  | "one_way_anova"
  | "one_proportion"
  | "two_proportion_z"
  | "chi_square_independence"
  | "mann_whitney_u"
  | "wilcoxon_signed_rank";
export type HypExitId = "EXIT-06" | "EXIT-07" | "EXIT-08" | "EXIT-09" | "EXIT-11" | "EXIT-12" | "EXIT-14" | "EXIT-15";

export interface HypGroupInput {
  label: string;
  values?: number[] | null;
  successes?: number | null;
  n?: number | null;
}

/** The routing input contract (hypothesis_common.HypothesisQuestion) --
 * every field an EXIT-06..15 check needs is detectable from this object
 * alone, never inferred and never silent (module docstring). */
export interface HypothesisQuestion {
  question_text: string;
  comparison_type: HypComparisonType;
  declared_data_type: HypDeclaredDataType;
  groups: HypGroupInput[];
  paired_before?: number[] | null;
  paired_after?: number[] | null;
  paired_before_label: string;
  paired_after_label: string;
  sample?: number[] | null;
  sample_label: string;
  target?: number | null;
  contingency_table?: number[][] | null;
  row_labels?: string[] | null;
  col_labels?: string[] | null;
  time_ordered: boolean;
  user_shape_concern: boolean;
  measurements_per_unit: number;
  question_intent?: HypQuestionIntent | null;
  comparisons_declared: number;
  tests_run_including_this_one: number;
  declared_primary: boolean;
}

export interface HypDecisionNode {
  question: string;
  answer: string;
  branch: string;
}

/** matrix §4 registry row this selector raised -- message/routes_to are
 * the engine's own words (_EXIT_REGISTRY in hypothesis_selector.py),
 * rendered verbatim rather than re-typed client-side. */
export interface HypExitPayload {
  exit_id: HypExitId;
  message: string;
  routes_to: string;
  detail: string;
}

export interface HypRoutingDecision {
  question: string;
  comparison_type: string;
  decision_path: HypDecisionNode[];
  route: HypRouteName | null;
  exit: HypExitPayload | null;
  switch_reason: string | null;
  recommend_nonparametric: boolean;
}

/** dataset_provenance is a *list* here (routes/hypothesis.py), unlike
 * baseline's single DatasetProvenance -- T-17's question shape can pull
 * more than one column at once (two groups, a before/after pair, ...). */
export interface HypothesisRouteResponse extends HypRoutingDecision {
  dataset_provenance?: DatasetProvenance[];
}

export interface HypGroupSummary {
  label: string;
  n: number;
  mean?: number | null;
  sd?: number | null;
  median?: number | null;
  successes?: number | null;
  proportion?: number | null;
}

export interface HypContingencyCell {
  row: string;
  col: string;
  observed: number;
  expected: number;
}

/** Rendered verbatim by the UI (build brief): what was compared, what the
 * p-value does/doesn't mean here, effect size in words, and the
 * practical-significance prompt. */
export interface HypPlainLanguageBlock {
  comparison_summary: string;
  p_value_meaning: string;
  effect_size_in_words: string;
  practical_significance_prompt: string;
}

/** matrix §4 EXIT-13: ANOVA-significant canned next step + the honest
 * interim read -- attached to a *successful* result, never a routing
 * refusal (hypothesis_common.RouteName's module note). */
export interface HypExit13Payload {
  exit_id: "EXIT-13";
  message: string;
  interim_read: HypGroupSummary[];
  largest_vs_smallest: string;
  routes_to: string;
}

/** The one result shape every T-17 route produces (hypothesis_common
 * module docstring) -- family-specific numbers (Cramer's V, Hodges-Lehmann
 * shift, risk difference, ...) stay null on the routes that don't produce
 * them. */
export interface HypothesisTestResult {
  test_name: HypRouteName;
  statistic_name: string;
  statistic: number;
  df?: number | null;
  df_between?: number | null;
  df_within?: number | null;
  p_value: number;
  alpha: number;
  two_sided: boolean;
  significant: boolean;

  effect_size_name: string;
  effect_size_value: number;
  effect_size_ci?: [number, number] | null;
  effect_size_ci_method?: string | null;

  groups: HypGroupSummary[];
  contingency?: HypContingencyCell[] | null;
  cramers_v?: number | null;
  hodges_lehmann_shift?: number | null;
  hodges_lehmann_ci?: [number, number] | null;
  hodges_lehmann_ci_method?: string | null;
  rank_biserial_r?: number | null;
  risk_difference?: number | null;
  risk_difference_ci?: [number, number] | null;
  risk_difference_ci_method?: string | null;
  equal_shape_caveat?: string | null;

  assumptions_checked: string[];
  warnings: string[];
  plain_language: HypPlainLanguageBlock;
  exit13?: HypExit13Payload | null;
}

/** T-17's /run contract: route + compute in one call. `result` stays null
 * and `refused` is true whenever the selector raised an exit -- no test
 * math ever ran past that point (hypothesis_runner module docstring). */
export interface HypothesisRunResult {
  question_text: string;
  routing: HypRoutingDecision;
  result: Computed<HypothesisTestResult> | null;
  refused: boolean;
  dataset_provenance?: DatasetProvenance[];
}

// ---- T-17 Hypothesis Testing artifact (artifacts/hypothesis.py) ----
// THIN by design (build brief): stores the question as stated and the
// declared-primary flag; routing/result are always server-recomputed from
// the stored question on validate/save (never hand-typed, same contract as
// MsaArtifact.result) -- see that module's docstring.

export interface HypothesisRunArtifact extends ArtifactBase {
  tool_id: "T-17";
  question: HypothesisQuestion;
  declared_primary: boolean;
  routing?: HypRoutingDecision | null;
  result?: Computed<HypothesisTestResult> | null;
  refused: boolean;
}

// ---- T-15 Fishbone (6M) + 5 Whys (artifacts/fishbone.py) ----

export type FishboneBranch = "people" | "method" | "machine" | "material" | "measurement" | "environment";
export const FISHBONE_BRANCHES: FishboneBranch[] = [
  "people",
  "method",
  "machine",
  "material",
  "measurement",
  "environment",
];

export type CauseStatus = "candidate" | "investigating" | "verified" | "ruled_out";
export const CAUSE_STATUSES: CauseStatus[] = ["candidate", "investigating", "verified", "ruled_out"];

export type EvidenceKind = "dataset" | "hypothesis_run" | "check_sheet" | "observation_note";
export const EVIDENCE_KINDS: EvidenceKind[] = ["dataset", "hypothesis_run", "check_sheet", "observation_note"];

/** `ref` is an artifact/dataset id for the three artifact-backed kinds, or
 * the note text itself for `observation_note` -- artifacts/fishbone.py's
 * Evidence model, unchecked cross-reference (no project-store lookup at
 * the schema layer; the desktop resolves it for display). */
export interface FishboneEvidence {
  kind: EvidenceKind;
  ref: string;
}

export interface FishboneCause {
  cause_id: string;
  branch: FishboneBranch;
  text: string;
  parent_cause_id?: string | null;
  status: CauseStatus;
  evidence?: FishboneEvidence | null;
  why_chain_position?: number | null;
}

export interface FishboneEffect {
  text: string;
  charter_ref?: string | null;
}

export interface CausePosition {
  x: number;
  y: number;
}

/** One verified cause as it feeds Improve (R-ANA-06) -- evidence is never
 * null here, unlike FishboneCause.evidence (schema-guaranteed). */
export interface VerifiedCauseEntry {
  cause_id: string;
  branch: FishboneBranch;
  text: string;
  evidence: FishboneEvidence;
  parent_cause_id?: string | null;
  why_chain_position?: number | null;
}

export interface VerifiedCausesSummary {
  count: number;
  causes: VerifiedCauseEntry[];
}

export interface FishboneArtifact extends ArtifactBase {
  tool_id: "T-15";
  effect: FishboneEffect;
  causes: FishboneCause[];
  /** Keyed by cause_id -- opaque display data, round-tripped, never
   * interpreted by the engine (process_map.py's layout pattern). */
  layout: Record<string, CausePosition>;
  /** Server-computed, never hand-typed -- present once the engine has
   * echoed the artifact back. An empty list is itself the honest
   * zero-verified-causes state, not "nothing computed yet". */
  verified_causes?: Computed<VerifiedCausesSummary> | null;
}

// ---- T-16 FMEA (process) (artifacts/fmea.py) ----

export type FmeaActionStatus = "open" | "done" | "na";
export const FMEA_ACTION_STATUSES: FmeaActionStatus[] = ["open", "done", "na"];

export interface FmeaRow {
  row_id: string;
  /** Optional link to a T-06 ProcessMapArtifact step_id -- unchecked
   * cross-reference; `step_name` is always present so a row never floats
   * with no named step, linked or not. */
  process_step_ref?: string | null;
  step_name: string;
  failure_mode: string;
  effect: string;
  cause: string;
  severity: number;
  occurrence: number;
  detection: number;
  action: string;
  action_owner: string;
  action_due?: string | null;
  action_status: FmeaActionStatus;
  /** Honest self-report: the desktop sets this once the anchor text has
   * actually been shown for this row's rating (T-11's two_people_confirmed
   * "checklist confirmation" idiom). */
  anchors_consulted: boolean;
  /** computed_field on the engine (FmeaRow.rpn = severity * occurrence *
   * detection) -- present on rows the engine has echoed back, absent on a
   * fresh client-side draft that hasn't round-tripped yet (CopqRow.amount's
   * pattern). */
  rpn?: number;
}

/** This engine's own original 1-10 anchor wording (PLAN §6: no AIAG/ASQ
 * licensed text) -- embedded on the artifact itself, never client-supplied.
 * JSON object keys are always strings on the wire. */
export interface FmeaAnchors {
  severity: Record<string, string>;
  occurrence: Record<string, string>;
  detection: Record<string, string>;
}

export interface FmeaBlockingFlag {
  row_id: string;
  failure_mode: string;
  effect: string;
  severity: number;
  reason: string;
}

export interface FmeaArtifact extends ArtifactBase {
  tool_id: "T-16";
  rows: FmeaRow[];
  /** Server-computed reference data -- present once the engine has echoed
   * the artifact back. */
  anchors?: FmeaAnchors | null;
  /** Server-computed, never hand-typed. An empty list is itself the
   * honest "nothing to block" state, not "nothing computed yet". */
  blocking_flags?: Computed<FmeaBlockingFlag[]> | null;
  /** row_id order, severity desc then rpn desc (rubric R-ANA-03's stated
   * RPN limitation: severity-first, RPN alone can't outrank it). */
  sorted_view?: Computed<string[]> | null;
}

// ---- T-18 Solution Selection Matrix (artifacts/solution_matrix.py) ----

export type Quadrant = "quick_win" | "major_project" | "fill_in" | "thankless_task";

export interface SolutionCriterion {
  criterion_id: string;
  name: string;
  weight: number;
  declared_at: string;
}

export interface SolutionCriterionScore {
  criterion_id: string;
  score: number;
  scored_at: string;
}

export interface Solution {
  solution_id: string;
  name: string;
  description: string;
  /** Unchecked cross-reference into T-15's verified causes -- [] is the
   * legal "pending linkage" state (prescore flags it; the ranked list
   * excludes it into its own section). */
  linked_cause_ids: string[];
  impact: number;
  effort: number;
  criterion_scores: SolutionCriterionScore[];
}

/** Per-solution computed view -- present once the engine has echoed the
 * artifact back (FmeaRow.rpn's "server-computed, never hand-typed"
 * contract, at the artifact level since weighted_total needs `criteria` too). */
export interface SolutionScore {
  solution_id: string;
  quadrant: Quadrant;
  weighted_total: number | null;
}

export interface RankedEntry {
  rank: number;
  solution_id: string;
  name: string;
  quadrant: Quadrant;
  weighted_total: number | null;
  impact: number;
  effort: number;
  linked_cause_ids: string[];
}

export interface UnlinkedSolution {
  solution_id: string;
  name: string;
  reason: string;
}

/** The artifact's headline output (PLAN §4.1): the queue the Improve loop
 * works through. */
export interface RankedFixList {
  ranked: RankedEntry[];
  unlinked: UnlinkedSolution[];
}

export interface SolutionMatrixArtifact extends ArtifactBase {
  tool_id: "T-18";
  solutions: Solution[];
  criteria: SolutionCriterion[];
  /** Server-computed, never hand-typed -- present once the engine has
   * echoed the artifact back. */
  scores?: Computed<SolutionScore[]> | null;
  ranked_fix_list?: Computed<RankedFixList> | null;
}

// ---- T-19 Pilot Plan (artifacts/pilot_plan.py) ----

export type ComparisonKind = "before_period" | "parallel_group";
export type PilotDirection = "higher_is_better" | "lower_is_better";
export type PilotStatus = "designed" | "running" | "complete";
export const PILOT_STATUSES: PilotStatus[] = ["designed", "running", "complete"];

/** One entry in the append-only `changes` list -- the structural EXIT-10
 * trigger (artifacts/pilot_plan.py): capped at length 1 server-side, a
 * second entry raises EXIT-10 by name on save. */
export interface PilotChange {
  change_id: string;
  text: string;
}

export interface PilotTheOneChange {
  statement: string;
  linked_solution_id?: string | null;
  linked_cause_ids: string[];
}

export interface PilotComparisonDesign {
  kind: ComparisonKind;
  description: string;
}

export interface PilotInclusion {
  who_or_what: string;
  how_selected: string;
  honesty_note: string;
}

export interface PilotSuccessThreshold {
  metric_ref: string;
  direction: PilotDirection;
  value: number;
  /** Pre-declaration timestamp, stamped client-side at save (rubric
   * R-IMP-02 #3) -- entry order only, never observation order. */
  declared_at: string;
}

export interface PilotAnalysisPlan {
  expected_route: string;
  rationale: string;
}

export interface PilotConfounderAnswer {
  changed: boolean;
  note: string;
}

export interface PilotConfounderChecklist {
  staffing: PilotConfounderAnswer;
  season: PilotConfounderAnswer;
  demand: PilotConfounderAnswer;
  measurement: PilotConfounderAnswer;
  other: PilotConfounderAnswer;
}

/** Rubric R-IMP-02 #1's "one honest carve-out" (M4 addition,
 * artifacts/pilot_plan.py) -- a genuinely inseparable package, declared up
 * front. When present, `changes` must carry exactly one entry per listed
 * component (1:1) and EXIT-10 does not fire for that declared set. */
export interface PilotDeclaredPackage {
  rationale: string;
  components: string[];
}

export interface PilotPlanArtifact extends ArtifactBase {
  tool_id: "T-19";
  the_one_change: PilotTheOneChange;
  changes: PilotChange[];
  comparison_design: PilotComparisonDesign;
  inclusion: PilotInclusion;
  success_threshold: PilotSuccessThreshold;
  analysis_plan: PilotAnalysisPlan;
  falsification_line: string;
  confounder_checklist: PilotConfounderChecklist;
  declared_package?: PilotDeclaredPackage | null;
  /** Server-stamped whenever declared_package is present -- "package-level
   * credit only, never a single component" (rubric R-IMP-02's carve-out). */
  package_attribution_note?: Computed<string> | null;
  status: PilotStatus;
}

// ---- T-21 Control Charts (artifacts/control_chart.py, stats/p_chart.py) ----

export type ChartType = "imr" | "p";
export type DataShape = "continuous" | "attribute";
export type DefectivesOrDefects = "defectives" | "defects";

export interface ChartSelector {
  data_shape: DataShape;
  defectives_or_defects?: DefectivesOrDefects | null;
}

export interface ControlChartDataSource {
  kind: "dataset" | "check_sheet" | "manual";
  dataset_id?: string | null;
  dataset_sha256?: string | null;
  column?: string | null;
  check_sheet_artifact_id?: string | null;
}

export interface PSubgroup {
  label: string;
  n: number;
  defective_count: number;
}

export interface PChartPoint {
  label: string;
  n: number;
  defective_count: number;
  p: number;
  ucl: number;
  lcl: number;
}

export interface PChartResult {
  k: number;
  total_defectives: number;
  total_n: number;
  p_bar: number;
  points: PChartPoint[];
  signals: ImrSignal[];
  meets_freeze_floor: boolean;
}

export interface ArmedState {
  monitoring_started: boolean;
  cadence_note: string;
}

export interface RecalculationLogEntry {
  reason: string;
  at: string;
  triggered_by: "initial_freeze" | "recalculate";
}

export interface SignalAcknowledgment {
  acknowledged: boolean;
  response_note: string;
  at?: string | null;
}

export interface TrackedSignal {
  signal: ImrSignal;
  acknowledgment: SignalAcknowledgment;
}

/** control_chart.py's EXIT-11 payload shape -- surfaces inside a 422's
 * validation `msg` string (the same ValidationError-as-teaching-text
 * move pilot_plan.py's EXIT-10 uses), never as a separate JSON field. */
export interface ControlChartArtifact extends ArtifactBase {
  tool_id: "T-21";
  chart_type: ChartType;
  metric_ref: string;
  selector: ChartSelector;
  source: ControlChartDataSource;
  imr_values?: number[] | null;
  p_subgroups?: PSubgroup[] | null;
  /** Western Electric zone rules 2/3, opt-in (M4 addition, matrix VI.A.1)
   * -- I-MR only, default false; the engine rejects either true on a
   * p-chart (control_chart.py has no zone-rule math for it). Applies to
   * the live MONITORING read (`signals`), not the frozen limits. */
  rule2_enabled: boolean;
  rule3_enabled: boolean;
  freeze_requested: boolean;
  recalculate_reason?: string | null;
  action_at?: string | null;
  frozen_at?: string | null;
  source_dataset_hash?: string | null;
  frozen_window_values?: number[] | null;
  frozen_window_subgroups?: PSubgroup[] | null;
  imr_baseline?: Computed<ImrChartResult> | null;
  p_baseline?: Computed<PChartResult> | null;
  recalculation_log: RecalculationLogEntry[];
  armed: ArmedState;
  acknowledgments: Record<string, SignalAcknowledgment>;
  signals?: Computed<TrackedSignal[]> | null;
}

// ---- T-20 Before/After Proof + Remaining-Gap Check (artifacts/proof.py) ----

export interface ProofDataRef {
  dataset_id?: string | null;
  dataset_sha256?: string | null;
  column?: string | null;
  values: number[];
}

export interface GuardrailInput {
  metric_ref: string;
  direction: PilotDirection;
  before_value: number;
  after_value: number;
}

export interface GuardrailCheck extends GuardrailInput {
  pct_change: number | null;
  moved: "improved" | "worse" | "unchanged";
  material_worsening: boolean;
}

export interface NextCauseRef {
  cause_id: string;
  cause_text: string;
  via_solution_id: string;
  via_solution_name: string;
  rank: number;
}

export interface GapResult {
  charter_baseline_value: number;
  charter_goal_value: number;
  after_value: number;
  direction: PilotDirection;
  original_gap: number;
  recovered: number;
  recovered_pct: number | null;
  remaining: number;
  goal_met: boolean;
  next_cause_ref: NextCauseRef | null;
  loop_verdict: string;
}

export interface ProofVerdict {
  proof_form: "inferential" | "descriptive";
  threshold_verdict: "met" | "not_met";
  weakened: boolean;
  confounder_notes: string[];
  /** Non-null only when the linked pilot declared a package (rubric
   * R-IMP-02's carve-out) -- names the package and states plainly that
   * proof credit belongs to the package, never a single component. Also
   * rides inside `headline` verbatim (artifacts/proof.py's compute_verdict). */
  package_attribution: string | null;
  stability_caveat: string | null;
  guardrail_tradeoff: string | null;
  headline: string;
}

export interface ProofArtifact extends ArtifactBase {
  tool_id: "T-20";
  pilot_ref: string;
  metric_ref: string;
  operational_definition_ref: string;
  measurement_system_ref: string;
  usl?: number | null;
  lsl?: number | null;
  operational_definition_ok: boolean;
  before: ProofDataRef;
  after: ProofDataRef;
  declared_threshold: PilotSuccessThreshold;
  confounders: PilotConfounderChecklist;
  /** Echoed verbatim from the linked T-19 pilot, when it declared one
   * (rubric R-IMP-02's carve-out) -- see ProofVerdict.package_attribution. */
  declared_package?: PilotDeclaredPackage | null;
  guardrails: GuardrailInput[];
  charter_ref: string;
  charter_baseline_value: number;
  charter_goal_value: number;
  charter_goal_direction: PilotDirection;
  next_cause_ref?: NextCauseRef | null;
  before_baseline?: BaselineResult | null;
  after_baseline?: BaselineResult | null;
  test_result?: HypothesisRunResult | null;
  guardrail_report?: Computed<GuardrailCheck[]> | null;
  gap?: Computed<GapResult> | null;
  verdict?: Computed<ProofVerdict> | null;
}

// ---- T-22 Control Plan + Response Plan (OCAP) + Scheduled Check-ins (artifacts/control_plan.py) ----

export type CadenceUnit = "days" | "weeks" | "months";
export const CADENCE_UNITS: CadenceUnit[] = ["days", "weeks", "months"];
export type CheckInVerdict = "pass" | "fail";
export type ControlPlanChartType = "imr" | "p";

export interface ShiftOwner {
  shift: string;
  owner_name: string;
  owner_accepted: boolean;
}

export interface MonitoredItem {
  item_id: string;
  characteristic: string;
  how_measured: string;
  operational_definition_ref: string;
  where: string;
  frequency: string;
  frequency_reason: string;
  is_primary_ctq: boolean;
  is_improve_change: boolean;
  /** Schema-loose on purpose (engine module docstring) -- blank is legal so
   * an ownerless item can be saved and then flagged as theater by
   * plan_health/prescore, never blocked outright. */
  owner_name: string;
  owner_accepted: boolean;
  per_shift_owners: ShiftOwner[];
}

export interface OcapEntry {
  ocap_id: string;
  monitored_item_id: string;
  trigger_signal: string;
  action_steps: string[];
  escalation_trigger: string;
  escalation_contact: string;
  acting_owner: string;
}

export interface TrainingRow {
  row_id: string;
  who: string;
  sop_ref?: string | null;
  by_whom: string;
  by_when?: string | null;
  verified_how: string;
  verified_at?: string | null;
  done: boolean;
}

export interface CheckInCadence {
  unit: CadenceUnit;
  interval: number;
}

/** The caller-resolved snapshot of a T-21 chart's own FROZEN baseline --
 * the desktop copies these numbers in from a loaded ControlChartArtifact,
 * exactly once per freeze, never recomputed here. */
export interface FrozenLimitsRef {
  control_chart_artifact_id: string;
  chart_type: ControlPlanChartType;
  center?: number | null;
  ucl?: number | null;
  lcl?: number | null;
  p_bar?: number | null;
  frozen_at: string;
}

export interface ControlPlanEnteredValues {
  kind: "dataset" | "manual";
  dataset_id?: string | null;
  values?: number[] | null;
  subgroup?: PSubgroup | null;
}

export interface CheckInResult {
  verdict: CheckInVerdict;
  detail: string;
}

export interface CompletedCheckIn {
  check_in_id: string;
  label: string;
  due_date: string;
  completed_at: string;
  entered: ControlPlanEnteredValues;
  note: string;
  /** Server-computed pass/fail against the frozen band -- never hand-typed. */
  result?: Computed<CheckInResult> | null;
}

export interface CheckInSchedule {
  cadence: CheckInCadence;
  start_date: string;
  control_chart_ref: string;
  frozen_limits: FrozenLimitsRef;
  completed: CompletedCheckIn[];
  /** Server-computed = start_date advanced by len(completed) cadence steps. */
  next_due?: Computed<string> | null;
}

export interface PlanHealthResult {
  ownerless_item_ids: string[];
  unaccepted_owner_item_ids: string[];
  check_in_overdue: boolean;
  check_in_overdue_detail: string;
  /** R-CTL-03's Fail line made machine-checkable: true whenever any item is ownerless. */
  is_theater: boolean;
}

export interface ControlPlanArtifact extends ArtifactBase {
  tool_id: "T-22";
  monitored_items: MonitoredItem[];
  ocap_entries: OcapEntry[];
  training_rows: TrainingRow[];
  check_in_schedule?: CheckInSchedule | null;
  /** Caller-supplied "now" for plan_health's overdue read -- never
   * generated client-side except at save time (control_chart.py's
   * action_at precedent). */
  as_of: string;
  plan_health?: Computed<PlanHealthResult> | null;
}

// ---- T-23 5S Audit (scored) (artifacts/five_s.py) ----

export type FiveSCategory = "sort" | "set_in_order" | "shine" | "standardize" | "sustain";
export const FIVE_S_CATEGORIES: FiveSCategory[] = ["sort", "set_in_order", "shine", "standardize", "sustain"];
export const FIVE_S_CATEGORY_LABELS: Record<FiveSCategory, string> = {
  sort: "Sort", set_in_order: "Set in Order", shine: "Shine", standardize: "Standardize", sustain: "Sustain",
};

export interface CategoryScore {
  category: FiveSCategory;
  score: number;
  note: string;
}

/** Rubric R-CTL-05 #3's first path to "recurrence is real" (the second is
 * >=2 existing trend points). */
export interface RecurrenceSchedule {
  cadence_note: string;
  next_round_due?: string | null;
}

export interface AuditRound {
  round_id: string;
  date: string;
  area: string;
  scores: CategoryScore[];
  /** Reuses T-07's FloorPlanRef/floorplan-image store verbatim -- no new
   * photo store for 5S (task brief's reuse instruction). */
  photos: FloorPlanRef[];
  improvement_action: string;
  improvement_action_owner: string;
  /** computed_field on the engine -- present once echoed back. */
  total?: number;
  lowest_category?: FiveSCategory;
}

export interface TrendPoint {
  round_id: string;
  date: string;
  area: string;
  total: number;
  per_category: Record<string, number>;
  lowest_category: FiveSCategory;
}

export interface FiveSArtifact extends ArtifactBase {
  tool_id: "T-23";
  rounds: AuditRound[];
  schedule?: RecurrenceSchedule | null;
  trend?: Computed<TrendPoint[]> | null;
}

// ---- T-24 Standard Work / SOP (artifacts/standard_work.py) ----

export interface SopStep {
  step_id: string;
  order: number;
  action: string;
  standard: string;
  changed_from_prior: boolean;
  /** Unchecked cross-ref -> T-06 ProcessMapArtifact step_id. */
  source_step_ref?: string | null;
  note: string;
}

export interface ChangeLogEntry {
  version: number;
  at: string;
  note: string;
}

export interface StandardWorkArtifact extends ArtifactBase {
  tool_id: "T-24";
  title: string;
  version: number;
  owner: string;
  effective_date: string;
  supersedes?: string | null;
  seeded_from_process_map_id?: string | null;
  linked_control_plan_id?: string | null;
  steps: SopStep[];
  change_log: ChangeLogEntry[];
}

// ---- T-25 A3 Final Report + Tollgate Checklists (artifacts/a3.py) ----

export type A3PanelKind =
  | "background" | "current_condition" | "goal" | "analysis"
  | "countermeasures" | "results" | "follow_up_control" | "lessons";

export const A3_PANEL_ORDER: A3PanelKind[] = [
  "background", "current_condition", "goal", "analysis",
  "countermeasures", "results", "follow_up_control", "lessons",
];

export const A3_PANEL_TITLES: Record<A3PanelKind, string> = {
  background: "Background", current_condition: "Current Condition", goal: "Goal / Target",
  analysis: "Analysis", countermeasures: "Countermeasures", results: "Results / Realized Benefits",
  follow_up_control: "Follow-up / Control", lessons: "Lessons Learned",
};

/** Which tool a "re-seed from artifact" affordance pulls from by default
 * -- a desktop-side hint mirroring artifacts/a3.py's PANEL_SEED_TOOL_HINT. */
export const A3_PANEL_SEED_TOOL_HINT: Record<A3PanelKind, string> = {
  background: "T-03", current_condition: "T-13", goal: "T-03", analysis: "T-15",
  countermeasures: "T-18", results: "T-20", follow_up_control: "T-22", lessons: "T-20",
};

export interface A3SeededFrom {
  artifact_ref: string;
  tool_id: string;
  fields: string[];
}

export interface A3Panel {
  panel: A3PanelKind;
  seeded_from?: A3SeededFrom | null;
  narrative: string;
  seeded_at?: string | null;
}

export interface RealizedBenefitsResult {
  realized_to_date: number;
  net_of_fix_cost: number;
}

export interface RealizedBenefits {
  copq_rerun_artifact_id: string;
  window: string;
  before_amount: number;
  after_amount: number;
  fix_cost: number;
  annualized_projection?: number | null;
  /** Required by the engine whenever annualized_projection is set (rubric
   * R-WRAP-02's Needs-work line: "a projection presented without its
   * basis") -- e.g. "Q2 actuals x 4". Null/omitted only when no
   * projection is entered. */
  annualized_projection_basis?: string | null;
  result?: Computed<RealizedBenefitsResult> | null;
}

export type TollgatePhase = "Define" | "Measure" | "Analyze" | "Improve" | "Control" | "Wrap";
export const TOLLGATE_PHASES: TollgatePhase[] = ["Define", "Measure", "Analyze", "Improve", "Control", "Wrap"];

export interface TollgateQuestion {
  question_id: string;
  text: string;
}

export interface TollgateAnswer {
  question_id: string;
  answered: boolean;
  response: string;
  evidence_ref?: string | null;
}

/** `questions` is engine-stamped (original wording, FmeaAnchors' pattern)
 * -- only `answers` survives a round trip from whatever the client posts. */
export interface TollgateChecklist {
  phase: TollgatePhase;
  questions: TollgateQuestion[];
  answers: TollgateAnswer[];
}

export interface ObjectivesInput {
  charter_baseline_value: number;
  charter_goal_value: number;
  achieved_value: number;
  direction: PilotDirection;
}

export interface LessonEntry {
  lesson_id: string;
  text: string;
  went_wrong: boolean;
}

export interface OpenItem {
  item_id: string;
  description: string;
  owner: string;
}

/** Caller-resolved snapshot of the linked FMEA's own computed
 * blocking_flags (fmea.py, reused verbatim) -- the desktop loads the
 * project's latest T-16 artifact and copies its blocking_flags in. */
export interface FmeaCloseCheckInput {
  fmea_artifact_id: string;
  blocking_flags: FmeaBlockingFlag[];
}

export interface CloseBlockResult {
  close_blocked: boolean;
  blocking_rows: FmeaBlockingFlag[];
  reason: string;
}

export interface ClosureBlock {
  objectives_input?: ObjectivesInput | null;
  /** Server-computed via proof.py's compute_gap, reused verbatim -- same
   * numbers/shape as T-20's own gap panel. */
  objectives_verdict?: Computed<GapResult> | null;
  lessons: LessonEntry[];
  open_items: OpenItem[];
  fmea_check?: FmeaCloseCheckInput | null;
  /** Server-computed -- true whenever the linked FMEA carries an
   * unaddressed severity-9/10 safety/regulatory row (R-WRAP-03/R-ANA-03). */
  close_check?: Computed<CloseBlockResult> | null;
  project_status: "open" | "closed";
}

export interface A3Artifact extends ArtifactBase {
  tool_id: "T-25";
  panels: A3Panel[];
  realized_benefits?: RealizedBenefits | null;
  tollgates: TollgateChecklist[];
  closure: ClosureBlock;
}

// ---- Advisor (Layer 2, PLAN §5, engine/sigma_engine/advisor + routes/advisor.py) ----
// Mirrored field-for-field from context.py's BudgetReport/BudgetDroppedEntry
// and routes/advisor.py's request/response models. The advisor is strictly
// optional -- every one of these calls degrades to a clean, typed
// "unconfigured" response (never a 500) when no API key is set.

// The five PLAN §5.1 modes + "generic" (M5 unit 2) -- mirrors
// routes/advisor.py's AdvisorMode Literal exactly.
export type AdvisorMode = "generic" | "review" | "help_me_think" | "explain" | "tollgate" | "remedy";

/** explain mode's optional focus (PLAN §5.1 mode 3): either a computed
 * result the user clicked (kind/ref read off the tool's own result state)
 * or free text when nothing clickable applies. Untrusted like any other
 * user/UI-sourced text -- the engine wraps it the same way as `question`
 * (advisor/modes.py's AdvisorFocusRef docstring). */
export interface AdvisorFocusRef {
  kind: string;
  ref: string;
}

export interface AdvisorBudgetDroppedEntry {
  tier: string;
  id: string;
  estimated_tokens: number;
}

export interface AdvisorBudgetReport {
  input_budget_tokens: number;
  output_budget_tokens: number;
  estimated_input_tokens: number;
  token_estimate_method: string;
  included: string[];
  dropped: AdvisorBudgetDroppedEntry[];
}

export interface AdvisorAskRequest {
  project_id: string;
  mode: AdvisorMode;
  artifact_id?: string;
  /** Free-text user input, reused across modes rather than one field per
   * mode (routes/advisor.py's own scope-call comment): generic/review's
   * question, help_me_think's optional seed topic, and remedy's optional
   * constraints (budget, headcount, what can't change) all travel here. */
  question?: string;
  /** An id the advisor asked for by name on a prior turn (a
   * REQUEST_ARTIFACT: line in its answer) -- sent back so the next call's
   * assembled context includes that artifact in full, not just a summary. */
  follow_up_artifact_request?: string;
  /** tollgate mode's request shape (PLAN §5.1 mode 4) -- required by the
   * engine whenever mode is "tollgate" (422 otherwise). */
  phase?: TollgatePhase;
  /** explain mode's optional focus (PLAN §5.1 mode 3). */
  focus?: AdvisorFocusRef;
}

/** review mode's structured payload (advisor/modes.py's ReviewResponse). */
export interface AdvisorReviewCriterion {
  criterion_id: string;
  verdict: "pass" | "needs_work";
  specific_fix: string;
}
export interface AdvisorReviewStructured {
  criteria: AdvisorReviewCriterion[];
  overall_note: string;
}

/** help_me_think mode's structured payload (HelpMeThinkResponse). */
export interface AdvisorProposal {
  text: string;
  /** Required (non-null) when the current artifact is a T-15 fishbone;
   * may be null for every other divergent tool (T-05, T-18). */
  evidence_question: string | null;
}
export interface AdvisorHelpMeThinkStructured {
  proposals: AdvisorProposal[];
}

/** tollgate mode's structured payload (TollgateResponse). */
export interface AdvisorTollgateAction {
  action: string;
  tied_to_question_id: string;
}
export interface AdvisorTollgateStructured {
  recommendation: "go" | "go_with_actions" | "no_go";
  reasons: string[];
  actions: AdvisorTollgateAction[];
}

/** remedy mode's structured payload (RemedyResponse) -- the flagship. */
export interface AdvisorRemedyCandidate {
  title: string;
  why_it_fits_the_verified_cause: string;
  cause_ids: string[];
  estimated_cost_band: "low" | "medium" | "high";
  risks: string;
  pilot_first: string;
  how_youd_know_it_worked: string;
}
export interface AdvisorRemedyStructured {
  remedies: AdvisorRemedyCandidate[];
}

export interface AdvisorAskResponse {
  mode: AdvisorMode;
  /** Always present: a prose mode's (generic/explain) answer text, or a
   * structured mode's raw last-attempt text (useful for display even when
   * `structured` is null, e.g. the unstructured_fallback case). */
  answer: string;
  /** The mode-specific parsed payload -- cast to the right
   * Advisor*Structured interface based on `mode` (review ->
   * AdvisorReviewStructured, help_me_think -> AdvisorHelpMeThinkStructured,
   * tollgate -> AdvisorTollgateStructured, remedy -> AdvisorRemedyStructured).
   * Always null for a prose mode (generic/explain). */
  structured: AdvisorReviewStructured | AdvisorHelpMeThinkStructured | AdvisorTollgateStructured | AdvisorRemedyStructured | null;
  /** True exactly when a structured mode's response failed to parse even
   * after its one retry -- render `answer` as plain text with a "the model
   * returned unstructured output" note, never as a blank/broken card. */
  unstructured_fallback: boolean;
  budget_report: AdvisorBudgetReport;
  /** Artifact ids the model asked for by name on this turn, parsed from
   * its answer -- the UI's cue to offer a follow-up call with
   * follow_up_artifact_request set to one of these. */
  requested_artifact_ids: string[];
}

export interface AdvisorSettingsResponse {
  /** Masked (last-4-only) or null if nothing is stored -- never the real
   * key (routes/advisor.py: "write-only, masked on read"). */
  api_key_masked: string | null;
  base_url: string | null;
  enabled: boolean;
}

export interface AdvisorSettingsUpdateRequest {
  /** Omit or send "" to leave the stored key unchanged -- the GET response
   * never echoes the real key back, so a settings form can't round-trip it
   * into this field. A non-empty string sets/overwrites it. */
  api_key?: string | null;
  base_url?: string | null;
  enabled: boolean;
}

export interface AdvisorStatusResponse {
  configured: boolean;
  model: string;
}
