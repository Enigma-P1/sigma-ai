import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact, timeStudyToDataset } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { DatasetMeta, ElementTime, PrescoreResult, ProjectMetadata, TimeStudyArtifact, TimeStudyCycle, WorkElement } from "../../api/types";
import {
  buildTimeStudyBody, canSaveTimeStudy, emptyElement, manualCycle, markCycleDeleted, nextCycleNumber,
  removeElementCascade, setCycleElementSeconds, setCycleNote, timeStudyStateFromArtifact,
} from "./timeStudyLogic";
import { useStopwatch } from "./useStopwatch";
import { useWorkSampling } from "./useWorkSampling";

const ARTIFACT_ID = "timestudy";
const SCHEMA_VERSION = 1;

/** T-09's state + engine wiring. Composes useStopwatch (timer mechanics)
 * and useWorkSampling (the optional interval-observation tab) rather than
 * folding everything inline -- this hook owns elements/cycles/save/
 * to_dataset, the two composed hooks own their own narrower state. */
export function useTimeStudyForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [elements, setElements] = useState<WorkElement[]>([emptyElement(0)]);
  const [cycles, setCycles] = useState<TimeStudyCycle[]>([]);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<TimeStudyArtifact | null>(null);
  const [datasetsByElement, setDatasetsByElement] = useState<Record<string, DatasetMeta>>({});
  const [sendingElementId, setSendingElementId] = useState<string | null>(null);
  const [sendError, setSendError] = useState<string | null>(null);
  const [currentCycleTimes, setCurrentCycleTimes] = useState<ElementTime[]>([]);
  const [currentNote, setCurrentNote] = useState("");

  function dirty() {
    setServerArtifact(null); // state changed since the last save
    setDatasetsByElement({}); // the exported per-element datasets described the old cycles
  }

  const workSampling = useWorkSampling(dirty);
  const stopwatch = useStopwatch();

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as TimeStudyArtifact;
        const s = timeStudyStateFromArtifact(d);
        setElements(s.elements);
        setCycles(s.cycles);
        workSampling.replaceAll(s.intervalObservations);
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
    // workSampling's identity changes every render (it's not memoized) --
    // intentionally excluded from deps so this effect only re-runs on a
    // real project/version change, not on every observation edit.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, existingVersion]);

  function addElement() {
    setElements((p) => [...p, emptyElement(p.length)]);
    dirty();
  }
  function updateElement(id: string, patch: Partial<WorkElement>) {
    setElements((p) => p.map((e) => (e.element_id === id ? { ...e, ...patch } : e)));
    dirty();
  }
  function removeElement(id: string) {
    const next = removeElementCascade(elements, cycles, id);
    setElements(next.elements);
    setCycles(next.cycles);
    dirty();
  }

  function addManualCycle() {
    setCycles((p) => [...p, manualCycle(nextCycleNumber(p), elements)]);
    dirty();
  }
  function updateCycleSeconds(cycleNumber: number, elementId: string, seconds: number) {
    setCycles((p) => setCycleElementSeconds(p, cycleNumber, elementId, seconds));
    dirty();
  }
  function updateCycleNote(cycleNumber: number, note: string) {
    setCycles((p) => setCycleNote(p, cycleNumber, note));
    dirty();
  }
  function deleteCycle(cycleNumber: number, reason: string) {
    setCycles((p) => markCycleDeleted(p, cycleNumber, reason, new Date().toISOString()));
    dirty();
  }

  // ---- Stopwatch-driven capture: start -> split per element -> finish ----
  function handleStopwatchStart() {
    setCurrentCycleTimes([]);
    setCurrentNote("");
    stopwatch.start();
  }
  function handleStopwatchSplit(elementId: string) {
    if (!stopwatch.running) return;
    const seconds = stopwatch.split();
    setCurrentCycleTimes((p) => [...p.filter((t) => t.element_id !== elementId), { element_id: elementId, seconds }]);
  }
  function handleFinishCycle() {
    if (currentCycleTimes.length === 0) return;
    setCycles((p) => [...p, { cycle_number: nextCycleNumber(p), element_times: currentCycleTimes, observer_note: currentNote }]);
    setCurrentCycleTimes([]);
    setCurrentNote("");
    stopwatch.reset();
    dirty();
  }
  function handleCancelCycle() {
    setCurrentCycleTimes([]);
    setCurrentNote("");
    stopwatch.reset();
  }

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildTimeStudyBody({
      artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, elements, cycles, intervalObservations: workSampling.observations,
    });
    try {
      const res = await saveArtifact(projectId, "T-09", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as TimeStudyArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the stats panel blank */
      }
      try {
        setPrescore(await runPrescore("T-09", body));
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

  async function handleSendElementToBaseline(elementId: string) {
    if (version == null) return;
    setSendingElementId(elementId);
    setSendError(null);
    try {
      const meta = await timeStudyToDataset(projectId, ARTIFACT_ID, { element_id: elementId, created_at: new Date().toISOString() });
      setDatasetsByElement((p) => ({ ...p, [elementId]: meta }));
    } catch (err) {
      setSendError(err instanceof ApiError ? err.message : "Could not export this element to a dataset.");
    } finally {
      setSendingElementId(null);
    }
  }

  return {
    elements, addElement, updateElement, removeElement,
    cycles, addManualCycle, updateCycleSeconds, updateCycleNote, deleteCycle,
    stopwatch, currentCycleTimes, currentNote, setCurrentNote,
    handleStopwatchStart, handleStopwatchSplit, handleFinishCycle, handleCancelCycle,
    workSampling,
    version, saving, canSave: canSaveTimeStudy(elements) && !saving,
    generalError, prescore, serverArtifact, handleSave,
    datasetsByElement, sendingElementId, sendError, handleSendElementToBaseline,
  };
}
