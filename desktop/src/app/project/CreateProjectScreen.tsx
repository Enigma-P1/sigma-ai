import { useState } from "react";
import { Button, Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import { createProject } from "../../api/client";
import { ApiError } from "../../api/errors";
import { defaultProjectFolderPath, projectFolderPath, slugify } from "./path";
import { rememberProject } from "./recentProjects";

export interface CreateProjectScreenProps {
  onCreated: (projectId: string) => void;
}

/** Create-project screen against POST /project/create (M1 brief). */
export function CreateProjectScreen({ onCreated }: CreateProjectScreenProps) {
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("");
  const [idTouched, setIdTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const effectiveId = idTouched ? projectId : slugify(name);

  async function submit() {
    if (!name.trim() || !effectiveId.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const created_at = new Date().toISOString();
      const meta = await createProject({ project_id: effectiveId, name: name.trim(), created_at });
      // The project now exists on disk -- ask the engine for its real path
      // rather than repeating the pre-creation guess (path.ts).
      const folder_path = await projectFolderPath(meta.project_id);
      rememberProject({ project_id: meta.project_id, name: meta.name, folder_path, last_opened_at: created_at });
      onCreated(meta.project_id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel title="Start a new project">
      <Field label="Project name" required htmlFor="create-project-name">
        <TextInput
          id="create-project-name"
          data-testid="create-project-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Coffee Bar order-to-handoff time"
        />
      </Field>
      {/* "Project folder (ID)" read as a technical field a supervisor was
        * expected to understand: one tester said it "sounds like a
        * technical field, not something I would expect to fill in as an
        * operations supervisor", and asked for the folder name to be named
        * as a folder name and marked leave-alone. It fills itself in from
        * the project name, so most people should never touch it. */}
      <Field
        label="Folder name on this computer"
        htmlFor="create-project-id"
        helper={`Filled in from the project name — leave it alone unless you need a different folder. Saved in ${defaultProjectFolderPath(effectiveId || "…")}`}
      >
        <TextInput
          id="create-project-id"
          data-testid="create-project-id"
          value={effectiveId}
          onChange={(e) => {
            setProjectId(e.target.value);
            setIdTouched(true);
          }}
        />
      </Field>
      {error && <VerdictBanner tone="fail" headline={error} />}
      <Button variant="primary" disabled={submitting || !name.trim()} onClick={() => void submit()} data-testid="create-project-submit">
        {submitting ? "Creating…" : "Create project"}
      </Button>
    </Panel>
  );
}
