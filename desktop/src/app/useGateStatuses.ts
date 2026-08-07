import { useEffect, useState } from "react";
import { checkGate } from "../api/client";
import type { GateResult, Phase } from "../api/types";
import { PHASE_ENTRY_GATES } from "./phases";
import { PHASES } from "./tools";
import { combineGateResults } from "./gateLogic";
import type { CombinedGate } from "./gateLogic";

/** Calls /gates/check for every gate_id in PHASE_ENTRY_GATES and combines
 * the results per phase. Re-runs when `refreshKey` changes (bump it after
 * any artifact save, since gate outcomes depend on which artifacts exist). */
export function useGateStatuses(
  projectId: string,
  refreshKey: number,
): { byPhase: Partial<Record<Phase, CombinedGate>>; loading: boolean } {
  const [byPhase, setByPhase] = useState<Partial<Record<Phase, CombinedGate>>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    async function run() {
      const allGateIds = Array.from(new Set(PHASES.flatMap((p) => PHASE_ENTRY_GATES[p])));
      const results: Record<string, GateResult> = {};
      await Promise.all(
        allGateIds.map(async (gateId) => {
          try {
            results[gateId] = await checkGate(gateId, projectId);
          } catch {
            // Leave this gate_id out of `results` on network/engine error;
            // combineGateResults treats an absent gate as no evidence
            // rather than crashing the whole rail.
          }
        }),
      );
      if (cancelled) return;

      const next: Partial<Record<Phase, CombinedGate>> = {};
      for (const phase of PHASES) {
        const ids = PHASE_ENTRY_GATES[phase];
        const subset: Record<string, GateResult> = {};
        for (const id of ids) {
          if (results[id]) subset[id] = results[id];
        }
        next[phase] = combineGateResults(subset);
      }
      setByPhase(next);
      setLoading(false);
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [projectId, refreshKey]);

  return { byPhase, loading };
}
