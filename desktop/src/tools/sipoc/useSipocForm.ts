import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { PrescoreResult, ProjectMetadata, SipocArtifact } from "../../api/types";
import { EMPTY_SIPOC_STATE, processStepsToBody, sipocCanSave, sipocStateFromArtifact } from "./sipocLogic";
import type { SipocState } from "./sipocLogic";

const ARTIFACT_ID = "sipoc";
const SCHEMA_VERSION = 1;

/** SipocForm's state, load-on-open, and save/prescore wiring -- pulled into
 * a hook purely to keep any one file's length down (same rationale as
 * COPQ's useCopqForm). */
export function useSipocForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<SipocState>(EMPTY_SIPOC_STATE);
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
        setState(sipocStateFromArtifact(data as unknown as SipocArtifact));
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function update(patch: Partial<SipocState>) {
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
      tool_id: "T-04",
      created_at: now,
      updated_at: now,
      supplier_input_pairs: state.supplier_input_pairs.map((p) => ({ supplier: p.supplier.trim(), input: p.input.trim() })),
      process_steps: processStepsToBody(state.process_steps),
      output_customer_pairs: state.output_customer_pairs.map((p) => ({ output: p.output.trim(), customer: p.customer.trim() })),
      scope_start: state.scope_start.trim(),
      scope_end: state.scope_end.trim(),
    };

    try {
      const res = await saveArtifact(projectId, "T-04", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-04", body));
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

  return { state, update, version, saving, canSave: sipocCanSave(state) && !saving, generalError, fieldErrors, prescore, handleSave };
}
