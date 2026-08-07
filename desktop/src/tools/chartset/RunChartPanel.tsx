import { useEffect, useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { RunChart } from "../../charts";
import { runDescriptive } from "../../api/client";
import type { Computed, DatasetDetail, DescriptiveStats } from "../../api/types";
import { numericColumnValues, numericColumns } from "./chartSetLogic";

export function RunChartPanel({ detail }: { detail: DatasetDetail }) {
  const columns = numericColumns(detail.meta);
  const [column, setColumn] = useState(columns[0]?.name ?? "");
  const [descriptive, setDescriptive] = useState<Computed<DescriptiveStats> | null>(null);
  const values = column ? numericColumnValues(detail.rows, column) : [];

  useEffect(() => {
    if (!column || values.length < 2) {
      setDescriptive(null);
      return;
    }
    let cancelled = false;
    runDescriptive(values)
      .then((d) => { if (!cancelled) setDescriptive(d); })
      .catch(() => { if (!cancelled) setDescriptive(null); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [column, detail]);

  return (
    <div data-testid="chartset-runchart-panel">
      <div className="sigma-chartset__controls">
        <Field label="Column" htmlFor="chartset-runchart-column">
          <SelectInput id="chartset-runchart-column" data-testid="chartset-runchart-column" value={column} onChange={(e) => setColumn(e.target.value)}>
            {columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
      </div>
      <RunChart data={values} unitLabel={column} descriptive={descriptive} testId="chartset-runchart" />
    </div>
  );
}
