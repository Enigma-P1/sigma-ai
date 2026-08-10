import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { ProcessMapCanvas } from "./ProcessMapCanvas";
import { LanesPanel } from "./LanesPanel";
import { StepsList } from "./StepsList";
import { ConnectorsPanel } from "./ConnectorsPanel";
import { StepInspector } from "./StepInspector";
import { ValueAddPanel } from "./ValueAddPanel";
import { DemandPanel } from "./DemandPanel";
import { Legend } from "./Legend";
import { WasteWalkSummary } from "./WasteWalkSummary";
import { PrescoreStrip } from "../PrescoreStrip";
import { PROCESS_MAP_CHECK_LABELS } from "./processMapChecks";
import { processMapMissingFields } from "./processMapLogic";
import { useProcessMapForm } from "./useProcessMapForm";
import type { ProjectMetadata } from "../../api/types";
import "./ProcessMapForm.css";

export interface ProcessMapFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-06 Process Map (swimlane) + Waste Walk: the interactive canvas map
 * builder -- the first Konva-canvas tool (PLAN §3's reason the product
 * left Streamlit). Every mutation goes through useProcessMapForm; the
 * constraint/longest-step banners render only DemandPanel's server-echoed
 * values, never a client-side max() over step times (matrix §5a A-7). */
export function ProcessMapForm({ projectId, project, onSaved }: ProcessMapFormProps) {
  const f = useProcessMapForm(projectId, project, onSaved);
  const selectedStep = f.steps.find((s) => s.step_id === f.selectedStepId) ?? null;

  return (
    <Panel title="Process Map (swimlane) + Waste Walk" right={f.version != null && <span data-testid="processmap-version-badge">v{f.version} saved</span>}>
      <p>
        Drag steps within or between lanes, connect them to show the flow, tag each value-add / non-value-add /
        enabling with a reason, and walk the 8 wastes. Times and the demand block feed the engine&rsquo;s bottleneck
        readout below -- the map is the one data model every downstream Measure tool reuses.
      </p>

      <Legend />
      <ProcessMapCanvas
        lanes={f.lanes} steps={f.steps} connectors={f.connectors} layout={f.layout}
        selectedStepId={f.selectedStepId} onSelectStep={f.setSelectedStepId} onMoveStep={f.moveStep}
      />
      <WasteWalkSummary steps={f.steps} />

      <div className="sigma-processmap-panels-row">
        <LanesPanel lanes={f.lanes} onAdd={f.addLane} onUpdate={f.updateLane} onRemove={f.removeLane} />
        <StepsList lanes={f.lanes} steps={f.steps} selectedStepId={f.selectedStepId} onSelect={f.setSelectedStepId} onAdd={f.addStep} onRemove={f.removeStep} />
      </div>

      <ConnectorsPanel steps={f.steps} connectors={f.connectors} onAdd={f.addConnector} onRemove={f.removeConnector} />

      {selectedStep && (
        <StepInspector step={selectedStep} lanes={f.lanes} onChange={(patch) => f.updateStep(selectedStep.step_id, patch)} />
      )}

      <DemandPanel
        demand={f.demand} onChange={f.updateDemand}
        longestStep={f.serverArtifact?.longest_step} constraintStep={f.serverArtifact?.constraint_step}
        saved={f.version != null}
      />

      <ValueAddPanel valueAddRatio={f.serverArtifact?.value_add_ratio} saved={f.version != null} />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="processmap-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={processMapMissingFields(f.lanes, f.steps)} />}

      <PrescoreStrip results={f.prescore} labels={PROCESS_MAP_CHECK_LABELS} />
    </Panel>
  );
}
