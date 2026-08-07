import type { ReactNode } from "react";
import { PhaseSection } from "./PhaseSection";
import { PHASES } from "./tools";
import type { CombinedGate } from "./gateLogic";
import type { Phase, ProjectMetadata } from "../api/types";
import "./DmaicRail.css";

export interface DmaicRailProps {
  project: ProjectMetadata;
  gatesByPhase: Partial<Record<Phase, CombinedGate>>;
  activePhase: Phase;
  activeToolId: string | null;
  onSelectTool: (phase: Phase, toolId: string) => void;
  footer?: ReactNode;
}

/** Left rail: the DMAIC spine (M1 brief) -- one PhaseSection per phase, in
 * order, each carrying its own gate badge and tool list. */
export function DmaicRail({ project, gatesByPhase, activePhase, activeToolId, onSelectTool, footer }: DmaicRailProps) {
  return (
    <nav className="sigma-rail" aria-label="DMAIC phases">
      <div className="sigma-rail__scroll">
        {PHASES.map((phase) => (
          <PhaseSection
            key={phase}
            phase={phase}
            gate={gatesByPhase[phase]}
            project={project}
            activePhase={activePhase}
            activeToolId={activeToolId}
            onSelectTool={onSelectTool}
          />
        ))}
      </div>
      {footer && <div className="sigma-rail__footer">{footer}</div>}
    </nav>
  );
}
