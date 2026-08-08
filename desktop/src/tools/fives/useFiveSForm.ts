import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact, uploadFloorPlan } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { fileToBase64 } from "../dataimport/dataImportLogic";
import type { AuditRound, FiveSArtifact, FloorPlanRef, PrescoreResult, ProjectMetadata } from "../../api/types";
import { buildFiveSBody, canSave, emptyRound, fiveSStateFromArtifact, roundsMissingFields } from "./fiveSLogic";

const ARTIFACT_ID = "five-s";
const SCHEMA_VERSION = 1;

/** T-23's state + engine wiring. Photo upload reuses T-07's floor-plan
 * image store/route verbatim (uploadFloorPlan -- task brief's reuse
 * instruction), not a new endpoint. */
export function useFiveSForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [rounds, setRounds] = useState<AuditRound[]>([emptyRound()]);
  const [cadenceNote, setCadenceNote] = useState("");
  const [nextRoundDue, setNextRoundDue] = useState<string | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<FiveSArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as FiveSArtifact;
        const s = fiveSStateFromArtifact(d);
        setRounds(s.rounds);
        setCadenceNote(s.cadenceNote);
        setNextRoundDue(s.nextRoundDue);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; a fresh round is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function dirty() {
    setServerArtifact(null);
  }

  function addRound() {
    setRounds((prev) => [...prev, emptyRound()]);
    dirty();
  }
  function updateRound(roundId: string, patch: Partial<AuditRound>) {
    setRounds((prev) => prev.map((r) => (r.round_id === roundId ? { ...r, ...patch } : r)));
    dirty();
  }
  function removeRound(roundId: string) {
    setRounds((prev) => prev.filter((r) => r.round_id !== roundId));
    dirty();
  }

  async function addPhoto(roundId: string, file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      const base64 = await fileToBase64(file);
      const meta = await uploadFloorPlan(projectId, { source_filename: file.name, content_base64: base64, created_at: new Date().toISOString() });
      const ref: FloorPlanRef = { image_id: meta.image_id, source_filename: meta.source_filename, sha256: meta.sha256, width_px: meta.width_px, height_px: meta.height_px };
      updateRound(roundId, { photos: [...(rounds.find((r) => r.round_id === roundId)?.photos ?? []), ref] });
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Could not upload the photo.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildFiveSBody({ artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, rounds, cadenceNote, nextRoundDue });

    try {
      const res = await saveArtifact(projectId, "T-23", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        const reloaded = (await loadArtifact(projectId, ARTIFACT_ID)) as unknown as FiveSArtifact;
        setServerArtifact(reloaded);
      } catch {
        /* the save itself succeeded; a failed re-load just skips the trend refresh */
      }
      try {
        setPrescore(await runPrescore("T-23", body));
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

  return {
    rounds, addRound, updateRound, removeRound, addPhoto, uploading, uploadError,
    cadenceNote, setCadenceNote: (v: string) => { setCadenceNote(v); dirty(); },
    nextRoundDue, setNextRoundDue: (v: string | null) => { setNextRoundDue(v); dirty(); },
    version, saving, canSave: canSave(rounds) && !saving, missing: roundsMissingFields(rounds),
    generalError, prescore, serverArtifact, handleSave,
  };
}
