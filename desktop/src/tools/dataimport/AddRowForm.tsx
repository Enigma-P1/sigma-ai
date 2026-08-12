import { Button, Field, TextInput } from "../../design/components";
import type { ColumnInfo } from "../../api/types";

export interface AddRowFormProps {
  columns: ColumnInfo[];
  values: Record<string, string>;
  onChange: (column: string, value: string) => void;
  onApply: () => void;
  applying: boolean;
}

/** docs/uat/PLAN.md 1.2's third piece: one row, typed once, added to a new
 * dataset. Any column left blank saves as "" -- the same rule an ordinary
 * short row already gets on import (datasets.py's AddRowDerivation), not a
 * stricter one invented because this row arrived one field at a time. */
export function AddRowForm({ columns, values, onChange, onApply, applying }: AddRowFormProps) {
  return (
    <div className="sigma-dataimport__add-row" data-testid="dataimport-add-row-form">
      <p className="sigma-dataimport__mode-helper">
        Fill in as many columns as you know. Anything left blank is saved as blank. This creates a new dataset with
        one more row -- the one you are looking at now is not changed.
      </p>
      <div className="sigma-dataimport__add-row-grid">
        {columns.map((c) => (
          <Field key={c.name} label={c.name} htmlFor={`dataimport-add-row-${c.name}`}>
            <TextInput
              id={`dataimport-add-row-${c.name}`} data-testid={`dataimport-add-row-input-${c.name}`}
              value={values[c.name] ?? ""} onChange={(e) => onChange(c.name, e.target.value)}
            />
          </Field>
        ))}
      </div>
      <Button variant="primary" size="sm" disabled={applying} onClick={onApply} data-testid="dataimport-add-row-apply">
        {applying ? "Adding…" : "Add row → new dataset"}
      </Button>
    </div>
  );
}
