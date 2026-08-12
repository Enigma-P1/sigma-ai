import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { useToolDraft } from "../../app/useToolDraft";
import type { FmeaArtifact, FmeaRow, PrescoreResult, ProcessMapArtifact, ProcessMapStep, ProjectMetadata } from "../../api/types";
import { buildFmeaBody, canSaveFmea, emptyRow, fmeaStateFromArtifact } from "./fmeaLogic";

const ARTIFACT_ID = "fmea";
const SCHEMA_VERSION = 1;

// A stable, never-mutated reference (every update replaces the array via
// setRows, never pushes/splices in place) -- shared between `rows`'s own
// initializer and the "no saved version" draft baseline below, so the two
// start out `===` the way useToolDraft needs for its untouched-since-mount
// check (the same reasoning as CharterForm.tsx's module-level EMPTY_STATE).
const EMPTY_ROWS: FmeaRow[] = [];

/** T-16's state + engine wiring -- same load/save/reload/prescore shape as
 * useProcessMapForm.ts / useFishboneForm.ts. Also best-effort loads the
 * project's saved T-06 Process Map (if any) so FmeaWorksheet's step picker
 * can offer real steps by name instead of free text alone. */
export function useFmeaForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [rows, setRows] = useState<FmeaRow[]>(EMPTY_ROWS);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<FmeaArtifact | null>(null);
  const [processMapSteps, setProcessMapSteps] = useState<ProcessMapStep[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;
  const processMapArtifactId = Object.keys(project.artifact_index).find((id) => project.artifact_index[id]?.tool_id === "T-06");

  // What this form would show with no draft in play -- undefined until
  // that's settled, so useToolDraft never has to guess whether a stored
  // draft "differs" from a baseline that hasn't loaded yet.
  const [baseline, setBaseline] = useState<FmeaRow[] | undefined>(undefined);

  useEffect(() => {
    if (!existingVersion) {
      setBaseline(EMPTY_ROWS);
      return;
    }
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as FmeaArtifact;
        const loaded = fmeaStateFromArtifact(d).rows;
        setRows(loaded);
        setServerArtifact(d);
        setVersion(existingVersion);
        setBaseline(loaded);
      })
      .catch(() => {
        /* best-effort prefill; an empty worksheet is still usable. Also
           the draft-restore baseline -- see CharterForm.tsx's identical
           catch for why this branch sets it too. */
        if (!cancelled) setBaseline(EMPTY_ROWS);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  // Draft autosave (PLAN Phase 4.1) -- same wiring as CharterForm.tsx,
  // the tool this feature was built for; see useToolDraft.ts for the
  // restore/autosave contract.
  const draft = useToolDraft<FmeaRow[]>(projectId, "T-16", { baseline, state: rows, setState: setRows });

  useEffect(() => {
    if (!processMapArtifactId) return;
    let cancelled = false;
    loadArtifact(projectId, processMapArtifactId)
      .then((data) => {
        if (!cancelled) setProcessMapSteps((data as unknown as ProcessMapArtifact).steps ?? []);
      })
      .catch(() => {
        /* the step picker just falls back to free text */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, processMapArtifactId]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server anchors/blocking_flags/sorted_view no longer describe it
  }

  function addRow() {
    setRows((prev) => [...prev, emptyRow()]);
    dirty();
  }
  function updateRow(rowId: string, patch: Partial<FmeaRow>) {
    setRows((prev) => prev.map((r) => (r.row_id === rowId ? { ...r, ...patch } : r)));
    dirty();
  }
  function removeRow(rowId: string) {
    setRows((prev) => prev.filter((r) => r.row_id !== rowId));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const body = buildFmeaBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, rows });

    try {
      const res = await saveArtifact(projectId, "T-16", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as FmeaArtifact;
        setServerArtifact(reloaded);
        const reloadedRows = fmeaStateFromArtifact(reloaded).rows; // picks up engine-computed rpn per row
        setRows(reloadedRows);
        setBaseline(reloadedRows); // this is now the saved truth -- nothing left for a draft to protect
      } catch {
        // the save itself succeeded; a failed re-load just leaves rpn as
        // a draft value. Still move the draft baseline up to what was
        // actually saved (`rows`, pre-reload), or useToolDraft would see
        // `rows` and the old `baseline` disagree and autosave a new
        // draft for content that is already a real artifact.
        setBaseline(rows);
      }
      // This typing is now a real artifact -- the draft that was
      // protecting it has nothing left to protect.
      draft.clearDraft();
      try {
        setPrescore(await runPrescore("T-16", body));
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
    rows, addRow, updateRow, removeRow,
    version, saving, canSave: canSaveFmea(rows) && !saving,
    generalError, fieldErrors, prescore, serverArtifact, processMapSteps, handleSave,
    draftRestoredAt: draft.restoredAt, discardDraft: draft.discardDraft,
  };
}
