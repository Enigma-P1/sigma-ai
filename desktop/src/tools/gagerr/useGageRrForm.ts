import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { canSave as gridCanSave, emptyGrid, gridFromArtifact, gridToReadings, missingFields, resizeGrid } from "./gageRrLogic";
import type { GridValue } from "./gageRrLogic";
import type { GageRRArtifact, PrescoreResult, ProjectMetadata } from "../../api/types";

const ARTIFACT_ID = "gage-rr";
const SCHEMA_VERSION = 1;

export type PoolChoice = "auto" | "always" | "never";

const POOL_VALUE: Record<PoolChoice, boolean | null> = { auto: null, always: true, never: false };

function poolChoiceFrom(value: boolean | null | undefined): PoolChoice {
  if (value === true) return "always";
  if (value === false) return "never";
  return "auto";
}

/** T-35's state + engine wiring. Same shape as useMsaForm.ts (load on
 * open, save re-validates and recomputes server-side, reload for the fresh
 * result, then prescore) with one difference that matters:
 *
 * A HALF-ENTERED STUDY IS ALLOWED TO SAVE. A crossed Gage R&R takes two
 * shifts to collect, and a tool that refuses to keep the first shift's
 * readings until the second is done is a tool people run on paper instead.
 * The engine carries the reason it cannot compute yet (design_error) and
 * the screen shows it; nothing here blocks the save on completeness.
 */
export function useGageRrForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [grid, setGrid] = useState<GridValue>(emptyGrid);
  const [gaugeName, setGaugeName] = useState("");
  const [toleranceText, setToleranceText] = useState("");
  const [poolChoice, setPoolChoice] = useState<PoolChoice>("auto");
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<GageRRArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as GageRRArtifact;
        setGaugeName(d.gauge_name ?? "");
        setToleranceText(d.tolerance != null ? String(d.tolerance) : "");
        setPoolChoice(poolChoiceFrom(d.pool_interaction));
        const loaded = gridFromArtifact(d);
        if (loaded) setGrid(loaded);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty grid is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  /** Any edit invalidates the displayed result: it was computed from the
   * readings as they were, and showing it beside changed readings is the
   * exact stale-number problem the chart fingerprint exists to stop. */
  function updateGrid(next: GridValue) {
    setGrid(next);
    setServerArtifact(null);
  }

  function resize(next: { parts?: number; operators?: number; trials?: number }) {
    updateGrid(resizeGrid(grid, next));
  }

  function updateTolerance(text: string) {
    setToleranceText(text);
    setServerArtifact(null);
  }

  function updatePoolChoice(choice: PoolChoice) {
    setPoolChoice(choice);
    setServerArtifact(null);
  }

  const canSave = !saving && gridCanSave(grid);

  async function handleSave() {
    if (!canSave) return;
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body: Record<string, unknown> = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-35",
      created_at: now,
      updated_at: now,
      gauge_name: gaugeName.trim() || null,
      tolerance: toleranceText.trim() === "" ? null : Number(toleranceText),
      pool_interaction: POOL_VALUE[poolChoice],
      readings: gridToReadings(grid),
    };

    try {
      const res = await saveArtifact(projectId, "T-35", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as GageRRArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the result blank */
      }
      try {
        setPrescore(await runPrescore("T-35", body));
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
    grid, updateGrid, resize,
    gaugeName, setGaugeName, toleranceText, updateTolerance, poolChoice, updatePoolChoice,
    version, saving, canSave, missing: missingFields(grid),
    generalError, fieldErrors, prescore, serverArtifact, handleSave,
  };
}
