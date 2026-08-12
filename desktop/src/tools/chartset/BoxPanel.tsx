import { useEffect, useState } from "react";
import { Field, SelectInput } from "../../design/components";
import { BoxChart } from "../../charts";
import type { DatasetDetail } from "../../api/types";
import { buildBoxGroups, numericColumns, resolveColumn, textColumns } from "./chartSetLogic";
import { saveChartSetView } from "./chartSetViewStore";
import type { ChartSetView } from "./chartSetViewStore";

export interface BoxPanelProps {
  detail: DatasetDetail;
  projectId: string;
  /** This project's saved chart view (chartSetViewStore.ts, PLAN 2.1) --
   * seeds the value/group pickers the first time this panel sees a
   * dataset. */
  restored?: ChartSetView;
}

export function BoxPanel({ detail, projectId, restored }: BoxPanelProps) {
  const values = numericColumns(detail.meta);
  const groupsCols = textColumns(detail.meta);
  const [valueColumn, setValueColumnState] = useState(() => resolveColumn(restored?.boxValueColumn, values));
  const [groupColumn, setGroupColumnState] = useState(() => resolveColumn(restored?.boxGroupColumn, groupsCols));

  // The dataset changed under an already-mounted panel -- the previous
  // picks may not exist on the new one, so fall back the same way the
  // initial pick does instead of leaving a selection the <select> can't
  // actually show.
  useEffect(() => {
    setValueColumnState((prev) => resolveColumn(prev, values));
    setGroupColumnState((prev) => resolveColumn(prev, groupsCols));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail.meta.dataset_id]);

  function setValueColumn(next: string) {
    setValueColumnState(next);
    saveChartSetView(projectId, { boxValueColumn: next });
  }
  function setGroupColumn(next: string) {
    setGroupColumnState(next);
    saveChartSetView(projectId, { boxGroupColumn: next });
  }

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
