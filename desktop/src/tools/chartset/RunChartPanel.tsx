import { useEffect, useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { RunChart } from "../../charts";
import { runDescriptive } from "../../api/client";
import type { Computed, DatasetDetail, DescriptiveStats } from "../../api/types";
import { numericColumnValues, numericColumns, resolveColumn } from "./chartSetLogic";
import { saveChartSetView } from "./chartSetViewStore";
import type { ChartSetView } from "./chartSetViewStore";

export interface RunChartPanelProps {
  detail: DatasetDetail;
  projectId: string;
  /** This project's saved chart view (chartSetViewStore.ts, PLAN 2.1) --
   * seeds the column picker the first time this panel sees a dataset. */
  restored?: ChartSetView;
}

export function RunChartPanel({ detail, projectId, restored }: RunChartPanelProps) {
  const columns = numericColumns(detail.meta);
  const [column, setColumnState] = useState(() => resolveColumn(restored?.runChartColumn, columns));
  const [descriptive, setDescriptive] = useState<Computed<DescriptiveStats> | null>(null);
  const values = column ? numericColumnValues(detail.rows, column) : [];

  // The dataset changed under an already-mounted panel -- the previous pick
  // may not exist on the new one, so fall back to its first column instead
  // of leaving a selection the <select> can't actually show.
  useEffect(() => {
    setColumnState((prev) => resolveColumn(prev, columns));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail.meta.dataset_id]);

  function setColumn(next: string) {
    setColumnState(next);
    saveChartSetView(projectId, { runChartColumn: next });
  }

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

  // Same reason as HistogramPanel: no numeric column means the headline
  // would wait on statistics that are never requested.
  if (columns.length === 0) {
    return <p data-testid="chartset-runchart-panel">A run chart needs a numeric column; this dataset has none. Set a column's type to numeric on the import screen if it should be one.</p>;
  }

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
