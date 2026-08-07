/** Best-effort display of a project's folder path.
 *
 * There is no engine endpoint that reports a project's real on-disk path
 * (ProjectMetadata carries no path field -- see project_store.py) and the
 * browser/webview has no OS API to ask the running engine process what
 * SIGMA_PROJECTS_ROOT it was launched with. What we *can* say honestly is
 * the engine's documented default (routes/deps.py: DEFAULT_PROJECTS_ROOT =
 * ~/.sigma-ai/projects), so this renders that convention, clearly labeled
 * as the default rather than asserted as fact. Flagged in the build report.
 */
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
