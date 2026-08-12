import { Button, Field, SelectInput, TextInput } from "../../design/components";
import { DERIVE_COLUMN_DEFAULT_SEPARATOR } from "../../api/types";
import type { ColumnInfo } from "../../api/types";

export interface DeriveColumnFormProps {
  columns: ColumnInfo[];
  newColumnName: string;
  onNewColumnNameChange: (v: string) => void;
  leftColumn: string;
  onLeftColumnChange: (v: string) => void;
  rightColumn: string;
  onRightColumnChange: (v: string) => void;
  separator: string;
  onSeparatorChange: (v: string) => void;
  onApply: () => void;
  applying: boolean;
}

/** docs/uat/PLAN.md 1.4: join two columns into one new column, the general
 * answer to "group by two things" -- Dave's "Item ordered" and "Item
 * shipped" on the same row with no way to pair them for a Pareto
 * (docs/uat/README.md). */
export function DeriveColumnForm({
  columns, newColumnName, onNewColumnNameChange, leftColumn, onLeftColumnChange,
  rightColumn, onRightColumnChange, separator, onSeparatorChange, onApply, applying,
}: DeriveColumnFormProps) {
  const canApply = newColumnName.trim() !== "" && leftColumn !== "" && rightColumn !== "" && !applying;

  return (
    <div className="sigma-dataimport__derive-column" data-testid="dataimport-derive-column-form">
      <p className="sigma-dataimport__mode-helper">
        Combine two columns into one new one -- e.g. "Item ordered" and "Item shipped" into a single value a Pareto
        can group on. This creates a new dataset with the extra column -- the one you are looking at now is not
        changed.
      </p>
      <div className="sigma-dataimport__derive-column-grid">
        <Field label="New column name" htmlFor="dataimport-derive-column-name">
          <TextInput
            id="dataimport-derive-column-name" data-testid="dataimport-derive-column-name" value={newColumnName}
            onChange={(e) => onNewColumnNameChange(e.target.value)} placeholder="e.g. item_pair"
          />
        </Field>
        <Field label="First column" htmlFor="dataimport-derive-column-left">
          <SelectInput
            id="dataimport-derive-column-left" data-testid="dataimport-derive-column-left" value={leftColumn}
            onChange={(e) => onLeftColumnChange(e.target.value)}
          >
            <option value="">Select a column…</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </SelectInput>
        </Field>
        <Field
          label="Separator" htmlFor="dataimport-derive-column-separator"
          helper={`Default "${DERIVE_COLUMN_DEFAULT_SEPARATOR}" -- e.g. "Ketchup 4 oz${DERIVE_COLUMN_DEFAULT_SEPARATOR}Ketchup 6 oz".`}
        >
          <TextInput
            id="dataimport-derive-column-separator" data-testid="dataimport-derive-column-separator" value={separator}
            onChange={(e) => onSeparatorChange(e.target.value)}
          />
        </Field>
        <Field label="Second column" htmlFor="dataimport-derive-column-right">
          <SelectInput
            id="dataimport-derive-column-right" data-testid="dataimport-derive-column-right" value={rightColumn}
            onChange={(e) => onRightColumnChange(e.target.value)}
          >
            <option value="">Select a column…</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </SelectInput>
        </Field>
      </div>
      <Button variant="primary" size="sm" disabled={!canApply} onClick={onApply} data-testid="dataimport-derive-column-apply">
        {applying ? "Deriving…" : "Derive column → new dataset"}
      </Button>
    </div>
  );
}
