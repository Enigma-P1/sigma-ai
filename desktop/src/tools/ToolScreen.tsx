import type { ReactNode } from "react";
import { AdvisorPanel } from "../advisor/AdvisorPanel";
import { HelperFrame } from "./HelperFrame";
import type { HelperFrameContent } from "./helperFrameTypes";
import { GateBanner } from "../app/GateBanner";
import type { CombinedGate } from "../app/gateLogic";
import type { Phase } from "../api/types";
import "./ToolScreen.css";

export interface ToolScreenProps {
  toolId: string;
  toolName: string;
  phase: Phase;
  projectId: string;
  gate: CombinedGate | undefined;
  onGateOverridden: () => void;
  helperContent: HelperFrameContent;
  onOpenAdvisorSettings: () => void;
  children: ReactNode;
}

/** The generic tool screen scaffold every tool renders inside (M1 brief):
 * this phase's gate banner, the artifact form area (children), and the
 * five-part helper frame alongside it. Tool-specific forms never render
 * their own gate banner or helper frame -- they just supply `children`.
 *
 * M5 unit 1 adds the Advisor panel to the sidebar, above the helper frame
 * -- one shared, collapsible, Layer-2-optional panel every tool screen
 * gets for free, rather than 25 individual call sites each wiring one in. */
export function ToolScreen({
  toolId, toolName, phase, projectId, gate, onGateOverridden, helperContent, onOpenAdvisorSettings, children,
}: ToolScreenProps) {
  return (
    <div className="sigma-tool-screen" data-testid="tool-screen" data-tool-id={toolId}>
      <div className="sigma-tool-screen__header">
        <span className="sigma-tool-screen__tool-id">{toolId}</span>
        <h2 className="sigma-tool-screen__tool-name">{toolName}</h2>
      </div>

      {gate && <GateBanner phase={phase} projectId={projectId} gate={gate} onOverridden={onGateOverridden} />}

      <div className="sigma-tool-screen__body">
        <div className="sigma-tool-screen__main">{children}</div>
        <div className="sigma-tool-screen__sidebar">
          <AdvisorPanel projectId={projectId} onOpenSettings={onOpenAdvisorSettings} />
          <HelperFrame content={helperContent} />
        </div>
      </div>
    </div>
  );
}
