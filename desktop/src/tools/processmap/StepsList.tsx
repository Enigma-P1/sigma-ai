import { Button, Panel, StatusPill } from "../../design/components";
import type { PillTone } from "../../design/components";
import type { ProcessMapLane, ProcessMapStep, StepType } from "../../api/types";
import { STEP_TYPE_LABELS } from "./processMapLogic";

export interface StepsListProps {
  lanes: ProcessMapLane[];
  steps: ProcessMapStep[];
  selectedStepId: string | null;
  onSelect: (stepId: string) => void;
  onAdd: (laneId: string) => void;
  onRemove: (stepId: string) => void;
}

const TONE_FOR_TYPE: Record<StepType, PillTone> = { value_add: "pass", non_value_add: "fail", enabling: "accent" };

/** Non-canvas step overview, one section per lane: a selectable row per
 * step (drives the inspector below) plus an "+ Add step" button per lane.
 * Deliberately plain HTML -- Konva nodes are canvas-drawn and can't carry
 * DOM test ids, so this is the reliable control surface for adding/
 * selecting steps (the canvas itself supports click-to-select + drag too). */
export function StepsList({ lanes, steps, selectedStepId, onSelect, onAdd, onRemove }: StepsListProps) {
  return (
    <Panel title="Steps" subtitle="Select a step to edit it in the inspector">
      {lanes.map((lane, laneIndex) => (
        <div key={lane.lane_id} className="sigma-processmap-steps-lane">
          <div className="sigma-processmap-steps-lane__name">{lane.name}</div>
          <ul className="sigma-processmap-steps-list">
            {steps
              .filter((s) => s.lane_id === lane.lane_id)
              .sort((a, b) => a.order - b.order)
              .map((step) => (
                <li key={step.step_id}>
                  <button
                    type="button"
                    data-testid={`processmap-step-row-${step.step_id}`}
                    className={`sigma-processmap-step-row ${step.step_id === selectedStepId ? "sigma-processmap-step-row--selected" : ""}`}
                    onClick={() => onSelect(step.step_id)}
                  >
                    <StatusPill tone={TONE_FOR_TYPE[step.step_type]} label={STEP_TYPE_LABELS[step.step_type]} />
                    <span>{step.name}</span>
                  </button>
                  <button type="button" className="sigma-processmap-step-remove" aria-label={`Remove ${step.name}`} onClick={() => onRemove(step.step_id)}>
                    ×
                  </button>
                </li>
              ))}
          </ul>
          <Button variant="ghost" size="sm" type="button" onClick={() => onAdd(lane.lane_id)} data-testid={`processmap-add-step-${laneIndex}`}>
            + Add step
          </Button>
        </div>
      ))}
    </Panel>
  );
}
