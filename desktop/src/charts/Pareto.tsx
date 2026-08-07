import { ChartFrame } from "./ChartFrame";
import { CHART_COLORS } from "./palette";
import type { Computed, ParetoResult } from "../api/types";
import type { VerdictTone } from "../design/components";

export interface ParetoChartProps {
  title?: string;
  /** The full engine response (POST /stats/pareto) — sort order,
   * cumulative shares, the vital-few call, and the flat-vs-not call are
   * all engine-made (M2 brief: "the vital-few call is engine-made, not
   * client-made"). */
  result: Computed<ParetoResult> | null;
  testId?: string;
}

function headlineFor(result: ParetoResult | undefined): { headline: string; tone: VerdictTone } {
  if (!result) return { headline: "Waiting on the engine's Pareto tally…", tone: "neutral" };
  if (result.flat) {
    return {
      headline: `No small subset dominates — ${result.categories.length} categories are roughly even (${result.total} total)`,
      tone: "flag",
    };
  }
  const vital = result.categories.filter((c) => c.vital_few);
  const share = vital[vital.length - 1]?.cumulative_share ?? 0;
  return {
    headline: `Vital few: ${vital.map((c) => c.category).join(", ")} account for ${(share * 100).toFixed(1)}% of ${result.total}`,
    tone: "pass",
  };
}

export function ParetoChart({ title = "Pareto", result, testId }: ParetoChartProps) {
  const value = result?.value;
  const { headline, tone } = headlineFor(value);
  const categories = value?.categories ?? [];

  return (
    <ChartFrame
      title={title}
      headline={headline}
      tone={tone}
      detail="Bars sorted by count; the line is cumulative share. Vital-few bars are highlighted to the 80% line."
      data={[
        {
          type: "bar", name: "Count",
          x: categories.map((c) => c.category), y: categories.map((c) => c.count),
          marker: { color: categories.map((c) => (c.vital_few ? CHART_COLORS.accent : CHART_COLORS.neutralSoft)) },
        },
        {
          type: "scatter", mode: "lines+markers", name: "Cumulative %", yaxis: "y2",
          x: categories.map((c) => c.category), y: categories.map((c) => c.cumulative_share * 100),
          line: { color: CHART_COLORS.textMuted, width: 2 },
          marker: { color: CHART_COLORS.textMuted, size: 5 },
        },
      ]}
      layout={{
        yaxis: { title: { text: "Count" } },
        yaxis2: { title: { text: "Cumulative %" }, overlaying: "y", side: "right", range: [0, 100], gridcolor: "transparent" },
        shapes: [{ type: "line", x0: 0, x1: 1, xref: "paper", y0: 80, y1: 80, yref: "y2", line: { color: CHART_COLORS.textFaint, dash: "dot", width: 1 } }],
        showlegend: true,
        legend: { orientation: "h", y: -0.2 },
      }}
      testId={testId}
    />
  );
}
