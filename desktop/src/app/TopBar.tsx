import { useSaveState } from "./SaveStateContext";
import type { Phase } from "../api/types";
import "./TopBar.css";

export interface TopBarProps {
  projectName: string;
  phase: Phase;
  onGoHome: () => void;
  onOpenDiagnostics: () => void;
  onOpenAdvisorSettings: () => void;
}

const SAVE_LABEL: Record<string, string> = {
  idle: "No changes yet",
  saving: "Saving…",
  saved: "Saved",
  error: "Save failed",
};

/** Top bar: project name + phase + save state (M1 brief). Save state comes
 * from SaveStateContext so any tool screen can update it without prop
 * drilling through the whole shell. */
export function TopBar({ projectName, phase, onGoHome, onOpenDiagnostics, onOpenAdvisorSettings }: TopBarProps) {
  const { saveState } = useSaveState();

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
