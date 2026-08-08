import { useState } from "react";
import { makeObservation } from "./timeStudyLogic";
import type { IntervalObservation, WorkSamplingCategory } from "../../api/types";

/** Interval-observation state for T-09's optional work-sampling tab,
 * composed into useTimeStudyForm rather than folded inline -- keeps that
 * hook to the cycle-timing path. `onChange` is useTimeStudyForm's own
 * dirty() (called synchronously, not deferred, so no stale-closure risk),
 * so a tap here invalidates the stale server view exactly like a cycle
 * edit does. */
export function useWorkSampling(onChange: () => void) {
  const [observations, setObservations] = useState<IntervalObservation[]>([]);

  function log(category: WorkSamplingCategory) {
    setObservations((p) => [...p, makeObservation(category)]);
    onChange();
  }
  function updateNote(observationId: string, note: string) {
    setObservations((p) => p.map((o) => (o.observation_id === observationId ? { ...o, note } : o)));
    onChange();
  }
  function remove(observationId: string) {
    setObservations((p) => p.filter((o) => o.observation_id !== observationId));
    onChange();
  }
  /** The load-on-open path only -- no onChange, this isn't a user edit. */
  function replaceAll(next: IntervalObservation[]) {
    setObservations(next);
  }

  return { observations, log, updateNote, remove, replaceAll };
}
