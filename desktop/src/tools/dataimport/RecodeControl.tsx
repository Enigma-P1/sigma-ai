import { Button, Field, SelectInput, TextInput } from "../../design/components";
import { distinctValueCounts } from "./dataImportLogic";
import type { ColumnInfo } from "../../api/types";

export interface RecodeControlProps {
  columns: ColumnInfo[];
  rows: Record<string, string>[];
  column: string;
  onColumnChange: (column: string) => void;
  selected: Set<string>;
  onToggleValue: (value: string) => void;
  target: string;
  onTargetChange: (value: string) => void;
  onApply: () => void;
  applying: boolean;
}

/** The vital-few fix, and the derivation that matters most (docs/uat/
 * PLAN.md 1.3): pick a column, see every distinct value it actually holds
 * with a count, check off however many spellings are really the same
 * thing, and say what they should all become. Dave's `JM` / `J. Morales` /
 * `J Morales` -- one man, three spellings, wrongly counted as three
 * separate members of a Pareto's vital few (docs/uat/README.md) -- is
 * exactly this control, mergeable in a handful of clicks. */
export function RecodeControl({
  columns, rows, column, onColumnChange, selected, onToggleValue, target, onTargetChange, onApply, applying,
}: RecodeControlProps) {
  const values = column ? distinctValueCounts(rows, column) : [];
  const canApply = selected.size > 0 && target.trim() !== "" && !applying;

  return (
    <div className="sigma-dataimport__recode" data-testid="dataimport-recode-control">
      <p className="sigma-dataimport__mode-helper">
        Select every spelling below that really means the same thing, then say what they should all become. This
        creates a new dataset -- the one you are looking at now is not changed.
      </p>

      <Field label="Column to recode" htmlFor="dataimport-recode-column">
        <SelectInput
          id="dataimport-recode-column" data-testid="dataimport-recode-column" value={column}
          onChange={(e) => onColumnChange(e.target.value)}
        >
          <option value="">Select a column…</option>
          {columns.map((c) => (
            <option key={c.name} value={c.name}>{c.name}</option>
          ))}
        </SelectInput>
      </Field>

      {column &&
        (values.length === 0 ? (
          <p className="sigma-dataimport__status">This column has no values to recode.</p>
        ) : (
          <div className="sigma-dataimport__recode-values" data-testid="dataimport-recode-values">
            {values.map((v, i) => (
              <label key={v.value} className="sigma-dataimport__recode-row" data-testid={`dataimport-recode-value-${i}`}>
                <input type="checkbox" checked={selected.has(v.value)} onChange={() => onToggleValue(v.value)} />
                <span className="sigma-dataimport__recode-value">{v.value}</span>
                <span className="sigma-dataimport__recode-count">({v.count})</span>
              </label>
            ))}
          </div>
        ))}

      <Field
        label="Recode selected values to" htmlFor="dataimport-recode-target"
        helper='The one value every checked spelling becomes -- e.g. "J. Morales".'
      >
        <TextInput
          id="dataimport-recode-target" data-testid="dataimport-recode-target" value={target}
          onChange={(e) => onTargetChange(e.target.value)} placeholder="Type the value they should all become"
        />
      </Field>

      <Button variant="primary" size="sm" disabled={!canApply} onClick={onApply} data-testid="dataimport-recode-apply">
        {applying
          ? "Recoding…"
          : selected.size > 0
            ? `Recode ${selected.size} value${selected.size === 1 ? "" : "s"} → new dataset`
            : "Select values to recode"}
      </Button>
    </div>
  );
}
