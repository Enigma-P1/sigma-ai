import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { PlotlyDatum, PlotlyLayout } from "plotly.js-dist-min";
import { CHART_COLORS, CHART_FONT_FAMILY } from "./palette";

export interface PlotlyChartProps {
  data: PlotlyDatum[];
  layout?: PlotlyLayout;
  height?: number;
}

/** Raw Plotly binding — internal to charts/. Every chart-specific
 * component (Histogram, RunChart, ParetoChart, ScatterChart, BoxChart,
 * T-13's ImrChart) renders through ChartFrame, never this directly, so
 * the §F base layout (tokens palette, muted grid) lives in exactly one
 * place (ChartFrame.tsx). */
export function PlotlyChart({ data, layout, height = 340 }: PlotlyChartProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const { xaxis, yaxis, ...restLayout } = (layout ?? {}) as Record<string, unknown>;
    const mergedLayout: PlotlyLayout = {
      autosize: true,
      height,
      margin: { l: 56, r: 24, t: 16, b: 44 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: CHART_FONT_FAMILY, size: 12, color: CHART_COLORS.text },
      showlegend: false,
      ...restLayout,
      xaxis: {
        gridcolor: CHART_COLORS.grid, zerolinecolor: CHART_COLORS.grid, linecolor: CHART_COLORS.border,
        ...(xaxis as Record<string, unknown> | undefined),
      },
      yaxis: {
        gridcolor: CHART_COLORS.grid, zerolinecolor: CHART_COLORS.grid, linecolor: CHART_COLORS.border,
        ...(yaxis as Record<string, unknown> | undefined),
      },
    };
    // react() both creates (first call) and updates (subsequent calls) --
    // no purge+recreate flicker on every data/layout change.
    void Plotly.react(el, data, mergedLayout, { responsive: true, displaylogo: false, displayModeBar: "hover" });
  }, [data, layout, height]);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => Plotly.Plots.resize(el));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Separate one-time effect: purge only on final unmount, not on every
  // data/layout-driven re-run of the effect above.
  useEffect(() => {
    const el = ref.current;
    return () => {
      if (el) Plotly.purge(el);
    };
  }, []);

  return <div ref={ref} className="sigma-plotly" />;
}
