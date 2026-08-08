import { useCallback, useEffect, useState } from "react";
import { TopBar } from "./TopBar";
import { DmaicRail } from "./DmaicRail";
import { StuckButton } from "./StuckButton";
import { SaveStateProvider } from "./SaveStateContext";
import { useGateStatuses } from "./useGateStatuses";
import { toolById } from "./tools";
import { openProject } from "../api/client";
import { ApiError } from "../api/errors";
import { ToolRouter } from "../tools/ToolRouter";
import type { DatasetPreset } from "../tools/ToolRouter";
import type { Phase, ProjectMetadata } from "../api/types";
import "./ProjectWorkspace.css";

export interface ProjectWorkspaceProps {
  projectId: string;
  onGoHome: () => void;
  onOpenDiagnostics: () => void;
  onOpenAdvisorSettings: () => void;
}

/** The open-project shell: top bar + DMAIC rail + active tool (M1 brief).
 * Owns the project metadata, the active phase/tool selection, and the
 * refresh key that both the project metadata and the gate-status hook key
 * off of after every artifact save. */
export function ProjectWorkspace({ projectId, onGoHome, onOpenDiagnostics, onOpenAdvisorSettings }: ProjectWorkspaceProps) {
  const [project, setProject] = useState<ProjectMetadata | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activePhase, setActivePhase] = useState<Phase>("Intake");
  const [activeToolId, setActiveToolId] = useState<string | null>("T-01");
  const [refreshKey, setRefreshKey] = useState(0);
  const [presetDataset, setPresetDataset] = useState<DatasetPreset | null>(null);

  const refresh = useCallback(() => {
    openProject(projectId)
      .then((meta) => {
        setProject(meta);
        setLoadError(null);
      })
      .catch((err: unknown) => {
        setLoadError(err instanceof ApiError ? err.message : "Could not load this project.");
      });
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const { byPhase } = useGateStatuses(projectId, refreshKey);

  function handleSaved() {
    setRefreshKey((k) => k + 1);
    refresh();
  }

  function handleSelectTool(phase: Phase, toolId: string) {
    setActivePhase(phase);
    setActiveToolId(toolId);
    setPresetDataset(null); // a normal rail navigation always clears any stale deep-link preset
  }

  function handleStuckNavigate(toolId: string) {
    const tool = toolById(toolId);
    if (tool) handleSelectTool(tool.phase, toolId);
  }

  /** T-08/T-09's "send to Pareto/baseline" deep link: jump straight to the
   * target tool with the freshly-exported dataset preselected (M2 brief:
   * "a simple navigation param") -- unlike handleSelectTool, this is the
   * one path that's allowed to set presetDataset. */
  function handleNavigateToDataset(toolId: string, datasetId: string) {
    const tool = toolById(toolId);
    if (!tool) return;
    setActivePhase(tool.phase);
    setActiveToolId(toolId);
    setPresetDataset({ toolId, datasetId });
  }

  if (loadError) {
    return (
      <div className="sigma-workspace__error">
        <p>{loadError}</p>
        <button type="button" onClick={onGoHome}>
          Back to projects
        </button>
      </div>
    );
  }

  if (!project) {
    return <div className="sigma-workspace__loading">Loading project…</div>;
  }

  return (
    <SaveStateProvider>
      <div className="sigma-workspace">
        <TopBar
          projectName={project.name}
          phase={activePhase}
          onGoHome={onGoHome}
          onOpenDiagnostics={onOpenDiagnostics}
          onOpenAdvisorSettings={onOpenAdvisorSettings}
        />
        <div className="sigma-workspace__body">
          <DmaicRail
            project={project}
            gatesByPhase={byPhase}
            activePhase={activePhase}
            activeToolId={activeToolId}
            onSelectTool={handleSelectTool}
            footer={<StuckButton phase={activePhase} project={project} onNavigateToTool={handleStuckNavigate} />}
          />
          <main className="sigma-workspace__main">
            {activeToolId ? (
              <ToolRouter
                toolId={activeToolId}
                phase={activePhase}
                projectId={projectId}
                project={project}
                gate={byPhase[activePhase]}
                onGateOverridden={() => setRefreshKey((k) => k + 1)}
                onSaved={handleSaved}
                presetDataset={presetDataset}
                onNavigateToDataset={handleNavigateToDataset}
                onOpenAdvisorSettings={onOpenAdvisorSettings}
              />
            ) : (
              <p className="sigma-workspace__empty">Pick a tool from the rail to get started.</p>
            )}
          </main>
        </div>
      </div>
    </SaveStateProvider>
  );
}
