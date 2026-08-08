import { ChartFrame } from "../../charts/ChartFrame";
import { CHART_COLORS } from "../../charts/palette";
import type { Computed, TrendPoint } from "../../api/types";

export interface FiveSTrendChartProps {
  trend: Computed<TrendPoint[]> | null;
}

/** Rubric R-CTL-05 #3: "recurrence is real ... a trend line" -- rendered
 * straight off the engine's own trend rollup, nothing recomputed here. */
export function FiveSTrendChart({ trend }: FiveSTrendChartProps) {
  const points = trend?.value ?? [];
  const headline = points.length === 0
    ? "No rounds yet"
    : `${points.length} round(s) plotted -- latest total ${points[points.length - 1].total}/25`;

  return (
    <ChartFrame
      title="5S Trend" headline={headline} tone={points.length >= 2 ? "pass" : "neutral"}
      detail={points.length < 2 ? "A second round makes this trend line real (rubric R-CTL-05 #3)." : undefined}
      data={[{
        type: "scatter", mode: "lines+markers",
        x: points.map((p) => p.date), y: points.map((p) => p.total), text: points.map((p) => p.area),
        line: { color: CHART_COLORS.accent, width: 2 }, marker: { color: CHART_COLORS.accent, size: 8 },
      }]}
      layout={{ xaxis: { title: { text: "Round date" } }, yaxis: { title: { text: "Total (0-25)" }, range: [0, 25] } }}
      testId="fives-trend-chart"
    />
  );
}
