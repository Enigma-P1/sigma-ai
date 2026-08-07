import { Field, Panel, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import type { OutputCustomerPair } from "../../api/types";
import { emptyOutputCustomerPair } from "./sipocLogic";

export interface OutputCustomerSectionProps {
  value: OutputCustomerPair[];
  onChange: (v: OutputCustomerPair[]) => void;
}

/** Output <-> Customer columns, one row per pair -- the CTQ-bearing output
 * needs to be paired to the customer who actually receives it (rubric
 * R-DEF-06), not left in a free-floating list. */
export function OutputCustomerSection({ value, onChange }: OutputCustomerSectionProps) {
  return (
    <Panel title="Outputs and Customers" subtitle="What the process produces, and who actually receives it.">
      <Field label="Output -> Customer pairs" required helper="Name the real receiving customer, not just the next internal step.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={emptyOutputCustomerPair}
          minItems={1}
          addLabel="+ Add output/customer pair"
          renderRow={(pair, i, update) => (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
              <TextInput data-testid={`sipoc-output-${i}`} value={pair.output} onChange={(e) => update({ ...pair, output: e.target.value })} placeholder="Molded part" />
              <TextInput data-testid={`sipoc-customer-${i}`} value={pair.customer} onChange={(e) => update({ ...pair, customer: e.target.value })} placeholder="Assembly line" />
            </div>
          )}
        />
      </Field>
    </Panel>
  );
}
