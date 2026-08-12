import { useEffect, useState } from "react";
import { listDatasets, previewDataset, saveDataset } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { ColumnType, DatasetMeta, DatasetPreview } from "../../api/types";
import { fileToBase64 } from "./dataImportLogic";

/** All of DataImportForm's state and engine wiring (T-11's import half),
 * pulled into a hook the same way useCopqForm.ts is — the file-read +
 * preview + confirm-types + save flow carries more steps than a plain
 * artifact form's load/save. */
export function useDataImportForm(projectId: string, onSaved: () => void) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [contentBase64, setContentBase64] = useState<string | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [columnTypes, setColumnTypes] = useState<Record<string, ColumnType>>({});
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMeta, setSavedMeta] = useState<DatasetMeta | null>(null);
  const [priorDatasets, setPriorDatasets] = useState<DatasetMeta[]>([]);
  // Which saved dataset's rows are currently expanded below -- at most one
  // at a time (docs/uat/README.md: showing the actual rows back is the
  // point, not a gallery of every dataset open together), reachable from
  // either the just-saved confirmation or the prior-imports list below.
  const [viewingDatasetId, setViewingDatasetId] = useState<string | null>(null);

  function handleToggleRows(datasetId: string) {
    setViewingDatasetId((cur) => (cur === datasetId ? null : datasetId));
  }

  function closeRows() {
    setViewingDatasetId(null);
  }

  /** A derivation control inside the rows view (recode / edit cells / add
   * row / delete rows / derive column) just produced a brand-new
   * DatasetMeta -- never an edit to the one on screen (datasets.py module
   * docstring). This hook owns viewingDatasetId, so DatasetRowsView asks to
   * switch by calling back up here rather than tracking a second "which
   * dataset am I really showing" id that could drift from this one's.
   * Switching what's shown is only half the point, though -- the new
   * dataset also needs to actually show up in "Datasets saved in this
   * project" below once the rows view closes, which is why this refreshes
   * the same list handleSave does. */
  function handleDatasetDerived(meta: DatasetMeta) {
    setViewingDatasetId(meta.dataset_id);
    refreshPriorDatasets();
  }

  function refreshPriorDatasets() {
    listDatasets(projectId)
      .then(setPriorDatasets)
      .catch(() => {
        /* best-effort list; an empty prior-imports panel is still usable */
      });
  }

  useEffect(refreshPriorDatasets, [projectId]);

  async function runPreview(name: string, base64: string, types: Record<string, ColumnType>) {
    setLoadingPreview(true);
    setError(null);
    try {
      setPreview(await previewDataset(projectId, { source_filename: name, content_base64: base64, column_types: types }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not read that file.");
      setPreview(null);
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleFileSelected(file: File) {
    setSavedMeta(null);
    setColumnTypes({});
    setFileName(file.name);
    const base64 = await fileToBase64(file);
    setContentBase64(base64);
    await runPreview(file.name, base64, {});
  }

  async function handleColumnTypeChange(columnName: string, type: ColumnType) {
    const next = { ...columnTypes, [columnName]: type };
    setColumnTypes(next);
    if (fileName && contentBase64) await runPreview(fileName, contentBase64, next);
  }

  async function handleSave() {
    if (!fileName || !contentBase64) return;
    setSaving(true);
    setError(null);
    try {
      const meta = await saveDataset(projectId, {
        source_filename: fileName, content_base64: contentBase64, column_types: columnTypes,
        created_at: new Date().toISOString(),
      });
      setSavedMeta(meta);
      refreshPriorDatasets();
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save this dataset.");
    } finally {
      setSaving(false);
    }
  }

  return {
    fileName, preview, columnTypes, loadingPreview, saving, error, savedMeta, priorDatasets, viewingDatasetId,
    handleFileSelected, handleColumnTypeChange, handleSave, handleToggleRows, closeRows, handleDatasetDerived,
    canSave: preview != null && !saving,
  };
}
