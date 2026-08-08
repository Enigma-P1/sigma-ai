import { Button, Field, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { AttributeStudyFields } from "./AttributeStudyFields";
import { ContinuousStudyFields } from "./ContinuousStudyFields";
import { Exit03Panel } from "./Exit03Panel";
import { MsaResultView } from "./MsaResultView";
import { PrescoreStrip } from "../PrescoreStrip";
import { MSA_CHECK_LABELS } from "./msaChecks";
import { useMsaForm } from "./useMsaForm";
import type { MsaDataType, ProjectMetadata } from "../../api/types";
import "./MsaForm.css";

export interface MsaFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-12 Measurement Check: study designer (continuous or attribute path),
 * readings entry grid, run -> verdict rendered with the band, the named
 * denominator, the caveat, and the EXIT-02 stop panel on fail. Nothing
 * here is computed client-side -- MsaResultView renders the engine's own
 * response, same contract as BaselineResultView (T-13). */
export function MsaForm({ projectId, project, onSaved }: MsaFormProps) {
  const f = useMsaForm(projectId, project, onSaved);

  return (
    <Panel title="Measurement Check (MSA)" right={f.version != null && <span data-testid="msa-version-badge">v{f.version} saved</span>}>
      <p>
        A resolution pre-check first (can the gauge even see the process?), then either test/retest repeatability%
        (continuous) or two-rater kappa + % agreement (attribute) — the narrow, honestly-named check this suite
        runs. Full multi-operator Gage R&amp;R is out of scope; see &ldquo;Is your question bigger than this
        check?&rdquo; below.
      </p>

      <div className="sigma-msa-row">
        <Field label="Data type" htmlFor="msa-data-type">
          <SelectInput
            id="msa-data-type" data-testid="msa-data-type" value={f.dataType}
            onChange={(e) => f.setDataType(e.target.value as MsaDataType)}
          >
            <option value="continuous">Continuous (test/retest repeatability%)</option>
            <option value="attribute">Attribute (two-rater judgment)</option>
          </SelectInput>
        </Field>
        <Field label="Operator" required htmlFor="msa-operator" helper="Single-operator study — who ran it.">
          <TextInput id="msa-operator" data-testid="msa-operator" value={f.operator} onChange={(e) => f.setOperator(e.target.value)} />
        </Field>
      </div>

      {f.dataType === "continuous" ? (
        <ContinuousStudyFields
          gaugeName={f.gaugeName} onGaugeNameChange={f.setGaugeName}
          gaugeIncrementText={f.gaugeIncrementText} onGaugeIncrementChange={f.setGaugeIncrementText}
          uslText={f.uslText} onUslChange={f.setUslText} lslText={f.lslText} onLslChange={f.setLslText}
          items={f.continuousItems} onItemsChange={f.updateContinuousItems}
        />
      ) : (
        <AttributeStudyFields items={f.attributeItems} onItemsChange={f.updateAttributeItems} />
      )}

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="msa-run">
        {f.saving ? "Running…" : f.version != null ? "Re-run measurement check" : "Run measurement check"}
      </Button>

      {f.serverArtifact?.result && <MsaResultView result={f.serverArtifact.result} />}

      <PrescoreStrip results={f.prescore} labels={MSA_CHECK_LABELS} />

      <Exit03Panel />
    </Panel>
  );
}
