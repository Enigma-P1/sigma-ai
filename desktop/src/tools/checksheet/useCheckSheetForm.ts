import { useEffect, useMemo, useState } from "react";
import { checkSheetToDataset, loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { CheckSheetArtifact, CheckSheetCategory, CheckSheetEntry, DatasetMeta, PrescoreResult, ProjectMetadata, StrataFieldDef } from "../../api/types";
import {
  buildCheckSheetBody, canSaveCheckSheet, checkSheetStateFromArtifact, deriveStrataOptions,
  emptyCategory, emptyStrataField, makeTallyEntry, markEntryDeleted, removeCategoryCascade, removeStrataFieldCascade,
} from "./checkSheetLogic";

const ARTIFACT_ID = "checksheet";
const SCHEMA_VERSION = 1;

/** T-08's state + engine wiring -- same load/save/reload/prescore shape as
 * useProcessMapForm.ts, plus the check-sheet-specific tap/strata-toggle
 * state and the to_dataset "send to Pareto" action. */
export function useCheckSheetForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [categories, setCategories] = useState<CheckSheetCategory[]>([emptyCategory(0)]);
  const [strataFields, setStrataFields] = useState<StrataFieldDef[]>([]);
  const [entries, setEntries] = useState<CheckSheetEntry[]>([]);
  const [activeStrata, setActiveStrata] = useState<Record<string, string>>({});
  const [manualStrataOptions, setManualStrataOptions] = useState<Record<string, string[]>>({});
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<CheckSheetArtifact | null>(null);
  const [dataset, setDataset] = useState<DatasetMeta | null>(null);
  const [sendingToPareto, setSendingToPareto] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as CheckSheetArtifact;
        const s = checkSheetStateFromArtifact(d);
        setCategories(s.categories);
        setStrataFields(s.strataFields);
        setEntries(s.entries);
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

  function dirty() {
    setServerArtifact(null); // state changed since the last save
    setDataset(null); // the exported dataset described the old entries
  }

  function addCategory() {
    setCategories((p) => [...p, emptyCategory(p.length)]);
    dirty();
  }
  function updateCategory(id: string, patch: Partial<CheckSheetCategory>) {
    setCategories((p) => p.map((c) => (c.category_id === id ? { ...c, ...patch } : c)));
    dirty();
  }
  function removeCategory(id: string) {
    const next = removeCategoryCascade(categories, entries, id);
    setCategories(next.categories);
    setEntries(next.entries);
    dirty();
  }

  function addStrataField() {
    setStrataFields((p) => [...p, emptyStrataField(p.length)]);
    dirty();
  }
  function updateStrataField(key: string, patch: Partial<StrataFieldDef>) {
    setStrataFields((p) => p.map((f) => (f.key === key ? { ...f, ...patch } : f)));
    dirty();
  }
  function removeStrataField(key: string) {
    const next = removeStrataFieldCascade(strataFields, entries, key);
    setStrataFields(next.strataFields);
    setEntries(next.entries);
    setActiveStrata((p) => {
      const rest = { ...p };
      delete rest[key];
      return rest;
    });
    dirty();
  }

  const strataOptions = useMemo(
    () => deriveStrataOptions(strataFields, entries, manualStrataOptions),
    [strataFields, entries, manualStrataOptions],
  );

  function setActiveStratumValue(key: string, value: string) {
    setActiveStrata((p) => ({ ...p, [key]: value }));
  }
  function addStrataOption(key: string, value: string) {
    setManualStrataOptions((p) => ({ ...p, [key]: Array.from(new Set([...(p[key] ?? []), value])) }));
    setActiveStratumValue(key, value);
  }

  function tap(categoryId: string) {
    setEntries((p) => [...p, makeTallyEntry(categoryId, activeStrata)]);
    dirty();
  }
  function updateEntryNote(entryId: string, note: string) {
    setEntries((p) => p.map((e) => (e.entry_id === entryId ? { ...e, note } : e)));
    dirty();
  }
  function deleteEntry(entryId: string, reason: string) {
    setEntries((p) => markEntryDeleted(p, entryId, reason, new Date().toISOString()));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildCheckSheetBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, categories, strataFields, entries });
    try {
      const res = await saveArtifact(projectId, "T-08", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as CheckSheetArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the prescore/server view blank */
      }
      try {
        setPrescore(await runPrescore("T-08", body));
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

  async function handleSendToPareto() {
    if (version == null) return;
    setSendingToPareto(true);
    setSendError(null);
    try {
      setDataset(await checkSheetToDataset(projectId, ARTIFACT_ID, { created_at: new Date().toISOString() }));
    } catch (err) {
      setSendError(err instanceof ApiError ? err.message : "Could not export this check sheet to a dataset.");
    } finally {
      setSendingToPareto(false);
    }
  }

  return {
    categories, addCategory, updateCategory, removeCategory,
    strataFields, addStrataField, updateStrataField, removeStrataField,
    activeStrata, strataOptions, setActiveStratumValue, addStrataOption,
    entries, tap, updateEntryNote, deleteEntry, tallyByCategory: entries,
    version, saving, canSave: canSaveCheckSheet(categories) && !saving,
    generalError, prescore, serverArtifact, handleSave,
    dataset, sendingToPareto, sendError, handleSendToPareto,
  };
}
