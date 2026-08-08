import { Button, Field, MissingHint, Panel, TextInput, VerdictBanner } from "../../design/components";
import { SpaghettiCanvas } from "./SpaghettiCanvas";
import { FloorPlanUpload } from "./FloorPlanUpload";
import { CalibrationPanel } from "./CalibrationPanel";
import { OperatorsPanel } from "./OperatorsPanel";
import { TraceControls } from "./TraceControls";
import { RoutesList } from "./RoutesList";
import { DeltaPanel } from "./DeltaPanel";
import { PlaybackControls } from "./PlaybackControls";
import { PrescoreStrip } from "../PrescoreStrip";
import { SPAGHETTI_CHECK_LABELS } from "./spaghettiChecks";
import { spaghettiMissingFields } from "./spaghettiLogic";
import { useSpaghettiForm } from "./useSpaghettiForm";
import type { LayoutMode, ProjectMetadata } from "../../api/types";
import "./SpaghettiForm.css";

export interface SpaghettiFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

const LAYOUT_MODE_OPTIONS: { value: LayoutMode; label: string }[] = [
  { value: "current", label: "Current" },
  { value: "proposed", label: "Proposed" },
];

/** T-07 Spaghetti Diagram: upload, calibrate, trace, and read the engine's
 * own metrics -- the interactive flagship (PLAN §4.1). Every number on
 * this screen (distance, walk time, daily burden, crossings, the delta
 * table) comes from SpaghettiArtifact.metrics as saved by the engine;
 * nothing here recomputes a claimed figure client-side. */
export function SpaghettiForm({ projectId, project, onSaved }: SpaghettiFormProps) {
  const f = useSpaghettiForm(projectId, project, onSaved);
  const unit = f.serverArtifact?.metrics?.value.unit ?? f.calibration?.unit ?? null;

  return (
    <Panel title="Spaghetti Diagram (interactive)" right={f.version != null && <span data-testid="spaghetti-version-badge">v{f.version} saved</span>}>
      <p>
        Upload the floor plan, calibrate scale by drawing one known-length line, then trace routes per operator and
        trip. Distance, walk time, and the daily travel burden are the engine&rsquo;s own arithmetic on your trace —
        nothing here is eyeballed.
      </p>

      <FloorPlanUpload
        hasFloorPlan={f.floorPlan != null} sourceFilename={f.floorPlan?.source_filename}
        uploading={f.uploadingFloorPlan} error={f.floorPlanError} onFileSelected={(file) => void f.handleFloorPlanSelected(file)}
      />

      <CalibrationPanel
        calibration={f.calibration} draftPoints={f.calibrationDraft} calibrating={f.calibrating}
        onStart={f.startCalibration} onConfirm={f.confirmCalibration} onCancel={f.cancelCalibration}
      />

      <div className="sigma-spaghetti-mode-row">
        <Field label="Layout mode" htmlFor="spaghetti-layout-mode-current">
          <div className="sigma-spaghetti-mode-toggle">
            {LAYOUT_MODE_OPTIONS.map((opt) => (
              <Button
                key={opt.value} variant={f.activeLayoutMode === opt.value ? "primary" : "ghost"} size="sm"
                onClick={() => f.setActiveLayoutMode(opt.value)} data-testid={`spaghetti-layout-mode-${opt.value}`}
              >
                {opt.label}
              </Button>
            ))}
          </div>
        </Field>
        <label className="sigma-spaghetti-heatmap-toggle">
          <input type="checkbox" data-testid="spaghetti-heatmap-toggle" checked={f.heatmapOn} onChange={(e) => f.setHeatmapOn(e.target.checked)} />
          Heatmap (line width/opacity scaled by frequency — display only)
        </label>
      </div>

      <SpaghettiCanvas
        imageSrc={f.floorPlanImageSrc} imageWidth={f.floorPlan?.width_px ?? 0} imageHeight={f.floorPlan?.height_px ?? 0}
        mode={f.canvasMode} calibration={f.calibration} calibrationDraft={f.calibrationDraft}
        operators={f.operators} routes={f.routes} traceDraft={f.traceDraft} activeLayoutMode={f.activeLayoutMode}
        heatmapOn={f.heatmapOn} playbackRouteId={f.playbackRouteId} playing={f.playing} onCanvasClick={f.handleCanvasClick}
      />

      <TraceControls
        operators={f.operators} tracing={f.tracing} draftPoints={f.traceDraft} activeLayoutMode={f.activeLayoutMode}
        operatorId={f.traceOperatorId} tripLabel={f.traceTripLabel} frequencyText={f.traceFrequencyText}
        onOperatorChange={f.setTraceOperatorId} onTripLabelChange={f.setTraceTripLabel} onFrequencyChange={f.setTraceFrequencyText}
        onStart={f.startTrace} onUndo={f.undoTracePoint} onFinish={f.finishTrace} onCancel={f.cancelTrace}
      />

      <div className="sigma-spaghetti-panels-row">
        <OperatorsPanel operators={f.operators} onAdd={f.addOperator} onUpdate={f.updateOperator} onRemove={f.removeOperator} />
        <RoutesList routes={f.routes} operators={f.operators} metricsByRouteId={f.metricsByRouteId} onRemove={f.removeRoute} />
      </div>

      <DeltaPanel delta={f.serverArtifact?.metrics?.value.delta ?? null} unit={unit} />

      <PlaybackControls
        routes={f.routes} activeLayoutMode={f.activeLayoutMode} selectedRouteId={f.playbackRouteId}
        playing={f.playing} onSelectRoute={f.setPlaybackRouteId} onTogglePlay={f.togglePlay}
      />

      <Panel title="Walk speed & observation window" collapsible defaultOpen={false}>
        <Field label="Walk speed override (units/min)" htmlFor="spaghetti-walk-speed" helper="Leave blank to use the engine's cited default (84 m/min ≈ 1.4 m/s).">
          <TextInput
            id="spaghetti-walk-speed" type="number" min={0} data-testid="spaghetti-walk-speed"
            value={f.walkSpeedOverrideText} onChange={(e) => f.setWalkSpeedOverrideText(e.target.value)}
          />
        </Field>
        <div className="sigma-spaghetti-inspector-row">
          <Field label="When" htmlFor="spaghetti-obs-when">
            <TextInput id="spaghetti-obs-when" data-testid="spaghetti-obs-when" value={f.observationWindow.when} onChange={(e) => f.setObservationWindow({ ...f.observationWindow, when: e.target.value })} />
          </Field>
          <Field label="Duration" htmlFor="spaghetti-obs-duration">
            <TextInput id="spaghetti-obs-duration" data-testid="spaghetti-obs-duration" value={f.observationWindow.duration} onChange={(e) => f.setObservationWindow({ ...f.observationWindow, duration: e.target.value })} />
          </Field>
          <Field label="Shift" htmlFor="spaghetti-obs-shift">
            <TextInput id="spaghetti-obs-shift" data-testid="spaghetti-obs-shift" value={f.observationWindow.shift} onChange={(e) => f.setObservationWindow({ ...f.observationWindow, shift: e.target.value })} />
          </Field>
        </div>
      </Panel>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="spaghetti-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={spaghettiMissingFields(f.floorPlan)} />}

      <PrescoreStrip results={f.prescore} labels={SPAGHETTI_CHECK_LABELS} />
    </Panel>
  );
}
