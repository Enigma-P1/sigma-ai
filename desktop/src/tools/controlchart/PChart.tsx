import { ChartFrame } from "../../charts/ChartFrame";
import { CHART_COLORS } from "../../charts/palette";
import type { PChartPoint } from "../../api/types";
import type { VerdictTone } from "../../design/components";

export interface PChartSignal {
  rule_id: string;
  start_index: number;
  end_index: number;
  side: string;
}

export interface PChartProps {
  points: PChartPoint[];
  pBar: number;
  signals: PChartSignal[];
  meetsFreezeFloor: boolean;
  testId?: string;
}

function pointColor(signals: PChartSignal[], i: number, normal: string, flagged: string): string {
  return signals.some((s) => i >= s.start_index && i <= s.end_index) ? flagged : normal;
}

/** T-21's p-chart: proportion per subgroup with VARYING per-point limits
 * (a stepped "hv" line, not a fixed band -- stats/p_chart.py's own
 * varying-n formula). The plain IMR chart (src/tools/baseline/ImrChart.tsx)
 * is reused verbatim for the continuous half of T-21; this is the
 * attribute-half sibling the task brief calls for. */
export function PChart({ points, pBar, signals, meetsFreezeFloor, testId }: PChartProps) {
  const hasSignal = signals.length > 0;
  const tone: VerdictTone = hasSignal ? "fail" : meetsFreezeFloor ? "pass" : "flag";
  const headline = hasSignal
    ? `${signals.length} signal(s) against the frozen limits`
    : meetsFreezeFloor
      ? `${points.length} subgroups, no default-rule signal`
      : `${points.length} subgroup(s) -- below the 20-subgroup freeze floor (matrix §4a)`;
  const colors = points.map((_, i) => pointColor(signals, i, CHART_COLORS.accent, CHART_COLORS.fail));
  const x = points.map((_, i) => i + 1);

  return (
    <ChartFrame
      title="p Chart — Proportion Defective"
      headline={headline}
      tone={tone}
      detail={`Center line p̄=${pBar.toFixed(4)} — limits vary per subgroup size (n), narrower for larger subgroups`}
      data={[
        {
          type: "scatter", mode: "lines+markers", name: "p", x, y: points.map((p) => p.p),
          line: { color: CHART_COLORS.textFaint, width: 1 }, marker: { color: colors, size: 7 },
          text: points.map((p) => `${p.label}: n=${p.n}, defective=${p.defective_count}`), hoverinfo: "text+y",
        },
        { type: "scatter", mode: "lines", name: "UCL", x, y: points.map((p) => p.ucl), line: { color: CHART_COLORS.fail, dash: "dash", shape: "hv" } },
        { type: "scatter", mode: "lines", name: "LCL", x, y: points.map((p) => p.lcl), line: { color: CHART_COLORS.fail, dash: "dash", shape: "hv" } },
        { type: "scatter", mode: "lines", name: "p̄", x, y: points.map(() => pBar), line: { color: CHART_COLORS.textMuted, width: 1.5 } },
      ]}
      layout={{ xaxis: { title: { text: "Subgroup" } }, yaxis: { title: { text: "Proportion defective" } } }}
      testId={testId}
    />
  );
}
