import { useState } from "react";
import { Button, Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import { openProject } from "../../api/client";
import { ApiError } from "../../api/errors";
import { forgetProject, loadRecentProjects, rememberProject } from "./recentProjects";
import type { RecentProject } from "./recentProjects";
import { projectFolderPath } from "./path";
import "./RecentProjects.css";

export interface OpenProjectScreenProps {
  onOpened: (projectId: string) => void;
}

/** Open-project screen against GET /project/{id} (M1 brief), backed by a
 * localStorage recent-projects list since the engine has no "list all
 * projects" endpoint. */
export function OpenProjectScreen({ onOpened }: OpenProjectScreenProps) {
  const [recents, setRecents] = useState<RecentProject[]>(() => loadRecentProjects());
  const [manualId, setManualId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function open(projectId: string) {
    if (!projectId.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const meta = await openProject(projectId.trim());
      // The project is confirmed to exist -- ask the engine for its real
      // path rather than the documented-default guess (path.ts).
      const folder_path = await projectFolderPath(meta.project_id);
      setRecents(
        rememberProject({
          project_id: meta.project_id,
          name: meta.name,
          folder_path,
          last_opened_at: new Date().toISOString(),
        }),
      );
      onOpened(meta.project_id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open that project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel title="Open a project">
      {recents.length > 0 ? (
        <ul className="sigma-recent-list">
          {recents.map((p) => (
            <li key={p.project_id} className="sigma-recent-list__row">
              <button
                type="button"
                className="sigma-recent-list__open"
                onClick={() => void open(p.project_id)}
                data-testid={`recent-project-${p.project_id}`}
              >
                <span className="sigma-recent-list__name">{p.name}</span>
                <span className="sigma-recent-list__path">{p.folder_path}</span>
              </button>
              <button
                type="button"
                className="sigma-recent-list__forget"
                onClick={() => setRecents(forgetProject(p.project_id))}
                aria-label={`Forget ${p.name}`}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="sigma-recent-list__path">No recent projects yet on this machine.</p>
      )}
      <Field label="Or open by project ID" htmlFor="open-project-id">
        <TextInput
          id="open-project-id"
          data-testid="open-project-id"
          value={manualId}
          onChange={(e) => setManualId(e.target.value)}
          placeholder="project-id"
        />
      </Field>
      {error && <VerdictBanner tone="fail" headline={error} />}
      <Button variant="secondary" disabled={submitting || !manualId.trim()} onClick={() => void open(manualId)} data-testid="open-project-submit">
        {submitting ? "Opening…" : "Open"}
      </Button>
    </Panel>
  );
}
