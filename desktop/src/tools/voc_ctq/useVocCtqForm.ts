import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { PrescoreResult, ProjectMetadata, VocCtqArtifact } from "../../api/types";
import { EMPTY_VOC_CTQ_STATE, vocCtqCanSave, vocCtqStateFromArtifact } from "./vocCtqLogic";
import type { VocCtqState } from "./vocCtqLogic";

const ARTIFACT_ID = "voc-ctq";
const SCHEMA_VERSION = 1;

/** VocCtqForm's state, load-on-open, and save/prescore wiring -- pulled
 * into a hook purely to keep any one file's length down (same rationale as
 * COPQ's useCopqForm and SIPOC's useSipocForm). */
export function useVocCtqForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<VocCtqState>(EMPTY_VOC_CTQ_STATE);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        setState(vocCtqStateFromArtifact(data as unknown as VocCtqArtifact));
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function update(patch: Partial<VocCtqState>) {
    setState((s) => ({ ...s, ...patch }));
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-05",
      created_at: now,
      updated_at: now,
      customers: state.customers.map((c) => ({ role: c.role.trim(), is_internal: c.is_internal })),
      statements: state.statements.map((s) => ({ ...s, customer_role: s.customer_role.trim(), text: s.text.trim() })),
      needs: state.needs.map((n) => ({ ...n, text: n.text.trim() })),
      ctqs: state.ctqs.map((c) => ({
        ...c,
        measure: c.measure.trim(),
        critical_vs_easy_check: c.critical_vs_easy_check.trim(),
        target: c.target?.trim() || null,
      })),
      primary_ctq_id: state.primary_ctq_id.trim(),
      charter_metric_link: state.charter_metric_link.trim(),
    };

    try {
      const res = await saveArtifact(projectId, "T-05", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-05", body));
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

  return { state, update, version, saving, canSave: vocCtqCanSave(state) && !saving, generalError, fieldErrors, prescore, handleSave };
}
