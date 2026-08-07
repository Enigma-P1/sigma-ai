import { useState } from "react";
import { Button, Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import { createProject } from "../../api/client";
import { ApiError } from "../../api/errors";
import { defaultProjectFolderPath, slugify } from "./path";
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
      rememberProject({
        project_id: meta.project_id,
        name: meta.name,
        folder_path: defaultProjectFolderPath(meta.project_id),
        last_opened_at: created_at,
      });
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
      <Field
        label="Project folder (ID)"
        htmlFor="create-project-id"
        helper={`Default location: ${defaultProjectFolderPath(effectiveId || "…")}`}
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
