import { useEffect, useState } from "react";
import { getDataset, listDatasets, runBaseline } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { ArtifactIndexEntry, BaselineResponse, DatasetMeta, ProjectMetadata } from "../../api/types";
import { parseSpecLimit } from "./baselineLogic";

// Same artifact_id constant useCollectionPlanForm.ts saves T-11's plan
// under -- read-only here, display only (M2 brief: "a link chip ... when
// one exists"), never fetched/loaded, just presence + version off the
// project's own artifact index.
const COLLECTION_PLAN_ARTIFACT_ID = "collection-plan";

/** T-13's state + engine wiring. The enforced order (spec limits +
 * operational definition before anything runs) is a UI-layout concern
 * (BaselineForm.tsx renders the sections in that order and gates Run on
 * it) — this hook just holds the values and makes the one call.
 * `initialDatasetId` is the T-08/T-09 deep-link preset (ToolRouter's
 * DatasetPreset): applied once, the first time it appears in the fetched
 * dataset list, so a manual re-selection afterward isn't fought. */
export function useBaselineForm(projectId: string, project: ProjectMetadata, initialDatasetId?: string) {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [datasetId, setDatasetIdRaw] = useState<string>("");
  const [presetApplied, setPresetApplied] = useState(false);
  function setDatasetId(id: string) {
    setPresetApplied(true); // a manual pick always counts as "handled," even if it matches the preset
    setDatasetIdRaw(id);
  }
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

  useEffect(() => {
    if (presetApplied || !initialDatasetId) return;
    const preset = datasets.find((d) => d.dataset_id === initialDatasetId);
    if (!preset) return; // not loaded yet -- try again once `datasets` updates
    setPresetApplied(true);
    setDatasetIdRaw(preset.dataset_id);
    const numericCols = preset.columns.filter((c) => c.type === "numeric");
    // T-09's per-element export (routes/time_study.py) carries both
    // cycle_number and seconds as numeric columns -- prefer the one
    // actually named "seconds" (that tool's documented export contract)
    // over whichever numeric column happens to come first in the CSV.
    const preferred = numericCols.find((c) => c.name === "seconds") ?? numericCols[0];
    if (preferred) setColumn(preferred.name);
  }, [datasets, initialDatasetId, presetApplied]);

  const selectedDataset = datasets.find((d) => d.dataset_id === datasetId) ?? null;
  const numericColumns = selectedDataset?.columns.filter((c) => c.type === "numeric") ?? [];
  const usl = parseSpecLimit(uslText);
  const lsl = parseSpecLimit(lslText);

  // Display-only link chip (M2 brief): does the project already have a
  // T-11 Data Collection Plan? Read straight off the project's own
  // artifact index -- no fetch, no navigation wired up here.
  const collectionPlanEntry: ArtifactIndexEntry | undefined = project.artifact_index[COLLECTION_PLAN_ARTIFACT_ID];

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
    collectionPlanEntry,
  };
}
