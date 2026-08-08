import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { useA3PanelSeeding } from "./useA3PanelSeeding";
import type { A3Artifact, A3PanelKind, PrescoreResult, ProjectMetadata, TollgateAnswer } from "../../api/types";
import { buildA3Body, canSave, emptyState, missingFields, stateFromArtifact, type A3State } from "./a3Logic";

const ARTIFACT_ID = "a3";
const SCHEMA_VERSION = 1;

/** T-25's state + engine wiring. Seeding (loading a source artifact and
 * drafting narrative from it) is a desktop action (a3.py's own module
 * docstring: "the actual seeding ... is a desktop action, echoed-by-ref
 * here") -- see a3Seeding.ts / useA3PanelSeeding.ts. */
export function useA3Form(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<A3State>(emptyState());
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [closeBlockedError, setCloseBlockedError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<A3Artifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as A3Artifact;
        setState(stateFromArtifact(d));
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a blank A3 is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function update(patch: Partial<A3State>) {
    setState((prev) => ({ ...prev, ...patch }));
    setServerArtifact(null); // state changed since the last save -- the old server closure/prescore no longer describe it
  }

  function setPanelNarrative(panel: A3PanelKind, narrative: string) {
    update({ panels: state.panels.map((p) => (p.panel === panel ? { ...p, narrative } : p)) });
  }

  function setTollgateAnswer(phase: string, answer: TollgateAnswer) {
    const existing = state.tollgateAnswers[phase] ?? [];
    const next = existing.some((a) => a.question_id === answer.question_id)
      ? existing.map((a) => (a.question_id === answer.question_id ? answer : a))
      : [...existing, answer];
    update({ tollgateAnswers: { ...state.tollgateAnswers, [phase]: next } });
  }

  const { seeding, reseedPanel, loadFmeaForClose } = useA3PanelSeeding(projectId, project, ARTIFACT_ID, SCHEMA_VERSION, state, update, setState);

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setCloseBlockedError(null);
    const body = buildA3Body({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, state });

    try {
      const res = await saveArtifact(projectId, "T-25", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as A3Artifact;
        setServerArtifact(reloaded);
        setState(stateFromArtifact(reloaded));
      } catch {
        /* the save itself succeeded; a failed re-load just skips the badge/closure refresh */
      }
      try {
        setPrescore(await runPrescore("T-25", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      const exitMsg = err instanceof ApiError && err.validation ? err.validation.map((v) => v.msg).find((m) => m.includes("R-WRAP-03")) : undefined;
      if (exitMsg) {
        setCloseBlockedError(exitMsg);
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  return {
    state, update, setPanelNarrative, reseedPanel, seeding, loadFmeaForClose, setTollgateAnswer,
    version, saving, canSave: canSave(state) && !saving, missing: missingFields(state),
    generalError, closeBlockedError, prescore, serverArtifact, handleSave,
  };
}
