import type { GateResult, GateStatus } from "../api/types";

export interface CombinedGate {
  status: GateStatus;
  missing: string[];
  reasons: string[];
  byGateId: Record<string, GateResult>;
}

// Worst-status-wins ordering when a phase has more than one entry gate
// (Define has both a soft and a hard gate on the same Intake->Define
// transition -- gates.py's GATE_TABLE).
const SEVERITY: Record<GateStatus, number> = {
  HARD_BLOCK: 3,
  SOFT_BLOCK: 2,
  NOT_YET_BUILT: 1,
  CLEAR: 0,
};

export function combineGateResults(results: Record<string, GateResult>): CombinedGate {
  const entries = Object.entries(results);
  if (entries.length === 0) {
    return { status: "CLEAR", missing: [], reasons: [], byGateId: {} };
  }
  let status: GateStatus = "CLEAR";
  const missing = new Set<string>();
  const reasons: string[] = [];
  for (const [, result] of entries) {
    if (SEVERITY[result.status] > SEVERITY[status]) status = result.status;
    result.missing.forEach((m) => missing.add(m));
    if (result.reason) reasons.push(result.reason);
  }
  return { status, missing: [...missing], reasons, byGateId: results };
}
