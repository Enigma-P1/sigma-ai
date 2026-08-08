import { Field, Panel, SelectInput, TextArea, TextInput, YesNoToggle } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { WasteChecklist } from "./WasteChecklist";
import { STEP_TYPE_LABELS } from "./processMapLogic";
import { STEP_TYPES } from "../../api/types";
import type { ProcessMapLane, ProcessMapStep, StepType } from "../../api/types";

export interface StepInspectorProps {
  step: ProcessMapStep;
  lanes: ProcessMapLane[];
  onChange: (patch: Partial<ProcessMapStep>) => void;
}

const REASON_REQUIRED: StepType[] = ["value_add", "non_value_add"];

/** The step inspector: every field a selected step carries (M2 brief) --
 * name, lane, type + reason, time, defect point, strata, and the 8-wastes
 * checklist. One panel, reused regardless of how the step was selected
 * (canvas click or the StepsList row). */
export function StepInspector({ step, lanes, onChange }: StepInspectorProps) {
  const reasonNeeded = REASON_REQUIRED.includes(step.step_type);
  return (
    <Panel title={`Inspector — ${step.name || "step"}`} subtitle={step.step_id}>
      <div className="sigma-processmap-inspector-row">
        <Field label="Step name" required htmlFor="processmap-step-name">
          <TextInput id="processmap-step-name" data-testid="processmap-step-name" value={step.name} onChange={(e) => onChange({ name: e.target.value })} />
        </Field>
        <Field label="Lane" htmlFor="processmap-step-lane">
          <SelectInput id="processmap-step-lane" data-testid="processmap-step-lane" value={step.lane_id} onChange={(e) => onChange({ lane_id: e.target.value })}>
            {lanes.map((l) => (
              <option key={l.lane_id} value={l.lane_id}>{l.name}</option>
            ))}
          </SelectInput>
        </Field>
      </div>

      <div className="sigma-processmap-inspector-row">
        <Field label="Type" htmlFor="processmap-step-type">
          <SelectInput id="processmap-step-type" data-testid="processmap-step-type" value={step.step_type} onChange={(e) => onChange({ step_type: e.target.value as StepType })}>
            {STEP_TYPES.map((t) => (
              <option key={t} value={t}>{STEP_TYPE_LABELS[t]}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Time (minutes)" htmlFor="processmap-step-time" helper="Leave blank if not timed yet.">
          <TextInput
            id="processmap-step-time" type="number" min={0} data-testid="processmap-step-time"
            value={step.time_minutes ?? ""}
            onChange={(e) => onChange({ time_minutes: e.target.value === "" ? null : Number(e.target.value) })}
          />
        </Field>
      </div>

      <Field
        label="Reason" required={reasonNeeded} htmlFor="processmap-step-reason"
        helper={reasonNeeded ? "Apply the value test honestly: would the customer pay for it, does it change the thing, done right the first time?" : "Optional for an enabling step."}
      >
        <TextArea id="processmap-step-reason" data-testid="processmap-step-reason" rows={2} value={step.reason} onChange={(e) => onChange({ reason: e.target.value })} />
      </Field>

      <Field label="Defect point" helper="Is this where defects are typically introduced or caught?">
        <YesNoToggle name="processmap-step-defect" value={step.defect_point} onChange={(v) => onChange({ defect_point: v })} />
      </Field>

      <Field label="Stratification factors" helper="Shift, machine, operator, day -- whatever this step's data should be sliced by later.">
        <DynamicList
          items={step.strata}
          onChange={(items) => onChange({ strata: items })}
          makeEmpty={() => ""}
          addLabel="+ Add stratification factor"
          renderRow={(item, i, update) => (
            <TextInput data-testid={`processmap-step-strata-${i}`} value={item} onChange={(e) => update(e.target.value)} placeholder="e.g. morning shift" />
          )}
        />
      </Field>

      <Field label="8-wastes walk">
        <WasteChecklist wastes={step.wastes} onChange={(wastes) => onChange({ wastes })} />
      </Field>
    </Panel>
  );
}
