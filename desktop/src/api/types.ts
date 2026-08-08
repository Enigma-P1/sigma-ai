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

export interface BottleneckResult {
  bottleneck_step_id: string;
  bottleneck_step_name: string;
  bottleneck_time_minutes: number;
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
  /** Server-computed (matrix §5a A-7), never hand-typed -- present once the
   * engine has echoed the artifact back (validate/save/load). Null means
   * "nothing to name yet" (demand incomplete, or no step has a time), not
   * an error. */
  bottleneck?: Computed<BottleneckResult> | null;
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
  ev_percent: number;
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
  /** Server-computed (T-06 bottleneck's pattern), never hand-typed. Null
   * only when there's no calibration yet to scale by. */
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
