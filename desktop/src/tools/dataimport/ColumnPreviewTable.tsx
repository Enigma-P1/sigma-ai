import { SelectInput } from "../../design/components";
import type { ColumnInfo, ColumnType } from "../../api/types";

export interface ColumnPreviewTableProps {
  columns: ColumnInfo[];
  onTypeChange: (columnName: string, type: ColumnType) => void;
}

/** T-11's "column preview with inferred types (confirmable)" — one row
 * per column: name, what the sniffer inferred, a dropdown to confirm or
 * override it, and a few real sample values so the choice isn't blind. */
export function ColumnPreviewTable({ columns, onTypeChange }: ColumnPreviewTableProps) {
  return (
    <div className="sigma-dataimport__table-wrap" data-testid="dataimport-column-preview">
      <table className="sigma-dataimport__table">
        <thead>
          <tr>
            <th>Column</th>
            <th>Inferred type</th>
            <th>Confirmed type</th>
            <th>Sample values</th>
          </tr>
        </thead>
        <tbody>
          {columns.map((c) => (
            <tr key={c.name}>
              <td>{c.name}</td>
              <td>{c.inferred_type}</td>
              <td>
                <SelectInput
                  value={c.type}
                  data-testid={`dataimport-column-type-${c.name}`}
                  onChange={(e) => onTypeChange(c.name, e.target.value as ColumnType)}
                >
                  <option value="numeric">numeric</option>
                  <option value="text">text</option>
                </SelectInput>
              </td>
              <td className="sigma-dataimport__samples">{c.sample_values.join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
