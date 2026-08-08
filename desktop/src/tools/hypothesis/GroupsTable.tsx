import { fmt } from "./hypothesisLogic";
import type { HypGroupSummary } from "../../api/types";
import "./HypothesisResults.css";

export interface GroupsTableProps {
  groups: HypGroupSummary[];
  testId?: string;
}

const DASH = "—";

/** The group means/medians table every route's result (and EXIT-13's
 * interim read) renders from -- shared so both places read identically. */
export function GroupsTable({ groups, testId = "hyp-groups-table" }: GroupsTableProps) {
  if (groups.length === 0) return null;
  return (
    <table className="sigma-hyp-groups-table" data-testid={testId}>
      <thead>
        <tr>
          <th>Group</th><th>n</th><th>Mean</th><th>SD</th><th>Median</th><th>Successes</th><th>Proportion</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g) => (
          <tr key={g.label}>
            <td>{g.label}</td>
            <td>{g.n}</td>
            <td>{g.mean != null ? fmt(g.mean) : DASH}</td>
            <td>{g.sd != null ? fmt(g.sd) : DASH}</td>
            <td>{g.median != null ? fmt(g.median) : DASH}</td>
            <td>{g.successes != null ? g.successes : DASH}</td>
            <td>{g.proportion != null ? `${(g.proportion * 100).toFixed(1)}%` : DASH}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
