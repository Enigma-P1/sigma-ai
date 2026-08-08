import { Button, TextInput } from "../../design/components";
import type { ContingencyState } from "./hypothesisFormState";
import "./HypothesisForm.css";

export interface ContingencyTableFieldsProps {
  value: ContingencyState;
  onChange: (v: ContingencyState) => void;
}

const MIN_ROWS = 2;
const MIN_COLS = 2;

/** Rows x cols observed-count grid for the association_categorical route
 * (chi-square independence). Floored at 2x2 -- a table needs at least that
 * to test an association at all. */
export function ContingencyTableFields({ value, onChange }: ContingencyTableFieldsProps) {
  function addRow() {
    onChange({ ...value, rowLabels: [...value.rowLabels, `Row ${value.rowLabels.length + 1}`], cells: [...value.cells, value.colLabels.map(() => "")] });
  }
  function removeRow(i: number) {
    if (value.rowLabels.length <= MIN_ROWS) return;
    onChange({ ...value, rowLabels: value.rowLabels.filter((_, idx) => idx !== i), cells: value.cells.filter((_, idx) => idx !== i) });
  }
  function addCol() {
    onChange({ ...value, colLabels: [...value.colLabels, `Col ${value.colLabels.length + 1}`], cells: value.cells.map((row) => [...row, ""]) });
  }
  function removeCol(j: number) {
    if (value.colLabels.length <= MIN_COLS) return;
    onChange({ ...value, colLabels: value.colLabels.filter((_, idx) => idx !== j), cells: value.cells.map((row) => row.filter((_, idx) => idx !== j)) });
  }
  function setRowLabel(i: number, label: string) {
    onChange({ ...value, rowLabels: value.rowLabels.map((l, idx) => (idx === i ? label : l)) });
  }
  function setColLabel(j: number, label: string) {
    onChange({ ...value, colLabels: value.colLabels.map((l, idx) => (idx === j ? label : l)) });
  }
  function setCell(i: number, j: number, text: string) {
    onChange({ ...value, cells: value.cells.map((row, ri) => (ri === i ? row.map((c, ci) => (ci === j ? text : c)) : row)) });
  }

  return (
    <div className="sigma-hyp-contingency" data-testid="hyp-contingency-table">
      <table className="sigma-hyp-contingency__table">
        <thead>
          <tr>
            <th />
            {value.colLabels.map((label, j) => (
              <th key={j}>
                <TextInput data-testid={`hyp-contingency-col-${j}`} value={label} onChange={(e) => setColLabel(j, e.target.value)} />
                {value.colLabels.length > MIN_COLS && <button type="button" className="sigma-hyp-contingency__remove" onClick={() => removeCol(j)}>×</button>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {value.rowLabels.map((rowLabel, i) => (
            <tr key={i}>
              <th>
                <TextInput data-testid={`hyp-contingency-row-${i}`} value={rowLabel} onChange={(e) => setRowLabel(i, e.target.value)} />
                {value.rowLabels.length > MIN_ROWS && <button type="button" className="sigma-hyp-contingency__remove" onClick={() => removeRow(i)}>×</button>}
              </th>
              {value.colLabels.map((_, j) => (
                <td key={j}>
                  <TextInput
                    type="number" min={0} data-testid={`hyp-contingency-cell-${i}-${j}`}
                    value={value.cells[i]?.[j] ?? ""} onChange={(e) => setCell(i, j, e.target.value)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="sigma-hyp-row">
        <Button variant="ghost" size="sm" data-testid="hyp-contingency-add-row" onClick={addRow}>+ Add row</Button>
        <Button variant="ghost" size="sm" data-testid="hyp-contingency-add-col" onClick={addCol}>+ Add column</Button>
      </div>
    </div>
  );
}
