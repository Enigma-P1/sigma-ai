import { getProjectInfo } from "../../api/client";

/** The project's real folder path, from the engine's GET
 * /project/{id}/info (routes/projects.py, backed by
 * ProjectStore.resolved_project_path) -- closes the gap this module used
 * to carry: there was no endpoint that reported a project's real on-disk
 * path, so the app rendered the documented default instead and labeled it
 * as such. Only usable once the project exists on disk (create/open have
 * already succeeded); falls back to the documented default if the engine
 * call fails for any reason, so a transient error never blocks remembering
 * the project in the recents list. */
export async function projectFolderPath(projectId: string): Promise<string> {
  try {
    const info = await getProjectInfo(projectId);
    return info.folder_path;
  } catch {
    return defaultProjectFolderPath(projectId);
  }
}

/** The engine's documented default location (routes/deps.py:
 * DEFAULT_PROJECTS_ROOT = ~/.sigma-ai/projects), for the create-project
 * screen's pre-creation preview -- there's no project on disk yet to ask
 * the engine about, so this is the only honest thing to show there. */
export function defaultProjectFolderPath(projectId: string): string {
  return `~/.sigma-ai/projects/${projectId}`;
}

/** Slugify a project name into a filesystem- and URL-safe project_id. */
export function slugify(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "project";
}
