import { Field, Panel, TextInput, YesNoToggle } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import type { VocCustomer } from "../../api/types";
import { emptyCustomer } from "./vocCtqLogic";

export interface CustomersSectionProps {
  value: VocCustomer[];
  onChange: (v: VocCustomer[]) => void;
}

/** Who the customer even is, internal or external -- "everyone" is nobody
 * (rubric R-DEF-07). */
export function CustomersSection({ value, onChange }: CustomersSectionProps) {
  return (
    <Panel title="Customers" subtitle="Who this process actually serves -- named by role, internal or external.">
      <Field label="Customers" required helper="At least one, named by role.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={emptyCustomer}
          minItems={1}
          addLabel="+ Add customer"
          renderRow={(c, i, update) => (
            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-2)" }}>
              <TextInput data-testid={`voc-customer-${i}-role`} value={c.role} onChange={(e) => update({ ...c, role: e.target.value })} placeholder="external - end buyer" />
              <Field label="Internal?" htmlFor={`voc-customer-${i}-internal`}>
                <YesNoToggle name={`voc-customer-${i}-internal`} value={c.is_internal} onChange={(v) => update({ ...c, is_internal: v })} />
              </Field>
            </div>
          )}
        />
      </Field>
    </Panel>
  );
}
