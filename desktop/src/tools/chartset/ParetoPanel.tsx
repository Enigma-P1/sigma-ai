import { useEffect, useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { ParetoChart } from "../../charts";
import { runPareto } from "../../api/client";
import type { Computed, DatasetDetail, ParetoResult } from "../../api/types";
import { resolveColumn, textColumnValues, textColumns } from "./chartSetLogic";
import { saveChartSetView } from "./chartSetViewStore";
import type { ChartSetView } from "./chartSetViewStore";

export interface ParetoPanelProps {
  detail: DatasetDetail;
  projectId: string;
  /** This project's saved chart view (chartSetViewStore.ts, PLAN 2.1) --
   * seeds the column picker the first time this panel sees a dataset. */
  restored?: ChartSetView;
}

export function ParetoPanel({ detail, projectId, restored }: ParetoPanelProps) {
  const columns = textColumns(detail.meta);
  const [column, setColumnState] = useState(() => resolveColumn(restored?.paretoColumn, columns));
  const [result, setResult] = useState<Computed<ParetoResult> | null>(null);

  // The dataset changed under an already-mounted panel (the picker above
  // this grid, not this one) -- the previous pick may not exist on the new
  // one, so fall back to its first column instead of leaving a selection
  // the <select> can't actually show.
  useEffect(() => {
    setColumnState((prev) => resolveColumn(prev, columns));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail.meta.dataset_id]);

  function setColumn(next: string) {
    setColumnState(next);
    saveChartSetView(projectId, { paretoColumn: next });
  }

  // Rows whose category cell is blank cannot be tallied, so they are not in
  // the chart -- and a chart headed "9 total" over a 10-row dataset reads as
  // an arithmetic error unless the missing one is named. Saying it here is
  // the whole fix: the count was always right, it was just unexplained.
  // (`detail.rows` here is already the filter-panel's subset, not the whole
  // dataset -- see ChartSetScreen's filteredDetail -- so this count and the
  // filter's own "N of M rows" line stay consistent with each other.)
  const excluded = column ? detail.rows.length - textColumnValues(detail.rows, column).length : 0;

  useEffect(() => {
    const categories = column ? textColumnValues(detail.rows, column) : [];
    if (categories.length === 0) {
      setResult(null);
      return;
    }
    let cancelled = false;
    runPareto(categories)
      .then((r) => { if (!cancelled) setResult(r); })
      .catch(() => { if (!cancelled) setResult(null); });
    return () => { cancelled = true; };
  }, [column, detail]);

  if (columns.length === 0) {
    return <p data-testid="chartset-pareto-panel">This dataset has no text (categorical) columns for a Pareto chart.</p>;
  }

  return (
    <div data-testid="chartset-pareto-panel">
      <div className="sigma-chartset__controls">
        <Field label="Category column" htmlFor="chartset-pareto-column">
          <SelectInput id="chartset-pareto-column" data-testid="chartset-pareto-column" value={column} onChange={(e) => setColumn(e.target.value)}>
            {columns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </SelectInput>
        </Field>
      </div>
      {excluded > 0 && (
        <p className="sigma-chartset__excluded" data-testid="chartset-pareto-excluded">
          {excluded} of {detail.rows.length} rows have no {column} and are not counted in this chart.
        </p>
      )}
      <ParetoChart result={result} subject={column} testId="chartset-pareto" />
    </div>
  );
}
