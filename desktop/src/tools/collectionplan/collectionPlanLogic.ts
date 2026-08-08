import type {
  CollectionLogistics, DataCollectionDataType, DataCollectionPlanArtifact, OperationalDefinition, StratificationFactor,
} from "../../api/types";

export function emptyOperationalDefinition(): OperationalDefinition {
  return {
    what_measured: "", how_instrument: "", precision_unit: "", starts_when: "", stops_when: "",
    two_people_confirmed: false,
  };
}

export function emptyStratificationFactor(): StratificationFactor {
  return { name: "", values_expected: [] };
}

export function emptyLogistics(): CollectionLogistics {
  return { who_collects: "", where_collected: "", when_how_often: "", planned_n: null, sample_size_rationale: "" };
}

/** Structural gate only (PLAN §4.2 hard/soft split -- content completeness
 * is prescore's job): a stratification factor row needs a name to mean
 * anything, mirrored client-side from the engine's own schema rule. */
export function canSaveCollectionPlan(factors: StratificationFactor[]): boolean {
  return factors.every((f) => f.name.trim() !== "");
}

/** A factor's "values expected" is authored as one comma-separated field
 * rather than its own nested dynamic list -- the set is short (2-4 values)
 * and rarely needs per-value structure of its own. */
export function parseValuesExpected(text: string): string[] {
  return text.split(",").map((v) => v.trim()).filter((v) => v !== "");
}

export function formatValuesExpected(values: string[]): string {
  return values.join(", ");
}

export function buildCollectionPlanBody(input: {
  artifactId: string;
  schemaVersion: number;
  metricName: string;
  charterMetricId: string;
  operationalDefinition: OperationalDefinition;
  dataType: DataCollectionDataType | null;
  stratificationFactors: StratificationFactor[];
  noStratificationReason: string;
  logistics: CollectionLogistics;
  biasNote: string;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-11",
    created_at: now,
    updated_at: now,
    metric_name: input.metricName,
    charter_metric_id: input.charterMetricId.trim() === "" ? null : input.charterMetricId.trim(),
    operational_definition: input.operationalDefinition,
    data_type: input.dataType,
    stratification_factors: input.stratificationFactors,
    no_stratification_reason: input.noStratificationReason,
    logistics: input.logistics,
    bias_note: input.biasNote,
  };
}

export function collectionPlanStateFromArtifact(artifact: DataCollectionPlanArtifact) {
  return {
    metricName: artifact.metric_name,
    charterMetricId: artifact.charter_metric_id ?? "",
    operationalDefinition: artifact.operational_definition,
    dataType: artifact.data_type,
    stratificationFactors: artifact.stratification_factors,
    noStratificationReason: artifact.no_stratification_reason,
    logistics: artifact.logistics,
    biasNote: artifact.bias_note,
  };
}
