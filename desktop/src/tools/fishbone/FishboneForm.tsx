import { Button, Field, MissingHint, Panel, SelectInput, TextArea, VerdictBanner } from "../../design/components";
import { FishboneCanvas } from "./FishboneCanvas";
import { BranchList } from "./BranchList";
import { CauseInspector } from "./CauseInspector";
import { VerifiedCausesSummaryPanel } from "./VerifiedCausesSummaryPanel";
import { PrescoreStrip } from "../PrescoreStrip";
import { FISHBONE_CHECK_LABELS } from "./fishboneChecks";
import { fishboneMissingFields } from "./fishboneLogic";
import { useFishboneForm } from "./useFishboneForm";
import type { ProjectMetadata } from "../../api/types";
import "./FishboneForm.css";
import { ReportButton } from "../../app/ReportButton";

export interface FishboneFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-15 Fishbone (6M) + 5 Whys: the evidence-disciplined cause explorer.
 * Every mutation goes through useFishboneForm; the verified-causes summary
 * renders only the server-echoed Computed<VerifiedCausesSummary>, never a
 * client-side filter over `causes` (DemandPanel.tsx's precedent). */
export function FishboneForm({ projectId, project, onSaved }: FishboneFormProps) {
  const f = useFishboneForm(projectId, project, onSaved);
  const selectedCause = f.causes.find((c) => c.cause_id === f.selectedCauseId) ?? null;
  const parentOfSelected = selectedCause?.parent_cause_id
    ? f.causes.find((c) => c.cause_id === selectedCause.parent_cause_id) ?? null
    : null;
  const charterOptions = Object.keys(project.artifact_index).filter((id) => project.artifact_index[id]?.tool_id === "T-03");

  return (
    <Panel title="Fishbone (6M) + 5 Whys" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="fishbone-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-15"
            captureKey="T-15-fishbone"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
      <p>
        Click a branch to add a candidate cause. Every cause needs an evidence pointer before it can be marked
        verified -- team consensus alone is not evidence. A candidate with no evidence yet carries a visible flag
        until it does.
      </p>

      <div className="sigma-fishbone-effect-row">
        <Field label="Effect statement" required htmlFor="fishbone-effect-text" helper="The baselined problem -- the measured gap, not a convenient symptom of it.">
          <TextArea id="fishbone-effect-text" data-testid="fishbone-effect-text" rows={2} value={f.effectText} onChange={(e) => f.setEffectText(e.target.value)} />
        </Field>
        <Field label="Charter link (optional)" htmlFor="fishbone-charter-ref">
          <SelectInput id="fishbone-charter-ref" data-testid="fishbone-charter-ref" value={f.charterRef} onChange={(e) => f.setCharterRef(e.target.value)}>
            <option value="">-- not linked --</option>
            {charterOptions.map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </SelectInput>
        </Field>
      </div>

      <FishboneCanvas
        effectText={f.effectText} causes={f.causes} layout={f.layout}
        selectedCauseId={f.selectedCauseId} onSelectCause={f.setSelectedCauseId}
        onMoveCause={f.moveCause} onAddCause={f.addCause}
      />

      <div className="sigma-fishbone-panels-row">
        <BranchList causes={f.causes} selectedCauseId={f.selectedCauseId} onSelect={f.setSelectedCauseId} onAdd={f.addCause} />
        {selectedCause ? (
          <CauseInspector
            projectId={projectId} project={project} cause={selectedCause} parent={parentOfSelected}
            onChange={(patch) => f.updateCause(selectedCause.cause_id, patch)} onAskWhy={f.addWhy}
          />
        ) : (
          <Panel title="Cause inspector"><p>Select a cause (or add one from a branch) to edit it here.</p></Panel>
        )}
      </div>

      <VerifiedCausesSummaryPanel summary={f.serverArtifact?.verified_causes} saved={f.version != null} />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="fishbone-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={fishboneMissingFields(f.effectText, f.causes)} />}

      <PrescoreStrip results={f.prescore} labels={FISHBONE_CHECK_LABELS} />
    </Panel>
  );
}
