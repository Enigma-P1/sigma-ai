import type { ReactNode } from "react";
import { AdvisorPanel } from "../advisor/AdvisorPanel";
import { HelperFrame } from "./HelperFrame";
import type { HelperFrameContent } from "./helperFrameTypes";
import { GateBanner } from "../app/GateBanner";
import type { CombinedGate } from "../app/gateLogic";
import type { Phase } from "../api/types";
import "./ToolScreen.css";

/** The data-first front door (docs/uat/PLAN.md decision 1, approved):
 * "keep the gate, but let 'import a file and chart it' be a front door that
 * does not pass through it." T-11 (import) and T-14 (charts) write no
 * project artifact and assert no methodology -- looking at a spreadsheet is
 * a legitimate first act, and greeting it with "Needs earlier steps (can
 * override)" is the gate charging a toll on the one path that owes it
 * nothing. The gate still stands everywhere it means something: every
 * artifact-writing tool, the tollgates, and the phase packs.
 *
 * The first shipped version of this decision was only a help-panel detour
 * (the Intake stuck-tree pointing at T-11) while these two screens still
 * wore the banner -- an external ship review called that out as the door
 * not actually existing, and it was right. */
const UNGATED_TOOL_IDS = new Set(["T-11", "T-14"]);

export interface ToolScreenProps {
  toolId: string;
  toolName: string;
  phase: Phase;
  projectId: string;
  gate: CombinedGate | undefined;
  onGateOverridden: () => void;
  helperContent: HelperFrameContent;
  onOpenAdvisorSettings: () => void;
  /** This tool's fixed saved-artifact id (app/tools.ts's ToolDef.artifactId),
   * undefined for the two tools with no saved artifact (T-13, T-14) -- see
   * that field's own docstring. Passed straight through to AdvisorPanel so
   * "review"/"help_me_think"/"explain" modes know which artifact is
   * "current" without re-deriving it (M5 unit 2). */
  artifactId?: string;
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
  toolId, toolName, phase, projectId, gate, onGateOverridden, helperContent, onOpenAdvisorSettings, artifactId, children,
}: ToolScreenProps) {
  return (
    <div className="sigma-tool-screen" data-testid="tool-screen" data-tool-id={toolId}>
      <div className="sigma-tool-screen__header">
        <span className="sigma-tool-screen__tool-id">{toolId}</span>
        <h2 className="sigma-tool-screen__tool-name">{toolName}</h2>
      </div>

      {gate && !UNGATED_TOOL_IDS.has(toolId) && (
        <GateBanner phase={phase} projectId={projectId} gate={gate} onOverridden={onGateOverridden} />
      )}

      <div className="sigma-tool-screen__body">
        <div className="sigma-tool-screen__main">{children}</div>
        <div className="sigma-tool-screen__sidebar">
          <AdvisorPanel projectId={projectId} toolId={toolId} artifactId={artifactId} onOpenSettings={onOpenAdvisorSettings} />
          <HelperFrame content={helperContent} />
        </div>
      </div>
    </div>
  );
}
