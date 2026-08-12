import { useState } from "react";
import { useSaveState } from "./SaveStateContext";
import { downloadProjectPdf } from "../api/client";
import { ApiError } from "../api/errors";
import { safeFilename, saveBlob } from "../api/saveBlob";
import type { Phase } from "../api/types";
import "./TopBar.css";

export interface TopBarProps {
  projectName: string;
  projectId: string;
  phase: Phase;
  onGoHome: () => void;
  onOpenDiagnostics: () => void;
  onOpenAdvisorSettings: () => void;
}

const SAVE_LABEL: Record<string, string> = {
  // "No changes yet" was a claim this state cannot make: `idle` only means
  // no save has been attempted, and nothing reports edits up to here -- so
  // the bar sat on "No changes yet" while a user typed a charter, and then
  // the text was gone. Say what idle actually knows.
  idle: "Nothing saved yet",
  saving: "Saving…",
  saved: "Saved",
  error: "Save failed",
};

/** Top bar: project name + phase + save state (M1 brief). Save state comes
 * from SaveStateContext so any tool screen can update it without prop
 * drilling through the whole shell. */
export function TopBar({ projectName, projectId, phase, onGoHome, onOpenDiagnostics, onOpenAdvisorSettings }: TopBarProps) {
  const { saveState } = useSaveState();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  /** The whole project as one PDF. Lives in the top bar rather than on a
   * tool screen because it is not about any one tool -- and because the
   * question it answers ("I did the work, where is it?") is asked from
   * wherever the user happens to be standing. */
  async function handleExportProject() {
    setExporting(true);
    setExportError(null);
    try {
      const blob = await downloadProjectPdf(projectId);
      saveBlob(blob, `${safeFilename(projectName, projectId)}-project-record.pdf`);
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Could not export the project.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <header className="sigma-topbar">
      <div className="sigma-topbar__identity">
        <button type="button" className="sigma-topbar__link" onClick={onGoHome} data-testid="topbar-home">
          ← Projects
        </button>
        <span className="sigma-topbar__project" data-testid="topbar-project-name">
          {projectName}
        </span>
        <span className="sigma-topbar__phase" data-testid="topbar-phase">
          {phase}
        </span>
      </div>
      <div className="sigma-topbar__right">
        <span className={`sigma-topbar__save-state sigma-topbar__save-state--${saveState}`} data-testid="topbar-save-state">
          {SAVE_LABEL[saveState]}
        </span>
        <button
          type="button"
          className="sigma-topbar__link"
          disabled={exporting}
          title={exportError ?? "Download every saved tool as one PDF"}
          onClick={() => void handleExportProject()}
          data-testid="topbar-export-project"
        >
          {exporting ? "Exporting…" : "Export project"}
        </button>
        {exportError && (
          <span className="sigma-topbar__export-error" role="alert" data-testid="topbar-export-error">
            {exportError}
          </span>
        )}
        <button
          type="button"
          className="sigma-topbar__link"
          onClick={onOpenAdvisorSettings}
          data-testid="topbar-advisor-settings"
        >
          Advisor settings
        </button>
        <button type="button" className="sigma-topbar__link" onClick={onOpenDiagnostics} data-testid="topbar-diagnostics">
          Diagnostics
        </button>
      </div>
    </header>
  );
}
