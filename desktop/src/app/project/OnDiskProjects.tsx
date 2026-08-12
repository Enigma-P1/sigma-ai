import { useEffect, useState } from "react";
import { listProjects } from "../../api/client";
import type { ProjectSummary } from "../../api/client";
import { DeleteProjectButton } from "./DeleteProjectButton";
import "./RecentProjects.css";

export interface OnDiskProjectsProps {
  onOpen: (projectId: string) => void;
  /** Project ids already shown in the recently-opened list, so this section
   * shows what that one cannot rather than repeating it. */
  hideIds?: string[];
  /** Bump to force a refetch. Deleting a project from the RECENT list drops
   * it from hideIds, which would otherwise un-hide a row for it in the list
   * this component fetched at mount -- a project the user just deleted
   * reappearing under a different heading. Found by driving the real
   * screen; the two lists share a filesystem and had no way to tell each
   * other anything. */
  refreshKey?: number;
}

/** Every project actually in the projects folder.
 *
 * WHY THIS EXISTS: the Open-a-project screen was backed only by a
 * localStorage recently-opened history, so a project you had not opened on
 * THIS machine was invisible — including one you had just unzipped into the
 * projects folder on purpose. That is what happened with the worked example
 * (docs/field-notes.md): a complete project sitting on disk, and an app that
 * would not admit it existed, with no error to explain why.
 *
 * The recent list stays: it is genuinely better for "where was I", because
 * it is ordered by when YOU last looked rather than by when the file
 * changed. This section answers the different question — what do I have. */
export function OnDiskProjects({ onOpen, hideIds = [], refreshKey = 0 }: OnDiskProjectsProps) {
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    listProjects()
      .then((rows) => live && setProjects(rows))
      .catch(() => live && setError("Could not read the projects folder."));
    return () => {
      live = false;
    };
  }, [refreshKey]);

  if (error) return <p className="sigma-recent-list__empty">{error}</p>;
  if (projects === null) return <p className="sigma-recent-list__empty">Looking for projects…</p>;

  const hidden = new Set(hideIds);
  const rows = projects.filter((p) => !hidden.has(p.project_id));
  if (rows.length === 0) {
    return (
      <p className="sigma-recent-list__empty" data-testid="ondisk-empty">
        {projects.length === 0
          ? "No projects in your projects folder yet."
          : "Everything on this machine is already listed above."}
      </p>
    );
  }

  return (
    <ul className="sigma-recent-list" data-testid="ondisk-list">
      {rows.map((p) => (
        <li key={p.project_id} className="sigma-recent-list__row">
          <button
            type="button"
            className="sigma-recent-list__open"
            onClick={() => onOpen(p.project_id)}
            data-testid={`ondisk-project-${p.project_id}`}
          >
            <span className="sigma-recent-list__name">{p.name}</span>
            <span className="sigma-recent-list__path">
              {p.latest_phase} · {p.artifact_count} tool{p.artifact_count === 1 ? "" : "s"} saved
            </span>
          </button>
          <DeleteProjectButton
            projectId={p.project_id}
            name={p.name}
            artifactCount={p.artifact_count}
            onDeleted={() => setProjects((cur) => (cur ?? []).filter((row) => row.project_id !== p.project_id))}
          />
        </li>
      ))}
    </ul>
  );
}
