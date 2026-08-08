import type {
  Calibration, FloorPlanRef, LayoutMode, Operator, ObservationWindow,
  SpaghettiArtifact, SpaghettiRoute,
} from "../../api/types";
import { genId } from "../processmap/processMapLogic";

export interface DraftPoint {
  x: number;
  y: number;
}

export function emptyOperator(index: number): Operator {
  return { operator_id: genId("operator"), name: `Operator ${index + 1}`, color_index: index };
}

export const emptyObservationWindow: ObservationWindow = { when: "", duration: "", shift: "" };

/** floor_plan is SpaghettiArtifact's one schema-required field (every
 * other coordinate on the canvas is meaningless without it) -- everything
 * else can legitimately be empty on an early save (mirrors T-06's
 * lanes/steps-required, demand-optional split). canSaveSpaghetti below and
 * the rendered "Missing: ..." hint both read from this one list (Jordan
 * usability fix). */
export function spaghettiMissingFields(floorPlan: FloorPlanRef | null): string[] {
  return floorPlan == null ? ["a floor plan image"] : [];
}

export function canSaveSpaghetti(floorPlan: FloorPlanRef | null): boolean {
  return spaghettiMissingFields(floorPlan).length === 0;
}

export function buildSpaghettiBody(input: {
  artifactId: string;
  schemaVersion: number;
  floorPlan: FloorPlanRef;
  calibration: Calibration | null;
  operators: Operator[];
  routes: SpaghettiRoute[];
  walkSpeedOverride: number | null;
  observationWindow: ObservationWindow;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-07",
    created_at: now,
    updated_at: now,
    floor_plan: input.floorPlan,
    calibration: input.calibration,
    operators: input.operators,
    routes: input.routes,
    walk_speed_override_per_minute: input.walkSpeedOverride,
    observation_window: input.observationWindow,
  };
}

export function spaghettiStateFromArtifact(artifact: SpaghettiArtifact): {
  floorPlan: FloorPlanRef;
  calibration: Calibration | null;
  operators: Operator[];
  routes: SpaghettiRoute[];
  walkSpeedOverride: number | null;
  observationWindow: ObservationWindow;
} {
  return {
    floorPlan: artifact.floor_plan,
    calibration: artifact.calibration ?? null,
    operators: artifact.operators,
    routes: artifact.routes,
    walkSpeedOverride: artifact.walk_speed_override_per_minute ?? null,
    observationWindow: artifact.observation_window,
  };
}

export function newRoute(input: {
  operatorId: string;
  tripLabel: string;
  frequencyPerDay: number;
  points: DraftPoint[];
  layoutMode: LayoutMode;
}): SpaghettiRoute {
  return {
    route_id: genId("route"), operator_id: input.operatorId, trip_label: input.tripLabel,
    frequency_per_day: input.frequencyPerDay, points: input.points.map((p) => ({ x: p.x, y: p.y })),
    layout_mode: input.layoutMode,
  };
}

// Heatmap toggle's strokeWidth scale -- a pure DISPLAY transform of
// already-known frequency_per_day (M2 brief: "labeled as such"), never a
// claimed engine number. Linear between a floor and a cap so one very-
// high-frequency route can't swallow the canvas.
const MIN_STROKE_WIDTH = 2;
const MAX_STROKE_WIDTH = 10;

export function heatmapStrokeWidth(frequencyPerDay: number, maxFrequencyPerDay: number): number {
  if (maxFrequencyPerDay <= 0) return MIN_STROKE_WIDTH;
  const ratio = Math.min(Math.max(frequencyPerDay / maxFrequencyPerDay, 0), 1);
  return MIN_STROKE_WIDTH + ratio * (MAX_STROKE_WIDTH - MIN_STROKE_WIDTH);
}

export function pointsToFlat(points: DraftPoint[]): number[] {
  return points.flatMap((p) => [p.x, p.y]);
}

export function operatorName(operators: Operator[], operatorId: string): string {
  return operators.find((o) => o.operator_id === operatorId)?.name ?? operatorId;
}

export function formatUnitValue(value: number, unit: string): string {
  return `${value.toFixed(1)} ${unit}`;
}
