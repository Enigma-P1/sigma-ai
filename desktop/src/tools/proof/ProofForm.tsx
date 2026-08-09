import { Button, Field, MissingHint, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { ArraySourceInput } from "../hypothesis/ArraySourceInput";
import { ConfounderChecklistSection } from "../pilotplan/ConfounderChecklistSection";
import { BaselineResultView } from "../baseline/BaselineResultView";
import { GapPanel } from "./GapPanel";
import { useProofForm } from "./useProofForm";
import type { ProjectMetadata } from "../../api/types";

export interface ProofFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

const CHECK_LABELS: Record<string, string> = {
  threshold_as_declared: "Threshold rendered as declared",
  confounder_echo_present: "Confounder echo present",
  guardrail_section_present_or_explicitly_none: "Guardrail section present",
  gap_arithmetic_consistency: "Gap arithmetic consistent",
  metric_identity_single_copy: "Same metric/definition/measurement system",
  capability_language_requires_stability: "Capability language backed by stability",
};

/** T-20 Before/After Proof + Remaining-Gap Check -- where the Improve
 * loop closes. Renders the engine's proof verbatim: side-by-side
 * stability/capability (BaselineResultView, reused as-is -- before_
 * baseline/after_baseline share BaselineResult's exact shape), the test
 * result, the threshold verdict AS DECLARED, the confounder echo, the
 * guardrail table, and the GAP panel. */
export function ProofForm({ projectId, project, onSaved }: ProofFormProps) {
  const f = useProofForm(projectId, project, onSaved);
  const a = f.serverArtifact;
  const pilotIds = Object.keys(project.artifact_index).filter((id) => project.artifact_index[id]?.tool_id === "T-19");

  return (
    <Panel title="Before/After Proof" right={f.version != null && <span data-testid="proof-version-badge">v{f.version} saved</span>}>
      <p>Re-run the engine on the pilot's before/after data: stability, capability, the appropriate test, the threshold as declared, and the loop&rsquo;s remaining gap.</p>

      <div className="sigma-proof-row">
        <Field label="Pilot plan" htmlFor="proof-pilot-ref">
          <SelectInput id="proof-pilot-ref" data-testid="proof-pilot-ref" value={f.state.pilotRef} onChange={(e) => f.update({ pilotRef: e.target.value })}>
            <option value="">Select the pilot this proves…</option>
            {pilotIds.map((id) => <option key={id} value={id}>{id}</option>)}
          </SelectInput>
        </Field>
        <Field label="Metric monitored" htmlFor="proof-metric-ref">
          <TextInput id="proof-metric-ref" data-testid="proof-metric-ref" value={f.state.metricRef} onChange={(e) => f.update({ metricRef: e.target.value })} />
        </Field>
      </div>
      {f.state.declaredPackage && (
        <p data-testid="proof-declared-package-chip">
          Declared package ({f.state.declaredPackage.components.length} components: {f.state.declaredPackage.components.join(", ")}) --
          proof credit is package-level only.
        </p>
      )}
      <div className="sigma-proof-row">
        <Field label="Operational definition (same as baseline)" htmlFor="proof-operational-definition-ref">
          <TextInput id="proof-operational-definition-ref" data-testid="proof-operational-definition-ref" value={f.state.operationalDefinitionRef} onChange={(e) => f.update({ operationalDefinitionRef: e.target.value })} />
        </Field>
        <Field label="Measurement system (same as baseline)" htmlFor="proof-measurement-system-ref">
          <TextInput id="proof-measurement-system-ref" data-testid="proof-measurement-system-ref" value={f.state.measurementSystemRef} onChange={(e) => f.update({ measurementSystemRef: e.target.value })} />
        </Field>
      </div>
      <div className="sigma-proof-row">
        <Field label="USL" htmlFor="proof-usl"><TextInput id="proof-usl" data-testid="proof-usl" value={f.state.uslText} onChange={(e) => f.update({ uslText: e.target.value })} /></Field>
        <Field label="LSL" htmlFor="proof-lsl"><TextInput id="proof-lsl" data-testid="proof-lsl" value={f.state.lslText} onChange={(e) => f.update({ lslText: e.target.value })} /></Field>
      </div>

      <ArraySourceInput value={f.state.before} onChange={(v) => f.update({ before: v })} datasets={f.datasets} datasetDetails={f.datasetDetails} onNeedDatasetDetail={f.loadDatasetDetail} testId="proof-before" labelText="Before period" />
      <ArraySourceInput value={f.state.after} onChange={(v) => f.update({ after: v })} datasets={f.datasets} datasetDetails={f.datasetDetails} onNeedDatasetDetail={f.loadDatasetDetail} testId="proof-after" labelText="After period" />

      <div className="sigma-proof-row">
        <Field label="Declared threshold value" htmlFor="proof-threshold-value">
          <TextInput id="proof-threshold-value" data-testid="proof-threshold-value" value={f.state.thresholdValue} onChange={(e) => f.update({ thresholdValue: e.target.value })} />
        </Field>
        <Field label="Direction" htmlFor="proof-threshold-direction">
          <SelectInput id="proof-threshold-direction" data-testid="proof-threshold-direction" value={f.state.thresholdDirection} onChange={(e) => f.update({ thresholdDirection: e.target.value as "higher_is_better" | "lower_is_better" })}>
            <option value="lower_is_better">Lower is better</option>
            <option value="higher_is_better">Higher is better</option>
          </SelectInput>
        </Field>
      </div>

      <ConfounderChecklistSection value={f.state.confounders} onChange={(v) => f.update({ confounders: v })} />

      <Panel title="Guardrail (consequential metric)">
        <div className="sigma-proof-row">
          <Field label="Guardrail metric" htmlFor="proof-guardrail-metric-ref"><TextInput id="proof-guardrail-metric-ref" data-testid="proof-guardrail-metric-ref" value={f.state.guardrailMetricRef} onChange={(e) => f.update({ guardrailMetricRef: e.target.value })} /></Field>
          <Field label="Direction" htmlFor="proof-guardrail-direction">
            <SelectInput id="proof-guardrail-direction" data-testid="proof-guardrail-direction" value={f.state.guardrailDirection} onChange={(e) => f.update({ guardrailDirection: e.target.value as "higher_is_better" | "lower_is_better" })}>
              <option value="higher_is_better">Higher is better</option>
              <option value="lower_is_better">Lower is better</option>
            </SelectInput>
          </Field>
          <Field label="Before" htmlFor="proof-guardrail-before"><TextInput id="proof-guardrail-before" data-testid="proof-guardrail-before" value={f.state.guardrailBeforeText} onChange={(e) => f.update({ guardrailBeforeText: e.target.value })} /></Field>
          <Field label="After" htmlFor="proof-guardrail-after"><TextInput id="proof-guardrail-after" data-testid="proof-guardrail-after" value={f.state.guardrailAfterText} onChange={(e) => f.update({ guardrailAfterText: e.target.value })} /></Field>
        </div>
      </Panel>

      <Panel title="Charter goal vs baseline (the original gap)">
        <div className="sigma-proof-row">
          <Field label="Charter reference" htmlFor="proof-charter-ref"><TextInput id="proof-charter-ref" data-testid="proof-charter-ref" value={f.state.charterRef} onChange={(e) => f.update({ charterRef: e.target.value })} /></Field>
          <Field label="Charter baseline value" htmlFor="proof-charter-baseline"><TextInput id="proof-charter-baseline" data-testid="proof-charter-baseline" value={f.state.charterBaselineText} onChange={(e) => f.update({ charterBaselineText: e.target.value })} /></Field>
          <Field label="Charter goal value" htmlFor="proof-charter-goal"><TextInput id="proof-charter-goal" data-testid="proof-charter-goal" value={f.state.charterGoalText} onChange={(e) => f.update({ charterGoalText: e.target.value })} /></Field>
        </div>
        {f.state.nextCauseRef && (
          <p data-testid="proof-next-cause-chip">Next verified cause queued: {f.state.nextCauseRef.cause_text} (via {f.state.nextCauseRef.via_solution_name})</p>
        )}
      </Panel>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}
      <div className="sigma-proof-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="proof-save">
          {f.saving ? "Running…" : "Run proof"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      {a?.verdict && (
        <div data-testid="proof-threshold-verdict">
          <VerdictBanner
            tone={a.verdict.value.threshold_verdict === "met" ? "pass" : "fail"}
            headline={a.verdict.value.headline}
            detail={`Declared: ${a.declared_threshold.value} (${a.declared_threshold.direction})`}
          />
        </div>
      )}
      {a?.verdict?.value.weakened && (
        <div data-testid="proof-confounder-echo">
          <VerdictBanner tone="flag" headline="Confounder reported — this proof is weakened" detail={a.verdict.value.confounder_notes.join("; ")} />
        </div>
      )}

      <div className="sigma-proof-baselines">
        {a?.before_baseline && <div data-testid="proof-before-baseline"><BaselineResultView result={a.before_baseline} values={a.before.values} /></div>}
        {a?.after_baseline && <div data-testid="proof-after-baseline"><BaselineResultView result={a.after_baseline} values={a.after.values} /></div>}
      </div>

      {a?.test_result && (
        <div data-testid="proof-test-result">
          <VerdictBanner
            tone={a.test_result.refused ? "exit" : "neutral"}
            headline={a.test_result.refused ? `Refused: ${a.test_result.routing.exit?.exit_id ?? "no test"}` : a.test_result.result?.value.plain_language.comparison_summary ?? ""}
            detail={
              a.verdict?.value.proof_form === "descriptive"
                ? (a.verdict.value.threshold_verdict === "met"
                    ? "Descriptive proof — observed improvement is shown, not statistically tested."
                    : "Descriptive proof — threshold not met, so no improvement is claimed; not statistically tested either way.")
                : a.test_result.result?.value.plain_language.p_value_meaning
            }
          />
        </div>
      )}

      {a?.guardrail_report && a.guardrail_report.value.length > 0 && (
        <table className="sigma-proof-guardrail-table" data-testid="proof-guardrail-table">
          <thead><tr><th>Metric</th><th>Before</th><th>After</th><th>Moved</th></tr></thead>
          <tbody>
            {a.guardrail_report.value.map((g) => (
              <tr key={g.metric_ref}><td>{g.metric_ref}</td><td>{g.before_value}</td><td>{g.after_value}</td><td>{g.moved}{g.material_worsening ? " (material)" : ""}</td></tr>
            ))}
          </tbody>
        </table>
      )}

      {a?.gap && <GapPanel gap={a.gap.value} />}

      <PrescoreStrip results={f.prescore} labels={CHECK_LABELS} />
    </Panel>
  );
}
