import { useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { ScatterChart } from "../../charts";
import type { DatasetDetail } from "../../api/types";
import { numericColumnValues, numericColumns } from "./chartSetLogic";

/** Visual only, no engine call — a scatter's raw x/y points are the same
 * stored numbers displayed, not a derived statistic (M0 matrix
 * correction A-2: no fitted line, no r computed anywhere for this v1
 * chart, client or server). */
export function ScatterPanel({ detail }: { detail: DatasetDetail }) {
  const columns = numericColumns(detail.meta);
  const [xColumn, setXColumn] = useState(columns[0]?.name ?? "");
  const [yColumn, setYColumn] = useState(columns[1]?.name ?? columns[0]?.name ?? "");

  if (columns.length < 2) {
    return <p data-testid="chartset-scatter-panel">Scatter needs at least two numeric columns; this dataset has {columns.length}.</p>;
  }

  const x = numericColumnValues(detail.rows, xColumn);
  const y = numericColumnValues(detail.rows, yColumn);
  const n = Math.min(x.length, y.length);

  return (
    <div data-testid="chartset-scatter-panel">
      <div className="sigma-chartset__controls">
        <Field label="X column" htmlFor="chartset-scatter-x">
          <SelectInput id="chartset-scatter-x" data-testid="chartset-scatter-x" value={xColumn} onChange={(e) => setXColumn(e.target.value)}>
            {columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
        <Field label="Y column" htmlFor="chartset-scatter-y">
          <SelectInput id="chartset-scatter-y" data-testid="chartset-scatter-y" value={yColumn} onChange={(e) => setYColumn(e.target.value)}>
            {columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
      </div>
      <ScatterChart x={x.slice(0, n)} y={y.slice(0, n)} xLabel={xColumn} yLabel={yColumn} testId="chartset-scatter" />
    </div>
  );
}
