import { useEffect, useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { ParetoChart } from "../../charts";
import { runPareto } from "../../api/client";
import type { Computed, DatasetDetail, ParetoResult } from "../../api/types";
import { textColumnValues, textColumns } from "./chartSetLogic";

export function ParetoPanel({ detail }: { detail: DatasetDetail }) {
  const columns = textColumns(detail.meta);
  const [column, setColumn] = useState(columns[0]?.name ?? "");
  const [result, setResult] = useState<Computed<ParetoResult> | null>(null);

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
      <ParetoChart result={result} testId="chartset-pareto" />
    </div>
  );
}
