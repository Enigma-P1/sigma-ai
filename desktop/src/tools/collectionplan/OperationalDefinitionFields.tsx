import { Field, Panel, TextInput } from "../../design/components";
import type { OperationalDefinition } from "../../api/types";

export interface OperationalDefinitionFieldsProps {
  value: OperationalDefinition;
  onChange: (v: OperationalDefinition) => void;
}

/** Rubric R-MEA-05 #1's "two people" test, as fields -- the exact block
 * T-13's own operational-definition checkbox (BaselineForm) is confirming
 * against once this plan exists. */
export function OperationalDefinitionFields({ value, onChange }: OperationalDefinitionFieldsProps) {
  function set<K extends keyof OperationalDefinition>(key: K, v: OperationalDefinition[K]) {
    onChange({ ...value, [key]: v });
  }

  return (
    <Panel title="Operational definition" subtitle="Would two different people measuring this get the same number?">
      <Field label="What is measured" htmlFor="dcp-what-measured">
        <TextInput
          id="dcp-what-measured" data-testid="dcp-what-measured" value={value.what_measured}
          onChange={(e) => set("what_measured", e.target.value)}
          placeholder="Minutes from order placed to order handed to customer"
        />
      </Field>
      <Field label="How -- instrument or method" htmlFor="dcp-how-instrument">
        <TextInput
          id="dcp-how-instrument" data-testid="dcp-how-instrument" value={value.how_instrument}
          onChange={(e) => set("how_instrument", e.target.value)}
          placeholder="POS timestamp minus order timestamp, read from the register log"
        />
      </Field>
      <Field label="Precision / unit" htmlFor="dcp-precision-unit">
        <TextInput
          id="dcp-precision-unit" data-testid="dcp-precision-unit" value={value.precision_unit}
          onChange={(e) => set("precision_unit", e.target.value)}
          placeholder="minutes, to the nearest 0.1"
        />
      </Field>
      <div className="sigma-dcp-row">
        <Field label="Starts when" htmlFor="dcp-starts-when">
          <TextInput
            id="dcp-starts-when" data-testid="dcp-starts-when" value={value.starts_when}
            onChange={(e) => set("starts_when", e.target.value)}
            placeholder="Order is placed at the register"
          />
        </Field>
        <Field label="Stops when" htmlFor="dcp-stops-when">
          <TextInput
            id="dcp-stops-when" data-testid="dcp-stops-when" value={value.stops_when}
            onChange={(e) => set("stops_when", e.target.value)}
            placeholder="Drink is handed across the counter"
          />
        </Field>
      </div>
      <label className="sigma-dcp-checkbox">
        <input
          type="checkbox" data-testid="dcp-two-people-confirmed" checked={value.two_people_confirmed}
          onChange={(e) => set("two_people_confirmed", e.target.checked)}
        />
        Two different people measuring this the same way would get the same answer.
      </label>
    </Panel>
  );
}
