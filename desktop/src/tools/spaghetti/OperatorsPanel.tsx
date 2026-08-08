import { Button, Field, Panel, TextInput } from "../../design/components";
import type { Operator } from "../../api/types";
import { colorForOperator } from "./canvasColors";

export interface OperatorsPanelProps {
  operators: Operator[];
  onAdd: () => void;
  onUpdate: (operatorId: string, patch: Partial<Operator>) => void;
  onRemove: (operatorId: string) => void;
}

/** Operator add/rename controls -- color_index is assigned automatically
 * at creation (canvasColors.colorForOperator); the swatch here is just a
 * readback so a name can be matched to its route color on the canvas. */
export function OperatorsPanel({ operators, onAdd, onUpdate, onRemove }: OperatorsPanelProps) {
  return (
    <Panel title="Operators" subtitle="Who is being traced">
      <div className="sigma-spaghetti-operators">
        {operators.map((op, i) => (
          <div className="sigma-spaghetti-operator-row" key={op.operator_id}>
            <span className="sigma-spaghetti-operator-swatch" style={{ background: colorForOperator(op.color_index) }} aria-hidden="true" />
            <Field label="Name" htmlFor={`spaghetti-operator-${i}-name`}>
              <TextInput
                id={`spaghetti-operator-${i}-name`} data-testid={`spaghetti-operator-${i}-name`}
                value={op.name} onChange={(e) => onUpdate(op.operator_id, { name: e.target.value })}
              />
            </Field>
            <Button variant="ghost" size="sm" type="button" onClick={() => onRemove(op.operator_id)} data-testid={`spaghetti-operator-${i}-remove`}>
              Remove
            </Button>
          </div>
        ))}
      </div>
      <Button variant="ghost" size="sm" type="button" onClick={onAdd} data-testid="spaghetti-add-operator">
        + Add operator
      </Button>
    </Panel>
  );
}
