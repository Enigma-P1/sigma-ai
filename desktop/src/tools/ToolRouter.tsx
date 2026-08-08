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
import { dataImportHelperContent } from "./dataimport/dataImportContent";
import { T11Screen } from "./T11Screen";
import { MsaForm } from "./msa/MsaForm";
import { msaHelperContent } from "./msa/msaContent";
import { ProcessMapForm } from "./processmap/ProcessMapForm";
import { processMapHelperContent } from "./processmap/processMapContent";
import { SpaghettiForm } from "./spaghetti/SpaghettiForm";
import { spaghettiHelperContent } from "./spaghetti/spaghettiContent";
import { CheckSheetForm } from "./checksheet/CheckSheetForm";
import { checkSheetHelperContent } from "./checksheet/checkSheetContent";
import { TimeStudyForm } from "./timestudy/TimeStudyForm";
import { timeStudyHelperContent } from "./timestudy/timeStudyContent";
import { BaselineForm } from "./baseline/BaselineForm";
import { baselineHelperContent } from "./baseline/baselineContent";
import { ChartSetScreen } from "./chartset/ChartSetScreen";
import { chartSetHelperContent } from "./chartset/chartSetContent";
import { HypothesisForm } from "./hypothesis/HypothesisForm";
import { hypothesisHelperContent } from "./hypothesis/hypothesisContent";
import { FishboneForm } from "./fishbone/FishboneForm";
import { fishboneHelperContent } from "./fishbone/fishboneContent";
import { FmeaForm } from "./fmea/FmeaForm";
import { fmeaHelperContent } from "./fmea/fmeaContent";
import { SolutionMatrixForm } from "./solutionmatrix/SolutionMatrixForm";
import { solutionMatrixHelperContent } from "./solutionmatrix/solutionMatrixContent";
import { PilotPlanForm } from "./pilotplan/PilotPlanForm";
import { pilotPlanHelperContent } from "./pilotplan/pilotPlanContent";
import { ProofForm } from "./proof/ProofForm";
import { proofHelperContent } from "./proof/proofContent";
import { ControlChartForm } from "./controlchart/ControlChartForm";
import { controlChartHelperContent } from "./controlchart/controlChartContent";
import { ControlPlanForm } from "./controlplan/ControlPlanForm";
import { controlPlanHelperContent } from "./controlplan/controlPlanContent";
import { FiveSForm } from "./fives/FiveSForm";
import { fiveSHelperContent } from "./fives/fiveSContent";
import { StandardWorkForm } from "./standardwork/StandardWorkForm";
import { standardWorkHelperContent } from "./standardwork/standardWorkContent";
import { A3Form } from "./a3/A3Form";
import { a3HelperContent } from "./a3/a3Content";
import { placeholderHelperContent } from "./helperFrameTypes";
import { toolById } from "../app/tools";
import type { CombinedGate } from "../app/gateLogic";
import type { Phase, ProjectMetadata } from "../api/types";

/** Deep-link param (M2 brief: "a simple navigation param"): set by
 * CheckSheetForm/TimeStudyForm's "send to Pareto/baseline" once a
 * to_dataset export succeeds, consumed by ChartSetScreen/BaselineForm to
 * preselect that dataset -- ProjectWorkspace owns the state, clears it
 * whenever the rail is used to navigate normally. */
export interface DatasetPreset {
  toolId: string;
  datasetId: string;
}

export interface ToolRouterProps {
  toolId: string;
  phase: Phase;
  projectId: string;
  project: ProjectMetadata;
  gate: CombinedGate | undefined;
  onGateOverridden: () => void;
  onSaved: () => void;
  presetDataset?: DatasetPreset | null;
  onNavigateToDataset?: (toolId: string, datasetId: string) => void;
}

/** Dispatches the active tool id to its real form (T-01..T-05, the whole
 * Intake+Define set this milestone completes) or an honest placeholder
 * (everything else), always inside the generic ToolScreen scaffold. */
export function ToolRouter({ toolId, phase, projectId, project, gate, onGateOverridden, onSaved, presetDataset, onNavigateToDataset }: ToolRouterProps) {
  const tool = toolById(toolId);
  if (!tool) return null;
  const presetFor = (id: string) => (presetDataset?.toolId === id ? presetDataset.datasetId : undefined);

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

  // T-06..T-14 (M2): real engine-backed forms with the real M2 helper
  // content (the Measure content unit) -- each panel's checklist restates
  // its rubric items, per tier-a-done-means §2.
  if (toolId === "T-06") {
    return (
      <ToolScreen {...screenProps} helperContent={processMapHelperContent}>
        <ProcessMapForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-07") {
    return (
      <ToolScreen {...screenProps} helperContent={spaghettiHelperContent}>
        <SpaghettiForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-08") {
    return (
      <ToolScreen {...screenProps} helperContent={checkSheetHelperContent}>
        <CheckSheetForm projectId={projectId} project={project} onSaved={onSaved} onNavigateToDataset={onNavigateToDataset} />
      </ToolScreen>
    );
  }

  if (toolId === "T-09") {
    return (
      <ToolScreen {...screenProps} helperContent={timeStudyHelperContent}>
        <TimeStudyForm projectId={projectId} project={project} onSaved={onSaved} onNavigateToDataset={onNavigateToDataset} />
      </ToolScreen>
    );
  }

  if (toolId === "T-11") {
    return (
      <ToolScreen {...screenProps} helperContent={dataImportHelperContent}>
        <T11Screen projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-12") {
    return (
      <ToolScreen {...screenProps} helperContent={msaHelperContent}>
        <MsaForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-13") {
    return (
      <ToolScreen {...screenProps} helperContent={baselineHelperContent}>
        <BaselineForm projectId={projectId} project={project} initialDatasetId={presetFor("T-13")} />
      </ToolScreen>
    );
  }

  if (toolId === "T-14") {
    return (
      <ToolScreen {...screenProps} helperContent={chartSetHelperContent}>
        <ChartSetScreen projectId={projectId} initialDatasetId={presetFor("T-14")} onVisited={onSaved} />
      </ToolScreen>
    );
  }

  // T-15/T-16/T-17 (M3): the Analyze-phase screens with the real Analyze
  // five-part content unit (PLAN §4.3) -- each panel's checklist restates
  // its rubric items, per tier-a-done-means §2.
  if (toolId === "T-15") {
    return (
      <ToolScreen {...screenProps} helperContent={fishboneHelperContent}>
        <FishboneForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-16") {
    return (
      <ToolScreen {...screenProps} helperContent={fmeaHelperContent}>
        <FmeaForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-17") {
    return (
      <ToolScreen {...screenProps} helperContent={hypothesisHelperContent}>
        <HypothesisForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  // T-18..T-25 (M4): real engine-backed forms with the real
  // Improve/Control/Wrap five-part content units (PLAN §4.3) -- each
  // panel's checklist restates its rubric items, per tier-a-done-means §2.
  if (toolId === "T-18") {
    return (
      <ToolScreen {...screenProps} helperContent={solutionMatrixHelperContent}>
        <SolutionMatrixForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-19") {
    return (
      <ToolScreen {...screenProps} helperContent={pilotPlanHelperContent}>
        <PilotPlanForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-20") {
    return (
      <ToolScreen {...screenProps} helperContent={proofHelperContent}>
        <ProofForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-21") {
    return (
      <ToolScreen {...screenProps} helperContent={controlChartHelperContent}>
        <ControlChartForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-22") {
    return (
      <ToolScreen {...screenProps} helperContent={controlPlanHelperContent}>
        <ControlPlanForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-23") {
    return (
      <ToolScreen {...screenProps} helperContent={fiveSHelperContent}>
        <FiveSForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-24") {
    return (
      <ToolScreen {...screenProps} helperContent={standardWorkHelperContent}>
        <StandardWorkForm projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  if (toolId === "T-25") {
    return (
      <ToolScreen {...screenProps} helperContent={a3HelperContent}>
        <A3Form projectId={projectId} project={project} onSaved={onSaved} />
      </ToolScreen>
    );
  }

  return (
    <ToolScreen {...screenProps} helperContent={placeholderHelperContent(toolId, tool.name)}>
      <ToolPlaceholder tool={tool} />
    </ToolScreen>
  );
}
