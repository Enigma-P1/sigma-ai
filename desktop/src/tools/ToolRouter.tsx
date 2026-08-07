import { ToolScreen } from "./ToolScreen";
import { ToolPlaceholder } from "./ToolPlaceholder";
import { PickerForm } from "./picker/PickerForm";
import { pickerHelperContent } from "./picker/pickerContent";
import { CharterForm } from "./charter/CharterForm";
import { charterHelperContent } from "./charter/charterContent";
import { placeholderHelperContent } from "./helperFrameTypes";
import { toolById } from "../app/tools";
import type { CombinedGate } from "../app/gateLogic";
import type { Phase, ProjectMetadata } from "../api/types";

export interface ToolRouterProps {
  toolId: string;
  phase: Phase;
  projectId: string;
  project: ProjectMetadata;
  gate: CombinedGate | undefined;
  onGateOverridden: () => void;
  onSaved: () => void;
}

/** Dispatches the active tool id to its real form (T-01, T-03) or an
 * honest placeholder (everything else this milestone), always inside the
 * generic ToolScreen scaffold. */
export function ToolRouter({ toolId, phase, projectId, project, gate, onGateOverridden, onSaved }: ToolRouterProps) {
  const tool = toolById(toolId);
  if (!tool) return null;

  const screenProps = { toolId, toolName: tool.name, phase, projectId, gate, onGateOverridden };

  if (toolId === "T-01") {
    return (
      <ToolScreen {...screenProps} helperContent={pickerHelperContent}>
        <PickerForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-03") {
    return (
      <ToolScreen {...screenProps} helperContent={charterHelperContent}>
        <CharterForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  return (
    <ToolScreen {...screenProps} helperContent={placeholderHelperContent(toolId, tool.name)}>
      <ToolPlaceholder tool={tool} />
    </ToolScreen>
  );
}
