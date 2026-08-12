import { useEffect, useMemo, useState } from "react";
import { Field, Panel, SelectInput, VerdictBanner } from "../../design/components";
import { getDataset, listDatasets } from "../../api/client";
import { ApiError } from "../../api/errors";
import { markToolVisited } from "../../app/toolVisitedStore";
import type { DatasetDetail, DatasetMeta } from "../../api/types";
import { HistogramPanel } from "./HistogramPanel";
import { RunChartPanel } from "./RunChartPanel";
import { ParetoPanel } from "./ParetoPanel";
import { ScatterPanel } from "./ScatterPanel";
import { BoxPanel } from "./BoxPanel";
import { FilterPanel } from "./FilterPanel";
import { applyRowFilter } from "./chartSetLogic";
import { loadChartSetView, saveChartSetView } from "./chartSetViewStore";
import "./ChartSetScreen.css";

export interface ChartSetScreenProps {
  projectId: string;
  /** T-08's "send to Pareto" deep link (ToolRouter's DatasetPreset) --
   * preselects the dataset once it loads. */
  initialDatasetId?: string;
  /** Fired once charts have rendered for a chosen dataset (Jordan
   * usability fix: T-14 has no artifact of its own, so it could never
   * mark itself Done in the rail). ToolRouter wires this to the same
   * onSaved callback every artifact-backed tool already uses to refresh
   * the rail after a change -- the mark itself is toolVisitedStore.ts. */
  onVisited?: () => void;
}

/** T-14: pick a dataset, then the five-chart set, each with its own
 * column picker and its own engine-computed verdict headline (M2 brief).
 * Rows are fetched once here and passed down — chart panels only choose
 * which stored columns to look at, they don't compute statistics.
 *
 * The dataset and every panel's column choice are remembered per project
 * (chartSetViewStore.ts, PLAN 2.1) and restored the next time this screen
 * opens, so "the chart I made" survives a close-and-reopen instead of
 * having to be rebuilt from scratch. The filter (PLAN 2.5) is deliberately
 * not remembered -- see that store's own note on why. */
export function ChartSetScreen({ projectId, initialDatasetId, onVisited }: ChartSetScreenProps) {
  // Read once per project -- recomputed only if `projectId` itself changes,
  // never on this screen's own re-renders.
  const restoredView = useMemo(() => loadChartSetView(projectId), [projectId]);

  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [datasetsLoaded, setDatasetsLoaded] = useState(false);
  const [datasetId, setDatasetId] = useState("");
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presetApplied, setPresetApplied] = useState(false);
  // The remembered dataset (or the T-08 deep link) named an id this project
  // doesn't have -- deleted, or just never real to begin with. Said plainly
  // instead of a silent empty picker, which would read as the screen having
  // forgotten everything rather than just the one dataset.
  const [restoredDatasetMissing, setRestoredDatasetMissing] = useState(false);

  const [filterColumn, setFilterColumn] = useState("");
  const [filterValues, setFilterValues] = useState<string[]>([]);

  useEffect(() => {
    listDatasets(projectId)
      .then(setDatasets)
      .catch(() => {
        /* an empty picker is still an honest state -- T-11 hasn't been used yet */
      })
      .finally(() => setDatasetsLoaded(true));
  }, [projectId]);

  useEffect(() => {
    if (presetApplied || !datasetsLoaded) return;
    setPresetApplied(true);
    // T-08's deep link is a fresher, more specific intent than whatever was
    // open last time, so it wins outright when both are present.
    const wantedId = initialDatasetId ?? restoredView.datasetId;
    if (!wantedId) return;
    const found = datasets.find((d) => d.dataset_id === wantedId);
    if (found) setDatasetId(found.dataset_id);
    else setRestoredDatasetMissing(true);
  }, [datasets, datasetsLoaded, initialDatasetId, presetApplied, restoredView.datasetId]);

  useEffect(() => {
    if (!datasetId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    getDataset(projectId, datasetId)
      .then((d) => {
        setDetail(d);
        // Charts are about to render for a chosen dataset -- mark T-14
        // visited/Done in the rail (toolVisitedStore.ts), the same
        // "something changed, refresh" signal onSaved carries everywhere else.
        markToolVisited(projectId, "T-14");
        onVisited?.();
        // Whatever brought us to this dataset -- a manual pick, the T-08
        // deep link, or the view restored above -- it is now "the chart
        // this project has open," so it's what a later visit should restore.
        saveChartSetView(projectId, { datasetId });
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this dataset."))
      .finally(() => setLoading(false));
    // onVisited deliberately excluded: ProjectWorkspace's onSaved isn't
    // memoized, and this effect must only re-run when the chosen dataset
    // changes, not on every parent re-render (that would refetch in a loop).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, datasetId]);

  // A dataset switch invalidates any filter drawn from the previous one --
  // carrying a stale column+values pair over silently would either break
  // (the column doesn't exist here) or, worse, coincidentally match
  // something unrelated. Every newly chosen dataset starts unfiltered.
  useEffect(() => {
    setFilterColumn("");
    setFilterValues([]);
  }, [datasetId]);

  const filteredRows = useMemo(
    () => (detail ? applyRowFilter(detail.rows, filterColumn, filterValues) : []),
    [detail, filterColumn, filterValues],
  );
  // Only `rows` is narrowed -- `meta` (the column list every picker reads)
  // still describes the whole dataset, so a column whose values were all
  // filtered out doesn't also vanish from the dropdowns.
  const filteredDetail = useMemo(() => (detail ? { ...detail, rows: filteredRows } : null), [detail, filteredRows]);

  return (
    <Panel title="Pareto / Histogram / Run Chart + Scatter / Box">
      <Field label="Dataset" htmlFor="chartset-dataset">
        <SelectInput
          id="chartset-dataset" data-testid="chartset-dataset-select" value={datasetId}
          onChange={(e) => { setPresetApplied(true); setRestoredDatasetMissing(false); setDatasetId(e.target.value); }}
        >
          <option value="">Select a dataset…</option>
          {datasets.map((d) => (
            <option key={d.dataset_id} value={d.dataset_id}>{d.source_filename} ({d.row_count} rows)</option>
          ))}
        </SelectInput>
      </Field>
      {restoredDatasetMissing && (
        <p className="sigma-chartset__notice" data-testid="chartset-dataset-gone">
          The dataset remembered from last time is no longer in this project — pick another above.
        </p>
      )}

      {loading && <p>Loading dataset…</p>}
      {error && <VerdictBanner tone="fail" headline={error} />}

      {detail && filteredDetail && (
        <>
          <FilterPanel
            columns={detail.meta.columns}
            rows={detail.rows}
            column={filterColumn}
            values={filterValues}
            onColumnChange={setFilterColumn}
            onValuesChange={setFilterValues}
            filteredCount={filteredRows.length}
          />
          <div className="sigma-chartset__grid">
            <HistogramPanel detail={filteredDetail} projectId={projectId} restored={restoredView} />
            <RunChartPanel detail={filteredDetail} projectId={projectId} restored={restoredView} />
            <ParetoPanel detail={filteredDetail} projectId={projectId} restored={restoredView} />
            <ScatterPanel detail={filteredDetail} projectId={projectId} restored={restoredView} />
            <BoxPanel detail={filteredDetail} projectId={projectId} restored={restoredView} />
          </div>
        </>
      )}
    </Panel>
  );
}
