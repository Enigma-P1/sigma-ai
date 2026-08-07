import { ChartFrame } from "./ChartFrame";
import { CHART_COLORS } from "./palette";
import type { Computed, DescriptiveStats } from "../api/types";
import type { VerdictTone } from "../design/components";

export interface HistogramProps {
  title?: string;
  data: number[];
  unitLabel?: string;
  usl?: number | null;
  lsl?: number | null;
  /** Engine-computed (POST /stats/descriptive) — the headline quotes
   * this, never a client-side mean/sd of `data` (rubric R-MEA-10). */
  descriptive: Computed<DescriptiveStats> | null;
  testId?: string;
}

function headlineFor(descriptive: Computed<DescriptiveStats> | null, unitLabel: string): { headline: string; tone: VerdictTone } {
  if (!descriptive) return { headline: "Waiting on the engine's descriptive statistics…", tone: "neutral" };
  const d = descriptive.value;
  const u = unitLabel ? ` ${unitLabel}` : "";
  return { headline: `n=${d.n} · mean ${d.mean.toFixed(2)}${u} · sd ${d.sd.toFixed(2)}${u} · median ${d.median.toFixed(2)}${u}`, tone: "neutral" };
}

export function Histogram({ title = "Histogram", data, unitLabel = "", usl, lsl, descriptive, testId }: HistogramProps) {
  const { headline, tone } = headlineFor(descriptive, unitLabel);
  const specLine = (value: number) => ({
    type: "line", x0: value, x1: value, yref: "paper", y0: 0, y1: 1,
    line: { color: CHART_COLORS.fail, dash: "dash", width: 2 },
  });
  const shapes = [usl != null && specLine(usl), lsl != null && specLine(lsl)].filter(Boolean);

  return (
    <ChartFrame
      title={title}
      headline={headline}
      tone={tone}
      detail={usl != null || lsl != null ? "Dashed red lines mark the spec limit(s) entered for this column." : undefined}
      data={[{ type: "histogram", x: data, marker: { color: CHART_COLORS.accentSoft, line: { color: CHART_COLORS.accent, width: 1 } } }]}
      layout={{ shapes, xaxis: { title: unitLabel ? { text: unitLabel } : undefined }, bargap: 0.05 }}
      testId={testId}
    />
  );
}
