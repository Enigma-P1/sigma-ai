import { Button, Field, MissingHint, Panel, SelectInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { ComparisonInclusionSection } from "./ComparisonInclusionSection";
import { ConfounderChecklistSection } from "./ConfounderChecklistSection";
import { DeclaredPackageSection } from "./DeclaredPackageSection";
import { FalsificationSection } from "./FalsificationSection";
import { OneChangeSection } from "./OneChangeSection";
import { ThresholdAnalysisSection } from "./ThresholdAnalysisSection";
import { PILOT_PLAN_CHECK_LABELS } from "./pilotPlanChecks";
import { pilotPlanMissingFields } from "./pilotPlanLogic";
import { usePilotPlanForm } from "./usePilotPlanForm";
import type { PilotStatus, ProjectMetadata } from "../../api/types";
import { PILOT_STATUSES } from "../../api/types";
import "./PilotPlanForm.css";
import { ReportButton } from "../../app/ReportButton";

export interface PilotPlanFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

const STATUS_LABELS: Record<PilotStatus, string> = { designed: "Designed", running: "Running", complete: "Complete" };

/** T-19 Pilot Plan: a small-study designer, not a form -- one guided
 * vertical flow, in the order the rubric grades: the one change, the
 * comparison + who/what + honesty, the threshold + analysis plan declared
 * before data, the falsification line, the confounder checklist, then a
 * status control. Every mutation goes through usePilotPlanForm. */
export function PilotPlanForm({ projectId, project, onSaved }: PilotPlanFormProps) {
  const f = usePilotPlanForm(projectId, project, onSaved);
  const declaredAt = f.serverArtifact?.success_threshold.declared_at ?? null;

  return (
    <Panel title="Pilot Plan" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="pilot-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-19"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
      <p>
        Design one small study before you touch anything. One change, a comparison you defined before running it,
        who&rsquo;s included and how you picked them, a threshold and analysis plan declared now, a line that says
        what would prove you wrong, and the confounders you&rsquo;re watching for.
      </p>

      <OneChangeSection
        statement={f.state.primaryChangeText} linkedSolutionId={f.state.linkedSolutionId} extraChanges={f.state.extraChanges}
        exitError={f.exitError} packageActive={f.state.declaredPackage !== null} onStatementChange={(v) => f.update({ primaryChangeText: v })}
        onAddExtraChange={f.addExtraChange} onUpdateExtraChange={f.updateExtraChange} onRemoveExtraChange={f.removeExtraChange}
      />

      <DeclaredPackageSection value={f.state.declaredPackage} onChange={(v) => f.update({ declaredPackage: v })} />

      <ComparisonInclusionSection
        comparisonDesign={f.state.comparisonDesign} inclusion={f.state.inclusion}
        onComparisonChange={(v) => f.update({ comparisonDesign: v })} onInclusionChange={(v) => f.update({ inclusion: v })}
      />

      <ThresholdAnalysisSection
        metricRef={f.state.metricRef} direction={f.state.direction} thresholdValue={f.state.thresholdValue}
        expectedRoute={f.state.expectedRoute} rationale={f.state.rationale} declaredAt={declaredAt}
        onMetricRefChange={(v) => f.update({ metricRef: v })} onDirectionChange={(v) => f.update({ direction: v })}
        onThresholdValueChange={(v) => f.update({ thresholdValue: v })} onExpectedRouteChange={(v) => f.update({ expectedRoute: v })}
        onRationaleChange={(v) => f.update({ rationale: v })}
      />

      <FalsificationSection value={f.state.falsificationLine} onChange={(v) => f.update({ falsificationLine: v })} />

      <ConfounderChecklistSection value={f.state.confounderChecklist} onChange={(v) => f.update({ confounderChecklist: v })} />

      <div className="sigma-pilot-status-row">
        <Field label="Status" htmlFor="pilot-status">
          <SelectInput id="pilot-status" data-testid="pilot-status" value={f.state.status} onChange={(e) => f.update({ status: e.target.value as PilotStatus })}>
            {PILOT_STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
          </SelectInput>
        </Field>
      </div>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-pilot-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="pilot-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={pilotPlanMissingFields(f.state)} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={PILOT_PLAN_CHECK_LABELS} />
    </Panel>
  );
}
