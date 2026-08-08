import { Button, Field, SelectInput, TextInput } from "../../design/components";
import type { LayoutMode, Operator } from "../../api/types";
import type { DraftPoint } from "./spaghettiLogic";

export interface TraceControlsProps {
  operators: Operator[];
  tracing: boolean;
  draftPoints: DraftPoint[];
  activeLayoutMode: LayoutMode;
  operatorId: string;
  tripLabel: string;
  frequencyText: string;
  onOperatorChange: (id: string) => void;
  onTripLabelChange: (label: string) => void;
  onFrequencyChange: (text: string) => void;
  onStart: () => void;
  onUndo: () => void;
  onFinish: () => void;
  onCancel: () => void;
}

function canStart(operatorId: string, tripLabel: string, frequencyText: string): boolean {
  return operatorId !== "" && tripLabel.trim() !== "" && Number(frequencyText) > 0;
}

/** Trace mode: set who/what/how-often BEFORE clicking points (so every
 * point that lands has a route to belong to), then click the floor plan
 * to build the polyline; finishing commits it tagged with the active
 * layout_mode (current/proposed). */
export function TraceControls(props: TraceControlsProps) {
  const {
    operators, tracing, draftPoints, activeLayoutMode, operatorId, tripLabel, frequencyText,
    onOperatorChange, onTripLabelChange, onFrequencyChange, onStart, onUndo, onFinish, onCancel,
  } = props;

  return (
    <div className="sigma-spaghetti-trace">
      <div className="sigma-spaghetti-inspector-row">
        <Field label="Operator" htmlFor="spaghetti-trace-operator">
          <SelectInput id="spaghetti-trace-operator" data-testid="spaghetti-trace-operator" value={operatorId} disabled={tracing} onChange={(e) => onOperatorChange(e.target.value)}>
            <option value="">Select an operator…</option>
            {operators.map((o) => (
              <option key={o.operator_id} value={o.operator_id}>{o.name}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Trip label" htmlFor="spaghetti-trace-trip-label" helper="e.g. Register to grinder">
          <TextInput id="spaghetti-trace-trip-label" data-testid="spaghetti-trace-trip-label" value={tripLabel} disabled={tracing} onChange={(e) => onTripLabelChange(e.target.value)} />
        </Field>
        <Field label="Frequency (trips/day)" htmlFor="spaghetti-trace-frequency">
          <TextInput
            id="spaghetti-trace-frequency" type="number" min={0} data-testid="spaghetti-trace-frequency"
            value={frequencyText} disabled={tracing} onChange={(e) => onFrequencyChange(e.target.value)}
          />
        </Field>
      </div>

      {!tracing ? (
        <Button variant="secondary" disabled={!canStart(operatorId, tripLabel, frequencyText)} onClick={onStart} data-testid="spaghetti-trace-start">
          Trace a {activeLayoutMode} route
        </Button>
      ) : (
        <div className="sigma-spaghetti-trace-active">
          <p>Click the floor plan to add points ({draftPoints.length} placed). Finish needs at least 2.</p>
          <Button variant="ghost" size="sm" disabled={draftPoints.length === 0} onClick={onUndo} data-testid="spaghetti-trace-undo">
            Undo last point
          </Button>
          <Button variant="primary" size="sm" disabled={draftPoints.length < 2} onClick={onFinish} data-testid="spaghetti-trace-finish">
            Finish route
          </Button>
          <Button variant="ghost" size="sm" onClick={onCancel} data-testid="spaghetti-trace-cancel">
            Cancel
          </Button>
        </div>
      )}
    </div>
  );
}
