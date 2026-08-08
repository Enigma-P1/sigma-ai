import { Button, Field, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { OperationalDefinitionFields } from "./OperationalDefinitionFields";
import { StratificationFactorsFields } from "./StratificationFactorsFields";
import { LogisticsFields } from "./LogisticsFields";
import { PrescoreStrip } from "../PrescoreStrip";
import { COLLECTION_PLAN_CHECK_LABELS } from "./collectionPlanChecks";
import { useCollectionPlanForm } from "./useCollectionPlanForm";
import { DATA_COLLECTION_DATA_TYPES } from "../../api/types";
import type { DataCollectionDataType, ProjectMetadata } from "../../api/types";
import "./CollectionPlanForm.css";

export interface CollectionPlanFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-11's PLAN half (rubric R-MEA-05): metric link, operational
 * definition, data type, stratification factors, collection logistics,
 * bias note. The import and sample-size halves are separate forms --
 * see T11Screen, which tabs all three together. */
export function CollectionPlanForm({ projectId, project, onSaved }: CollectionPlanFormProps) {
  const f = useCollectionPlanForm(projectId, project, onSaved);

  return (
    <Panel title="Data Collection Plan" right={f.version != null && <span data-testid="dcp-version-badge">v{f.version} saved</span>}>
      <div className="sigma-dcp-row">
        <Field label="Metric name" htmlFor="dcp-metric-name">
          <TextInput id="dcp-metric-name" data-testid="dcp-metric-name" value={f.metricName} onChange={(e) => f.setMetricName(e.target.value)} />
        </Field>
        <Field label="Charter metric link (optional)" htmlFor="dcp-charter-metric-id" helper="The charter's SMART-goal metric name, if this plan measures it.">
          <TextInput id="dcp-charter-metric-id" data-testid="dcp-charter-metric-id" value={f.charterMetricId} onChange={(e) => f.setCharterMetricId(e.target.value)} />
        </Field>
      </div>

      <OperationalDefinitionFields value={f.operationalDefinition} onChange={f.setOperationalDefinition} />

      <Field label="Data type" htmlFor="dcp-data-type" helper="This one field drives every downstream chart and test route.">
        <SelectInput
          id="dcp-data-type" data-testid="dcp-data-type" value={f.dataType ?? ""}
          onChange={(e) => f.setDataType((e.target.value || null) as DataCollectionDataType | null)}
        >
          <option value="">Select…</option>
          {DATA_COLLECTION_DATA_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </SelectInput>
      </Field>

      <StratificationFactorsFields
        factors={f.stratificationFactors} onChange={f.setStratificationFactors}
        noReason={f.noStratificationReason} onNoReasonChange={f.setNoStratificationReason}
      />

      <LogisticsFields value={f.logistics} onChange={f.setLogistics} biasNote={f.biasNote} onBiasNoteChange={f.setBiasNote} />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="dcp-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>

      <PrescoreStrip results={f.prescore} labels={COLLECTION_PLAN_CHECK_LABELS} />
    </Panel>
  );
}
