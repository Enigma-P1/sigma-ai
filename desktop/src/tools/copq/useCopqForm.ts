import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { CopqArtifact, PrescoreResult, ProjectMetadata } from "../../api/types";
import type { CopqRowValue } from "./CopqRowFields";
import { copqCanSave, copqRowsFromArtifact, copqRowsToBody, draftCopqTotal, emptyCopqRow } from "./copqLogic";

const ARTIFACT_ID = "copq";
const SCHEMA_VERSION = 1;

/** All of CopqForm's state, load-on-open, and save/prescore wiring --
 * pulled into a hook (rather than living in CopqForm.tsx directly, as
 * picker/charter's forms do) purely to keep any one file's length down;
 * COPQ's save flow carries one more step than picker/charter's (the
 * reload-after-save that makes the total genuinely engine-sourced -- see
 * copqLogic.ts's draftCopqTotal). */
export function useCopqForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [rows, setRows] = useState<CopqRowValue[]>([emptyCopqRow()]);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<CopqArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as CopqArtifact;
        setRows(copqRowsFromArtifact(d));
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

  function updateRows(next: CopqRowValue[]) {
    setRows(next);
    setServerArtifact(null); // rows changed since the last save -- the old server total no longer describes them
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
      tool_id: "T-02",
      created_at: now,
      updated_at: now,
      rows: copqRowsToBody(rows),
      total: draftCopqTotal(rows),
    };

    try {
      const res = await saveArtifact(projectId, "T-02", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        // What CopqForm renders as each row's amount and the grand total
        // always comes from this fresh GET, not from `body` above.
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as CopqArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the total display blank */
      }
      try {
        setPrescore(await runPrescore("T-02", body));
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
    rows,
    updateRows,
    version,
    saving,
    canSave: copqCanSave(rows) && !saving,
    generalError,
    fieldErrors,
    prescore,
    serverArtifact,
    handleSave,
  };
}
