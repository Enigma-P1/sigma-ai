import type {
  ProcessMapArtifact,
  ProcessMapConnector,
  ProcessMapLane,
  ProcessMapStep,
  StepPosition,
  StepType,
  WasteId,
} from "../../api/types";

/** Canvas layout constants -- shared by ProcessMapCanvas (rendering) and
 * the lane/order-on-drop math below, so "where a lane band is drawn" and
 * "which lane a dropped step lands in" can never drift apart. */
export const LANE_HEIGHT = 150;
export const LANE_LABEL_WIDTH = 170;
export const STEP_WIDTH = 150;
export const STEP_HEIGHT = 68;
export const STEP_GAP = 26;
export const CANVAS_TOP_PADDING = 20;

export const STEP_TYPE_LABELS: Record<StepType, string> = {
  value_add: "Value-add",
  non_value_add: "Non-value-add",
  enabling: "Enabling",
};

export const WASTE_CATALOG: { id: WasteId; label: string }[] = [
  { id: "defects", label: "Defects" },
  { id: "overproduction", label: "Overproduction" },
  { id: "waiting", label: "Waiting" },
  { id: "non_utilized_talent", label: "Non-utilized talent" },
  { id: "transportation", label: "Transportation" },
  { id: "inventory", label: "Inventory" },
  { id: "motion", label: "Motion" },
  { id: "extra_processing", label: "Extra-processing" },
];

let counter = 0;
/** Deterministic-enough unique id for a session (not persisted identity --
 * once saved, the id itself is what's persisted). Counter-based, not
 * timestamp-based, so two ids requested in the same tick never collide. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function laneTopY(laneIndex: number): number {
  return CANVAS_TOP_PADDING + laneIndex * LANE_HEIGHT;
}

/** Inverse of laneTopY, clamped to the valid lane range -- what a step's
 * drag-end Y coordinate maps to. */
export function laneIndexForY(y: number, laneCount: number): number {
  const idx = Math.floor((y - CANVAS_TOP_PADDING) / LANE_HEIGHT);
  return Math.min(Math.max(idx, 0), Math.max(laneCount - 1, 0));
}

export function defaultStepPosition(laneIndex: number, stepsAlreadyInLane: number): StepPosition {
  return {
    x: LANE_LABEL_WIDTH + 20 + stepsAlreadyInLane * (STEP_WIDTH + STEP_GAP),
    y: laneTopY(laneIndex) + (LANE_HEIGHT - STEP_HEIGHT) / 2,
  };
}

export function emptyLane(index: number): ProcessMapLane {
  return { lane_id: genId("lane"), name: `Lane ${index + 1}`, owner: "" };
}

export function emptyStep(laneId: string, order: number): ProcessMapStep {
  return {
    step_id: genId("step"),
    lane_id: laneId,
    name: "New step",
    order,
    step_type: "value_add",
    reason: "",
    time_minutes: null,
    defect_point: false,
    strata: [],
    wastes: [],
  };
}

export interface DemandValue {
  available_time_minutes: number | null;
  demand_units: number | null;
}

export const emptyDemand: DemandValue = { available_time_minutes: null, demand_units: null };

/** Recompute `order` for every step in one lane from left-to-right canvas
 * position -- what a drag-end (or a lane reassignment) calls so "order"
 * always reflects the card layout the user just arranged, never a stale
 * number from before the drag. */
export function reorderLane(steps: ProcessMapStep[], laneId: string, layout: Record<string, StepPosition>): ProcessMapStep[] {
  const inLane = steps.filter((s) => s.lane_id === laneId).sort((a, b) => (layout[a.step_id]?.x ?? 0) - (layout[b.step_id]?.x ?? 0));
  const orderByStepId = new Map(inLane.map((s, i) => [s.step_id, i + 1]));
  return steps.map((s) => (s.lane_id === laneId ? { ...s, order: orderByStepId.get(s.step_id) ?? s.order } : s));
}

/** Client-side display tally only (rubric R-MEA-02's waste-walk summary
 * strip) -- a plain count of already-loaded WasteEntry rows, the same kind
 * of reduction PrescoreStrip does over server-provided results. Not a
 * "computed result": no provenance, nothing the engine would need to
 * stamp, same distinction CopqForm draws around its own draft total. */
export function wasteTally(steps: ProcessMapStep[]): Record<WasteId, number> {
  const tally = Object.fromEntries(WASTE_CATALOG.map((w) => [w.id, 0])) as Record<WasteId, number>;
  for (const step of steps) {
    for (const w of step.wastes) tally[w.waste_id] += 1;
  }
  return tally;
}

export function canSaveProcessMap(lanes: ProcessMapLane[], steps: ProcessMapStep[]): boolean {
  return lanes.length > 0 && steps.length > 0 && lanes.every((l) => l.name.trim() !== "") && steps.every((s) => s.name.trim() !== "");
}

export function buildProcessMapBody(input: {
  artifactId: string;
  schemaVersion: number;
  lanes: ProcessMapLane[];
  steps: ProcessMapStep[];
  connectors: ProcessMapConnector[];
  layout: Record<string, StepPosition>;
  demand: DemandValue;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  const hasDemand = input.demand.available_time_minutes != null || input.demand.demand_units != null;
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-06",
    created_at: now,
    updated_at: now,
    lanes: input.lanes,
    steps: input.steps,
    connectors: input.connectors,
    demand: hasDemand ? input.demand : null,
    layout: input.layout,
  };
}

export function processMapStateFromArtifact(artifact: ProcessMapArtifact): {
  lanes: ProcessMapLane[];
  steps: ProcessMapStep[];
  connectors: ProcessMapConnector[];
  layout: Record<string, StepPosition>;
  demand: DemandValue;
} {
  return {
    lanes: artifact.lanes,
    steps: artifact.steps,
    connectors: artifact.connectors,
    layout: artifact.layout ?? {},
    demand: {
      available_time_minutes: artifact.demand?.available_time_minutes ?? null,
      demand_units: artifact.demand?.demand_units ?? null,
    },
  };
}
