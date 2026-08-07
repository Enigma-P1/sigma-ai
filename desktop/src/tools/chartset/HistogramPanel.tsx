import { useEffect, useState } from "react";
import { Field, SelectInput, TextInput } from "../../design/components";
import { Histogram } from "../../charts";
import { runDescriptive } from "../../api/client";
import type { Computed, DatasetDetail, DescriptiveStats } from "../../api/types";
import { numericColumnValues, numericColumns } from "./chartSetLogic";

export function HistogramPanel({ detail }: { detail: DatasetDetail }) {
  const columns = numericColumns(detail.meta);
  const [column, setColumn] = useState(columns[0]?.name ?? "");
  const [usl, setUsl] = useState("");
  const [lsl, setLsl] = useState("");
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
    // eslint: values is re-derived from detail/column every render; the
    // effect only needs to re-fire when the *selection* changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [column, detail]);

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
