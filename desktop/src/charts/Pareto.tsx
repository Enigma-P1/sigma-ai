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

/** How many category names the headline spells out before it starts
 * counting instead. Five fits a line; twenty-one does not. */
const HEADLINE_NAME_LIMIT = 5;

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
  // A "vital few" of twenty-one names is a sentence nobody reads, and the
  // reader cannot tell from it that the few is not few. Naming the first
  // handful and counting the rest says both. The engine still owns the
  // vital-few/flat call -- this only decides how to print it.
  const names = vital.length > HEADLINE_NAME_LIMIT
    ? `${vital.slice(0, HEADLINE_NAME_LIMIT).map((c) => c.category).join(", ")} and ${vital.length - HEADLINE_NAME_LIMIT} more`
    : vital.map((c) => c.category).join(", ");
  const scale = vital.length > HEADLINE_NAME_LIMIT ? `${vital.length} of ${result.categories.length} categories — ` : "";
  return {
    headline: `Vital few: ${scale}${names} account for ${(share * 100).toFixed(1)}% of ${result.total}`,
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
        // WITHOUT THIS the axis is silently numeric whenever the categories
        // happen to look like numbers -- aisle "12", part number "22187" --
        // because Plotly type-infers from the x values. The bars then sit at
        // their numeric positions instead of in count order, no bar carries
        // a label (the axis prints 20k, 30k, 40k …), and the cumulative line
        // zigzags. Two testers hit this on their own data before it was
        // found: a Pareto of part numbers is exactly the case that breaks.
        xaxis: { type: "category" },
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
