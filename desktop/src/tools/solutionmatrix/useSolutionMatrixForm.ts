import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type {
  FishboneArtifact,
  PrescoreResult,
  ProjectMetadata,
  Solution,
  SolutionCriterion,
  SolutionMatrixArtifact,
  VerifiedCauseEntry,
} from "../../api/types";
import {
  buildSolutionMatrixBody,
  canSaveSolutionMatrix,
  solutionMatrixStateFromArtifact,
  stripCriterionScores,
} from "./solutionMatrixLogic";

const ARTIFACT_ID = "solution-matrix";
const SCHEMA_VERSION = 1;

/** T-18's state + engine wiring -- same load/save/reload/prescore shape as
 * useFmeaForm.ts. Also best-effort loads the project's saved T-15 Fishbone
 * (if any) so the causes picker can offer real verified causes instead of
 * free text alone (FmeaForm's process-map-step-picker precedent, applied
 * here to fishbone's verified_causes summary). */
export function useSolutionMatrixForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [criteria, setCriteria] = useState<SolutionCriterion[]>([]);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<SolutionMatrixArtifact | null>(null);
  const [verifiedCauses, setVerifiedCauses] = useState<VerifiedCauseEntry[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;
  const fishboneArtifactId = Object.keys(project.artifact_index).find((id) => project.artifact_index[id]?.tool_id === "T-15");

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as SolutionMatrixArtifact;
        const s = solutionMatrixStateFromArtifact(d);
        setSolutions(s.solutions);
        setCriteria(s.criteria);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty matrix is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  useEffect(() => {
    if (!fishboneArtifactId) return;
    let cancelled = false;
    loadArtifact(projectId, fishboneArtifactId)
      .then((data) => {
        if (!cancelled) setVerifiedCauses((data as unknown as FishboneArtifact).verified_causes?.value.causes ?? []);
      })
      .catch(() => {
        /* the causes picker just falls back to manual linking */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, fishboneArtifactId]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server scores/ranked_fix_list no longer describe it
  }

  function addSolution(s: Solution) {
    setSolutions((prev) => [...prev, s]);
    dirty();
  }
  function updateSolution(solutionId: string, next: Solution) {
    setSolutions((prev) => prev.map((s) => (s.solution_id === solutionId ? next : s)));
    dirty();
  }
  function removeSolution(solutionId: string) {
    setSolutions((prev) => prev.filter((s) => s.solution_id !== solutionId));
    dirty();
  }
  function addCriterion(c: SolutionCriterion) {
    setCriteria((prev) => [...prev, c]);
    dirty();
  }
  function updateCriterion(criterionId: string, next: SolutionCriterion) {
    setCriteria((prev) => prev.map((c) => (c.criterion_id === criterionId ? next : c)));
    dirty();
  }
  function removeCriterion(criterionId: string) {
    setCriteria((prev) => prev.filter((c) => c.criterion_id !== criterionId));
    setSolutions((prev) => stripCriterionScores(prev, criterionId));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const body = buildSolutionMatrixBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, solutions, criteria });

    try {
      const res = await saveArtifact(projectId, "T-18", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as SolutionMatrixArtifact;
        setServerArtifact(reloaded);
        setSolutions(solutionMatrixStateFromArtifact(reloaded).solutions);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves scores as drafts */
      }
      try {
        setPrescore(await runPrescore("T-18", body));
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
    solutions, criteria, addSolution, updateSolution, removeSolution, addCriterion, updateCriterion, removeCriterion,
    version, saving, canSave: canSaveSolutionMatrix(solutions) && !saving,
    generalError, fieldErrors, prescore, serverArtifact, verifiedCauses, handleSave,
  };
}
