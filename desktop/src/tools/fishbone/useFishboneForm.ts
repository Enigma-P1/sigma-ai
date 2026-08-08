import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { CausePosition, FishboneCause, FishboneEvidence, PrescoreResult, ProjectMetadata } from "../../api/types";
import type { FishboneArtifact } from "../../api/types";
import {
  buildFishboneBody,
  canSaveFishbone,
  causeDepth,
  causesForBranch,
  defaultCausePosition,
  emptyCause,
  fishboneStateFromArtifact,
} from "./fishboneLogic";

const ARTIFACT_ID = "fishbone";
const SCHEMA_VERSION = 1;

/** T-15's state + engine wiring -- same load/save/reload/prescore shape as
 * useProcessMapForm.ts. The canvas and the HTML control surfaces
 * (BranchList/CauseInspector/EvidenceDrawer) all read and write through
 * this one hook. */
export function useFishboneForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [effectText, setEffectText] = useState("");
  const [charterRef, setCharterRef] = useState("");
  const [causes, setCauses] = useState<FishboneCause[]>([]);
  const [layout, setLayout] = useState<Record<string, CausePosition>>({});
  const [selectedCauseId, setSelectedCauseId] = useState<string | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<FishboneArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as FishboneArtifact;
        const s = fishboneStateFromArtifact(d);
        setEffectText(s.effectText);
        setCharterRef(s.charterRef);
        setCauses(s.causes);
        setLayout(s.layout);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty diagram is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server verified_causes no longer describes it
  }

  function addCause(branch: FishboneCause["branch"]) {
    const cause = emptyCause(branch, null, null);
    setCauses((prev) => [...prev, cause]);
    setLayout((prev) => ({ ...prev, [cause.cause_id]: defaultCausePosition(branch, causesForBranch(causes, branch).length, 0) }));
    setSelectedCauseId(cause.cause_id);
    dirty();
  }

  /** "Ask why again": the 5-Whys affordance -- a child cause on the same
   * branch, one level deeper. */
  function addWhy(parentCauseId: string) {
    const parent = causes.find((c) => c.cause_id === parentCauseId);
    if (!parent) return;
    const depth = causeDepth(causes, parentCauseId) + 1;
    const nextPosition = (parent.why_chain_position ?? 1) + 1;
    const cause = emptyCause(parent.branch, parentCauseId, nextPosition);
    setCauses((prev) => [...prev, cause]);
    setLayout((prev) => ({
      ...prev,
      [cause.cause_id]: defaultCausePosition(parent.branch, causesForBranch(causes, parent.branch).length, depth),
    }));
    setSelectedCauseId(cause.cause_id);
    dirty();
  }

  function updateCause(causeId: string, patch: Partial<FishboneCause>) {
    setCauses((prev) => prev.map((c) => (c.cause_id === causeId ? { ...c, ...patch } : c)));
    dirty();
  }

  function setEvidence(causeId: string, evidence: FishboneEvidence | null) {
    updateCause(causeId, { evidence });
  }

  function moveCause(causeId: string, x: number, y: number) {
    setLayout((prev) => ({ ...prev, [causeId]: { x, y } }));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const body = buildFishboneBody({
      artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, effectText, charterRef: charterRef.trim() || null, causes, layout,
    });

    try {
      const res = await saveArtifact(projectId, "T-15", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as FishboneArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the summary panel blank */
      }
      try {
        setPrescore(await runPrescore("T-15", body));
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
    effectText, setEffectText, charterRef, setCharterRef,
    causes, layout, selectedCauseId, setSelectedCauseId,
    addCause, addWhy, updateCause, setEvidence, moveCause,
    version, saving, canSave: canSaveFishbone(effectText, causes) && !saving,
    generalError, fieldErrors, prescore, serverArtifact, handleSave,
  };
}
