/** Client-side memory of "the user already acknowledged this soft gate."
 *
 * The engine has no endpoint to list prior overrides (routes/gates.py only
 * exposes /check and /override) and /gates/check's status doesn't change
 * once an override is logged -- override() only appends to the project's
 * append-only overrides.log.jsonl (project_store.py), it doesn't feed back
 * into check()'s inputs. So re-checking a soft-blocked gate after a
 * successful override still returns SOFT_BLOCK from the engine. This module
 * is what stops the UI from re-prompting for a reason on every visit; the
 * engine-reported status is still shown, just alongside "you already
 * logged a reason for this." Flagged in the build report. */

const STORAGE_KEY = "sigma-ai.gate-overrides.v1";

interface OverrideRecord {
  reason: string;
  timestamp: string;
}

function keyFor(projectId: string, gateId: string): string {
  return `${projectId}::${gateId}`;
}

function readAll(): Record<string, OverrideRecord> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, OverrideRecord>) : {};
  } catch {
    return {};
  }
}

export function getGateOverride(projectId: string, gateId: string): OverrideRecord | undefined {
  return readAll()[keyFor(projectId, gateId)];
}

export function recordGateOverride(projectId: string, gateId: string, reason: string, timestamp: string): void {
  const all = readAll();
  all[keyFor(projectId, gateId)] = { reason, timestamp };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
  } catch {
    /* degrade silently -- worst case the user is asked again next visit */
  }
}
