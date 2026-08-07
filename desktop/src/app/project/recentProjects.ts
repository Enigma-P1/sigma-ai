/** Recent-projects list, persisted in localStorage (M1 brief). The engine
 * has no "list projects" endpoint, so this list is the only way the app
 * remembers what exists between sessions -- it's a convenience index, not
 * the source of truth (the project folder on disk is). */

const STORAGE_KEY = "sigma-ai.recent-projects.v1";
const MAX_ENTRIES = 20;

export interface RecentProject {
  project_id: string;
  name: string;
  /** The project's real folder path from the engine's /project/{id}/info
   * (see path.ts's projectFolderPath), falling back to the documented
   * default only if that call failed at the time this was recorded. */
  folder_path: string;
  last_opened_at: string;
}

export function loadRecentProjects(): RecentProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed as RecentProject[];
  } catch {
    return [];
  }
}

export function rememberProject(entry: RecentProject): RecentProject[] {
  const existing = loadRecentProjects().filter((p) => p.project_id !== entry.project_id);
  const next = [entry, ...existing].slice(0, MAX_ENTRIES);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* localStorage unavailable (private mode, quota) -- degrade silently,
     * the session still works, it just won't be remembered next time. */
  }
  return next;
}

export function forgetProject(projectId: string): RecentProject[] {
  const next = loadRecentProjects().filter((p) => p.project_id !== projectId);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* see rememberProject */
  }
  return next;
}
