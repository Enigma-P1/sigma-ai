import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type {
  PrescoreResult,
  ProcessMapArtifact,
  ProcessMapConnector,
  ProcessMapLane,
  ProcessMapStep,
  ProjectMetadata,
  StepPosition,
} from "../../api/types";
import type { DemandValue } from "./processMapLogic";
import {
  buildProcessMapBody,
  canSaveProcessMap,
  defaultStepPosition,
  emptyDemand,
  emptyLane,
  emptyStep,
  laneIndexForY,
  processMapStateFromArtifact,
  reorderLane,
} from "./processMapLogic";

const ARTIFACT_ID = "process-map";
const SCHEMA_VERSION = 1;

/** T-06's state + engine wiring -- same load/save/reload/prescore shape as
 * useMsaForm.ts. The canvas (ProcessMapCanvas) and the HTML control strips
 * (LanesPanel/StepsList/ConnectorsPanel/StepInspector) all read and write
 * through this one hook, so "what's on the map" has exactly one owner. */
export function useProcessMapForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [lanes, setLanes] = useState<ProcessMapLane[]>([]);
  const [steps, setSteps] = useState<ProcessMapStep[]>([]);
  const [connectors, setConnectors] = useState<ProcessMapConnector[]>([]);
  const [layout, setLayout] = useState<Record<string, StepPosition>>({});
  const [demand, setDemand] = useState<DemandValue>(emptyDemand);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<ProcessMapArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as ProcessMapArtifact;
        const s = processMapStateFromArtifact(d);
        setLanes(s.lanes);
        setSteps(s.steps);
        setConnectors(s.connectors);
        setLayout(s.layout);
        setDemand(s.demand);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty canvas is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server longest_step/constraint_step no longer describe it
  }

  function addLane() {
    setLanes((prev) => [...prev, emptyLane(prev.length)]);
    dirty();
  }
  function updateLane(laneId: string, patch: Partial<ProcessMapLane>) {
    setLanes((prev) => prev.map((l) => (l.lane_id === laneId ? { ...l, ...patch } : l)));
    dirty();
  }
  function removeLane(laneId: string) {
    const doomedSteps = new Set(steps.filter((s) => s.lane_id === laneId).map((s) => s.step_id));
    setLanes((prev) => prev.filter((l) => l.lane_id !== laneId));
    setSteps((prev) => prev.filter((s) => !doomedSteps.has(s.step_id)));
    setConnectors((prev) => prev.filter((c) => !doomedSteps.has(c.from_step) && !doomedSteps.has(c.to_step)));
    if (selectedStepId && doomedSteps.has(selectedStepId)) setSelectedStepId(null);
    dirty();
  }

  function addStep(laneId?: string) {
    const targetLane = laneId ?? lanes[0]?.lane_id;
    if (!targetLane) return;
    const laneIndex = lanes.findIndex((l) => l.lane_id === targetLane);
    const stepsInLane = steps.filter((s) => s.lane_id === targetLane).length;
    const step = emptyStep(targetLane, stepsInLane + 1);
    setSteps((prev) => [...prev, step]);
    setLayout((prev) => ({ ...prev, [step.step_id]: defaultStepPosition(laneIndex, stepsInLane) }));
    setSelectedStepId(step.step_id);
    dirty();
  }
  function updateStep(stepId: string, patch: Partial<ProcessMapStep>) {
    setSteps((prev) => prev.map((s) => (s.step_id === stepId ? { ...s, ...patch } : s)));
    dirty();
  }
  function removeStep(stepId: string) {
    setSteps((prev) => prev.filter((s) => s.step_id !== stepId));
    setConnectors((prev) => prev.filter((c) => c.from_step !== stepId && c.to_step !== stepId));
    setLayout((prev) => {
      const next = { ...prev };
      delete next[stepId];
      return next;
    });
    if (selectedStepId === stepId) setSelectedStepId(null);
    dirty();
  }

  /** Canvas drag-end: reposition, reassign lane by drop Y, and recompute
   * `order` in whichever lane(s) changed (processMapLogic.reorderLane). */
  function moveStep(stepId: string, x: number, y: number) {
    const newLayout = { ...layout, [stepId]: { x, y } };
    const oldLaneId = steps.find((s) => s.step_id === stepId)?.lane_id;
    const newLaneId = lanes[laneIndexForY(y, lanes.length)]?.lane_id ?? oldLaneId;
    let nextSteps = steps.map((s) => (s.step_id === stepId ? { ...s, lane_id: newLaneId ?? s.lane_id } : s));
    if (oldLaneId) nextSteps = reorderLane(nextSteps, oldLaneId, newLayout);
    if (newLaneId && newLaneId !== oldLaneId) nextSteps = reorderLane(nextSteps, newLaneId, newLayout);
    setLayout(newLayout);
    setSteps(nextSteps);
    dirty();
  }

  function addConnector(fromStep: string, toStep: string, label: string) {
    if (!fromStep || !toStep || fromStep === toStep) return;
    if (connectors.some((c) => c.from_step === fromStep && c.to_step === toStep)) return;
    setConnectors((prev) => [...prev, { from_step: fromStep, to_step: toStep, label: label.trim() || null }]);
    dirty();
  }
  function removeConnector(index: number) {
    setConnectors((prev) => prev.filter((_, i) => i !== index));
    dirty();
  }

  function updateDemand(patch: Partial<DemandValue>) {
    setDemand((prev) => ({ ...prev, ...patch }));
    dirty();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const body = buildProcessMapBody({
      artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, lanes, steps, connectors, layout, demand,
    });

    try {
      const res = await saveArtifact(projectId, "T-06", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as ProcessMapArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the bottleneck banner blank */
      }
      try {
        setPrescore(await runPrescore("T-06", body));
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
    lanes, steps, connectors, layout, demand, selectedStepId, setSelectedStepId,
    addLane, updateLane, removeLane, addStep, updateStep, removeStep, moveStep,
    addConnector, removeConnector, updateDemand,
    version, saving, canSave: canSaveProcessMap(lanes, steps) && !saving,
    generalError, fieldErrors, prescore, serverArtifact, handleSave,
  };
}
