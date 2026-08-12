import { useEffect, useState } from "react";
import { Field, SelectInput, TextInput } from "../../design/components";
import { Histogram } from "../../charts";
import { runDescriptive } from "../../api/client";
import type { Computed, DatasetDetail, DescriptiveStats } from "../../api/types";
import { numericColumnValues, numericColumns, resolveColumn } from "./chartSetLogic";
import { saveChartSetView } from "./chartSetViewStore";
import type { ChartSetView } from "./chartSetViewStore";

export interface HistogramPanelProps {
  detail: DatasetDetail;
  projectId: string;
  /** This project's saved chart view (chartSetViewStore.ts, PLAN 2.1) --
   * seeds the column/USL/LSL the first time this panel sees a dataset. */
  restored?: ChartSetView;
}

export function HistogramPanel({ detail, projectId, restored }: HistogramPanelProps) {
  const columns = numericColumns(detail.meta);
  const [column, setColumnState] = useState(() => resolveColumn(restored?.histogramColumn, columns));
  const [usl, setUslState] = useState(restored?.histogramUsl ?? "");
  const [lsl, setLslState] = useState(restored?.histogramLsl ?? "");
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
    saveChartSetView(projectId, { histogramColumn: next });
  }
  function setUsl(next: string) {
    setUslState(next);
    saveChartSetView(projectId, { histogramUsl: next });
  }
  function setLsl(next: string) {
    setLslState(next);
    saveChartSetView(projectId, { histogramLsl: next });
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
    // eslint: values is re-derived from detail/column every render; the
    // effect only needs to re-fire when the *selection* changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [column, detail]);

  // With no numeric column there is nothing to select, nothing to send to
  // /stats/descriptive, and so the headline sits on "Waiting on the engine's
  // descriptive statistics…" for good -- which reads as a hung request
  // rather than as "this dataset has no numbers in it". Scatter and Box
  // already say so plainly; this says it the same way.
  if (columns.length === 0) {
    return <p data-testid="chartset-histogram-panel">A histogram needs a numeric column; this dataset has none. Set a column's type to numeric on the import screen if it should be one.</p>;
  }

  return (
    <div data-testid="chartset-histogram-panel">
      <div className="sigma-chartset__controls">
        <Field label="Column" htmlFor="chartset-histogram-column">
          <SelectInput id="chartset-histogram-column" data-testid="chartset-histogram-column" value={column} onChange={(e) => setColumn(e.target.value)}>
            {columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
        <Field label="USL (optional)" htmlFor="chartset-histogram-usl">
          <TextInput id="chartset-histogram-usl" type="number" value={usl} onChange={(e) => setUsl(e.target.value)} />
        </Field>
        <Field label="LSL (optional)" htmlFor="chartset-histogram-lsl">
          <TextInput id="chartset-histogram-lsl" type="number" value={lsl} onChange={(e) => setLsl(e.target.value)} />
        </Field>
      </div>
      <Histogram
        data={values} unitLabel={column}
        usl={usl.trim() === "" ? null : Number(usl)} lsl={lsl.trim() === "" ? null : Number(lsl)}
        descriptive={descriptive} testId="chartset-histogram"
      />
    </div>
  );
}
