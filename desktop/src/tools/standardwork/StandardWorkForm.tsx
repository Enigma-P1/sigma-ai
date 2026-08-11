import { Button, Field, MissingHint, Panel, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { StepsEditor } from "./StepsEditor";
import { STANDARD_WORK_CHECK_LABELS } from "./standardWorkChecks";
import { useStandardWorkForm } from "./useStandardWorkForm";
import type { ProjectMetadata } from "../../api/types";
import "./StandardWorkForm.css";
import { ReportButton } from "../../app/ReportButton";

export interface StandardWorkFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-24 Standard Work / SOP: the improved method written down so it
 * survives the author. Steps can seed from the T-06 process map's current
 * steps, then get their own standard filled in. */
export function StandardWorkForm({ projectId, project, onSaved }: StandardWorkFormProps) {
  const f = useStandardWorkForm(projectId, project, onSaved);

  return (
    <Panel title="Standard Work / SOP" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="standardwork-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-24"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
      <p>Write the improved method as steps a qualified-but-new person could follow -- one action, one standard, per step.</p>

      <div className="sigma-standardwork-header">
        <Field label="Title" htmlFor="standardwork-title"><TextInput id="standardwork-title" data-testid="standardwork-title" value={f.state.title} onChange={(e) => f.update({ title: e.target.value })} /></Field>
        <Field label="Version" htmlFor="standardwork-version"><TextInput id="standardwork-version" type="number" min={1} value={f.state.version} onChange={(e) => f.update({ version: Number(e.target.value) })} /></Field>
        <Field label="Owner" htmlFor="standardwork-owner"><TextInput id="standardwork-owner" data-testid="standardwork-owner" value={f.state.owner} onChange={(e) => f.update({ owner: e.target.value })} /></Field>
        <Field label="Effective date" htmlFor="standardwork-effective"><TextInput id="standardwork-effective" type="date" value={f.state.effectiveDate} onChange={(e) => f.update({ effectiveDate: e.target.value })} /></Field>
        <Field label="Supersedes (prior instruction, if any)" htmlFor="standardwork-supersedes"><TextInput id="standardwork-supersedes" value={f.state.supersedes ?? ""} onChange={(e) => f.update({ supersedes: e.target.value || null })} /></Field>
      </div>

      {f.processMapSteps.length > 0 && (
        <Button variant="ghost" size="sm" onClick={f.seedFromProcessMap} data-testid="standardwork-seed-from-process-map">
          Seed steps from the process map ({f.processMapSteps.length} step(s))
        </Button>
      )}

      <StepsEditor steps={f.state.steps} onChange={f.updateStep} onRemove={f.removeStep} onAdd={f.addStep} />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-standardwork-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="standardwork-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={STANDARD_WORK_CHECK_LABELS} />
    </Panel>
  );
}
