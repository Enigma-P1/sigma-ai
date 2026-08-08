import type { ElementTime, IntervalObservation, TimeStudyArtifact, TimeStudyCycle, WorkElement, WorkSamplingCategory } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as processMapLogic.ts's genId. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyElement(index: number): WorkElement {
  return { element_id: genId("elem"), name: `Element ${index + 1}`, description: "" };
}

export function canSaveTimeStudy(elements: WorkElement[]): boolean {
  return elements.length > 0 && elements.every((e) => e.name.trim() !== "");
}

export function nextCycleNumber(cycles: TimeStudyCycle[]): number {
  return cycles.reduce((max, c) => Math.max(max, c.cycle_number), 0) + 1;
}

/** A freshly manually-added cycle: every declared element seeded at 0s,
 * immediately editable in CyclesTable (also how a smoke/component test
 * enters exact hand-computable values without depending on wall-clock
 * timing -- the stopwatch and this manual path both just produce a Cycle). */
export function manualCycle(cycleNumber: number, elements: WorkElement[]): TimeStudyCycle {
  return {
    cycle_number: cycleNumber,
    element_times: elements.map((e) => ({ element_id: e.element_id, seconds: 0 })),
    observer_note: "",
  };
}

export function setCycleElementSeconds(cycles: TimeStudyCycle[], cycleNumber: number, elementId: string, seconds: number): TimeStudyCycle[] {
  return cycles.map((c) => {
    if (c.cycle_number !== cycleNumber) return c;
    const has = c.element_times.some((et) => et.element_id === elementId);
    const element_times: ElementTime[] = has
      ? c.element_times.map((et) => (et.element_id === elementId ? { ...et, seconds } : et))
      : [...c.element_times, { element_id: elementId, seconds }];
    return { ...c, element_times };
  });
}

export function setCycleNote(cycles: TimeStudyCycle[], cycleNumber: number, note: string): TimeStudyCycle[] {
  return cycles.map((c) => (c.cycle_number === cycleNumber ? { ...c, observer_note: note } : c));
}

/** mm:ss.t display for the stopwatch (StopwatchPanel) -- capture-only
 * formatting, never what a stats panel renders (those come verbatim from
 * the engine's computed element_stats). */
export function formatStopwatch(ms: number): string {
  const totalSeconds = Math.max(0, ms) / 1000;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = (totalSeconds % 60).toFixed(1);
  return `${minutes}:${seconds.padStart(4, "0")}`;
}

export function makeObservation(category: WorkSamplingCategory): IntervalObservation {
  return { observation_id: genId("obs"), timestamp: new Date().toISOString(), category, note: "" };
}

export function buildTimeStudyBody(input: {
  artifactId: string;
  schemaVersion: number;
  elements: WorkElement[];
  cycles: TimeStudyCycle[];
  intervalObservations: IntervalObservation[];
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-09",
    created_at: now,
    updated_at: now,
    elements: input.elements,
    cycles: input.cycles,
    interval_observations: input.intervalObservations,
  };
}

export function timeStudyStateFromArtifact(artifact: TimeStudyArtifact): {
  elements: WorkElement[];
  cycles: TimeStudyCycle[];
  intervalObservations: IntervalObservation[];
} {
  return { elements: artifact.elements, cycles: artifact.cycles, intervalObservations: artifact.interval_observations };
}

/** Removing an element strips its times from every cycle (never leaving a
 * cycle referencing an undeclared element_id, same reasoning as
 * checkSheetLogic's removeCategoryCascade) -- cycles left with zero
 * element_times are dropped entirely (the schema requires >=1 per cycle). */
export function removeElementCascade(elements: WorkElement[], cycles: TimeStudyCycle[], elementId: string) {
  return {
    elements: elements.filter((e) => e.element_id !== elementId),
    cycles: cycles
      .map((c) => ({ ...c, element_times: c.element_times.filter((et) => et.element_id !== elementId) }))
      .filter((c) => c.element_times.length > 0),
  };
}
