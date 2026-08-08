import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { PilotChange, PilotPlanArtifact, PrescoreResult, ProjectMetadata, SolutionMatrixArtifact } from "../../api/types";
import {
  buildPilotPlanBody,
  canSavePilotPlan,
  emptyPilotPlanState,
  pilotPlanStateFromArtifact,
  type PilotPlanState,
} from "./pilotPlanLogic";

const ARTIFACT_ID = "pilot-plan";
const SCHEMA_VERSION = 1;

/** T-19's state + engine wiring -- same load/save/reload/prescore shape as
 * useSolutionMatrixForm.ts. Also best-effort loads the project's saved
 * T-18 Solution Matrix (if any) so a brand-new pilot plan starts with the
 * top-ranked fix list entry pre-selected (task brief: "top-ranked
 * pre-selected"), the same T-15-summary-fetch technique applied one tool
 * downstream. */
export function usePilotPlanForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<PilotPlanState>(emptyPilotPlanState());
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<PilotPlanArtifact | null>(null);
  const [exitError, setExitError] = useState<string | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;
  const solutionMatrixArtifactId = Object.keys(project.artifact_index).find((id) => project.artifact_index[id]?.tool_id === "T-18");

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as PilotPlanArtifact;
        setState(pilotPlanStateFromArtifact(d));
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

  useEffect(() => {
    // Only pre-select on a genuinely new pilot plan -- never overwrite a
    // loaded one's own linked solution.
    if (existingVersion || !solutionMatrixArtifactId) return;
    let cancelled = false;
    loadArtifact(projectId, solutionMatrixArtifactId)
      .then((data) => {
        if (cancelled) return;
        const top = (data as unknown as SolutionMatrixArtifact).ranked_fix_list?.value.ranked[0];
        if (!top) return;
        setState((prev) => (prev.linkedSolutionId ? prev : {
          ...prev,
          linkedSolutionId: top.solution_id,
          linkedCauseIds: top.linked_cause_ids,
          primaryChangeText: prev.primaryChangeText || top.name,
        }));
      })
      .catch(() => {
        /* no ranked fix list yet -- the flow still works with a manually-typed change */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, solutionMatrixArtifactId, existingVersion]);

  function dirty() {
    setServerArtifact(null);
    setExitError(null);
  }

  function update(patch: Partial<PilotPlanState>) {
    setState((prev) => ({ ...prev, ...patch }));
    dirty();
  }

  function addExtraChange() {
    setState((prev) => ({ ...prev, extraChanges: [...prev.extraChanges, { change_id: `extra-${prev.extraChanges.length + 1}`, text: "" }] }));
    dirty();
  }
  function updateExtraChange(index: number, next: PilotChange) {
    setState((prev) => ({ ...prev, extraChanges: prev.extraChanges.map((c, i) => (i === index ? next : c)) }));
    dirty();
  }
  function removeExtraChange(index: number) {
    setState((prev) => ({ ...prev, extraChanges: prev.extraChanges.filter((_, i) => i !== index) }));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    setExitError(null);
    const body = buildPilotPlanBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, state });

    try {
      const res = await saveArtifact(projectId, "T-19", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as PilotPlanArtifact;
        setServerArtifact(reloaded);
      } catch {
        /* the save itself succeeded; a failed re-load just skips the badge refresh */
      }
      try {
        setPrescore(await runPrescore("T-19", body));
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
        const exitMsg = err.validation.map((v) => v.msg).find((m) => m.includes("EXIT-10"));
        if (exitMsg) {
          setExitError(exitMsg);
        } else {
          setGeneralError("Some fields need fixing before this can save.");
        }
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  return {
    state, update, addExtraChange, updateExtraChange, removeExtraChange,
    version, saving, canSave: canSavePilotPlan(state) && !saving,
    generalError, fieldErrors, exitError, prescore, serverArtifact, handleSave,
  };
}
