/** Lightweight, localStorage-backed "visited/Done" mark for tools that
 * have no artifact of their own to save -- T-14's chart screen is the one
 * case today (PLAN gives it no ARTIFACT_REGISTRY entry, so
 * project.artifact_index can never carry a "done" signal for it). Scoped
 * per project, read the same way the rail reads project.artifact_index
 * (PhaseSection.toolStatus) so a locally-visited tool renders Done exactly
 * like an artifact-backed one, and so the "I'm stuck" router's
 * completion-awareness (stuckTree.ts) sees it as done too. */

const KEY_PREFIX = "sigma-ai:tool-visited:";

function storageKey(projectId: string): string {
  return `${KEY_PREFIX}${projectId}`;
}

export function markToolVisited(projectId: string, toolId: string): void {
  try {
    const next = new Set(getVisitedTools(projectId));
    next.add(toolId);
    localStorage.setItem(storageKey(projectId), JSON.stringify([...next]));
  } catch {
    /* localStorage unavailable (private mode, etc.) -- Done just won't stick locally; not fatal */
  }
}

export function getVisitedTools(projectId: string): Set<string> {
  try {
    const raw = localStorage.getItem(storageKey(projectId));
    return new Set<string>(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}
