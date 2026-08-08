import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { ElementsSetup } from "./ElementsSetup";
import { StopwatchPanel } from "./StopwatchPanel";
import { CyclesTable } from "./CyclesTable";
import { ElementStatsPanel } from "./ElementStatsPanel";
import { WorkSamplingPanel } from "./WorkSamplingPanel";
import { PrescoreStrip } from "../PrescoreStrip";
import { TIME_STUDY_CHECK_LABELS } from "./timeStudyChecks";
import { timeStudyMissingFields } from "./timeStudyLogic";
import { useTimeStudyForm } from "./useTimeStudyForm";
import type { ProjectMetadata } from "../../api/types";
import "./TimeStudyForm.css";

export interface TimeStudyFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
  /** Deep-link callback, same shape as CheckSheetForm's -- fired with the
   * T-13 tool id and the freshly-exported dataset id once "send to
   * baseline" succeeds for a given element. */
  onNavigateToDataset?: (toolId: string, datasetId: string) => void;
}

/** T-09 Guided Time Study / Work Sampling: elements first (visibly, per
 * PLAN §4.1), then the stopwatch + cycles table, the engine's own
 * per-element stats once saved, the optional work-sampling tab, and a
 * per-element "send to baseline" export (rubric R-MEA-04, zero re-entry). */
export function TimeStudyForm({ projectId, project, onSaved, onNavigateToDataset }: TimeStudyFormProps) {
  const f = useTimeStudyForm(projectId, project, onSaved);

  return (
    <Panel title="Guided Time Study / Work Sampling" right={f.version != null && <span data-testid="timestudy-version-badge">v{f.version} saved</span>}>
      <ElementsSetup elements={f.elements} onAdd={f.addElement} onUpdate={f.updateElement} onRemove={f.removeElement} />

      <div className="sigma-timestudy-section-title">2. Time repeated cycles</div>
      <StopwatchPanel
        elements={f.elements} running={f.stopwatch.running} elapsedMs={f.stopwatch.elapsedMs}
        currentCycleTimes={f.currentCycleTimes} currentNote={f.currentNote} onSetNote={f.setCurrentNote}
        onStart={f.handleStopwatchStart} onSplit={f.handleStopwatchSplit} onFinish={f.handleFinishCycle} onCancel={f.handleCancelCycle}
      />

      <CyclesTable
        elements={f.elements} cycles={f.cycles} onAddCycle={f.addManualCycle}
        onUpdateSeconds={f.updateCycleSeconds} onUpdateNote={f.updateCycleNote} onDeleteCycle={f.deleteCycle}
      />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="timestudy-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={timeStudyMissingFields(f.elements)} />}

      {f.serverArtifact?.element_stats && (
        <ElementStatsPanel stats={f.serverArtifact.element_stats.value} cycles={f.cycles} onEditCycleNote={f.updateCycleNote} />
      )}

      <PrescoreStrip results={f.prescore} labels={TIME_STUDY_CHECK_LABELS} />

      <WorkSamplingPanel
        observations={f.workSampling.observations} onLog={f.workSampling.log}
        onUpdateNote={f.workSampling.updateNote} onRemove={f.workSampling.remove}
        summary={f.serverArtifact?.work_sampling_summary}
      />

      {f.sendError && <VerdictBanner tone="fail" headline={f.sendError} />}
      {f.serverArtifact?.element_stats && (
        <div className="sigma-timestudy-baseline-export">
          <div className="sigma-timestudy-section-title">Send an element to baseline</div>
          {f.serverArtifact.element_stats.value.map((s, i) => {
            const dataset = f.datasetsByElement[s.element_id];
            return (
              <div key={s.element_id} className="sigma-timestudy-baseline-export__row">
                <span>{s.element_name}</span>
                {dataset ? (
                  <div data-testid={`timestudy-dataset-ready-${i}`}>
                    <Button variant="primary" data-testid={`timestudy-go-to-baseline-${i}`} onClick={() => onNavigateToDataset?.("T-13", dataset.dataset_id)}>
                      Open in Baseline (T-13)
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="secondary" disabled={s.n === 0 || f.sendingElementId === s.element_id}
                    onClick={() => void f.handleSendElementToBaseline(s.element_id)} data-testid={`timestudy-send-to-baseline-${i}`}
                  >
                    {f.sendingElementId === s.element_id ? "Exporting…" : "Send to baseline"}
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Panel>
  );
}
