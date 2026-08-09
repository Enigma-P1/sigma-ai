import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { resolveArraySource } from "../hypothesis/hypothesisRequestBuilder";
import { useDatasetDetailCache } from "../hypothesis/useDatasetDetailCache";
import {
  ARTIFACT_ID, controlChartStateFromArtifact, emptyControlChartState, missingFields, parseSubgroupsText,
} from "./controlChartState";
import type { ControlChartState } from "./controlChartState";
import { parseNumberList } from "../hypothesis/hypothesisParsing";
import { buildControlChartBody } from "./controlChartLogic";
import type { ControlChartArtifact, PrescoreResult, ProjectMetadata, PSubgroup } from "../../api/types";

/** T-21's state + engine wiring. Data (IMR values / p-chart subgroups)
 * lives entirely on the artifact itself (module docstring of
 * control_chart.py) -- this hook resolves the current data-entry source
 * to raw values only at save time, same async-resolve-then-save shape as
 * T-17's useHypothesisForm/hypothesisRequestBuilder. */
export function useControlChartForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const { datasets, datasetDetails, getDatasetDetailCached, loadDatasetDetail } = useDatasetDetailCache(projectId);
  const [state, setState] = useState<ControlChartState>(emptyControlChartState());
  const [serverArtifact, setServerArtifact] = useState<ControlChartArtifact | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [exitError, setExitError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as ControlChartArtifact;
        setState(controlChartStateFromArtifact(d));
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a blank flow is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function update(patch: Partial<ControlChartState>) {
    setState((prev) => ({ ...prev, ...patch }));
    setExitError(null);
  }

  function updateAcknowledgment(key: string, patch: Partial<{ acknowledged: boolean; response_note: string }>) {
    setState((prev) => ({ ...prev, acknowledgments: { ...prev.acknowledgments, [key]: { ...prev.acknowledgments[key], acknowledged: false, response_note: "", ...patch } } }));
  }

  const previewImrCount = state.imrSource.mode === "paste" ? parseNumberList(state.imrSource.pasteText).length : state.imrSource.column ? 2 : 0;
  const previewSubgroups = state.dataShape === "attribute" ? parseSubgroupsText(state.pSubgroupsPasteText) : [];
  const missing = missingFields(state, previewImrCount, previewSubgroups);
  const canSave = missing.length === 0 && !saving;

  async function doSave(action: { freeze?: boolean; recalculateReason?: string }) {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setExitError(null);
    try {
      const resolvedImr = state.dataShape === "continuous" ? (await resolveArraySource(state.imrSource, getDatasetDetailCached, { preferRef: false })).values : null;
      const resolvedSub: PSubgroup[] | null = state.dataShape === "attribute" ? parseSubgroupsText(state.pSubgroupsPasteText) : null;
      const nowIso = new Date().toISOString();
      const body = buildControlChartBody(state, resolvedImr, resolvedSub, serverArtifact, nowIso, action);

      const res = await saveArtifact(projectId, "T-21", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      setState((prev) => ({ ...prev, freezeRequested: false, recalculateReason: "" }));
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as ControlChartArtifact;
        setServerArtifact(reloaded);
      } catch {
        /* the save itself succeeded; a failed re-load just skips the badge refresh */
      }
      try {
        // projectId turns on the project-aware measurement_check_on_file
        // check (a freeze with no T-12 on file gets a visible flag).
        setPrescore(await runPrescore("T-21", body, projectId));
      } catch {
        /* prescore is a nice-to-have on top of a successful save */
      }
    } catch (err) {
      setSaveState("error");
      if (err instanceof ApiError && err.validation) {
        const exitMsg = err.validation.map((v) => v.msg).find((m) => m.includes("EXIT-11"));
        const floorMsg = err.validation.map((v) => v.msg).find((m) => m.includes("EXIT-04"));
        if (exitMsg) setExitError(exitMsg);
        else setGeneralError(floorMsg ?? "Some fields need fixing before this can save.");
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  return {
    state, update, updateAcknowledgment,
    datasets, datasetDetails, loadDatasetDetail,
    version, saving, canSave, missing,
    generalError, exitError, prescore, serverArtifact,
    handleFreeze: () => doSave({ freeze: true }),
    handleRecalculate: (reason: string) => doSave({ recalculateReason: reason }),
    handleSaveMeta: () => doSave({}),
  };
}
