import { Button, Field, TextArea, TextInput } from "../../design/components";
import type { SopStep } from "../../api/types";

export interface StepsEditorProps {
  steps: SopStep[];
  onChange: (stepId: string, patch: Partial<SopStep>) => void;
  onRemove: (stepId: string) => void;
  onAdd: () => void;
}

/** Each step: an action with its standard ("what right looks like"), and
 * a changed-from-prior toggle -- the points that changed from the old
 * method, highlighted (rubric R-CTL-06 #1). */
export function StepsEditor({ steps, onChange, onRemove, onAdd }: StepsEditorProps) {
  return (
    <div data-testid="standardwork-steps-editor">
      {steps.map((s, i) => (
        <div key={s.step_id} className="sigma-standardwork-step" data-testid={`standardwork-step-${s.step_id}`}>
          <div className="sigma-standardwork-step__order">{i + 1}</div>
          <Field label="Action" htmlFor={`sw-${s.step_id}-action`}>
            <TextInput id={`sw-${s.step_id}-action`} data-testid={`standardwork-step-${s.step_id}-action`} value={s.action} onChange={(e) => onChange(s.step_id, { action: e.target.value })} />
          </Field>
          <Field label="Standard (what right looks like)" htmlFor={`sw-${s.step_id}-standard`}>
            <TextArea id={`sw-${s.step_id}-standard`} data-testid={`standardwork-step-${s.step_id}-standard`} rows={2} value={s.standard} onChange={(e) => onChange(s.step_id, { standard: e.target.value })} />
          </Field>
          <label>
            <input type="checkbox" data-testid={`standardwork-step-${s.step_id}-changed`} checked={s.changed_from_prior} onChange={(e) => onChange(s.step_id, { changed_from_prior: e.target.checked })} />
            {" "}Changed from the prior method
          </label>
          {s.source_step_ref && <span className="sigma-standardwork-step__source">seeded from process-map step {s.source_step_ref}</span>}
          <Button variant="danger" size="sm" onClick={() => onRemove(s.step_id)}>Remove</Button>
        </div>
      ))}
      <Button variant="ghost" size="sm" onClick={onAdd} data-testid="standardwork-add-step">+ Add step</Button>
    </div>
  );
}
