import { fmt } from "./hypothesisLogic";
import type { HypContingencyCell } from "../../api/types";
import "./HypothesisResults.css";

export interface ContingencyResultTableProps {
  cells: HypContingencyCell[];
}

/** Observed vs. expected per cell -- chi_square_independence's own table,
 * read straight off the engine response (never recomputed here). */
export function ContingencyResultTable({ cells }: ContingencyResultTableProps) {
  const rows = Array.from(new Set(cells.map((c) => c.row)));
  const cols = Array.from(new Set(cells.map((c) => c.col)));
  const at = (row: string, col: string) => cells.find((c) => c.row === row && c.col === col);

  return (
    <table className="sigma-hyp-groups-table" data-testid="hyp-contingency-result">
      <thead>
        <tr><th /> {cols.map((c) => <th key={c}>{c}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r}>
            <th>{r}</th>
            {cols.map((c) => {
              const cell = at(r, c);
              return <td key={c}>{cell ? `${cell.observed} (exp ${fmt(cell.expected, 1)})` : "—"}</td>;
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
