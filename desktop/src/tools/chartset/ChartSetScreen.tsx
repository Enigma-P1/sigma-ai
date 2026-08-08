import { useEffect, useState } from "react";
import { Field, Panel, SelectInput, VerdictBanner } from "../../design/components";
import { getDataset, listDatasets } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { DatasetDetail, DatasetMeta } from "../../api/types";
import { HistogramPanel } from "./HistogramPanel";
import { RunChartPanel } from "./RunChartPanel";
import { ParetoPanel } from "./ParetoPanel";
import { ScatterPanel } from "./ScatterPanel";
import { BoxPanel } from "./BoxPanel";
import "./ChartSetScreen.css";

export interface ChartSetScreenProps {
  projectId: string;
  /** T-08's "send to Pareto" deep link (ToolRouter's DatasetPreset) --
   * preselects the dataset once it loads. */
  initialDatasetId?: string;
}

/** T-14: pick a dataset, then the five-chart set, each with its own
 * column picker and its own engine-computed verdict headline (M2 brief).
 * Rows are fetched once here and passed down — chart panels only choose
 * which stored columns to look at, they don't compute statistics. */
export function ChartSetScreen({ projectId, initialDatasetId }: ChartSetScreenProps) {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presetApplied, setPresetApplied] = useState(false);

  useEffect(() => {
    listDatasets(projectId)
      .then(setDatasets)
      .catch(() => {
        /* an empty picker is still an honest state -- T-11 hasn't been used yet */
      });
  }, [projectId]);

  useEffect(() => {
    if (presetApplied || !initialDatasetId) return;
    const preset = datasets.find((d) => d.dataset_id === initialDatasetId);
    if (!preset) return; // not loaded yet -- try again once `datasets` updates
    setPresetApplied(true);
    setDatasetId(preset.dataset_id);
  }, [datasets, initialDatasetId, presetApplied]);

  useEffect(() => {
    if (!datasetId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    getDataset(projectId, datasetId)
      .then(setDetail)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this dataset."))
      .finally(() => setLoading(false));
  }, [projectId, datasetId]);

  return (
    <Panel title="Pareto / Histogram / Run Chart + Scatter / Box">
      <Field label="Dataset" htmlFor="chartset-dataset">
        <SelectInput
          id="chartset-dataset" data-testid="chartset-dataset-select" value={datasetId}
          onChange={(e) => { setPresetApplied(true); setDatasetId(e.target.value); }}
        >
          <option value="">Select a dataset…</option>
          {datasets.map((d) => (
            <option key={d.dataset_id} value={d.dataset_id}>{d.source_filename} ({d.row_count} rows)</option>
          ))}
        </SelectInput>
      </Field>

      {loading && <p>Loading dataset…</p>}
      {error && <VerdictBanner tone="fail" headline={error} />}

      {detail && (
        <div className="sigma-chartset__grid">
          <HistogramPanel detail={detail} />
          <RunChartPanel detail={detail} />
          <ParetoPanel detail={detail} />
          <ScatterPanel detail={detail} />
          <BoxPanel detail={detail} />
        </div>
      )}
    </Panel>
  );
}
