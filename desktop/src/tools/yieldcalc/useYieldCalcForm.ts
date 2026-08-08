import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { PrescoreResult, ProjectMetadata, YieldCalcArtifact } from "../../api/types";
import {
  type DpmoBlockValue,
  type YieldStepValue,
  dpmoBlockFromArtifact,
  dpmoBlockToBody,
  emptyDpmoBlock,
  emptyYieldStep,
  yieldCalcCanSave,
  yieldStepsFromArtifact,
  yieldStepsToBody,
} from "./yieldCalcLogic";

const ARTIFACT_ID = "yieldcalc";
const SCHEMA_VERSION = 1;

/** All of YieldCalcForm's state, load-on-open, and save/prescore wiring --
 * same load/save/reload/prescore shape as useCopqForm.ts, extended for
 * T-10's two independent blocks (steps table + optional DPMO block). */
export function useYieldCalcForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [steps, setSteps] = useState<YieldStepValue[]>([emptyYieldStep()]);
  const [stepsInSeries, setStepsInSeries] = useState<boolean | null>(null);
  const [includeDpmo, setIncludeDpmo] = useState(false);
  const [dpmoBlock, setDpmoBlock] = useState<DpmoBlockValue>(emptyDpmoBlock());
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<YieldCalcArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as YieldCalcArtifact;
        setSteps(yieldStepsFromArtifact(d));
        setStepsInSeries(d.steps_in_series);
        const block = dpmoBlockFromArtifact(d);
        setIncludeDpmo(block != null);
        if (block) setDpmoBlock(block);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server results no longer describe it
  }

  function updateSteps(next: YieldStepValue[]) {
    setSteps(next);
    dirty();
  }

  function setSeries(value: boolean) {
    setStepsInSeries(value);
    dirty();
  }

  function toggleIncludeDpmo(value: boolean) {
    setIncludeDpmo(value);
    dirty();
  }

  function updateDpmoBlock(patch: Partial<DpmoBlockValue>) {
    setDpmoBlock((prev) => ({ ...prev, ...patch }));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body: Record<string, unknown> = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-10",
      created_at: now,
      updated_at: now,
      steps: yieldStepsToBody(steps),
      steps_in_series: stepsInSeries,
      dpmo_block: includeDpmo ? dpmoBlockToBody(dpmoBlock) : null,
    };

    try {
      const res = await saveArtifact(projectId, "T-10", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        // What the form renders as each step's defective units/FPY and the
        // artifact-level RTY/DPMO/sigma always comes from this fresh GET,
        // not from `body` above (CopqForm's same reload-after-save contract).
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as YieldCalcArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves results blank */
      }
      try {
        setPrescore(await runPrescore("T-10", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      if (err instanceof ApiError && err.validation) {
        const grouped = groupValidationByField(err.validation);
        const flat: Record<string, string> = {};
        for (const [path, items] of Object.entries(grouped)) flat[path] = items[0]?.msg ?? "Invalid value.";
        setFieldErrors(flat);
        setGeneralError("Some fields need fixing before this can save.");
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  return {
    steps,
    updateSteps,
    stepsInSeries,
    setSeries,
    includeDpmo,
    toggleIncludeDpmo,
    dpmoBlock,
    updateDpmoBlock,
    version,
    saving,
    canSave: yieldCalcCanSave(steps, stepsInSeries, includeDpmo, dpmoBlock) && !saving,
    generalError,
    fieldErrors,
    prescore,
    serverArtifact,
    handleSave,
  };
}
