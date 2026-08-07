import { Field, Panel, SelectInput, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { VOC_STATEMENT_SOURCES } from "../../api/types";
import type { VocStatement, VocStatementSource } from "../../api/types";
import { STATEMENT_SOURCE_LABELS } from "./vocCtqLogic";

export interface StatementsSectionProps {
  value: VocStatement[];
  onChange: (v: VocStatement[]) => void;
  makeEmpty: () => VocStatement;
}

/** Customer statements, captured close to verbatim with a named source
 * (rubric R-DEF-07: statements arriving pre-digested into needs, with no
 * verbatim to audit, is a Needs-work finding). */
export function StatementsSection({ value, onChange, makeEmpty }: StatementsSectionProps) {
  return (
    <Panel title="Voice of the Customer" subtitle="What customers actually said, close to verbatim.">
      <Field label="Statements" required helper="One row per real thing a customer said -- not pre-summarized.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={makeEmpty}
          minItems={1}
          addLabel="+ Add statement"
          renderRow={(s, i, update) => (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
                <TextInput data-testid={`voc-statement-${i}-role`} value={s.customer_role} onChange={(e) => update({ ...s, customer_role: e.target.value })} placeholder="Customer role (from above)" />
                <SelectInput data-testid={`voc-statement-${i}-source`} value={s.source} onChange={(e) => update({ ...s, source: e.target.value as VocStatementSource })}>
                  {VOC_STATEMENT_SOURCES.map((src) => (
                    <option key={src} value={src}>
                      {STATEMENT_SOURCE_LABELS[src]}
                    </option>
                  ))}
                </SelectInput>
              </div>
              <TextInput data-testid={`voc-statement-${i}-text`} value={s.text} onChange={(e) => update({ ...s, text: e.target.value })} placeholder="Parts sometimes arrive cracked." />
              <TextInput data-testid={`voc-statement-${i}-detail`} value={s.source_detail} onChange={(e) => update({ ...s, source_detail: e.target.value })} placeholder="Source detail, e.g. 2026 Q2 complaint log" />
            </>
          )}
        />
      </Field>
    </Panel>
  );
}
