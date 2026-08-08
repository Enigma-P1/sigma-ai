import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { emptyHypothesisFormState, formStateFromQuestion } from "./hypothesisFormState";
import type { HypothesisFormState } from "./hypothesisFormState";
import { buildResolvedQuestion } from "./hypothesisRequestBuilder";
import { missingFieldsForReflection } from "./hypothesisValidation";
import { useDatasetDetailCache } from "./useDatasetDetailCache";
import { useHypothesisPreviewRun } from "./useHypothesisPreviewRun";
import type { HypothesisRunArtifact, PrescoreResult, ProjectMetadata } from "../../api/types";

const ARTIFACT_ID = "hypothesis";
const SCHEMA_VERSION = 1;

/** T-17's top-level state: the form fields, load-on-open prefill, and
 * save+prescore -- composed with useHypothesisPreviewRun (the /route,
 * /run wiring) and useDatasetDetailCache (dataset loading). One saved slot
 * per project, versioned on re-run+save -- same pattern as T-12/T-13 (a
 * fresh analysis is a new version, not a second artifact). */
export function useHypothesisForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const { datasets, datasetDetails, loadDatasetDetail, getDatasetDetailCached } = useDatasetDetailCache(projectId);
  const [state, setState] = useState<HypothesisFormState>(emptyHypothesisFormState());
  const pr = useHypothesisPreviewRun(state, projectId, getDatasetDetailCached);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const a = data as unknown as HypothesisRunArtifact;
        setState((s) => ({ ...s, ...formStateFromQuestion(a.question), reflection: a.notes ?? "" }));
        if (a.routing) pr.setRouting(a.routing);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a blank form is still usable */
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- pr.setRouting is a stable setState identity
  }, [projectId, existingVersion]);

  function patch(p: Partial<HypothesisFormState>) {
    pr.reset(); // any question/data edit invalidates the last preview/run -- never show a stale tree for new inputs
    setState((s) => ({ ...s, ...p }));
  }

  /** The reflection field is filled in AFTER seeing the result -- unlike
   * every other field, editing it must never blank out the just-computed
   * routing/result the user is writing about. */
  function setReflection(reflection: string) {
    setState((s) => ({ ...s, reflection }));
  }

  const missingForReflection = missingFieldsForReflection(state.reflection);
  const canSave = pr.runResult != null && missingForReflection.length === 0 && !saving;

  async function handleSave() {
    if (!canSave) return;
    setSaving(true);
    setSaveState("saving");
    setSaveError(null);
    const now = new Date().toISOString();
    try {
      const question = await buildResolvedQuestion(state, getDatasetDetailCached);
      const body = {
        schema_version: SCHEMA_VERSION, artifact_id: ARTIFACT_ID, tool_id: "T-17",
        created_at: now, updated_at: now, notes: state.reflection.trim() || null,
        question, declared_primary: state.declaredPrimary,
      };
      const res = await saveArtifact(projectId, "T-17", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-17", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      setSaveError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return {
    datasets, datasetDetails, loadDatasetDetail,
    state, patch, setReflection,
    ...pr,
    saving, saveError, version, canSave, handleSave, prescore, missingForReflection,
  };
}
