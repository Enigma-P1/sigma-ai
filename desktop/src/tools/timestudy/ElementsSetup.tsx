import { Button, Field, TextArea, TextInput } from "../../design/components";
import type { WorkElement } from "../../api/types";

export interface ElementsSetupProps {
  elements: WorkElement[];
  onAdd: () => void;
  onUpdate: (id: string, patch: Partial<WorkElement>) => void;
  onRemove: (id: string) => void;
}

/** T-09's required first step, rendered first on the screen so the order
 * is visible, not just enforced in the schema: work elements are defined
 * before any timing happens (PLAN §4.1 T-09 row). */
export function ElementsSetup({ elements, onAdd, onUpdate, onRemove }: ElementsSetupProps) {
  return (
    <div className="sigma-timestudy-elements">
      <div className="sigma-timestudy-elements__title">1. Work elements (define these before timing anything)</div>
      {elements.map((e, i) => (
        <div className="sigma-timestudy-elements__row" key={e.element_id}>
          <Field label={`Element ${i + 1} name`} htmlFor={`timestudy-element-${i}-name`}>
            <TextInput
              id={`timestudy-element-${i}-name`} data-testid={`timestudy-element-${i}-name`} value={e.name}
              onChange={(ev) => onUpdate(e.element_id, { name: ev.target.value })}
            />
          </Field>
          <Field label="Start/stop trigger (optional)" htmlFor={`timestudy-element-${i}-description`}>
            <TextArea
              id={`timestudy-element-${i}-description`} data-testid={`timestudy-element-${i}-description`} value={e.description} rows={1}
              onChange={(ev) => onUpdate(e.element_id, { description: ev.target.value })}
            />
          </Field>
          {elements.length > 1 && (
            <button type="button" className="sigma-timestudy-elements__remove" aria-label={`Remove ${e.name}`} onClick={() => onRemove(e.element_id)}>
              ×
            </button>
          )}
        </div>
      ))}
      <Button variant="ghost" size="sm" type="button" onClick={onAdd} data-testid="timestudy-add-element">
        + Add element
      </Button>
    </div>
  );
}
