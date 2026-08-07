import { useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { BoxChart } from "../../charts";
import type { DatasetDetail } from "../../api/types";
import { buildBoxGroups, numericColumns, textColumns } from "./chartSetLogic";

export function BoxPanel({ detail }: { detail: DatasetDetail }) {
  const values = numericColumns(detail.meta);
  const groupsCols = textColumns(detail.meta);
  const [valueColumn, setValueColumn] = useState(values[0]?.name ?? "");
  const [groupColumn, setGroupColumn] = useState(groupsCols[0]?.name ?? "");

  if (values.length === 0 || groupsCols.length === 0) {
    return <p data-testid="chartset-box-panel">Box plot needs one numeric column and one text (grouping) column.</p>;
  }

  const groups = buildBoxGroups(detail.rows, groupColumn, valueColumn);

  return (
    <div data-testid="chartset-box-panel">
      <div className="sigma-chartset__controls">
        <Field label="Value column (numeric)" htmlFor="chartset-box-value">
          <SelectInput id="chartset-box-value" data-testid="chartset-box-value" value={valueColumn} onChange={(e) => setValueColumn(e.target.value)}>
            {values.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
        <Field label="Group by (text)" htmlFor="chartset-box-group">
          <SelectInput id="chartset-box-group" data-testid="chartset-box-group" value={groupColumn} onChange={(e) => setGroupColumn(e.target.value)}>
            {groupsCols.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
      </div>
      <BoxChart groups={groups} unitLabel={valueColumn} testId="chartset-box" />
    </div>
  );
}
