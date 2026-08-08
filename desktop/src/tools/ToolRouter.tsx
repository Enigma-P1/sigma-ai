import { ToolScreen } from "./ToolScreen";
import { ToolPlaceholder } from "./ToolPlaceholder";
import { PickerForm } from "./picker/PickerForm";
import { pickerHelperContent } from "./picker/pickerContent";
import { CopqForm } from "./copq/CopqForm";
import { copqHelperContent } from "./copq/copqContent";
import { CharterForm } from "./charter/CharterForm";
import { charterHelperContent } from "./charter/charterContent";
import { SipocForm } from "./sipoc/SipocForm";
import { sipocHelperContent } from "./sipoc/sipocContent";
import { VocCtqForm } from "./voc_ctq/VocCtqForm";
import { vocCtqHelperContent } from "./voc_ctq/vocCtqContent";
import { DataImportForm } from "./dataimport/DataImportForm";
import { SampleSizePanel } from "./samplesize/SampleSizePanel";
import { MsaForm } from "./msa/MsaForm";
import { BaselineForm } from "./baseline/BaselineForm";
import { ChartSetScreen } from "./chartset/ChartSetScreen";
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

/** Dispatches the active tool id to its real form (T-01..T-05, the whole
 * Intake+Define set this milestone completes) or an honest placeholder
 * (everything else), always inside the generic ToolScreen scaffold. */
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

  if (toolId === "T-02") {
    return (
      <ToolScreen {...screenProps} helperContent={copqHelperContent}>
        <CopqForm projectId={projectId} project={project} onSaved={onSaved} />
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

  if (toolId === "T-04") {
    return (
      <ToolScreen {...screenProps} helperContent={sipocHelperContent}>
        <SipocForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-05") {
    return (
      <ToolScreen {...screenProps} helperContent={vocCtqHelperContent}>
        <VocCtqForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  // T-11/T-12/T-13/T-14 (M2): real engine-backed forms, but helper-frame
  // content stays PLACEHOLDER this milestone -- a content unit follows,
  // same as every not-yet-content-written tool.
  if (toolId === "T-11") {
    return (
      <ToolScreen {...screenProps} helperContent={placeholderHelperContent(tool.id, tool.name)}>
        <DataImportForm projectId={projectId} onSaved={onSaved} />
        <SampleSizePanel />
      </ToolScreen>
    );
  }

  if (toolId === "T-12") {
    return (
      <ToolScreen {...screenProps} helperContent={placeholderHelperContent(tool.id, tool.name)}>
        <MsaForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-13") {
    return (
      <ToolScreen {...screenProps} helperContent={placeholderHelperContent(tool.id, tool.name)}>
        <BaselineForm projectId={projectId} />
      </ToolScreen>
    );
  }

  if (toolId === "T-14") {
    return (
      <ToolScreen {...screenProps} helperContent={placeholderHelperContent(tool.id, tool.name)}>
        <ChartSetScreen projectId={projectId} />
      </ToolScreen>
    );
  }

  return (
    <ToolScreen {...screenProps} helperContent={placeholderHelperContent(toolId, tool.name)}>
      <ToolPlaceholder tool={tool} />
    </ToolScreen>
  );
}
