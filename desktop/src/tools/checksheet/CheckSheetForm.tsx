import { useState } from "react";
import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { CategorySetup } from "./CategorySetup";
import { TallyView } from "./TallyView";
import { TranscribePanel } from "./TranscribePanel";
import { EntriesTable } from "./EntriesTable";
import { PrescoreStrip } from "../PrescoreStrip";
import { CHECK_SHEET_CHECK_LABELS } from "./checkSheetChecks";
import { checkSheetMissingFields, tallyCounts } from "./checkSheetLogic";
import { useCheckSheetForm } from "./useCheckSheetForm";
import type { ProjectMetadata } from "../../api/types";
import "./CheckSheetForm.css";

type EntryModeTab = "live" | "transcribe";

export interface CheckSheetFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
  /** Deep-link callback (M2 brief: "a simple navigation param") -- fired
   * with the T-14 tool id and the freshly-exported dataset id once "send
   * to Pareto" succeeds, so ProjectWorkspace can jump there with the
   * dataset preselected. */
  onNavigateToDataset?: (toolId: string, datasetId: string) => void;
}

/** T-08 Check Sheet / Tally: category + strata setup, the tap-to-count
 * field view, the captured entries log, then save and (once saved) export
 * to a dataset that feeds Pareto with zero re-entry (rubric R-MEA-06 #3). */
export function CheckSheetForm({ projectId, project, onSaved, onNavigateToDataset }: CheckSheetFormProps) {
  const f = useCheckSheetForm(projectId, project, onSaved);
  const [mode, setMode] = useState<EntryModeTab>("live");

  return (
    <Panel title="Check Sheet / Tally" right={f.version != null && <span data-testid="checksheet-version-badge">v{f.version} saved</span>}>
      <CategorySetup
        categories={f.categories} onAddCategory={f.addCategory} onUpdateCategory={f.updateCategory} onRemoveCategory={f.removeCategory}
        strataFields={f.strataFields} onAddStrataField={f.addStrataField} onUpdateStrataField={f.updateStrataField} onRemoveStrataField={f.removeStrataField}
      />

      <div className="sigma-checksheet-mode-tabs" role="tablist" aria-label="How entries are being captured">
        <Button
          variant={mode === "live" ? "primary" : "secondary"} size="sm" type="button"
          onClick={() => setMode("live")} data-testid="checksheet-mode-live"
        >
          Live tally
        </Button>
        <Button
          variant={mode === "transcribe" ? "primary" : "secondary"} size="sm" type="button"
          onClick={() => setMode("transcribe")} data-testid="checksheet-mode-transcribe"
        >
          Transcribe a paper tally
        </Button>
      </div>

      {mode === "live" ? (
        <TallyView
          categories={f.categories} strataFields={f.strataFields} strataOptions={f.strataOptions}
          activeStrata={f.activeStrata} onSetActiveStratum={f.setActiveStratumValue} onAddStrataOption={f.addStrataOption}
          tallyCounts={tallyCounts(f.entries)} onTap={f.tap}
        />
      ) : (
        <TranscribePanel categories={f.categories} onLog={f.logTranscribed} />
      )}

      <EntriesTable entries={f.entries} categories={f.categories} strataFields={f.strataFields} onUpdateNote={f.updateEntryNote} onDeleteEntry={f.deleteEntry} />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="checksheet-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={checkSheetMissingFields(f.categories)} />}

      <PrescoreStrip results={f.prescore} labels={CHECK_SHEET_CHECK_LABELS} />

      <div className="sigma-checksheet-export">
        {f.sendError && <VerdictBanner tone="fail" headline={f.sendError} />}
        {f.dataset ? (
          <div data-testid="checksheet-dataset-ready">
            <VerdictBanner
              tone="pass" headline={`Exported ${f.dataset.row_count} rows to a dataset`}
              detail="Pareto reads this dataset's category column directly -- nothing re-typed."
              actions={
                <Button variant="primary" data-testid="checksheet-go-to-pareto" onClick={() => onNavigateToDataset?.("T-14", f.dataset!.dataset_id)}>
                  Open in Pareto (T-14)
                </Button>
              }
            />
          </div>
        ) : (
          <Button variant="secondary" disabled={f.version == null || f.sendingToPareto} onClick={() => void f.handleSendToPareto()} data-testid="checksheet-send-to-pareto">
            {f.sendingToPareto ? "Exporting…" : "Send to Pareto"}
          </Button>
        )}
      </div>
    </Panel>
  );
}
