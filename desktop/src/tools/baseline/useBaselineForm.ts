import { useEffect, useState } from "react";
import { getDataset, listDatasets, runBaseline } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { BaselineResponse, DatasetMeta } from "../../api/types";
import { parseSpecLimit } from "./baselineLogic";

/** T-13's state + engine wiring. The enforced order (spec limits +
 * operational definition before anything runs) is a UI-layout concern
 * (BaselineForm.tsx renders the sections in that order and gates Run on
 * it) — this hook just holds the values and makes the one call. */
export function useBaselineForm(projectId: string) {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [datasetId, setDatasetId] = useState<string>("");
  const [column, setColumn] = useState<string>("");
  const [uslText, setUslText] = useState("");
  const [lslText, setLslText] = useState("");
  const [operationalDefinitionOk, setOperationalDefinitionOk] = useState(false);
  const [enableRule2, setEnableRule2] = useState(false);
  const [enableRule3, setEnableRule3] = useState(false);
  const [applySigmaShift, setApplySigmaShift] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BaselineResponse | null>(null);
  const [chartValues, setChartValues] = useState<number[]>([]);

  useEffect(() => {
    listDatasets(projectId)
      .then(setDatasets)
      .catch(() => {
        /* an empty picker is still an honest state -- T-11 hasn't been used yet */
      });
  }, [projectId]);

  const selectedDataset = datasets.find((d) => d.dataset_id === datasetId) ?? null;
  const numericColumns = selectedDataset?.columns.filter((c) => c.type === "numeric") ?? [];
  const usl = parseSpecLimit(uslText);
  const lsl = parseSpecLimit(lslText);

  const specsReady = usl != null || lsl != null;
  const dataReady = datasetId !== "" && column !== "";
  const canRun = dataReady && specsReady && operationalDefinitionOk && !running;

  async function handleRun() {
    if (!canRun) return;
    setRunning(true);
    setError(null);
    try {
      const [baseline, detail] = await Promise.all([
        runBaseline({
          project_id: projectId, dataset_id: datasetId, column, usl, lsl,
          operational_definition_ok: operationalDefinitionOk,
          enable_rule2: enableRule2, enable_rule3: enableRule3, apply_sigma_shift: applySigmaShift,
        }),
        getDataset(projectId, datasetId),
      ]);
      setResult(baseline);
      setChartValues(detail.rows.map((r) => Number(r[column])));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not run the baseline.");
      setResult(null);
    } finally {
      setRunning(false);
    }
  }

  return {
    datasets, datasetId, setDatasetId, column, setColumn, numericColumns,
    uslText, setUslText, lslText, setLslText,
    operationalDefinitionOk, setOperationalDefinitionOk,
    enableRule2, setEnableRule2, enableRule3, setEnableRule3, applySigmaShift, setApplySigmaShift,
    running, error, result, chartValues,
    dataReady, specsReady, canRun, handleRun,
  };
}
