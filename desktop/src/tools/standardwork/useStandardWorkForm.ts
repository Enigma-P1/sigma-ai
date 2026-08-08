import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { PrescoreResult, ProcessMapArtifact, ProcessMapStep, ProjectMetadata, StandardWorkArtifact } from "../../api/types";
import { buildBody, canSave, emptyState, emptyStep, missingFields, stateFromArtifact, type StandardWorkState } from "./standardWorkLogic";

const ARTIFACT_ID = "sop";
const PROCESS_MAP_ARTIFACT_ID = "process-map"; // T-06's fixed single-instance id (processMapLogic.ts)
const SCHEMA_VERSION = 1;

/** T-24's state + engine wiring. Best-effort loads the project's saved
 * T-06 Process Map so "seed steps from the process map" has real steps to
 * offer (FmeaForm's own T-06 step-picker precedent). */
export function useStandardWorkForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<StandardWorkState>(emptyState());
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<StandardWorkArtifact | null>(null);
  const [processMapSteps, setProcessMapSteps] = useState<ProcessMapStep[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as StandardWorkArtifact;
        setState(stateFromArtifact(d));
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a blank SOP is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  useEffect(() => {
    if (!project.artifact_index[PROCESS_MAP_ARTIFACT_ID]) return;
    let cancelled = false;
    loadArtifact(projectId, PROCESS_MAP_ARTIFACT_ID)
      .then((data) => {
        if (!cancelled) setProcessMapSteps((data as unknown as ProcessMapArtifact).steps ?? []);
      })
      .catch(() => {
        /* no process map yet -- steps stay hand-entered */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, project.artifact_index]);

  function dirty() {
    setServerArtifact(null);
  }

  function update(patch: Partial<StandardWorkState>) {
    setState((prev) => ({ ...prev, ...patch }));
    dirty();
  }

  function addStep() {
    update({ steps: [...state.steps, emptyStep(state.steps.length + 1)] });
  }
  function updateStep(stepId: string, patch: Partial<StandardWorkState["steps"][number]>) {
    update({ steps: state.steps.map((s) => (s.step_id === stepId ? { ...s, ...patch } : s)) });
  }
  function removeStep(stepId: string) {
    update({ steps: state.steps.filter((s) => s.step_id !== stepId) });
  }

  /** Seed steps from the process map's current step list (PLAN §4.1: "from
   * the T-06 map's proposed state or hand-entered") -- names copied in as
   * a starting point, order preserved, each marked changed_from_prior so
   * the user can uncheck the ones that stayed the same. */
  function seedFromProcessMap() {
    if (processMapSteps.length === 0) return;
    const sorted = [...processMapSteps].sort((a, b) => a.order - b.order);
    update({
      steps: sorted.map((s, i) => ({ step_id: emptyStep(0).step_id, order: i + 1, action: s.name, standard: "", changed_from_prior: true, source_step_ref: s.step_id, note: "" })),
      seededFromProcessMapId: PROCESS_MAP_ARTIFACT_ID,
    });
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, state });

    try {
      const res = await saveArtifact(projectId, "T-24", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as StandardWorkArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just skips the badge refresh */
      }
      try {
        setPrescore(await runPrescore("T-24", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return {
    state, update, addStep, updateStep, removeStep, processMapSteps, seedFromProcessMap,
    version, saving, canSave: canSave(state) && !saving, missing: missingFields(state),
    generalError, prescore, serverArtifact, handleSave,
  };
}
