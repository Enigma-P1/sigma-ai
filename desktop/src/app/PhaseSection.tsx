import { StatusPill } from "../design/components";
import { labelForGateStatus, labelForToolStatus, toneForGateStatus, toneForToolStatus } from "./statusTone";
import type { ToolRailStatus } from "./statusTone";
import { toolsForPhase } from "./tools";
import { PHASE_BLURB } from "./phases";
import { getVisitedTools } from "./toolVisitedStore";
import type { CombinedGate } from "./gateLogic";
import type { Phase, ProjectMetadata } from "../api/types";
import "./PhaseSection.css";

export interface PhaseSectionProps {
  phase: Phase;
  gate: CombinedGate | undefined;
  project: ProjectMetadata;
  activeToolId: string | null;
  activePhase: Phase;
  onSelectTool: (phase: Phase, toolId: string) => void;
}

/** "Done" is either a saved artifact (project.artifact_index) or, for a
 * tool with no artifact of its own (T-14), a locally-marked visit
 * (toolVisitedStore.ts) -- the lightweight sibling signal for exactly
 * that case, read the same way for every tool in the rail. */
function toolStatus(toolId: string, live: boolean, project: ProjectMetadata, locked: boolean, visited: ReadonlySet<string>): ToolRailStatus {
  if (locked) return "blocked";
  const done = Object.values(project.artifact_index).some((e) => e.tool_id === toolId) || visited.has(toolId);
  if (done) return "done";
  return live ? "available" : "not-yet";
}

/** One phase's block in the DMAIC rail: name, gate badge, blurb, and its
 * tool list with per-tool status pills (M1 brief). */
export function PhaseSection({ phase, gate, project, activeToolId, activePhase, onSelectTool }: PhaseSectionProps) {
  const tools = toolsForPhase(phase);
  const locked = gate?.status === "HARD_BLOCK";
  const isActivePhase = phase === activePhase;
  const visitedTools = getVisitedTools(project.project_id);

  return (
    <div className={`sigma-phase ${isActivePhase ? "sigma-phase--active" : ""}`} data-testid={`phase-${phase}`}>
      <div className="sigma-phase__header">
        <span className="sigma-phase__name">{phase}</span>
        {gate && gate.status !== "CLEAR" && (
          <StatusPill
            tone={toneForGateStatus(gate.status)}
            label={labelForGateStatus(gate.status)}
            title={[gate.status, ...gate.reasons].join(" — ") || undefined}
          />
        )}
      </div>
      <p className="sigma-phase__blurb">{PHASE_BLURB[phase]}</p>
      <ul className="sigma-phase__tools">
        {tools.map((tool) => {
          const status = toolStatus(tool.id, tool.live, project, locked, visitedTools);
          const isActiveTool = activeToolId === tool.id;
          return (
            <li key={tool.id}>
              <button
                type="button"
                className={`sigma-phase__tool ${isActiveTool ? "sigma-phase__tool--active" : ""}`}
                onClick={() => onSelectTool(phase, tool.id)}
                data-testid={`nav-tool-${tool.id}`}
              >
                <span className="sigma-phase__tool-id">{tool.id}</span>
                <span className="sigma-phase__tool-name">{tool.name}</span>
                <StatusPill tone={toneForToolStatus(status)} label={labelForToolStatus(status)} dot={false} />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
