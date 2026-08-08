import { ChartFrame } from "../../charts/ChartFrame";
import { CHART_COLORS } from "../../charts/palette";
import { EXIT04_NEXT_ACTION, pointColor, pointHoverText } from "./baselineLogic";
import type { Computed, ImrChartResult } from "../../api/types";
import type { VerdictTone } from "../../design/components";

export interface ImrChartProps {
  values: number[];
  stability: Computed<ImrChartResult>;
  stable: boolean;
  stabilityNote: string;
  unitLabel?: string;
  testId?: string;
}

/** T-13's I-MR chart: points, 3σ limits, and Western Electric signals
 * colored with the rule name on hover (M2 brief). The plain Run Chart in
 * T-14 (src/charts/RunChart.tsx) is the lighter cousin — time order and a
 * median center line only, no sigma limits or signals. */
export function ImrChart({ values, stability, stable, stabilityNote, unitLabel = "", testId }: ImrChartProps) {
  const s = stability.value;
  const tone: VerdictTone = stable ? "pass" : "fail";
  const colors = values.map((_, i) => pointColor(s.signals, i, CHART_COLORS.accent, CHART_COLORS.fail));
  const hover = values.map((v, i) => pointHoverText(s.signals, i, v));
  const limitLine = (y: number, color: string, dash?: string) => ({
    type: "line", x0: 0, x1: 1, xref: "paper", y0: y, y1: y, line: { color, dash, width: 1.5 },
  });

  return (
    <ChartFrame
      title="I-MR Chart — Individuals"
      headline={stabilityNote}
      tone={tone}
      detail={
        <>
          {!stable && <p data-testid="baseline-exit04-next-action">{EXIT04_NEXT_ACTION}</p>}
          {`Center line ${s.i_cl.toFixed(3)}${unitLabel} · limits ${s.i_lcl.toFixed(3)} to ${s.i_ucl.toFixed(3)}${unitLabel} (3σ, sigma_within=${s.sigma_within.toFixed(3)})`}
        </>
      }
      data={[{
        type: "scatter", mode: "lines+markers",
        x: values.map((_, i) => i + 1), y: values,
        line: { color: CHART_COLORS.textFaint, width: 1 },
        marker: { color: colors, size: 7 },
        text: hover, hoverinfo: "text",
      }]}
      layout={{
        xaxis: { title: { text: "Observation order" } },
        yaxis: { title: unitLabel ? { text: unitLabel } : undefined },
        shapes: [
          limitLine(s.i_cl, CHART_COLORS.textMuted),
          limitLine(s.i_ucl, CHART_COLORS.fail, "dash"),
          limitLine(s.i_lcl, CHART_COLORS.fail, "dash"),
        ],
      }}
      testId={testId}
    />
  );
}
