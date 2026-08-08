import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { ControlPlanArtifact, PrescoreResult, ProjectMetadata } from "../../api/types";
import { makeControlPlanEditors } from "./controlPlanEditors";
import { buildControlPlanBody, canSave, controlPlanStateFromArtifact, emptyControlPlanState, missingFields, type ControlPlanState } from "./controlPlanLogic";
import { useFrozenLimits } from "./useFrozenLimits";

const ARTIFACT_ID = "control-plan";
const SCHEMA_VERSION = 1;

export function useControlPlanForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<ControlPlanState>(emptyControlPlanState());
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<ControlPlanArtifact | null>(null);
  const frozenLimits = useFrozenLimits(projectId, project);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as ControlPlanArtifact;
        setState(controlPlanStateFromArtifact(d));
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a blank plan is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function update(patch: Partial<ControlPlanState>) {
    setState((prev) => ({ ...prev, ...patch }));
    setServerArtifact(null); // state changed since the last save -- the old server plan_health no longer describes it
  }

  const editors = makeControlPlanEditors(state, update);

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildControlPlanBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, state, frozenLimits });

    try {
      const res = await saveArtifact(projectId, "T-22", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as ControlPlanArtifact;
        setServerArtifact(reloaded);
        setState(controlPlanStateFromArtifact(reloaded));
      } catch {
        /* the save itself succeeded; a failed re-load just skips the badge/health refresh */
      }
      try {
        setPrescore(await runPrescore("T-22", body));
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
    state, update, ...editors,
    version, saving, canSave: canSave(state) && !saving, missing: missingFields(state),
    generalError, prescore, serverArtifact, frozenLimits, handleSave,
  };
}
