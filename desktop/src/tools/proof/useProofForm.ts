import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { resolveArraySource } from "../hypothesis/hypothesisRequestBuilder";
import { useDatasetDetailCache } from "../hypothesis/useDatasetDetailCache";
import { buildProofBody, findNextCauseClientSide } from "./proofLogic";
import { ARTIFACT_ID, emptyProofState, missingFields, proofStateFromArtifact } from "./proofState";
import type { ProofState } from "./proofState";
import { parseNumberList } from "../hypothesis/hypothesisParsing";
import type {
  CharterArtifact, FishboneArtifact, PilotPlanArtifact, PrescoreResult, ProjectMetadata, ProofArtifact, SolutionMatrixArtifact,
} from "../../api/types";

function findArtifactIdByTool(project: ProjectMetadata, toolId: string): string | undefined {
  return Object.keys(project.artifact_index).find((id) => project.artifact_index[id]?.tool_id === toolId);
}

/** T-20's state + engine wiring. On a brand-new proof, best-effort
 * prefills from whatever the project already has saved: T-19's declared
 * threshold + confounders + pilot_ref, T-03's charter baseline/goal, and
 * T-15+T-18's next-not-yet-piloted verified cause -- every one of these
 * is an ECHO (proof.py's own module docstring), never independently
 * re-verified by the engine, so a best-effort client-side prefill is
 * exactly the intended contract, not a shortcut around it. */
export function useProofForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const { datasets, datasetDetails, getDatasetDetailCached, loadDatasetDetail } = useDatasetDetailCache(projectId);
  const [state, setState] = useState<ProofState>(emptyProofState());
  const [serverArtifact, setServerArtifact] = useState<ProofArtifact | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;
  const pilotArtifactId = findArtifactIdByTool(project, "T-19");
  const charterArtifactId = findArtifactIdByTool(project, "T-03");
  const fishboneArtifactId = findArtifactIdByTool(project, "T-15");
  const solutionMatrixArtifactId = findArtifactIdByTool(project, "T-18");

  useEffect(() => {
    if (!existingVersion) return;
    loadArtifact(projectId, ARTIFACT_ID).then((d) => {
      const a = d as unknown as ProofArtifact;
      setState(proofStateFromArtifact(a));
      setServerArtifact(a);
      setVersion(existingVersion);
    }).catch(() => { /* best-effort prefill; a blank flow is still usable */ });
  }, [projectId, existingVersion]);

  useEffect(() => {
    if (existingVersion || !pilotArtifactId) return;
    loadArtifact(projectId, pilotArtifactId).then((d) => {
      const p = d as unknown as PilotPlanArtifact;
      setState((prev) => ({
        ...prev, pilotRef: pilotArtifactId, metricRef: prev.metricRef || p.success_threshold.metric_ref,
        thresholdValue: prev.thresholdValue || String(p.success_threshold.value),
        thresholdDirection: p.success_threshold.direction, confounders: p.confounder_checklist,
      }));
    }).catch(() => { /* no pilot yet -- the flow still works with manual entry */ });
  }, [projectId, pilotArtifactId, existingVersion]);

  useEffect(() => {
    if (existingVersion || !charterArtifactId) return;
    loadArtifact(projectId, charterArtifactId).then((d) => {
      const c = d as unknown as CharterArtifact;
      const goal = c.goal;
      if (goal.baseline_value == null) return;
      const lowerIsBetter = goal.target_value < goal.baseline_value;
      setState((prev) => ({
        ...prev, charterRef: charterArtifactId, charterBaselineText: prev.charterBaselineText || String(goal.baseline_value),
        charterGoalText: prev.charterGoalText || String(goal.target_value),
        charterGoalDirection: lowerIsBetter ? "lower_is_better" : "higher_is_better",
        guardrailMetricRef: prev.guardrailMetricRef || goal.consequential_metrics[0] || "",
      }));
    }).catch(() => { /* no charter yet */ });
  }, [projectId, charterArtifactId, existingVersion]);

  useEffect(() => {
    if (existingVersion || !fishboneArtifactId || !solutionMatrixArtifactId || !pilotArtifactId) return;
    Promise.all([loadArtifact(projectId, fishboneArtifactId), loadArtifact(projectId, solutionMatrixArtifactId), loadArtifact(projectId, pilotArtifactId)])
      .then(([fb, sm, pilot]) => {
        const verified = (fb as unknown as FishboneArtifact).verified_causes?.value.causes ?? [];
        const ranked = (sm as unknown as SolutionMatrixArtifact).ranked_fix_list?.value.ranked ?? [];
        const pilotedIds = (pilot as unknown as PilotPlanArtifact).the_one_change.linked_cause_ids;
        const next = findNextCauseClientSide(ranked, verified, pilotedIds);
        setState((prev) => (prev.nextCauseRef ? prev : { ...prev, nextCauseRef: next }));
      }).catch(() => { /* no fishbone/solution-matrix chain yet */ });
  }, [projectId, fishboneArtifactId, solutionMatrixArtifactId, pilotArtifactId, existingVersion]);

  function update(patch: Partial<ProofState>) {
    setState((prev) => ({ ...prev, ...patch }));
  }

  const previewBeforeCount = state.before.mode === "paste" ? parseNumberList(state.before.pasteText).length : state.before.column ? 2 : 0;
  const previewAfterCount = state.after.mode === "paste" ? parseNumberList(state.after.pasteText).length : state.after.column ? 2 : 0;
  const missing = missingFields(state, previewBeforeCount, previewAfterCount);
  const canSave = missing.length === 0 && !saving;

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    try {
      const [before, after] = await Promise.all([
        resolveArraySource(state.before, getDatasetDetailCached, { preferRef: false }),
        resolveArraySource(state.after, getDatasetDetailCached, { preferRef: false }),
      ]);
      const body = buildProofBody(state, before.values, after.values, new Date().toISOString(), serverArtifact);
      const res = await saveArtifact(projectId, "T-20", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as ProofArtifact);
      } catch { /* the save itself succeeded; a failed re-load just skips the badge refresh */ }
      try {
        setPrescore(await runPrescore("T-20", body));
      } catch { /* prescore is a nice-to-have on top of a successful save */ }
    } catch (err) {
      setSaveState("error");
      setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return {
    state, update, datasets, datasetDetails, loadDatasetDetail,
    version, saving, canSave, missing, generalError, prescore, serverArtifact, handleSave,
  };
}
