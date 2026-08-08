import type { AuditRound, CategoryScore, FiveSArtifact, FiveSCategory } from "../../api/types";
import { FIVE_S_CATEGORIES } from "../../api/types";

let counter = 0;
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyScores(): CategoryScore[] {
  return FIVE_S_CATEGORIES.map((category) => ({ category, score: 0, note: "" }));
}

export function emptyRound(): AuditRound {
  return {
    round_id: genId("round"), date: new Date().toISOString().slice(0, 10), area: "",
    scores: emptyScores(), photos: [], improvement_action: "", improvement_action_owner: "",
  };
}

export function draftTotal(round: AuditRound): number {
  return round.scores.reduce((sum, s) => sum + s.score, 0);
}

export function draftLowestCategory(round: AuditRound): FiveSCategory {
  return round.scores.reduce((min, s) => (s.score < min.score ? s : min), round.scores[0]).category;
}

export function roundsMissingFields(rounds: AuditRound[]): string[] {
  const missing: string[] = [];
  if (rounds.length === 0) missing.push("at least one audit round");
  if (!rounds.every((r) => r.area.trim())) missing.push("every round's area");
  return missing;
}

export function canSave(rounds: AuditRound[]): boolean {
  return roundsMissingFields(rounds).length === 0;
}

export function buildFiveSBody(input: {
  artifactId: string; schemaVersion: number; rounds: AuditRound[]; cadenceNote: string; nextRoundDue: string | null;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-23",
    created_at: now, updated_at: now, rounds: input.rounds,
    schedule: input.cadenceNote.trim() ? { cadence_note: input.cadenceNote, next_round_due: input.nextRoundDue } : null,
  };
}

export function fiveSStateFromArtifact(a: FiveSArtifact): { rounds: AuditRound[]; cadenceNote: string; nextRoundDue: string | null } {
  return {
    rounds: a.rounds, cadenceNote: a.schedule?.cadence_note ?? "", nextRoundDue: a.schedule?.next_round_due ?? null,
  };
}
