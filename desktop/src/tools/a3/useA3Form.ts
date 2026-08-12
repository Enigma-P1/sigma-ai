import { useEffect, useRef, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { useToolDraft } from "../../app/useToolDraft";
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
  // emptyState() hands back a fresh object every call (a3Logic.ts's own
  // choice, so nothing accidentally shares a mutable singleton) -- computed
  // once here and reused for both `state`'s initializer and the "no saved
  // version" baseline below, so the two start out `===` the way useToolDraft
  // needs them to for its own untouched-since-mount check.
  const emptyStateOnceRef = useRef<A3State | null>(null);
  if (emptyStateOnceRef.current === null) emptyStateOnceRef.current = emptyState();
  const EMPTY = emptyStateOnceRef.current;

  const [state, setState] = useState<A3State>(EMPTY);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [closeBlockedError, setCloseBlockedError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<A3Artifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  // What this form would show with no draft in play -- undefined until
  // that's settled, so useToolDraft never has to guess whether a stored
  // draft "differs" from a baseline that hasn't loaded yet.
  const [baseline, setBaseline] = useState<A3State | undefined>(undefined);

  useEffect(() => {
    if (!existingVersion) {
      setBaseline(EMPTY);
      return;
    }
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as A3Artifact;
        const loaded = stateFromArtifact(d);
        setState(loaded);
        setServerArtifact(d);
        setVersion(existingVersion);
        setBaseline(loaded);
      })
      .catch(() => {
        /* best-effort prefill; a blank A3 is still usable. Also the
           draft-restore baseline -- see CharterForm.tsx's identical catch
           for why this branch sets it too. */
        if (!cancelled) setBaseline(EMPTY);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion, EMPTY]);

  // Draft autosave (PLAN Phase 4.1) -- same wiring as CharterForm.tsx,
  // the tool this feature was built for; see useToolDraft.ts for the
  // restore/autosave contract.
  const draft = useToolDraft<A3State>(projectId, "T-25", { baseline, state, setState });

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
        const reloadedState = stateFromArtifact(reloaded);
        setState(reloadedState);
        setBaseline(reloadedState); // this is now the saved truth -- nothing left for a draft to protect
      } catch {
        // the save itself succeeded; a failed re-load just skips the
        // badge/closure refresh. Still move the draft baseline up to what
        // was actually saved (`state`, pre-reload), or useToolDraft would
        // see `state` and the old `baseline` disagree and autosave a new
        // draft for content that is already a real artifact.
        setBaseline(state);
      }
      // This typing is now a real artifact -- the draft that was
      // protecting it has nothing left to protect.
      draft.clearDraft();
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
    draftRestoredAt: draft.restoredAt, discardDraft: draft.discardDraft,
  };
}
