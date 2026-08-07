import { ChartFrame } from "./ChartFrame";
import { CHART_COLORS } from "./palette";

export interface ScatterChartProps {
  title?: string;
  x: number[];
  y: number[];
  xLabel: string;
  yLabel: string;
  testId?: string;
}

/** Visual only — no fitted line, no r (M0 matrix correction A-2, PLAN
 * §4.1 T-14 row). The caption names EXIT-15 explicitly rather than
 * quietly omitting the regression math. */
export function ScatterChart({ title = "Scatter", x, y, xLabel, yLabel, testId }: ScatterChartProps) {
  return (
    <ChartFrame
      title={title}
      headline={`${x.length} points plotted — look for a visual pattern only`}
      tone="neutral"
      caption={
        <>
          <strong>EXIT-15:</strong> correlation and regression (a fitted line, an r value) are not computed in this
          version — deferred to v1.1. This plot is for visual inspection only.
        </>
      }
      data={[{ type: "scatter", mode: "markers", x, y, marker: { color: CHART_COLORS.accent, size: 7, opacity: 0.75 } }]}
      layout={{ xaxis: { title: { text: xLabel } }, yaxis: { title: { text: yLabel } } }}
      testId={testId}
    />
  );
}
