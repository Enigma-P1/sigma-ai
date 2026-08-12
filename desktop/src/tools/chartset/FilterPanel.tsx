import { Button, Field, Panel, SelectInput, VerdictBanner } from "../../design/components";
import type { ColumnInfo } from "../../api/types";
import { distinctColumnValues } from "./chartSetLogic";

export interface FilterPanelProps {
  /** Every column on the dataset -- not narrowed to text or numeric, since
   * a shift code or an aisle number is exactly the kind of column a
   * supervisor wants to split on (PLAN 2.5's own example, "only errors on
   * first shift," reads as a coded value as easily as a name). */
  columns: ColumnInfo[];
  /** The RAW, unfiltered rows -- the value picker and the total-row count
   * both describe the whole dataset, never an already-filtered result. */
  rows: Record<string, string>[];
  column: string;
  values: string[];
  onColumnChange: (column: string) => void;
  onValuesChange: (values: string[]) => void;
  /** How many of `rows` survive the current column/values pair -- computed
   * once in ChartSetScreen (chartSetLogic.ts's applyRowFilter) and passed
   * down rather than redone here, since every chart panel needs the exact
   * same number. */
  filteredCount: number;
}

/** T-14's subset control (PLAN 2.5): pick a column, pick one or more of
 * its values, every chart on the screen recomputes over just those rows.
 * The filtering itself happens here, client-side, on the raw stored
 * values -- what each chart panel sends onward to the engine afterward
 * (runPareto/runDescriptive) is the same kind of array it always sent,
 * just shorter; no statistic is decided here. And nothing about it is
 * silent: the row-count line below is the one thing on this screen a
 * user can't miss, because a chart quietly drawn over a subset is a lie
 * waiting to be quoted. */
export function FilterPanel({ columns, rows, column, values, onColumnChange, onValuesChange, filteredCount }: FilterPanelProps) {
  const total = rows.length;
  const active = column !== "" && values.length > 0;
  const options = column ? distinctColumnValues(rows, column) : [];

  function toggle(value: string, checked: boolean) {
    onValuesChange(checked ? [...values, value] : values.filter((v) => v !== value));
  }

  function clear() {
    onColumnChange("");
    onValuesChange([]);
  }

  return (
    <Panel title="Filter" subtitle="Applies to every chart below" className="sigma-chartset-filter">
      <div data-testid="chartset-filter-panel">
        <Field label="Column" htmlFor="chartset-filter-column">
          <SelectInput
            id="chartset-filter-column"
            data-testid="chartset-filter-column"
            value={column}
            onChange={(e) => {
              onColumnChange(e.target.value);
              onValuesChange([]); // a new column invalidates whatever values were checked for the old one
            }}
          >
            <option value="">No filter</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name}
              </option>
            ))}
          </SelectInput>
        </Field>

        {column !== "" && (
          <div className="sigma-chartset-filter__values" data-testid="chartset-filter-values">
            {options.length === 0 && <p>Every {column} cell is blank -- nothing to pick.</p>}
            {options.map(({ value, count }, i) => (
              <label className="sigma-chartset-filter__value" key={value}>
                <input
                  type="checkbox"
                  data-testid={`chartset-filter-value-${i}`}
                  checked={values.includes(value)}
                  onChange={(e) => toggle(value, e.target.checked)}
                />
                {value} <span className="sigma-chartset-filter__value-count">({count})</span>
              </label>
            ))}
          </div>
        )}

        <div data-testid="chartset-filter-count">
          <VerdictBanner
            tone={active ? "flag" : "neutral"}
            headline={active ? `${filteredCount} of ${total} rows — every chart below is drawn from this subset` : `All ${total} rows charted`}
            actions={
              active ? (
                <Button variant="ghost" size="sm" data-testid="chartset-filter-clear" onClick={clear}>
                  Clear filter
                </Button>
              ) : undefined
            }
          />
        </div>
      </div>
    </Panel>
  );
}
