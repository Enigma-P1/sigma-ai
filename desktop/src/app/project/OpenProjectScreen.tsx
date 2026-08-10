import { useState } from "react";
import { Button, Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import { openProject } from "../../api/client";
import { ApiError } from "../../api/errors";
import { forgetProject, loadRecentProjects, rememberProject } from "./recentProjects";
import type { RecentProject } from "./recentProjects";
import { projectFolderPath } from "./path";
import { OnDiskProjects } from "./OnDiskProjects";
import "./RecentProjects.css";

export interface OpenProjectScreenProps {
  onOpened: (projectId: string) => void;
}

/** Open-project screen against GET /project/{id} (M1 brief).
 *
 * Two lists, deliberately, because they answer different questions.
 * "Recently opened" is a localStorage history ordered by when YOU last
 * looked, which is what "where was I" wants. "In your projects folder" is
 * GET /projects — what actually exists.
 *
 * For a long time only the first existed, so a project you had not opened
 * on this machine was invisible, including one you had just unzipped there
 * on purpose. There was no error: the list was simply, correctly, empty of
 * something that was really there (docs/field-notes.md). */
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
        <p className="sigma-recent-list__empty">No recent projects yet on this machine.</p>
      )}
      <p className="sigma-recent-list__section" data-testid="ondisk-heading">
        In your projects folder
      </p>
      <OnDiskProjects onOpen={(id) => void open(id)} hideIds={recents.map((p) => p.project_id)} />

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
