import type { Quadrant, Solution, SolutionCriterion } from "../../api/types";
import type { SolutionMatrixArtifact } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as fmeaLogic.ts's genId -- unique for a
 * session, not persisted identity. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptySolution(): Solution {
  return { solution_id: genId("solution"), name: "", description: "", linked_cause_ids: [], impact: 3, effort: 3, criterion_scores: [] };
}

export function emptyCriterion(): SolutionCriterion {
  return { criterion_id: genId("criterion"), name: "", weight: 1, declared_at: new Date().toISOString() };
}

export const QUADRANT_LABELS: Record<Quadrant, string> = {
  quick_win: "Quick win",
  major_project: "Major project",
  fill_in: "Fill-in",
  thankless_task: "Thankless task",
};

/** Client-side-only display value before the first save -- mirrors
 * artifacts/solution_matrix.py's compute_quadrant exactly (both axes are
 * the same 1-5 scale split at its own midpoint, >=3 "high"). Authoritative
 * once the engine has echoed the artifact back (FmeaRow.rpn's draftRpn
 * idiom, fmeaLogic.ts). */
export function draftQuadrant(impact: number, effort: number): Quadrant {
  const highImpact = impact >= 3;
  const highEffort = effort >= 3;
  if (highImpact && !highEffort) return "quick_win";
  if (highImpact && highEffort) return "major_project";
  if (!highImpact && !highEffort) return "fill_in";
  return "thankless_task";
}

/** Client-side-only weighted total -- mirrors artifacts/solution_matrix.py's
 * compute_solution_scores: null unless every declared criterion has a
 * score recorded (a partial set never produces a trustworthy number, same
 * schema-hard rule the engine enforces at save). */
export function draftWeightedTotal(solution: Solution, criteria: SolutionCriterion[]): number | null {
  if (solution.criterion_scores.length === 0 || criteria.length === 0) return null;
  const weightById = new Map(criteria.map((c) => [c.criterion_id, c.weight]));
  const scoredIds = new Set(solution.criterion_scores.map((sc) => sc.criterion_id));
  if (scoredIds.size !== criteria.length || ![...weightById.keys()].every((id) => scoredIds.has(id))) return null;
  let total = 0;
  for (const sc of solution.criterion_scores) {
    const w = weightById.get(sc.criterion_id);
    if (w == null) return null;
    total += sc.score * w;
  }
  return Math.round(total * 10000) / 10000;
}

export function solutionMatrixMissingFields(solutions: Solution[]): string[] {
  const missing: string[] = [];
  if (solutions.length === 0) missing.push("at least one solution");
  if (!solutions.every((s) => s.name.trim() !== "")) missing.push("every solution's name");
  return missing;
}

export function canSaveSolutionMatrix(solutions: Solution[]): boolean {
  return solutionMatrixMissingFields(solutions).length === 0;
}

export function buildSolutionMatrixBody(input: {
  artifactId: string;
  schemaVersion: number;
  solutions: Solution[];
  criteria: SolutionCriterion[];
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-18",
    created_at: now, updated_at: now, solutions: input.solutions, criteria: input.criteria,
  };
}

export function solutionMatrixStateFromArtifact(artifact: SolutionMatrixArtifact): { solutions: Solution[]; criteria: SolutionCriterion[] } {
  return { solutions: artifact.solutions, criteria: artifact.criteria };
}

/** Dropping a criterion strips every solution's now-dangling score for it
 * -- the schema rejects a criterion_scores entry referencing an undeclared
 * criterion_id, so the client keeps the two lists consistent on removal
 * rather than let a save fail with a confusing error. */
export function stripCriterionScores(solutions: Solution[], removedCriterionId: string): Solution[] {
  return solutions.map((s) => ({ ...s, criterion_scores: s.criterion_scores.filter((sc) => sc.criterion_id !== removedCriterionId) }));
}
