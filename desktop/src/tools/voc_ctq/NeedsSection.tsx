import { Field, Panel, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import type { CustomerNeed, VocStatement } from "../../api/types";

export interface NeedsSectionProps {
  value: CustomerNeed[];
  onChange: (v: CustomerNeed[]) => void;
  makeEmpty: () => CustomerNeed;
  statements: VocStatement[];
}

function toggleStatement(ids: string[], id: string): string[] {
  return ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
}

/** Customer needs, each linked to >=1 statement it came from -- the
 * statement -> need edge of the tree (rubric R-DEF-07). Checkboxes pick
 * from the statements already captured above, rather than free-typed IDs a
 * user could mistype into a dangling reference. */
export function NeedsSection({ value, onChange, makeEmpty, statements }: NeedsSectionProps) {
  return (
    <Panel title="Customer needs" subtitle="What the customer actually needs, traced back to real statements.">
      <Field label="Needs" required helper="Each need must trace back to at least one statement above.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={makeEmpty}
          minItems={1}
          addLabel="+ Add need"
          renderRow={(need, i, update) => (
            <>
              <TextInput data-testid={`voc-need-${i}-text`} value={need.text} onChange={(e) => update({ ...need, text: e.target.value })} placeholder="Parts must arrive intact" />
              <div data-testid={`voc-need-${i}-statements`} style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
                {statements.length === 0 && <p style={{ fontSize: "var(--text-xs)", color: "var(--color-text-faint)" }}>No statements captured yet.</p>}
                {statements.map((s) => (
                  <label key={s.statement_id} style={{ display: "flex", alignItems: "center", gap: "var(--space-1)", fontSize: "var(--text-xs)" }}>
                    <input
                      type="checkbox"
                      data-testid={`voc-need-${i}-statement-${s.statement_id}`}
                      checked={need.statement_ids.includes(s.statement_id)}
                      onChange={() => update({ ...need, statement_ids: toggleStatement(need.statement_ids, s.statement_id) })}
                    />
                    {s.statement_id}: {s.text.slice(0, 60) || "(empty)"}
                  </label>
                ))}
              </div>
            </>
          )}
        />
      </Field>
    </Panel>
  );
}
