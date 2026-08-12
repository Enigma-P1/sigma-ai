import { Button, Field, Panel, VerdictBanner } from "../../design/components";
import { ColumnPreviewTable } from "./ColumnPreviewTable";
import { DatasetRowsView } from "./DatasetRowsView";
import { qualityFindingLines, summarizeQuality } from "./dataImportLogic";
import { useDataImportForm } from "./useDataImportForm";
import "./DataImportForm.css";

export interface DataImportFormProps {
  projectId: string;
  onSaved: () => void;
}

/** T-11's import half (PLAN §4.1 Data Collection Plan row; sample-size
 * guidance is a later unit): upload -> confirmable column-type preview ->
 * plain quality scan -> save to the project. */
export function DataImportForm({ projectId, onSaved }: DataImportFormProps) {
  const f = useDataImportForm(projectId, onSaved);
  const quality = f.preview ? summarizeQuality(f.preview.quality) : null;

  return (
    <Panel title="Data Collection Plan — import a dataset">
      <Field
        label="Upload a CSV or XLSX file"
        helper="Column types are inferred automatically. Confirm or change them below, review the quality scan, then save."
      >
        <input
          type="file"
          accept=".csv,.xlsx"
          data-testid="dataimport-file-input"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void f.handleFileSelected(file);
          }}
        />
      </Field>

      {f.loadingPreview && <p className="sigma-dataimport__status">Reading file…</p>}
      {f.error && <VerdictBanner tone="fail" headline={f.error} />}

      {f.preview && quality && (
        <>
          <ColumnPreviewTable columns={f.preview.columns} onTypeChange={(name, type) => void f.handleColumnTypeChange(name, type)} />

          <div data-testid="dataimport-quality-scan">
            <VerdictBanner
              tone={quality.tone}
              headline={quality.headline}
              detail={
                <ul className="sigma-dataimport__quality-list">
                  {qualityFindingLines(f.preview.quality).map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              }
            />
          </div>

          <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="dataimport-save">
            {f.saving ? "Saving…" : "Save dataset to project"}
          </Button>
        </>
      )}

      {f.savedMeta && (
        <div data-testid="dataimport-save-confirmation">
          <VerdictBanner
            tone="pass"
            headline={`Saved: ${f.savedMeta.row_count} rows as dataset ${f.savedMeta.dataset_id.slice(0, 8)}`}
            detail={`SHA-256 ${f.savedMeta.sha256} — the provenance anchor any baseline computed from this dataset links back to.`}
            actions={
              <Button
                variant="secondary" size="sm" onClick={() => f.handleToggleRows(f.savedMeta!.dataset_id)}
                data-testid="dataimport-view-rows-latest"
              >
                {f.viewingDatasetId === f.savedMeta.dataset_id ? "Hide rows" : "View rows"}
              </Button>
            }
          />
        </div>
      )}

      {f.priorDatasets.length > 0 && (
        <div className="sigma-dataimport__prior">
          <p>Previously imported into this project:</p>
          <ul>
            {f.priorDatasets.map((d) => (
              <li key={d.dataset_id}>
                <span>
                  {d.source_filename} — {d.row_count} rows, saved {d.created_at}
                </span>
                <Button
                  variant="ghost" size="sm" onClick={() => f.handleToggleRows(d.dataset_id)}
                  data-testid={`dataimport-view-rows-${d.dataset_id}`}
                >
                  {f.viewingDatasetId === d.dataset_id ? "Hide rows" : "View rows"}
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {f.viewingDatasetId && (
        <DatasetRowsView projectId={projectId} datasetId={f.viewingDatasetId} onClose={f.closeRows} />
      )}
    </Panel>
  );
}
