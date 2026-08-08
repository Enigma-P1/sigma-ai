import { useEffect, useMemo, useState } from "react";
import { getFloorPlan, loadArtifact, runPrescore, saveArtifact, uploadFloorPlan } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { fileToBase64 } from "../dataimport/dataImportLogic";
import type {
  Calibration, FloorPlanRef, LayoutMode, Operator, ObservationWindow,
  PrescoreResult, ProjectMetadata, RouteMetrics, SpaghettiArtifact, SpaghettiRoute, SpaghettiUnit,
} from "../../api/types";
import type { CanvasMode } from "./SpaghettiCanvas";
import type { DraftPoint } from "./spaghettiLogic";
import {
  buildSpaghettiBody, canSaveSpaghetti, emptyObservationWindow, emptyOperator, newRoute, spaghettiStateFromArtifact,
} from "./spaghettiLogic";

const ARTIFACT_ID = "spaghetti";
const SCHEMA_VERSION = 1;

/** T-07's state + engine wiring -- same load/save/reload/prescore shape as
 * useProcessMapForm.ts, extended for the upload step and the calibrate/
 * trace canvas modes. The canvas and every panel around it read and write
 * through this one hook, so "what's on the diagram" has exactly one owner. */
export function useSpaghettiForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();

  const [floorPlan, setFloorPlan] = useState<FloorPlanRef | null>(null);
  const [floorPlanImageSrc, setFloorPlanImageSrc] = useState<string | null>(null);
  const [uploadingFloorPlan, setUploadingFloorPlan] = useState(false);
  const [floorPlanError, setFloorPlanError] = useState<string | null>(null);

  const [calibration, setCalibration] = useState<Calibration | null>(null);
  const [calibrating, setCalibrating] = useState(false);
  const [calibrationDraft, setCalibrationDraft] = useState<DraftPoint[]>([]);

  const [operators, setOperators] = useState<Operator[]>([]);
  const [routes, setRoutes] = useState<SpaghettiRoute[]>([]);

  const [tracing, setTracing] = useState(false);
  const [traceDraft, setTraceDraft] = useState<DraftPoint[]>([]);
  const [traceOperatorId, setTraceOperatorId] = useState("");
  const [traceTripLabel, setTraceTripLabel] = useState("");
  const [traceFrequencyText, setTraceFrequencyText] = useState("");

  const [activeLayoutMode, setActiveLayoutMode] = useState<LayoutMode>("current");
  const [heatmapOn, setHeatmapOn] = useState(false);
  const [walkSpeedOverrideText, setWalkSpeedOverrideText] = useState("");
  const [observationWindow, setObservationWindow] = useState<ObservationWindow>(emptyObservationWindow);

  const [playbackRouteId, setPlaybackRouteId] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);

  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<SpaghettiArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then(async (data) => {
        if (cancelled) return;
        const d = data as unknown as SpaghettiArtifact;
        const s = spaghettiStateFromArtifact(d);
        setFloorPlan(s.floorPlan);
        setCalibration(s.calibration);
        setOperators(s.operators);
        setRoutes(s.routes);
        setWalkSpeedOverrideText(s.walkSpeedOverride != null ? String(s.walkSpeedOverride) : "");
        setObservationWindow(s.observationWindow);
        setServerArtifact(d);
        setVersion(existingVersion);
        try {
          const detail = await getFloorPlan(projectId, s.floorPlan.image_id);
          if (!cancelled) setFloorPlanImageSrc(`data:${detail.meta.content_type};base64,${detail.content_base64}`);
        } catch {
          /* best-effort image re-fetch; the rest of the artifact still loaded */
        }
      })
      .catch(() => {
        /* best-effort prefill; an empty canvas is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function dirty() {
    setServerArtifact(null); // state changed since the last save -- the old server metrics no longer describe it
  }

  async function handleFloorPlanSelected(file: File) {
    setUploadingFloorPlan(true);
    setFloorPlanError(null);
    try {
      const base64 = await fileToBase64(file);
      const meta = await uploadFloorPlan(projectId, { source_filename: file.name, content_base64: base64, created_at: new Date().toISOString() });
      setFloorPlan(meta);
      setFloorPlanImageSrc(`data:${meta.content_type};base64,${base64}`);
      dirty();
    } catch (err) {
      setFloorPlanError(err instanceof ApiError ? err.message : "Could not upload that image.");
    } finally {
      setUploadingFloorPlan(false);
    }
  }

  function startCalibration() {
    setCalibrating(true);
    setTracing(false);
    setCalibrationDraft([]);
  }
  function cancelCalibration() {
    setCalibrating(false);
    setCalibrationDraft([]);
  }
  function confirmCalibration(realLength: number, unit: SpaghettiUnit) {
    if (calibrationDraft.length !== 2) return;
    setCalibration({ point_a: calibrationDraft[0], point_b: calibrationDraft[1], real_length: realLength, unit });
    setCalibrating(false);
    setCalibrationDraft([]);
    dirty();
  }

  function startTrace() {
    setTracing(true);
    setCalibrating(false);
    setTraceDraft([]);
  }
  function cancelTrace() {
    setTracing(false);
    setTraceDraft([]);
  }
  function undoTracePoint() {
    setTraceDraft((prev) => prev.slice(0, -1));
  }
  function finishTrace() {
    const frequency = Number(traceFrequencyText);
    if (traceDraft.length < 2 || !traceOperatorId || !traceTripLabel.trim() || !(frequency > 0)) return;
    const route = newRoute({
      operatorId: traceOperatorId, tripLabel: traceTripLabel.trim(), frequencyPerDay: frequency,
      points: traceDraft, layoutMode: activeLayoutMode,
    });
    setRoutes((prev) => [...prev, route]);
    setTraceDraft([]);
    setTracing(false);
    dirty();
  }

  /** Dispatches a raw canvas click to whichever mode is active -- the
   * canvas component itself stays a dumb renderer that never knows about
   * calibrate-vs-trace state. */
  function handleCanvasClick(point: DraftPoint) {
    if (calibrating) {
      setCalibrationDraft((prev) => (prev.length >= 2 ? [point] : [...prev, point]));
    } else if (tracing) {
      setTraceDraft((prev) => [...prev, point]);
    }
  }

  function addOperator() {
    setOperators((prev) => [...prev, emptyOperator(prev.length)]);
    dirty();
  }
  function updateOperator(operatorId: string, patch: Partial<Operator>) {
    setOperators((prev) => prev.map((o) => (o.operator_id === operatorId ? { ...o, ...patch } : o)));
    dirty();
  }
  function removeOperator(operatorId: string) {
    setOperators((prev) => prev.filter((o) => o.operator_id !== operatorId));
    setRoutes((prev) => prev.filter((r) => r.operator_id !== operatorId)); // cascade, mirrors LanesPanel's removeLane
    if (traceOperatorId === operatorId) setTraceOperatorId("");
    dirty();
  }

  function removeRoute(routeId: string) {
    setRoutes((prev) => prev.filter((r) => r.route_id !== routeId));
    if (playbackRouteId === routeId) setPlaybackRouteId(null);
    dirty();
  }

  function togglePlay() {
    setPlaying((p) => !p);
  }

  /** Unlike observationWindow (inert with respect to metrics), a walk-speed
   * override changes the computed walk-time figures -- mark dirty the same
   * way updateDemand does in useProcessMapForm.ts, so a stale metrics panel
   * never sits next to a not-yet-saved override value. */
  function updateWalkSpeedOverrideText(text: string) {
    setWalkSpeedOverrideText(text);
    dirty();
  }

  const canvasMode: CanvasMode = calibrating ? "calibrate" : tracing ? "trace" : "idle";

  const metricsByRouteId = useMemo(() => {
    if (!serverArtifact?.metrics) return null;
    const map: Record<string, RouteMetrics> = {};
    for (const rm of serverArtifact.metrics.value.routes) map[rm.route_id] = rm;
    return map;
  }, [serverArtifact]);

  async function handleSave() {
    if (!floorPlan) return;
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const walkSpeedOverride = walkSpeedOverrideText.trim() === "" ? null : Number(walkSpeedOverrideText);
    const body = buildSpaghettiBody({
      artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, floorPlan, calibration, operators, routes,
      walkSpeedOverride, observationWindow,
    });

    try {
      const res = await saveArtifact(projectId, "T-07", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as SpaghettiArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the metrics/delta panels blank */
      }
      try {
        setPrescore(await runPrescore("T-07", body));
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
    floorPlan, floorPlanImageSrc, uploadingFloorPlan, floorPlanError, handleFloorPlanSelected,
    calibration, calibrating, calibrationDraft, startCalibration, cancelCalibration, confirmCalibration,
    operators, addOperator, updateOperator, removeOperator,
    routes, removeRoute, metricsByRouteId,
    tracing, traceDraft, traceOperatorId, setTraceOperatorId, traceTripLabel, setTraceTripLabel,
    traceFrequencyText, setTraceFrequencyText, startTrace, cancelTrace, undoTracePoint, finishTrace,
    canvasMode, handleCanvasClick,
    activeLayoutMode, setActiveLayoutMode, heatmapOn, setHeatmapOn,
    walkSpeedOverrideText, setWalkSpeedOverrideText: updateWalkSpeedOverrideText, observationWindow, setObservationWindow,
    playbackRouteId, setPlaybackRouteId, playing, togglePlay,
    version, saving, canSave: canSaveSpaghetti(floorPlan) && !saving,
    generalError, fieldErrors, prescore, serverArtifact, handleSave,
  };
}
