import { ChartFrame } from "./ChartFrame";
import { CHART_COLORS } from "./palette";
import type { Computed, DescriptiveStats } from "../api/types";

export interface RunChartProps {
  title?: string;
  data: number[];
  unitLabel?: string;
  /** Engine-computed median (POST /stats/descriptive) drawn as the
   * center line — never a client-side re-derivation of it. */
  descriptive: Computed<DescriptiveStats> | null;
  testId?: string;
}

/** T-14's Run Chart: time order + a median center line only. The fuller
 * I-MR control chart (sigma limits, Western Electric rule signals) is
 * T-13 Baseline's job (PLAN §4.1 lists Run Chart and Baseline as
 * separate rows) — see src/tools/baseline/ImrChart.tsx for that one. */
export function RunChart({ title = "Run Chart", data, unitLabel = "", descriptive, testId }: RunChartProps) {
  const median = descriptive?.value.median ?? null;
  const u = unitLabel ? ` ${unitLabel}` : "";
  const headline =
    median == null
      ? "Waiting on the engine's descriptive statistics…"
      : `${data.length} points in collection order · center line (median) ${median.toFixed(2)}${u}`;

  return (
    <ChartFrame
      title={title}
      headline={headline}
      tone="neutral"
      detail="Points are plotted in the order the dataset was collected — no reordering."
      data={[{
        type: "scatter", mode: "lines+markers",
        x: data.map((_, i) => i + 1), y: data,
        line: { color: CHART_COLORS.accent, width: 1.5 },
        marker: { color: CHART_COLORS.accent, size: 5 },
      }]}
      layout={{
        xaxis: { title: { text: "Observation order" } },
        yaxis: { title: unitLabel ? { text: unitLabel } : undefined },
        shapes: median == null ? [] : [{
          type: "line", x0: 0, x1: 1, xref: "paper", y0: median, y1: median,
          line: { color: CHART_COLORS.textFaint, dash: "dot", width: 1.5 },
        }],
      }}
      testId={testId}
    />
  );
}
