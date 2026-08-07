import { ChartFrame } from "./ChartFrame";
import { CHART_SERIES_PALETTE } from "./palette";

export interface BoxGroup {
  label: string;
  values: number[];
}

export interface BoxChartProps {
  title?: string;
  groups: BoxGroup[];
  unitLabel?: string;
  testId?: string;
}

/** Group display (PLAN §4.1 T-14 row). Plotly's box trace computes its
 * own quartiles/whiskers to draw the box — a plotting-library rendering
 * detail, not a Green-Belt statistic the app is asserting; anything
 * quoted as a number in a headline still comes from the engine. */
export function BoxChart({ title = "Box Plot", groups, unitLabel = "", testId }: BoxChartProps) {
  const nonEmpty = groups.filter((g) => g.values.length > 0);
  return (
    <ChartFrame
      title={title}
      headline={
        nonEmpty.length === 0
          ? "Waiting on data…"
          : `${nonEmpty.length} group${nonEmpty.length === 1 ? "" : "s"} shown — read the boxes for median, spread, and outliers`
      }
      tone="neutral"
      data={nonEmpty.map((g, i) => ({
        type: "box", name: g.label, y: g.values,
        marker: { color: CHART_SERIES_PALETTE[i % CHART_SERIES_PALETTE.length] },
        boxpoints: "outliers",
      }))}
      layout={{ yaxis: { title: unitLabel ? { text: unitLabel } : undefined } }}
      testId={testId}
    />
  );
}
