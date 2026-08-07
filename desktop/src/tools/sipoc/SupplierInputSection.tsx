import { Field, Panel, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import type { SupplierInputPair } from "../../api/types";
import { emptySupplierInputPair } from "./sipocLogic";

export interface SupplierInputSectionProps {
  value: SupplierInputPair[];
  onChange: (v: SupplierInputPair[]) => void;
}

/** Supplier <-> Input columns, one row per pair -- enforced by construction
 * (each row IS the pairing), not by convention (PLAN §4.1). */
export function SupplierInputSection({ value, onChange }: SupplierInputSectionProps) {
  return (
    <Panel title="Suppliers and Inputs" subtitle="Who supplies what goes into the process.">
      <Field label="Supplier -> Input pairs" required helper="One row per pair -- a supplier with no input, or vice versa, isn't allowed.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={emptySupplierInputPair}
          minItems={1}
          addLabel="+ Add supplier/input pair"
          renderRow={(pair, i, update) => (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
              <TextInput data-testid={`sipoc-supplier-${i}`} value={pair.supplier} onChange={(e) => update({ ...pair, supplier: e.target.value })} placeholder="Resin vendor" />
              <TextInput data-testid={`sipoc-input-${i}`} value={pair.input} onChange={(e) => update({ ...pair, input: e.target.value })} placeholder="Raw resin pellets" />
            </div>
          )}
        />
      </Field>
    </Panel>
  );
}
