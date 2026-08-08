import { Button, Field, Panel, TextInput } from "../../design/components";
import type { TrainingRow } from "../../api/types";

export interface TrainingRowsEditorProps {
  rows: TrainingRow[];
  onAdd: () => void;
  onChange: (rowId: string, patch: Partial<TrainingRow>) => void;
  onRemove: (rowId: string) => void;
}

/** A-5 / rubric R-CTL-04 #2: who, on what (the T-24 SOP), by whom, by
 * when, verified how, done -- "a fix nobody is trained on dies with the
 * project." */
export function TrainingRowsEditor({ rows, onAdd, onChange, onRemove }: TrainingRowsEditorProps) {
  return (
    <Panel title="Training & Handoff" subtitle="Who gets trained on the new method, by whom, verified how">
      {rows.map((r) => (
        <div key={r.row_id} className="sigma-controlplan-training-row" data-testid={`controlplan-training-${r.row_id}`}>
          <Field label="Who" htmlFor={`train-${r.row_id}-who`}><TextInput id={`train-${r.row_id}-who`} value={r.who} onChange={(e) => onChange(r.row_id, { who: e.target.value })} /></Field>
          <Field label="SOP reference (T-24 artifact id)" htmlFor={`train-${r.row_id}-sop`}><TextInput id={`train-${r.row_id}-sop`} value={r.sop_ref ?? ""} onChange={(e) => onChange(r.row_id, { sop_ref: e.target.value || null })} /></Field>
          <Field label="By whom" htmlFor={`train-${r.row_id}-bywhom`}><TextInput id={`train-${r.row_id}-bywhom`} value={r.by_whom} onChange={(e) => onChange(r.row_id, { by_whom: e.target.value })} /></Field>
          <Field label="By when" htmlFor={`train-${r.row_id}-byWhen`}><TextInput id={`train-${r.row_id}-byWhen`} type="date" value={(r.by_when ?? "").slice(0, 10)} onChange={(e) => onChange(r.row_id, { by_when: e.target.value || null })} /></Field>
          <Field label="Verified how" htmlFor={`train-${r.row_id}-verified`}><TextInput id={`train-${r.row_id}-verified`} value={r.verified_how} onChange={(e) => onChange(r.row_id, { verified_how: e.target.value })} /></Field>
          <label>
            <input type="checkbox" checked={r.done} onChange={(e) => onChange(r.row_id, { done: e.target.checked })} /> Done
          </label>
          <Button variant="danger" size="sm" onClick={() => onRemove(r.row_id)}>Remove</Button>
        </div>
      ))}
      <Button variant="ghost" size="sm" onClick={onAdd} data-testid="controlplan-add-training">+ Add training row</Button>
    </Panel>
  );
}
